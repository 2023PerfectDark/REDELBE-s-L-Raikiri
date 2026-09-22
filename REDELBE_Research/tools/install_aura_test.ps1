$ErrorActionPreference = 'Stop'
$gameDir = 'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round'
$sourceDir = Join-Path $PSScriptRoot '..\experiments\aura\package'
$manifest = Get-Content -LiteralPath (Join-Path $sourceDir 'manifest.json') -Raw | ConvertFrom-Json
$loaderRoot = Join-Path $gameDir 'REDELBE_LR'
$selected = [IO.File]::ReadAllText((Join-Path $loaderRoot 'active_package.txt')).Trim()
if ($selected -ne $manifest.active_package) {throw 'Active package changed; rebuild the test'}
$active = [IO.Path]::GetFullPath((Join-Path $loaderRoot $selected))
if (!$active.StartsWith((Join-Path $loaderRoot 'sets\'),[StringComparison]::OrdinalIgnoreCase)) {throw 'Invalid package path'}
$oldRoot = Join-Path $active $manifest.original_root_target
if ((Get-FileHash -LiteralPath $oldRoot).Hash.ToLowerInvariant() -ne $manifest.baseline_root_sha256) {throw 'Active index changed; rebuild the test'}
$table = Join-Path $active 'redirects.tsv'
$backup = Join-Path $active ('aura_backup_' + (Get-Date -Format yyyyMMdd_HHmmss) + '.tsv')
Copy-Item -LiteralPath $table -Destination $backup
$lines = [IO.File]::ReadAllLines($table)
$newLines = [Collections.Generic.List[string]]::new()
foreach ($line in $lines) {
 if ($line.Replace('\','/').StartsWith("fdata_package/root.rdb`t")) {$newLines.Add("fdata_package/root.rdb`taura_test/root.rdb")}
 elseif ($line -match '^fdata_package[/\\]data[/\\]0x(285cb0c3|f589e402)\.file\t') {throw 'Aura resource already overridden'}
 else {$newLines.Add($line)}
}
foreach ($id in @('285cb0c3','f589e402')) {$newLines.Add("fdata_package/data/0x$id.file`taura_test/data/0x$id.file")}
Get-Process DOA6LR -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq (Join-Path $gameDir 'DOA6LR.exe')} | Stop-Process
Start-Sleep -Milliseconds 1500
if (Get-Process DOA6LR -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq (Join-Path $gameDir 'DOA6LR.exe')}) {throw 'Game still running'}
$target = Join-Path $active 'aura_test'
New-Item -ItemType Directory -Force -Path $target,(Join-Path $target 'data') | Out-Null
Copy-Item -LiteralPath (Join-Path $sourceDir 'root.rdb') -Destination $target -Force
Copy-Item -LiteralPath (Join-Path $sourceDir 'manifest.json') -Destination $target -Force
foreach ($id in @('285cb0c3','f589e402')) {Copy-Item -LiteralPath (Join-Path $sourceDir "data\0x$id.file") -Destination (Join-Path $target 'data') -Force}
[IO.File]::WriteAllLines($table,$newLines,[Text.UTF8Encoding]::new($false))
[IO.File]::WriteAllText((Join-Path $target 'rollback_table.txt'),$backup)
Write-Output "Honoka aura test installed. Rollback table: $backup"
Start-Process -FilePath 'D:\Games Only\Steam folder\steam.exe' -ArgumentList '-applaunch','4144680' -WindowStyle Hidden
