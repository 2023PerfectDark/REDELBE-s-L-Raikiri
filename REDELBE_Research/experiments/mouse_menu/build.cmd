@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
if not exist build mkdir build
cl /nologo /std:c++17 /EHsc /O2 /W4 /MT /LD loader.cpp /Fobuild\loader.obj /Febuild\REDELBE_LR.asi /link /INCREMENTAL:NO /MAP:build\REDELBE_LR.map /OUT:build\REDELBE_LR.asi
set result=%errorlevel%
popd
exit /b %result%
