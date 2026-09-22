$ErrorActionPreference='Stop'
$game='G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round'
$research=Split-Path $PSScriptRoot -Parent
$stamp=Get-Date -Format yyyyMMdd_HHmmss
$checkpoint=Join-Path $game ('REDELBE_LR\rollback\private_preview_'+$stamp)
$destination=Join-Path $game ('REDELBE_LR\sets\private_preview_'+$stamp)
New-Item -ItemType Directory -Path $checkpoint | Out-Null
Copy-Item -LiteralPath (Join-Path $game 'dinput8.dll') -Destination $checkpoint
Copy-Item -LiteralPath (Join-Path $game 'REDELBE_LR\active_package.txt') -Destination $checkpoint
Copy-Item -LiteralPath (Join-Path $game 'REDELBE_LR\loader.log') -Destination $checkpoint
foreach($proc in @(Get-Process DOA6LR -ErrorAction SilentlyContinue)) {
 if($proc.Path -eq (Join-Path $game 'DOA6LR.exe')) {
  if(-not $proc.CloseMainWindow()){throw 'Game did not accept normal close'}
  if(-not $proc.WaitForExit(20000)){throw 'Game is still running; installation stopped'}
 }
}
Copy-Item -LiteralPath (Join-Path $research 'packages\hanabi_private_preview_v7') -Destination $destination -Recurse
Copy-Item -LiteralPath (Join-Path $research 'experiments\hair_color\native_test\build\dinput8.dll') -Destination (Join-Path $game 'dinput8.dll') -Force
('sets/'+(Split-Path $destination -Leaf)) | Set-Content -LiteralPath (Join-Path $game 'REDELBE_LR\active_package.txt') -Encoding ascii
Start-Process -FilePath (Join-Path $game 'DOA6LR.exe') -WorkingDirectory $game -WindowStyle Hidden
Write-Output "Preview installed. Checkpoint: $checkpoint"
