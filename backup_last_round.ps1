$ErrorActionPreference = 'Stop'
$source = 'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round'
$stamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
$destination = "$source - Backup $stamp"
$evidence = Join-Path $PSScriptRoot "REDELBE_Research\backups\full_game_$stamp"
if (Get-Process DOA6LR -ErrorAction SilentlyContinue) { throw 'Close Last Round before creating the backup.' }
if (Test-Path -LiteralPath $destination) { throw 'Backup destination already exists.' }
$files = @(Get-ChildItem -LiteralPath $source -Recurse -File -Force)
$directories = @(Get-ChildItem -LiteralPath $source -Recurse -Directory -Force)
if (@(Get-ChildItem -LiteralPath $source -Recurse -Force -Attributes ReparsePoint).Count) { throw 'Reparse points require explicit handling.' }
$bytes = ($files | Measure-Object Length -Sum).Sum
if ((Get-PSDrive G).Free -lt ($bytes + 1GB)) { throw 'Insufficient backup space.' }
New-Item -ItemType Directory -Path $evidence -Force | Out-Null
$statusPath = Join-Path $evidence 'status.json'
$state = [ordered]@{Source=$source;Destination=$destination;Evidence=$evidence;FileCount=$files.Count;Bytes=$bytes;Phase='Copying';VerifiedFiles=0;VerifiedBytes=0;Started=(Get-Date).ToString('o')}
$state | ConvertTo-Json | Set-Content -LiteralPath $statusPath
Write-Output "Destination: $destination"
Write-Output "Evidence: $evidence"
$copyLog = Join-Path $evidence 'robocopy.log'
& robocopy.exe $source $destination /E /COPY:DAT /DCOPY:DAT /R:2 /W:2 /MT:8 /J /XJ /NP /NFL /NDL "/LOG:$copyLog"
$copyCode = $LASTEXITCODE
$state.CopyExitCode = $copyCode
if ($copyCode -ge 8) { $state.Phase='CopyFailed'; $state | ConvertTo-Json | Set-Content -LiteralPath $statusPath; throw "Robocopy failed: $copyCode" }
$state.Phase = 'Verifying SHA256'
$state | ConvertTo-Json | Set-Content -LiteralPath $statusPath
$manifest = [System.Collections.Generic.List[object]]::new()
$lastUpdate = Get-Date
foreach ($file in $files) {
    $relative = $file.FullName.Substring($source.Length + 1)
    $target = Join-Path $destination $relative
    $current = Get-Item -LiteralPath $file.FullName
    $copied = Get-Item -LiteralPath $target
    if ($current.Length -ne $file.Length -or $current.LastWriteTimeUtc -ne $file.LastWriteTimeUtc) { throw "Source changed during backup: $relative" }
    if ($copied.Length -ne $file.Length) { throw "Size mismatch: $relative" }
    $sourceHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    if ($sourceHash -ne $targetHash) { throw "Content mismatch: $relative" }
    $manifest.Add([pscustomobject]@{Path=$relative;Bytes=$file.Length;SHA256=$sourceHash})
    $state.VerifiedFiles++
    $state.VerifiedBytes += $file.Length
    if (((Get-Date) - $lastUpdate).TotalSeconds -ge 10) {
        $state | ConvertTo-Json | Set-Content -LiteralPath $statusPath
        Write-Output "Verified $($state.VerifiedFiles)/$($files.Count) files, $([math]::Round($state.VerifiedBytes/1GB,2))/$([math]::Round($bytes/1GB,2)) GiB"
        $lastUpdate = Get-Date
    }
}
$afterFiles = @(Get-ChildItem -LiteralPath $source -Recurse -File -Force)
$backupFiles = @(Get-ChildItem -LiteralPath $destination -Recurse -File -Force)
if ($afterFiles.Count -ne $files.Count -or $backupFiles.Count -ne $files.Count) { throw 'File count changed or does not match.' }
foreach ($directory in $directories) {
    $relative = $directory.FullName.Substring($source.Length + 1)
    if (-not (Test-Path -LiteralPath (Join-Path $destination $relative) -PathType Container)) { throw "Missing directory: $relative" }
}
foreach ($file in $files) {
    $current = Get-Item -LiteralPath $file.FullName
    if ($current.Length -ne $file.Length -or $current.LastWriteTimeUtc -ne $file.LastWriteTimeUtc) { throw "Source changed during verification: $($file.FullName)" }
}
$manifest | Export-Csv -LiteralPath (Join-Path $evidence 'sha256_manifest.csv') -NoTypeInformation
$state.Phase='Complete'
$state.Completed=(Get-Date).ToString('o')
$state.VerifiedDirectories=$directories.Count
$state | ConvertTo-Json | Set-Content -LiteralPath $statusPath
$state | ConvertTo-Json
