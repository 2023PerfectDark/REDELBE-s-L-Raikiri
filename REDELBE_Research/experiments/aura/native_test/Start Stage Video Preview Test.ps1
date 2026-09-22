$ErrorActionPreference = 'Stop'
$gameDir = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$gameExe = Join-Path $gameDir 'DOA6LR.exe'
$gameProcess = Get-Process DOA6LR -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $gameExe} | Select-Object -First 1
if (!$gameProcess) {throw 'Start this DOA6LR game copy first, then start the video preview test.'}
$videoDir = Join-Path $gameDir 'REDELBE_LR\StageVidPreviews'
Start-Process -FilePath (Join-Path $PSScriptRoot 'StageVideoPreviewTest.exe') -ArgumentList @($gameProcess.Id,('"' + $videoDir + '"')) -WindowStyle Hidden
