import json,struct,ctypes as c,ctypes.wintypes as w
from pathlib import Path
r=json.load(open('analysis/aura_native_trace.json'));k=c.WinDLL('kernel32');k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE;k.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)];k.CloseHandle.argtypes=[w.HANDLE];h=k.OpenProcess(0x410,False,r['pid'])
def read(p,n):
 b=c.create_string_buffer(n);got=c.c_size_t();k.ReadProcessMemory(h,p,b,n,c.byref(got));return b.raw[:got.value]
rows=[]
for addr in sorted({int(x['registers']['rcx'],16) for x in r['hits']}):
 b=read(addr,384);ptr=struct.unpack_from('<Q',b,0xa0)[0];d=read(ptr,512);rows.append(dict(object=hex(addr),resource=hex(ptr),data=d.hex()));print(hex(addr),hex(ptr),d[:64].hex())
Path('analysis/aura_native_objects.json').write_text(json.dumps(rows,indent=2));k.CloseHandle(h)
