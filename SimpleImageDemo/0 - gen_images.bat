python "W:\ComfyUI\ComfyParamVisualizer\gen_images.py" ^
  --workflow_api "W:\ComfyUI\ComfyParamVisualizer\SimpleImageDemo\simple_image1_API.json" ^
  --basepath "W:\ComfyUI\ComfyParamVisualizer\SimpleImageDemo" ^
  --server http://127.0.0.1:8188 ^
  --t 3-cfg.txt --as float ^
  --u 3-steps.txt --as int ^
  --save-target 9:filename_prefix.txt ^
  --verbose

  PAUSE