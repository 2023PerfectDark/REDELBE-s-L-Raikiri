param([ValidateSet('all','keep-mods')][string]$Mode)
$ErrorActionPreference='Stop'
$game=Split-Path -Parent $PSScriptRoot
while ($game -and !(Test-Path -LiteralPath (Join-Path $game 'DOA6LR.exe'))) {
    $parent=Split-Path -Parent $game
    if ($parent -eq $game) { throw 'DOA6LR.exe not found.' }
    $game=$parent
}
if (!$game) { throw 'DOA6LR.exe not found.' }
if (!$Mode) {
    Write-Host 'Uninstall REDELBE LR'
    Write-Host '1 - Delete REDELBE and all content in its program folder.'
    Write-Host '2 - Archive mods and top-level REDELBE LR .txt/.ini files, then uninstall.'
    Write-Host 'DOA6LR and Kashira files will not be deleted.'
    Write-Host 'Any other response cancels.'
    $answer=Read-Host 'Choose 1 or 2'
    if ($answer -eq '1') {$Mode='all'} elseif ($answer -eq '2') {$Mode='keep-mods'} else {exit 0}
}
# Execute a temporary copy so Windows can delete the installed executable.
$temp=Join-Path ([IO.Path]::GetTempPath()) ('REDELBE-Uninstall-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temp | Out-Null
try {
    $exe=Join-Path $temp 'REDELBE_LR_Sync.exe'
    Copy-Item -LiteralPath (Join-Path $game 'REDELBE_LR_Sync.exe') -Destination $exe
    & $exe uninstall $game --mode $Mode
    if ($LASTEXITCODE -ne 0) {throw 'Uninstall stopped. See the error above.'}
    Write-Host 'Uninstall complete.'
} finally {
    $resolved=[IO.Path]::GetFullPath($temp)
    $tempRoot=[IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\')+'\'
    if ($resolved.StartsWith($tempRoot,[StringComparison]::OrdinalIgnoreCase) -and [IO.Path]::GetFileName($resolved).StartsWith('REDELBE-Uninstall-')) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
