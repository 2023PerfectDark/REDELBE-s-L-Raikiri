import sys,struct,csv,json
from pathlib import Path
sys.path.insert(0,'tools')
from lr_resources import *
from build_aura_test import records,columns
names={int(r[0],16):r[1] for r in csv.reader((GAME/'KashiraProjects/Name2Hash/DOA6LR.csv').open(encoding='utf-8-sig')) if len(r)==2};targets={0x39fc500d,0x1ddfc7f4,0x07072dbf,0x4fba76c5};out=[]
for index in ('root','system'):
 ip=GAME/'fdata_package'/f'{index}.rdb';es={e['id']:e for e in read_index(ip)[1]}
 for fid,e in es.items():
  name=names.get(fid,'')
  if 'kidsobjdb' not in name or e['file_size']>60000000:continue
  try:b=extract(ip,e)
  except FileNotFoundError:continue
  if b[:4]!=b'_DOK' or not any(struct.pack('<I',x) in b for x in targets):continue
  for p,z,oid in records(b):
   if oid not in targets:continue
   row=dict(database=name,id=hex(oid),refs=[]);r=b[p:z]
   for key,(_,d,n,t,c) in columns(r).items():
    if n==4:
     v=struct.unpack_from('<I',r,d)[0]
     if v in es:row['refs'].append(dict(property=hex(key),id=hex(v),name=names.get(v)))
   out.append(row);print(json.dumps(row))
Path('analysis/aura_texture_lookup.json').write_text(json.dumps(out,indent=2))
