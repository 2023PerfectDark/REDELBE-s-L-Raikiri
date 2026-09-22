import json,struct
from pathlib import Path
from lr_resources import GAME,read_index,extract
from dok_patch import records,props,u
ROOT=Path(__file__).resolve().parents[1]
res={}
for path in (GAME/'fdata_package').glob('*.rdb'):
 for e in read_index(path)[1]:res[e['id']]=(path,e)
b=extract(*res[0xd956e4a2]);rr={r[2]:r for r in records(b)}
results=[]
for fid in (0x27d41bb4,0x75624ccc):
 data=extract(*res[fid]);rows=[]
 for i,x in struct.iter_unpack('<II',data):
  rows.append({'index':i,'hash':hex(x),'exists':x in rr})
 results.append({'file':hex(fid),'rows':rows})
(ROOT/'analysis/isolation/hanabi_native_texture_bindings.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
