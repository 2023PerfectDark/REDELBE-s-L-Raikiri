"""Temporary UI availability probe; never modifies the executable on disk.

Only the verified, constant-false availability result is changed. This does
not enable any purchase, ownership, currency, or save operation. Use --restore
or restart the game to remove the probe.
"""
import ctypes as C
from ctypes import wintypes as W
import argparse

p=argparse.ArgumentParser();p.add_argument('pid',type=int);p.add_argument('--restore',action='store_true');a=p.parse_args()
k=C.WinDLL('kernel32',use_last_error=True);ps=C.WinDLL('psapi',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
k.WriteProcessMemory.argtypes=k.ReadProcessMemory.argtypes
k.VirtualProtectEx.argtypes=[W.HANDLE,C.c_void_p,C.c_size_t,W.DWORD,C.POINTER(W.DWORD)]
k.FlushInstructionCache.argtypes=[W.HANDLE,C.c_void_p,C.c_size_t]
k.CloseHandle.argtypes=[W.HANDLE]
ps.EnumProcessModulesEx.argtypes=[W.HANDLE,C.POINTER(W.HMODULE),W.DWORD,C.POINTER(W.DWORD),W.DWORD]
ps.GetModuleFileNameExW.argtypes=[W.HANDLE,W.HMODULE,W.LPWSTR,W.DWORD]
h=k.OpenProcess(0x438,False,a.pid);assert h,C.get_last_error()
try:
 mods=(W.HMODULE*1024)();needed=W.DWORD();assert ps.EnumProcessModulesEx(h,mods,C.sizeof(mods),C.byref(needed),3)
 name=C.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,mods[0],name,len(name))
 assert name.value.lower().endswith('\\dead or alive 6 last round\\doa6lr.exe'),name.value
 address=mods[0]+0x37be770;buf=C.create_string_buffer(7);got=C.c_size_t()
 assert k.ReadProcessMemory(h,address,buf,7,C.byref(got)) and got.value==7
 old=bytes.fromhex('b001' if a.restore else '32c0')+bytes.fromhex('4883c428c3')
 assert buf.raw==old,buf.raw.hex()
 new=bytes.fromhex('32c0' if a.restore else 'b001');protect=W.DWORD()
 assert k.VirtualProtectEx(h,address,2,0x40,C.byref(protect))
 try:
  assert k.WriteProcessMemory(h,address,new,2,C.byref(got)) and got.value==2
  assert k.FlushInstructionCache(h,address,2)
 finally:
  temp=W.DWORD();assert k.VirtualProtectEx(h,address,2,protect.value,C.byref(temp))
 print('Restored native availability' if a.restore else 'Temporary availability probe enabled')
finally:k.CloseHandle(h)
