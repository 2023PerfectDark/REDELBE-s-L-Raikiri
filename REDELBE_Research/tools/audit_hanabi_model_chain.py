"""Read-only object-chain audit for independently addressable Hanabi models."""
import json
from pathlib import Path
from lr_resources import GAME, read_index, extract
from dok_patch import records,props,u
ROOT=Path(__file__).resolve().parents[1]
res={}
for path in (GAME/'fdata_package').glob('*.rdb'):
 for e in read_index(path)[1]:res[e['id']]=(path,e)
dbs={fid:extract(*res[fid]) for fid in (0xb290631c,0xd956e4a2,0x718ccb8b)}
allrec={}
for fid,b in dbs.items():
 for rec in records(b):allrec.setdefault(rec[2],[]).append((fid,rec))
models={0x6a2367a7,0xd7feb38f,0xfdc5c014}
report=[]
for fid,b in dbs.items():
 for rec in records(b):
  values=[]
  for key,kind,n,o,s in props(b,rec):
   if s%4==0:values.extend(u(b,o+j) for j in range(0,s,4))
  if not models.intersection(values):continue
  row={'database':hex(fid),'oid':hex(rec[2]),'type':hex(rec[3]),'properties':[]}
  for key,kind,n,o,s in props(b,rec):
   vv=[u(b,o+j) for j in range(0,s,4)] if s%4==0 else []
   row['properties'].append({'key':hex(key),'kind':kind,'count':n,'values':[hex(v) for v in vv], 'object_targets':[hex(v) for v in vv if v in allrec]})
  report.append(row)
out=ROOT/'analysis/isolation/hanabi_model_chain.json';out.write_text(json.dumps(report,indent=2))
summary=[]
for row in report:
 seen=set();queue=[int(row['oid'],16)];texture_resources=set()
 while queue:
  oid=queue.pop()
  if oid in seen:continue
  seen.add(oid)
  for fid,rec in allrec.get(oid,[]):
   bb=dbs[fid]
   for key,kind,n,o,s in props(bb,rec):
    if kind not in (4,5):continue
    vv=[u(bb,o+j) for j in range(0,s,4)]
    if key==0x6c7321d2:texture_resources.update(vv)
    queue.extend(v for v in vv if v in allrec and v not in seen)
 summary.append({'root':row['oid'],'reachable_objects':len(seen),'textures':[hex(x) for x in sorted(texture_resources)],'objects':[hex(x) for x in sorted(seen)]})
(ROOT/'analysis/isolation/hanabi_model_closure.json').write_text(json.dumps(summary,indent=2))
print(json.dumps([{k:v for k,v in s.items() if k!='objects'} for s in summary],indent=2))
