import json,shutil,uuid,hashlib
from pathlib import Path
from audit_ayane_import import names,resources
from lr_resources import extract
from kashira_bridge import export_project
from legacy_resources import index,extract as oldextract
ROOT=Path('packages/hanabi_project_ready')
def main():
 src=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6\REDELBE\Layer2\(DoAxNaruto) Hanabi Hyuga (Adult)')
 if ROOT.exists():raise ValueError('Project output already exists')
 assets=ROOT/'Content_Legacy/REDELBE_Layer2/KOK_COS_001';assets.mkdir(parents=True)
 report=json.loads(Path('analysis/isolation/reference_audit.json').read_text())
 mod=next(m for m in report['mods'] if 'Hanabi' in m['name'])
 missing={fid for t in mod['textures'] if not t['present_in_lr'] for fid in t['ids']}
 parent=Path('packages/legacy_texture_isolation');plan=json.loads((parent/'restoration_plan.json').read_text())
 plan['resources']=[r for r in plan['resources'] if r['id'] in missing];plan['changes']=[r for r in plan['changes'] if r['old_resource'] in missing]
 deps=ROOT/'REDELBE_Dependencies';(deps/'restored').mkdir(parents=True)
 for r in plan['resources']:shutil.copyfile(parent/'restored'/f"0x{r['id']:08x}.g1t",deps/'restored'/f"0x{r['id']:08x}.g1t")
 for c in plan['changes']:c['database']=0xd956e4a2
 plan['changes']+=json.loads(Path('analysis/isolation/hanabi_support.json').read_text())
 oldindex={}
 for file in src.parents[2].glob('*.rdb'):oldindex.update(index(file))
 rows=[]
 for p in src.rglob('*'):
  if not p.is_file() or p.suffix.lower() not in ('.g1m','.g1t','.grp','.oid','.oidex','.mtl','.ktid','.sid','.swg','.g1a','.srsa'):continue
  ids=names.get(p.name.lower(),set())
  if not ids and p.suffix=='.sid':
   (ROOT/'Source_Reference').mkdir(exist_ok=True);shutil.copyfile(p,ROOT/'Source_Reference'/p.name)
   print('Preserved unregistered SID as source reference:',p.name);continue
  if len(ids)!=1:raise ValueError('Ambiguous filename: '+str(p))
  fid=next(iter(ids))
  if fid in resources:baseline=extract(*resources[fid][0])
  elif fid in missing:baseline=(deps/'restored'/f'0x{fid:08x}.g1t').read_bytes()
  else:
   entry=oldindex[fid];baseline=oldextract(entry)
   (deps/'restored'/f'0x{fid:08x}{p.suffix.lower()}').write_bytes(baseline)
   plan['resources'].append({'id':fid,'type':entry['type'],'size':len(baseline),'sha256':hashlib.sha256(baseline).hexdigest(),'extension':p.suffix.lower()})
  payload=p.read_bytes();target=assets/f'0x{fid:08x}{p.suffix.lower()}'
  if target.exists():raise ValueError('Duplicate resource')
  target.write_bytes(payload)
  row={'source':str(p),'file':target.name,'id':fid,'original_header':baseline[:16].hex(),'mod_header':payload[:16].hex(),'bytes':len(payload)};rows.append(row)
  if baseline[:4]!=payload[:4]:print('Different header',p.name,baseline[:16].hex(),payload[:16].hex())
 name='REDELBE LR - Hanabi Hyuga Adult'
 marker={'schema':1,'mode':'Layer2','target':'doa6lr','id':str(uuid.uuid5(uuid.NAMESPACE_URL,'redelbe-lr/hanabi-adult/kok001')),'slot':'KOK_COS_001','name':'(DoAxNaruto) Hanabi Hyuga (Adult)','assets':'Content_Legacy/REDELBE_Layer2/KOK_COS_001'}
 (ROOT/'Content_Legacy/redelbe_layer2.json').write_text(json.dumps(marker,indent=2))
 (ROOT/'project.ktproj').write_text(json.dumps({'SchemaVersion':1,'Name':name,'TargetGame':'doa6lr','Author':'Original mod author; LR test preparation','Description':'Experimental Hanabi Layer2 port for Kokoro COS001, FACE001, HAIR001. Texture restoration dependency installed with the project.','CreatedUtc':'2026-09-16T00:00:00Z','ModifiedUtc':'2026-09-16T00:00:00Z'},indent=2))
 (ROOT/'source_mapping.json').write_text(json.dumps(rows,indent=2))
 # Keep Vanilla byte-identical to LR even where its face support differs from DOA6.
 for c in plan['changes']:
  r=next(r for r in plan['resources'] if r['id']==c['old_resource'])
  baseline=extract(*resources[c['lr_resource']][0])
  (deps/'restored'/f"0x{r['id']:08x}{r.get('extension','.g1t')}").write_bytes(baseline)
  r.update(size=len(baseline),sha256=hashlib.sha256(baseline).hexdigest(),baseline_resource=c['lr_resource'])
 (deps/'restoration_plan.json').write_text(json.dumps(plan,indent=2))
 export_project(ROOT,ROOT.parent/(name+'.ktmod'))
 print('Prepared',len(rows),'runtime assets and',len(missing),'restored texture dependencies')
if __name__=='__main__':main()
