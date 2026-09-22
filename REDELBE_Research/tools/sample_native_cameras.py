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
 import time
 root=Path(__file__).resolve().parents[1]/'experiments/animation_browser'
 source=json.loads((root/'native_camera_scan.json').read_text());assert source['pid']==int(sys.argv[1]),'rescan after restart'
 addresses=[int(x['address'],16) for x in source['hits']]
 samples=[]
 for iteration in range(6):
  rows=[]
  for address in addresses:
   if q(address)!=base+0x4272448:continue
   data=read(address,0x69d0)
   if len(data)!=0x69d0:continue
   rows.append(dict(address=hex(address),position=struct.unpack_from('<3f',data,0x2ea0),rotation=struct.unpack_from('<4f',data,0x2eac),eye=struct.unpack_from('<4f',data,0x2ee0),raw=data.hex()))
  samples.append(rows);time.sleep(.25)
 (root/'native_camera_samples.json').write_text(json.dumps(dict(pid=int(sys.argv[1]),base=hex(base),samples=samples),indent=2))
 for row in samples[-1]:
  older=next((r for r in samples[0] if r['address']==row['address']),None)
  print(json.dumps({k:v for k,v in row.items() if k!='raw'}|{'changed':older is not None and older['raw']!=row['raw']}))
finally:k.CloseHandle(h)
