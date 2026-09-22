"""Briefly suspend one test-game thread, read its context/stack, always resume."""
import ctypes as C, ctypes.wintypes as W, argparse, json, struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('pid',type=int);p.add_argument('tid',type=int);p.add_argument('output',type=Path);a=p.parse_args()
k=C.WinDLL('kernel32',use_last_error=True);ps=C.WinDLL('psapi',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.OpenThread.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenThread.restype=W.HANDLE
for f in ('SuspendThread','ResumeThread'): getattr(k,f).argtypes=[W.HANDLE];getattr(k,f).restype=W.DWORD
k.GetThreadContext.argtypes=[W.HANDLE,C.c_void_p];k.GetThreadContext.restype=W.BOOL
k.CloseHandle.argtypes=[W.HANDLE]
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
ps.EnumProcessModulesEx.argtypes=[W.HANDLE,C.POINTER(W.HMODULE),W.DWORD,C.POINTER(W.DWORD),W.DWORD]
ps.GetModuleFileNameExW.argtypes=[W.HANDLE,W.HMODULE,W.LPWSTR,W.DWORD]
class Info(C.Structure): _fields_=[('base',C.c_void_p),('size',W.DWORD),('entry',C.c_void_p)]
ps.GetModuleInformation.argtypes=[W.HANDLE,W.HMODULE,C.POINTER(Info),W.DWORD]
h=k.OpenProcess(0x410,False,a.pid);t=k.OpenThread(0xa,False,a.tid)
if not h or not t: raise C.WinError(C.get_last_error())
try:
    mods=(W.HMODULE*2048)();needed=W.DWORD();ps.EnumProcessModulesEx(h,mods,C.sizeof(mods),C.byref(needed),3);ranges=[]
    for m in mods[:min(2048,needed.value//8)]:
        name=C.create_unicode_buffer(32768);i=Info();ps.GetModuleFileNameExW(h,m,name,32768);ps.GetModuleInformation(h,m,C.byref(i),C.sizeof(i));ranges.append((i.base,i.size,Path(name.value).name))
    def resolve(x):
        for base,size,name in ranges:
            if base<=x<base+size:return f'{name}+0x{x-base:x}'
        return None
    context=C.create_string_buffer(1248);address=(C.addressof(context)+15)&~15
    C.c_uint32.from_address(address+48).value=0x100003
    if k.SuspendThread(t)==0xffffffff: raise C.WinError(C.get_last_error())
    try:
        if not k.GetThreadContext(t,address): raise C.WinError(C.get_last_error())
        rip=C.c_uint64.from_address(address+248).value;rsp=C.c_uint64.from_address(address+152).value
        stack=C.create_string_buffer(4096);n=C.c_size_t();k.ReadProcessMemory(h,rsp,stack,4096,C.byref(n))
    finally:k.ResumeThread(t)
    result=dict(pid=a.pid,tid=a.tid,rip=resolve(rip) or hex(rip),rsp=hex(rsp),stack_candidates=[dict(offset=hex(i),value=hex(x),module=resolve(x)) for i in range(0,n.value-7,8) for x in [struct.unpack_from('<Q',stack.raw,i)[0]] if resolve(x)])
    a.output.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
finally:k.CloseHandle(t);k.CloseHandle(h)
