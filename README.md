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

1) To keep this simple, we'll use the default, simple ComfyUI workflow.  But you could use any workflow, even the crazy huge ones.
2) 





