import hashlib,json,shutil,zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'packages/REDELBE_LR_0.3_RC4';payload=out/'REDELBE_LR_Package'
payload.mkdir(parents=True,exist_ok=True)
for name in ('REDELBE_LR_Sync.exe','REDELBE_LR_Launcher.exe','dinput8.dll'):
 shutil.copy2(root/'prototype/build'/name,payload/name)
helper=payload/'REDELBE_LR/bridge_tools';helper.mkdir(parents=True,exist_ok=True)
for file in (root/'prototype/build/kashira_portable_v2').iterdir():
 if file.is_file() and not file.name.startswith('Kashira.Core') and file.suffix!='.pdb':shutil.copy2(file,helper/file.name)
notices=payload/'REDELBE_LR/Notices';notices.mkdir(parents=True,exist_ok=True)
runtime=Path.home()/'.nuget/packages/microsoft.netcore.app.runtime.win-x64/10.0.7'
for name in ('LICENSE.TXT','THIRD-PARTY-NOTICES.TXT'):shutil.copy2(runtime/name,notices/('dotnet-'+name))
shutil.copy2(Path(r'C:\Users\Owner\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\LICENSE.txt'),notices/'Python-LICENSE.txt')
licensefile=root/'tools/build_deps/pyinstaller-6.22.3.dist-info/licenses/COPYING.txt'
if not licensefile.exists():raise FileNotFoundError(licensefile)
shutil.copy2(licensefile,notices/'PyInstaller-COPYING.txt')
(notices/'README.txt').write_text('Kashira and KashiraEditor are user-supplied. Kashira.Core.dll is read from the installed manager locally and is not redistributed here.\n.NET bundle format reference: https://github.com/dotnet/runtime/tree/main/src/installer/managed/Microsoft.NET.HostModel/Bundle\n')
commands={
 'Install REDELBE LR.cmd':'"%~dp0REDELBE_LR_Package\\REDELBE_LR_Sync.exe" install "%~dp0REDELBE_LR_Package" "%~dp0."',
 'Remove REDELBE LR.cmd':'"%~dp0REDELBE_LR_Package\\REDELBE_LR_Sync.exe" uninstall "%~dp0."',
 'Sync REDELBE Layer2.cmd':'"%~dp0REDELBE_LR_Sync.exe" sync "%~dp0."'}
for name,command in commands.items():
 (out/name).write_text('@echo off\n'+command+'\nif errorlevel 1 echo REDELBE LR could not complete the operation. See the error above.\npause\n')
for name,command in {'Sync REDELBE Layer2.cmd':'sync','Remove REDELBE LR.cmd':'uninstall'}.items():
 (payload/name).write_text('@echo off\n"%~dp0REDELBE_LR_Sync.exe" '+command+' "%~dp0."\npause\n')
manifest={p.relative_to(payload).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(payload.rglob('*')) if p.is_file() and p.name!='release_manifest.json'}
(payload/'release_manifest.json').write_text(json.dumps(manifest,indent=2))
(out/'README.txt').write_text('''REDELBE LR 0.3 RC4 — portable preview

Requirements: Windows x64, a legitimate DOA6LR installation, Kashira-win-x64.exe
and KashiraEditor-win-x64.exe placed beside DOA6LR.exe. No Python, .NET SDK,
original DOA6 installation, personal logs, or research files are required.

INSTALL
Extract this ZIP's contents beside DOA6LR.exe (not inside an extra folder).
Close the game and Kashira, then run Install REDELBE LR.cmd.
The installer refuses to overwrite a different dinput8.dll. Resolve that conflict
first; do not blindly replace another loader. Existing REDELBE files are backed up.
An old REDELBE_LR.asi is moved into the installation checkpoint to avoid loading
two REDELBE versions. The new loader is contained entirely in dinput8.dll.

USE
Run REDELBE_LR_Launcher.exe. It prepares enabled Kashira packages before launching.
Steam must be running. If Steam restarts the game, set Steam Launch Options to:
"FULL PATH TO REDELBE_LR_Launcher.exe" %command%
Use your own installation path. Clear that option when removing this loader.
Do not run Kashira Apply or build over packages while the game is running.

Add/remove .ktmod files in _Kashira/Mods or enable/disable them in Kashira profiles.
Launch again to refresh the Layer2 catalog. Start at Vanilla; F and L2/LT cycle
forward, Select/Back backward. In the hair/details menu, these controls cycle
hair/head mods independently and the caption shows the hair slot code.
Hair/head choices start at Vanilla and override overlapping costume assets only
while selected. Random costume selection is supported in Versus and Free Training.
Assets remain on disk until requested; preparation creates disk caches.

TITLE NAME
The title version line includes Raikiri 0.3 RC4. After the first launch, edit
REDELBE_LR/branding.ini in Notepad (save as UTF-8):
[Branding]
Enabled=1
Name=Raikiri
Version=0.3 RC4

Change Name and Version whenever desired; restart the game to apply reliably.
Enabled=0 hides the loader label. Keep names short to fit the native pane.
The game version remains intact. Your branding.ini is preserved during upgrades.

EDITOR
Build ordinary single-slot legacy costume, hair, or head packages into _Kashira/Mods.
The bridge identifies their slot and converts them to Layer2, preserving originals.
Rebuilds replace the package; the next launch converts the new build again.
Explicit marked COS, HAIR, and FACE Layer2 packages are supported too. Optional saved-project paths
in REDELBE_LR/bridge.json must be relative to the game folder.
Texture-only mods without a model, ambiguous multi-slot packages, new resource IDs,
and authored material manifests are not automatically converted to isolated Layer2.
They require an explicit compatible package. Original DOA6 mods are not auto-ports.
Hanabi's experimental restoration and other people's mods are not bundled.

UPDATES
Functions are located using unique complete-function patterns and verified call
relationships. Code movement alone can be handled automatically. Changed code or
layouts may still require a loader update; unmatched patterns disable the loader.
The bridge reads the current game's resource indexes and costume names each time
its inputs change. Never copy old game archives over a new title update.

REMOVE
Close the game/Kashira and run Remove REDELBE LR.cmd from this extracted package.
Matching installed loader files and generated data move to REDELBE_LR_Removed_*.
Projects and mods are preserved. Unchanged automatically converted packages are
restored; edited packages are preserved. Run Kashira Apply afterwards if desired.
Clear a custom Steam Launch Option. Delete the extracted package only after removal.

VALIDATION
Pattern resolution tested against the pre-update build and Ver. 1.11, including
changed-code and ambiguous-match rejection. Ver. 1.11 menus and cycling work;
single-DLL startup also reaches menus without a pre-existing ASI loader.
Install/removal tests preserve user files. This is a release candidate: wider
testing on other PCs and randomization regression testing are still recommended.
''')
archive=out.parent/(out.name+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(out.rglob('*')):
  if p.is_file():z.write(p,p.relative_to(out).as_posix())
print(archive,archive.stat().st_size,'bytes',len(manifest),'runtime files')
