@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
if not exist build mkdir build
cl /nologo /std:c++17 /EHsc /O2 /W4 /MT test_launcher.cpp user32.lib /Fobuild\test_launcher.obj /Febuild\REDELBE_LR_Launcher.exe /link /SUBSYSTEM:WINDOWS /INCREMENTAL:NO
set result=%errorlevel%
popd
exit /b %result%
