$ErrorActionPreference = 'Stop'
$steamExe = 'D:\Games Only\Steam folder\steam.exe'
$configPath = 'D:\Games Only\Steam folder\userdata\230915170\config\localconfig.vdf'
$gamePath = 'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round - Backup 2026-09-15_210415'
$gameExe = Join-Path $gamePath 'DOA6LR.exe'
if (Get-Process DOA6LR -ErrorAction SilentlyContinue) { throw 'Close Last Round first.' }
if (-not (Test-Path -LiteralPath $gameExe)) { throw 'Test executable missing.' }
$research = Split-Path -Parent $PSScriptRoot
$launcherSource = Join-Path $research 'prototype\build\REDELBE_LR_Launcher.exe'
$launcherTarget = Join-Path $gamePath 'REDELBE_LR_Launcher.exe'
if (-not (Test-Path -LiteralPath $launcherSource)) { throw 'Build the test launcher first.' }
$backupPath = Join-Path $research ('backups\steam_test_launch_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
if (Test-Path -LiteralPath $launcherTarget) { Copy-Item -LiteralPath $launcherTarget -Destination (Join-Path $backupPath 'REDELBE_LR_Launcher.exe') }
Copy-Item -LiteralPath $launcherSource -Destination $launcherTarget
if ((Get-FileHash -LiteralPath $launcherSource).Hash -ne (Get-FileHash -LiteralPath $launcherTarget).Hash) { throw 'Launcher copy hash mismatch.' }
Start-Process -FilePath $steamExe -ArgumentList '-shutdown' -WindowStyle Hidden
$deadline = (Get-Date).AddSeconds(40)
while ((Get-Process steam -ErrorAction SilentlyContinue) -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 500 }
if (Get-Process steam -ErrorAction SilentlyContinue) { throw 'Steam did not exit; configuration was not modified.' }
Copy-Item -LiteralPath $configPath -Destination (Join-Path $backupPath 'localconfig.vdf')
$content = [IO.File]::ReadAllText($configPath)
$blockPattern = '(?ms)^\t{5}"4144680"\r?\n\t{5}\{\r?\n.*?^\t{5}\}'
$blocks = [regex]::Matches($content, $blockPattern)
if ($blocks.Count -ne 1) { throw 'Expected exactly one Last Round app block.' }
$block = $blocks[0]
$optionPattern = '(?m)^(\t{6}"LaunchOptions"\s+)"(?:\\.|[^"\\])*"'
$options = [regex]::Matches($block.Value, $optionPattern)
if ($options.Count -ne 1) { throw 'Expected exactly one launch-option entry.' }
$launch = '"' + $launcherTarget + '" %command%'
$encoded = $launch.Replace('\','\\').Replace('"','\"')
$option = $options[0]
$newOption = $option.Groups[1].Value + '"' + $encoded + '"'
$position = $block.Index + $option.Index
$updated = $content.Substring(0,$position) + $newOption + $content.Substring($position+$option.Length)
$restored = $updated.Substring(0,$position) + $option.Value + $updated.Substring($position+$newOption.Length)
if ($restored -cne $content) { throw 'Unexpected edits beyond launch option.' }
[pscustomobject]@{Game=$gamePath;OriginalEntry=$option.Value;LaunchOptions=$launch;Config=$configPath;Backup=$backupPath} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $backupPath 'change.json')
[IO.File]::WriteAllText($configPath,$updated,[Text.UTF8Encoding]::new($false))
if ([IO.File]::ReadAllText($configPath) -cne $updated) { throw 'Saved configuration verification failed.' }
Write-Output "Launch options saved. Backup: $backupPath"
Start-Process -FilePath $steamExe -ArgumentList '-silent','-applaunch','4144680' -WindowStyle Hidden
