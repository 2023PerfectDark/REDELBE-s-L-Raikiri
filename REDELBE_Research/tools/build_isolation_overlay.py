"""Build an OFFLINE LR overlay registering restored old texture IDs.

No game writes. Rebuild from current live indexes; review before integration.
"""
from pathlib import Path
import struct,json,hashlib,shutil
from lr_resources import read_index,u32
from build_layer2_package import wrap
from audit_ayane_import import GAME
def main():
 root=Path('packages/legacy_texture_isolation');plan=json.loads((root/'restoration_plan.json').read_text())
 out=root/'overlay'
 if out.exists():raise ValueError('Use a fresh output directory')
 (out/'data').mkdir(parents=True)
 path=GAME/'fdata_package/root.rdb';raw,entries,_=read_index(path);lookup={e['id']:e for e in entries}
 template=next(e for e in entries if e['type_id']==0xafbec60c and e['c_size']==13)
 records={e['id']:bytearray(raw[e['rdb_offset']:e['rdb_offset']+((e['entry_size']+3)&~3)]) for e in entries}
 payloads=[(r['id'],root/'restored'/f"0x{r['id']:08x}.g1t",True) for r in plan['resources']]+[(0xd956e4a2,root/'0xd956e4a2.dok',False)]
 hashes=[]
 for fid,file,new in payloads:
  if new and fid in lookup:raise ValueError('Restored hash now exists; regenerate audit')
  e=template if new else lookup[fid]
  if e['c_size']!=13:raise ValueError('Unsupported index layout')
  data=file.read_bytes();container=bytearray(wrap(raw,e,data));struct.pack_into('<I',container,36,fid)
  (out/'data'/f'0x{fid:08x}.file').write_bytes(container)
  record=bytearray(records[e['id']]);struct.pack_into('<I',record,36,fid);struct.pack_into('<Q',record,24,len(data));struct.pack_into('<I',record,44,0x20000)
  ext=e['entry_size']-13;struct.pack_into('<H',record,ext,0xc01);struct.pack_into('<I',record,ext+2,0);struct.pack_into('<I',record,ext+6,len(container))
  records[fid]=record;hashes.append({'id':fid,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
 header=bytearray(raw[:u32(raw,8)]);struct.pack_into('<I',header,16,len(records))
 (out/'root.rdb').write_bytes(bytes(header)+b''.join(records[k] for k in sorted(records)))
 shutil.copyfile(path.with_suffix('.rdx'),out/'root.rdx')
 _,checked,_=read_index(out/'root.rdb')
 from lr_resources import extract
 for row in hashes:
  data=extract(out/'root.rdb',next(e for e in checked if e['id']==row['id']))
  if hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Registered resource failed extraction roundtrip')
 original_ids=set(lookup)-{0xd956e4a2}
 for fid in original_ids:
  e=lookup[fid]
  if records[fid]!=raw[e['rdb_offset']:e['rdb_offset']+((e['entry_size']+3)&~3)]:raise ValueError('Unrelated index entry changed')
 result={'status':'OFFLINE ONLY - NOT INSTALLED','added_resources':22,'verified_assets':hashes,'unchanged_index_records':len(original_ids),'baseline_root_sha256':hashlib.sha256(raw).hexdigest()}
 (root/'overlay_verification.json').write_text(json.dumps(result,indent=2));print('PASS: 22 new IDs + patched MaterialEditor extract correctly;',len(original_ids),'existing index entries preserved')
if __name__=='__main__':main()
