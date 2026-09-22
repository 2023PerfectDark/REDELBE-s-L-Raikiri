"""Prepare isolated Hanabi material bindings in the workspace, without installation."""
import hashlib,json
from pathlib import Path
from lr_resources import GAME,read_index,extract
from isolated_material_chain import Database,MaterialCloner
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'packages/hanabi_cloned_materials_v2'
if OUT.exists():raise ValueError('Preserve existing output before rebuilding')
res={e['id']:(p,e) for p in (GAME/'fdata_package').glob('*.rdb') for e in read_index(p)[1]}
dbs={fid:Database(extract(*res[fid])) for fid in (0xb290631c,0x2082ad97,0xd956e4a2)}
source=ROOT/'packages/hanabi_project_ready'
meta=json.loads((source/'Content_Legacy/redelbe_layer2.json').read_text())
assets=source/meta['assets'];replacements={}
audit=json.loads((ROOT/'analysis/isolation/hanabi_current_private_audit.json').read_text())
for texture in audit:
 for target in texture['targets']:
  old=target['original_resource'];current=target['current_resource']
  data=(assets/f'0x{old:08x}.g1t').read_bytes()
  for fid in (old,current):
   if fid in replacements and replacements[fid]!=data:raise ValueError('Texture payloads share a baseline; object-specific mapping required')
   replacements[fid]=data
nextid=0x0fa80000
def alloc():
 global nextid
 while nextid in res:nextid+=1
 result=nextid;nextid+=1;return result
cloner=MaterialCloner(dbs,lambda fid:extract(*res[fid]),alloc,res)
chains=json.loads((ROOT/'analysis/isolation/hanabi_donor_chains.json').read_text())['source_slots']
bindings={}
for slot,chain in chains.items():
 materials={str(m['material']):cloner.material(m['material'],replacements) for m in chain['bindings']}
 dm=dbs[0xb290631c]
 base=cloner.binding(dm.scalar(chain['model'],MaterialCloner.TBC),replacements)
 bindings[slot]={'materials':materials,'base_texture_binding':base,'source_model':chain['model']}
OUT.mkdir(parents=True);(OUT/'assets').mkdir();(OUT/'databases').mkdir()
for fid,db in dbs.items():(OUT/'databases'/f'0x{fid:08x}.kidsobjdb').write_bytes(db.serialize())
manifest=[]
for fid,asset in cloner.assets.items():
 p=OUT/'assets'/f"0x{fid:08x}{asset['extension']}";p.write_bytes(asset['payload'])
 manifest.append({'id':fid,'source':asset['source'],'extension':asset['extension'],'sha256':hashlib.sha256(asset['payload']).hexdigest()})
summary={'bindings':bindings,'assets':manifest,'texture_objects':cloner.audit,
 'original_records_unchanged':True,'runtime_binding_installed':False,
 'replaced_texture_resources':sorted({x['original_resource'] for x in cloner.audit if x['private_resource']!=x['original_resource']})}
(OUT/'manifest.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({'cloned_materials':sum(len(b['materials']) for b in bindings.values()),'cloned_texture_objects':len(cloner.audit),'new_files':len(manifest),'replaced_texture_resources':len(summary['replaced_texture_resources']),'original_records_unchanged':True,'runtime_binding_installed':False},indent=2))
