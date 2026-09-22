@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /std:c++17 /EHsc /O2 /W4 /MT /LD dinput_proxy.cpp /Fobuild\dinput_proxy.obj /Febuild\dinput8.dll /link /DEF:dinput_proxy.def /INCREMENTAL:NO
set result=%errorlevel%
popd
exit /b %result%
