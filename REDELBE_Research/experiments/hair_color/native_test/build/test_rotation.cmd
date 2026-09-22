@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
cl /nologo /EHsc /std:c++17 /FeREDELBE_Research\experiments\hair_color\native_test\build\test_rotation.exe /FoREDELBE_Research\experiments\hair_color\native_test\build\test_rotation.obj REDELBE_Research\experiments\hair_color\native_test\build\test_rotation.cpp
if errorlevel 1 exit /b 1
REDELBE_Research\experiments\hair_color\native_test\build\test_rotation.exe
