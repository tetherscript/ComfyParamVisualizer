# ComfyParamVisualizer

Which ComfyUI workflow parameter combination is best?  Use the visualizer to find it.

https://github.com/user-attachments/assets/643010be-6cb1-4581-ae36-ceac92412540

> [!TIP]
> Quick win: You can try the viewer right now. Just copy the repo to your pc and open the ComfyParamVisualizer\SimpleImage1\params\images .html files to view the 12 images in that folder.

## The problem
So you have ComfyUI and want to generate an image.  There are thousands of different workflow parameter combinations. Which combination gives you the image you want?  How exactly do they contribute to your image?  You could just use the default parameter settings, but you wonder 'Is there something better?' The only way to find out is to manually tweak the settings, wait for image generation, rinse, repeat. 

This is the least complex image genertion workflow in ComfyUI and is used as it's default workflow.  Each of the highlighted parameters affects the generated image, and usually only several parameter combinations give the best image, many give a so-so image, and the rest give a horrible result. 

There are 11 parameter dimensions in this simple workflow.  That's a lot of combinations.  So which combination of these parameters is best? 
![cui1](https://github.com/user-attachments/assets/025d93ac-5311-41e0-a81b-5c93f3e008c4)


How much time do you spend looking for the best result?  Tweaking parameters and clicking Run is 90% of what we do in ComfyUI.

XY Plot custom nodes exist that can help understand, and perhaps discover the best parameter settings.  But these can have compatibility issues and can conflict with your other nodes, and they don't work for all workflows.

In a perfect world with infinite GPU speed, we could adjust parameters and instantly see the resulting image.  But alas, no infinite GPU.

> [!WARNING]
> Be sure to review the content of the python scripts and html files so you are comfortable with running them in your environment. You can always create new scripts from scratch with the included ChatGPT prompts, and tweak them to suit your needs.

## A Solution

With this in mind, ComfyParamVisualizer was created. 
- usable with any workflow
- usable with any ComfyUI installation (no sage, with sage, portable, not portable, Windows, Linux).
- doesn't conflict with any custom nodes, because it is not used within the ComfyUI user interface.

> [!TIP]
> Terminology alert: 'Scrubbing'. The grabbing of a slider and moving it back and forth to change the values quickly, originally referred to scrubbing back and forth in a video player. Scrubbing those params will help you understand ComfyUI.
![scrub1](https://github.com/user-attachments/assets/c6983cf5-a8a3-43d0-9ba6-d582f4547c79)

### High-level overview
- In the ComfyUI editor, create and save your workflow.
- Edit several .bat and param .txt files.
- Run the .bat files to generate the images and create .html viewers for your images.

> [!TIP]
> You can use it on up to 7 dimensions (s,t,u,v,x,y,z) in any combination of node properties, so that could do something like : LoraFile * Lora:strength * KSampler:scheduler * KSampler:sampler_name * KSampler:cfg * KSampler:steps * somethingelse.  I usually test it with 1500+ images.  This would be a perfect thing to throw at a runpod.ai rtx5090 instance - just let it go crazy for several hours, then download the resulting images and analyze them locally.  Much could be learned from that.

# DETAILED INSTRUCTIONS

To keep this simple, we'll use the default, simple ComfyUI workflow in Templates/Getting Started/Image Generation, as shown in the above screenshot.  It uses a 2GB model, and is the fastest way to generate images as you get used to setting up the visualizer.  But you could use any workflow, even the crazy huge ones.  In my testing, I use a 10 year old motherboard/CPU 32GB ram, RTX5060Ti-16GB.  I'm pretty sure my old GTX1080 8GB would work as that is what I used to learn ComfyUI.

We'll test the KSampler:cfg vs KSampler:steps and specify 4 cfgs with 3 steps.  This will generate 12 images quickly so you can run the scripts and view them in the browser.

Load this template in ComfyUI

<img width="421" height="421" alt="image" src="https://github.com/user-attachments/assets/87983351-c861-471e-972c-e8b2b2902be1" />

## 1. The Visualizer files and folders
Grab a copy of this repo.  

```
/ComfyParamVisualizer
  gen_images.py - the image generation script.
  make_aligned_viewer.py - the basic html viewer creation script.
  make_axis_grid_viewer.py - an advanced html viewer creation script that includes an XY Plot.
  /1Misc
    ChatGPT5Prompt_for_gen_images_py.txt - for recreating the image generation script with ChatGPT5.
    ChatGPT5Prompt_for_make_aligned_viewer_py.txt - for recreating the basic viewer script with ChatGPT5.
    ChatGPT5Prompt_recreate_axis_grid_viewer.txt - for recreating the grid viewer script with ChatGPT5.
    ChatGPTStart.jpg - a good way to start tweaking the script, in ChatGPT5.
    dump_picklist.bat - calls dump_picklist.py
    dump_picklist.py - a helper for getting a node property list, like scheduler names so you don't have to enter them manually.
    dump_picklist_CHATGPT.txt - for recreating this script in ChatGPT5.
    sampler_names.txt - output from dump_picklist_py
    scheduler.txt - output from dump_picklist_py
  /SimpleImageDemo *uses the ksampler steps and cfg with 12 images.
    0 - gen_images.bat - for generating the images
    1 - gen_aligned_viewer.bat - for creating the simple viewer
    2 - gen_axis_grid_viewer.bat - for creating the XY plot viewer
    simple_image1.json - your workflow file
    simple_image1_API.json - your workflow API file
    /params
      3-cfg.txt - param values
      3-steps.txt - param values
      9-filename_prefix.txt - use this to specify an /output/subfolder for the generated images
      /images *copy the generated images here before creating the viewer
        *.png
        *.html - the viewer files you will generate
```

*For this example, we will modify the contents /SimpleImageDemo folder.*

## 2. In ComfyUI Editor
Go to the settings, search for 'node ID badge Mode' - set to Show all.  Now each node will show it's nodeid, and you'll need this because you'll refer to params as nodeid:paramname, like 3:steps or 25:strength.
<img width="911" height="182" alt="image" src="https://github.com/user-attachments/assets/8a5e9217-64dc-487d-b017-091c255338c0" />

To make sure the workflow is configured correctly, run the workflow and view the resulting image.  Set the seed 'control after generate' to fixed once you find a good seed, or use seed 156680208700286 which is what i used in the demo.
<img width="1056" height="512" alt="image" src="https://github.com/user-attachments/assets/e31030a1-f22e-4f77-9db3-67d2a98d15c6" />

We'll refer to the node and parameter pairs as '3-cfg' (in the param and batch files), and ''3:cfg' (when viewed in the browser).  But they mean the same thing: the cfg property of the node with id=3, which in our case, is a KSampler.  We need to refer by nodeid and not KSampler because you might have multiple ksamplers in a workflow.  Nodeid's are always unique within a workflow.  When we display the nodeid:property in the browser, we'll retrieve the node type or title 'KSampler' from your workflow file and display that as well so you don't need to try to remember what the heck nodeid 3 was referring to.  

<img width="305" height="134" alt="image" src="https://github.com/user-attachments/assets/13ab3abd-b27a-4946-98d7-08dbf6d324ea" />
<img width="217" height="99" alt="image" src="https://github.com/user-attachments/assets/951242dd-464a-4fb2-b215-8428a7477fef" />
<img width="281" height="115" alt="image" src="https://github.com/user-attachments/assets/d4414a37-bd85-4fe3-b83e-fa5944df2b72" />

It even shows up as '3-cfg-8_0' in the image filename ```3-cfg-8_0--3-steps-30_00001_.png```. That image has a KSampler nodeid 3 with a cfg of 8.0. Note that all the params you are testing are embedded in the filename. 

Now copy the workflow json file AND the API version of it to your /SimpleImage1 folder.  Ex: running ComfyUI Embedded on Windows:
- Go to File/SaveAs to save the workflow. Call it 'SimpleImage1'.  It will save to 'ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI\user\default\workflows' as 'simple_image.json'.  This will be used when the html viewer page is created.
- Go to the File/Export(API) and name it simple_image_api.  It will save it to your download folder (on Windows anyways) as 'simple_image_api.json'. This will be used when the image generation request is sent to the ComfyUI built-in webserver.

> [!TIP]
> Keep the ComfyUI console running, however don't use the ComfyUI editor while generating images with the following script.

## 3. Generate the images
We need to tell it exactly which node property values to use:

- Go to \SimpleImageDemo\params folder and edit:
3-cfg.txt
```
8.0
9.0
10.0
```

- Go to \SimpleImageDemo\params folder and edit:
3-steps.txt
```
20
30
40
50
```

- Nodeid 9 is the Save Image node, and we'll use that to specify the /output/subfolder in which the generated images will be placed.  Go to \SimpleImageDemo\params folder and edit:
9-filename_prefix.txt
```
SampleImageDemo
```

NOTE: If the image generation fails due to ComfyUI crashing (usually due to a bad combination of parameters it really doesn't like), the next time you try to generate images it will try to resume where it left off so you don't have to start completely over.

> [!TIP]
> When you generate images, it will look in ComfyParamVisualizer\SimpleImageDemo\params\images to see if the image already exists.  If it exists, it will skip it.  So for a full regeneration, remove all .pngs and .html files from this folder.

* gen_images.py parameters (from ChatGPT5Prompt_for_gen_images_py.txt).
`--server` (default `http://127.0.0.1:8188`)
`--client-id` (optional; default to a freshly generated UUID4 string)
Axis specifiers (all optional except `--s` and `--t`, which are **required**): `--s`, `--t`, `--u`, `--v`, `--x`, `--y`, `--z`
`--as` (repeatable): consumed in global axis order (`s, t, u, v, x, y, z`) for each **provided** axis. Accept values `auto`, `int`, `float`, `string`, or `str` (treat `str` as `string`). If a provided axis has no corresponding `--as`, default to `auto`.
`--save-target` (required): `<nodeId>:filename_prefix.txt`. Read `<basepath>/params/<nodeId>-filename_prefix.txt` to get the folder token (trimmed). This node **must** exist and is the only SaveImage node whose `filename_prefix` the script may modify.
`--dry-run` (flag): perform all planning, logging, and cleanup reporting without performing any HTTP requests.
`--verbose` (flag): enables detailed logging (axis file reads, value counts, cleaned/ skipped files, assignments, etc.).

Now edit the image generation batch file to list the dimensions, data types and save target node.
- Go to `\SimpleImageDemo` and edit `0 - gen_images.bat`:
```
@echo off
setlocal
pushd "%~dp0"

python "..\gen_images.py" ^
  --basepath "." ^
  --workflow_api "simple_image1_API.json" ^
  --server http://127.0.0.1:8188 ^
  --s 3-cfg.txt --as float ^
  --t 3-steps.txt --as int ^
  --save-target 9:filename_prefix.txt ^
  --verbose

popd
PAUSE
```
Now run `0 - gen_images.bat` and you should see output similar to:
```
[INFO] Reading filename_prefix from D:\VSCODE\2\ComfyParamVisualizer\SimpleImageDemo\params\9-filename_prefix.txt
[INFO] Prefix token (from 9-filename_prefix.txt) = 'SampleImageDemo'
[INFO] Axis s: reading values from D:\VSCODE\2\ComfyParamVisualizer\SimpleImageDemo\params\3-cfg.txt (type=float)
[INFO] Axis s: 3 values loaded
[INFO] Axis s -> node 3, input 'cfg', count=3
[INFO] Axis t: reading values from D:\VSCODE\2\ComfyParamVisualizer\SimpleImageDemo\params\3-steps.txt (type=int)
[INFO] Axis t: 4 values loaded
[INFO] Axis t -> node 3, input 'steps', count=4
[INFO] Images folder D:\VSCODE\2\ComfyParamVisualizer\SimpleImageDemo\params\images\SampleImageDemo does not exist; skipping cleanup.
Planned permutations: 3 * 4 * 1 * 1 * 1 * 1 * 1 = 12
[OK]  s=8.0 t=20 -> queued (prefix=SampleImageDemo/3-cfg-8_0--3-steps-20)
[OK]  s=8.0 t=30 -> queued (prefix=SampleImageDemo/3-cfg-8_0--3-steps-30)
[OK]  s=8.0 t=40 -> queued (prefix=SampleImageDemo/3-cfg-8_0--3-steps-40)
[OK]  s=8.0 t=50 -> queued (prefix=SampleImageDemo/3-cfg-8_0--3-steps-50)
[OK]  s=9.0 t=20 -> queued (prefix=SampleImageDemo/3-cfg-9_0--3-steps-20)
[OK]  s=9.0 t=30 -> queued (prefix=SampleImageDemo/3-cfg-9_0--3-steps-30)
[OK]  s=9.0 t=40 -> queued (prefix=SampleImageDemo/3-cfg-9_0--3-steps-40)
[OK]  s=9.0 t=50 -> queued (prefix=SampleImageDemo/3-cfg-9_0--3-steps-50)
[OK]  s=10.0 t=20 -> queued (prefix=SampleImageDemo/3-cfg-10_0--3-steps-20)
[OK]  s=10.0 t=30 -> queued (prefix=SampleImageDemo/3-cfg-10_0--3-steps-30)
[OK]  s=10.0 t=40 -> queued (prefix=SampleImageDemo/3-cfg-10_0--3-steps-40)
[OK]  s=10.0 t=50 -> queued (prefix=SampleImageDemo/3-cfg-10_0--3-steps-50)
Done. Enqueued 12 prompts to http://127.0.0.1:8188. Images folder: D:\VSCODE\2\ComfyParamVisualizer\SimpleImageDemo\params\images\SampleImageDemo
Press any key to continue . . .
```

Want a rehearsal without generating anything? Add `--dry-run` to the batch file to preview the plan, cleanup actions, and sample filenames before posting prompts to ComfyUI.

This is good.  You may see 'path not found' kind of errors, so check your paths in the .bat again if that happens.

Meanwhile, your ComfyUI console shows this:
```
got prompt
got prompt
got prompt
got prompt
got prompt
got prompt
got prompt
got prompt
got prompt
got prompt
got prompt
got prompt
model weight dtype torch.float16, manual cast: None
model_type EPS
Using pytorch attention in VAE
Using pytorch attention in VAE
VAE load device: cuda:0, offload device: cpu, dtype: torch.bfloat16
CLIP/text encoder model load device: cuda:0, offload device: cpu, current: cpu, dtype: torch.float16
Requested to load SD1ClipModel
loaded completely 13549.8 235.84423828125 True
Requested to load BaseModel
loaded completely 13265.83067779541 1639.406135559082 True
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 20/20 [00:01<00:00, 12.12it/s]
Requested to load AutoencoderKL
loaded completely 11354.61699295044 159.55708122253418 True
Prompt executed in 4.05 seconds
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 30/30 [00:01<00:00, 17.86it/s]
Prompt executed in 1.96 seconds
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 40/40 [00:02<00:00, 17.53it/s]
Prompt executed in 2.56 seconds
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 50/50 [00:02<00:00, 17.55it/s]
Prompt executed in 3.13 seconds
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 20/20 [00:01<00:00, 18.62it/s]
Prompt executed in 1.34 seconds
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 30/30 [00:01<00:00, 17.79it/s]
Prompt executed in 1.95 seconds
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 40/40 [00:02<00:00, 17.63it/s]
Prompt executed in 2.53 seconds
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 50/50 [00:02<00:00, 17.52it/s]
Prompt executed in 3.12 seconds
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 20/20 [00:01<00:00, 18.57it/s]
Prompt executed in 1.34 seconds
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 30/30 [00:01<00:00, 17.94it/s]
Prompt executed in 1.93 seconds
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 40/40 [00:02<00:00, 17.69it/s]
Prompt executed in 2.54 seconds
100%|██████████████████████████████████████████████████████████████████████████████████████████████████████| 50/50 [00:02<00:00, 17.47it/s]
Prompt executed in 3.13 seconds
```

*Don't you wish all image generations were that fast? Omg.*

The PNGs arrive in `SimpleImageDemo\params\images\<folder_token>` automatically. No manual copying is needed—leave them in place so the viewers can load them.

Delete the two HTML files shipped in the repo (they contain placeholder paths) and regenerate them with the viewer batch files to get links that match your machine.

# 4. Generate the viewer html file(s)
You are almost there! The viewer batch files now assume the repository layout, so you usually only need to point them at the workflow JSON. For example, `1 - gen_aligned_viewer.bat` ships as:
```
@echo off
setlocal
pushd "%~dp0"

python "..\make_aligned_viewer.py" ^
  --workflow "simple_image1.json"

popd
PAUSE
```

Now run `1 - gen_aligned_viewer.bat` and it will create `params/images/0000_aligned_viewer.html`.  Open that HTML file in your browser (double-click it) and you will see:

<img width="817" height="609" alt="image" src="https://github.com/user-attachments/assets/c59de184-867a-459c-9cee-b1ce1a9e23a1" />

- Each NodeNameOrTitle:NodeID:Property has a slider for the values you included in the param .txt file.
- Check the checkbox on the left to lock the slider so you don't accidentally change the value.
- Move the sliders and see the changes to your image. Enjoy!

`2 - gen_axis_grid_viewer.bat` follows the same pattern—by default it runs `python "..\make_axis_grid_viewer.py" --workflow "simple_image1.json"` so the images folder and output name are inferred for you. Run it to generate the grid/XY viewer.

We put this in a separate viewer because only using it for scrubbing can cause some flickering/redraw issues on some browsers.  

Just select the sliders to use as the X and Y axis.  If there were more than two sliders, you could still scrub the non-axis sliders, causing the XY plot to regenerate as you scrub.
<img width="955" height="887" alt="image" src="https://github.com/user-attachments/assets/85777dc5-f188-4fab-b79e-6a4be7527c8b" />

# 5. Complete

That's it! Rinse, repeat with your favorite workflow.  Crush that GPU.  Rejoice in knowing a bit more about how all those workflow parameters affect your images.

> [!TIP]
> You can print your html page to pdf!
 
RussDev

Tetherscript











