@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /std:c++17 /EHsc /W4 /MT test_victory_rules.cpp /Fobuild\test_victory_rules.obj /Febuild\test_victory_rules.exe
if errorlevel 1 exit /b 1
build\test_victory_rules.exe
set result=%errorlevel%
popd
exit /b %result%
