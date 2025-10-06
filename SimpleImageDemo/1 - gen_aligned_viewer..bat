@echo off
setlocal
pushd "%~dp0"

python "..\make_aligned_viewer.py" ^
  --workflow "simple_image1.json"

popd
PAUSE
