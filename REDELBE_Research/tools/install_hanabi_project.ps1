$ErrorActionPreference = 'Stop'
$research = Split-Path $PSScriptRoot -Parent
$game = 'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round - Backup 2026-09-15_210415'
$exe = Join-Path $game 'DOA6LR.exe'
foreach ($proc in @(Get-Process -Name DOA6LR -ErrorAction SilentlyContinue)) {
 if ($proc.Path -eq $exe) { throw "Close the backup game first (PID $($proc.Id))" }
}
if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash -ne '35e9949d790afbb963c2a1ed16fecc0f2c4dc214271d5240791404abb77bc9ea') { throw 'Unexpected game version' }
$source = Join-Path $research 'packages\hanabi_project_ready'
$destination = Join-Path $game 'KashiraProjects\REDELBE_LR_Hanabi'
$name = 'REDELBE LR - Hanabi Hyuga Adult'
$package = Join-Path $game ('_Kashira\Mods\' + $name + '.ktmod')
if ((Test-Path -LiteralPath $destination) -or (Test-Path -LiteralPath $package)) { throw 'Hanabi target already exists; preserve user edits before updating' }
$configPath = Join-Path $game 'REDELBE_LR\bridge.json'
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json -AsHashtable
if ($config.ContainsKey('legacy_restoration')) { throw 'Existing restoration plan needs an explicit merge' }
$checkpoint = Join-Path $research ('backups\hanabi_before_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $checkpoint | Out-Null
foreach ($relative in @('REDELBE_LR_Sync.exe','REDELBE_LR\bridge.json','REDELBE_LR\active_package.txt','REDELBE_LR\bridge_state.json')) {
 Copy-Item -LiteralPath (Join-Path $game $relative) -Destination $checkpoint
}
Copy-Item -LiteralPath $source -Destination $destination -Recurse
Copy-Item -LiteralPath (Join-Path $research ('packages\'+$name+'.ktmod')) -Destination $package
foreach ($file in Get-ChildItem -LiteralPath $source -Recurse -File) {
 $relative = [IO.Path]::GetRelativePath($source,$file.FullName)
 if ((Get-FileHash -LiteralPath $file.FullName).Hash -ne (Get-FileHash -LiteralPath (Join-Path $destination $relative)).Hash) { throw "Copy verification failed: $relative" }
}
$config.projects[$name] = 'KashiraProjects/REDELBE_LR_Hanabi/project.ktproj'
$config.legacy_restoration = 'KashiraProjects/REDELBE_LR_Hanabi/REDELBE_Dependencies/restoration_plan.json'
$config | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $configPath -Encoding utf8
Copy-Item -LiteralPath (Join-Path $research 'prototype\build\REDELBE_LR_Sync.exe') -Destination (Join-Path $game 'REDELBE_LR_Sync.exe')
& (Join-Path $game 'REDELBE_LR_Sync.exe') sync $game
if ($LASTEXITCODE -ne 0) { throw "Preparation failed; checkpoint preserved at $checkpoint" }
Write-Output "Installed project: $destination\project.ktproj"
Write-Output "Previous bridge checkpoint: $checkpoint"
