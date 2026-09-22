$ErrorActionPreference='Stop'
$research=Split-Path -Parent $PSScriptRoot
$game='G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round - Backup 2026-09-15_210415'
if(Get-Process DOA6LR -ErrorAction SilentlyContinue){throw 'Close the game first.'}
$checkpoint=Join-Path $research ('backups\native_kashira_before_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $checkpoint | Out-Null
foreach($part in @('REDELBE_LR_Sync.exe','REDELBE_LR\active_package.txt','REDELBE_LR\bridge_state.json')) {
 Copy-Item -LiteralPath (Join-Path $game $part) -Destination $checkpoint
}
$helper=Join-Path $game 'REDELBE_LR\bridge_tools'
New-Item -ItemType Directory -Path $helper -Force | Out-Null
Copy-Item -Path "$research\prototype\build\kashira_prepare\*" -Destination $helper -Force
Copy-Item -LiteralPath "$research\prototype\build\REDELBE_LR_Sync.exe" -Destination $game -Force
& "$game\REDELBE_LR_Sync.exe" sync $game
if($LASTEXITCODE -ne 0){throw 'Native costume preparation failed. See REDELBE_LR/kashira_prepare.log.'}
Write-Output "Previous bridge checkpoint: $checkpoint"
