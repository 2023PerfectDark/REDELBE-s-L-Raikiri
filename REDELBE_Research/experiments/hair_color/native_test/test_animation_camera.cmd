@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
pushd "%~dp0"
cl /nologo /std:c++17 /EHsc /O2 /MT test_animation_camera.cpp /Fobuild\test_animation_camera.obj /Febuild\test_animation_camera.exe
popd
