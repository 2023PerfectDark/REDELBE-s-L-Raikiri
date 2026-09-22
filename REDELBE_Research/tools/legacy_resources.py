"""Read-only DOA6 text-address RDB reader; never resolves REDELBE overrides."""
import struct,re,zlib
from pathlib import Path
def u32(b,p):return struct.unpack_from('<I',b,p)[0]
def u64(b,p):return struct.unpack_from('<Q',b,p)[0]
def index(path):
 b=Path(path).read_bytes()
 if b[:8]!=b'_DRK0000':raise ValueError('Bad RDB signature')
 p=u32(b,8);out={}
 while p<len(b):
  p=(p+3)&~3
  if p==len(b):break
  if b[p:p+8]!=b'IDRK0000':raise ValueError('Bad RDB entry')
  size=u64(b,p+8);cs=u32(b,p+16)
  if size<48 or cs>size-48 or p+size>len(b):raise ValueError('Entry bounds')
  fid=u32(b,p+36)
  if fid in out:raise ValueError('Duplicate resource')
  out[fid]={'id':fid,'path':Path(path),'address':b[p+size-cs:p+size].split(b'\0')[0].decode('ascii'),'size':u64(b,p+24),'type':u32(b,p+40)}
  p+=size
 return out
def extract(e):
 m=re.fullmatch(r'([0-9a-fA-F]+)@([0-9a-fA-F]+)(?:#([0-9a-fA-F]+))?(?:&([0-9a-fA-F]+))?',e['address'])
 if not m:
  if e['address']:raise ValueError('Unsupported legacy resource address')
  file=e['path'].parent/'data'/f"0x{e['id']:08x}.file";b=file.read_bytes();length=len(b)
 else:
  offset,length=int(m[1],16),int(m[2],16)
  file=Path(str(e['path'])+'.bin'+(str(int(m[3],16)) if m[3] else '')+('_'+str(int(m[4],16)) if m[4] else ''))
  with file.open('rb') as f:
   f.seek(offset);b=f.read(length)
 if len(b)!=length or b[:8]!=b'IDRK0000':raise ValueError('Missing/truncated legacy container')
 size,cs,usize=u64(b,8),u32(b,16),u64(b,24)
 if size>len(b) or size<48+cs or usize>512*1024*1024:raise ValueError('Invalid container size')
 payload=b[size-cs:size]
 if cs==usize:return payload
 out=bytearray();p=0
 while p<len(payload) and len(out)<usize:
  n=u32(payload,p);p+=4
  if not n or p+n>len(payload):raise ValueError('Bad compressed chunk')
  out.extend(zlib.decompress(payload[p:p+n]));p+=n
 if len(out)!=usize:raise ValueError('Legacy decompressed length mismatch')
 return bytes(out)
