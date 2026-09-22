$ErrorActionPreference = 'Stop'
$game = 'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round'
$stage = Join-Path (Split-Path $PSScriptRoot -Parent) 'packages\hanabi_private_main_test'
if (@(Get-Process DOA6LR -ErrorAction SilentlyContinue).Count) { throw 'Close game before installing' }
$outfit = Join-Path $game 'KashiraProjects\REDELBE_LR_Hanabi'
if (Test-Path -LiteralPath $outfit) { throw 'Preserve existing outfit project before installation' }
$hair = Join-Path $game 'KashiraProjects\REDELBE_LR_Hanabi_Hair_Head'
$checkpoint = Join-Path $game ('REDELBE_LR\rollback\hanabi_private_' + (Get-Date -Format yyyyMMdd_HHmmss))
New-Item -ItemType Directory -Path $checkpoint | Out-Null
$configPath = Join-Path $game 'REDELBE_LR\bridge.json'
$hairPackage = Join-Path $game '_Kashira\Mods\REDELBE LR - Hanabi Hair Head.ktmod'
Copy-Item -LiteralPath $configPath -Destination $checkpoint
Copy-Item -LiteralPath $hairPackage -Destination $checkpoint
Copy-Item -LiteralPath (Join-Path $game 'REDELBE_LR\active_package.txt') -Destination $checkpoint
$resolvedHair = (Resolve-Path -LiteralPath $hair).Path
$resolvedCheckpoint = (Resolve-Path -LiteralPath $checkpoint).Path
if (-not $resolvedHair.StartsWith($game + '\') -or -not $resolvedCheckpoint.StartsWith($game + '\REDELBE_LR\rollback\')) { throw 'Unexpected rollback path' }
Move-Item -LiteralPath $resolvedHair -Destination (Join-Path $resolvedCheckpoint 'REDELBE_LR_Hanabi_Hair_Head')
Copy-Item -LiteralPath (Join-Path $stage 'REDELBE_LR_Hanabi_Hair_Head') -Destination $hair -Recurse
Copy-Item -LiteralPath (Join-Path $stage 'REDELBE_LR_Hanabi') -Destination $outfit -Recurse
Copy-Item -LiteralPath (Join-Path $stage '(Hair-Head) Hanabi Hyuga Hair 1 (Adult Byakugan).ktmod') -Destination $hairPackage -Force
Copy-Item -LiteralPath (Join-Path $stage 'REDELBE LR - Hanabi Hyuga Adult.ktmod') -Destination (Join-Path $game '_Kashira\Mods\REDELBE LR - Hanabi Hyuga Adult.ktmod')
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json -AsHashtable
$config.projects['REDELBE LR - Hanabi Hyuga Adult'] = 'KashiraProjects/REDELBE_LR_Hanabi/project.ktproj'
$config.legacy_restoration = 'KashiraProjects/REDELBE_LR_Hanabi/REDELBE_Dependencies/restoration_plan.json'
$config | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $configPath -Encoding utf8
& (Join-Path $game 'REDELBE_LR_Sync.exe') sync $game
if ($LASTEXITCODE -ne 0) { throw "Sync failed; checkpoint: $checkpoint" }
Write-Output "Installed; rollback checkpoint: $checkpoint"
