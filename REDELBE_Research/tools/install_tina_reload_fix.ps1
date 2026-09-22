$ErrorActionPreference = 'Stop'
$research = Split-Path $PSScriptRoot -Parent
$game = 'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round - Backup 2026-09-15_210415'
$exe = Join-Path $game 'DOA6LR.exe'
foreach ($proc in @(Get-Process -Name DOA6LR -ErrorAction SilentlyContinue)) {
    if ($proc.Path -eq $exe) { throw "Close the backup game first (PID $($proc.Id))" }
}
if ((Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash -ne '35e9949d790afbb963c2a1ed16fecc0f2c4dc214271d5240791404abb77bc9ea') { throw 'Unexpected game version' }
$checkpoint = Join-Path $research ('backups\tina_reload_before_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $checkpoint | Out-Null
Copy-Item -LiteralPath (Join-Path $game 'REDELBE_LR.asi') -Destination $checkpoint
Copy-Item -LiteralPath (Join-Path $game 'REDELBE_LR\loader.log') -Destination $checkpoint
Copy-Item -LiteralPath (Join-Path $research 'prototype\build\REDELBE_LR.map') -Destination (Join-Path $checkpoint 'new_build.map')
Copy-Item -LiteralPath (Join-Path $research 'prototype\build\REDELBE_LR.asi') -Destination (Join-Path $game 'REDELBE_LR.asi')
$expected = (Get-FileHash -LiteralPath (Join-Path $research 'prototype\build\REDELBE_LR.asi') -Algorithm SHA256).Hash
$actual = (Get-FileHash -LiteralPath (Join-Path $game 'REDELBE_LR.asi') -Algorithm SHA256).Hash
if ($actual -ne $expected) { throw 'Installed DLL hash mismatch' }
Write-Output "Installed model-default cache correction: $actual"
Write-Output "Previous DLL and crash log: $checkpoint"
