import json,struct,ctypes as c,ctypes.wintypes as w
from pathlib import Path
r=json.load(open('analysis/aura_effect_instances.json'));k=c.WinDLL('kernel32');k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE;k.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)];k.CloseHandle.argtypes=[w.HANDLE];h=k.OpenProcess(0x410,False,r['pid']);assert h
def read(p,n):
 b=c.create_string_buffer(n);got=c.c_size_t();k.ReadProcessMemory(h,p,b,n,c.byref(got));return b.raw[:got.value]
rows=[];ids={0x7fa35bed,0x6360b6f0,0xf56f07de,0xc0a1ca5d,0xa7a17260,0x85fef54e}
for row in r['hits']:
 b=bytes.fromhex(row['object'])
 if not struct.unpack_from('<Q',b,0xb0)[0]:continue
 pointers={f'obj_{off:x}':struct.unpack_from('<Q',b,off)[0] for off in (0xa8,0xb0,0xc0)}
 d=bytes.fromhex(row['descriptor'])
 if len(d)>=0x168:pointers['desc_e0']=struct.unpack_from('<Q',d,0xe0)[0];pointers['desc_160']=struct.unpack_from('<Q',d,0x160)[0]
 chunks={name:read(p,1024).hex() for name,p in pointers.items() if p}
 rows.append(dict(address=row['address'],pointers={k:hex(v) for k,v in pointers.items()},chunks=chunks))
 for name,chunk in chunks.items():
  q=bytes.fromhex(chunk)
  found=[hex(fid) for fid in ids if struct.pack('<I',fid) in q]
  if found:print(row['address'],name,found)
Path('analysis/aura_active_links.json').write_text(json.dumps(rows,indent=2));print('active inspected',len(rows));k.CloseHandle(h)
