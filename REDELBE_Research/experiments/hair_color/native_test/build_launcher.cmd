@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /std:c++17 /EHsc /O2 /MT test_launcher.cpp /Fobuild\launcher.obj /Febuild\REDELBE_LR_Launcher.exe /link /SUBSYSTEM:WINDOWS user32.lib
exit /b %errorlevel%
