"""Decode targeted original motor records using their own RNK field labels."""
from pathlib import Path
import sys,struct,json
from lr_resources import names_from_rnk
sys.stdout.reconfigure(encoding='utf-8')
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path('analysis/aura_definitions/285cb0c3.bin');b=p.read_bytes();names=names_from_rnk(Path('analysis/aura_definitions/285cb0c3.names').read_bytes())
sizes={0:1,1:1,2:2,3:2,4:4,5:4,8:4,10:16,12:8,13:12}
pos=struct.unpack_from('<I',b,8)[0];out=[]
while pos<len(b):
 sig,ver,size,fid=struct.unpack_from('<4I',b,pos)
 assert sig in (0x4b4f4449,0x4b4f4452),(hex(pos),hex(sig))
 header=24 if sig==0x4b4f4449 else 28
 count=struct.unpack_from('<I',b,pos+header-4)[0];ns=names.get(fid,[])
 if ns and 'ActRID_EFF_ATTACH' in ns[0]:
  cols=[];data=pos+header+count*12
  for i in range(count):
   typ,n,col=struct.unpack_from('<III',b,pos+header+12*i);length=sizes[typ]*n
   raw=b[data:data+length];fmt={0:'b',1:'B',2:'h',3:'H',4:'i',5:'I',8:'f',10:'f',12:'f',13:'f'}[typ]
   values=list(struct.unpack('<'+fmt*(length//struct.calcsize(fmt)),raw))
   cols.append(dict(name=ns[i+2] if len(ns)>i+2 else hex(col),hash=hex(col),type=typ,values=values,offset=data))
   data+=length
  out.append(dict(name=ns[0],id=hex(fid),offset=pos,columns=cols))
 pos=(pos+size+3)&~3
Path('analysis/aura_action_records'+('_lr' if len(sys.argv)>1 else '')+'.json').write_text(json.dumps(out,indent=2))
for e in out:
 if 'ResourceAction' in e['name'] or 'body_aura' in e['name']:print(json.dumps(e,ensure_ascii=False,indent=2))
