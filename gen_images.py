#!/usr/bin/env python3
# gen_images_7d.py
#
# 7-axis ComfyUI sweeper (s, t, u, v, x, y, z). IDs only. API JSON only.
# Values per axis are read from line-delimited files under <basepath>/params:
#   --t 31-steps.txt  --as int   -> reads <basepath>/params/31-steps.txt; applies to node 31, input 'steps'
#   --u 31-cfg.txt    --as float -> reads <basepath>/params/31-cfg.txt;   applies to node 31, input 'cfg'
#   --v 38-text.txt   --as string-> reads <basepath>/params/38-text.txt;  applies to node 38, input 'text'
#
# Save target:
#   --save-target <nodeId>:<param>:<subfolder>
#     -> uses <subfolder> as the base token for the images folder
#     -> sets the specified node's input <param> to:
#        "<subfolder>/<nodeId>-<prop>-<val>--<nodeId>-<prop>-<val>..."
#        (floats keep a decimal point, then '.' becomes '_')
#
# Cleanup + Resume:
#   Images live in <basepath>/params/images (files only; subfolders untouched).
#   For the planned sweep, we compute the complete set of expected filenames:
#     "<segments>_00001.png" for each permutation (segments as above)
#   - Remove any files in that folder that are NOT in the expected set.
#   - Resume by skipping permutations whose expected file already exists.
#
# Stdlib only.

import argparse
import copy
import itertools
import json
import os
import re
import sys
import uuid
from urllib import request, error

AXES = ["s", "t", "u", "v", "x", "y", "z"]  # s and t required
DEFAULT_WORKFLOW_FILE = "simple_image1_API.json"

# -------------------- API JSON helpers --------------------

def load_api_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    if isinstance(doc, dict) and "prompt" in doc and isinstance(doc["prompt"], dict):
        return doc["prompt"]
    if isinstance(doc, dict) and "nodes" in doc and isinstance(doc["nodes"], dict):
        return doc["nodes"]
    if isinstance(doc, dict):
        return doc
    raise ValueError("Workflow must be API-format JSON (export via 'Save (API format)').")

def set_input_literal(prompt, node_id, input_name, value):
    if node_id not in prompt:
        raise KeyError("Node id '%s' not found in API JSON." % node_id)
    node = prompt[node_id]
    if "inputs" not in node or not isinstance(node["inputs"], dict):
        raise KeyError("Node '%s' has no 'inputs' dict." % node_id)
    node["inputs"][input_name] = value  # force literal (overrides any link)

def post_prompt(server, prompt_dict, client_id):
    payload = {"prompt": prompt_dict, "client_id": client_id}
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(server.rstrip("/") + "/prompt", data=data,
                          headers={"Content-Type": "application/json"}, method="POST")
    with request.urlopen(req) as resp:
        return resp.read()

# -------------------- Axis spec + values --------------------

_axis_spec_re = re.compile(r"^(?P<nid>\d+)-(?P<input>[A-Za-z0-9_]+)\.txt$")

def parse_axis_spec(filename):
    """
    '31-steps.txt' -> ('31', 'steps')
    """
    base = os.path.basename(filename)
    m = _axis_spec_re.match(base)
    if not m:
        raise ValueError("Axis spec '%s' must look like '<nodeId>-<input>.txt'." % filename)
    return m.group("nid"), m.group("input")

def coerce_token(token, as_type):
    t = as_type.lower()
    if t in ("string", "str"):
        return token
    if t == "int":
        return int(token, 10)
    if t == "float":
        return float(token)
    # auto: try int, then float, else string
    try:
        return int(token, 10)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return token

def read_values_file(path, as_type, axis_name, verbose=False):
    """
    Read a line-delimited values file. Ignores blank lines and lines starting with '#'.
    Returns a list of parsed tokens.
    """
    if verbose:
        print("[INFO] Axis %s: reading values from %s (type=%s)" % (axis_name, path, as_type))
    if not os.path.isfile(path):
        raise FileNotFoundError("Axis %s values file not found: %s" % (axis_name, path))

    vals = []
    with open(path, "r", encoding="utf-8") as f:
        for i, raw in enumerate(f, 1):
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            if line.lstrip().startswith("#"):
                continue
            try:
                vals.append(coerce_token(line, as_type))
            except Exception as e:
                raise ValueError("Axis %s: parse error on line %d in %s (%s)"
                                 % (axis_name, i, path, str(e)))
    if verbose:
        print("[INFO] Axis %s: %d values loaded" % (axis_name, len(vals)))
    if not vals:
        raise ValueError("Axis %s: no values found in %s" % (axis_name, path))
    return vals

# -------------------- Save-target / prefix text --------------------

_save_target_re = re.compile(r"^(?P<nid>\d+):(?P<input>[A-Za-z0-9_]+):(?P<folder>.+)$")

def parse_save_target(arg):
    """
    '<nodeId>:<param>:<subfolder>' -> (node_id, param, subfolder)
    """
    m = _save_target_re.match(arg.strip())
    if not m:
        raise ValueError("--save-target must look like '<nodeId>:<param>:<subfolder>' (e.g. '9:filename_prefix:MyImages')")
    nid = m.group("nid").strip()
    inp = m.group("input").strip()
    folder = m.group("folder").strip()
    if not nid.isdigit():
        raise ValueError("Left side of --save-target must be a numeric node id.")
    if not folder:
        raise ValueError("Subfolder part in --save-target must be non-empty.")
    return nid, inp, folder

# -------------------- Filename segment builders --------------------

def safe_value_str(v):
    # Floats: always keep a decimal point; then replace '.' with '_'
    if isinstance(v, float):
        s = "{:.15f}".format(v).rstrip("0").rstrip(".")
        if "." not in s:
            s += ".0"
    else:
        s = str(v)
    return s.replace(".", "_")

def build_segments(axis_specs, axis_values_for_combo):
    """
    Build the segment string from FINAL values per (node_id,input) pair in first-appearance
    order by axis (s,t,u,v,x,y,z). Later axes override earlier ones.
    Returns: segments string "<id>-<prop>-<val>--..."
    """
    final_map = {}
    order = []
    for axis in AXES:
        spec = axis_specs.get(axis)
        if not spec:
            continue
        val = axis_values_for_combo.get(axis, None)
        if val is None:
            continue
        nid, prop = spec
        key = (nid, prop)
        final_map[key] = val
        if key not in order:
            order.append(key)
    parts = []
    for (nid, prop) in order:
        parts.append("%s-%s-%s" % (nid, prop, safe_value_str(final_map[(nid, prop)])))
    return "--".join(parts)

# -------------------- Images folder cleanup + resume --------------------

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def list_files(path):
    try:
        return [n for n in os.listdir(path) if os.path.isfile(os.path.join(path, n))]
    except FileNotFoundError:
        return []

def cleanup_folder(images_dir_for_prefix, expected_names, verbose=False):
    """
    Remove any files in images_dir_for_prefix that are not in expected_names.
    Do not touch subfolders.
    """
    if not os.path.isdir(images_dir_for_prefix):
        if verbose:
            print("[INFO] Images folder %s does not exist; skipping cleanup." % images_dir_for_prefix)
        return
    current = set(list_files(images_dir_for_prefix))
    for name in sorted(current):
        if name not in expected_names:
            try:
                os.remove(os.path.join(images_dir_for_prefix, name))
                if verbose:
                    print("[CLEAN] Removed extraneous file:", name)
            except Exception as e:
                print("[WARN] Could not remove %s: %s" % (name, str(e)), file=sys.stderr)

# -------------------- Main --------------------

def main():
    ap = argparse.ArgumentParser(
        description="ComfyUI 7D sweeper (IDs only). s and t are required. Values from <basepath>/params/*.txt."
    )
    ap.add_argument("--basepath", default=".",
                    help="Project base folder (default: current working directory). Must contain 'params' subfolder.")
    ap.add_argument("--workflow_api", default=None,
                    help="Path to API-format workflow JSON (default: <basepath>/%s)." % DEFAULT_WORKFLOW_FILE)
    ap.add_argument("--server", default="http://127.0.0.1:8188",
                    help="ComfyUI server base URL.")
    ap.add_argument("--client-id", default=None,
                    help="Optional client_id (default: random UUID4).")

    # Axis specs: each is "<nodeId>-<input>.txt" (relative to <basepath>/params)
    for axis in AXES:
        ap.add_argument("--" + axis, default=None,
                        help="Axis %s file name (e.g., '31-steps.txt') located under <basepath>/params." % axis)

    # Global types list consumed in axis order for provided axes
    ap.add_argument("--as", dest="types", action="append", default=[],
                    help="Type for the next provided axis in order (s,t,u,v,x,y,z). "
                         "Repeat per axis. One of: auto, int, float, string. "
                         "If omitted for an axis, defaults to auto.")

    # Save target: EXACTLY one, "<nodeId>:<param>:<subfolder>"
    ap.add_argument("--save-target", required=True,
                    help=("Target node, input, and base subfolder, e.g. '9:filename_prefix:SampleImageDemo'. "
                          "The script sets that node's input to '<subfolder>/<segments>' for each permutation."))

    ap.add_argument("--dry-run", action="store_true", help="Do not POST; just print plan and cleanup actions.")
    ap.add_argument("--verbose", action="store_true", help="Verbose logging.")

    args = ap.parse_args()

    # Resolve basepath relative to the current working directory
    basepath = os.path.abspath(args.basepath)
    base_params = os.path.join(basepath, "params")
    images_root = os.path.join(base_params, "images")
    if not os.path.isdir(base_params):
        print("Error: '%s' does not exist. Expected <basepath>/params." % base_params, file=sys.stderr)
        sys.exit(1)

    # Resolve workflow API path
    workflow_api_path = args.workflow_api
    if workflow_api_path is None:
        workflow_api_path = os.path.join(basepath, DEFAULT_WORKFLOW_FILE)
    elif not os.path.isabs(workflow_api_path):
        workflow_api_path = os.path.join(basepath, workflow_api_path)

    # Load API workflow
    try:
        prompt_base = load_api_prompt(workflow_api_path)
    except Exception as e:
        print("Error loading workflow API from '%s': %s" % (workflow_api_path, str(e)), file=sys.stderr)
        sys.exit(1)

    # Parse save-target and get prefix token
    try:
        target_node_id, target_param, prefix_folder = parse_save_target(args.save_target)
        if args.verbose:
            print("[INFO] Prefix token = '%s' (node %s, input '%s')" % (prefix_folder, target_node_id, target_param))
    except Exception as e:
        print("Error in --save-target: %s" % str(e), file=sys.stderr)
        sys.exit(1)

    # Gather which axes are provided and their types (consumed in axis order)
    provided_axes = [a for a in AXES if getattr(args, a) is not None]
    # Enforce s and t present
    for req_axis in ("s", "t"):
        if getattr(args, req_axis) is None:
            print("Axis '%s' is required. Provide --%s <nodeId>-<input>.txt" % (req_axis, req_axis), file=sys.stderr)
            sys.exit(1)

    # Build per-axis type map from --as queue
    type_queue = list(args.types or [])
    type_map = {}
    for axis in AXES:
        if getattr(args, axis) is not None:
            as_type = (type_queue.pop(0) if type_queue else "auto")
            tnorm = as_type.lower()
            if tnorm not in ("auto", "int", "float", "string", "str"):
                print("Invalid --as value for axis %s: %s (use auto|int|float|string)" % (axis, as_type), file=sys.stderr)
                sys.exit(1)
            type_map[axis] = "string" if tnorm == "str" else tnorm
        else:
            type_map[axis] = None

    # Parse axis specs and read values
    axis_specs = {}   # axis -> (node_id, input_name)
    axis_values = {}  # axis -> [values] or [None] if unused

    for axis in AXES:
        spec_name = getattr(args, axis)
        if spec_name is None:
            axis_values[axis] = [None]
            continue

        try:
            nid, inp = parse_axis_spec(spec_name)
        except Exception as e:
            print("Axis %s spec error: %s" % (axis, str(e)), file=sys.stderr)
            sys.exit(1)

        if nid not in prompt_base:
            print("Axis %s: node id '%s' not found in --workflow_api." % (axis, nid), file=sys.stderr)
            sys.exit(1)

        axis_specs[axis] = (nid, inp)

        values_path = os.path.join(base_params, spec_name)
        try:
            vals = read_values_file(values_path, type_map[axis] or "auto", axis, verbose=args.verbose)
        except Exception as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)

        axis_values[axis] = vals

        if axis in ("s", "t") and not vals:
            print("Axis %s requires at least one value (file: %s)." % (axis, values_path), file=sys.stderr)
            sys.exit(1)

        if args.verbose:
            print("[INFO] Axis %s -> node %s, input '%s', count=%d"
                  % (axis, nid, inp, len(vals)))

    # Build all permutations (in fixed axis order)
    dims = [range(len(axis_values[a])) for a in AXES]
    combos = list(itertools.product(*dims))
    total = len(combos)

    # Compute expected filenames for cleanup and resume
    images_dir_for_prefix = os.path.join(images_root, prefix_folder)
    expected_files = set()
    seg_cache = []  # keep segments in order alongside combos for resume loop

    for idxs in combos:
        # Value snapshot for this combo
        axis_val = {axis: axis_values[axis][i] for axis, i in zip(AXES, idxs)}
        # Build segments from final values by (node_id,input)
        segments = build_segments(axis_specs, axis_val)
        seg_cache.append(segments)
        expected_files.add("%s_%05d.png" % (segments, 1))  # always _00001.png per unique prefix

    # Cleanup anything not expected (files only)
    cleanup_folder(images_dir_for_prefix, expected_files, verbose=args.verbose)

    # Dry-run: show plan and exit
    print("Planned permutations: " + " * ".join(str(len(axis_values[a])) for a in AXES) + " = %d" % total)
    if args.dry_run:
        print("[DRY] Folder = %s" % images_dir_for_prefix)
        print("[DRY] Expected file count = %d" % len(expected_files))
        # Show a couple examples
        for i, s in enumerate(seg_cache[:min(5, len(seg_cache))], 1):
            print("[DRY] e.g. %s" % os.path.join(images_dir_for_prefix, "%s_00001.png" % s))
        return

    # Enqueue, skipping combos whose file already exists
    client_id = args.client_id or str(uuid.uuid4())
    enq = 0

    for idxs, segments in zip(combos, seg_cache):
        # If this expected file already exists, skip
        target_png = os.path.join(images_dir_for_prefix, "%s_00001.png" % segments)
        if os.path.isfile(target_png):
            if args.verbose:
                print("[SKIP] %s already exists" % target_png)
            continue

        # Deep copy API prompt and apply axis values
        prompt = copy.deepcopy(prompt_base)
        log_parts = []

        for axis, i in zip(AXES, idxs):
            val = axis_values[axis][i]
            spec = axis_specs.get(axis)
            if spec is None or val is None:
                continue
            nid, inp = spec
            try:
                set_input_literal(prompt, nid, inp, val)
            except Exception as e:
                print("[ERR] axis %s -> %s:%s assign failed: %s" % (axis, nid, inp, str(e)), file=sys.stderr)
                sys.exit(1)
            log_parts.append("%s=%s" % (axis, str(val)))

        # Build full filename_prefix: "<prefix_folder>/<segments>"
        clean_prefix = prefix_folder.rstrip("/\\")
        filename_prefix = "%s/%s" % (clean_prefix, segments) if clean_prefix else segments

        # Set ONLY on the specified target node and input
        try:
            set_input_literal(prompt, target_node_id, target_param, filename_prefix)
        except Exception as e:
            print("[ERR] save-target set failed on node %s input '%s': %s" % (target_node_id, target_param, str(e)), file=sys.stderr)
            sys.exit(1)

        tag = " ".join(log_parts) if log_parts else "(no axes set)"
        try:
            post_prompt(args.server, prompt, client_id)
            enq += 1
            print("[OK]  %s -> queued (prefix=%s)" % (tag, filename_prefix))
        except error.HTTPError as e:
            try:
                msg = e.read().decode("utf-8", errors="ignore")
            except Exception:
                msg = str(e)
            print("[ERR] HTTP %d: %s" % (e.code, msg), file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print("[ERR] %s" % str(e), file=sys.stderr)
            sys.exit(1)

    print("Done. Enqueued %d prompts to %s. Images folder: %s" %
          (enq, args.server, images_dir_for_prefix))

if __name__ == "__main__":
    main()
