@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /std:c++17 /EHsc /O2 /MT test_decode.cpp /Fobuild\test_decode.obj /Febuild\test_decode.exe
if errorlevel 1 exit /b 1
build\test_decode.exe build\decoder_test.mp4 build\audio_test.mp4
set result=%errorlevel%
popd
exit /b %result%
