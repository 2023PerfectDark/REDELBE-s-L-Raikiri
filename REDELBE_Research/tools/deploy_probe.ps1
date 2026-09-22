param(
    [ValidateSet('Install','Remove')][string]$Action = 'Install',
    [string]$PackagePath,
    [string]$GamePath = 'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round'
)
$ErrorActionPreference = 'Stop'
$research = Split-Path -Parent $PSScriptRoot
$target = (Resolve-Path -LiteralPath $GamePath -ErrorAction Stop).Path.TrimEnd('\')
$expected = '35E9949D790AFBB963C2A1ED16FECC0F2C4DC214271D5240791404ABB77BC9EA'
if (Get-Process DOA6LR -ErrorAction SilentlyContinue) { throw 'Close Last Round before installing or removing the probe.' }
if ((Get-FileHash -LiteralPath (Join-Path $target 'DOA6LR.exe')).Hash -ne $expected) { throw 'Executable fingerprint changed; reassess compatibility first.' }
$targetDll = Join-Path $target 'REDELBE_LR.asi'
$targetData = Join-Path $target 'REDELBE_LR'
$sourceDll = Join-Path $research 'prototype\build\REDELBE_LR.asi'
if ($PackagePath) {
    $package = (Resolve-Path -LiteralPath $PackagePath).Path
    $packageRoot = (Join-Path $research 'packages') + '\'
    if (-not $package.StartsWith($packageRoot, [StringComparison]::OrdinalIgnoreCase)) { throw 'Package must be inside the research packages directory.' }
    foreach ($required in @('manifest.json','redirects.tsv','baselines.tsv','overlay')) {
        if (-not (Test-Path -LiteralPath (Join-Path $package $required))) { throw "Package missing $required" }
    }
}
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss_fff'
$backup = Join-Path $research "backups\$stamp"
New-Item -ItemType Directory -Path $backup -Force | Out-Null
$baseline = Get-ChildItem -LiteralPath $target -File | Where-Object { $_.Extension -in '.dll','.asi','.exe','.ini','.json' } | ForEach-Object {
    [pscustomobject]@{Name=$_.Name;Length=$_.Length;SHA256=(Get-FileHash -LiteralPath $_.FullName).Hash}
}
$baseline | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $backup 'baseline.json')
if ($Action -eq 'Install') {
    if (Test-Path -LiteralPath $targetDll) { Copy-Item -LiteralPath $targetDll -Destination (Join-Path $backup 'REDELBE_LR.asi') }
    if (Test-Path -LiteralPath $targetData) { Copy-Item -LiteralPath $targetData -Destination (Join-Path $backup 'REDELBE_LR') -Recurse }
    Copy-Item -LiteralPath $sourceDll -Destination $targetDll
    if ((Get-FileHash -LiteralPath $targetDll).Hash -ne (Get-FileHash -LiteralPath $sourceDll).Hash) { throw 'Installed binary hash mismatch' }
    New-Item -ItemType Directory -Path $targetData -Force | Out-Null
    if ($PackagePath) {
        $parts = @('manifest.json','redirects.tsv','baselines.tsv','overlay')
        if (Test-Path -LiteralPath (Join-Path $package 'layer2.tsv')) {
            $parts += @('layer2.tsv','vanilla.tsv','vanilla','Layer2')
        } elseif (Test-Path -LiteralPath (Join-Path $targetData 'layer2.tsv')) {
            throw 'Remove the existing Layer2 package before installing a fixed overlay.'
        }
        foreach ($part in $parts) {
            Copy-Item -LiteralPath (Join-Path $package $part) -Destination $targetData -Recurse -Force
        }
    }
    [pscustomobject]@{Action=$Action;Target=$targetDll;SHA256=(Get-FileHash -LiteralPath $targetDll).Hash;Backup=$backup} | ConvertTo-Json | Tee-Object -FilePath (Join-Path $backup 'deployment.json')
} else {
    # Move only these exact project-owned paths into the workspace backup.
    foreach ($item in @($targetDll,$targetData)) {
        if (Test-Path -LiteralPath $item) {
            $resolved = (Resolve-Path -LiteralPath $item).Path
            if ($resolved -ne $targetDll -and $resolved -ne $targetData) { throw "Unexpected removal path: $resolved" }
            Move-Item -LiteralPath $resolved -Destination $backup
            if (Test-Path -LiteralPath $resolved) {
                if ($resolved -ne $targetDll) { throw 'The overlay folder remains after moving; inspect before any further removal.' }
                $savedDll = Join-Path $backup 'REDELBE_LR.asi'
                if ((Get-FileHash -LiteralPath $resolved).Hash -ne (Get-FileHash -LiteralPath $savedDll).Hash) { throw 'Residual probe differs from backup.' }
                Remove-Item -LiteralPath $resolved
            }
        }
    }
    [pscustomobject]@{Action=$Action;Backup=$backup} | ConvertTo-Json
}
