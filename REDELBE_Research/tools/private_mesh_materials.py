"""Build private material bundles from the mesh and its private base table."""
import struct
from dok_patch import u
from isolated_material_chain import MaterialCloner

def materials(data):
 pos=u(data,12)
 for _ in range(u(data,20)):
  size=u(data,pos+8)
  if u(data,pos)==0x47314d47:
   off=pos+0x30
   for _ in range(u(data,pos+0x2c)):
    sid,n=struct.unpack_from('<II',data,off)
    if sid==0x10002:
     p=off+12;out=[]
     for _ in range(u(data,off+8)):
      count=u(data,p+4);p+=16;slots=[]
      for _ in range(count):
       index,_,primary,physics=struct.unpack_from('<4H',data,p)
       slots.append((index,primary,physics));p+=12
      out.append(slots)
     if p!=off+n:raise ValueError('Material section bounds mismatch')
     return out
    off+=n
  pos+=size
 raise ValueError('No mesh materials')

def build(cloner,template,slots,base_table):
 db=cloner.locate(template)
 tbc=db.scalar(template,MaterialCloner.TBC)
 kts_source=db.scalar(template,0x0a3d837b)
 refs=dict(struct.iter_unpack('<II',base_table))
 physics={1:1,2:59,3:8,5:0,8:0,19:0,21:0,30:30,37:37,41:0,47:47,55:0,62:0}
 kts=struct.pack('<4sIHHI',b'GSTK',0,len(slots),1,1)
 table=bytearray()
 for j,(index,primary,ph) in enumerate(slots):
  if index not in refs:raise ValueError(f'Missing mesh texture index {index}')
  cloner.locate(refs[index])
  table+=struct.pack('<II',j,refs[index])
  kts+=struct.pack('<I4H',j,primary,physics.get(primary,ph),4,4)
 kts_id=cloner.asset(kts_source,kts,'.kts')
 table_id=cloner.asset(db.scalar(tbc,MaterialCloner.KTID),table,'.ktid')
 private_tbc=db.clone(tbc,cloner.oid(),{MaterialCloner.KTID:table_id})
 return db.clone(template,cloner.oid(),{MaterialCloner.TBC:private_tbc,0x0a3d837b:kts_id})
