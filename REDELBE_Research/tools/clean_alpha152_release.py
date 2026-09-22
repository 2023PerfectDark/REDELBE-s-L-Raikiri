"""Remove private research narrative and consolidate the public distribution."""
from pathlib import Path
import hashlib,json,shutil,zipfile,datetime
root=Path(__file__).resolve().parents[1]
release=root/'releases/REDELBE_LR_Alpha_152'
archive=root/'releases/REDELBE_LR_Alpha_152.zip'
backup=root/'analysis/release_archive'
backup.mkdir(parents=True,exist_ok=True)
if archive.exists():shutil.copy2(archive,backup/('Alpha152_before_cleanup_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'.zip'))
runtime=release/'_REDELBE_Runtime/runtime.zip'
with zipfile.ZipFile(runtime) as z:payload={n:z.read(n) for n in z.namelist() if not n.endswith('/')}

notes='''[REDELBE LR (Last Raikiri) Update ver. Alpha 152]
-Automatic mod synchronization when starting through the REDELBE launcher.
-Layer2 costume and hair/head switching with F, LT/L2 and Back/Select.
-Mods start unloaded until selected; supported random selection can choose mods.
-Kashira package support and private asset preparation for compatible mods.
-Beta hair colors with saved choices and Break Blow color inheritance.
-Mouse menu navigation, wardrobe rotation, and stage scrolling/dragging.
-Configurable roster transitions, slot labels and battle HUD toggle.
-Offline AI versus AI, pattern rewards and optional local cosmetic tickets.
-Stage video previews with optional audio and music-volume control.
-Configurable character aura and custom sound support.
-Birthday notices based only on the computer's local date.
-Animation browser with dedicated cameras and free camera controls.
-Slow, smooth, repeating update-notice scrolling.
-Editable title branding and update messages; original developer notices preserved.
-SRS 0.3.14: SRSA/SRST pair handling and missing-companion file selection.
-Local hair-color and animation-library setup tools.
-Recognition of Lost Paradise Oboro resource names.
'''
(release/'REDELBE_LR/update_info.txt').write_text(notes,encoding='utf8')
payload['REDELBE_LR/update_info.txt']=notes.encode()
(release/'changelog.txt').write_text(notes+'''
PUBLIC ALPHA LIMITATIONS
-Tested with DOA6LR 1.11; future updates can require a loader update.
-Private isolation depends on compatible resources; shared fallback can conflict.
-Original DOA6 mods need porting. Stage/weather mod compatibility is incomplete.
-DOA5 animation ports and their facial/teleport research assets are not included.
-Other Katana-engine audio variants are not universally supported.
''',encoding='utf8')

modder=release/'README (for modders).txt'
modder.write_text('''REDELBE LR Alpha 152 — Modder guide

MODS
Build LR-compatible packages with KashiraEditor and place them in _Kashira/Mods.
Loose LR Layer2 folders go in REDELBE_LR/Layer2. Launch through REDELBE after
adding, removing or rebuilding mods; synchronization runs before the game.
Original DOA6 mods require porting. Do not distribute generated sets or caches.
Keep project redelbe_layer2.json metadata when present.

ISOLATION
Supported character mods receive separate model, material and texture references.
Unsupported cloning falls back to shared redirects, which may still conflict.
Hair/head selection takes precedence over the costume for the parts it replaces.
Inspect synchronization errors when a package cannot be prepared.

AURAS
Add [Aura] enabled = true or false to the character mod.ini to override the
global setting. Hair/head overrides costume; omitted settings inherit defaults.
A persistent sidecar can use REDELBE_LR/Layer2/<exact mod caption>/mod.ini.
Enter a new match after changes. AuraSound controls the custom loop separately;
the loop follows Game SE and pause. Supply your own compatible WAV.

SETTINGS AND BRANDING
REDELBE.ini contains player settings. branding.ini sets the title-screen label.
update_info.txt and update_info.ini control the release message and scrolling.
birthdays.ini contains editable birthday dates. The computer date is used locally.
Launcher authors can extract settings.schema.json and SETTINGS.md from
_REDELBE_Runtime/Modder Reference.zip. These are optional integration references.

AUDIO
Use SRS with LR banks. Streamed banks require the matching SRSA and SRST.
MP3/WAV/OGG replacement follows the supported destination format. Keep both
bank files together. Other Katana-engine layouts may be unsupported.

LOCAL SETUP
Tools/Prepare Hair Colors.exe generates the palette from the user's game.
Tools/Prepare Animation Library.exe builds the browser library locally.
Neither tool needs a development workspace or Python installation.
''',encoding='utf8')

internal=release/'_REDELBE_Runtime'
with zipfile.ZipFile(internal/'Modder Reference.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name in ('SETTINGS.md','settings.schema.json'):
        p=release/'REDELBE_LR'/name
        if p.exists():z.write(p,name)
with zipfile.ZipFile(internal/'Licenses.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in (release/'Notices').rglob('*'):
        if p.is_file():z.write(p,p.relative_to(release/'Notices').as_posix())
    p=release/'Tools/SRS Audio Studio LR/NOTICE - tkinterdnd2.txt'
    if p.exists():z.write(p,'SRS-tkinterdnd2.txt')

remove=['SHA256SUMS.json','_REDELBE_Runtime/verification.json',
 'REDELBE_LR/AURA_OPTIONS.md','REDELBE_LR/README Automatic Layer2 Isolation.md',
 'REDELBE_LR/SETTINGS.md','REDELBE_LR/settings.schema.json',
 'Tools/SRS Audio Studio LR/SRS Audio Studio LR 0.3.13.exe',
 'Tools/SRS Audio Studio LR/README.md','Tools/SRS Audio Studio LR/UPDATE 0.3.14.txt',
 'Tools/SRS Audio Studio LR/NOTICE - tkinterdnd2.txt','Tools/SRS Audio Studio LR/_runtime/README.txt']
for name in remove:
    p=release/name
    if p.is_file():p.unlink()
for p in (release/'Notices').rglob('*'):
    if p.is_file():p.unlink()
if (release/'Notices').exists() and not any((release/'Notices').iterdir()):(release/'Notices').rmdir()

# Keep the setup button visible while its implementation lives with internal files.
tool=release/'Tools/SRS Audio Studio LR'
p=tool/'Setup FFmpeg.ps1'
if p.exists():
    s=p.read_text().replace("$target = Join-Path $PSScriptRoot 'bin'","$toolRoot = Split-Path -Parent $PSScriptRoot\n$target = Join-Path $toolRoot 'bin'").replace("('_runtime/ffmpeg_download_'","('ffmpeg_download_'")
    (tool/'_runtime').mkdir(exist_ok=True)
    (tool/'_runtime/Setup FFmpeg.ps1').write_text(s)
    p.unlink()
p=tool/'Setup FFmpeg.cmd';p.write_text(p.read_text().replace('%~dp0Setup FFmpeg.ps1','%~dp0_runtime\\Setup FFmpeg.ps1'))
(tool/'START HERE.txt').write_text('SRS Audio Studio LR 0.3.14\nRun Setup FFmpeg.cmd once, then SRS Audio Studio LR.exe. See README.html for audio editing. Open either SRSA or SRST; a streamed bank always needs the matching pair. Missing companions can be selected. Licenses are in ../../_REDELBE_Runtime/Licenses.zip.\n')

for name in ('REDELBE_LR/AURA_OPTIONS.md','REDELBE_LR/README Automatic Layer2 Isolation.md','REDELBE_LR/Birthday list and sources.txt'):
    payload.pop(name,None)
# Required test-named binaries retain their runtime paths, but remain compressed.
payload['release_manifest.json']=json.dumps({n:hashlib.sha256(data).hexdigest() for n,data in payload.items() if n!='release_manifest.json'},indent=2).encode()
with zipfile.ZipFile(runtime,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in payload.items():z.writestr(name,data)
(internal/'README.txt').write_text('Required installer data. Leave this folder intact. No manual extraction is needed. Modder Reference.zip is optional documentation for launcher authors; Licenses.zip contains bundled software licenses.\n')
p=release/'README (for users).txt';s=p.read_text().replace('DOA5 animation ports are experimental author test assets, not bundled here.','DOA5 animation ports are not included.').replace('Experimental animation facial retargeting/teleportation are unfinished.','')
s+='\nBundled software licenses: _REDELBE_Runtime/Licenses.zip.\n'
p.write_text(s,encoding='utf8')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in release.rglob('*'):
        if p.is_file():z.write(p,p.relative_to(release).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
digest=hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.zip.sha256').write_text(digest+'  '+archive.name+'\n')
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'sha256':digest,'files':[p.relative_to(release).as_posix() for p in release.rglob('*') if p.is_file()]},indent=2))
