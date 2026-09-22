@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /std:c++17 /EHsc /O2 /MT check_video.cpp /Fobuild\check_video.obj /Febuild\check_video.exe
set result=%errorlevel%
popd
exit /b %result%
