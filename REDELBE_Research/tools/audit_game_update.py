"""Read-only compatibility audit; writes only a workspace report."""
import hashlib,json,re,struct
from pathlib import Path
from lr_resources import read_index
from legacy_restoration import merge

game=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round')
backup=game.with_name(game.name+' - Backup 2026-09-15_210415')
def image(path):
 b=path.read_bytes();pe=struct.unpack_from('<I',b,60)[0]
 n=struct.unpack_from('<H',b,pe+6)[0];opt=struct.unpack_from('<H',b,pe+20)[0]
 sections=[]
 for i in range(n):
  p=pe+24+opt+i*40
  vs,va,size,off=struct.unpack_from('<IIII',b,p+8)
  sections.append((va,size,off))
 def read(rva,n):
  for va,size,off in sections:
   if va<=rva and rva+n<=va+size:return b[off+rva-va:off+rva-va+n]
  return b''
 return b,read
old,oread=image(backup/'DOA6LR.exe');new,nread=image(game/'DOA6LR.exe')
source=Path('prototype/layer2_runtime.h').read_text()
checks=[]
for addr,sig in re.findall(r'\{base\+0x([0-9a-f]+),bytes\("([0-9a-f ]+)"\)',source):
 expected=bytes.fromhex(sig);rva=int(addr,16)
 checks.append({'rva':hex(rva),'signature_matches':nread(rva,len(expected))==expected,'first_256_bytes_unchanged':oread(rva,256)==nread(rva,256)})
for rva,n in [(0x21c1e90,256),(0x22dbff0,256),(0x22ca7cc,7),(0x22cc812,7),(0xe4aea3,6),(0x41baa80,8),(0x39a7c61,32),(0x39b0fdc,32)]:
 checks.append({'rva':hex(rva),'bytes_unchanged':oread(rva,n)==nread(rva,n)})
result={'new_exe_sha256':hashlib.sha256(new).hexdigest(),'backup_exe_sha256':hashlib.sha256(old).hexdigest(),'loader_hash_gate_accepts_update':old==new,'hook_checks':checks}
indexes={};resources={}
for name in ('root','system'):
 p=game/'fdata_package'/f'{name}.rdb';raw,entries,_=read_index(p)
 indexes[name]=(p,raw)
 for e in entries:resources.setdefault(e['id'],[]).append((name,e))
result['index_counts']={name:len(read_index(p)[1]) for name,(p,_) in indexes.items()}
try:
 originals=merge(indexes,resources,Path('packages/hanabi_project_ready/REDELBE_Dependencies/restoration_plan.json'))
 result['hanabi_restoration']={'compatible':True,'verified_dependencies':len(originals)}
except Exception as e:result['hanabi_restoration']={'compatible':False,'error':str(e)}
Path('analysis/game_update_audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
