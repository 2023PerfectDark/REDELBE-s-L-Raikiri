$ErrorActionPreference='Stop'
$research=Split-Path -Parent $PSScriptRoot
$game='G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round - Backup 2026-09-15_210415'
$game=(Resolve-Path -LiteralPath $game).Path.TrimEnd('\')
if (Get-Process DOA6LR -ErrorAction SilentlyContinue) { throw 'Close Last Round first.' }
if ((Get-FileHash -LiteralPath "$game\DOA6LR.exe").Hash -ne '35E9949D790AFBB963C2A1ED16FECC0F2C4DC214271D5240791404ABB77BC9EA') { throw 'Game fingerprint changed.' }
$source=Join-Path $research 'packages\kbridge'
$checkpoint=Join-Path $research ('backups\kashira_before_'+(Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $checkpoint | Out-Null
$files=@('REDELBE_LR.asi','REDELBE_LR_Launcher.exe')
foreach($name in $files) { Copy-Item -LiteralPath "$game\$name" -Destination $checkpoint }
Copy-Item -LiteralPath "$game\REDELBE_LR" -Destination $checkpoint -Recurse
Copy-Item -LiteralPath "$research\packages\prototype_02_tools\prototype" -Destination "$checkpoint\caption_source" -Recurse
$hashes=@{}
foreach($name in @('root.rdb','root.rdx','system.rdb','system.rdx')) { $hashes[$name]=(Get-FileHash -LiteralPath "$game\fdata_package\$name").Hash }
$hashes | ConvertTo-Json | Set-Content -LiteralPath "$checkpoint\archive_hashes.json"
$projects=Join-Path $game 'KashiraProjects'
New-Item -ItemType Directory -Path $projects -Force | Out-Null
foreach($item in Get-ChildItem -LiteralPath "$source\KashiraProjects" -Directory) {
    if(Test-Path -LiteralPath (Join-Path $projects $item.Name)) { throw "Project already exists: $($item.Name)" }
}
foreach($item in Get-ChildItem -LiteralPath "$source\Mods" -File) {
    if(Test-Path -LiteralPath "$game\_Kashira\Mods\$($item.Name)") { throw "Package already exists: $($item.Name)" }
}
Copy-Item -Path "$source\KashiraProjects\*" -Destination $projects -Recurse
Copy-Item -Path "$source\Mods\*.ktmod" -Destination "$game\_Kashira\Mods"
Copy-Item -LiteralPath "$source\bridge.json" -Destination "$game\REDELBE_LR\bridge.json"
Copy-Item -LiteralPath "$research\prototype\build\REDELBE_LR_Sync.exe" -Destination $game
$cmd="@echo off`r`n`"%~dp0REDELBE_LR_Sync.exe`" sync `"%~dp0.`"`r`npause`r`n"
[IO.File]::WriteAllText("$game\Sync REDELBE Layer2.cmd",$cmd,[Text.Encoding]::ASCII)
& "$game\REDELBE_LR_Sync.exe" sync $game
if($LASTEXITCODE -ne 0) { throw 'Sync failed. Previous loader and launcher are still installed.' }
foreach($name in $files) {
    Copy-Item -LiteralPath "$research\prototype\build\$name" -Destination "$game\$name" -Force
    if((Get-FileHash -LiteralPath "$research\prototype\build\$name").Hash -ne (Get-FileHash -LiteralPath "$game\$name").Hash) { throw 'Installed binary mismatch' }
}
foreach($name in $hashes.Keys) {
    if((Get-FileHash -LiteralPath "$game\fdata_package\$name").Hash -ne $hashes[$name]) { throw "Archive changed: $name" }
}
[pscustomobject]@{Game=$game;Checkpoint=$checkpoint;Projects=21;ActivePackage=(Get-Content -LiteralPath "$game\REDELBE_LR\active_package.txt")} | ConvertTo-Json | Tee-Object -FilePath "$checkpoint\installation.json"
