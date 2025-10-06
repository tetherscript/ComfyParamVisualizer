#!/usr/bin/env python3
# make_axis_grid_viewer.py
# Viewer generator for ComfyUI dimensioned image sets.
# Supports: single image, 1D grid (X or Y axis), 2D grid (X & Y axes).
# Lazy-load only: images are never embedded; relative URLs are used.
#
# Updates in this version:
# - Eliminate redraw flicker: keep grid structure stable and update <img> src in-place where possible.
# - Grid and background fully respect theme colors.
# - Unique axis choices per picklist; disable slider when set to X or Y.
# - Uniform 10px grid spacing; min image size 256px; horizontal scroll when too many X items.
# - Single-image mode auto-fits in viewport without scrolling.

import json
import re
import argparse
from pathlib import Path
import sys
from string import Template
import os

def parse_args():
    p = argparse.ArgumentParser(
        description="ComfyUI ND image viewer with axis grids (lazy-load only)."
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
        help="Path to output HTML (default: <images>/0000_axis_grid_viewer.html).",
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
        return node_id, prop, vnum, val_token, dotted  # key, display
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
    out_html = resolve_path(output_arg, img_dir / "0000_axis_grid_viewer.html").resolve()
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

    dim_labels = []
    max_label = 0
    for (nid, prop) in dim_signature:
        title = node_titles.get(nid, f"Node {nid}")
        label = f"{title}:{nid}:{prop}"
        dim_labels.append(label)
        max_label = max(max_label, len(label))

    label_em = max(8.0, min(60.0, max_label * 0.62))

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

    html = Template("""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>ComfyParamVisualizer</title>
<style>
:root { --bg:#fff; --fg:#111; --muted:#666; --border:#cfcfcf; --accent:#7a7afe; }
:root[data-theme="dark"]{ --bg:#0d0f13; --fg:#e5e7eb; --muted:#9aa0a6; --border:#2a2f3a; --accent:#7aa2ff; }
body{margin:0;font-family:sans-serif;background:var(--bg);color:var(--fg);}
.container{width:100%;max-width:none;margin:12px auto;padding:0 12px;box-sizing:border-box;}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}
h1{margin:0;font-size:1.05rem;font-weight:600;}
.meta{font-size:0.85rem;color:var(--muted);margin-bottom:8px;}
.toggle{border:1px solid var(--border);background:transparent;color:var(--fg);
       border-radius:8px;padding:4px 8px;cursor:pointer;}

#sliders{border:1px solid var(--border);border-radius:8px;padding:8px 10px 2px 10px;
         background:rgba(127,127,127,0.03);}
.slider-row{display:grid;grid-template-columns:auto ${label_em}em 1fr 110px;
            align-items:center;gap:10px;margin:10px 0;}
.label-col{justify-self:end;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.slider-wrap{display:flex;flex-direction:column;align-items:center;gap:2px;}
.value-bubble{font-size:0.85rem;color:var(--muted);}

/* Theme-aware form controls */
.axis-wrap{display:flex;gap:6px;align-items:center;justify-content:flex-end;}
.axis-wrap select{
  padding:2px 6px;
  border:1px solid var(--border);
  border-radius:6px;
  background:var(--bg);
  color:var(--fg);
}
.axis-wrap option{ background:var(--bg); color:var(--fg); }
input[type=checkbox]{
  width:16px;height:16px;
  accent-color: var(--accent);
  background: var(--bg);
}

/* Grid */
#gridWrap{
  margin-top:10px;border:1px solid var(--border);border-radius:8px;padding:8px;
  overflow-x:auto; overflow-y:auto; width:100%;
  box-sizing:border-box;
  background:var(--bg); /* respect theme */
}
#grid{
  display:grid;
  gap:10px;
  align-items:start;
  grid-auto-rows:auto;
  background:var(--bg); /* respect theme */
}
.hdr{font-size:0.9rem;color:var(--muted);text-align:center;padding:2px 4px;white-space:nowrap;background:var(--bg);}
.yhdr{text-align:right;padding-right:6px;white-space:nowrap;}
.cell{display:flex;flex-direction:column;align-items:center;gap:4px;background:var(--bg);}
.cell a{display:block;border:1px solid var(--border);width:100%;}
.cell img{
  display:block;
  width:100%;
  height:auto;
  object-fit:contain;
  background:#000;
  min-width:256px;
}
.footer{display:none;}
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

  <div id="gridWrap">
    <div id="grid"></div>
    <div class="footer" id="gridHint"></div>
  </div>
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
const axis=new Array(dims).fill("none"); // "none" | "x" | "y"
const slidersRoot=document.getElementById("sliders");
const gridWrap=document.getElementById("gridWrap");
const gridRoot=document.getElementById("grid");
const gridHint=document.getElementById("gridHint");

const sliderEls=[];
const lockEls=[];
const axisSelEls=[];

// Track current grid structure to avoid teardown/rebuild (reduces flicker)
let curStruct = { mode:"", xLen:0, yLen:0 };
let imageCells = []; // Array of <img> elements in row-major order (no headers)

function sliderWidth(n){return Math.min(680,Math.max(140,140+(n-2)*36));}
function buildUI(){
  for(let i=0;i<dims;i++){
    const row=document.createElement("div");row.className="slider-row";

    const lock=document.createElement("input");lock.type="checkbox";
    lock.onchange=()=>{locked[i]=lock.checked;updateDisabledState(i);};
    row.appendChild(lock);
    lockEls.push(lock);

    const label=document.createElement("div");label.className="label-col";label.textContent=data.dim_labels[i];
    row.appendChild(label);

    const wrap=document.createElement("div");wrap.className="slider-wrap";
    const bubble=document.createElement("div");bubble.className="value-bubble";bubble.textContent=data.dim_values[i][0].d;
    const slider=document.createElement("input");slider.type="range";
    slider.min=0;slider.max=data.dim_values[i].length-1;slider.step=1;slider.value=0;
    slider.style.width=sliderWidth(data.dim_values[i].length)+"px";
    slider.oninput=()=>{curIdx[i]=+slider.value;bubble.textContent=data.dim_values[i][curIdx[i]].d;renderGrid();};
    wrap.appendChild(bubble);wrap.appendChild(slider);
    row.appendChild(wrap);
    sliderEls.push(slider);

    const axisWrap=document.createElement("div");axisWrap.className="axis-wrap";
    const axisSel=document.createElement("select");
    ["none","x","y"].forEach(v=>axisSel.add(new Option(v,v)));
    axisSel.value="none";
    axisSel.onchange=()=>{setAxis(i, axisSel.value);};
    axisWrap.appendChild(axisSel);
    row.appendChild(axisWrap);
    axisSelEls.push(axisSel);

    slidersRoot.appendChild(row);

    updateDisabledState(i);
  }
  syncAxisOptions();
}

function updateDisabledState(i){
  const shouldDisable = locked[i] || axis[i] !== "none";
  sliderEls[i].disabled = shouldDisable;
}

function syncAxisOptions(){
  const xOwner = axis.indexOf("x");
  const yOwner = axis.indexOf("y");
  for(let j=0;j<axisSelEls.length;j++){
    const sel = axisSelEls[j];
    for(let k=0;k<sel.options.length;k++){
      const opt = sel.options[k];
      if(opt.value==="x"){
        opt.disabled = (xOwner !== -1 && j !== xOwner);
      } else if(opt.value==="y"){
        opt.disabled = (yOwner !== -1 && j !== yOwner);
      } else {
        opt.disabled = false;
      }
    }
  }
}

function setAxis(i, v){
  axis[i]=v;
  updateDisabledState(i);
  syncAxisOptions();
  // Axes change may alter structure; rebuild if needed
  curStruct.mode=""; // force structure recompute
  renderGrid();
}

function keyFrom(idxOverride){
  const arr=[];
  for(let d=0; d<dims; d++){
    const i = (idxOverride && Object.prototype.hasOwnProperty.call(idxOverride, d)) ? idxOverride[d] : curIdx[d];
    arr.push(data.dim_values[d][i].k);
  }
  return arr.join("|");
}

function fnameFor(idxOverride){
  const k = keyFrom(idxOverride);
  return data.lookup[k];
}

function ensureStructure(hasX, hasY, xLen, yLen){
  let desiredMode = "single";
  if(hasX && hasY) desiredMode="xy";
  else if(hasX) desiredMode="x";
  else if(hasY) desiredMode="y";

  if(curStruct.mode===desiredMode && curStruct.xLen===xLen && curStruct.yLen===yLen){
    return; // no structural change; reuse DOM
  }

  // rebuild structure
  gridRoot.innerHTML="";
  imageCells = [];
  curStruct = { mode:desiredMode, xLen:xLen, yLen:yLen };

  if(desiredMode==="xy"){
    gridRoot.style.gridTemplateColumns = "auto " + Array(xLen).fill("minmax(256px,1fr)").join(" ");
    const makeHdr=(txt, cls)=>{ const d=document.createElement("div"); d.className="hdr "+(cls||""); d.textContent=txt; return d; };
    gridRoot.appendChild(makeHdr("", "yhdr"));
    for(let cx=0; cx<xLen; cx++){ gridRoot.appendChild(makeHdr(data.dim_values[axis.indexOf("x")][cx].d, "")); }
    for(let ry=0; ry<yLen; ry++){
      gridRoot.appendChild(makeHdr(data.dim_values[axis.indexOf("y")][ry].d, "yhdr"));
      for(let cx=0; cx<xLen; cx++){
        const img = makeImgCell();
        imageCells.push(img);
        gridRoot.appendChild(img.parentElement.parentElement);
      }
    }
  } else if(desiredMode==="x"){
    gridRoot.style.gridTemplateColumns = "auto " + Array(xLen).fill("minmax(256px,1fr)").join(" ");
    const makeHdr=(txt, cls)=>{ const d=document.createElement("div"); d.className="hdr "+(cls||""); d.textContent=txt; return d; };
    gridRoot.appendChild(makeHdr("", "yhdr"));
    for(let cx=0; cx<xLen; cx++){ gridRoot.appendChild(makeHdr(data.dim_values[axis.indexOf("x")][cx].d, "")); }
    gridRoot.appendChild(makeHdr("", "yhdr"));
    for(let cx=0; cx<xLen; cx++){
      const img = makeImgCell();
      imageCells.push(img);
      gridRoot.appendChild(img.parentElement.parentElement);
    }
  } else if(desiredMode==="y"){
    gridRoot.style.gridTemplateColumns = "auto minmax(256px,1fr)";
    const makeHdr=(txt, cls)=>{ const d=document.createElement("div"); d.className="hdr "+(cls||""); d.textContent=txt; return d; };
    for(let ry=0; ry<yLen; ry++){
      gridRoot.appendChild(makeHdr(data.dim_values[axis.indexOf("y")][ry].d, "yhdr"));
      const img = makeImgCell();
      imageCells.push(img);
      gridRoot.appendChild(img.parentElement.parentElement);
    }
  } else {
    gridRoot.style.gridTemplateColumns = "minmax(256px,1fr)";
    const img = makeImgCell();
    imageCells.push(img);
    gridRoot.appendChild(img.parentElement.parentElement);
  }
}

function makeImgCell(){
  const cell=document.createElement("div");cell.className="cell";
  const a=document.createElement("a");a.target="_blank";a.rel="noopener noreferrer";
  const im=new Image(); im.loading="lazy"; im.alt="";
  a.appendChild(im);
  cell.appendChild(a);
  // return image element so caller can update src without rebuilding
  return im;
}

function desiredFilenames(hasX, hasY, xDim, yDim, xLen, yLen){
  const list=[];
  if(hasX && hasY){
    for(let ry=0; ry<yLen; ry++){
      for(let cx=0; cx<xLen; cx++){
        const override={}; override[xDim]=cx; override[yDim]=ry;
        list.push(fnameFor(override));
      }
    }
  } else if(hasX){
    for(let cx=0; cx<xLen; cx++){
      const override={}; override[xDim]=cx;
      list.push(fnameFor(override));
    }
  } else if(hasY){
    for(let ry=0; ry<yLen; ry++){
      const override={}; override[yDim]=ry;
      list.push(fnameFor(override));
    }
  } else {
    list.push(fnameFor(null));
  }
  return list;
}

function renderGrid(){
  const xDim = axis.indexOf("x");
  const yDim = axis.indexOf("y");
  const hasX = xDim !== -1;
  const hasY = yDim !== -1;

  const xLen = hasX ? data.dim_values[xDim].length : 1;
  const yLen = hasY ? data.dim_values[yDim].length : 1;

  ensureStructure(hasX, hasY, xLen, yLen);

  // Update images in-place (no grid teardown -> minimal flicker)
  const names = desiredFilenames(hasX, hasY, xDim, yDim, xLen, yLen);
  for(let i=0;i<imageCells.length;i++){
    const im = imageCells[i];
    const fname = names[i];
    const a = im.parentElement;
    if(!fname){
      // missing: blank this cell
      if(im.dataset.loaded!=="missing"){
        im.removeAttribute("src");
        im.dataset.loaded="missing";
        a.removeAttribute("href");
      }
      continue;
    }
    const url = data.image_urls[fname];
    if(a.href !== url){
      a.href = url;
    }
    if(im.getAttribute("src") !== url){
      im.decoding = "async";
      im.src = url; // in-place swap
      im.dataset.loaded="ok";
    }
  }

  // Single-image fit
  if(!hasX && !hasY){
    fitSingleImage();
    window.addEventListener("resize", fitSingleImage, { once: true });
  }
}

function fitSingleImage(){
  const img = gridRoot.querySelector(".cell img");
  if(!img) return;
  const rect = gridWrap.getBoundingClientRect();
  const available = window.innerHeight - rect.top - 24;
  img.style.maxHeight = (available>100 ? available : 100) + "px";
}

buildUI();
renderGrid();
</script>
</body>
</html>
""").substitute(
        label_em=f"{label_em:.1f}",
        meta_json=json.dumps(meta)
    )

    out_html.write_text(html, encoding="utf-8")
    print("Generated HTML:", out_html)
    print("Note: Viewer uses lazy-load only. Keep the PNGs in place so the HTML can load them.")

if __name__ == "__main__":
    main()
