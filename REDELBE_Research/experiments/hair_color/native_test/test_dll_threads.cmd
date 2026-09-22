@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
if not exist build\thread_test mkdir build\thread_test
cl /nologo /EHsc /O2 /MT test_dll_threads.cpp /Fobuild\thread_test\test.obj /Febuild\thread_test\DOA6LR.exe
if errorlevel 1 exit /b 1
build\thread_test\DOA6LR.exe "%CD%\build\REDELBE_LR.asi"
set result=%errorlevel%
popd
exit /b %result%
