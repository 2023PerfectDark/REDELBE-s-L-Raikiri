$ErrorActionPreference = 'Stop'
$gameDir = 'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round'
$research = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$checkpoint = Join-Path $gameDir ('REDELBE_LR\install_backups\rrpreview_' + (Get-Date -Format yyyyMMdd_HHmmss))
New-Item -ItemType Directory -Path $checkpoint | Out-Null
foreach ($name in @('dinput8.dll','REDELBE_LR_Sync.exe','REDELBE_LR\installed_files.json','REDELBE_LR\active_package.txt','REDELBE_LR\bridge_state.json')) {
    $target = Join-Path $gameDir $name
    if (Test-Path -LiteralPath $target) { Copy-Item -LiteralPath $target -Destination (Join-Path $checkpoint ([IO.Path]::GetFileName($name))) }
}
$destination = Join-Path $gameDir 'REDELBE_LR\RRPreview\Moka Announcer'
if (Test-Path -LiteralPath $destination) { throw 'Moka RRPreview destination already exists; inspect before replacing' }
Get-Process DOA6LR -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq (Join-Path $gameDir 'DOA6LR.exe') } | Stop-Process
Start-Sleep -Milliseconds 1500
if (Get-Process DOA6LR -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq (Join-Path $gameDir 'DOA6LR.exe') }) { throw 'Main game still running' }
New-Item -ItemType Directory -Path $destination | Out-Null
Copy-Item -LiteralPath (Join-Path $research 'packages\RRPreview_Moka\RRPreview\Moka Announcer\SE1_Common_SV.srsa') -Destination $destination
Copy-Item -LiteralPath (Join-Path $research 'packages\RRPreview_Moka\RRPreview\Moka Announcer\SE1_Common_SV.srst') -Destination $destination
foreach ($name in @('dinput8.dll','REDELBE_LR_Sync.exe')) { Copy-Item -LiteralPath (Join-Path $research ('prototype\build\'+$name)) -Destination (Join-Path $gameDir $name) -Force }
& (Join-Path $gameDir 'REDELBE_LR_Sync.exe') sync $gameDir
if ($LASTEXITCODE -ne 0) { throw "RRPreview synchronization failed. Checkpoint: $checkpoint" }
$manifestPath = Join-Path $gameDir 'REDELBE_LR\installed_files.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
foreach ($name in @('dinput8.dll','REDELBE_LR_Sync.exe')) {
    $manifest | Add-Member -Force -NotePropertyName $name -NotePropertyValue ((Get-FileHash -LiteralPath (Join-Path $gameDir $name) -Algorithm SHA256).Hash.ToLowerInvariant())
}
$manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-Output "Checkpoint: $checkpoint"
Start-Process -FilePath 'D:\Games Only\Steam folder\steam.exe' -ArgumentList '-applaunch','4144680' -WindowStyle Hidden
