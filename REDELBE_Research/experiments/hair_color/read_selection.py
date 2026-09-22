"""Read-only request snapshot for the exact locally built loader."""
import ctypes as C, ctypes.wintypes as W, hashlib, json, re, struct, sys
from pathlib import Path
here=Path(__file__).resolve().parent
k=C.WinDLL('kernel32',use_last_error=True);ps=C.WinDLL('psapi',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.CloseHandle.argtypes=[W.HANDLE]
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
ps.EnumProcessModulesEx.argtypes=[W.HANDLE,C.POINTER(W.HMODULE),W.DWORD,C.POINTER(W.DWORD),W.DWORD]
ps.GetModuleFileNameExW.argtypes=[W.HANDLE,W.HMODULE,W.LPWSTR,W.DWORD]
h=k.OpenProcess(0x410,False,int(sys.argv[1]))
if not h:raise C.WinError(C.get_last_error())
try:
    mods=(W.HMODULE*1024)();n=W.DWORD()
    if not ps.EnumProcessModulesEx(h,mods,C.sizeof(mods),C.byref(n),3):raise C.WinError(C.get_last_error())
    bases={}
    for m in mods[:min(n.value//8,1024)]:
        name=C.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,m,name,len(name))
        if Path(name.value).name.lower()=='dinput8.dll' and 'system32' not in name.value.lower():
            disk=Path(name.value).read_bytes();local=(here/'native_test/build/dinput8.dll').read_bytes()
            if hashlib.sha256(disk).digest()!=hashlib.sha256(local).digest():raise ValueError('Loader differs from map build')
            bases['loader']=m
    if 'loader' not in bases:raise ValueError('Local loader not found')
    def read(addr,size):
        b=C.create_string_buffer(size);got=C.c_size_t()
        if not k.ReadProcessMemory(h,addr,b,size,C.byref(got)) or got.value!=size:raise C.WinError(C.get_last_error())
        return b.raw
    mapping=(here/'native_test/build/dinput8.map').read_text()
    def address(symbol):
        line=next(l for l in mapping.splitlines() if symbol in l)
        absolute=int(re.search(r'\b000000018[0-9a-fA-F]+\b',line)[0],16)
        return bases['loader']+absolute-0x180000000
    rows=[]
    for side in range(2):
        values=struct.unpack('<Q6Ii',read(address('?requests@l2@@')+40*side,36))
        rows.append(dict(zip(['object','player','character','costume','face','hair','costume_color','native_hair_color'],[hex(v) for v in values])))
    result=dict(pid=int(sys.argv[1]),requests=rows,editor_slot=struct.unpack('<I',read(address('?customSlotIndex@mousemenu@l2@@'),4))[0])
    print(json.dumps(result,indent=2))
    (here/'selection_snapshot.json').write_text(json.dumps(result,indent=2))
finally:k.CloseHandle(h)
