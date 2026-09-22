"""Read only the two known preview owners from the matching loader's link map."""
import ctypes as C,ctypes.wintypes as W,struct,re,json,sys,hashlib
from pathlib import Path
from lr_resources import GAME
root=Path(__file__).resolve().parents[1]
build=root/'experiments/hair_color/native_test/build'
installed_sha=hashlib.sha256((GAME/'dinput8.dll').read_bytes()).hexdigest()
# Archived layout observed with a matching link map before the next build.
# Never apply this RVA to another binary.
archived_layouts={'d7a01f433c1842cd7aeefe0134d3ae8db5cebfc1e357c83441217933dcc24449':0xc6100}
if installed_sha in archived_layouts:
 requests_rva=archived_layouts[installed_sha]
else:
 assert hashlib.sha256((build/'dinput8.dll').read_bytes()).hexdigest()==installed_sha,'No matching loader layout'
 mapping=(build/'dinput8.map').read_text()
 requests_rva=int(re.search(r'\?requests@l2@@\S+\s+([0-9A-Fa-f]+)',mapping)[1],16)-0x180000000
k=C.WinDLL('kernel32',use_last_error=True);ps=C.WinDLL('psapi')
k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
k.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
k.CloseHandle.argtypes=[W.HANDLE]
ps.EnumProcessModulesEx.argtypes=[W.HANDLE,C.POINTER(W.HMODULE),W.DWORD,C.POINTER(W.DWORD),W.DWORD]
ps.GetModuleFileNameExW.argtypes=[W.HANDLE,W.HMODULE,W.LPWSTR,W.DWORD]
h=k.OpenProcess(0x410,False,int(sys.argv[1]));assert h
def read(p,n):
 b=C.create_string_buffer(n);got=C.c_size_t()
 if not p or not k.ReadProcessMemory(h,p,b,n,C.byref(got)):return b''
 return b.raw[:got.value]
def q(p):
 b=read(p,8);return struct.unpack('<Q',b)[0] if len(b)==8 else 0
try:
 mods=(W.HMODULE*1024)();n=W.DWORD();assert ps.EnumProcessModulesEx(h,mods,C.sizeof(mods),C.byref(n),3)
 module={}
 for m in mods[:n.value//C.sizeof(W.HMODULE)]:
  name=C.create_unicode_buffer(32768);ps.GetModuleFileNameExW(h,m,name,len(name))
  if Path(name.value).parent==GAME:module[Path(name.value).name.lower()]=m
 dll=module['dinput8.dll'];assert 'doa6lr.exe' in module
 addr=requests_rva+dll
 report={'pid':int(sys.argv[1]),'loader_sha256':installed_sha,'game_base':hex(module['doa6lr.exe']),'dll_base':hex(dll),'players':[]}
 for p in range(2):
  row=read(addr+p*40,40);obj,player,chara,costume,face,hair,color,haircolor=struct.unpack('<Q6Ii',row[:36])
  owner=obj+0x98+p*0x2d8 if obj else 0
  entry={'player':p,'object':hex(obj),'owner':hex(owner),'parts':[]}
  for part in range(3):
   req=q(owner+part*0x38);raw=read(req,0x90)
   item={'part':part,'request':hex(req),'raw':raw.hex(),'components':{}}
   for off in (0x58,0x60,0x68):
    ptr=q(req+off) if req else 0
    item['components'][hex(off)]={'pointer':hex(ptr),'data':read(ptr,0x180).hex()}
    if off==0x68 and ptr:
     render=q(ptr+0x150);data=read(render,0x180)
     item['render']={'pointer':hex(render),'data':data.hex()}
     if len(data)>0xa1 and data[0xa1]!=255:
      lod=q(render+0xa8+8*data[0xa1]);item['render']['lod']={'pointer':hex(lod),'data':read(lod,0x100).hex()}
   entry['parts'].append(item)
  entry['owner_bytes']=read(owner,0x2d8).hex();report['players'].append(entry)
 label=sys.argv[2] if len(sys.argv)>2 else 'live_private_model_state'
 assert re.fullmatch(r'[A-Za-z0-9_-]+',label),'Invalid snapshot label'
 (root/f'analysis/isolation/{label}.json').write_text(json.dumps(report,indent=2))
 print(json.dumps({'game_base':report['game_base'],'players':[{'owner':v['owner'],'parts':[{'part':x['part'],'request':x['request'],'components':{k:v['pointer'] for k,v in x['components'].items()}} for x in v['parts']]} for v in report['players']]},indent=2))
finally:k.CloseHandle(h)
