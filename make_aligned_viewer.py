#!/usr/bin/env python3
# make_aligned_viewer.py (lazy-load only, no mode line)
# Change: The viewer ALWAYS uses lazy-load, and the "Mode: Lazy-load images on demand"
# line has been removed from the HTML. No base64 embedding occurs.
# Everything else remains the same.

import json
import re
import argparse
from pathlib import Path
import sys
from string import Template
import os

def parse_args():
    p = argparse.ArgumentParser(
        description="ComfyUI compact ND viewer (lazy-load only, with theme toggle)."
    )
    p.add_argument(
        "--images",
        dest="image_dir",
        default=None,
        help="Path to folder of PNGs (default: <base>/params/images).",
    )
    p.add_argument(
        "--workflow",
        dest="workflow",
        default=None,
        help="Path to ComfyUI workflow JSON (default: <base>/simple_image1.json).",
    )
    p.add_argument(
        "-o",
        "--output",
        dest="output",
        default=None,
        help="Path to output HTML (default: <images>/0000_aligned_viewer.html).",
    )
    p.add_argument(
        "--base",
        dest="basepath",
        default=".",
        help="Base directory for resolving relative paths (default: current directory).",
    )
    p.add_argument(
        "legacy_args",
        nargs="*",
        help=argparse.SUPPRESS,
    )
    return p.parse_args()

def strip_counter(token: str) -> str:
    # remove optional trailing _00001 or _00001_
    m = re.match(r"^(.*?)(_+\d+_?)$", token)
    if m and m.group(1):
        return m.group(1)
    return token

def parse_dimension_segment(seg: str):
    parts = seg.split("-")
    if len(parts) != 3:
        return None
    node_str, prop, val_token = parts
    if not node_str.isdigit():
        return None
    node_id = int(node_str)
    if not re.fullmatch(r"[A-Za-z0-9_]+", prop or ""):
        return None
    val_token = strip_counter(val_token)
    dotted = val_token.replace("_", ".")
    try:
        vnum = float(dotted)
        return node_id, prop, vnum, dotted, dotted
    except ValueError:
        if not re.fullmatch(r"[A-Za-z0-9_]+", val_token or ""):
            return None
        return node_id, prop, None, val_token, val_token

def parse_filename(fname: str):
    stem = Path(fname).stem
    segs = stem.split("--")
    dims = []
    for seg in segs:
        p = parse_dimension_segment(seg)
        if p is None:
            return None
        dims.append(p)
    return dims

def load_node_titles(workflow_path: Path):
    with open(workflow_path, "r", encoding="utf-8") as f:
        wf = json.load(f)
    titles = {}
    def pick_title(node):
        return (node.get("title")
                or node.get("label")
                or node.get("type")
                or "Node %s" % node.get("id", "?"))
    if isinstance(wf, dict) and "nodes" in wf:
        nodes = wf["nodes"]
        it = nodes.values() if isinstance(nodes, dict) else nodes
        for node in it:
            titles[int(node["id"])] = pick_title(node)
        return titles
    if isinstance(wf, list):
        for node in wf:
            titles[int(node["id"])] = pick_title(node)
        return titles
    raise ValueError("Unrecognized workflow JSON format.")

def relpath_for_html(target: Path, base: Path) -> str:
    """
    Return a POSIX-style relative path from base -> target for embedding in HTML/JSON.
    """
    rel = os.path.relpath(target, base)
    return rel.replace("\\", "/")

def main():
    args = parse_args()

    basepath = Path(args.basepath).resolve()
    if not basepath.is_dir():
        sys.exit(f"Base path not found: {basepath}")

    legacy = list(args.legacy_args or [])
    image_arg = args.image_dir
    workflow_arg = args.workflow
    output_arg = args.output

    if legacy:
        if image_arg is None and len(legacy) >= 1:
            image_arg = legacy[0]
        if workflow_arg is None and len(legacy) >= 2:
            workflow_arg = legacy[1]
        if output_arg is None and len(legacy) >= 3:
            output_arg = legacy[2]
        if len(legacy) > 3:
            sys.exit("Too many positional arguments supplied.")

    def resolve_path(path_value, default_path):
        if path_value is None:
            return default_path
        p = Path(path_value)
        if not p.is_absolute():
            p = basepath / p
        return p

    img_dir = resolve_path(image_arg, basepath / "params" / "images").resolve()
    wf_path = resolve_path(workflow_arg, basepath / "simple_image1.json").resolve()
    out_html = resolve_path(output_arg, img_dir / "0000_aligned_viewer.html").resolve()
    out_base = out_html.parent
    out_base.mkdir(parents=True, exist_ok=True)

    if not img_dir.is_dir():
        sys.exit(f"Image directory not found: {img_dir}")
    if not wf_path.is_file():
        sys.exit(f"Workflow JSON not found: {wf_path}")

    node_titles = load_node_titles(wf_path)

    images = []
    dim_signature = None
    dim_count = None
    dim_info = []
    for f in sorted(img_dir.glob("*.png")):
        parsed = parse_filename(f.name)
        if not parsed:
            continue
        if dim_count is None:
            dim_count = len(parsed)
            dim_info = [{'keys': {}, 'all_numeric': True} for _ in range(dim_count)]
            dim_signature = [(d[0], d[1]) for d in parsed]
        elif len(parsed) != dim_count:
            raise ValueError(f"Inconsistent dimension count in {f.name}")
        this_sig = [(d[0], d[1]) for d in parsed]
        if this_sig != dim_signature:
            raise ValueError(f"Dimension signature mismatch in {f.name}")
        value_keys = []
        for i,(nid,prop,vnum,vkey,vdisp) in enumerate(parsed):
            if vnum is None:
                dim_info[i]['all_numeric'] = False
            dim_info[i]['keys'].setdefault(vkey, {'num': vnum, 'disp': vdisp})
            value_keys.append(vkey)
        images.append((tuple(value_keys), f.name))
    if not images:
        sys.exit("No valid images found.")

    dim_values = []
    for i in range(dim_count):
        items = dim_info[i]['keys']
        if dim_info[i]['all_numeric']:
            order = sorted(items.keys(), key=lambda k: (items[k]['num'], k))
        else:
            order = sorted(items.keys())
        dim_values.append([{'k': k, 'd': items[k]['disp']} for k in order])

    lookup = {"|".join(vals): fname for vals, fname in images}

    # Prepare meta payload for lazy-load only
    dim_labels = []
    max_label = 0
    for (nid, prop) in dim_signature:
        title = node_titles.get(nid, f"Node {nid}")
        label = f"{title}:{nid}:{prop}"
        dim_labels.append(label)
        max_label = max(max_label, len(label))

    label_em = max(8.0, min(60.0, max_label * 0.62))

    # Lazy-load only: no base64 embedding
    image_urls = {
        fname: relpath_for_html(img_dir / fname, out_base)
        for _, fname in images
    }
    meta = dict(
        dim_values=dim_values,
        lookup=lookup,
        dim_labels=dim_labels,
        label_em=label_em,
        lazy=True,
        image_urls=image_urls
    )

    html_template = Template("""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>ComfyParamVisualizer</title>
<style>
:root { --bg:#fff; --fg:#111; --muted:#666; --border:#cfcfcf; --accent:#7a7afe; }
:root[data-theme="dark"]{ --bg:#0d0f13; --fg:#e5e7eb; --muted:#9aa0a6; --border:#2a2f3a; --accent:#7aa2ff; }
body{margin:0;font-family:sans-serif;background:var(--bg);color:var(--fg);}
.container{max-width:980px;margin:12px auto;padding:0 12px;}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}
h1{margin:0;font-size:1.05rem;font-weight:600;}
.meta{font-size:0.85rem;color:var(--muted);margin-bottom:8px;}
.toggle{border:1px solid var(--border);background:transparent;color:var(--fg);
       border-radius:8px;padding:4px 8px;cursor:pointer;}
#sliders{border:1px solid var(--border);border-radius:8px;padding:8px 10px 2px 10px;
         background:rgba(127,127,127,0.03);}
.slider-row{display:grid;grid-template-columns:auto ${label_em}em 1fr;
            align-items:center;gap:10px;margin:10px 0;}
.label-col{justify-self:end;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.slider-wrap{display:flex;flex-direction:column;align-items:center;gap:2px;}
.value-bubble{font-size:0.85rem;color:var(--muted);}
#filename{text-align:center;font-size:0.85rem;opacity:0.7;margin:8px 0 6px 0;word-break:break-all;}
#filename a{color:inherit;text-decoration:underline;}
#canvas-wrap{display:flex;justify-content:center;padding-bottom:10px;}
canvas{border:1px solid var(--border);background:#000;max-width:95vw;height:auto;}
/* Slider base */
input[type=range]{width:240px;height:26px;background:transparent;}
/* WebKit */
input[type=range]::-webkit-slider-runnable-track{height:6px;background:rgba(127,127,127,0.35);border-radius:6px;}
input[type=range]::-webkit-slider-thumb{
  -webkit-appearance:none;appearance:none;width:24px;height:24px;border-radius:50%;
  background:var(--accent);border:1px solid rgba(0,0,0,0.25);margin-top:-9px;}
input[type=range]:hover::-webkit-slider-thumb{width:26px;height:26px;margin-top:-10px;}
/* Firefox */
input[type=range]::-moz-range-track{height:6px;background:rgba(127,127,127,0.35);border-radius:6px;}
input[type=range]::-moz-range-thumb{
  width:24px;height:24px;border-radius:50%;background:var(--accent);
  border:1px solid rgba(0,0,0,0.25);}
input[type=range]:hover::-moz-range-thumb{width:26px;height:26px;}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>ComfyParamVisualizer</h1>
    <button id="themeToggle" class="toggle" type="button">Theme</button>
  </div>
  <div class="meta">
  </div>
  <div id="sliders"></div>
  <div id="filename"><a id="filenameLink" href="#" target="_blank"></a></div>
  <div id="canvas-wrap"><canvas id="canvas"></canvas></div>
</div>
<script>
(function(){
  const saved=localStorage.getItem("viewer_theme");
  if(saved==="dark"||( !saved && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches)){
    document.documentElement.setAttribute("data-theme","dark");
  }
  document.getElementById("themeToggle").onclick=function(){
    const cur=document.documentElement.getAttribute("data-theme");
    if(cur==="dark"){document.documentElement.removeAttribute("data-theme");localStorage.setItem("viewer_theme","light");}
    else{document.documentElement.setAttribute("data-theme","dark");localStorage.setItem("viewer_theme","dark");}
  };
})();
const data=${meta_json};
const dims=data.dim_values.length;
const curIdx=new Array(dims).fill(0);
const locked=new Array(dims).fill(false);
const canvas=document.getElementById("canvas");
const ctx=canvas.getContext("2d");
const fnameLink=document.getElementById("filenameLink");
const slidersRoot=document.getElementById("sliders");

// Image LRU cache for lazy mode
const CAP=64;
const map=new Map();
const imgs={
  has:(k)=>map.has(k),
  get:(k)=>map.get(k),
  set:(k,img)=>{
    if(map.has(k)) map.delete(k);
    map.set(k,img);
    if(map.size>CAP){
      const oldest=map.keys().next().value;
      const oldImg=map.get(oldest);
      oldImg.src="";
      map.delete(oldest);
    }
  }
};

// Initialize after first image is ready
function initAfterFirstImage(w,h){
  canvas.width=w; canvas.height=h;
  buildUI(); resizeCanvas(); updateImage();
  window.addEventListener("resize",resizeCanvas);
}

// Load one arbitrary image to size the canvas
const firstFname = Object.values(data.lookup)[0];
const probe=new Image();
probe.onload=()=>initAfterFirstImage(probe.naturalWidth, probe.naturalHeight);
probe.onerror=()=>initAfterFirstImage(512,512);
probe.src=data.image_urls[firstFname];

function sliderWidth(n){return Math.min(680,Math.max(140,140+(n-2)*36));}
function buildUI(){
  for(let i=0;i<dims;i++){
    const row=document.createElement("div");row.className="slider-row";
    const lock=document.createElement("input");lock.type="checkbox";
    const label=document.createElement("div");label.className="label-col";label.textContent=data.dim_labels[i];
    const wrap=document.createElement("div");wrap.className="slider-wrap";
    const bubble=document.createElement("div");bubble.className="value-bubble";bubble.textContent=data.dim_values[i][0].d;
    const slider=document.createElement("input");slider.type="range";
    slider.min=0;slider.max=data.dim_values[i].length-1;slider.step=1;slider.value=0;
    slider.style.width=sliderWidth(data.dim_values[i].length)+"px";
    lock.onchange=()=>{locked[i]=lock.checked;slider.disabled=lock.checked;};
    slider.oninput=()=>{if(locked[i])return;curIdx[i]=+slider.value;bubble.textContent=data.dim_values[i][curIdx[i]].d;updateImage();};
    wrap.appendChild(bubble);wrap.appendChild(slider);
    row.appendChild(lock);row.appendChild(label);row.appendChild(wrap);
    slidersRoot.appendChild(row);
  }
}
function key(){return curIdx.map((v,d)=>data.dim_values[d][v].k).join("|");}

let currentUrl=null;
function updateImage(){
  const fname=data.lookup[key()];
  if(!fname){ fnameLink.textContent="No match"; fnameLink.removeAttribute("href"); currentUrl=null; return; }
  const url=data.image_urls[fname];
  let im = imgs.has(fname) ? imgs.get(fname) : null;
  if(im && im.complete){
    drawAndLink(im, url, fname);
    return;
  }
  im = new Image();
  im.onload=()=>{ imgs.set(fname, im); drawAndLink(im, url, fname); };
  im.onerror=()=>{ fnameLink.textContent="Failed to load: "+fname; currentUrl=null; };
  im.src=url;
}

function drawAndLink(im, url, fname){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.drawImage(im,0,0);
  currentUrl=url;
  fnameLink.textContent=fname;
  fnameLink.href=url;
  fnameLink.download=fname;
}

document.getElementById("canvas").addEventListener("contextmenu",e=>{
  e.preventDefault();
  if(currentUrl) window.open(currentUrl,"_blank","noopener,noreferrer");
});

function resizeCanvas(){
  const h=window.innerHeight-document.getElementById("sliders").getBoundingClientRect().bottom-10;
  canvas.style.maxHeight=Math.max(120,h)+"px";
}
</script>
</body>
</html>
""")

    html = html_template.substitute(
        label_em=f"{label_em:.1f}",
        meta_json=json.dumps(meta)
    )

    out_html.write_text(html, encoding="utf-8")
    print("Generated HTML:", out_html)
    print("Note: Viewer uses lazy-load only. Keep the PNGs in place so the HTML can load them.")

if __name__ == "__main__":
    main()
