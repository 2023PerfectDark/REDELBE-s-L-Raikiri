from pathlib import Path
import struct,sys,ast,zlib
r=Path('REDELBE_Research/experiments/doa5_victory_port');g=Path('C:/SteamLibrary/steamapps/common/Dead or Alive 5 Last Round')
encoded=next(x.split()[1] for x in (r/'lrs-5.19/dat/char_kasumi.dat').read_text().splitlines() if x.split() and x.split()[0]=='KASUMI_FACE.TMC')
found=[]
for p in g.glob('*.bin'):
 b=p.read_bytes()
 if b[:4]!=b'LFMO':continue
 _,nl,nf,lo,fo,ln,fn=struct.unpack_from('<4s6I',b)
 for i in range(nf):
  lid,ix,o=struct.unpack_from('<3I',b,fo+12*i)
  if b[o:b.index(0,o)].decode().lstrip('/')!=encoded:continue
  with p.with_suffix('.lnk').open('rb') as f:
   f.seek(32+32*ix);pos,size,unc,flags=struct.unpack('<4Q',f.read(32));f.seek(pos);data=bytearray(f.read(size));found.append((p.name,ix,len(data)))
  if data[:4]!=b'TMC\0':
   tree=ast.parse((r/'lrs-5.19/doa5.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['generate_key','xor_buffer','unpack_buffer']];phrase=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='XOR_PHRASE' for t in n.targets))
   env={'struct':struct,'zlib':zlib,'align':lambda n,a:(n+a-1)&~(a-1),'XOR_PHRASE':phrase,'DOAError':ValueError};exec(compile(ast.Module(body=nodes,type_ignores=[]),'reviewed_archive_decode','exec'),env)
   size=struct.unpack_from('<I',data)[0];data=data[4:];env['xor_buffer'](data,env['generate_key'](size));data=env['unpack_buffer'](data);assert len(data)==size and data[:4]==b'TMC\0'
  (r/'DOA5_KASUMI_FACE.decoded.TMC').write_bytes(data)
print('DOA5',found)
sys.path.insert(0,'REDELBE_Research/tools');import lr_resources as lr
wanted={0xf10a17f9:'KAS_FACE_001.g1m',0xe3045172:'KAS_FACE_001.oid',0x69390edf:'KAS_FACE_001.oidex',0xf80f980f:'KAS_FACIAL_7020_WIN.g1a'}
for path in (lr.GAME/'fdata_package').glob('*.rdb'):
 _,entries,_=lr.read_index(path)
 for e in entries:
  if e['id'] in wanted:
   try:data=lr.extract(path,e)
   except (FileNotFoundError,ValueError):continue
   (r/wanted[e['id']]).write_bytes(data);print('LR',wanted[e['id']],len(data))
