$ErrorActionPreference = 'Stop'
$game = Split-Path -Parent $PSScriptRoot
while ($game -and !(Test-Path -LiteralPath (Join-Path $game 'DOA6LR.exe'))) {
    $parent = Split-Path -Parent $game
    if ($parent -eq $game) { $game = $null; break }
    $game = $parent
}
if (!$game) { throw 'Put REDELBE''s Last Raikiri inside your DOA6LR game folder, then run Install again.' }
$game = [IO.Path]::GetFullPath($game)
foreach ($required in @('Kashira-win-x64.exe','KashiraEditor-win-x64.exe')) {
    if (!(Test-Path -LiteralPath (Join-Path $game $required))) { throw "Put $required beside DOA6LR.exe first." }
}
if (Get-Process DOA6LR -ErrorAction SilentlyContinue) { throw 'Close DOA6LR before installing.' }
$visible = Join-Path $game 'REDELBE''s Last Raikiri'
$data = Join-Path $visible 'REDELBE LR'
$alias = Join-Path $game 'REDELBE_LR'
$oldData = Join-Path $visible 'REDELBE_LR'
$formerData = Join-Path $game 'REDELBE Last Raikiri\REDELBE_LR'
if (Test-Path -LiteralPath $oldData) {
    if (![IO.Path]::GetFullPath($oldData).StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid migration path.' }
    if (Test-Path -LiteralPath $data) {
        $saved=Join-Path $PSScriptRoot ('Before migration '+(Get-Date -Format yyyyMMdd_HHmmss))
        Move-Item -LiteralPath $data -Destination $saved
    }
    Move-Item -LiteralPath $oldData -Destination $data
}
foreach ($target in @($visible,$data,$alias)) {
    if (![IO.Path]::GetFullPath($target).StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid installation path.' }
}
New-Item -ItemType Directory -Path $visible -Force | Out-Null
$existing = Get-Item -LiteralPath $alias -Force -ErrorAction SilentlyContinue
if ($existing -and !($existing.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
    # Preserve the existing working configuration during an upgrade.
    if (Test-Path -LiteralPath $data) {
        $saved = Join-Path $visible ('Before migration '+(Get-Date -Format yyyyMMdd_HHmmss))
        Move-Item -LiteralPath $data -Destination $saved
    }
    Move-Item -LiteralPath $alias -Destination $data
    $existing = $null
}
if ($existing) {
    $actual = [IO.Path]::GetFullPath([string]$existing.Target)
    if ($actual -eq $oldData -or $actual -eq $formerData) {
        # Delete only the old junction, never its target contents.
        [IO.Directory]::Delete($alias)
        New-Item -ItemType Junction -Path $alias -Target $data | Out-Null
        $actual = $data
    }
    if ($actual -ne $data) { throw 'Existing REDELBE_LR link points elsewhere. It was not changed.' }
} else {
    New-Item -ItemType Directory -Path $data -Force | Out-Null
    New-Item -ItemType Junction -Path $alias -Target $data | Out-Null
}
$staging = Join-Path ([IO.Path]::GetTempPath()) ('REDELBE-Install-' + [Guid]::NewGuid().ToString('N'))
$internal = Join-Path $PSScriptRoot 'Data'
New-Item -ItemType Directory -Path $internal -Force | Out-Null
foreach ($name in @('bridge_tools','install_backups','Notices','bridge.json','installed_files.json','settings.schema.json')) {
    $old = Join-Path $data $name
    $new = Join-Path $internal $name
    if (Test-Path -LiteralPath $old) {
        if (Test-Path -LiteralPath $new) { throw "Both old and new copies exist for $name. No files overwritten." }
        if (![IO.Path]::GetFullPath($old).StartsWith($game+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid internal migration path.' }
        Move-Item -LiteralPath $old -Destination $new
    }
}
try {
    Expand-Archive -LiteralPath (Join-Path $PSScriptRoot 'runtime.zip') -DestinationPath $staging
    # Windows refuses overwriting hidden files with the sync tool's copy routine.
    foreach ($name in @('REDELBE_LR_Launcher.exe','REDELBE_LR_Sync.exe','Sync REDELBE Layer2.cmd','Remove REDELBE LR.cmd')) {
        $path = Join-Path $game $name
        if (Test-Path -LiteralPath $path) { $item=Get-Item -LiteralPath $path -Force; $item.Attributes=$item.Attributes -band (-bnot [IO.FileAttributes]::Hidden) }
    }
    & (Join-Path $staging 'REDELBE_LR_Sync.exe') install $staging $game
    if ($LASTEXITCODE -ne 0) { throw 'Installation failed. Read the error above; the game was not started.' }
    # Root compatibility entry points remain available to every existing tool.
    foreach ($name in @('REDELBE_LR','REDELBE_LR_Launcher.exe','REDELBE_LR_Sync.exe','Sync REDELBE Layer2.cmd','Remove REDELBE LR.cmd')) {
        $path = Join-Path $game $name
        if (Test-Path -LiteralPath $path) { $item=Get-Item -LiteralPath $path -Force; $item.Attributes=$item.Attributes -bor [IO.FileAttributes]::Hidden }
    }
    Write-Output "Ready. Editable files are in $data"
    Write-Output 'Use Play DOA6LR with REDELBE.cmd in REDELBE''s Last Raikiri.'
} finally {
    $resolved = [IO.Path]::GetFullPath($staging)
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if ($resolved.StartsWith($tempRoot,[StringComparison]::OrdinalIgnoreCase) -and ([IO.Path]::GetFileName($resolved)).StartsWith('REDELBE-Install-') -and (Test-Path -LiteralPath $resolved)) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
