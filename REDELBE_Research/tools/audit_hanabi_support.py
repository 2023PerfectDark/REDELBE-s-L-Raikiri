import json
from pathlib import Path
from legacy_resources import index,extract as oldextract
from lr_resources import extract
from audit_ayane_import import GAME,resources,names
from dok_patch import records,props,u
old=GAME.with_name('Dead or Alive 6');db={}
for file in old.glob('*.rdb'):db.update(index(file))
src=old/'REDELBE/Layer2/(DoAxNaruto) Hanabi Hyuga (Adult)'
missing={next(iter(names[p.name.lower()])):p for p in (src/'Character').iterdir() if p.is_file() and names.get(p.name.lower()) and not any(x in resources for x in names[p.name.lower()])}
changes=[]
for fid in (0xb290631c,):
 a=oldextract(db[fid]);b=extract(*resources[fid][0]);new={r[2]:r for r in records(b)}
 for rec in records(a):
  # Model record references to the absent files, matched by exact object/property.
  for key,kind,n,pos,length in props(a,rec):
   if length!=4 or u(a,pos) not in missing:continue
   target=u(a,pos);nr=new.get(rec[2])
   if not nr:continue
   matches=[v for v in props(b,nr) if v[0]==key and v[4]==4]
   if len(matches)!=1:continue
   current=u(b,matches[0][3]);changes.append({'database':fid,'oid':rec[2],'property':key,'old_resource':target,'lr_resource':current})
print('Missing resources',[(p.name,hex(fid)) for fid,p in missing.items()]);print('Reference patches',changes)
out=Path('analysis/isolation/hanabi_support.json');out.write_text(json.dumps(changes,indent=2))
for fid,p in missing.items():print(p.name,'old indexed',fid in db,'references',sum(c['old_resource']==fid for c in changes))
