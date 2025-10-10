@echo off
setlocal
pushd "%~dp0"

python "..\make_axis_grid_viewer.py" ^
  --workflow "simple_video_1.json"

popd
PAUSE
