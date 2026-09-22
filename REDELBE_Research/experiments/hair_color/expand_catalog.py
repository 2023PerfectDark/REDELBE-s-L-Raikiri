import sys,re,json,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from lr_resources import GAME,read_index,extract
from dok_patch import records,props,u

def object_hash(s):
 h=0;p=31
 for c in s.encode('utf-8'):
  h=(h+(c if c<128 else c-256)*p)&0xffffffff;p=p*31&0xffffffff
 return h

def audit():
 p=GAME/'fdata_package/root.rdb';_,entries,_=read_index(p);idx={e['id']:e for e in entries}
 b=extract(p,idx[0xd956e4a2]);refs={}
 for r in records(b):
  for k,t,n,v,z in props(b,r):
   if k==0x6c7321d2 and t==5 and n==1:refs[r[2]]=u(b,v)
 rows=[]
 lines=(GAME/'KashiraProjects/Name2Hash/DOA6LR.csv').read_text(encoding='utf-8-sig').splitlines()
 lines += [f'0,MPR_Muscle_Character_{ch}HAIR{i:03}_{part}_kidsalb.g1t' for ch in 'AYA BAS BAY BRA CRI DGO ELI HEL HON HTM HYT JAN KAS KOK LEI LIS MAR MIL MOM MNT MPP NIC NYO PHF RAC RID RIG RYU SKD SNK MAI TIN ZAC'.split() for i in range(121) for part in ['hair','hair_BLEND','hair01_BLEND','hair02_BLEND','hair03_BLEND']]
 seen=set()
 for line in lines:
  h,_,name=line.partition(',')
  m=re.fullmatch(r'MPR_Muscle_Character_([A-Z]{3})(HAIR|FACE)(\d{3})_(hair(?:\d+|_[a-z])?(?:_BLEND)?)_kidsalb.g1t',name,re.I)
  if not m:continue
  if name in seen:continue
  seen.add(name)
  oid=object_hash('CE1ResourceStaticTexture［'+name[:-4]+'］');fid=refs.get(oid)
  if fid is None:continue
  rows.append(dict(character=m[1],kind=m[2],slot=m[3],part=m[4],name=name,object=f'{oid:08x}',resource=f'{fid:08x}' if fid is not None else None,in_index=fid in idx))
 return rows
if __name__=='__main__':
 rows=audit();Path(__file__).with_name('expanded_candidates.json').write_text(json.dumps(rows,indent=2))
 print('verified',sum(r['resource'] is not None for r in rows),'total',len(rows));print(collections.Counter(r['character'] for r in rows if r['resource']))
 print('unverified',[(r['character'],r['kind'],r['slot']) for r in rows if not r['resource']][:20])
