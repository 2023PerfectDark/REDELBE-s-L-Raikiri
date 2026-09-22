$ErrorActionPreference='Stop'
$research=Split-Path $PSScriptRoot -Parent
$game='G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round'
$exe=Join-Path $game 'DOA6LR.exe'
Get-Process DOA6LR -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exe } | Stop-Process
Start-Sleep -Seconds 2
$checkpoint=Join-Path $game ('REDELBE_LR\install_backups\hair_' + (Get-Date -Format yyyyMMdd_HHmmss))
New-Item -ItemType Directory -Path $checkpoint | Out-Null
foreach($rel in @('dinput8.dll','REDELBE_LR_Sync.exe','REDELBE_LR\bridge.json','REDELBE_LR\installed_files.json','REDELBE_LR\active_package.txt','REDELBE_LR\branding.ini','REDELBE_LR\bridge_tools\REDELBE_Kashira_Prepare.dll','REDELBE_LR\bridge_tools\REDELBE_Kashira_Prepare.exe')) {
 $source=Join-Path $game $rel
 if(Test-Path -LiteralPath $source){$dest=Join-Path $checkpoint $rel;New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force | Out-Null;Copy-Item -LiteralPath $source -Destination $dest}
}
foreach($folder in @('Eve_Ponytail','Hanabi_Hair_Head')) {
 $dest=Join-Path $game ('KashiraProjects\REDELBE_LR_'+$folder)
 if(Test-Path -LiteralPath $dest){throw 'Project already exists; preserve edits before updating'}
 Copy-Item -LiteralPath (Join-Path $research ('packages\hair_layer2_tests\'+$folder)) -Destination $dest -Recurse
}
foreach($name in @('REDELBE LR - Eve Ponytail Hair.ktmod','REDELBE LR - Hanabi Hair Head.ktmod')) {
 $dest=Join-Path $game ('_Kashira\Mods\'+$name)
 if(Test-Path -LiteralPath $dest){throw 'Package already exists'}
 Copy-Item -LiteralPath (Join-Path $research ('packages\hair_layer2_tests\'+$name)) -Destination $dest
}
$configPath=Join-Path $game 'REDELBE_LR\bridge.json'
$config=Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json -AsHashtable
if($config.ContainsKey('legacy_restoration')){throw 'Existing dependencies need merge before installing'}
$config.legacy_restoration='KashiraProjects/REDELBE_LR_Hanabi_Hair_Head/REDELBE_Dependencies/restoration_plan.json'
$config.projects['REDELBE LR - Eve Ponytail Hair']='KashiraProjects/REDELBE_LR_Eve_Ponytail/project.ktproj'
$config.projects['REDELBE LR - Hanabi Hair Head']='KashiraProjects/REDELBE_LR_Hanabi_Hair_Head/project.ktproj'
$config | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $configPath -Encoding utf8
foreach($name in @('dinput8.dll','REDELBE_LR_Sync.exe')){Copy-Item -LiteralPath (Join-Path $research ('prototype\build\'+$name)) -Destination (Join-Path $game $name)}
foreach($file in Get-ChildItem -LiteralPath (Join-Path $research 'prototype\build\kashira_portable_v2') -File) {
 if($file.Name -notlike 'Kashira.Core*' -and $file.Extension -ne '.pdb'){Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $game ('REDELBE_LR\bridge_tools\'+$file.Name))}
}
$branding=Join-Path $game 'REDELBE_LR\branding.ini'
$text=Get-Content -LiteralPath $branding -Raw
$text.Replace('Version=0.3 RC3','Version=0.3 RC4') | Set-Content -LiteralPath $branding -Encoding utf8
$manifestPath=Join-Path $game 'REDELBE_LR\installed_files.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -AsHashtable
foreach($rel in @($manifest.Keys)){$manifest[$rel]=(Get-FileHash -LiteralPath (Join-Path $game $rel) -Algorithm SHA256).Hash.ToLower()}
$manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $manifestPath -Encoding utf8
& (Join-Path $game 'REDELBE_LR_Sync.exe') sync $game
if($LASTEXITCODE -ne 0){throw 'Hair preparation failed; game left closed'}
Write-Output ('Hair Layer2 installation checkpoint: '+$checkpoint)
