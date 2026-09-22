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
 import re,time
 mods=(W.HMODULE*1024)();needed=W.DWORD();ps.EnumProcessModulesEx(h,mods,C.sizeof(mods),C.byref(needed),3);base=mods[0]
 name=C.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,mods[0],name,len(name));assert name.value.lower().endswith('\\doa6lr.exe')
 log=(Path(name.value).parent/'REDELBE_LR/loader.log').read_text();matches=list(re.finditer(r'LAYER2 PRIVATE BATTLE TRACE player=0 object=([0-9A-Fa-f]+)',log));assert matches
 owner=int(matches[-1][1],16);model=u64(owner+0x18);container=u64(model+0x150)
 targets={'model':model,'container':container};raw=read(container,0x1000)
 for off in range(0,len(raw),8):
  ptr=struct.unpack_from('<Q',raw,off)[0]
  if ptr%8==0 and 0x100000000<=ptr<0x700000000000 and len(read(ptr,8))==8:targets['container+'+hex(off)]=ptr
 targets=dict(list(targets.items())[:40]);before={key:read(p,0x800) for key,p in targets.items()};time.sleep(0.25);after={key:read(p,0x800) for key,p in targets.items()}
 out=[]
 for key,p in targets.items():
  a=before[key];b=after[key];changes=[]
  if len(a)==len(b):
   for off in range(0,len(a)-3,4):
    if a[off:off+4]!=b[off:off+4]:changes.append(dict(offset=hex(off),before=a[off:off+4].hex(),after=b[off:off+4].hex()))
  out.append(dict(name=key,address=hex(p),before=a.hex(),after=b.hex(),changes=changes))
 dest=Path(__file__).resolve().parents[1]/'experiments/animation_browser/motion_state_samples.json';dest.write_text(json.dumps(dict(pid=int(sys.argv[1]),base=hex(base),objects=out),indent=2));print(json.dumps([dict(name=x['name'],address=x['address'],changed_fields=len(x['changes'])) for x in out]))
finally:k.CloseHandle(h)
