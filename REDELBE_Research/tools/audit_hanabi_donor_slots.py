"""Read current LR's costume/face/hair and material chains for donor preparation."""
import json,struct
from pathlib import Path
from lr_resources import GAME,read_index,extract
from dok_patch import records,props,u
ROOT=Path(__file__).resolve().parents[1]
res={e['id']:(p,e) for p in (GAME/'fdata_package').glob('*.rdb') for e in read_index(p)[1]}
dbs={fid:extract(*res[fid]) for fid in (0x6d011726,0xb290631c,0x2082ad97,0xd956e4a2)}
objects={}
for fid,b in dbs.items():
 for rec in records(b):objects.setdefault(rec[2],[]).append((fid,rec))
def record(oid):
 matches=objects.get(oid,[])
 if len(matches)!=1:raise ValueError(f'Ambiguous or missing object {oid:08x}')
 fid,r=matches[0];b=dbs[fid]
 return {k:b[o:o+s] for k,t,n,o,s in props(b,r)}
def words(p,key):
 b=p.get(key,b'');return list(struct.unpack('<'+'I'*(len(b)//4),b))
def scalar(p,key):return words(p,key)[0]
b=dbs[0x6d011726]
root=next(r for r in records(b) if r[3]==0xdac911d7)
p=record(root[2]);names=p[0x4d269345].decode('ascii').strip('\0').split('\0');oids=words(p,0x8f9f2da6)
assert len(names)==len(oids)
slots=dict(zip(names,oids));report={}
for name in ('KOK_COS_001','KOK_FACE_001','KOK_HAIR_001'):
 cs=record(slots[name]);motor=record(scalar(cs,0x68a6f779));dm=record(scalar(motor,0x0b6e1578))
 materials=set(words(cs,0x24c114f6))|set(words(motor,0x34cf9e5c)[1::2]);materials.discard(0)
 bindings=[]
 for mbe in materials:
  m=record(mbe);tbc=record(scalar(m,0xf92c5190));ktid=scalar(tbc,0x7a1e1ef8)
  tex=[]
  for index,oid in struct.iter_unpack('<II',extract(*res[ktid])):
   t=record(oid);tex.append({'index':index,'object':oid,'resource':scalar(t,0x6c7321d2)})
  bindings.append({'material':mbe,'ktid':ktid,'textures':tex})
 report[name]={'setting':slots[name],'motor':scalar(cs,0x68a6f779),'model':scalar(motor,0x0b6e1578),'g1m':scalar(dm,0x8ab68b3f),'bindings':bindings}
out={'source_slots':report,'possible_background_names':[n for n in names if not any(x in n for x in ('_COS_','_FACE_','_HAIR_','_GLS_'))], 'all_slots':slots}
(ROOT/'analysis/isolation/hanabi_donor_chains.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'sources':{k:{'materials':len(v['bindings']),'texture_bindings':sum(len(m['textures']) for m in v['bindings'])} for k,v in report.items()},'possible_background_names':out['possible_background_names'][:40],'total_slots':len(slots)},indent=2))
