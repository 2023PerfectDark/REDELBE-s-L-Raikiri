import json, struct
from pathlib import Path
from lr_resources import GAME, read_index, extract
from dok_patch import records,props,u
ROOT=Path(__file__).resolve().parents[1]
resources={}
for path in (GAME/'fdata_package').glob('*.rdb'):
 for e in read_index(path)[1]:resources[e['id']]=(path,e)
b=extract(*resources[0xd956e4a2]);rr={r[2]:r for r in records(b)}
assets=GAME/'KashiraProjects/REDELBE_LR_Hanabi/Content_Legacy/REDELBE_Layer2/KOK_COS_001'
report={}
for p in assets.iterdir():
 if p.suffix not in ('.mtl','.ktid'):continue
 data=p.read_bytes();words=list(struct.unpack('<'+'I'*(len(data)//4),data))
 found=[]
 for i,w in enumerate(words):
  if w in rr:
   rec=rr[w]
   found.append({'offset':i*4,'oid':hex(w),'type':hex(rec[3]),'properties':[{'key':hex(k),'kind':t,'count':n,'values':[hex(u(b,o+j)) for j in range(0,s,4)] if s%4==0 else b[o:o+s].hex()} for k,t,n,o,s in props(b,rec)]})
 matches=[]
 wanted=set(words)-set(range(256))
 for rec in rr.values():
  for key,kind,n,o,s in props(b,rec):
   if s%4:continue
   values=[u(b,o+j) for j in range(0,s,4)]
   hits=wanted.intersection(values)
   if hits:matches.append({'oid':hex(rec[2]),'type':hex(rec[3]),'property':hex(key),'kind':kind,'hits':[hex(h) for h in hits]})
 report[p.name]={'words':[hex(w) for w in words],'material_objects':found,'reverse_matches':matches}
(ROOT/'analysis/isolation/hanabi_material_graph.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
