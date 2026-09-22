@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /std:c++17 /EHsc /W4 /MT test_roster_fade.cpp /Fobuild\test_roster_fade.obj /Febuild\test_roster_fade.exe
if errorlevel 1 exit /b 1
build\test_roster_fade.exe
set result=%errorlevel%
popd
exit /b %result%


