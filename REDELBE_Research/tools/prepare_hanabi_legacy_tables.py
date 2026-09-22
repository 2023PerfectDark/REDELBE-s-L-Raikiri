"""Extract only the original model tables needed to validate private bindings."""
from pathlib import Path
import json,struct
import legacy_resources as legacy
from isolated_material_chain import Database,MaterialCloner
root=Path(__file__).resolve().parents[1]
game=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6')
out=root/'analysis/isolation/legacy_templates';out.mkdir(exist_ok=True)
idx=legacy.index(game/'CharacterEditor.rdb')
allidx={k:v for p in game.glob('*.rdb') for k,v in legacy.index(p).items()}
db=Database(legacy.extract(allidx[0xb290631c]))
report={}
for fid in (0x27d41bb4,0x75624ccc):
 data=legacy.extract(idx[fid]);(out/f'0x{fid:08x}.ktid').write_bytes(data)
 report[hex(fid)]={'rows':len(data)//8,'entries':list(struct.iter_unpack('<II',data))}
 for _,oid in struct.iter_unpack('<II',data):
  if oid in db.items:
   (out/f'object_{oid:08x}.bin').write_bytes(db.items[oid])
(out/'tables.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v['rows'] for k,v in report.items()}))
