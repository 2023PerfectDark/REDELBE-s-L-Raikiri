@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
cl /nologo /std:c++17 /EHsc /W4 /MT test_battle_hud.cpp /Fobuild\test_battle_hud.obj /Febuild\test_battle_hud.exe
if errorlevel 1 exit /b 1
build\test_battle_hud.exe
set result=%errorlevel%
popd
exit /b %result%


