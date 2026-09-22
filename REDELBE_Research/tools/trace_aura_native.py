"""Bounded hardware-breakpoint trace of two verified native effect routines.
No code patching. Preserves debug registers, never kills game on debugger exit.
"""
import ctypes as c,ctypes.wintypes as w,struct,json,time,sys
from pathlib import Path
k=c.WinDLL('kernel32',use_last_error=True);ps=c.WinDLL('psapi',use_last_error=True)
def api(lib,name,args,result=w.BOOL):
 f=getattr(lib,name);f.argtypes=args;f.restype=result;return f
op=api(k,'OpenProcess',[w.DWORD,w.BOOL,w.DWORD],w.HANDLE)
ot=api(k,'OpenThread',[w.DWORD,w.BOOL,w.DWORD],w.HANDLE)
rpm=api(k,'ReadProcessMemory',[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)])
get=api(k,'GetThreadContext',[w.HANDLE,c.c_void_p]);setc=api(k,'SetThreadContext',[w.HANDLE,c.c_void_p]);close=api(k,'CloseHandle',[w.HANDLE])
suspend=api(k,'SuspendThread',[w.HANDLE],w.DWORD);resume=api(k,'ResumeThread',[w.HANDLE],w.DWORD)
attach=api(k,'DebugActiveProcess',[w.DWORD]);detach=api(k,'DebugActiveProcessStop',[w.DWORD]);kill=api(k,'DebugSetProcessKillOnExit',[w.BOOL])
wait=api(k,'WaitForDebugEvent',[c.c_void_p,w.DWORD]);cont=api(k,'ContinueDebugEvent',[w.DWORD,w.DWORD,w.DWORD])
mods=api(ps,'EnumProcessModules',[w.HANDLE,c.c_void_p,w.DWORD,c.POINTER(w.DWORD)])
namefn=api(ps,'GetModuleFileNameExW',[w.HANDLE,w.HMODULE,w.LPWSTR,w.DWORD],w.DWORD)
pid=int(sys.argv[1]);h=op(0x410,False,pid);assert h,c.get_last_error()
def read(addr,n):
 b=c.create_string_buffer(n);got=c.c_size_t();rpm(h,addr,b,n,c.byref(got));return b.raw[:got.value]
def context(th):
 raw=c.create_string_buffer(1248);p=(c.addressof(raw)+15)&~15;c.c_uint32.from_address(p+48).value=0x100013
 assert get(th,p),('GetThreadContext',c.get_last_error());return raw,p
image=Path('analysis/lr_updated.bin').read_bytes();handles=(w.HMODULE*1024)();needed=w.DWORD();assert mods(h,handles,c.sizeof(handles),c.byref(needed));base=handles[0]
n=c.create_unicode_buffer(32768);namefn(h,None,n,len(n));assert n.value.lower().endswith('\\doa6lr.exe')
targets=[0x3402a90,0x3402db0]
for rva in targets:assert read(base+rva,32)==image[rva:rva+32],f'Code differs at {rva:x}'
threads={};hits=[];attached=False;event=c.create_string_buffer(176);start=time.monotonic();initial=False
try:
 assert attach(pid),('DebugActiveProcess',c.get_last_error());attached=True;assert kill(False),c.get_last_error();print('TRACE ACTIVE: restart the offline round or use Fight Again now',flush=True)
 while time.monotonic()-start<50 and len(hits)<80:
  if not wait(event,250):continue
  code,epid,tid=struct.unpack_from('<III',event.raw);status=0x10002
  try:
   if code in (2,3):
    th=ot(0x1a,False,tid)
    if th:
     raw,p=context(th);old=c.string_at(p+72,48)
     if struct.unpack_from('<Q',old,40)[0]&0xff:close(th)
     else:
      threads[tid]=(th,old)
      c.c_uint64.from_address(p+72).value=base+targets[0];c.c_uint64.from_address(p+80).value=base+targets[1];c.c_uint64.from_address(p+104).value=0;c.c_uint64.from_address(p+112).value=5
      assert setc(th,p),c.get_last_error()
    # Debug event owns file/thread/process handles separately from OpenThread.
    if code==3:
     for off in (16,24,32):
      handle=struct.unpack_from('<Q',event.raw,off)[0]
      if handle:close(handle)
    else:
     handle=struct.unpack_from('<Q',event.raw,16)[0]
     if handle:close(handle)
   elif code==6:
    handle=struct.unpack_from('<Q',event.raw,16)[0]
    if handle:close(handle)
   elif code==1:
    exc=struct.unpack_from('<I',event.raw,16)[0]
    if exc==0x80000004 and tid in threads:
     th,_=threads[tid];raw,p=context(th);rip=c.c_uint64.from_address(p+248).value
     if rip-base in targets:
      regs={key:c.c_uint64.from_address(p+off).value for key,off in [('rcx',128),('rdx',136),('rsp',152),('r8',184),('r9',192)]}
      stack=read(regs['rsp'],256);row=dict(tid=tid,rva=hex(rip-base),registers={key:hex(v) for key,v in regs.items()},stack=stack.hex(),object=read(regs['rcx'],384).hex(),context=read(regs['rdx'],128).hex());hits.append(row)
      print('hit',hex(rip-base),'caller',hex(struct.unpack_from('<Q',stack)[0]-base) if len(stack)>=8 else '?',flush=True)
      c.c_uint32.from_address(p+68).value|=0x10000;c.c_uint64.from_address(p+104).value=0;assert setc(th,p)
     else:status=0x80010001
    elif exc==0x80000003 and not initial:initial=True
    else:status=0x80010001
   elif code==4:
    if tid in threads:close(threads.pop(tid)[0])
   elif code==5:break
  finally:cont(epid,tid,status)
finally:
 if attached:
  for th,old in threads.values():
   if suspend(th)!=0xffffffff:
    try:
     raw,p=context(th);c.memmove(p+72,old,48);setc(th,p)
    finally:resume(th)
   close(th)
  detach(pid)
 close(h)
 Path('analysis/aura_native_trace.json').write_text(json.dumps(dict(pid=pid,base=hex(base),seconds=time.monotonic()-start,hits=hits),indent=2));print('TRACE DETACHED; hits',len(hits),flush=True)
