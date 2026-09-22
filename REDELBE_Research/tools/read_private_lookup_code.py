"""Read-only disassembly of bounded native model lookup code in restored LR."""
import ctypes as C,ctypes.wintypes as W,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'python_deps'))
import capstone,pefile
from lr_resources import GAME
k=C.WinDLL('kernel32',use_last_error=True);ps=C.WinDLL('psapi',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
k.CloseHandle.argtypes=[W.HANDLE]
ps.EnumProcessModulesEx.argtypes=[W.HANDLE,C.POINTER(W.HMODULE),W.DWORD,C.POINTER(W.DWORD),W.DWORD]
ps.GetModuleFileNameExW.argtypes=[W.HANDLE,W.HMODULE,W.LPWSTR,W.DWORD]
h=k.OpenProcess(0x410,False,int(sys.argv[1]));assert h
try:
 modules=(W.HMODULE*1024)();needed=W.DWORD();assert ps.EnumProcessModulesEx(h,modules,C.sizeof(modules),C.byref(needed),3)
 base=modules[0];name=C.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,modules[0],name,len(name));assert Path(name.value)==GAME/'DOA6LR.exe'
 pe=pefile.PE(str(GAME/'DOA6LR.exe'),fast_load=True);pe.parse_data_directories(directories=[3]);cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);result={}
 start=0x22c0000;size=0x16000;window=C.create_string_buffer(size);received=C.c_size_t()
 assert k.ReadProcessMemory(h,base+start,window,size,C.byref(received))
 (Path(__file__).resolve().parents[1]/'analysis/isolation/native_model_window.bin').write_bytes(window.raw[:received.value])
 writes=[]
 for f in pe.DIRECTORY_ENTRY_EXCEPTION:
  fn=f.struct
  if not start<=fn.BeginAddress<start+size or fn.EndAddress>start+size:continue
  instructions=list(cs.disasm(window.raw[fn.BeginAddress-start:fn.EndAddress-start],fn.BeginAddress))
  for ix,i in enumerate(instructions):
   if i.mnemonic=='mov' and i.op_str.startswith('qword ptr [') and '+ 0x58]' in i.op_str:
    writes.append({'function':hex(fn.BeginAddress),'instructions':[f'{x.address:08x} {x.mnemonic} {x.op_str}' for x in instructions[max(0,ix-6):ix+3]]})
 result['request_58_writes']=writes
 for caller in (0x22cf216,0x22cb4fc):
  fn=next(f.struct for f in pe.DIRECTORY_ENTRY_EXCEPTION if f.struct.BeginAddress<=caller<f.struct.EndAddress)
  n=min(fn.EndAddress-fn.BeginAddress,16384);buf=C.create_string_buffer(n);got=C.c_size_t()
  assert k.ReadProcessMemory(h,base+fn.BeginAddress,buf,n,C.byref(got))
  decoded=list(cs.disasm(buf.raw[:got.value],fn.BeginAddress))
  result[hex(caller)]=[f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in decoded if caller-200<=i.address<=caller+25]
 out=Path(__file__).resolve().parents[1]/'analysis/isolation/private_lookup_code.json';out.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
finally:k.CloseHandle(h)
