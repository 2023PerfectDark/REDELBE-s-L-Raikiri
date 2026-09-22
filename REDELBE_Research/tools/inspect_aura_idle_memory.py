"""Read-only, bounded scan of one DOA6LR process for known aura resource IDs."""
import ctypes as c, ctypes.wintypes as w, struct, json, sys, time
from pathlib import Path
k=c.WinDLL('kernel32',use_last_error=True);ps=c.WinDLL('psapi',use_last_error=True)
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)]
k.CloseHandle.argtypes=[w.HANDLE]
class MBI(c.Structure):
 _fields_=[('base',c.c_void_p),('allocation',c.c_void_p),('ap',w.DWORD),('partition',w.WORD),('size',c.c_size_t),('state',w.DWORD),('protect',w.DWORD),('type',w.DWORD)]
k.VirtualQueryEx.argtypes=[w.HANDLE,c.c_void_p,c.POINTER(MBI),c.c_size_t];k.VirtualQueryEx.restype=c.c_size_t
ps.GetModuleFileNameExW.argtypes=[w.HANDLE,w.HMODULE,w.LPWSTR,w.DWORD]
h=k.OpenProcess(0x410,False,int(sys.argv[1]));assert h,c.get_last_error()
try:
 name=c.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,None,name,len(name));assert name.value.lower().endswith('\\doa6lr.exe'),name.value
 ids={0x0c3844a7:'honoka_idle',0x00399961:'aura_action'}
 hits=[];address=0;total=0;start=time.monotonic()
 while address<0x7fffffffffff and total<4*1024**3 and time.monotonic()-start<45:
  m=MBI()
  if not k.VirtualQueryEx(h,address,c.byref(m),c.sizeof(m)):break
  address=int(m.base or 0)+m.size
  if m.state!=0x1000 or m.type!=0x20000 or m.protect&0x101 or not m.protect&0xee:continue
  for off in range(0,m.size,4*1024**2):
   n=min(4*1024**2,m.size-off);buf=c.create_string_buffer(n);got=c.c_size_t()
   k.ReadProcessMemory(h,int(m.base)+off,buf,n,c.byref(got));data=buf.raw[:got.value];total+=len(data)
   for fid,label in ids.items():
    pos=0;pattern=struct.pack('<I',fid)
    while (pos:=data.find(pattern,pos))>=0:
     if len(hits)<300:hits.append(dict(effect=label,address=hex(int(m.base)+off+pos),region=hex(int(m.base)),offset=pos,context=data[max(0,pos-64):pos+1024].hex()))
     pos+=4
   if total>=4*1024**3 or time.monotonic()-start>=45:break
 result=dict(pid=int(sys.argv[1]),bytes_scanned=total,seconds=time.monotonic()-start,hits=hits)
 Path('analysis/aura_idle_live_scan.json').write_text(json.dumps(result,indent=2))
 print(json.dumps({**result,'hits':[{k:v for k,v in x.items() if k!='context'} for x in hits]},indent=2))
finally:k.CloseHandle(h)

