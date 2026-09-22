"""Read-only snapshot of pointers actually observed by the native evaluator."""
import ctypes as C, ctypes.wintypes as W, json, re, struct, sys
from pathlib import Path
k=C.WinDLL('kernel32',use_last_error=True);ps=C.WinDLL('psapi',use_last_error=True)
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
k.CloseHandle.argtypes=[W.HANDLE]
ps.EnumProcessModulesEx.argtypes=[W.HANDLE,C.POINTER(W.HMODULE),W.DWORD,C.POINTER(W.DWORD),W.DWORD]
ps.GetModuleFileNameExW.argtypes=[W.HANDLE,W.HMODULE,W.LPWSTR,W.DWORD]
h=k.OpenProcess(0x410,False,int(sys.argv[1]));assert h,C.get_last_error()
def read(p,n):
 b=C.create_string_buffer(n);got=C.c_size_t()
 return b.raw[:got.value] if p and k.ReadProcessMemory(h,p,b,n,C.byref(got)) else b''
def q(p):
 b=read(p,8);return struct.unpack('<Q',b)[0] if len(b)==8 else 0
try:
 mods=(W.HMODULE*1024)();needed=W.DWORD();ps.EnumProcessModulesEx(h,mods,C.sizeof(mods),C.byref(needed),3)
 base=mods[0];name=C.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,mods[0],name,len(name))
 assert name.value.lower().endswith('\\doa6lr.exe')
 log=(Path(name.value).parent/'REDELBE_LR/loader.log').read_text()
 hits=list(re.finditer(r'ANIMATION EVALUATE motion=([0-9A-F]+) manager=([0-9A-F]+) skeleton=([0-9A-F]+) time=([^ ]+)',log))
 selected={}
 for hit in hits:selected[(hit[1],hit[3])]=hit
 out=[]
 for hit in selected.values():
  motion,manager,skeleton=[int(hit[i],16) for i in range(1,4)]
  targets={'motion':motion,'skeleton':skeleton,'manager':manager,'model':q(skeleton+0x38),'model_resource':q(skeleton+0x40)}
  handle=q(q(motion+0x38))
  targets.update(motion_handle=handle,motion_descriptor=q(handle+0x18),motion_native=q(handle+0x20))
  if q(motion)==base+0x4257c28:targets['motion_native']=motion
  targets['motion_payload']=q(targets['motion_native']+0x18)
  payload=read(targets['motion_payload'],48)
  if len(payload)==48:
   fps,frames=struct.unpack_from('<fH',payload);bones=struct.unpack_from('<H',payload,8)[0]
   root=Path(name.value).parent/'REDELBE_LR/AnimationBrowser'
   for line in (root/'catalog.tsv').read_text(encoding='utf-8-sig').splitlines():
    cells=line.split('\t')
    if len(cells)<4 or cells[0]!='KAS' or 'DOA5' in cells[2]:continue
    path=root/cells[3]
    if not path.is_file():continue
    f=path.read_bytes()
    if len(f)<32 or f[:8]!=b'_A2G0400':continue
    if struct.unpack_from('<fH',f,12)!=(fps,frames) or struct.unpack_from('<H',f,18)[0]>>4!=bones:continue
    ks,vs=struct.unpack_from('<II',f,20);packed=32+4*bones+ks
    if read(q(targets['motion_payload']+24),4*bones)!=f[32:32+4*bones]:continue
    if read(q(targets['motion_payload']+32),ks)!=f[32+4*bones:packed]:continue
    if read(q(targets['motion_payload']+40),vs*32)!=f[packed:]:continue
    print('IDENTIFIED',cells[2],hex(motion),hit[4])

  if len(payload)==48:
   count=struct.unpack_from('<H',payload,8)[0]
   if 0<count<1024:
    rawids=read(struct.unpack_from('<Q',payload,24)[0],count*4)
    if len(rawids)==count*4 and count==344:
     f=Path('REDELBE_Research/experiments/doa5_victory_port/prototype/Faces/0xa3ad71de.g1a').read_bytes()
     ids=struct.unpack('<344I',rawids);other=struct.unpack_from('<344I',f,32)
     print('FACE guard',hex(struct.unpack_from('<I',read(motion,32),20)[0]),'mismatches',sum((a&0x3ff0)!=(b&0x3ff0) for a,b in zip(ids,other)))
  objects=[]
  for label,p in targets.items():
   raw=read(p,0x300);v=q(p)
   objects.append(dict(label=label,address=hex(p),vtable_rva=hex(v-base) if base<=v<base+0x7000000 else None,raw=raw.hex()))
  out.append(dict(time=hit[4],objects=objects))
 dest=Path(__file__).resolve().parents[1]/'experiments/animation_browser/evaluator_objects.json'
 dest.write_text(json.dumps(dict(pid=int(sys.argv[1]),base=hex(base),samples=out),indent=2))
 print(json.dumps([dict(motion=next(a['address'] for a in x['objects'] if a['label']=='motion'),payload=next(a['raw'][:96] for a in x['objects'] if a['label']=='motion_payload')) for x in out]))
finally:k.CloseHandle(h)
