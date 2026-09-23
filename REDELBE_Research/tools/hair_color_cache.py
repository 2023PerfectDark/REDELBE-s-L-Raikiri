"""Bounded, regenerable hair containers. Saved wardrobe choices live elsewhere."""
import contextlib,ctypes,hashlib,json,os,struct,subprocess,tempfile,time
from pathlib import Path
from lr_resources import read_index,extract
from build_layer2_package import wrap

LIMIT=1024*1024*1024

@contextlib.contextmanager
def exclusive(root):
 kernel=ctypes.WinDLL('kernel32',use_last_error=True)
 kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_wchar_p];kernel.CreateMutexW.restype=ctypes.c_void_p
 kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
 kernel.ReleaseMutex.argtypes=[ctypes.c_void_p];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
 name='Local\\REDELBE_HairCache_'+hashlib.sha256(str(root.resolve()).lower().encode()).hexdigest()[:24]
 handle=kernel.CreateMutexW(None,False,name)
 if not handle:raise OSError('Cannot lock hair cache')
 acquired=False
 try:
  acquired=kernel.WaitForSingleObject(handle,120000) in (0,0x80)
  if not acquired:raise TimeoutError('Hair cache is busy')
  yield
 finally:
  if acquired:kernel.ReleaseMutex(handle)
  kernel.CloseHandle(handle)

def trim(root,incoming=0,keep=None):
 files=list(root.glob('????????_??.file'))
 total=sum(p.stat().st_size for p in files)
 for p in sorted(files,key=lambda p:p.stat().st_mtime_ns):
  if total+incoming<=LIMIT:break
  if p==keep:continue
  size=p.stat().st_size
  try:p.unlink()
  except OSError:continue # A currently open game file can be pinned by Windows.
  total-=size
 if total+incoming>LIMIT:raise ValueError('Hair cache is full of in-use files; keeping the current color')

def request(game,bundle,fid,color,support=None):
 game=Path(game);bundle=Path(bundle);support=Path(support) if support else game/'REDELBE_LR/HairColorSupport'
 marker=json.loads((support/'cache.json').read_text())
 if marker.get('mode')!='cache' or not 0<=color<16:raise ValueError('Invalid hair cache request')
 ids={int(line.split('\t')[1],16) for line in (support/'hair_colors.tsv').read_text().splitlines()}
 if fid not in ids:raise ValueError('Hair texture is not in the prepared catalog')
 root=support/'Cache';root.mkdir(exist_ok=True)
 target=root/f'{fid:08x}_{color:02d}.file'
 with exclusive(root):
  source=game/'fdata_package/root.rdb'
  version=hashlib.sha256(source.read_bytes()+source.with_suffix('.rdx').read_bytes()).hexdigest()
  if version!=marker['source_hash']:raise ValueError('Game resources changed; run Prepare Hair Colors again')
  if target.is_file():os.utime(target,None);trim(root,keep=target);return target
  raw,entries,_=read_index(source);matches=[e for e in entries if e['id']==fid]
  if len(matches)!=1:raise ValueError('Missing or ambiguous hair resource')
  entry=matches[0];original=extract(source,entry)
  data=original
  if color:
   palette=json.loads((bundle/'palette.json').read_text())
   with tempfile.TemporaryDirectory(prefix='redelbe-hair-') as tmp:
    src=Path(tmp)/'source.g1t';dst=Path(tmp)/'color.g1t';src.write_bytes(original)
    subprocess.run([str(bundle/'hair_texture.exe'),str(src),str(dst),palette[color]['rgb']],check=True,capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=90)
    data=dst.read_bytes()
  container=wrap(raw,entry,data)
  trim(root,len(container))
  temporary=target.with_suffix('.pending')
  try:temporary.write_bytes(container);os.replace(temporary,target)
  finally:temporary.unlink(missing_ok=True)
 return target
