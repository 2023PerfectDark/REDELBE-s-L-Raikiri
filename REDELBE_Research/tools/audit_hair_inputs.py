from pathlib import Path
import sys,zipfile,io,json
sys.path.insert(0,'tools')
from audit_ayane_import import names
from lr_resources import read_index
base=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common');game=base/'Dead or Alive 6 Last Round'
ids={e['id'] for db in ('root','system') for e in read_index(game/'fdata_package'/f'{db}.rdb')[1]}
src=base/'Dead or Alive 6/REDELBE/Layer2/(Hair-Head) Hanabi Hyuga Hair 1 (Adult Byakugan)'
for p in src.rglob('*'):
 if p.suffix not in ('.g1m','.g1t','.grp','.oid','.oidex','.swg'):continue
 matches=names[p.name.lower()];print(p.name,[(hex(fid),fid in ids) for fid in matches])
exec(Path('tools/inspect_hair_zip.py').read_text().split('with zipfile')[0])
with zipfile.ZipFile(p) as z:
 with zipfile.ZipFile(io.BytesIO(z.read(z.namelist()[0]))) as inner:
  print(inner.read('mod.ini').decode())
  for row in (game/'KashiraProjects/Name2Hash/DOA6LR.csv').read_text(encoding='utf-8-sig').splitlines():
   if '236a19ff' in row.lower():print(row)
