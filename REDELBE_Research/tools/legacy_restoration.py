"""Merge explicitly planned legacy resources into a generated overlay, not game archives."""
import hashlib,json,struct
from pathlib import Path
from lr_resources import read_index,extract
from dok_patch import patch
def load_plan(path):
 path=Path(path);plan=json.loads(path.read_text());payloads={}
 for r in plan['resources']:
  ext=r.get('extension','.g1t')
  if ext not in ('.g1t','.grp','.oid','.oidex'):raise ValueError('Unsupported restored resource type')
  file=path.parent/'restored'/f"0x{r['id']:08x}{ext}"
  data=file.read_bytes()
  if hashlib.sha256(data).hexdigest()!=r['sha256'] or len(data)!=r['size']:raise ValueError('Restored Vanilla asset modified')
  if r['id'] in payloads:raise ValueError('Duplicate restored resource')
  payloads[r['id']]=(r['type'],data)
 return plan,payloads
def merge(index,resources,plan_path):
 plan,payloads=load_plan(plan_path);rootpath,raw=index['root'];entries=read_index(rootpath)[1]
 records={e['id']:(dict(e),bytearray(raw[e['rdb_offset']:e['rdb_offset']+((e['entry_size']+3)&~3)])) for e in entries}
 originals={}
 for fid,(typ,data) in payloads.items():
  if fid in resources:raise ValueError(f'Restored ID {fid:08x} now exists; regenerate dependency plan')
  candidates=[e for e in entries if e['type_id']==typ and e['c_size']==13]
  if not candidates:raise ValueError('Missing LR resource type template')
  entry=dict(candidates[0]);record=bytearray(records[entry['id']][1]);entry['id']=fid;entry['file_size']=len(data)
  struct.pack_into('<I',record,36,fid);struct.pack_into('<Q',record,24,len(data))
  records[fid]=(entry,record);originals[fid]=data
 header=bytearray(raw[:struct.unpack_from('<I',raw,8)[0]]);struct.pack_into('<I',header,16,len(records))
 merged=header
 for fid in sorted(records):
  e,record=records[fid];e['rdb_offset']=len(merged);merged+=record
  resources[fid]=[(db,other) for db,other in resources.get(fid,[]) if db!='root']+[('root',e)]
 index['root']=(rootpath,bytes(merged))
 grouped={}
 for change in plan['changes']:
  old=change['old_resource'];current=change['lr_resource']
  if len(resources.get(current,[]))!=1:raise ValueError('Current restoration baseline missing/ambiguous')
  db,e=resources[current][0]
  if payloads[old][1]!=extract(index[db][0],e):raise ValueError('Restored fallback differs from current LR default; regenerate dependency baseline')
  grouped.setdefault(change.get('database',0xd956e4a2),[]).append(change)
 for fid,changes in grouped.items():
  if len(resources.get(fid,[]))!=1:raise ValueError('Restoration database missing/ambiguous')
  db,e=resources[fid][0];before=extract(index[db][0],e);originals[fid]=patch(before,changes)
 return originals
