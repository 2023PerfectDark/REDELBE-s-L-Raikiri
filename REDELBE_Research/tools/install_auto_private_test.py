"""Install the tested local isolation build, preserving a rollback checkpoint."""
from pathlib import Path
import json,shutil,time,zipfile
root=Path(__file__).resolve().parents[1]
game=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round')
from kashira_bridge import game_closed,MARKER
game_closed(game)
checkpoint=game/'REDELBE_LR/rollback'/('automatic_private_'+time.strftime('%Y%m%d_%H%M%S'))
checkpoint.mkdir(parents=True)
recipe=json.loads((root/'analysis/isolation/hanabi_portable_recipe.json').read_text())
def backup(relative):
 p=game/relative
 if p.exists():
  dest=checkpoint/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
for relative in ('dinput8.dll','REDELBE_LR_Sync.exe','REDELBE_LR/active_package.txt','REDELBE_LR/bridge_state.json','REDELBE_LR/bridge_sources.json'):backup(relative)
for project,package in (('REDELBE_LR_Hanabi','REDELBE LR - Hanabi Hyuga Adult.ktmod'),('REDELBE_LR_Hanabi_Hair_Head','REDELBE LR - Hanabi Hair Head.ktmod')):
 relative=Path('KashiraProjects')/project/MARKER;backup(relative)
 p=game/relative;meta=json.loads(p.read_text(encoding='utf-8-sig'));meta['private_model_recipe']=recipe;p.write_text(json.dumps(meta,indent=2),encoding='utf-8')
 relative=Path('_Kashira/Mods')/package;backup(relative);p=game/relative
 temp=root/'analysis/isolation'/package
 with zipfile.ZipFile(p) as source,zipfile.ZipFile(temp,'w') as target:
  target.comment=source.comment
  for entry in source.infolist():
   data=source.read(entry)
   if entry.filename.replace('\\','/')==MARKER:
    meta=json.loads(data.decode('utf-8-sig'));meta['private_model_recipe']=recipe;data=json.dumps(meta,indent=2).encode()
   target.writestr(entry,data)
 shutil.copy2(temp,p)
shutil.copy2(root/'experiments/hair_color/native_test/build/dinput8.dll',game/'dinput8.dll')
shutil.copy2(root/'prototype/build/REDELBE_LR_Sync.exe',game/'REDELBE_LR_Sync.exe')
print('Installed; checkpoint:',checkpoint)
