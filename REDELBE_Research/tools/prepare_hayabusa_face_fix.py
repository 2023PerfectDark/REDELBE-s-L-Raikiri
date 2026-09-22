from pathlib import Path
import sys,json,hashlib
from lr_resources import GAME,read_index,extract
from legacy_resources import index,extract as oldextract
from dok_patch import patch
out=Path('packages/hayabusa_face_fix');out.mkdir(exist_ok=False)
project=GAME/'KashiraProjects/REDELBE_LR_Super_Saiyan_Hayabusa'
plan=json.loads((project/'REDELBE_Dependencies/restoration_plan.json').read_text())
change=dict(database=0xb290631c,oid=3518536940,property=1002428837,old_resource=0xc401b928,lr_resource=3952568101)
ip=GAME/'fdata_package/root.rdb';es={e['id']:e for e in read_index(ip)[1]}
assert change['old_resource'] not in es
patch(extract(ip,es[change['database']]),[change])
old=index(GAME.with_name('Dead or Alive 6')/'CharacterEditor.rdb');entry=old[change['old_resource']]
vanilla=extract(ip,es[change['lr_resource']]);payload=oldextract(entry)
(out/'baseline.grp').write_bytes(vanilla);(out/'mod.grp').write_bytes(payload)
plan['resources'].append(dict(id=change['old_resource'],type=entry['type'],size=len(vanilla),sha256=hashlib.sha256(vanilla).hexdigest(),extension='.grp',baseline_resource=change['lr_resource']))
plan['changes'].append(change);(out/'restoration_plan.json').write_text(json.dumps(plan,indent=2))
print('Prepared original face group with current LR fallback and verified exact CharacterEditor reference.')
