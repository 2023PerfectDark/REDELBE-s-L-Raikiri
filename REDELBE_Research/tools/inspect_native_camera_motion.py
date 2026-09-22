"""Read-only snapshot of pointers actually observed by the native evaluator."""
import ctypes as C, ctypes.wintypes as W, json, re, struct, sys
from pathlib import Path
k=C.WinDLL('kernel32',use_last_error=True);ps=C.WinDLL('psapi',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
k.CloseHandle.argtypes=[W.HANDLE]
ps.EnumProcessModulesEx.argtypes=[W.HANDLE,C.POINTER(W.HMODULE),W.DWORD,C.POINTER(W.DWORD),W.DWORD]
ps.GetModuleFileNameExW.argtypes=[W.HANDLE,W.HMODULE,W.LPWSTR,W.DWORD]
h=k.OpenProcess(0x410,False,int(sys.argv[1]));assert h,C.get_last_error()
def read(p,n):
 b=C.create_string_buffer(n);got=C.c_size_t()
 return b.raw[:got.value] if p and k.ReadProcessMemory(h,p,b,n,C.byref(got)) else b''
def q(p):
 b=read(p,8);return struct.unpack('<Q',b)[0] if len(b)==8 else 0
try:
 mods=(W.HMODULE*1024)();needed=W.DWORD();ps.EnumProcessModulesEx(h,mods,C.sizeof(mods),C.byref(needed),3)
 base=mods[0];name=C.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,mods[0],name,len(name))
 assert name.value.lower().endswith('\\doa6lr.exe')
 log=(Path(name.value).parent/'REDELBE_LR/loader.log').read_text()
 hits=list(re.finditer(r'NATIVE CAMERA camera=([0-9A-F]+) caller_rva=([0-9a-f]+) motion=([0-9A-F]+) time=([^ ]+)',log))
 selected={}
 for hit in hits[-200:]:
  if int(hit[3],16):selected[hit[3]]=hit
 out=[]
 for hit in selected.values():
  camera,handle=int(hit[1],16),int(hit[3],16)
  targets={'camera':camera,'motion_handle':handle,'motion_descriptor':q(handle+0x18),'motion_native':q(handle+0x20)}
  targets['motion_payload']=q(targets['motion_native']+0x10)
  objects=[]
  for label,p in targets.items():
   raw=read(p,0x300);v=q(p)
   objects.append(dict(label=label,address=hex(p),vtable_rva=hex(v-base) if base<=v<base+0x7000000 else None,raw=raw.hex()))
  out.append(dict(time=hit[4],objects=objects))
 dest=Path(__file__).resolve().parents[1]/'experiments/animation_browser/native_camera_motion_objects.json'
 dest.write_text(json.dumps(dict(pid=int(sys.argv[1]),base=hex(base),samples=out),indent=2))
 print(json.dumps(dict(base=hex(base),samples=[dict(time=x['time'],objects=[{k:v for k,v in a.items() if k!='raw'} for a in x['objects']]) for x in out])))
finally:k.CloseHandle(h)

