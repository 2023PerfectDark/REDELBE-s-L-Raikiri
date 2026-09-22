"""Prepare reversible legacy-hash restoration for the two requested mods offline."""
from pathlib import Path
import json,hashlib
from legacy_resources import index,extract as legacy_extract
from lr_resources import extract
from audit_ayane_import import GAME,resources
def main():
 report=json.loads(Path('analysis/isolation/reference_audit.json').read_text())
 old=GAME.with_name('Dead or Alive 6')
 source=index(old/'MaterialEditor.rdb')
 out=Path('packages/legacy_texture_isolation');out.mkdir(exist_ok=True)
 assets=out/'restored';assets.mkdir(exist_ok=True)
 ids={fid for mod in report['mods'] for tex in mod['textures'] for fid in tex['ids'] if not tex['present_in_lr']}
 changes=[r for r in report['changed_references'] if r['old_resource'] in ids]
 plan={'status':'OFFLINE ONLY; not installed or game tested','changes':changes,'resources':[]}
 for fid in sorted(ids):
  entry=source[fid];b=legacy_extract(entry)
  if b[:4]!=b'GT1G':raise ValueError('Expected G1T')
  (assets/f'0x{fid:08x}.g1t').write_bytes(b)
  plan['resources'].append({'id':fid,'type':entry['type'],'size':len(b),'sha256':hashlib.sha256(b).hexdigest()})
 if {r['old_resource'] for r in changes}!=ids:raise ValueError('Not all textures have a restoration reference')
 original=extract(*resources[0xd956e4a2][0]);(out/'MaterialEditor.before.dok').write_bytes(original)
 plan['lr_material_sha256']=hashlib.sha256(original).hexdigest()
 (out/'restoration_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
 print('Extracted',len(ids),'original vanilla textures;',len(changes),'exact reference patches;',sum(r['size'] for r in plan['resources']),'bytes')
if __name__=='__main__':main()
