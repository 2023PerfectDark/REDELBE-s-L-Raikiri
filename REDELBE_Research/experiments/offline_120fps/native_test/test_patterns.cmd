@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /std:c++17 /EHsc /O2 /W4 /MT test_patterns.cpp /Fobuild\test_patterns.obj /Febuild\test_patterns.exe
if errorlevel 1 exit /b 1
build\test_patterns.exe ..\analysis\lr_baseline.bin ..\analysis\lr_updated.bin
set result=%errorlevel%
popd
exit /b %result%
