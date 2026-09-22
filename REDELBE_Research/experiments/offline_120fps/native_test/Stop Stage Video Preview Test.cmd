@echo off
powershell.exe -NoProfile -Command "$target = Join-Path '%~dp0' 'StageVideoPreviewTest.exe'; Get-Process StageVideoPreviewTest -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $target } | Stop-Process"
