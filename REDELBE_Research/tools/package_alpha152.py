"""Allow-listed public Alpha 152 distribution. No player state or live mod sets."""
from pathlib import Path
import hashlib,json,re,shutil,zipfile
root=Path(__file__).resolve().parents[1]
game=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round')
old=root/'releases/REDELBE_LR_0.3_RC4_Release'
out=root/'releases/REDELBE_LR_Alpha_152'
stage=root/'analysis/release_staging/Alpha152'
out.mkdir(exist_ok=True);stage.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(old/'_REDELBE_Runtime/runtime.zip') as z:z.extractall(stage)
def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
for name in ('dinput8.dll','REDELBE_LR_Launcher.exe'):
    copy(root/'experiments/hair_color/native_test/build'/name,stage/name)
copy(game/'REDELBE_LR_Sync.exe',stage/'REDELBE_LR_Sync.exe')
for p in (game/'REDELBE_LR/bridge_tools').iterdir():
    if p.is_file() and p.suffix in ('.exe','.dll','.json'):copy(p,stage/'REDELBE_LR/bridge_tools'/p.name)
for name in ('REDELBE.ini','settings.schema.json','SETTINGS.md','slot_names.txt','birthdays.ini','Birthday list and sources.txt','AURA_OPTIONS.md','README Automatic Layer2 Isolation.md','branding.ini'):
    copy(game/'REDELBE_LR'/name,stage/'REDELBE_LR'/name)
for folder in ('BirthdayMessages','Audio'):
    shutil.copytree(game/'REDELBE_LR'/folder,stage/'REDELBE_LR'/folder,dirs_exist_ok=True)
copy(game/'REDELBE_LR/StageVideoTest/StageVideoPreviewTest.exe',stage/'REDELBE_LR/StageVideoTest/StageVideoPreviewTest.exe')
for name in ('update_info.ini','update_info.txt'):copy(root/'releases/alpha152_update'/name,stage/'REDELBE_LR'/name)
p=stage/'REDELBE_LR/update_info.ini';s=p.read_text();p.write_text(s.replace('ShowEveryLaunch=1','ShowEveryLaunch=0'))
p=stage/'REDELBE_LR/update_info.txt';s=p.read_text();s=s.replace('repeating automatic scrolling','slow, smooth, repeating automatic scrolling');s+='\n-Recognizes Lost Paradise Oboro stage resource names.\n';p.write_text(s)
p=stage/'REDELBE_LR/REDELBE.ini';s=p.read_text(encoding='utf-8-sig')
s=re.sub(r'(?m)^(log_ui_events\s*=).*',r'\1 false',s)
s=s.replace('EXPERIMENTAL integration; awaiting in-game validation.','LR SUPPORTED (offline).')
s=s.replace('Uses locally prepared clips. Original animation cameras are not yet supported.','Run Tools/Prepare Animation Library.exe first. Dedicated cameras and free camera controls are supported.')
s=s.replace('LR TESTING: default added Raidou aura for both fighters.','LR SUPPORTED: optional Raidou aura for both fighters.')
s=s.replace('LR TESTING: custom loop for the native Player 1 aura test.','LR SUPPORTED: optional custom aura sound. Supply your own WAV.')
s=s.replace('hair_color_unlocks = true','hair_color_unlocks = false')
s=re.sub(r'(?m)^survival_stage\s*=.*','survival_stage = default',s)
p.write_text(s,encoding='utf8')
for p in old.iterdir():
    if p.is_file() and p.suffix=='.cmd':copy(p,out/p.name)
shutil.copytree(old/'_REDELBE_Runtime',out/'_REDELBE_Runtime',dirs_exist_ok=True,ignore=shutil.ignore_patterns('runtime.zip'))
shutil.copytree(old/'Tools',out/'Tools',dirs_exist_ok=True)
copy(root/'packages/SRS_Audio_Studio_LR_0.3.14/SRS Audio Studio LR.exe',out/'Tools/SRS Audio Studio LR/SRS Audio Studio LR.exe')
(out/'Tools/SRS Audio Studio LR/UPDATE 0.3.14.txt').write_text('Open SRSA or SRST; streamed banks always require both matching files. Missing companions can be selected in a file picker. In-window bank drops extract audio; Explorer drops onto the executable open the bank editor. Raw KTSR envelopes are supported for validated layouts. Unsupported ADPCM variants remain unsupported; this does not add universal Katana-engine compatibility.\n')
shutil.copytree(old/'Notices',out/'Notices',dirs_exist_ok=True)
copy(root/'packages/Alpha152Tools/Prepare Hair Colors.exe',out/'Tools/Prepare Hair Colors.exe')
copy(root/'packages/AnimationBrowser_Preview/Tools/Prepare Animation Library.exe',out/'Tools/Prepare Animation Library.exe')
for folder in ('RRPreview','Layer2','StageVidPreviews','AuraSounds'):(out/'REDELBE_LR'/folder).mkdir(parents=True,exist_ok=True)
(out/'_Kashira/Mods').mkdir(parents=True,exist_ok=True)
for name in ('REDELBE.ini','branding.ini','settings.schema.json','SETTINGS.md','update_info.ini','update_info.txt','birthdays.ini','AURA_OPTIONS.md','README Automatic Layer2 Isolation.md'):
    copy(stage/'REDELBE_LR'/name,out/'REDELBE_LR'/name)
(out/'REDELBE_LR/Layer2/README.txt').write_text('Place compatible LR Layer2 mods here. Original DOA6 mods require porting; this is not automatic. Kashira packages go in _Kashira/Mods. Launch using Play DOA6LR with REDELBE.cmd to synchronize changes.\n')
(out/'REDELBE_LR/StageVidPreviews/README.txt').write_text('Place MP4s here named by stage slot, e.g. S0901WAY.mp4. Alternate variants use their own code. Oboro resource names: S0801LOS_OBORO, S0802LOS_OBORO, S0899LOS_OBORO. Videos are optional and not bundled. Playback starts after the stage name disappears. Configure audio/music ducking in REDELBE.ini.\n')
(out/'REDELBE_LR/AuraSounds/README.txt').write_text('Supply your own PCM 16-bit WAV. Configure its relative path and volume in REDELBE.ini or the compatible Layer2 mod settings.\n')
copy(stage/'REDELBE_LR/RRPreview/README.txt',out/'REDELBE_LR/RRPreview/README.txt')
(out/'README (for users).txt').write_text('''REDELBE LR (Last Raikiri) — Public Alpha 152
Tested locally with DOA6LR 1.11. Wider-PC testing is still needed.

INSTALL
1. Close the game and Kashira. Keep your own game and mods backed up.
2. Put Kashira-win-x64.exe and KashiraEditor-win-x64.exe beside DOA6LR.exe.
3. Extract this release beside DOA6LR.exe, then run Install REDELBE LR.cmd.
   A conflicting dinput8.dll is refused. Remove the old loader using its own
   uninstaller before a clean installation; preserve your settings and mods.
4. Start with Play DOA6LR with REDELBE.cmd. Steam must be running.
   Mod preparation runs automatically before launch. Direct DOA6LR.exe/Steam
   launches do not run that synchronization unless redirected to the launcher.

OPTIONAL FIRST-TIME SETUP
Tools/Prepare Hair Colors.exe generates the palette locally (about 27 GB).
Tools/Prepare Animation Library.exe builds the browser library from your game.
After setup, launch through REDELBE again. No Python or developer tools needed.
DOA5 animation ports are experimental author test assets, not bundled here.

EDITABLE FILES
REDELBE_LR/REDELBE.ini: player options. branding.ini: title name/version.
update_info.txt and update_info.ini: release notice and scrolling speed.
_Kashira/Mods: compatible packages. REDELBE_LR/Layer2: compatible LR folders.
REDELBE_LR/RRPreview: replacement SRSA and matching SRST banks.
REDELBE_LR/StageVidPreviews: optional stage MP4s; none are bundled.
Tools/SRS Audio Studio LR: optional audio editor and FFmpeg setup.
_REDELBE_Runtime is installer data; leave it intact, no browsing required.

CONTROLS
F or LT/L2: next Layer2; Back/Select: previous. Starts at Vanilla.
G / Square / X in Wardrobe Hairstyles: hair colors after palette setup.
F8 in Wardrobe or offline Training: animation browser confirmation.
C / Back toggles browser camera controls. F5: battle HUD if enabled.
Mouse: left confirm, right back; stage wheel/drag and wardrobe rotation.

REMOVAL
Close the game and run Remove REDELBE LR.cmd. User mods/projects are preserved.
Remove custom Steam launch options. Keep backups of your editable settings.

LIMITS
Future title updates can need a loader update despite pattern scanning.
Stage/weather mod ports and automatic DOA6 conversion are not completed.
Private isolation depends on compatible assets; some mods still share resources.
Experimental animation facial retargeting/teleportation are unfinished.
Unsupported formats/options are not enabled merely by naming them in an INI.
Offline features are intended for offline use; this is not online-PvP support.
''',encoding='utf8')
copy(old/'README (for modders).txt',out/'README (for modders).txt')
p=out/'README (for modders).txt';s=p.read_text();s+='\nALPHA 152\nCompatible character mods use private asset preparation when supported. Shared-resource fallback can still conflict. See README Automatic Layer2 Isolation.md. Hair colors and animation library are generated locally using the Tools executables. Mod-specific opponent dialogue is experimental. No normal-match DOA5 animation override is enabled.\n';p.write_text(s)
copy(root/'releases/REDELBE_LR_CHANGELOG.txt',out/'changelog.txt')
manifest={p.relative_to(stage).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(stage.rglob('*')) if p.is_file() and p.name!='release_manifest.json'}
(stage/'release_manifest.json').write_text(json.dumps(manifest,indent=2))
with zipfile.ZipFile(out/'_REDELBE_Runtime/runtime.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in stage.rglob('*'):
        if p.is_file():z.write(p,p.relative_to(stage).as_posix())
(root/'analysis/release_staging/paths.json').write_text(json.dumps({'release':str(out),'payload':str(stage)}))
print(out)
