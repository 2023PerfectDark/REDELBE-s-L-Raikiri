"""Reset only this exact experimental loader's bounded UI log counter."""
import ctypes as C,ctypes.wintypes as W,sys,re,hashlib,struct
from pathlib import Path
k=C.WinDLL('kernel32',use_last_error=True);ps=C.WinDLL('psapi',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.CloseHandle.argtypes=[W.HANDLE]
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
k.WriteProcessMemory.argtypes=k.ReadProcessMemory.argtypes
ps.EnumProcessModulesEx.argtypes=[W.HANDLE,C.POINTER(W.HMODULE),W.DWORD,C.POINTER(W.DWORD),W.DWORD]
ps.GetModuleFileNameExW.argtypes=[W.HANDLE,W.HMODULE,W.LPWSTR,W.DWORD]
build=Path('experiments/mouse_menu/build');source=build/'dinput8.dll'
line=next(x for x in (build/'dinput8.map').read_text().splitlines() if '?layoutLogs@l2@@' in x)
rva=int(line.split()[2],16)-0x180000000
expected=hashlib.sha256(source.read_bytes()).hexdigest()
if len(sys.argv)==4:rva=int(sys.argv[2],16);expected=sys.argv[3]
h=k.OpenProcess(0x438,False,int(sys.argv[1]));assert h,C.get_last_error()
try:
 mods=(W.HMODULE*1024)();n=W.DWORD();assert ps.EnumProcessModulesEx(h,mods,C.sizeof(mods),C.byref(n),3)
 for module in mods[:n.value//C.sizeof(W.HMODULE)]:
  name=C.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,module,name,len(name));path=Path(name.value)
  if path.name.lower()!='dinput8.dll':continue
  if path.parent.name!='Dead or Alive 6 Last Round':continue
  assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,'Installed DLL differs from linked map'
  old=W.DWORD();got=C.c_size_t();assert k.ReadProcessMemory(h,module+rva,C.byref(old),4,C.byref(got)) and got.value==4
  assert old.value<100000000,'Unexpected counter'
  zero=W.DWORD(0);assert k.WriteProcessMemory(h,module+rva,C.byref(zero),4,C.byref(got)) and got.value==4
  print('UI tracing counter reset:',old.value);break
 else:raise RuntimeError('Exact experimental loader not found')
finally:k.CloseHandle(h)
