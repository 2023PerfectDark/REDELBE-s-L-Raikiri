import sys,json,zipfile,io,uuid,hashlib
from pathlib import Path
sys.path.insert(0,'tools')
from audit_ayane_import import names
from lr_resources import read_index,extract
from kashira_bridge import export_project
base=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common');game=base/'Dead or Alive 6 Last Round'
out=Path('packages/hair_layer2_tests');out.mkdir(exist_ok=True)
resources={e['id']:(game/'fdata_package'/f'{db}.rdb',e) for db in ('root','system') for e in read_index(game/'fdata_package'/f'{db}.rdb')[1]}
def project(folder,slot,name):
 root=out/folder;assets=root/'Content_Legacy/REDELBE_Layer2'/slot;assets.mkdir(parents=True,exist_ok=True)
 meta={'schema':1,'mode':'Layer2','target':'doa6lr','id':str(uuid.uuid5(uuid.NAMESPACE_URL,'redelbe-lr/'+folder)),'slot':slot,'name':name,'assets':assets.relative_to(root).as_posix()}
 (root/'Content_Legacy/redelbe_layer2.json').write_text(json.dumps(meta,indent=2))
 (root/'project.ktproj').write_text(json.dumps({'SchemaVersion':1,'Name':name,'TargetGame':'doa6lr','Description':'Hair/head Layer2. Select matching hair, then F/LT/Back.','Author':'Original mod authors; LR Layer2 preparation'},indent=2))
 return root,assets
root,assets=project('Eve_Ponytail','KAS_HAIR_002',"(Hair) Stellar Blade Eve's Ponytail 1 (Kasumi)")
zpath=base/"Dead or Alive 6 Last Round - Backup 2026-09-15_210415/_Kashira/Mods/(Hair) ~LR~ Stellar Blade Eve's Ponytail 1 (Kasumi).zip"
with zipfile.ZipFile(zpath) as outer:
 with zipfile.ZipFile(io.BytesIO(outer.read(outer.namelist()[0]))) as z:
  for entry in z.infolist():
   if entry.filename.startswith('Content_Legacy/') and not entry.is_dir():(assets/Path(entry.filename).name).write_bytes(z.read(entry))
export_project(root,out/'REDELBE LR - Eve Ponytail Hair.ktmod')
root,assets=project('Hanabi_Hair_Head','KOK_HAIR_001','(Hair-Head) Hanabi Hyuga Hair 1 (Adult Byakugan)')
src=base/'Dead or Alive 6/REDELBE/Layer2/(Hair-Head) Hanabi Hyuga Hair 1 (Adult Byakugan)'
missing=set();rows=[]
for p in src.rglob('*'):
 if p.suffix.lower() not in ('.g1m','.g1t','.grp','.oid','.oidex','.swg'):continue
 ids=names[p.name.lower()]
 if len(ids)!=1:raise ValueError(p.name)
 fid=next(iter(ids));(assets/f'0x{fid:08x}{p.suffix}').write_bytes(p.read_bytes());rows.append({'source':p.name,'id':fid})
 if fid not in resources:missing.add(fid)
plan=json.loads(Path('packages/hanabi_project_ready/REDELBE_Dependencies/restoration_plan.json').read_text())
plan['resources']=[r for r in plan['resources'] if r['id'] in missing];plan['changes']=[c for c in plan['changes'] if c['old_resource'] in missing]
if {r['id'] for r in plan['resources']}!=missing:raise ValueError('Missing dependency plan')
deps=root/'REDELBE_Dependencies';(deps/'restored').mkdir(parents=True,exist_ok=True)
for r in plan['resources']:
 changes=[c for c in plan['changes'] if c['old_resource']==r['id']]
 if len(changes)!=1:raise ValueError('Ambiguous dependency')
 baseline=extract(*resources[changes[0]['lr_resource']]);(deps/'restored'/f"0x{r['id']:08x}{r.get('extension','.g1t')}").write_bytes(baseline)
 r.update(size=len(baseline),sha256=hashlib.sha256(baseline).hexdigest(),baseline_resource=changes[0]['lr_resource'])
plan['status']='Hair/head test dependencies, refreshed from current main LR; vanilla payloads preserved'
(deps/'restoration_plan.json').write_text(json.dumps(plan,indent=2));(root/'source_mapping.json').write_text(json.dumps(rows,indent=2))
export_project(root,out/'REDELBE LR - Hanabi Hair Head.ktmod')
print('Prepared Eve (7 assets), Hanabi',len(rows),'assets;',len(missing),'restored references. Audio and animation replacements excluded.')
