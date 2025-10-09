@echo off
setlocal
pushd "%~dp0"

python "..\gen_images.py" ^
  --basepath "." ^
  --workflow_api "simple_image1_API.json" ^
  --server http://127.0.0.1:8188 ^
  --s 3-cfg.txt --as float ^
  --t 3-steps.txt --as int ^
  --save-target 10:value:SampleImageDemo ^
  --verbose

popd
PAUSE
