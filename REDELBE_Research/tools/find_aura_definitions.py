"""Read-only search of original database resources for Raidou aura object references."""
import sys,struct,json,time
from pathlib import Path
import legacy_resources as l,lr_resources as r
sys.stdout.reconfigure(encoding='utf-8')
p=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6\KIDSSystemResource.rdb')
idx=l.index(p);names=r.names_from_rnk(l.extract(idx[l.u32(p.read_bytes(),20)]))
targets=(0xc0a1ca5d,0xa7a17260,0x85fef54e,0x7fa35bed)
out=[];total=0;start=time.monotonic();dest=Path('analysis/aura_definitions');dest.mkdir(exist_ok=True)
for fid,e in idx.items():
 if e['size']>32*1024**2:continue
 n=names.get(fid,[''])[0]
 if n.endswith(('.name','.ndb')):continue
 try:b=l.extract(e)
 except (OSError,ValueError):continue
 total+=len(b);hits={hex(h):[i for i in range(len(b)) if False] for h in []}
 for h in targets:
  needle=struct.pack('<I',h);positions=[];at=0
  while (at:=b.find(needle,at))>=0:positions.append(at);at+=4
  if positions:hits[hex(h)]=positions
 if hits:
  f=dest/(f'{fid:08x}.bin');f.write_bytes(b)
  row=dict(id=hex(fid),name=n,bytes=len(b),hits=hits);out.append(row);print(json.dumps(row))
 if total>1024**3 or time.monotonic()-start>45:break
(dest/'matches.json').write_text(json.dumps(out,indent=2))
print('Scanned bytes',total,'seconds',time.monotonic()-start)
