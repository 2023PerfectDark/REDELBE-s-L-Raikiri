@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
cl /nologo /std:c++17 /EHsc /O2 /MT REDELBE_Research\experiments\hair_color\native_test\build\test_port_body.cpp /FeREDELBE_Research\experiments\hair_color\native_test\build\test_port_body.exe /FoREDELBE_Research\experiments\hair_color\native_test\build\test_port_body.obj
