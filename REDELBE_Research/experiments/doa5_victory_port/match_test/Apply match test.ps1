param([ValidateSet('100','101','102')][string]$Intro, [ValidateSet('120','122','124')][string]$Victory, [switch]$Disable)
$ErrorActionPreference = 'Stop'
$game = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
if (!(Test-Path -LiteralPath (Join-Path $game 'DOA6LR.exe'))) { throw 'Install this folder inside REDELBE_LR first.' }
if (Get-Process DOA6LR -ErrorAction SilentlyContinue) { throw 'Close DOA6LR before changing the animation test.' }
if (!$Disable -and !$Intro) {
    $Intro = Read-Host 'Intro: 100, 101, 102, or Disable'
    if ($Intro -eq 'Disable') { $Disable = $true }
}
if (!$Disable -and !$Victory) { $Victory = Read-Host 'Victory: 120, 122, or 124' }
if (!$Disable -and ($Intro -notin @('100','101','102') -or $Victory -notin @('120','122','124'))) { throw 'Invalid animation number.' }
$target = Join-Path $game 'REDELBE_LR/RRPreview/Kasumi DOA5 Match Test'
if (Test-Path -LiteralPath $target) {
    $backup = Join-Path $PSScriptRoot ('previous/' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
    New-Item -ItemType Directory -Path $backup -Force | Out-Null
    Get-ChildItem -LiteralPath $target -File | ForEach-Object { Move-Item -LiteralPath $_.FullName -Destination $backup }
}
if (!$Disable) {
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    foreach ($profile in @("ENTRY_$Intro", "WIN_$Victory")) {
        Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot $profile) -Filter '*.g1a' -File | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $target }
    }
    $voiceFolder=Join-Path $PSScriptRoot "Voices_${Intro}_${Victory}"
    if(Test-Path -LiteralPath $voiceFolder) {
        Get-ChildItem -LiteralPath $voiceFolder -Filter '*.srsa' -File | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $target }
    }
}
& (Join-Path $game 'REDELBE_LR_Sync.exe') sync $game
if ($LASTEXITCODE -ne 0) { throw 'Sync failed. Do not launch until the sync error is resolved.' }
if ($Disable) { 'Kasumi match test disabled.' } else { "Installed ENTRY $Intro and WIN $Victory. Ready for an offline Versus test." }
