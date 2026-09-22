"""Preserve the installed Wardrobe palette across generated Layer2 catalogs."""
import hashlib,json,os,shutil,struct
from pathlib import Path
from lr_resources import read_index

def records(data):
 pos=struct.unpack_from('<I',data,8)[0];result={}
 while pos<len(data):
  size=struct.unpack_from('<Q',data,pos+8)[0];size=(size+3)&~3
  if size<48 or pos+size>len(data):raise ValueError('Invalid palette index')
  result[struct.unpack_from('<I',data,pos+36)[0]]=data[pos:pos+size];pos+=size
 return result

def link_or_copy(source,target):
 target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():return
 try:os.link(source,target)
 except OSError:shutil.copy2(source,target)

def capture(source,destination):
 source=Path(source);destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
 catalog=(source/'hair_colors.tsv').read_text();ids={int(line.split('\t')[1],16) for line in catalog.splitlines()}
 table=dict(line.split('\t') for line in (source/'vanilla.tsv').read_text().splitlines())
 index=records((source/'overlay/root.rdb').read_bytes())
 for fid in ids:
  key=f'fdata_package/data/0x{fid:08x}.file'
  link_or_copy(source/table[key],destination/'vanilla/data'/f'0x{fid:08x}.file')
 for p in (source/'HairColors').glob('*.file'):link_or_copy(p,destination/'HairColors'/p.name)
 (destination/'records.json').write_text(json.dumps({f'{fid:08x}':index[fid].hex() for fid in ids}))
 (destination/'hair_colors.tsv').write_text(catalog)

def prepare(game,package):
 game=Path(game);package=Path(package);support=game/'REDELBE_LR/HairColorSupport'
 if not (support/'hair_colors.tsv').exists():return
 overlay=package/'overlay/root.rdb';raw=overlay.read_bytes() if overlay.exists() else (game/'fdata_package/root.rdb').read_bytes()
 entries=records(raw);patches=json.loads((support/'records.json').read_text())
 vanilla=dict(line.split('\t') for line in (package/'vanilla.tsv').read_text().splitlines())
 for h,record in patches.items():
  fid=int(h,16)
  if fid not in entries:raise ValueError('Hair palette resource missing after game update: '+h)
  # Reuse only resource-container routing, not an old full game index.
  entries[fid]=bytes.fromhex(record)
  relative=f'vanilla/data/0x{h}.file';target=package/relative
  link_or_copy(support/relative,target)
  vanilla[f'fdata_package/data/0x{h}.file']=relative
 overlay.parent.mkdir(exist_ok=True);header=bytearray(raw[:struct.unpack_from('<I',raw,8)[0]])
 struct.pack_into('<I',header,16,len(entries));overlay.write_bytes(header+b''.join(entries[k] for k in sorted(entries)))
 (package/'vanilla.tsv').write_text(''.join(k+'\t'+v+'\n' for k,v in vanilla.items()))
 redirects=dict(line.split('\t') for line in (package/'redirects.tsv').read_text().splitlines());redirects['fdata_package/root.rdb']='overlay/root.rdb'
 (package/'redirects.tsv').write_text(''.join(k+'\t'+v+'\n' for k,v in redirects.items()))
 baselines=dict(line.split('\t') for line in (package/'baselines.tsv').read_text().splitlines())
 for ext in ('rdb','rdx'):
  key='fdata_package/root.'+ext;baselines[key]=hashlib.sha256((game/key).read_bytes()).hexdigest()
 (package/'baselines.tsv').write_text(''.join(k+'\t'+v+'\n' for k,v in baselines.items()))
