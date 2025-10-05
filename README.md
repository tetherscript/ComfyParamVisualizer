# ComfyParamVisualizer

https://github.com/user-attachments/assets/1d18e05f-b783-4fb0-a653-8ae5ba53d2eb

![view_grid1](https://github.com/user-attachments/assets/f4345a6a-4d20-4c17-8dac-824a0ad867dc)

## The problem
So you have ComfyUI and want to generate an image.  There could be 1000 different workflow parameter combinations. Which combination gives you the image you want?  How exactly do they contribute to your image?  You could just use the default parameter settings, but you wonder 'Is there something better?' The only way to find out is to manually tweak the settings, wait for image generation, rinse, repeat. 

This is the least complex image genertion workflow in ComfyUI and is used as it's default workflow.  Each of the highlighted parameters affects the generated image, and usually only several parameter combinations give the best image, many give a so-so image, and the rest give a horrible result.  So which combination of these parameters is best? 
![simple_image1_workflow_1a](https://github.com/user-attachments/assets/da1c611b-0a29-462f-8813-086d8b3959bb)

How much time do you spend looking for the best result?  Tweaking parameters is 90% of what we do in ComfyUI.

XY Plot custom nodes exist that can help understand, and perhaps discover the best parameter settings.  But these can have compatibility issues and can conflict with your other nodes, and they don't work for all workflows.

In a perfect world with infinite GPU speed, we could adjust parameters and instantly see the resulting image.  But alas, no infinite GPU.

## A Solution

With this in mind, ComfyParamVisualizer was created. 
- usable with any workflow
- usable with any ComfyUI installation (no sage, with sage, portable, not portable, Windows, Linux).
- doesn't conflict with any custom nodes, because it is not used within the ComfyUI user interface.

To use it, you
- edit and save your workflow in the ComfyUI editor like usual.  You can close the UI if you want, just leave ComfyUI running in the background.
- define the workflow parameters you want to test ex 'let's test KSampler steps vs cfg'.
- run a python script that calls the built-in ComfyUI webserver. This will generate images based on all combinations of the parameters you provided.  Got 4 steps and 3 cfgs? You going to get 12 images.  This can be huge if you have the time - I have done over 4000 images in one image generation call, gave me time to mow the lawn and wash the car.
- run another script to display the images in a web browser where you can adjust the workflow pamameters with sliders and see the corresponding image instantly.  Just scrub away on those sliders.
- or run a different script that allows you to scrub and optionally create an XY plot.
- You'll be saying 'ohhhh...i get how cfg and steps work now.'
- You can use it on up to 6 dimensions in any node, so that could be complex like: LoraFile * Lora:strength * KSampler:scheduler * KSampler:sampler_name * KSampler:cfg * KSampler:steps.

SCRIPTS, YOU SAY?  SECURITY!
- Yes, there are 3 python scripts and some batch files to call them.  And you are right to question the security aspects of this.  Peruse the scripts, run them sandboxed, whatever helps.  I have included the ChatGPT5 prompts to recreate the entire functionality.  I suggest using these prompts to explore the specifications and tweak these scripts just as you need them. 





