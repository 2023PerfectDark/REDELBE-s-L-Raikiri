from pathlib import Path
import json,shutil,datetime,re
from lr_resources import GAME
from kashira_bridge import sync
src=Path('packages/super_saiyan_hayabusa_lr_v2');dest=GAME/'KashiraProjects/REDELBE_LR_Super_Saiyan_Hayabusa';pkg=GAME/'_Kashira/Mods/REDELBE LR - Super Saiyan Hayabusa.ktmod'
if dest.exists() or pkg.exists():raise ValueError('Preserve existing project/package before installation')
root=GAME/'REDELBE_LR';backup=root/'research_backups'/('before_hayabusa_aura_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S'));backup.mkdir(parents=True)
for name in ('bridge.json','active_package.txt','bridge_state.json','REDELBE.ini'):
 if (root/name).exists():shutil.copy2(root/name,backup/name)
shutil.copy2(GAME/'dinput8.dll',backup/'dinput8.dll')
shutil.copytree(src/'Project',dest);shutil.copy2(src/pkg.name,pkg)
config=json.loads((root/'bridge.json').read_text(encoding='utf-8-sig'));config.setdefault('projects',{})['REDELBE LR - Super Saiyan Hayabusa']='KashiraProjects/REDELBE_LR_Super_Saiyan_Hayabusa/project.ktproj'
config['legacy_restoration']='KashiraProjects/REDELBE_LR_Super_Saiyan_Hayabusa/REDELBE_Dependencies/restoration_plan.json'
(root/'bridge.json').write_text(json.dumps(config,indent=2))
print(sync(GAME))
sidecar=root/'Layer2/Super Saiyan Hayabusa';sidecar.mkdir(parents=True,exist_ok=True)
shutil.copy2(dest/'mod.ini',sidecar/'mod.ini')
ini=root/'REDELBE.ini';text=ini.read_text(encoding='utf-8-sig');assert not re.search(r'^\[Aura\]\s*$',text,re.M)
text+='\n[Aura]\n; LR TESTING: default added Raidou aura for both fighters.\n; Selected Layer2 mod.ini can override this. Evaluated at match startup.\nenabled = false\n';ini.write_text(text,encoding='utf-8')
shutil.copy2('experiments/aura/AURA_OPTIONS.md',root/'AURA_OPTIONS.md')
shutil.copy2('experiments/aura/native_test/build/dinput8.dll',GAME/'dinput8.dll')
print('Installed; backup:',backup)
