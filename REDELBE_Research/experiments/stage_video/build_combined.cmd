@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /std:c++17 /DREDELBE_COMBINED /EHsc /O2 /W4 /MT /LD loader.cpp dinput_proxy.cpp /Fobuild\ /Febuild\dinput8.dll /link /DEF:dinput_proxy.def /MAP:build\dinput8.map /INCREMENTAL:NO
set result=%errorlevel%
popd
exit /b %result%
