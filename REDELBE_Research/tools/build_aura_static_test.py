"""Build model-static aura test; copies only, no original game writes."""
import struct,json,hashlib
from pathlib import Path
from lr_resources import GAME,read_index,extract,container_for
from build_aura_test import records,columns
out=Path('experiments/aura/static_package');out.mkdir(exist_ok=True)
ip=GAME/'fdata_package/root.rdb';raw,es,_=read_index(ip);lookup={e['id']:e for e in es}
b=extract(ip,lookup[0xd14d76ef]);a=next(b[p:z] for p,z,fid in records(b) if fid==0x399961);_,d,n,t,count=columns(a)[0xe1773a02];tracks=b''+a[d:d+n];assert count==15
manifest=json.loads(Path('experiments/aura/package/manifest.json').read_text());active=GAME/'REDELBE_LR'/manifest['active_package'];base=(active/manifest['original_root_target']).read_bytes();assert hashlib.sha256(base).hexdigest()==manifest['baseline_root_sha256'];index=bytearray(base)
offsets={};p=struct.unpack_from('<I',base,8)[0]
while p<len(base):
 offsets[struct.unpack_from('<I',base,p+36)[0]]=p;p=(p+struct.unpack_from('<Q',base,p+8)[0]+3)&~3
changes={}
for fid in (0x2082ad97,0xc0f49941):
 b=extract(ip,lookup[fid]);result=bytearray(b[:struct.unpack_from('<I',b,8)[0]]);found=0
 for p,z,oid in records(b):
  rec=b[p:z]
  if oid==0xe29b76db:
   at,d,n,t,count=columns(rec)[0xaa117b97];assert t==5 and count==0
   edited=bytearray(rec[:d]+tracks+rec[d:]);struct.pack_into('<I',edited,at+4,15);struct.pack_into('<I',edited,8,struct.unpack_from('<I',rec,8)[0]+len(tracks))
   old=columns(rec);new=columns(edited)
   for key,(_,sd,sn,st,sc) in old.items():
    _,nd,nn,nt,nc=new[key]
    if key!=0xaa117b97:assert (st,sc,rec[sd:sd+sn])==(nt,nc,edited[nd:nd+nn])
   rec=edited;found+=1
  result.extend(rec)
 assert found==1;struct.pack_into('<I',result,24,len(result));list(records(result));changes[fid]=bytes(result)
redirects=['fdata_package/root.rdb\taura_static/root.rdb']
for pkg in sorted({lookup[fid]['package_hash'] for fid in changes}):
 e=next(e for e in es if e.get('package_hash')==pkg);archive,_=container_for(ip,e);original=archive.read_bytes();result=bytearray(original[:16]);pos=16;positions={}
 while pos<len(original):
  assert original[pos:pos+8]==b'IDRK0000';size=struct.unpack_from('<Q',original,pos+8)[0];fid=struct.unpack_from('<I',original,pos+36)[0];rec=original[pos:pos+size]
  if fid in changes:
   data=changes[fid];csize=struct.unpack_from('<I',rec,16)[0];header=bytearray(rec[:size-csize]);struct.pack_into('<Q',header,8,len(header)+len(data));struct.pack_into('<I',header,16,len(data));struct.pack_into('<Q',header,24,len(data));struct.pack_into('<I',header,44,struct.unpack_from('<I',header,44)[0]&~0x400000);rec=bytes(header)+data
  positions[pos]=(len(result),len(rec),fid);result.extend(rec);pos+=size
  if pos<len(original):pos=(pos+15)&~15;result.extend(b'\0'*((-len(result))%16))
 for e in es:
  if e.get('package_hash')!=pkg or e.get('ext_flags')!=0x401:continue
  p=offsets[e['id']]
  if base[p:p+e['entry_size']]!=raw[e['rdb_offset']:e['rdb_offset']+e['entry_size']]:
   assert e['id'] not in changes;continue
  offset,size,fid=positions[e['offset']];assert fid==e['id'];assert e['c_size']==13;ext=p+e['entry_size']-13;struct.pack_into('<II',index,ext+2,offset,size)
  if fid in changes:struct.pack_into('<Q',index,p+24,len(changes[fid]));struct.pack_into('<I',index,p+44,e['flags']&~0x400000)
 (out/archive.name).write_bytes(result);redirects.append(f'fdata_package/{archive.name}\taura_static/{archive.name}');print(archive.name,len(positions),'records verified')
(out/'root.rdb').write_bytes(index);(out/'redirects.tsv').write_text('\n'.join(redirects)+'\n');print('Static model test prepared; original action tracks restored')
