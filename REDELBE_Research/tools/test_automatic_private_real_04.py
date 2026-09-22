import sys,json,shutil
from pathlib import Path
sys.path.insert(0,'REDELBE_Research/tools')
from kashira_bridge import input_plan,materialize
from lr_resources import GAME,read_index
from legacy_restoration import load_plan
from build_layer2_package import build
from automatic_private_models import prepare
from verify_layer2_package import verify
root=Path('REDELBE_Research');out=root/'packages/automatic_private_test_04';stage=root/'analysis/isolation/auto_inputs_04';stage.mkdir()
key,indices,candidates=input_plan(GAME);config=json.loads((GAME/'REDELBE_LR/bridge.json').read_text());restore=GAME/config['legacy_restoration'];_,restored=load_plan(restore)
known={e['id'] for db in ('root','system') for e in read_index(GAME/'fdata_package'/f'{db}.rdb')[1]}|set(restored)
definitions=[];recipes={}
for i,(_,file,meta,project) in enumerate(candidates):
 definitions.append(materialize(file,meta,project,stage/str(i),known,[]))
 if meta['slot'] in ('KOK_COS_001','KOK_HAIR_001'):recipes[i+1]=json.loads((root/'analysis/isolation/hanabi_portable_recipe.json').read_text())
build(GAME,out,definitions,restore)
print(json.dumps(prepare(GAME,out,definitions,recipes),indent=2));print(verify(out))
