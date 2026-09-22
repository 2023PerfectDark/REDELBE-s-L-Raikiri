"""Prepare a reversible, Honoka-only aura attachment experiment. No game writes."""
import struct,json,hashlib
from pathlib import Path
from lr_resources import GAME,read_index,extract
from build_layer2_package import wrap
SIZES={0:1,1:1,2:2,3:2,4:4,5:4,8:4,10:16,12:8,13:12}
def records(b):
 assert b[:4]==b'_DOK'
 p=struct.unpack_from('<I',b,8)[0];count=0
 while p<len(b):
  sig,ver,size,fid=struct.unpack_from('<4I',b,p)
  assert sig in (0x4b4f4449,0x4b4f4452) and size>=24 and p+size<=len(b)
  z=(p+size+3)&~3;yield p,z,fid;count+=1;p=z
 assert p==len(b) and count==struct.unpack_from('<I',b,16)[0]
def columns(record):
 h=24 if record[:4]==b'IDOK' else 28
 n=struct.unpack_from('<I',record,h-4)[0];data=h+n*12;out={}
 for i in range(n):
  at=h+i*12;t,num,fid=struct.unpack_from('<III',record,at);length=SIZES[t]*num
  assert data+length<=len(record)
  out[fid]=(at,data,length,t,num);data+=length
 return out
def patch(b,tracks):
 out=bytearray(b[:struct.unpack_from('<I',b,8)[0]]);changed=0
 for p,z,fid in records(b):
  rec=b[p:z]
  if fid==0x0c3844a7: # Honoka's normal idle action only.
   at,d,n,t,count=columns(rec)[0xe1773a02];assert t==5
   existing=list(struct.unpack('<'+'I'*count,rec[d:d+n]));assert not set(existing)&set(tracks)
   extra=struct.pack('<'+'I'*len(tracks),*tracks)
   edited=bytearray(rec[:d+n]+extra+rec[d+n:])
   struct.pack_into('<I',edited,at+4,count+len(tracks))
   struct.pack_into('<I',edited,8,struct.unpack_from('<I',rec,8)[0]+len(extra))
   # All preexisting fields/data are retained; only this list and its size grow.
   nc=columns(edited)
   for key,(_,cd,cl,ct,cn) in columns(rec).items():
    _,nd,nl,nt,nn=nc[key]
    assert nt==ct
    if key!=0xe1773a02:assert (cl,cn,rec[cd:cd+cl])==(nl,nn,edited[nd:nd+nl])
   rec=edited;changed+=1
  out.extend(rec)
 assert changed==1
 struct.pack_into('<I',out,24,len(out));list(records(out));return bytes(out)
def main():
 out=Path('experiments/aura/package');out.mkdir(parents=True,exist_ok=True);(out/'data').mkdir(exist_ok=True)
 ip=GAME/'fdata_package/root.rdb';raw,es,_=read_index(ip);lookup={e['id']:e for e in es}
 payload=extract(ip,lookup[0x285cb0c3]);action=next(payload[p:z] for p,z,fid in records(payload) if fid==0x399961)
 _,d,n,t,count=columns(action)[0xe1773a02];assert t==5 and count==15
 tracks=list(struct.unpack('<15I',action[d:d+n]))
 gamework=GAME/'REDELBE_LR';selected=(gamework/'active_package.txt').read_text().strip();active=gamework/selected
 lines=(active/'redirects.tsv').read_text(encoding='utf-8-sig').splitlines()
 rootline=next(line for line in lines if line.replace('\\','/').startswith('fdata_package/root.rdb\t'))
 rootfile=active/rootline.split('\t')[1];base=rootfile.read_bytes();patched=bytearray(base)
 offsets={fid:(p,z) for p,z,fid in []}
 # The active index may already contain mods. Read its record offsets directly.
 pos=struct.unpack_from('<I',base,8)[0]
 while pos<len(base):
  size=struct.unpack_from('<Q',base,pos+8)[0];fid=struct.unpack_from('<I',base,pos+36)[0]
  offsets[fid]=pos;pos=(pos+size+3)&~3
 changes=[]
 for fid in (0x285cb0c3,0xf589e402):
  e=lookup[fid];assert e['c_size']==13
  # Avoid silently replacing a modded version of these shared databases.
  pos=offsets[fid];assert base[pos:pos+e['entry_size']]==raw[e['rdb_offset']:e['rdb_offset']+e['entry_size']],hex(fid)
  original=extract(ip,e);result=patch(original,tracks);container=wrap(raw,e,result)
  (out/'data'/f'0x{fid:08x}.file').write_bytes(container)
  struct.pack_into('<Q',patched,pos+24,len(result));struct.pack_into('<I',patched,pos+44,0x20000)
  ext=pos+e['entry_size']-13;struct.pack_into('<HII',patched,ext,0xc01,0,len(container))
  changes.append(dict(id=hex(fid),original_sha256=hashlib.sha256(original).hexdigest(),patched_sha256=hashlib.sha256(result).hexdigest()))
 (out/'root.rdb').write_bytes(patched)
 (out/'manifest.json').write_text(json.dumps(dict(status='UNVERIFIED HONOKA IDLE TEST',active_package=selected,baseline_root_sha256=hashlib.sha256(base).hexdigest(),original_root_target=rootline.split('\t')[1],changes=changes),indent=2))
 print('Prepared Honoka-only test; 15 tracks appended; all other fields preserved.')
if __name__=='__main__':main()
