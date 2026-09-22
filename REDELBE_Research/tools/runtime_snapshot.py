"""Read-only snapshot of a running game's main module; no injection or writes."""
import argparse, ctypes as C, ctypes.wintypes as W, hashlib, json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('pid', type=int)
p.add_argument('output', type=Path)
a = p.parse_args()
k = C.WinDLL('kernel32', use_last_error=True)
ps = C.WinDLL('psapi', use_last_error=True)
k.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
k.OpenProcess.restype = W.HANDLE
k.ReadProcessMemory.argtypes = [W.HANDLE, C.c_void_p, C.c_void_p, C.c_size_t, C.POINTER(C.c_size_t)]
k.ReadProcessMemory.restype = W.BOOL
k.CloseHandle.argtypes = [W.HANDLE]
ps.EnumProcessModulesEx.argtypes = [W.HANDLE, C.POINTER(W.HMODULE), W.DWORD, C.POINTER(W.DWORD), W.DWORD]
ps.GetModuleFileNameExW.argtypes = [W.HANDLE, W.HMODULE, W.LPWSTR, W.DWORD]
class Info(C.Structure):
    _fields_ = [('base', C.c_void_p), ('size', W.DWORD), ('entry', C.c_void_p)]
ps.GetModuleInformation.argtypes = [W.HANDLE, W.HMODULE, C.POINTER(Info), W.DWORD]
h = k.OpenProcess(0x410, False, a.pid)
if not h: raise C.WinError(C.get_last_error())
try:
    mods = (W.HMODULE * 2048)(); needed = W.DWORD()
    if not ps.EnumProcessModulesEx(h, mods, C.sizeof(mods), C.byref(needed), 3): raise C.WinError(C.get_last_error())
    modules = []
    for m in mods[:min(needed.value // C.sizeof(W.HMODULE), len(mods))]:
        name = C.create_unicode_buffer(32768); info = Info()
        ps.GetModuleFileNameExW(h, m, name, len(name))
        ps.GetModuleInformation(h, m, C.byref(info), C.sizeof(info))
        modules.append(dict(path=name.value, base=info.base, size=info.size))
    main = modules[0]; data = bytearray(main['size']); failed = []
    for off in range(0, len(data), 0x1000):
        n = min(0x1000, len(data)-off); buf = C.create_string_buffer(n); read = C.c_size_t()
        ok = k.ReadProcessMemory(h, main['base']+off, buf, n, C.byref(read))
        data[off:off+read.value] = buf.raw[:read.value]
        if not ok: failed.append(hex(off))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.with_suffix('.bin').write_bytes(data)
    result = dict(pid=a.pid, modules=modules, unreadable_pages=failed, sha256=hashlib.sha256(data).hexdigest(), layout='memory: file offset equals RVA')
    a.output.with_suffix('.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(main=main, module_count=len(modules), unreadable_pages=len(failed), output=str(a.output))))
finally:
    k.CloseHandle(h)
