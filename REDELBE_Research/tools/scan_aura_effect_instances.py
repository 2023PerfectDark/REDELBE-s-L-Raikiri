"""Read-only scan for live effect instances identified by the captured native trace."""
import ctypes as c,ctypes.wintypes as w,struct,json,time,sys
from pathlib import Path
k=c.WinDLL('kernel32',use_last_error=True);ps=c.WinDLL('psapi')
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)];k.CloseHandle.argtypes=[w.HANDLE]
class MBI(c.Structure):
 _fields_=[('base',c.c_void_p),('allocation',c.c_void_p),('ap',w.DWORD),('partition',w.WORD),('size',c.c_size_t),('state',w.DWORD),('protect',w.DWORD),('type',w.DWORD)]
k.VirtualQueryEx.argtypes=[w.HANDLE,c.c_void_p,c.POINTER(MBI),c.c_size_t];k.VirtualQueryEx.restype=c.c_size_t
ps.EnumProcessModules.argtypes=[w.HANDLE,c.c_void_p,w.DWORD,c.POINTER(w.DWORD)]
ps.GetModuleFileNameExW.argtypes=[w.HANDLE,w.HMODULE,w.LPWSTR,w.DWORD]
pid=int(sys.argv[1]);h=k.OpenProcess(0x410,False,pid);assert h
mods=(w.HMODULE*1024)();needed=w.DWORD();assert ps.EnumProcessModules(h,mods,c.sizeof(mods),c.byref(needed));base=mods[0]
name=c.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,None,name,len(name));assert name.value.lower().endswith('\\doa6lr.exe')
def read(p,n):
 b=c.create_string_buffer(n);got=c.c_size_t();k.ReadProcessMemory(h,p,b,n,c.byref(got));return b.raw[:got.value]
pattern=struct.pack('<Q',base+0x4be3530);address=0;total=0;start=time.monotonic();hits=[]
try:
 while address<0x7fffffffffff and total<8*1024**3 and time.monotonic()-start<45:
  m=MBI()
  if not k.VirtualQueryEx(h,address,c.byref(m),c.sizeof(m)):break
  address=int(m.base or 0)+m.size
  if m.state!=0x1000 or m.type!=0x20000 or m.protect&0x101 or not m.protect&0xee:continue
  for off in range(0,m.size,4*1024**2):
   data=read(int(m.base)+off,min(4*1024**2,m.size-off));total+=len(data);p=0
   while (p:=data.find(pattern,p))>=0:
    addr=int(m.base)+off+p;obj=read(addr,384)
    if len(obj)==384 and len(hits)<1000:
     ptr=struct.unpack_from('<Q',obj,0xa0)[0];desc=read(ptr,512) if ptr else b''
     hits.append(dict(address=hex(addr),object=obj.hex(),resource=hex(ptr),descriptor=desc.hex()))
    p+=8
   if total>=8*1024**3 or time.monotonic()-start>=45:break
finally:k.CloseHandle(h)
Path('analysis/aura_effect_instances.json').write_text(json.dumps(dict(pid=pid,base=hex(base),bytes=total,seconds=time.monotonic()-start,hits=hits),indent=2))
print('Read-only scan:',len(hits),'instances;',total,'bytes;',round(time.monotonic()-start,2),'seconds')
for row in hits[:30]:print(row['address'],row['resource'],row['descriptor'][:64])
