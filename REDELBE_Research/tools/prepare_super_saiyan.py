import csv,collections,json,hashlib,shutil,uuid,struct
from pathlib import Path
from lr_resources import GAME,read_index,extract
from legacy_resources import index as oldindex
from kashira_bridge import export_project
from dok_patch import patch
from audit_ayane_import import chunks
src=GAME.with_name('Dead or Alive 6')/'REDELBE/Layer2/Super Saiyan Hayabusa'
out=Path('packages/super_saiyan_hayabusa_lr_v2')
if out.exists():raise ValueError('Output already exists; preserve it')
names=collections.defaultdict(set)
for row in csv.reader((GAME/'KashiraProjects/Name2Hash/DOA6LR.csv').open(encoding='utf-8-sig')):
 if len(row)==2:names[row[1].lower()].add(int(row[0],16))
resources={}
for db in ('root','system'):
 ip=GAME/'fdata_package'/f'{db}.rdb'
 for e in read_index(ip)[1]:resources[e['id']]=(ip,e)
files=[]
for p in src.rglob('*'):
 if p.suffix.lower() not in ('.g1t','.g1m'):continue
 ids=names[p.name.lower()]
 if len(ids)!=1:raise ValueError('Ambiguous resource '+p.name)
 files.append((p,next(iter(ids))))
missing={fid for p,fid in files if fid not in resources}
audit=json.loads(Path('analysis/isolation/reference_audit.json').read_text())
changes=[r for r in audit['changed_references'] if r['old_resource'] in missing]
assert {r['old_resource'] for r in changes}==missing
# Validate these exact references against the CURRENT game, not the old XML export.
material=extract(*resources[0xd956e4a2]);patch(material,changes)
project=out/'Project';assets=project/'Content_Legacy/REDELBE_Layer2/RYU_COS_001';assets.mkdir(parents=True)
old=oldindex(src.parents[2]/'MaterialEditor.rdb')
config=json.loads((GAME/'REDELBE_LR/bridge.json').read_text(encoding='utf-8-sig'))
previous=GAME/config['legacy_restoration'];plan=json.loads(previous.read_text());deps=project/'REDELBE_Dependencies';(deps/'restored').mkdir(parents=True)
for r in plan['resources']:shutil.copyfile(previous.parent/'restored'/f"0x{r['id']:08x}{r.get('extension','.g1t')}",deps/'restored'/f"0x{r['id']:08x}{r.get('extension','.g1t')}")
for fid in missing:
 targets={c['lr_resource'] for c in changes if c['old_resource']==fid};assert len(targets)==1
 baseline=extract(*resources[next(iter(targets))]);(deps/'restored'/f'0x{fid:08x}.g1t').write_bytes(baseline)
 plan['resources'].append(dict(id=fid,type=old[fid]['type'],size=len(baseline),sha256=hashlib.sha256(baseline).hexdigest(),extension='.g1t',baseline_resource=next(iter(targets))))
plan['changes']+=changes
face_changes=[dict(database=0xb290631c,oid=0x7fa2f496,old_resource=0xb7c2c648,lr_resource=0x0986e48a),dict(database=0xb290631c,oid=0x8b679fda,old_resource=0xc7e5818c,lr_resource=0x70c790ad)]
patch(extract(*resources[0xb290631c]),face_changes)
for change in face_changes:
 if not any(c.get('database',0xd956e4a2)==change['database'] and c['oid']==change['oid'] for c in plan['changes']):plan['changes'].append(change)

(deps/'restoration_plan.json').write_text(json.dumps(plan,indent=2))
rows=[]
for p,fid in files:
 b=p.read_bytes()
 baseline=extract(*resources[fid]) if fid in resources else (deps/'restored'/f'0x{fid:08x}.g1t').read_bytes()
 assert b[:4]==baseline[:4]
 if p.suffix=='.g1m':
  if chunks(b)==chunks(baseline)+['RTXE0100']:
   assert b[-16:]==bytes.fromhex('52545845303130301000000000000000')
   edited=bytearray(b[:-16]);struct.pack_into('<I',edited,8,len(edited));struct.pack_into('<I',edited,20,struct.unpack_from('<I',b,20)[0]-1);b=bytes(edited)
  assert b[:8]==baseline[:8] and chunks(b)==chunks(baseline)
 (assets/f'0x{fid:08x}{p.suffix}').write_bytes(b)
 rows.append(dict(source=p.name,id=hex(fid),size=len(b),sha256=hashlib.sha256(b).hexdigest(),restored=fid in missing))
meta=dict(schema=1,mode='Layer2',target='doa6lr',id=str(uuid.uuid5(uuid.NAMESPACE_URL,'redelbe-lr/super-saiyan-hayabusa/ryu001')),slot='RYU_COS_001',name='Super Saiyan Hayabusa',assets='Content_Legacy/REDELBE_Layer2/RYU_COS_001')
(project/'Content_Legacy/redelbe_layer2.json').write_text(json.dumps(meta,indent=2))
(project/'project.ktproj').write_text(json.dumps(dict(SchemaVersion=1,Name='REDELBE LR - Super Saiyan Hayabusa',TargetGame='doa6lr',Author='Original mod author; LR test preparation',Description='RYU_COS_001 costume bundle, RYU_HAIR_001 and RYU_FACE_003 textures; optional Raidou aura test.',CreatedUtc='2026-09-20T00:00:00Z',ModifiedUtc='2026-09-20T00:00:00Z'),indent=2))
(project/'source_mapping.json').write_text(json.dumps(rows,indent=2))
(project/'mod.ini').write_text('[General]\ntype = costume\n\n[Costume]\nslot = RYU_COS_001\n\n[Aura]\nenabled = true\n')
export_project(project,out/'REDELBE LR - Super Saiyan Hayabusa.ktmod')
print(json.dumps(dict(assets=len(files),restored=len(missing),patches=len(changes),output=str(out))))
