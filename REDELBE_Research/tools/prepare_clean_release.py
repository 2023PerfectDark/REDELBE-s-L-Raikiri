from pathlib import Path
import hashlib,json,shutil,zipfile
root=Path(__file__).resolve().parents[1];out=root/'releases/REDELBE_LR_0.3_RC4_Release';out.mkdir(parents=True,exist_ok=False)
stage=root/'analysis/release_staging/REDELBE_LR_0.3_RC4';shutil.copytree(root/'packages/REDELBE_LR_0.3_RC4/REDELBE_LR_Package',stage)
for name in ('dinput8.dll','REDELBE_LR_Sync.exe','REDELBE_LR_Launcher.exe'):shutil.copy2(root/'prototype/build'/name,stage/name)
for name in ('REDELBE.ini','fullmix.ini','random_tracks.txt','settings.schema.json','SETTINGS.md'):shutil.copy2(root/'settings'/name,stage/'REDELBE_LR'/name)
p=stage/'REDELBE_LR/REDELBE.ini';p.write_text(p.read_text(encoding='utf-8-sig').replace('survival_stage = My Stage','survival_stage = default'),encoding='utf8')
# Packaging is allow-listed; no live mods, logs, project paths, caches, or personal branding are read.
(stage/'REDELBE_LR/RRPreview').mkdir(exist_ok=True)
(stage/'REDELBE_LR/RRPreview/README.txt').write_text('Put replacement SRSA banks here, inside one folder per mod. Keep the matching SRST beside streamed SRSA banks. Only one replacement per bank. Close the game, then run Sync REDELBE LR.cmd or Sync RRPreview in SRS. A direct save here from SRS syncs automatically. Original DOA6 audio is not automatically an LR-compatible replacement.\n')
(stage/'REDELBE_LR/bridge_tools/README - INTERNAL.txt').write_text('Required private runtime components. Do not launch, edit, or remove individual files. Use the root Install / Play / Sync / Remove shortcuts.\n')
manifest={p.relative_to(stage).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stage.rglob('*')) if p.is_file() and p.name!='release_manifest.json'}
(stage/'release_manifest.json').write_text(json.dumps(manifest,indent=2))
internal=out/'_REDELBE_Runtime';internal.mkdir()
with zipfile.ZipFile(internal/'runtime.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in stage.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(stage).as_posix())
(internal/'README.txt').write_text('Installer runtime only. Leave this folder intact. You do not need to browse or unpack runtime.zip. Required runtime components are installed automatically. Development/research files are not included.\n')
(internal/'Install.ps1').write_text('''$ErrorActionPreference = 'Stop'
$game = Split-Path -Parent $PSScriptRoot
if (!(Test-Path -LiteralPath (Join-Path $game 'DOA6LR.exe'))) { throw 'Extract this release beside DOA6LR.exe, then run Install REDELBE LR.cmd.' }
$staging = Join-Path ([IO.Path]::GetTempPath()) ('REDELBE-Install-' + [Guid]::NewGuid().ToString('N'))
Expand-Archive -LiteralPath (Join-Path $PSScriptRoot 'runtime.zip') -DestinationPath $staging
try {
    & (Join-Path $staging 'REDELBE_LR_Sync.exe') install $staging $game
    if ($LASTEXITCODE -ne 0) { throw 'Installation failed. See details above. No conflicting loader is replaced automatically.' }
} finally {
    $resolved = [IO.Path]::GetFullPath($staging)
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\\') + '\\'
    if ($resolved.StartsWith($tempRoot,[StringComparison]::OrdinalIgnoreCase) -and ([IO.Path]::GetFileName($resolved)).StartsWith('REDELBE-Install-')) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
''',encoding='utf8')
(out/'Install REDELBE LR.cmd').write_text('@echo off\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0_REDELBE_Runtime\\Install.ps1"\npause\n')
for name,command in [('Play DOA6LR with REDELBE.cmd','"%~dp0REDELBE_LR_Launcher.exe"'),('Sync REDELBE LR.cmd','"%~dp0REDELBE_LR_Sync.exe" sync "%~dp0."'),('Remove REDELBE LR.cmd','"%~dp0REDELBE_LR_Sync.exe" uninstall "%~dp0."')]:
 (out/name).write_text('@echo off\nif not exist "%~dp0REDELBE_LR_Sync.exe" (\n echo Run Install REDELBE LR.cmd first.\n pause\n exit /b 1\n)\n'+command+'\nif errorlevel 1 echo Operation failed. See details above.\npause\n')
user=out/'REDELBE_LR';user.mkdir();(user/'READ ME FIRST.txt').write_text('After installation, edit REDELBE.ini here. Audio replacement banks go in RRPreview. Costume/hair packages go in the game folder _Kashira/Mods. Generated sets, bridge_tools, caches, logs and backup folders are internal runtime data, not mod-install locations.\n')
(user/'RRPreview').mkdir();shutil.copy2(stage/'REDELBE_LR/RRPreview/README.txt',user/'RRPreview/README.txt')
tool=out/'Tools/SRS Audio Studio LR';tool.mkdir(parents=True)
srs=root/'packages/SRS_Audio_Studio_LR_0.3.12'
for name in ('SRS Audio Studio LR.exe','Setup FFmpeg.cmd','Setup FFmpeg.ps1','README.md','README.html'):shutil.copy2(srs/name,tool/name)
# Retain download/build material inside the tool's internal folder, not beside the main buttons.
p=tool/'Setup FFmpeg.ps1';s=p.read_text().replace("Join-Path $PSScriptRoot ('ffmpeg_download_'", "Join-Path $PSScriptRoot ('_runtime/ffmpeg_download_'")
p.write_text(s,encoding='utf8');(tool/'_runtime').mkdir()
(tool/'START HERE.txt').write_text('Run Setup FFmpeg.cmd once (Internet required), then SRS Audio Studio LR.exe. Alternatively place an existing ffmpeg.exe in bin. SRS automatically finds DOA6LR.exe above this Tools folder. Audio Library -> select track -> Open bank in editor -> Replace -> Save new bank. Keep the game closed when syncing. See README.html.\n')
notices=out/'Notices';shutil.copytree(stage/'REDELBE_LR/Notices',notices)
(out/'README (for users).txt').write_text('''REDELBE LR / L-Raikiri 0.3 RC4 — clean release candidate
Includes SRS Audio Studio LR 0.3.12. Tested game version: 1.11.

INSTALL
1. Supply your own DOA6LR, Kashira-win-x64.exe and KashiraEditor-win-x64.exe.
   Put both Kashira executables beside DOA6LR.exe.
2. Extract this ZIP beside DOA6LR.exe. Close the game and Kashira.
3. Run Install REDELBE LR.cmd. It checks hashes and refuses a different dinput8.dll.
4. Run Play DOA6LR with REDELBE.cmd. Steam must be running.
No Python or .NET installation is required. The original DOA6 is not required.
For Steam launch redirection, use your own full path to REDELBE_LR_Launcher.exe
followed by %command% in Steam Launch Options. Clear this when removing REDELBE.

WHERE THINGS GO
REDELBE_LR/REDELBE.ini       Player settings (created by Install).
REDELBE_LR/RRPreview/       Audio replacement banks.
_Kashira/Mods/              LR-compatible costume, hair and head packages.
Tools/SRS Audio Studio LR/  Optional sound editor; run Setup FFmpeg.cmd once.
_REDELBE_Runtime/           Installer data. No manual browsing needed.

CONTROLS
F or L2/LT: next mod. Select/Back: previous mod. Starts at Vanilla.
Hair/head cycling works in the hair menu. Random character selection can
include costume mods in offline Versus/Free Training. F5 toggles battle HUD
when enabled in REDELBE.ini. Custom roster animations are configurable.

AUDIO
Keep SRSA and matching SRST together in a folder under RRPreview.
Only one replacement of each bank can be active. After moving/removing audio,
close the game and click Sync RRPreview in SRS or run Sync REDELBE LR.cmd.
Then restart the game. SRS saves directly into RRPreview synchronize automatically.
SRS volume matching is on by default; Apply selected/all process replacements.
The optional FFmpeg setup downloads its own runtime; no game sounds are bundled.

REMOVE
Close the game/Kashira; run Remove REDELBE LR.cmd. Runtime data is archived
in REDELBE_LR_Removed_*. Mods/projects are preserved. Use Kashira Apply if needed.
Clear custom Steam launch options. The extracted shortcuts, _REDELBE_Runtime,
Tools and documentation can then be removed manually if no longer wanted.
Do not delete _Kashira or your own projects.

LIMITS
Pattern matching tolerates some code movement, but updates can still need a
new loader. Unknown/ambiguous patterns are rejected. Stage/weather Layer2,
private material isolation and automatic original-DOA6 mod ports are not ready.
INI options marked UNAVAILABLE do nothing. Broader-PC validation is pending;
this is a release candidate, not a guarantee of future-update compatibility.
''',encoding='utf8')
(out/'README (for modders).txt').write_text('''REDELBE LR — modder guide
Use KashiraEditor to build LR-compatible costume/hair/head packages and place
them in _Kashira/Mods. Kashira profile enable/disable controls availability.
Run Sync REDELBE LR.cmd or the launcher after adding/removing/rebuilding mods.
Ordinary single-slot model packages can be prepared for Layer2. Texture-only,
ambiguous multi-slot and new-resource-ID packages require compatible authoring.
Do not put original DOA6 Layer2 folders here expecting automatic conversion.

SRS reads current LR audio first; original DOA6 banks can be opened manually.
MP3/WAV/OGG replacement matches destination settings. Mono ADPCM and Vorbis
replacement are supported; multichannel ADPCM currently supports export/preview.
Use existing LR banks to retain game cue IDs. Save creates a new bank folder.

For launcher integration use REDELBE_LR/settings.schema.json and SETTINGS.md.
These are copied by Install. Stable INI keys are retained. LR SUPPORTED marks
implemented settings. Loader branding is deliberately not a player INI option.

Runtime sets, indexes, bridge_tools and internal metadata are generated/managed
by the loader. Never distribute these generated folders as a mod. Public release
contains no personal test mods, game assets, dumps, logs, source workspace or backups.
''',encoding='utf8')
(out/'changelog.txt').write_text('Clean release candidate, 2026-09-18\nCurrent tested pattern loader, Kashira preparation, costume/hair Layer2 cycling, slot labels, roster transitions, F5 HUD toggle, break-blow patch and RRPreview audio support. SRS0.3.12: LR-first library, ENG/JP filters, sortable/movable columns, volume matching, direct bank editor and updated icon.\n')
(root/'analysis/release_staging/paths.json').write_text(json.dumps({'release':str(out),'payload':str(stage)}))
print(out)
