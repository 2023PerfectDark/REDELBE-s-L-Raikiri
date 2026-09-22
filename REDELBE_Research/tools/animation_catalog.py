"""Discover animation resources from the user's LR indexes, without fixed paths."""
import argparse,collections,csv,json,re
from pathlib import Path
from lr_resources import read_index,extract,names_from_rnk

def build_catalog(game,name_map=None):
 rows=[];warnings=[];indices=[];animation_types=set()
 supplied={}
 if name_map:
  with Path(name_map).open(encoding='utf-8-sig',newline='') as stream:
   for line in csv.reader(stream):
    if len(line)==2:
     try:supplied.setdefault(int(line[0],16),[]).append(line[1].strip())
     except ValueError:continue
 for path in sorted((Path(game)/'fdata_package').glob('*.rdb')):
  _,entries,name_id=read_index(path);names={}
  named=next((e for e in entries if e['id']==name_id),None)
  try:
   if named:names=names_from_rnk(extract(path,named))
  except (OSError,ValueError) as exc:warnings.append(path.name+': '+str(exc))
  for fid,labels in supplied.items():names.setdefault(fid,[]).extend(labels)
  indices.append((path,entries,names))
  for entry in entries:
   if any(n.lower().endswith(('.g1a','.g2a')) for n in names.get(entry['id'],[])):animation_types.add(entry['type_id'])
 for path,entries,names in indices:
  for e in entries:
   labels=sorted(set(n.replace('\\','/').split('/')[-1] for n in names.get(e['id'],[]) if n.lower().endswith(('.g1a','.g2a'))))
   if not labels and e['type_id'] not in animation_types:continue
   name=labels[0] if labels else f"0x{e['id']:08x}"
   character=name[:3] if re.match(r'^[A-Z]{3}(?:_|[0-9])',name) else 'Unknown/shared'
   role='camera' if '_CAMERA_' in name else 'facial' if '_FACIAL_' in name else 'motion' if labels else 'unknown'
   category=next((label for token,label in (('_WIN.','Victory'),('_ENT.','Entrance'),('_LOSE.','Defeat')) if token in name),'Other')
   rows.append(dict(id=f"0x{e['id']:08x}",index=path.stem,name=name,names=labels,character=character,role=role,category=category,bytes=e['file_size'],usage='unknown',discovery='filename' if labels else 'animation resource type',camera_candidates=[]))
 by_name={name:row for row in rows for name in row['names']}
 for row in rows:
  for name in row['names']:
   match=re.fullmatch(r'([A-Z]{3})0(\d{4})_(WIN|ENT|LOSE)\.g[12]a',name)
   if match:
    target=f'{match[1]}_CAMERA_{match[2]}_{match[3]}.g1a'
    if target in by_name:row['camera_candidates'].append(dict(id=by_name[target]['id'],name=target,basis='name match; playback unverified'))
 return dict(schema=1,animations=rows,warnings=warnings,summary=dict(resources=len(rows),named=sum(bool(r['names']) for r in rows),roles=dict(collections.Counter(r['role'] for r in rows))))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('game',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--names',type=Path);a=ap.parse_args()
 result=build_catalog(a.game,a.names);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result['summary']))
