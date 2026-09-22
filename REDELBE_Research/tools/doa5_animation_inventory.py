"""Read-only DOA5LR animation archive inventory; never modifies game files."""
import argparse, collections, hashlib, json, struct
from pathlib import Path

def inventory(path):
 size=path.stat().st_size
 with path.open('rb') as f:
  h=f.read(32)
  if len(h)!=32:raise ValueError('Truncated archive')
  count,declared,alignment=struct.unpack_from('<3Q',h,8)
  if count>1000000 or declared!=size or alignment!=2048 or 32+count*32>size:raise ValueError('Invalid archive header')
  table=f.read(count*32); rows=[]; end=32+count*32
  for i in range(count):
   off,packed,unpacked,flags=struct.unpack_from('<4Q',table,i*32)
   if off<end or off%alignment or off+packed>size or packed>256*1024*1024:raise ValueError(f'Invalid entry {i}')
   end=off+packed;f.seek(off);data=f.read(packed)
   children=[]
   if data.startswith(b'char_dat'):
    todo=[0];seen=set()
    while todo:
     base=todo.pop()
     if base in seen:continue
     seen.add(base)
     if base+48>len(data):raise ValueError('Truncated char_dat')
     version,header,total,n,used,unknown,tableoff=struct.unpack_from('<7I',data,base+8)
     if header!=48 or base+total>len(data) or n>10000 or tableoff+n*4>total:raise ValueError('Invalid char_dat header')
     offsets=struct.unpack_from('<'+str(n)+'I',data,base+tableoff)
     children.append(dict(offset=base,size=total,version=hex(version),count=n,used=used,children=list(offsets)))
     for rel in offsets:
      if rel and rel>=total:raise ValueError('Invalid child offset')
      if rel and data[base+rel:base+rel+8]==b'char_dat':todo.append(base+rel)
   rows.append(dict(index=i,offset=off,size=packed,unpacked=unpacked,flags=flags,signature=data[:8].hex(),sha256=hashlib.sha256(data).hexdigest(),containers=children))
 return dict(archive=path.name,size=size,magic=h[:4].decode('ascii'),entries=rows)

def main():
 p=argparse.ArgumentParser();p.add_argument('--game',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 reports=[inventory(a.game/n) for n in ['chara_rtm.lnk','rtm_common.lnk']]
 a.output.mkdir(parents=True,exist_ok=True);(a.output/'archive_inventory.json').write_text(json.dumps(reports,indent=2))
 for r in reports:print(r['archive'],len(r['entries']),'entries;',sum(bool(e['containers']) for e in r['entries']),'character-motion containers')
if __name__=='__main__':main()
