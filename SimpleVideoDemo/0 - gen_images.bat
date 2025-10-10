@echo off
setlocal
pushd "%~dp0"

python "..\gen_images.py" ^
  --basepath "." ^
  --workflow_api "simple_video_1_API.json" ^
  --server http://192.168.50.16:8188 ^
  --s 104-shift.txt --as float ^
  --t 103-shift.txt --as float ^
  --save-target 126:value:SimpleVideoDemo ^
  --verbose

popd
PAUSE
