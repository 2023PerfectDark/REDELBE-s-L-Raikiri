"""Audit generated mesh texture indices and independently addressed files."""
import json,struct
from pathlib import Path
from isolated_material_chain import Database,MaterialCloner
from dok_patch import u
root=Path(__file__).resolve().parents[1];p=root/'packages/hanabi_private_preview_v7'
meta=json.loads((p/'private_preview.json').read_text())
table=dict(x.split('\t') for x in (p/'vanilla.tsv').read_text().splitlines())
def payload(fid):
 b=(p/table[f'fdata_package/data/0x{fid:08x}.file']).read_bytes();return b[-u(b,16):]
ce=Database(payload(0xb290631c));common=Database(payload(0x2082ad97))
def section(b,key):
 pos=u(b,12)
 for _ in range(u(b,20)):
  size=u(b,pos+8)
  if u(b,pos)==0x47314d47:
   off=pos+0x30
   for _ in range(u(b,pos+0x2c)):
    sid,n=struct.unpack_from('<II',b,off)
    if sid==key:return b[off+8:off+n]
    off+=n
  pos+=size
 raise ValueError('Missing geometry section')
out={}
for name,cs in meta['hidden_slots'].items():
 motor=common.scalar(cs,0x68a6f779);dm=common.scalar(motor,0x0b6e1578)
 files={ext:ce.scalar(dm,k) for ext,k in [('g1m',0x8ab68b3f),('grp',0x3bbfd9a5),('mtl',0x7f0de9a3),('oidex',0x8dfd0584)]}
 tbc=ce.scalar(dm,MaterialCloner.TBC);ktid=ce.scalar(tbc,MaterialCloner.KTID)
 kt=payload(ktid);g=section(payload(files['g1m']),0x10002);pos=4;mats=[]
 for _ in range(u(g,0)):
  n=u(g,pos+4);pos+=16;entries=[]
  for _ in range(n):
   idx,_,typ=struct.unpack_from('<HHH',g,pos);pos+=12
   entries.append({'slot':idx,'category':typ,'in_range':idx<len(kt)//8})
  mats.append(entries)
 out[name]={'files':{k:hex(v) for k,v in files.items()},'ktid_rows':len(kt)//8,'material_count':len(mats),'invalid_indices':[x for m in mats for x in m if not x['in_range']],'texture_slots':mats}
(root/'analysis/isolation/private_mesh_bindings.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:{q:v for q,v in x.items() if q!='texture_slots'} for k,x in out.items()},indent=2))

# The body renders through MPR bundles; validate these as well as the base table.
from private_mesh_materials import materials
me=Database(payload(0xd956e4a2))
cs=meta['hidden_slots']['KOK_COS_901'];motor=common.scalar(cs,0x68a6f779);dm=common.scalar(motor,0x0b6e1578)
slots=materials(payload(ce.scalar(dm,0x8ab68b3f)))
base_refs=dict(struct.iter_unpack('<II',payload(ce.scalar(ce.scalar(dm,MaterialCloner.TBC),MaterialCloner.KTID))))
mi=common.values(cs,0x24c114f6)
assert len(mi)==len(slots)*common.scalar(cs,0xb3a1e5aa)
for i,mbe in enumerate(mi):
 kts=payload(me.scalar(mbe,0x0a3d837b))
 refs=list(struct.iter_unpack('<II',payload(me.scalar(me.scalar(mbe,MaterialCloner.TBC),MaterialCloner.KTID))))
 expected=slots[i%len(slots)]
 assert len(refs)==len(expected)==struct.unpack_from('<H',kts,8)[0]
 for j,(mesh_index,category,_) in enumerate(expected):
  assert refs[j]==(j,base_refs[mesh_index])
  assert struct.unpack_from('<H',kts,20+12*j)[0]==category
print('Verified all body variation bundles match the private mesh texture order.')
