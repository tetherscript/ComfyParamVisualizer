import sys
import os
import json

# Usage:
#   python dump_picklist.py <comfyui_root> <workflow_filename> <node_id> <property_name> <output_filename>

if len(sys.argv) != 6:
    print("Usage: python dump_picklist.py <comfyui_root> <workflow_filename> <node_id> <property_name> <output_filename>")
    sys.exit(1)

COMFYUI_ROOT = sys.argv[1]
WORKFLOW_FILENAME = sys.argv[2]
NODE_ID = sys.argv[3]
PROPERTY_NAME = sys.argv[4]
OUTPUT_FILENAME = sys.argv[5]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_FILE = os.path.join(SCRIPT_DIR, WORKFLOW_FILENAME)
OUTPUT_FILE = os.path.join(SCRIPT_DIR, OUTPUT_FILENAME)

# --- Validate ComfyUI root layout ---
has_pkg_nodes = os.path.isfile(os.path.join(COMFYUI_ROOT, "comfy", "nodes.py"))
has_root_nodes = os.path.isfile(os.path.join(COMFYUI_ROOT, "nodes.py"))
if not (has_pkg_nodes or has_root_nodes):
    raise FileNotFoundError(
        "Not a valid ComfyUI root. Expected either:\n"
        "  - comfy/nodes.py  (repo layout), or\n"
        "  - nodes.py        (portable layout)\n"
        "Got: " + COMFYUI_ROOT
    )

if not os.path.isfile(WORKFLOW_FILE):
    raise FileNotFoundError("Workflow file not found next to script: " + WORKFLOW_FILE)

# --- Purge any preloaded comfy/nodes to avoid wrong imports ---
for key in list(sys.modules.keys()):
    if key == "comfy" or key.startswith("comfy.") or key == "nodes":
        del sys.modules[key]

# --- Put OUR ComfyUI paths at the FRONT of sys.path ---
paths = [
    COMFYUI_ROOT,
    os.path.join(COMFYUI_ROOT, "comfy"),
    os.path.join(COMFYUI_ROOT, "execution"),
]
for p in reversed(paths):
    if p not in sys.path:
        sys.path.insert(0, p)

# --- Import correct modules based on layout ---
try:
    import nodes  # top-level nodes.py (portable + repo both have it)
except Exception as e:
    print("Error: Could not import 'nodes' from: " + COMFYUI_ROOT)
    print("Details: " + str(e))
    sys.exit(1)

# (Optional sanity check: ensure the imported file comes from COMFYUI_ROOT)
nodes_file = os.path.abspath(getattr(nodes, "__file__", ""))
if COMFYUI_ROOT not in nodes_file:
    print("Error: Imported 'nodes' from unexpected location: " + nodes_file)
    print("Expected under: " + COMFYUI_ROOT)
    sys.exit(1)

# --- Load workflow ---
with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
    workflow = json.load(f)

def get_node_type(wf, node_id):
    nodes_section = wf.get("nodes")
    if isinstance(nodes_section, list):
        for n in nodes_section:
            if str(n.get("id")) == str(node_id):
                t = n.get("type")
                if not t:
                    raise KeyError("Node found but missing 'type'.")
                return t
        raise KeyError("Node id not found in workflow nodes list: " + str(node_id))
    elif isinstance(nodes_section, dict):
        key = str(node_id)
        if key in nodes_section:
            t = nodes_section[key].get("type")
            if not t:
                raise KeyError("Node found but missing 'type'.")
            return t
        raise KeyError("Node id not found in workflow nodes dict: " + str(node_id))
    else:
        raise KeyError("Workflow missing 'nodes' or unexpected format.")

node_type = get_node_type(workflow, NODE_ID)

# --- Use the REAL registry (top-level nodes.py) ---
if not hasattr(nodes, "NODE_CLASS_MAPPINGS"):
    raise AttributeError("nodes.py has no NODE_CLASS_MAPPINGS (unexpected ComfyUI build).")

if node_type not in nodes.NODE_CLASS_MAPPINGS:
    raise KeyError("Node type not found in registry: " + node_type)

node_class = nodes.NODE_CLASS_MAPPINGS[node_type]
if not hasattr(node_class, "INPUT_TYPES"):
    raise AttributeError("Node has no INPUT_TYPES(): " + node_type)

input_types = node_class.INPUT_TYPES()

def get_picklist(input_types, prop_name):
    sections = [input_types.get("required", {}), input_types.get("optional", {})]
    for section in sections:
        if not isinstance(section, dict):
            continue
        if prop_name not in section:
            continue
        spec = section[prop_name]

        # Tuple like (["a","b"],) or ("ENUM", {"choices":[...]})
        if isinstance(spec, tuple) and len(spec) > 0:
            first = spec[0]
            if isinstance(first, list):
                return list(first)
            if len(spec) > 1 and isinstance(spec[1], dict):
                meta = spec[1]
                if "values" in meta and isinstance(meta["values"], list):
                    return list(meta["values"])
                if "choices" in meta and isinstance(meta["choices"], list):
                    return list(meta["choices"])

        # Direct list
        if isinstance(spec, list):
            return list(spec)

        # Dict with values/choices
        if isinstance(spec, dict):
            if "values" in spec and isinstance(spec["values"], list):
                return list(spec["values"])
            if "choices" in spec and isinstance(spec["choices"], list):
                return list(spec["choices"])

        raise ValueError("Property exists but is not a static picklist (may be dynamic): " + prop_name)

    raise KeyError("Property not found in required/optional: " + prop_name)

items = get_picklist(input_types, PROPERTY_NAME)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for v in items:
        f.write(str(v) + "\n")

print("ComfyUI root: " + COMFYUI_ROOT)
print("Workflow: " + WORKFLOW_FILENAME)
print("Node: " + node_type + " (ID " + str(NODE_ID) + ")")
print("Property: " + PROPERTY_NAME)
print("Dumped " + str(len(items)) + " picklist items to '" + OUTPUT_FILENAME + "' in " + SCRIPT_DIR)
print("Picklist values:")
for v in items:
    print("  " + str(v))
