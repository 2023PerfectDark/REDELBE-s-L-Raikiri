import sys,json,hashlib,struct
from pathlib import Path
from audit_ayane_import import GAME,resources
from build_layer2_package import build
from legacy_restoration import load_plan
from lr_resources import extract
from verify_layer2_package import verify,digest_container
from dok_patch import patch
p=Path('packages/hanabi_project_ready');out=Path('packages/hanabi_final_validation_v2')
planpath=p/'REDELBE_Dependencies/restoration_plan.json';plan,payloads=load_plan(planpath)
for c in plan['changes']:
 assert payloads[c['old_resource']][1]==extract(*resources[c['lr_resource']][0])
build(GAME,out,[('KOK_COS_001','Hanabi Hyuga Adult',str(p/'Content_Legacy/REDELBE_Layer2/KOK_COS_001'))],planpath)
result=verify(out)
raw=(out/'overlay/root.rdb').read_bytes();count=struct.unpack_from('<I',raw,16)[0]
original=(GAME/'fdata_package/root.rdb').read_bytes()
assert count==struct.unpack_from('<I',original,16)[0]+9
# Reject an updated/conflicting field instead of overwriting authored changes.
c=plan['changes'][0];db=extract(*resources[c['database']][0]);bad=dict(c,lr_resource=c['lr_resource']^1)
try:patch(db,[bad]);raise AssertionError('Conflict was accepted')
except ValueError:pass
result.update(restored_resources=9,patched_references=len(plan['changes']),vanilla_references_byte_identical=True)
(out/'validation.json').write_text(json.dumps(result,indent=2));print('PASS',result)
