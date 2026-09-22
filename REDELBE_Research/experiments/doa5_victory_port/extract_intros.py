from pathlib import Path
import struct,json
r=Path('REDELBE_Research/experiments/doa5_victory_port');g=Path('C:/SteamLibrary/steamapps/common/Dead or Alive 5 Last Round')
names={v:k for line in (r/'lrs-5.19/dat/anim.dat').read_text().splitlines() if len(x:=line.split())==2 for k,v in [x] if k.startswith('KASUMI_MOT_') and 'ENTRY' in k}
report=[]
for p in g.glob('*.bin'):
 b=p.read_bytes()
 if b[:4]!=b'LFMO':continue
 _,nl,nf,lo,fo,ln,fn=struct.unpack_from('<4s6I',b);assert fo+nf*12<=len(b)
 for i in range(nf):
  lid,index,off=struct.unpack_from('<3I',b,fo+i*12);name=b[off:b.index(0,off)].decode('ascii').lstrip('/')
  if name not in names:continue
  lnk=p.with_suffix('.lnk')
  with lnk.open('rb') as f:
   h=f.read(32);count,total,alignment=struct.unpack_from('<3Q',h,8);assert index<count and total==lnk.stat().st_size
   f.seek(32+32*index);pos,size,unc,flags=struct.unpack('<4Q',f.read(32));assert pos+size<=total and size<16*1024**2
   f.seek(pos);data=f.read(size);assert data[:6]==b'tdpack';dest=r/names[name];dest.write_bytes(data)
  report.append(dict(name=names[name],archive=lnk.name,index=index,size=size))
(r/'kasumi_intro_assets.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
