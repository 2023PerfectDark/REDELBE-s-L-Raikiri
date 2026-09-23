param([string]$ArchivePath)
$ErrorActionPreference='Stop'
$toolRoot=Split-Path -Parent $PSScriptRoot
$target=Join-Path $toolRoot 'bin'
$exe=Join-Path $target 'ffmpeg.exe'
if(Test-Path -LiteralPath $exe) {
    & $exe -version
    if($LASTEXITCODE -eq 0){Write-Host 'FFmpeg is already installed and working.';exit 0}
    throw 'Existing FFmpeg failed its version check. It was not overwritten.'
}
if(!$ArchivePath) {
    $cached=@(Get-ChildItem -LiteralPath $PSScriptRoot -Directory -Filter 'ffmpeg_download_*' | ForEach-Object {
        $file=Join-Path $_.FullName 'ffmpeg.zip'
        if(Test-Path -LiteralPath $file){Get-Item -LiteralPath $file}
    } | Sort-Object LastWriteTime -Descending)
    if($cached.Count){$ArchivePath=$cached[0].FullName;Write-Host 'Using the existing FFmpeg download.'}
}
if(!$ArchivePath) {
    $ArchivePath=Join-Path $PSScriptRoot 'ffmpeg.zip'
    [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
    Write-Host 'Downloading FFmpeg from gyan.dev...'
    Invoke-WebRequest -UseBasicParsing -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile $ArchivePath
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=[IO.Compression.ZipFile]::OpenRead($ArchivePath)
try {
    $matches=@($zip.Entries | Where-Object {$_.FullName -match '(^|/)bin/ffmpeg\.exe$'})
    if($matches.Count -ne 1){throw 'Downloaded ZIP must contain exactly one bin/ffmpeg.exe.'}
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    # Flatten only known files. Do not extract the long archive directory tree.
    $pending=Join-Path $target 'ffmpeg-setup.exe'
    [IO.Compression.ZipFileExtensions]::ExtractToFile($matches[0],$pending,$true)
    & $pending -version
    if($LASTEXITCODE -ne 0){throw 'Downloaded FFmpeg failed its version check.'}
    foreach($entry in $zip.Entries) {
        $name=[IO.Path]::GetFileName($entry.FullName)
        if($name -in @('LICENSE','LICENSE.txt','README.txt')) {
            [IO.Compression.ZipFileExtensions]::ExtractToFile($entry,(Join-Path $target ('FFmpeg-'+$name)),$true)
        }
    }
    Move-Item -LiteralPath $pending -Destination $exe
    Write-Host 'FFmpeg installed successfully. Open SRS Audio Studio LR.exe.'
} finally {$zip.Dispose()}
