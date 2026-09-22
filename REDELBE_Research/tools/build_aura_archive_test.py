"""Build archive-backed Honoka experiment; preserve all unrelated archive records."""
import struct,json,hashlib
from pathlib import Path
from lr_resources import GAME,read_index,container_for
from build_aura_test import patch,records,columns
from lr_resources import extract
out=Path('experiments/aura/package');raw,es,_=read_index(GAME/'fdata_package/root.rdb');lookup={e['id']:e for e in es}
payload=extract(GAME/'fdata_package/root.rdb',lookup[0x285cb0c3]);a=next(payload[p:z] for p,z,fid in records(payload) if fid==0x399961)
_,d,n,t,count=columns(a)[0xe1773a02];tracks=list(struct.unpack('<15I',a[d:d+n]))
archive,_=container_for(GAME/'fdata_package/root.rdb',lookup[0x285cb0c3]);original=archive.read_bytes();result=bytearray(original[:16]);positions={};pos=16;changes=0
while pos<len(original):
 assert original[pos:pos+8]==b'IDRK0000'
 size=struct.unpack_from('<Q',original,pos+8)[0];fid=struct.unpack_from('<I',original,pos+36)[0];rec=original[pos:pos+size]
 if fid in (0x285cb0c3,0xf589e402,0xd14d76ef):
  data=patch(extract(GAME/'fdata_package/root.rdb',lookup[fid]),tracks)
  csize=struct.unpack_from('<I',rec,16)[0];header=bytearray(rec[:size-csize]);struct.pack_into('<Q',header,8,len(header)+len(data));struct.pack_into('<I',header,16,len(data));struct.pack_into('<Q',header,24,len(data));struct.pack_into('<I',header,44,struct.unpack_from('<I',header,44)[0]&~0x400000)
  rec=bytes(header)+data;changes+=1
 positions[pos]=(len(result),len(rec),fid);result.extend(rec);pos+=size
 if pos<len(original):pos=(pos+15)&~15;result.extend(b'\0'*((-len(result))%16))
assert changes==3
manifest=json.loads((out/'manifest.json').read_text());active=GAME/'REDELBE_LR'/manifest['active_package'];base=(active/manifest['original_root_target']).read_bytes();assert hashlib.sha256(base).hexdigest()==manifest['baseline_root_sha256'];index=bytearray(base)
offsets={};cursor=struct.unpack_from('<I',base,8)[0]
while cursor<len(base):
 offsets[struct.unpack_from('<I',base,cursor+36)[0]]=cursor
 cursor=(cursor+struct.unpack_from('<Q',base,cursor+8)[0]+3)&~3
for e in es:
 if e.get('package_hash')!=0xaf1960fa or e.get('ext_flags')!=0x401:continue
 p=offsets[e['id']]
 if base[p:p+e['entry_size']]!=raw[e['rdb_offset']:e['rdb_offset']+e['entry_size']]:
  assert e['id'] not in (0x285cb0c3,0xf589e402,0xd14d76ef)
  continue # Preserve existing mod index entries verbatim.
 newoff,newsize,fid=positions[e['offset']];assert fid==e['id'];ext=p+e['entry_size']-e['c_size'];assert e['c_size']==13
 struct.pack_into('<II',index,ext+2,newoff,newsize)
 if fid in (0x285cb0c3,0xf589e402,0xd14d76ef):
  struct.pack_into('<Q',index,p+24,e['file_size']+60);struct.pack_into('<I',index,p+44,e['flags']&~0x400000)
(out/'archive_root.rdb').write_bytes(index);(out/'0xaf1960fa.fdata').write_bytes(result)
print('Verified',len(positions),'records; replaced',changes,'archive bytes',len(result))



