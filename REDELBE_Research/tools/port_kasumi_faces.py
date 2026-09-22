"""Experimental spatial facial retarget. Original DOA5 expressions, LR face rig.
Research output only: validate visually before release; not a one-to-one rig map.
"""
from pathlib import Path
import json,sys,numpy as np,zlib
sys.path.insert(0,str(Path(__file__).parent))
import port_kasumi_victories as p
R=p.ROOT

def worlds(items):
 out={}
 def get(i):
  if i not in out:
   parent,m=items[i];out[i]=(get(parent) if parent in items else np.eye(4))@m
  return out[i]
 for i in items:get(i)
 return out

def rigs():
 b=(R/'DOA5_KASUMI_FACE.decoded.TMC').read_bytes()
 def offsets(base):
  n=p.u(b,base+20,'I')[0];o=p.u(b,base+32,'I')[0];return [base+x for x in p.u(b,base+o,f'{n}I')]
 h=offsets(offsets(0)[6]);src={i:(p.u(b,o+64,'I')[0],np.array(p.u(b,o,'16f')).reshape(4,4).T) for i,o in enumerate(h)}
 sw=worlds(src);head=np.linalg.inv(sw[0]);sw={i:head@m for i,m in sw.items()}
 for m in sw.values():m[:3,3]*=100
 b=(R/'KAS_FACE_001.g1m').read_bytes();at=p.u(b,12,'I')[0]
 while b[at:at+4]!=b'SM1G':at+=p.u(b,at+8,'I')[0]
 bo,_,n,ni,_,_=p.u(b,at+12,'II4H');ids=p.u(b,at+28,f'{ni}H');inv={ix:bid for bid,ix in enumerate(ids) if ix!=65535};dst={}
 for bid,ix in enumerate(ids):
  if ix==65535:continue
  o=at+bo+ix*48;m=np.eye(4);m[:3,:3]=p.qmat(p.u(b,o+16,'4f'));m[:3,3]=p.u(b,o+32,'3f');dst[bid]=(inv.get(p.u(b,o+12,'H')[0],-1),m)
 tw=worlds(dst);center=tw[12][:3,3].copy()
 for m in tw.values():m[:3,3]-=center
 return src,sw,dst,tw

def main():
 src,sw,dst,tw=rigs();template=(R/'KAS_FACIAL_7020_WIN.g1a').read_bytes();n=p.u(template,18,'H')[0]>>4;ids=[(p.u(template,32+i*4,'I')[0]>>4)&1023 for i in range(n)]
 # Explicit articulated controls; surface bones receive a smooth local field.
 direct={136:8,143:6,144:7,145:7,249:12,383:30}
 controls=[i for i in range(2,45) if i not in (6,7,8,12,30)]
 points=np.array([sw[i][:3,3] for i in controls]);weights={};audit=[]
 for bid in ids:
  if bid in direct:continue
  point=tw[bid][:3,3];dist=np.linalg.norm(points-point,axis=1)
  # Do not blend a left-side expression into the opposite side of the face.
  if abs(point[0])>.75:dist=np.where(points[:,0]*point[0]<-.25,dist+100,dist)
  near=np.argsort(dist)[:4];w=1/np.maximum(dist[near],.15)**4;w/=w.sum();weights[bid]=(near,w)
  audit.append(dict(target=bid,sources=[controls[i] for i in near],weights=w.tolist(),nearest_cm=float(dist[near[0]])))
 delta='--delta' in sys.argv
 out=R/('prototype/FacesDeltas' if delta else 'prototype/Faces');out.mkdir(exist_ok=True);rows=[];report=[]
 for kind,suffix in [('WIN','120'),('WIN','122'),('WIN','124'),('ENTRY','100'),('ENTRY','101'),('ENTRY','102')]:
  data=json.loads((R/'decoded'/f'KASUMI_MOT_{kind}_{suffix}.json').read_text());motion=next(m for m in data['motions'] if m['root']=='OPT_Face_Root');raw=motion['actions'][0]['channels'];frames=len(raw[0]);dense=[]
  for channel_index,ch in enumerate(raw):
   keys=[i for i,v in enumerate(ch) if v is not None];assert keys[0]==0 and keys[-1]==frames-1
   values=np.array([ch[i] for i in keys])
   if channel_index%9 in (3,4,5):values=np.unwrap(values)
   dense.append(np.interp(np.arange(frames),keys,values))
  a=np.array(dense).reshape(44,9,frames);trans={bid:[(0,[]),(1,[])] for bid in ids};previous={};max_displacement=0
  for frame in range(frames):
   animated={0:np.eye(4)}
   def source(i):
    if i not in animated:
     v=a[i-2,:,frame];m=np.eye(4);m[:3,:3]=p.euler(v[3:6]);m[:3,3]=v[:3]*100
     parent=src[i][0];animated[i]=source(parent)@m
    return animated[i]
   skin={i:source(i)@np.linalg.inv(sw[i]) for i in range(2,45)}
   posed={i:tw[i].copy() for i in dst if i not in ids}
   for bid in ids:
    rest=tw[bid];m=rest.copy()
    if bid in direct:
     i=direct[bid];m[:3,:3]=skin[i][:3,:3]@rest[:3,:3];m[:3,3]=rest[:3,3]+source(i)[:3,3]-sw[i][:3,3]
    else:
     near,w=weights[bid];mat=sum(skin[controls[j]]*v for j,v in zip(near,w));m[:3,3]=(mat@np.append(rest[:3,3],1))[:3]
     u,_,vh=np.linalg.svd(mat[:3,:3]);rot=u@vh
     if np.linalg.det(rot)<0:u[:,-1]*=-1;rot=u@vh
     m[:3,:3]=rot@rest[:3,:3]
    displacement=np.linalg.norm(m[:3,3]-rest[:3,3]);max_displacement=max(max_displacement,float(displacement));assert displacement<12,'Face displacement out of bounds'
    posed[bid]=m
   for bid in ids:
    parent=dst[bid][0];local=np.linalg.inv(posed[parent])@posed[bid]
    rotation=dst[bid][1][:3,:3].T@local[:3,:3] if delta else local[:3,:3]
    translation=local[:3,3]-dst[bid][1][:3,3] if delta else local[:3,3]
    v,q=p.rotvec(rotation,previous.get(bid));previous[bid]=q
    trans[bid][0][1].append(v);trans[bid][1][1].append(translation)
  name=f'KAS_DOA5_{kind}_{suffix}_PORT_TEST.g1a';hid=zlib.crc32(name.encode());path=out/f'0x{hid:08x}.g1a';size=p.write_body(path,trans,ids,frames,reduce=True)
  rows.append(f'{name}\tFaces/{path.name}');report.append(dict(name=name,bones=len(ids),frames=frames,bytes=size,max_displacement_cm=max_displacement));print(report[-1],flush=True)
 prefix='face_delta' if delta else 'face'
 (R/f'prototype/{prefix}s.append.tsv').write_text('\n'.join(rows)+'\n');(R/f'prototype/{prefix}_mapping.json').write_text(json.dumps(audit,indent=2));(R/f'prototype/{prefix}_report.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()

