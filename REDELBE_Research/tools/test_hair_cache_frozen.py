"""Exercise the shipped helper on one real LR texture in an isolated fixture."""
import sys,tempfile,struct,subprocess,shutil
from pathlib import Path
from lr_resources import read_index,extract
from build_layer2_package import wrap
ROOT=Path(__file__).resolve().parents[1]
game=Path(sys.argv[1]);source=game/'fdata_package/root.rdb'
raw,entries,_=read_index(source);fid=0xdede91c6;entry=next(e for e in entries if e['id']==fid)
container=wrap(raw,entry,extract(source,entry))
with tempfile.TemporaryDirectory(prefix='hair cache test ') as temporary:
 fixture=Path(temporary);data=fixture/'fdata_package';(data/'data').mkdir(parents=True)
 patched=bytearray(raw);ext=entry['rdb_offset']+entry['entry_size']-13
 struct.pack_into('<H',patched,ext,0xc01)
 (data/'root.rdb').write_bytes(patched);shutil.copyfile(source.with_suffix('.rdx'),data/'root.rdx')
 (data/'data'/f'0x{fid:08x}.file').write_bytes(container)
 (fixture/'DOA6LR.exe').write_bytes(b'fixture, not executable')
 exe=ROOT/'packages/Alpha152Tools/Prepare Hair Colors.exe'
 subprocess.run([str(exe),'--game',str(fixture),'--mode','cache','--no-pause'],check=True)
 worker=fixture/'REDELBE_LR/HairColorSupport/HairCacheWorker.exe'
 for color in (0,12,12):subprocess.run([str(worker),'--game',str(fixture),'--cache-request',f'{fid:x}','--color',str(color),'--no-pause'],check=True)
 cache=worker.parent/'Cache';original=(cache/f'{fid:08x}_00.file').read_bytes();cyan=(cache/f'{fid:08x}_12.file').read_bytes()
 assert original==container and cyan!=original
 assert struct.unpack_from('<I',cyan,36)[0]==fid
 assert len(list(cache.glob('*.file')))==2
 assert sum(p.stat().st_size for p in cache.iterdir())<=1024**3
 print('Frozen setup, default fallback, Cyan generation, cache hit and resource ID passed.')
