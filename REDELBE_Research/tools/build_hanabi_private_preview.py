"""Create an isolated, disposable preview generation; never mutate the game."""
import json,struct,hashlib,shutil
from pathlib import Path
from lr_resources import GAME,read_index,extract
from dok_patch import records,props,u
from isolated_material_chain import Database,MaterialCloner
from build_layer2_package import wrap,slot_hash
from verify_layer2_package import verify
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'packages/hanabi_private_preview_v8'
if OUT.exists():raise ValueError('Output already exists')
active=GAME/'REDELBE_LR'/ (GAME/'REDELBE_LR/active_package.txt').read_text().strip()
# Rebuild from the pre-isolation generation, never clone an earlier test again.
while (active/'private_preview.json').exists():
 active=Path(json.loads((active/'private_preview.json').read_text())['source_generation'])
res={e['id']:(p,e) for p in (GAME/'fdata_package').glob('*.rdb') for e in read_index(p)[1]}
base=dict(line.split('\t') for line in (active/'vanilla.tsv').read_text().splitlines())
def payload(fid):
 key=f'fdata_package/data/0x{fid:08x}.file'
 if key in base:
  b=(active/base[key]).read_bytes();return b[len(b)-u(b,16):]
 return extract(*res[fid])
dbs={fid:Database(payload(fid)) for fid in (0xb290631c,0x2082ad97,0xd956e4a2)}
source=ROOT/'packages/hanabi_project_ready';meta=json.loads((source/'Content_Legacy/redelbe_layer2.json').read_text());assets=source/meta['assets']
replacements={int(p.stem,16):p.read_bytes() for p in assets.glob('*.g1t')}
audit=json.loads((ROOT/'analysis/isolation/hanabi_current_private_audit.json').read_text())
for t in audit:
 for x in t['targets']:replacements[x['current_resource']]=replacements[x['original_resource']]
v1=GAME/'KashiraProjects/REDELBE_LR_Hanabi/private_texture_mapping.json'
if v1.exists():
 for x in json.loads(v1.read_text()):replacements[x['private']]=replacements[x['old']]
nextid=0x0fa90000
def alloc():
 global nextid
 while nextid in res or f'fdata_package/data/0x{nextid:08x}.file' in base:nextid+=1
 result=nextid;nextid+=1;return result
cloner=MaterialCloner(dbs,payload,alloc,res)
chains=json.loads((ROOT/'analysis/isolation/hanabi_donor_chains.json').read_text())['source_slots']
newslots={};ce=dbs[0xb290631c];common=dbs[0x2082ad97]
for slot,chain in chains.items():
 materialmap={m['material']:cloner.material(m['material'],replacements) for m in chain['bindings']}
 original_tbc=ce.scalar(chain['model'],MaterialCloner.TBC)
 source_ktid=assets/f'0x{ce.scalar(original_tbc,MaterialCloner.KTID):08x}.ktid'
 if slot=='KOK_COS_001' and not source_ktid.exists():
  # The legacy mesh uses 22 texture slots; LR's reduced table has only 21.
  # Restore that order only in the cloned model, leaving vanilla untouched.
  source_ktid=ROOT/'analysis/isolation/legacy_templates/0x27d41bb4.ktid'
 ktid_data=bytearray(source_ktid.read_bytes()) if source_ktid.exists() else None
 if slot=='KOK_COS_001' and ktid_data is not None:
  for off in range(0,len(ktid_data),8):
   old=u(ktid_data,off+4)
   if any(old in d.items for d in dbs.values()):continue
   original=(ROOT/f'analysis/isolation/legacy_templates/object_{old:08x}.bin').read_bytes()
   temporary=Database(payload(0xb290631c));temporary.items[old]=original
   resource=temporary.scalar(old,MaterialCloner.TEXTURE)
   if resource not in res and f'fdata_package/data/0x{resource:08x}.file' not in base:
    raise ValueError(f'Legacy body texture needs restoration: {resource:08x}')
   private=cloner.oid();record=bytearray(original);struct.pack_into('<I',record,12,private)
   ce.items[private]=bytes(record);struct.pack_into('<I',ktid_data,off+4,private)
 tbc=cloner.binding(original_tbc,replacements,ktid_data)
 dmchanges={MaterialCloner.TBC:tbc}
 # Independent model data and support files; never replace Kokoro's file IDs.
 for key,ext in ((0x8ab68b3f,'.g1m'),(0x3bbfd9a5,'.grp'),(0x7f0de9a3,'.mtl'),(0x8dfd0584,'.oidex')):
  fid=ce.scalar(chain['model'],key)
  if not fid:continue
  replacement=assets/f'0x{fid:08x}{ext}'
  # Original model support was restored under legacy IDs in the active overlay.
  data=replacement.read_bytes() if replacement.exists() else payload(fid)
  dmchanges[key]=cloner.asset(fid,data,ext)
 model=ce.clone(chain['model'],cloner.oid(),dmchanges)
 motorchanges={0x0b6e1578:[model]}
 private_body_mi=None
 if slot=='KOK_COS_001':
  from private_mesh_materials import materials,build
  mesh=cloner.assets[dmchanges[0x8ab68b3f]]['payload']
  mesh_mats=materials(mesh)
  base_table=cloner.assets[ce.scalar(tbc,MaterialCloner.KTID)]['payload']
  mrnh=common.values(chain['motor'],0x34cf9e5c)
  if len(mrnh)!=2*len(mesh_mats):raise ValueError('Body material-name count mismatch')
  body_mbes=[build(cloner,mrnh[2*i+1],slots,base_table) for i,slots in enumerate(mesh_mats)]
  private_body_mi=body_mbes*common.scalar(chain['setting'],0xb3a1e5aa)
  motorchanges[0x34cf9e5c]=[x for i,mbe in enumerate(body_mbes) for x in (mrnh[2*i],mbe)]
 for key in (0x34cf9e5c,):
  if key in motorchanges:continue
  vv=common.values(chain['motor'],key)
  motorchanges[key]=[materialmap.get(v,v) if i%2 else v for i,v in enumerate(vv)]
 motor=common.clone_arrays(chain['motor'],cloner.oid(),motorchanges)
 cs=common.clone_arrays(chain['setting'],cloner.oid(),{0x68a6f779:[motor],0x24c114f6:private_body_mi if private_body_mi is not None else [materialmap.get(v,v) for v in common.values(chain['setting'],0x24c114f6)]})
 newslots[slot.replace('001','901')]=cs
# Add hidden model names to the native resolver. No selectable fighter entry is changed.
scn=Database(payload(0x6d011726));root=next(oid for oid,b in scn.items.items() if u(b,16)==0xdac911d7)
b=scn.items[root];r=(0,u(b,8),root,u(b,16),u(b,20));metadata=bytearray();values=bytearray()
from model_slot_registry import extend_registry,validate_registry
registry_props={key:(kind,n,b[o:o+s]) for key,kind,n,o,s in props(b,r)}
registry_changes=extend_registry(registry_props,newslots)
for key,kind,n,o,s in props(b,r):
 data=b[o:o+s]
 if key in registry_changes:kind,n,data=registry_changes[key]
 metadata+=struct.pack('<III',kind,n,key);values+=data
newroot=bytearray(b[:24])+metadata+values;struct.pack_into('<I',newroot,8,len(newroot));newroot+=b'\0'*((-len(newroot))%4)
scn.items[root]=bytes(newroot);scn.original_items[root]=bytes(newroot)
validate_registry({k:(t,n,newroot[o:o+s]) for k,t,n,o,s in props(newroot,(0,u(newroot,8),root,u(newroot,16),u(newroot,20)))})
shutil.copytree(active,OUT)
manifest=json.loads((OUT/'manifest.json').read_text());vanilla=dict(base)
raw,entries,_=read_index(GAME/'fdata_package/root.rdb')
shadow=(OUT/'overlay/root.rdb').read_bytes();rr={}
pos=u(shadow,8)
while pos<len(shadow):
 size=struct.unpack_from('<Q',shadow,pos+8)[0];fid=u(shadow,pos+36);rr[fid]=bytearray(shadow[pos:pos+((size+3)&~3)]);pos+=(size+3)&~3
def place(fid,data,source):
 if source in res:entry=dict(res[source][1]);path=res[source][0];originalraw=path.read_bytes()
 else:
  # Existing restored IDs use the source type from the active root index.
  template=rr[source];typ=u(template,40);entry=dict(next(e for e in entries if e['type_id']==typ and e['c_size']==13));originalraw=raw
 record=bytearray(originalraw[entry['rdb_offset']:entry['rdb_offset']+((entry['entry_size']+3)&~3)])
 struct.pack_into('<I',record,36,fid);entry['id']=fid
 container=bytearray(wrap(originalraw,entry,data));struct.pack_into('<I',container,36,fid)
 target=f'vanilla/data/0x{fid:08x}.file';(OUT/target).write_bytes(container)
 vanilla[f'fdata_package/data/0x{fid:08x}.file']=target
 if fid in rr:record=rr[fid]
 ext=len(record)-entry['c_size']
 # Entry padding can follow the 13-byte extended data: use declared entry size.
 ext=struct.unpack_from('<Q',record,8)[0]-u(record,16)
 struct.pack_into('<I',record,44,0x20000);struct.pack_into('<H',record,ext,0xc01);struct.pack_into('<I',record,ext+6,len(container))
 struct.pack_into('<Q',record,24,len(data));rr[fid]=record
 manifest['dependencies']=[x for x in manifest.get('dependencies',[]) if int(x['id'],16)!=fid]
 manifest['dependencies'].append({'id':hex(fid),'sha256':hashlib.sha256(data).hexdigest()})
for fid,db in {**dbs,0x6d011726:scn}.items():place(fid,db.serialize(),fid)
for fid,asset in cloner.assets.items():place(fid,asset['payload'],asset['source'])
header=bytearray(shadow[:u(shadow,8)]);struct.pack_into('<I',header,16,len(rr));(OUT/'overlay/root.rdb').write_bytes(header+b''.join(rr[k] for k in sorted(rr)))
(OUT/'vanilla.tsv').write_text('\n'.join(k+'\t'+v for k,v in vanilla.items())+'\n')
catalog=[line.split('\t') for line in (OUT/'layer2.tsv').read_text().splitlines()]
number=next(i for i,row in enumerate(catalog,1) if row[1]=='(DoAxNaruto) Hanabi Hyuga (Adult)')
table=OUT/catalog[number-1][2];folder=table.parent
# Keep only independently addressed files in Hanabi's active table.
first=next(iter(cloner.assets));key=f'fdata_package/data/0x{first:08x}.file'
table.write_text(key+'\t'+vanilla[key]+'\n')
manifest['assets']=[a for a in manifest['assets'] if a['mod']!=number]
data=cloner.assets[first]['payload'];digest=hashlib.sha256(data).hexdigest()
manifest['assets'].append({'mod':number,'id':hex(first),'slot':'KOK_COS_001','payload_sha256':digest,'vanilla_sha256':digest})
with (folder/'mod.ini').open('a') as f:
 f.write('\n[PrivateModel]\nenabled=1\n')
 for label,kind in (('costume','COS'),('face','FACE'),('hair','HAIR')):
  f.write(f'source_{label}=0x{slot_hash("KOK_"+kind+"_001"):08x}\nwork_{label}=0x{slot_hash("KOK_"+kind+"_901"):08x}\n')
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
(OUT/'private_preview.json').write_text(json.dumps({'hidden_slots':newslots,'new_assets':len(cloner.assets),'preview_only':True,'source_generation':str(active),'texture_bindings':cloner.audit,'assets':{hex(k):{'source':hex(v['source']),'extension':v['extension']} for k,v in cloner.assets.items()}},indent=2))
print(json.dumps(verify(OUT),indent=2))
