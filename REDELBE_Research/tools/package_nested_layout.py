from pathlib import Path
import zipfile,hashlib,json
root=Path(__file__).resolve().parents[1];release=root/'releases/REDELBE_LR_Alpha_152'
runtime=release/'_REDELBE_Runtime (Not important to you)'
legacy=release/'_REDELBE_Runtime'
if legacy.exists():
    if runtime.exists():raise RuntimeError('Both runtime folders exist; resolve before packaging.')
    legacy.rename(runtime)
(runtime/'Install.ps1').write_bytes((root/'tools/Install-Nested.ps1').read_bytes())
# Refresh the standalone synchronizer and its integrity record in the payload.
payload=runtime/'runtime.zip'
with zipfile.ZipFile(payload) as z:entries={n:z.read(n) for n in z.namelist() if not n.endswith('/')}
entries['REDELBE_LR_Sync.exe']=(root/'prototype/build/REDELBE_LR_Sync.exe').read_bytes()
manifest=json.loads(entries['release_manifest.json'])
manifest['REDELBE_LR_Sync.exe']=hashlib.sha256(entries['REDELBE_LR_Sync.exe']).hexdigest()
entries['dinput8.dll']=(root/'experiments/hair_color/native_test/build/dinput8.dll').read_bytes()
manifest['dinput8.dll']=hashlib.sha256(entries['dinput8.dll']).hexdigest()
schema_key='REDELBE_LR/settings.schema.json'
if schema_key in entries:
    from update_hair_settings import OPTIONS
    schema=json.loads(entries[schema_key])
    for option in OPTIONS:
        row=dict(option,id=option['section']+'.'+option['key'],status='supported',apply='restart',group=option['section'],legacy=False)
        schema['settings']=[e for e in schema['settings'] if e['id']!=row['id']]+[row]
    entries[schema_key]=json.dumps(schema,indent=2).encode()
    manifest[schema_key]=hashlib.sha256(entries[schema_key]).hexdigest()
entries['REDELBE_LR/REDELBE.ini']=(release/'REDELBE LR/REDELBE.ini').read_bytes()
manifest['REDELBE_LR/REDELBE.ini']=hashlib.sha256(entries['REDELBE_LR/REDELBE.ini']).hexdigest()
(release/'Tools/Prepare Hair Colors.exe').write_bytes((root/'packages/Alpha152Tools/Prepare Hair Colors.exe').read_bytes())
video='REDELBE_LR/StageVideoTest/StageVideoPreviewTest.exe'
entries[video]=(root/'experiments/hair_color/native_test/build/StageVideoPreviewTest.exe').read_bytes()
manifest[video]=hashlib.sha256(entries[video]).hexdigest()
entries['release_manifest.json']=json.dumps(manifest,indent=2).encode()
with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in entries.items():z.writestr(name,data)
installation=release/'installation'
installation.mkdir(exist_ok=True)
(installation/'uninstall.ps1').write_bytes((root/'tools/Uninstall-Prompt.ps1').read_bytes())
(installation/'uninstall REDELBE LR.cmd').write_text(r'''@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1"
pause
''')
old_remove=installation/'Remove REDELBE LR.cmd'
if old_remove.exists():old_remove.unlink()
old_public=release/'REDELBE_LR'
if old_public.exists():old_public.rename(release/'REDELBE LR')
for name in ('Install REDELBE LR.cmd','Remove REDELBE LR.cmd'):
    old=release/name
    if old.exists():old.unlink()
(installation/'Install REDELBE LR.cmd').write_text(r'''@echo off
set "runtime="
for /d %%D in ("%~dp0..\*") do if exist "%%~fD\runtime.zip" if exist "%%~fD\Install.ps1" set "runtime=%%~fD"
if not defined runtime (
 echo Required installer runtime is missing. Extract the complete release ZIP.
 pause
 exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%runtime%\Install.ps1"
set "result=%errorlevel%"
if not "%result%"=="0" echo Installation failed. Read the details above.
pause
exit /b %result%
''')
for name,command in [('Play DOA6LR with REDELBE.cmd','"%game%\\REDELBE_LR_Launcher.exe"'),('Sync REDELBE LR.cmd','"%game%\\REDELBE_LR_Sync.exe" sync "%game%"')]:
    ((installation if name.startswith('Remove ') else release)/name).write_text(r'''@echo off
set "game=%~dp0.."
:findgame
if exist "%game%\DOA6LR.exe" goto foundgame
for %%G in ("%game%") do set "current=%%~fG"
for %%G in ("%game%\..") do set "parent=%%~fG"
if /i "%current%"=="%parent%" goto foundgame
set "game=%parent%"
goto findgame
:foundgame
if not exist "%game%\DOA6LR.exe" (
 echo Keep REDELBE's Last Raikiri directly inside the DOA6LR game folder.
 pause
 exit /b 1
)
if not exist "%game%\REDELBE_LR_Sync.exe" (
 echo Run Install REDELBE LR.cmd first.
 pause
 exit /b 1
)
'''+command+'\nif errorlevel 1 pause\n')
p=release/'README (for users).txt';s=p.read_text(encoding='utf-8');s=s.replace('3. Extract this release beside DOA6LR.exe, then run Install REDELBE LR.cmd.','3. Extract REDELBE Last Raikiri into the game folder. Open installation and run Install REDELBE LR.cmd.')
s=s.split('\nFOLDER LAYOUT\n')[0]+'\nFOLDER LAYOUT\nDOA6LR.exe stays in the main game folder. Your editable REDELBE LR folder,\ntools and shortcuts live under REDELBE Last Raikiri. Hidden compatibility\nentry points let existing tools locate the game and mod data. Do not remove\nthose links manually. dinput8.dll must stay beside DOA6LR.exe to load the mod.\n'
s=s.replace('REDELBE Last Raikiri',"REDELBE's Last Raikiri").replace('Open it and run Install REDELBE LR.cmd.','Open installation and run Install REDELBE LR.cmd.')
p.write_text(s,encoding='utf-8')
archive=root/'releases/REDELBE_LR_Alpha_152.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in release.rglob('*'):
        if p.is_file():z.write(p,"REDELBE's Last Raikiri/"+p.relative_to(release).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
archive.with_suffix('.zip.sha256').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
print(archive)
