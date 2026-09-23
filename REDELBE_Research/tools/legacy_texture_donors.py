"""Find LR donors through stable texture-object references, never by appearance."""
import json
from pathlib import Path
from legacy_texture_objects import OBJECTS
from isolated_material_chain import Database,MaterialCloner
from lr_resources import read_index,extract

class Donors:
 def __init__(self,game):
  self.resources={e['id']:(p,e) for p in (Path(game)/'fdata_package').glob('*.rdb') for e in read_index(p)[1]}
  self.db=Database(extract(*self.resources[0xd956e4a2]))
 def find(self,fid,data):
  if data[:4]!=b'GT1G':raise ValueError('Legacy donor input is not a G1T texture: '+hex(fid))
  found=[]
  for oid in OBJECTS.get(fid,[]):
   if oid not in self.db.items:continue
   donor=self.db.scalar(oid,MaterialCloner.TEXTURE)
   if donor not in self.resources:continue
   baseline=extract(*self.resources[donor])
   if baseline[:4]!=b'GT1G':continue
   found.append({'legacy':fid,'object':oid,'donor':donor})
  if not found:raise ValueError('No verified LR texture-object donor for '+hex(fid))
  return found

def prepare(game,definitions,known_ids):
 resolver=None;report=[]
 for slot,name,directory in definitions:
  rows=[];unresolved=[]
  for p in Path(directory).glob('0x*.g1t'):
   fid=int(p.stem,16)
   if fid in known_ids:continue
   if resolver is None:resolver=Donors(game)
   try:rows.extend(resolver.find(fid,p.read_bytes()))
   except ValueError as exc:
    # This directory is generated staging, never the user's source mod.
    # Keep the payload for diagnosis, but don't register an unverified target.
    p.rename(p.with_suffix('.g1t.unresolved'))
    unresolved.append({'file':p.name,'reason':str(exc)})
    print('Texture donor unavailable; keeping native fallback: '+name+': '+p.name,flush=True)
  if rows:
   (Path(directory)/'texture_donors.json').write_text(json.dumps(rows,indent=2))
  if rows or unresolved:report.append({'mod':name,'textures':len({r['legacy'] for r in rows}),'bindings':len(rows),'unresolved':unresolved})
 return report
