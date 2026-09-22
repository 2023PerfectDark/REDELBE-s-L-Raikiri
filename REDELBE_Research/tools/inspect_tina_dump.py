import struct,sys,json
from pathlib import Path
d=Path(sys.argv[1]).read_bytes()
def u(fmt,o):return struct.unpack_from('<'+fmt,d,o)
count,table=u('II',8);streams={u('III',table+i*12)[0]:u('III',table+i*12)[1:] for i in range(count)}
ranges=[]
if 5 in streams:
 p=streams[5][1]
 for i in range(u('I',p)[0]):
  addr,size,off=u('QII',p+4+i*16);ranges.append((addr,size,off))
if 9 in streams:
 p=streams[9][1];n,off=u('QQ',p)
 for i in range(n):
  addr,size=u('QQ',p+16+i*16);ranges.append((addr,size,off));off+=size
def mem(addr,size):
 for a,n,o in ranges:
  if a<=addr<a+n:return d[o+addr-a:o+addr-a+min(size,a+n-addr)]
 return b''
e=streams[6][1];print('exception',u('IIQQII',e+8))
m=streams[4][1]
base=0
for i in range(u('I',m)[0]):
 o=m+4+i*108;b,n=u('QI',o);r=u('I',o+20)[0];name=d[r+4:r+4+u('I',r)[0]].decode('utf-16-le')
 if name.endswith('DOA6LR.exe'):base=b
print('base',hex(base))
ctx=u('II',e+160)[1]
for name,off in [('rbx',144),('rdi',176),('r12',216),('r13',224),('r14',232),('r15',240)]:
 v=u('Q',ctx+off)[0];print(name,hex(v),'memory',mem(v,32).hex())
 if name=='r13':print('vector at r13+1b8',mem(v+0x1b8,24).hex())
for a,n,o in ranges:
 b=d[o:o+n]
 for needle in (b'\x63\x73\x6d\xe0',):
  p=0
  while True:
   p=b.find(needle,p)
   if p<0:break
   if p+152<=len(b):
    rec=struct.unpack_from('<IIQQII15Q',b,p)
    if rec[4]==4 and rec[6] in (0x19930520,0x19930521,0x19930522) and rec[9]==base:
     print('C++ exception record',hex(a+p),[hex(x) for x in rec[:10]])
     obj=mem(rec[7],64);print('object',obj.hex())
     for q in range(0,len(obj)-7,8):
      ptr=struct.unpack_from('<Q',obj,q)[0];s=mem(ptr,180)
      if s:print('object field',q,hex(ptr),repr(s))
   p+=4
