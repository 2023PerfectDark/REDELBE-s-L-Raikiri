from pathlib import Path
import ctypes as c,ctypes.wintypes as w,hashlib,re,sys
root=Path('REDELBE_Research/experiments/hair_color/native_test/build');expected=root/'dinput8.dll'
k=c.WinDLL('kernel32',use_last_error=True);ps=c.WinDLL('psapi',use_last_error=True)
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)]
k.WriteProcessMemory.argtypes=k.ReadProcessMemory.argtypes;k.CloseHandle.argtypes=[w.HANDLE]
ps.EnumProcessModulesEx.argtypes=[w.HANDLE,c.POINTER(w.HMODULE),w.DWORD,c.POINTER(w.DWORD),w.DWORD]
ps.GetModuleFileNameExW.argtypes=[w.HANDLE,w.HMODULE,w.LPWSTR,w.DWORD]
h=k.OpenProcess(0x438,False,int(sys.argv[1]));assert h
try:
 mods=(w.HMODULE*1024)();needed=w.DWORD();assert ps.EnumProcessModulesEx(h,mods,c.sizeof(mods),c.byref(needed),3)
 found=[]
 for m in mods[:needed.value//c.sizeof(w.HMODULE)]:
  name=c.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,m,name,len(name))
  if name.value.lower().endswith('\\dead or alive 6 last round\\dinput8.dll'):
   assert hashlib.sha256(Path(name.value).read_bytes()).digest()==hashlib.sha256(expected.read_bytes()).digest();found.append(m)
 assert len(found)==1
 line=next(x for x in (root/'dinput8.map').read_text().splitlines() if '?evaluationTracing@animationtrace@@3_NA' in x)
 address=found[0]+int(line.split()[2],16)-0x180000000
 old=c.c_ubyte();got=c.c_size_t();assert k.ReadProcessMemory(h,address,c.byref(old),1,c.byref(got)) and got.value==1 and old.value in (0,1)
 new=c.c_ubyte(int(sys.argv[2]));assert new.value in (0,1)
 assert k.WriteProcessMemory(h,address,c.byref(new),1,c.byref(got)) and got.value==1
 print('Own-loader evaluation trace',old.value,'->',new.value)
finally:k.CloseHandle(h)
