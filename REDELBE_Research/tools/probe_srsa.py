from pathlib import Path
import struct,collections
def u(b,p):return struct.unpack_from('<I',b,p)[0]
for path in Path('analysis/audio').glob('*.srsa'):
 b=path.read_bytes();p=80;counts=collections.Counter();examples=[]
 while p<len(b):
  sig,size,fid,flags=struct.unpack_from('<IIII',b,p)
  if size<16 or p+size>len(b):raise ValueError('bad entry')
  fmt=None
  if sig==0x70cbccc5:fmt=u(b,p+u(b,p+u(b,p+20)))
  counts[(hex(sig),hex(fmt or 0))]+=1
  if len(examples)<3:examples.append((hex(fid),hex(flags),b[p:p+min(size,96)].hex()))
  p+=size
 print(path.name,dict(counts),examples if 'CHA_KOK' in path.name else '')
