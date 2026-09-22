$ErrorActionPreference = 'Stop'
$gameDir = 'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round'
$gameExe = Join-Path $gameDir 'DOA6LR.exe'
$sourceDll = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\prototype\build\dinput8.dll'))
if (!(Test-Path -LiteralPath $sourceDll)) { throw 'Build DLL missing' }
$checkpoint = Join-Path $gameDir ('REDELBE_LR\install_backups\roster_' + (Get-Date -Format yyyyMMdd_HHmmss))
New-Item -ItemType Directory -Path $checkpoint | Out-Null
Copy-Item -LiteralPath (Join-Path $gameDir 'dinput8.dll') -Destination $checkpoint
Copy-Item -LiteralPath (Join-Path $gameDir 'REDELBE_LR\installed_files.json') -Destination $checkpoint
Get-Process DOA6LR -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $gameExe } | Stop-Process
Start-Sleep -Milliseconds 1500
if (Get-Process DOA6LR -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $gameExe }) { throw 'Game still running' }
Copy-Item -LiteralPath $sourceDll -Destination (Join-Path $gameDir 'dinput8.dll') -Force
$manifestPath = Join-Path $gameDir 'REDELBE_LR\installed_files.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$manifest.'dinput8.dll' = (Get-FileHash -LiteralPath $sourceDll -Algorithm SHA256).Hash.ToLowerInvariant()
$manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Output "Checkpoint: $checkpoint"
Write-Output "Installed SHA256: $($manifest.'dinput8.dll')"
Start-Process -FilePath 'D:\Games Only\Steam folder\steam.exe' -ArgumentList '-applaunch','4144680' -WindowStyle Hidden

