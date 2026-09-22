@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /std:c++17 /EHsc /W4 test_private_route.cpp /Fobuild\test_private_route.obj /Febuild\test_private_route.exe
if errorlevel 1 exit /b 1
build\test_private_route.exe
set result=%errorlevel%
popd
exit /b %result%
