"""Strict same-size DOK property edits; all other bytes remain untouched."""
import struct
UNIT=(1,1,2,2,4,4,0,0,4,0,16,0,8,12)
def u(b,p):return struct.unpack_from('<I',b,p)[0]
def records(b):
 if b[:8]!=b'_DOK0000':raise ValueError('Invalid DOK')
 p=u(b,8)
 while p<len(b):
  if b[p:p+8]!=b'IDOK0000':raise ValueError('Invalid DOK record')
  size,oid,typ,count=struct.unpack_from('<IIII',b,p+8)
  if size<24+count*12 or p+size>len(b):raise ValueError('Invalid DOK bounds')
  yield p,size,oid,typ,count
  p+=(size+3)&~3
def props(b,rec):
 p,size,oid,typ,count=rec;v=p+24+count*12
 for i in range(count):
  kind,n,key=struct.unpack_from('<III',b,p+24+i*12)
  if kind>=len(UNIT) or not UNIT[kind]:raise ValueError(f'Unsupported property type {kind}')
  length=UNIT[kind]*n
  if v+length>p+size:raise ValueError('Property outside record')
  yield key,kind,n,v,length
  v+=length
def patch(b,changes):
 result=bytearray(b);byoid={}
 for c in changes:byoid.setdefault(c['oid'],[]).append(c)
 found=set()
 for rec in records(b):
  if rec[2] not in byoid:continue
  pp={key:(kind,n,offset,length) for key,kind,n,offset,length in props(b,rec)}
  for c in byoid[rec[2]]:
   key=c.get('property',0x6c7321d2);kind,n,offset,length=pp[key]
   if length!=4 or n!=1 or u(b,offset)!=c['lr_resource']:raise ValueError(f'Reference conflict for {rec[2]:08x}/{key:08x}; rebuild dependency plan')
   struct.pack_into('<I',result,offset,c['old_resource']);found.add((rec[2],key))
 if len(found)!=len(changes):raise ValueError('Missing/duplicate restoration property')
 return bytes(result)
