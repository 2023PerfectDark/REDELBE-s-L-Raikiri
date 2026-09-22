@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /std:c++17 /EHsc /O2 /W4 /MT video_preview.cpp /Fobuild\video_preview.obj /Febuild\StageVideoPreviewTest.exe /link /SUBSYSTEM:WINDOWS
set result=%errorlevel%
popd
exit /b %result%
