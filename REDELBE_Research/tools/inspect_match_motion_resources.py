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
 graph=json.loads(Path('REDELBE_Research/experiments/animation_browser/match_model_graph.json').read_text())
 for item in graph['objects']:
  if item['vtable']!='0x4257c28':continue
  p=int(item['address'],16);raw=read(p,32);payload=read(q(p+24),48)
  print(item['address'],'native',raw.hex(),'payload',payload.hex())
finally:k.CloseHandle(h)
