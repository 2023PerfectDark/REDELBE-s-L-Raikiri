import sys,json,struct,time
from pathlib import Path
sys.path.insert(0,'tools')
from lr_resources import *
from build_aura_test import records,columns
out=[]
for index in ('root','system'):
 ip=GAME/f'fdata_package/{index}.rdb';raw,es,_=read_index(ip)
 for e in es:
  if e['type_id']!=0x20a6a0bb or e['file_size']>100*1024**2:continue
  try:b=extract(ip,e)
  except (ValueError,OSError):continue
  if b[:4]!=b'_DOK' or struct.pack('<I',0x0c3844a7) not in b:continue
  matches=[]
  for p,z,fid in records(b):
   if fid not in (0x0c3844a7,0x399961):continue
   rec=b[p:z];v=columns(rec).get(0xe1773a02)
   matches.append(dict(id=hex(fid),offset=p,tracks=v[4] if v else None))
  if matches:
   row=dict(index=index,resource=hex(e['id']),size=len(b),matches=matches);out.append(row);print(row,flush=True)
   dest=Path('analysis/aura_lr_all');dest.mkdir(exist_ok=True);(dest/f'{e["id"]:08x}.bin').write_bytes(b)
Path('analysis/aura_lr_all_matches.json').write_text(json.dumps(out,indent=2))
