from pathlib import Path
import shutil,time
from kashira_bridge import game_closed
from hair_color_support import capture
root=Path(__file__).resolve().parents[1]
game=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round')
game_closed(game)
backup=game/'REDELBE_LR/rollback'/('hair_support_'+time.strftime('%Y%m%d_%H%M%S'));backup.mkdir(parents=True)
for name in ['dinput8.dll','REDELBE_LR_Sync.exe','REDELBE_LR/active_package.txt','REDELBE_LR/bridge_state.json']:
 target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(game/name,target)
capture(game/'REDELBE_LR/sets/hair_palette16_roster_01',game/'REDELBE_LR/HairColorSupport')
shutil.copy2(root/'experiments/hair_color/native_test/build/dinput8.dll',game/'dinput8.dll')
shutil.copy2(root/'prototype/build/REDELBE_LR_Sync.exe',game/'REDELBE_LR_Sync.exe')
print('Installed; rollback:',backup)
