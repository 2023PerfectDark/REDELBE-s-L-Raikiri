"""Capture live native facial resources without changing game state."""
import ctypes as C, ctypes.wintypes as W, json, struct, sys, time
from pathlib import Path
k=C.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
k.CloseHandle.argtypes=[W.HANDLE]
h=k.OpenProcess(0x410,False,int(sys.argv[1]));assert h
snapshot=json.loads(Path('REDELBE_Research/experiments/animation_browser/evaluator_objects.json').read_text());assert snapshot['pid']==int(sys.argv[1])
def read(p,n):
 b=C.create_string_buffer(n);got=C.c_size_t()
 return b.raw[:got.value] if p and k.ReadProcessMemory(h,p,b,n,C.byref(got)) else b''
def q(p):
 b=read(p,8);return struct.unpack('<Q',b)[0] if len(b)==8 else 0
out=Path('REDELBE_Research/experiments/doa5_victory_port/native_photo_expression_capture');out.mkdir(exist_ok=True)
records=[];seen=set()
try:
 for s in snapshot['samples']:
  objects={o['label']:int(o['address'],16) for o in s['objects']};native=objects['motion_native'];payload=q(native+24);head=read(payload,48)
  if len(head)!=48 or struct.unpack_from('<H',head,8)[0]!=344 or native in seen:continue
  seen.add(native);fps,frames=struct.unpack_from('<fH',head);table=read(q(payload+24),344*4)
  if len(table)!=1376:continue
  keys=q(payload+32);end=0;vectors=0;valid=True
  for entry in struct.unpack('<344I',table):
   off=(entry>>16)*4
   for _ in range(entry&15):
    raw=read(keys+off,8)
    if len(raw)!=8:valid=False;break
    op,n,first=struct.unpack('<HHI',raw)
    if op>2 or n>65535 or first+n>500000:valid=False;break
    off+=8+((n*2+3)&~3);vectors=max(vectors,first+n)
   end=max(end,off)
  if not valid or end>4000000:continue
  keydata=read(keys,end);packed=read(q(payload+40),vectors*32)
  if len(keydata)!=end or len(packed)!=vectors*32:continue
  data=struct.pack('<8sIfHHIII',b'_A2G0400',32+len(table)+end+len(packed),fps,frames,344<<4,end,vectors,0)+table+keydata+packed
  leaf=f'native_{native:x}_{frames}frames.g1a';(out/leaf).write_bytes(data)
  sk=objects['skeleton'];samples=[]
  for _ in range(12):samples.append(read(sk,0x100).hex());time.sleep(.04)
  records.append(dict(file=leaf,native=hex(native),payload_header=head.hex(),native_header=read(native,32).hex(),skeleton=hex(sk),skeleton_samples=samples,fps=fps,frames=frames))
 (out/'capture.json').write_text(json.dumps(records,indent=2));print(json.dumps([dict(file=r['file'],fps=r['fps'],frames=r['frames']) for r in records]))
finally:k.CloseHandle(h)
