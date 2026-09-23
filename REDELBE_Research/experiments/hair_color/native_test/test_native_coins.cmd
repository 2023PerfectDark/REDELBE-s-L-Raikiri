@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
pushd "%~dp0"
cl /nologo /std:c++17 /EHsc /MT test_native_coins.cpp /Fobuild\test_native_coins.obj /Febuild\test_native_coins.exe
if errorlevel 1 exit /b 1
build\test_native_coins.exe ..\..\..\analysis\lr_baseline.bin
if errorlevel 1 exit /b 1
build\test_native_coins.exe ..\..\..\analysis\lr_updated.bin
exit /b %errorlevel%
