python "W:\ComfyUI\ComfyParamVisualizer\gen_images.py" ^
  --workflow_api "W:\ComfyUI\ComfyParamVisualizer\SimpleImage1\simple_image1_API.json" ^
  --basepath "W:\ComfyUI\ComfyParamVisualizer\SimpleImage1" ^
  --server http://127.0.0.1:8188 ^
  --t 3-sampler_name.txt --as string ^
  --u 3-scheduler.txt --as string ^
  --v 3-cfg.txt --as float ^
  --x 3-steps.txt --as int ^
  --save-target 9:filename_prefix.txt ^
  --verbose

  PAUSE