# ComfyParamVisualizer

Which ComfyUI workflow parameter combination is best?

https://github.com/user-attachments/assets/1d18e05f-b783-4fb0-a653-8ae5ba53d2eb

![view_grid1](https://github.com/user-attachments/assets/f4345a6a-4d20-4c17-8dac-824a0ad867dc)

> [!TIP]
> You will need to edit the .bat files because they have absolute paths.  The SimpleImageDemo includes 12 generated images, but the generated .html files have absolute paths, so you'll need to recreate them with the scripts. 

## The problem
So you have ComfyUI and want to generate an image.  There could be 1000 different workflow parameter combinations. Which combination gives you the image you want?  How exactly do they contribute to your image?  You could just use the default parameter settings, but you wonder 'Is there something better?' The only way to find out is to manually tweak the settings, wait for image generation, rinse, repeat. 

This is the least complex image genertion workflow in ComfyUI and is used as it's default workflow.  Each of the highlighted parameters affects the generated image, and usually only several parameter combinations give the best image, many give a so-so image, and the rest give a horrible result.  So which combination of these parameters is best? 
![simple_image1_workflow_1a](https://github.com/user-attachments/assets/da1c611b-0a29-462f-8813-086d8b3959bb)

How much time do you spend looking for the best result?  Tweaking parameters is 90% of what we do in ComfyUI.

XY Plot custom nodes exist that can help understand, and perhaps discover the best parameter settings.  But these can have compatibility issues and can conflict with your other nodes, and they don't work for all workflows.

In a perfect world with infinite GPU speed, we could adjust parameters and instantly see the resulting image.  But alas, no infinite GPU.

> [!WARNING]
> Be sure to review the content of the python scripts and html files so you are comfortable with running them in your environment. You can always create new scripts from scratch with the included ChatGPT prompts, and tweak them to suit your needs.

## A Solution

With this in mind, ComfyParamVisualizer was created. 
- usable with any workflow
- usable with any ComfyUI installation (no sage, with sage, portable, not portable, Windows, Linux).
- doesn't conflict with any custom nodes, because it is not used within the ComfyUI user interface.

To use it, you (super-high level overview)
- In the ComfyUI editor, create and save your workflow.
- Edit several .bat and param .txt files.
- Run the .bat files and review your images using the generated .html in your browser.

To use it, you (ok, this is simplified a bit less)
- In the ComfyUI editor, set it to display nodeid's, then edit, save and export as API your workflow.  Take note of which nodes and parameters you want to test (ex. KSampler:3:steps, KSampler:3:cfg). 
- Edit the '0 - gen_images.bat' to reflect the node:parameters you want to test.
- Edit the \params parameter files that contain the parameter values to be tested, with filenames that reflect the node:paramater pair. The .bat file refers to these param files. Also change the paths in the .bat to reflect where you installed the scripts.
- Keep comfyui running. You can close the comfyui editor if you want, but it isn't necessary.  Don't use the ComfyUI editor if you keep it open.
- Run '0 - gen_images.bat'.  It will show info on which params will be be tested.  Each combination will be sent to the ComfyUI built-in webserver and queued and processed. In the ComfyUI console, you'll see the queueing and processing activity. When the processing has completed (you'll know because it doesn't start processing another).  This is the same idea as when you press the Run button in the ComfyUI editor - it queues and processes a single item.
- Now that the images have been generated, copy them to the /params/images folder.
- Run the '1 - gen_aligned_viewer.bat' and/or '2 - gen_axis_grid_viewer.bat' which creates image viewers as .html files in your images folder. 
- Open the .html file in your browser.  You can change the theme (light/dark), lock a slider with the checkbox, and adjust the sliders to see the image that was generated that match the slider settings.  Scrub the sliders back and forth - you'll see how the image changes.
- The grid_viewer html allows you to scrub the sliders, and also specify a slider to be x and/or y axis to give an XY plot.  You can scrub the other sliders and the plot will update.
That's it! Have fun.

> [!TIP]
> You can use it on up to 6 dimensions (t,u,v,w,x,y) in any node, so that could be complex like: LoraFile * Lora:strength * KSampler:scheduler * KSampler:sampler_name * KSampler:cfg * KSampler:steps.  I often test it with 1500+ images, and have tried 4000 and it worked fine, but all the fans on my PC were on full blast by the end.  This would be a perfect thing to throw at a runpod.ai 5090 instance - just let it go crazy for several hours, then download the resulting images and analyze them locally.

# DETAILED INSTRUCTIONS

To keep this simple, we'll use the default, simple ComfyUI workflow in Templates/Getting Started/Image Generation.  It uses a 2GB model, and is the fastest way to generate images as you get used to setting up the visualizer.  But you could use any workflow, even the crazy huge ones.  In my testing, I use an 10 yr old motherboard/CPU 32GB ram, RTX5060Ti-16GB.  I'm pretty sure my old GTX1080 8GB would work as that is what I used to learn ComfyUI.

We'll test the KSampler:cfg vs KSampler:steps and specify 4 cfgs with 3 steps.  This will generate 12 images quickly so you can run the scripts and view them in the browser.

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
  /SimpleImage1 *uses the ksampler scheduler_name, sampler, steps and cfg with approx 1500 images.
    0 - gen_images.bat - for generating the images
    1 - gen_aligned_viewer.bat - for creating the simple viewer
    2 - gen_axis_grid_viewer.bat - for creating the XY plot viewer
    simple_image1.json - your workflow file
    simple_image1_API.json - your workflow API file
    /params
      3-cfg.txt - param values
      3-steps.txt - param values
      3-sampler_name.txt
      3-scheduler.txt
      9-filename_prefix.txt - use this to specify an /output/subfolder for the generated images
      /images *copy the generated images here before creating the viewer
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
```

*For this example, we will modify the contents /SimpleImageDemo folder.*

## 2. In ComfyUI Editor
Go to the settings, search for 'node ID badge Mode' - set to Show all.  Now each node will show it's nodeid, and you'll need this because you'll refer to params as nodeid:paramname, like 3:steps or 25:strength.
<img width="911" height="182" alt="image" src="https://github.com/user-attachments/assets/8a5e9217-64dc-487d-b017-091c255338c0" />

To make sure the workflow is configured correctly, run the workflow and view the resulting image.  Set the seed 'control after generate' to fixed once you find a good seed, or use seed 156680208700286 which is what i used in the demo.
<img width="1056" height="512" alt="image" src="https://github.com/user-attachments/assets/e31030a1-f22e-4f77-9db3-67d2a98d15c6" />

We'll refer to the node and parameter pairs as '3-cfg' (in the param and batch files), and ''3:cfg' (when viewed in the browser).  But they mean the same thing: the cfg property of the node with id=3, which in our case, is a KSampler.  We need to refer by nodeid and not KSampler because you might have multiple ksamplers in a workflow.  Nodeid's are always unique within a workflow.  When we display the nodeid:property in the browser, we'll retrieve the node type or title 'KSampler' from your workflow file and display that as well so you don't need to try to remember what the heck nodeid 3 was referring to.  

<img width="316" height="119" alt="image" src="https://github.com/user-attachments/assets/cff7652e-af65-48fe-bbb9-1d586a602e82" />
<img width="281" height="115" alt="image" src="https://github.com/user-attachments/assets/d4414a37-bd85-4fe3-b83e-fa5944df2b72" />

It even shows up as '3-cfg-8_0' in the image filename ```3-cfg-8_0--3-steps-30_00001_.png```. That image has a KSampler nodeid 3 with a cfg of 8.0. Note that all the params you are testing are embedded in the filename. 

Now copy the workflow json file AND the API version of it to your /SimpleImage1 folder.  Ex: running ComfyUI Embedded on Windows:
- Go to File/SaveAs to save the workflow. Call it 'SimpleImage1'.  It will save to 'ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI\user\default\workflows' as 'simple_image.json'.  This will be used when the html viewer page is created.
- Go to the File/Export(API) and name it simple_image_api.  It will save it to your download folder (on Windows anyways) as 'simple_image_api.json'. This will be used when the image generation request is sent to the ComfyUI built-in webserver.

> [!TIP]
> You can keep the ComfyUI editor open if you like, but it isn't needed from here on.  Don't use it while the images are being generated by the script.

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
Now edit the image generation batch file to reflect YOUR file paths, server address and port and config files.  The available dimensions are t,u,v,w,x,y. Always start at t and work your way down as more dimensions are needed.
- Go to \SimpleImageDemo folder and edit:
0 - gen_images.bat
```
python "W:\ComfyUI\ComfyParamVisualizer\gen_images.py" ^
  --workflow_api "W:\ComfyUI\ComfyParamVisualizer\SimpleImageDemo\simple_image1_API.json" ^
  --basepath "W:\ComfyUI\ComfyParamVisualizer\SimpleImageDemo" ^
  --server http://127.0.0.1:8188 ^
  --t 3-cfg.txt --as float ^
  --u 3-steps.txt --as int ^
  --save-target 9:filename_prefix.txt ^
  --verbose

  PAUSE
```
Now run '0 - gen_images.bat' and you should see 
```W:\ComfyUI\ComfyParamVisualizer\SimpleImageDemo>python "W:\ComfyUI\ComfyParamVisualizer\gen_images.py"   --workflow_api "W:\ComfyUI\ComfyParamVisualizer\SimpleImageDemo\simple_image1_API.json"   --basepath "W:\ComfyUI\ComfyParamVisualizer\SimpleImageDemo"   --server http://127.0.0.1:8188   --t 3-cfg.txt --as float   --u 3-steps.txt --as int   --save-target 9:filename_prefix.txt   --verbose
[INFO] Reading filename_prefix from W:\ComfyUI\ComfyParamVisualizer\SimpleImageDemo\params\9-filename_prefix.txt
[INFO] Folder prefix token (from 9-filename_prefix.txt) = 'SampleImageDemo'
[INFO] Axis t: reading values from W:\ComfyUI\ComfyParamVisualizer\SimpleImageDemo\params\3-cfg.txt (type=float)
[INFO] Axis t: 3 values loaded
[INFO] Axis t -> node 3, input 'cfg', count=3
[INFO] Axis u: reading values from W:\ComfyUI\ComfyParamVisualizer\SimpleImageDemo\params\3-steps.txt (type=int)
[INFO] Axis u: 4 values loaded
[INFO] Axis u -> node 3, input 'steps', count=4
Planned permutations: 1 * 3 * 4 * 1 * 1 * 1 * 1 = 12
[OK]  t=8.0 u=20 -> queued (prefix=SampleImageDemo/3-cfg-8_0--3-steps-20)
[OK]  t=8.0 u=30 -> queued (prefix=SampleImageDemo/3-cfg-8_0--3-steps-30)
[OK]  t=8.0 u=40 -> queued (prefix=SampleImageDemo/3-cfg-8_0--3-steps-40)
[OK]  t=8.0 u=50 -> queued (prefix=SampleImageDemo/3-cfg-8_0--3-steps-50)
[OK]  t=9.0 u=20 -> queued (prefix=SampleImageDemo/3-cfg-9_0--3-steps-20)
[OK]  t=9.0 u=30 -> queued (prefix=SampleImageDemo/3-cfg-9_0--3-steps-30)
[OK]  t=9.0 u=40 -> queued (prefix=SampleImageDemo/3-cfg-9_0--3-steps-40)
[OK]  t=9.0 u=50 -> queued (prefix=SampleImageDemo/3-cfg-9_0--3-steps-50)
[OK]  t=10.0 u=20 -> queued (prefix=SampleImageDemo/3-cfg-10_0--3-steps-20)
[OK]  t=10.0 u=30 -> queued (prefix=SampleImageDemo/3-cfg-10_0--3-steps-30)
[OK]  t=10.0 u=40 -> queued (prefix=SampleImageDemo/3-cfg-10_0--3-steps-40)
[OK]  t=10.0 u=50 -> queued (prefix=SampleImageDemo/3-cfg-10_0--3-steps-50)
Done. Enqueued 12 prompts to http://127.0.0.1:8188. Images folder: W:\ComfyUI\ComfyParamVisualizer\SimpleImageDemo\params\images\SampleImageDemo

W:\ComfyUI\ComfyParamVisualizer\SimpleImageDemo>PAUSE
Press any key to continue . . .
```
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
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 20/20 [00:01<00:00, 18.37it/s]
Prompt executed in 1.41 seconds
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 30/30 [00:01<00:00, 17.97it/s]
Prompt executed in 1.93 seconds
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 40/40 [00:02<00:00, 17.81it/s]
Prompt executed in 2.52 seconds
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 50/50 [00:02<00:00, 17.66it/s]
Prompt executed in 3.11 seconds
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 20/20 [00:01<00:00, 17.32it/s]
Prompt executed in 1.44 seconds
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 30/30 [00:01<00:00, 17.86it/s]
Prompt executed in 1.96 seconds
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 40/40 [00:02<00:00, 17.72it/s]
Prompt executed in 2.52 seconds
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 50/50 [00:02<00:00, 17.62it/s]
Prompt executed in 3.11 seconds
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 20/20 [00:01<00:00, 18.70it/s]
Prompt executed in 1.33 seconds
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 30/30 [00:01<00:00, 18.03it/s]
Prompt executed in 1.93 seconds
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 40/40 [00:02<00:00, 17.70it/s]
Prompt executed in 2.52 seconds
100%|████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████| 50/50 [00:02<00:00, 17.59it/s]
Prompt executed in 3.11 seconds
```

*Don't you wish all image generations were that fast? Omg.*

Now copy the generated images from 
/output/SimpleImageDemo
to
ComfyParamVisualizer\SimpleImageDemo\params\images

<img width="411" height="184" alt="image" src="https://github.com/user-attachments/assets/e6dc8513-e4a3-474f-8b06-e29f713542d0" />

Delete those two repo .html files as those contain bad filepaths.  You'll need to re-create those .html files with the viewer .bat files.

# 4. Generate the viewer html file(s)
You are almost there! Next, edit paths in the 
1 - gen_aligned_viewer.bat
```
python "W:\ComfyUI\ComfyParamVisualizer\make_aligned_viewer.py" "W:\ComfyUI\ComfyParamVisualizer\SimpleImage1\params\images" "W:\ComfyUI\ComfyParamVisualizer\SimpleImage1\simple_image1.json" -o "W:\ComfyUI\ComfyParamVisualizer\SimpleImage1\params\images\0000_aligned_viewer.html"

PAUSE
```

Now run '1 - gen_aligned_viewer.bat' and it will create /params/images/0000_aligned_viewer.html.  Open that .html file in your browser (dbl-click on it) and you will see:

<img width="817" height="609" alt="image" src="https://github.com/user-attachments/assets/c59de184-867a-459c-9cee-b1ce1a9e23a1" />

- Each NodeNameOrTitle:NodeID:Property has a slider for the values you included in the param .txt file.
- Check the checkbox on the left to lock the slider so you don't accidentally change the value.
- Move the sliders and see the changes to your image. Enjoy!

- 










