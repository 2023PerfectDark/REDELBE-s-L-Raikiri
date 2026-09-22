$ErrorActionPreference = 'Stop'
$research = Split-Path $PSScriptRoot -Parent
$game = 'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round - Backup 2026-09-15_210415'
$exe = Join-Path $game 'DOA6LR.exe'
foreach ($proc in @(Get-Process -Name DOA6LR -ErrorAction SilentlyContinue)) {
    if ($proc.Path -eq $exe) { throw "Close the backup game first (PID $($proc.Id))" }
}
if ((Get-FileHash -LiteralPath $exe).Hash -ne '35e9949d790afbb963c2a1ed16fecc0f2c4dc214271d5240791404abb77bc9ea') { throw 'Unexpected game version' }
$checkpoint = Join-Path $research ('backups\model_scale_before_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $checkpoint | Out-Null
Copy-Item -LiteralPath (Join-Path $game 'REDELBE_LR.asi') -Destination $checkpoint
Copy-Item -LiteralPath (Join-Path $game 'REDELBE_LR\loader.log') -Destination $checkpoint
$source = Join-Path $research 'prototype\build\REDELBE_LR.asi'
$destination = Join-Path $game 'REDELBE_LR.asi'
Copy-Item -LiteralPath $source -Destination $destination
if ((Get-FileHash -LiteralPath $source).Hash -ne (Get-FileHash -LiteralPath $destination).Hash) { throw 'Installed DLL hash mismatch' }
Write-Output "Installed model scale initialization fix; backup: $checkpoint"
Get-FileHash -LiteralPath $destination
