"""Read the current-directory string of a 64-bit Windows process; no writes."""
import ctypes as c
from ctypes import wintypes as w
import struct
import sys
import json

k = c.WinDLL('kernel32', use_last_error=True)
n = c.WinDLL('ntdll')
k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
k.OpenProcess.restype = w.HANDLE
k.ReadProcessMemory.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t, c.POINTER(c.c_size_t)]
k.CloseHandle.argtypes = [w.HANDLE]
n.NtQueryInformationProcess.argtypes = [w.HANDLE, w.ULONG, c.c_void_p, w.ULONG, c.c_void_p]
handle = k.OpenProcess(0x410, False, int(sys.argv[1]))
if not handle:
    raise c.WinError(c.get_last_error())
def read(address, size):
    buffer = c.create_string_buffer(size)
    count = c.c_size_t()
    if not k.ReadProcessMemory(handle,address,buffer,size,c.byref(count)) or count.value != size:
        raise c.WinError(c.get_last_error())
    return buffer.raw
try:
    info = c.create_string_buffer(48)
    status = n.NtQueryInformationProcess(handle,0,info,48,None)
    if status != 0:
        raise RuntimeError(f'NtQueryInformationProcess status {status}')
    peb = struct.unpack_from('<Q',info.raw,8)[0]
    parameters = struct.unpack('<Q',read(peb+0x20,8))[0]
    length, maximum, address = struct.unpack('<HH4xQ',read(parameters+0x38,16))
    if length > maximum or length > 65534:
        raise RuntimeError('Invalid directory string')
    print(json.dumps({'pid':int(sys.argv[1]),'current_directory':read(address,length).decode('utf-16-le')}))
finally:
    k.CloseHandle(handle)
