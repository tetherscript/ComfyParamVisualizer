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
- works with image and video workflows

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
Open the 0-gen_images.bat
Edit as needed.  Then run it.
```
pushd "%~dp0"

python "..\gen_images.py" ^
  --basepath "." ^
  --workflow_api "simple_image1_API.json" ^
  --server http://127.0.0.1:8188 ^
  --s 3-cfg.txt --as float ^
  --t 3-steps.txt --as int ^
  --save-target 9:filename_prefix:SampleImageDemo ^
  --verbose

popd
PAUSE
```
Note: the --save-target could also be: 
```
--save-target 10:value:SampleImageDemo
```
which dumps the filename_prefix into any node that can accept a string. In this case it is a String primitive node, which in turn is used to set the filename_prefix of a Save Image node.  By setting this one node, the workflow can re-use this single string node to set the filename_prefix in multiple nodes, like when you save a video, and also a single frame from that video to be used as a thumbnail, both with the same filename, but different extensions.  This is needed to view videos in the html viewers.
![filename_prefix](https://github.com/user-attachments/assets/eddc07aa-3f90-4955-b57b-eecb33e28417)

## 4. Video
Generating video files that can be displayed in the viewer requires that you generate a thumbnail/placeholder/poster .png file for the video file .mp4.  But which frame of the video will you use?  We have included a solution for this:
1) Use a simple custom node in 1Misc/select_image_by_index.py that allows you to specify the zero-based index of the image that you want to save as the thumbnail.  You can use another method, but the image must be saved with the filename_prefix from #2 below.
2) Use a build-in string primitive node to receive the subfolder, and then connect the output of that node to the filename_prefix of your Save Image and Save Video nodes.
From the SimpleImageDemo workflow
<img width="1715" height="1650" alt="image" src="https://github.com/user-attachments/assets/5404d0dc-a1b1-43c0-8cfa-37ff8f8d89e2" />

## 5. Generate the axis grid viewer html file
Edit `2 - gen_axis_grid_viewer.bat` and point it to your workflow file (not the api one).
```
@echo off
setlocal
pushd "%~dp0"

python "..\make_axis_grid_viewer.py" ^
  --workflow "simple_image1.json"

popd
PAUSE
```
Now run `2 - gen_axis_grid_viewer.bat` and it will create `params/images/0000_axis_grid_viewer.html`.  Open that HTML file in your browser (double-click it) and you will see:
<img width="1745" height="1565" alt="image" src="https://github.com/user-attachments/assets/348b8a3e-ce24-4e37-9aec-d75ab02fadc7" />

Just select the sliders to use as the X and Y axis.  If there were more than two sliders, you could still scrub the non-axis sliders, causing the XY plot to regenerate as you scrub.  We put this in a separate viewer because only using it for scrubbing can cause some flickering/redraw issues on some browsers.  

## 6. Complete

That's it! Rinse, repeat with your favorite workflow.  Crush that GPU.  Rejoice in knowing a bit more about how all those workflow parameters affect your images.

> [!TIP]
> You can print your html page to pdf!
> 
> Click on an image in the viewer to load it into a separate tab, where you can drag it into the ComfyUI editor to recreate the workflow that made the image.
>
> Use the dump_picklist script and batch file from the 1Misc folder to generate lists of parameter value strings, like all the ksampler sampler_names, which can be a long list.  You can then copy/paste that into a param file.
>
> Check the /1Misc folder to find the ChatGPT prompts that contain the full specs, including explanations of the parameters.  It's a good read.


You made it this far. Join us in Discord:

https://discord.gg/8FkFYpxvhG
 
RussDev

Tetherscript











