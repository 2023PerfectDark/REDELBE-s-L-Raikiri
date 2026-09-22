"""Portable install/removal. All destinations are confined to a selected game folder."""
import hashlib,json,shutil,time
EDITABLE_FILES={"REDELBE_LR/REDELBE.ini","REDELBE_LR/branding.ini","REDELBE_LR/fullmix.ini","REDELBE_LR/random_tracks.txt"}
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def install(source,game):
 from kashira_bridge import safe_child,game_closed
 source=Path(source).resolve();game=Path(game).resolve();game_closed(game)
 for name in ('DOA6LR.exe','Kashira-win-x64.exe','KashiraEditor-win-x64.exe'):
  if not (game/name).is_file():raise ValueError(f'Place this package beside {name}, then run Install REDELBE LR.cmd')
 manifest=json.loads((source/'release_manifest.json').read_text())
 for name,digest in manifest.items():
  p=safe_child(source,name)
  if sha(p)!=digest:raise ValueError('Release file modified: '+name)
 proxy=game/'dinput8.dll'
 previous=game/'REDELBE_LR/installed_files.json'
 previous_manifest=json.loads(previous.read_text()) if previous.exists() else {}
 if proxy.exists() and sha(proxy) not in (manifest['dinput8.dll'],previous_manifest.get('dinput8.dll')):raise ValueError('A different dinput8.dll already exists. Keep it intact; resolve the loader conflict before installing REDELBE LR.')
 root=game/'REDELBE_LR';checkpoint=root/'install_backups'/time.strftime('%Y%m%d_%H%M%S')
 checkpoint.mkdir(parents=True,exist_ok=False)
 legacy=game/'REDELBE_LR.asi'
 if legacy.exists() and 'REDELBE_LR.asi' not in manifest:
  legacy.rename(checkpoint/'previous_REDELBE_LR.asi')
 for name in manifest:
  target=safe_child(game,name)
  if target.exists():
   saved=safe_child(checkpoint,name);saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved)
 for name in manifest:
  target=safe_child(game,name);target.parent.mkdir(parents=True,exist_ok=True)
  if name in EDITABLE_FILES and target.exists():
   manifest[name]=sha(target)
   continue
  shutil.copy2(safe_child(source,name),target)
 (root/'installed_files.json').write_text(json.dumps(manifest,indent=2))
 if not (root/'bridge.json').exists():(root/'bridge.json').write_text('{"projects":{}}\n')
 print('Installed. Run REDELBE_LR_Launcher.exe to synchronize and launch. Previous files: '+str(checkpoint))
def uninstall(game):
 from kashira_bridge import safe_child,game_closed
 game=Path(game).resolve();game_closed(game);root=game/'REDELBE_LR'
 manifest=json.loads((root/'installed_files.json').read_text())
 journal=root/'converted_packages.json'
 if journal.exists():
  for row in reversed(json.loads(journal.read_text())):
   target=safe_child(game,row['package']);original=safe_child(game,row['original'])
   if target.exists() and sha(target).lower()==row['converted_sha256'].lower():shutil.copy2(original,target)
   else:print('Preserved changed/removed package: '+row['package'])
 archive=game/('REDELBE_LR_Removed_'+time.strftime('%Y%m%d_%H%M%S'))
 archive.mkdir(exist_ok=False)
 # Preserve all mod data, profiles, projects and checkpoints. Only release-owned
 # files with matching hashes are moved; a changed file is never deleted.
 for name,digest in manifest.items():
  if name.startswith('REDELBE_LR/'):continue
  p=safe_child(game,name)
  if p.exists() and sha(p)==digest:
   dest=safe_child(archive,name);dest.parent.mkdir(parents=True,exist_ok=True);p.rename(dest)
  elif p.exists():print('Preserved changed file: '+name)
 root.rename(archive/'REDELBE_LR')
 print('Removed matching loader files. Mods/projects preserved. Use Kashira Apply to restore its normal management. Saved files: '+str(archive))
