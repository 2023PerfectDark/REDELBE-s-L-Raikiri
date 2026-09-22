from pathlib import Path
import json,collections,struct
from audit_ayane_import import names,resources
from lr_resources import extract
out=Path('analysis/audio');out.mkdir(exist_ok=True)
mods=json.loads(Path('analysis/isolation/inputs.json').read_text());rows=[]
for mod in mods:
 for f in mod['files']:
  if not f['path'].endswith('.srsa'):continue
  p=Path(mod['root'])/f['path'];ids=names.get(p.name.lower(),set())
  row={'name':p.name,'ids':list(ids),'old_header':p.read_bytes()[:80].hex()}
  for fid in ids:
   if len(resources.get(fid,[]))!=1:continue
   b=extract(*resources[fid][0]);target=out/f'{p.stem}.srsa';target.write_bytes(b)
   row.update(lr_bytes=len(b),lr_header=b[:80].hex(),extracted=str(target))
  rows.append(row)
(out/'input_audit.json').write_text(json.dumps(rows,indent=2))
for r in rows:print(r['name'],r.get('lr_bytes'),r.get('lr_header','')[:64])
