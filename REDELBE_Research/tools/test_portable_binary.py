"""Exercise the shipped EXE, including removing its own running image on Windows."""
import json,subprocess,uuid
from pathlib import Path
source=Path('packages/REDELBE_LR_0.3_RC2/REDELBE_LR_Package').resolve()
game=Path('analysis/portable-tests')/('Game folder '+uuid.uuid4().hex[:8]);game=game.resolve();game.mkdir(parents=True)
for name in ('DOA6LR.exe','Kashira-win-x64.exe','KashiraEditor-win-x64.exe'):(game/name).write_bytes(b'fixture only')
subprocess.run([str(source/'REDELBE_LR_Sync.exe'),'install',str(source),str(game)],check=True)
(game/'user project.txt').write_text('keep')
subprocess.run([str(game/'REDELBE_LR_Sync.exe'),'uninstall',str(game)],check=True)
assert not (game/'REDELBE_LR.asi').exists() and not (game/'dinput8.dll').exists()
assert (game/'user project.txt').read_text()=='keep'
result={'passed':True,'fixture':str(game),'self_removal':True,'preserved_user_files':True}
Path('analysis/portable_binary_test.json').write_text(json.dumps(result,indent=2));print(result)
