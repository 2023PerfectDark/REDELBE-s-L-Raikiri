"""Read-only, bounded character-preview object inspection for a supplied PID."""
import ctypes as C, ctypes.wintypes as W, json, struct, sys
from pathlib import Path
k=C.WinDLL('kernel32',use_last_error=True);ps=C.WinDLL('psapi',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
k.CloseHandle.argtypes=[W.HANDLE]
ps.EnumProcessModulesEx.argtypes=[W.HANDLE,C.POINTER(W.HMODULE),W.DWORD,C.POINTER(W.DWORD),W.DWORD]
ps.GetModuleFileNameExW.argtypes=[W.HANDLE,W.HMODULE,W.LPWSTR,W.DWORD]
h=k.OpenProcess(0x410,False,int(sys.argv[1]));assert h,C.get_last_error()
def read(p,n):
 buf=C.create_string_buffer(n);got=C.c_size_t()
 if not p or not k.ReadProcessMemory(h,p,buf,n,C.byref(got)):return b''
 return buf.raw[:got.value]
def u64(p):
 b=read(p,8);return struct.unpack('<Q',b)[0] if len(b)==8 else 0
def u32(p):
 b=read(p,4);return struct.unpack('<I',b)[0] if len(b)==4 else 0
try:
 mods=(W.HMODULE*1024)();needed=W.DWORD();ps.EnumProcessModulesEx(h,mods,C.sizeof(mods),C.byref(needed),3)
 base=mods[0];name=C.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,mods[0],name,len(name));assert name.value.lower().endswith('\\doa6lr.exe')
 log=Path(name.value).parent/'REDELBE_LR/loader.log'
 import re
 roots=[]
 mapping=u64(base+0x5ea7be8);head=u64(mapping)
 for side in range(2):
  node=u64(head+8);found=head
  for n in range(64):
   if not node or node==head or read(node+25,1)!=b'\0':break
   key=read(node+32,1)
   if not key:break
   if key[0]>=side:found=node;node=u64(node)
   else:node=u64(node+16)
  if found!=head and read(found+32,1)==bytes([side]):roots.append((side,u64(found+40)))
 queue=[(p,0,'P'+str(side+1)) for side,p in roots];seen=set();out=[]
 while queue and len(out)<160:
  p,depth,origin=queue.pop(0)
  if p in seen:continue
  seen.add(p);raw=read(p,0x500)
  if len(raw)!=0x500:continue
  v=u64(p);typ='';vtable=None
  if base<=v<base+0xa000000:
   vtable=hex(v-base);col=u64(v-8)
   if base<=col<base+0xa000000 and u32(col)==1:
    td=base+u32(col+12);typ=read(td+16,160).split(b'\0')[0].decode('ascii','replace')
  out.append(dict(address=hex(p),depth=depth,origin=origin,type=typ,vtable=vtable,data=raw.hex()))
  if depth>=2:continue
  for off in range(0,len(raw),8):
   q=struct.unpack_from('<Q',raw,off)[0]
   if q%8==0 and 0x100000000<=q<0x700000000000 and q not in seen:
    qv=u64(q)
    if base<=qv<base+0xa000000 or depth==0:queue.append((q,depth+1,hex(p)+'+'+hex(off)))
 dest=Path(__file__).resolve().parents[1]/'experiments/animation_browser/fighter_objects.json';dest.write_text(json.dumps(dict(pid=int(sys.argv[1]),base=hex(base),objects=out),indent=2))
 print(json.dumps(dict(roots=roots,objects=len(out))))
finally:k.CloseHandle(h)
