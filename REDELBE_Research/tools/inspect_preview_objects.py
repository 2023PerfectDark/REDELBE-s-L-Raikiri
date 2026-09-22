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
 base=mods[0];name=C.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,mods[0],name,len(name))
 assert name.value.lower().endswith('\\dead or alive 6 last round\\doa6lr.exe'),name.value
 def obj(p,size=0x200):
  v=u64(p);col=u64(v-8) if v else 0;td=base+u32(col+12) if col else 0
  raw=read(p,size)
  return dict(address=hex(p),vtable=hex(v-base),type=read(td+16,128).split(b'\0')[0].decode('ascii','replace') if td else '',data=raw.hex())
 # Verified from the pristine 1.11 script wrapper; research only, not runtime loader.
 root=u64(base+0x5e034b8);out=dict(base=hex(base),root=hex(root),players=[])
 for player in range(2):
  owner=root+0x98+player*0x2d8;parts=[]
  for offset,label in [(0,'body'),(0x38,'hair'),(0x70,'face')]:
   req=u64(owner+offset);entry=dict(part=label,handle=hex(owner+offset),control=hex(u64(owner+offset+8)),request=obj(req,0xa0))
   if req:
    for off,key in [(0x60,'animation'),(0x68,'model')]:
     p=u64(req+off);entry[key]=obj(p,0x320)
     if key=='model' and p:entry['model_container']=obj(u64(p+0x150),0x180)
   parts.append(entry)
  out['players'].append(parts)
 Path('analysis/preview_objects_live.json').write_text(json.dumps(out,indent=2))
 for parts in out['players']:
  for p in parts:print(p['part'],[(key,{k:v for k,v in value.items() if k!='data'}) for key,value in p.items() if isinstance(value,dict)])
finally:k.CloseHandle(h)
