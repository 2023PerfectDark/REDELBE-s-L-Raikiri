$ErrorActionPreference = 'Stop'
$gameDir = 'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round'
$gameExe = Join-Path $gameDir 'DOA6LR.exe'
$sourceDir = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\experiments\stage_video'))
$sourceDll = Join-Path $sourceDir 'build\dinput8.dll'
$helper = Join-Path $sourceDir 'build\StageVideoPreviewTest.exe'
if (!(Test-Path -LiteralPath $sourceDll) -or !(Test-Path -LiteralPath $helper)) {throw 'Test build missing'}
$checkpoint = Join-Path $gameDir ('REDELBE_LR\install_backups\stage_video_' + (Get-Date -Format yyyyMMdd_HHmmss))
New-Item -ItemType Directory -Path $checkpoint | Out-Null
Copy-Item -LiteralPath (Join-Path $gameDir 'dinput8.dll') -Destination $checkpoint
Copy-Item -LiteralPath (Join-Path $gameDir 'REDELBE_LR\installed_files.json') -Destination $checkpoint
Copy-Item -LiteralPath (Join-Path $gameDir 'REDELBE_LR\REDELBE.ini') -Destination $checkpoint
Get-Process DOA6LR -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $gameExe} | Stop-Process
Start-Sleep -Milliseconds 1500
if (Get-Process DOA6LR -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $gameExe}) {throw 'Game still running'}
$testDir = Join-Path $gameDir 'REDELBE_LR\StageVideoTest'
New-Item -ItemType Directory -Force -Path $testDir,(Join-Path $gameDir 'REDELBE_LR\StageVidPreviews') | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $gameDir 'REDELBE_LR\StageVidPreviews\Random Vanilla Stage-Modded Stage') | Out-Null
Copy-Item -LiteralPath $helper -Destination $testDir -Force
foreach ($name in @('Start Stage Video Preview Test.ps1','Start Stage Video Preview Test.cmd','Stop Stage Video Preview Test.cmd','README.txt')) {
 Copy-Item -LiteralPath (Join-Path $sourceDir $name) -Destination $testDir -Force
}
Copy-Item -LiteralPath $sourceDll -Destination (Join-Path $gameDir 'dinput8.dll') -Force
$iniPath = Join-Path $gameDir 'REDELBE_LR\REDELBE.ini'
$iniText = [IO.File]::ReadAllText($iniPath)
if ($iniText -notmatch '(?im)^\[StageVideoPreviews\]') {
 $extra = [IO.File]::ReadAllText((Join-Path $sourceDir 'audio_settings.ini'))
 [IO.File]::WriteAllText($iniPath,$iniText + "`r`n" + $extra,[Text.UTF8Encoding]::new($false))
}
$manifestPath = Join-Path $gameDir 'REDELBE_LR\installed_files.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$manifest.'dinput8.dll' = (Get-FileHash -LiteralPath $sourceDll -Algorithm SHA256).Hash.ToLowerInvariant()
$manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Output "Checkpoint: $checkpoint"
Write-Output "Installed SHA256: $($manifest.'dinput8.dll')"
Start-Process -FilePath 'D:\Games Only\Steam folder\steam.exe' -ArgumentList '-applaunch','4144680' -WindowStyle Hidden
