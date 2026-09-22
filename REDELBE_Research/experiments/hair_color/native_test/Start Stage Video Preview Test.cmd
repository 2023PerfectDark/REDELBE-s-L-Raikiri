@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start Stage Video Preview Test.ps1"
if errorlevel 1 pause
