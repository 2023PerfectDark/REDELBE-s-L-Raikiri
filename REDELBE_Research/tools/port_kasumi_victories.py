"""Local Kasumi DOA5 -> LR body/camera prototype. Does not modify either game."""
from pathlib import Path
import struct,json,math,zlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1]/'experiments/doa5_victory_port'
MAP=[2,12,10,7,17,19,3,5,15,8,18,20,4,6,16,11,9,13,23,14,24]
def u(b,p,fmt):return struct.unpack_from('<'+fmt,b,p)
def qmat(q):
 x,y,z,w=q;n=x*x+y*y+z*z+w*w;x,y,z,w=np.array(q)/math.sqrt(n)
 return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def euler(v):
 x,y,z=v;cx,sx=math.cos(x),math.sin(x);cy,sy=math.cos(y),math.sin(y);cz,sz=math.cos(z),math.sin(z)
 return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
def rotvec(m,previous=None):
 # Stable matrix -> quaternion; then choose quaternion sign for continuity.
 t=np.trace(m)
 if t>0:
  s=math.sqrt(t+1)*2;q=np.array([(m[2,1]-m[1,2])/s,(m[0,2]-m[2,0])/s,(m[1,0]-m[0,1])/s,s/4])
 else:
  i=int(np.argmax(np.diag(m)));j=(i+1)%3;k=(i+2)%3;s=math.sqrt(max(0,1+m[i,i]-m[j,j]-m[k,k]))*2;q=np.zeros(4);q[i]=s/4;q[j]=(m[j,i]+m[i,j])/s;q[k]=(m[k,i]+m[i,k])/s;q[3]=(m[k,j]-m[j,k])/s
 q/=np.linalg.norm(q)
 if previous is not None and np.dot(q,previous)<0:q=-q
 elif previous is None and q[3]<0:q=-q
 n=np.linalg.norm(q[:3]);v=q[:3]*(2*math.atan2(n,q[3])/n) if n>1e-10 else q[:3]*2
 return v,q

def skeletons():
 b=(ROOT/'DOA5_KASUMI_COS_001.decoded.TMC').read_bytes()
 def offsets(base):
  count=u(b,base+20,'I')[0];off=u(b,base+32,'I')[0];return [base+x for x in u(b,base+off,f'{count}I')]
 parts=offsets(0);h=offsets(parts[6]);nodes=offsets(parts[8]);src=[]
 for i in range(len(h)):
  name=b[nodes[i]+64:b.index(b'\0',nodes[i]+64)].decode();assert i>=21 or name.startswith(f'MOT{i:02d}_')
  matrix=np.array(u(b,h[i],'16f')).reshape(4,4).T;parent=u(b,h[i]+64,'I')[0];src.append((parent,matrix[:3,:3]))
 b=(ROOT/'KAS_COS_001.g1m').read_bytes();p=u(b,12,'I')[0];dst={};ix_to_id={}
 while p<len(b):
  sig,ver,size=u(b,p,'4s4sI')
  if sig==b'SM1G':
   bo,_,n,ni,np_,_=u(b,p+12,'II4H');ids=u(b,p+28,f'{ni}H');ix_to_id={ix:bid for bid,ix in enumerate(ids) if ix!=65535}
   for bid,ix in enumerate(ids):
    if ix==65535:continue
    a=p+bo+ix*48;parent=u(b,a+12,'H')[0];dst[bid]=(ix_to_id.get(parent,-1),qmat(u(b,a+16,'4f')),np.array(u(b,a+32,'3f')))
   break
  p+=size
 def worlds(items):
  out={}
  def get(i):
   if i not in out:
    p,r=items[i][:2];out[i]=get(p)@r if p in items else r
   return out[i]
  for i in items:get(i)
  return out
 sw=worlds(dict(enumerate(src)));tw=worlds(dst)
 for i,bid in enumerate(MAP):
  sp=src[i][0]
  if sp<21:assert dst[bid][0]==MAP[sp],(i,bid,'hierarchy mismatch')
 return src,dst,sw,tw

def pack(v):
 for exp in range(16):
  step=2**(exp-15);a=np.rint(np.array(v)/step).astype(np.int64)
  if np.all(a>=-524288) and np.all(a<=524287):return (exp<<60)|sum((int(x)&0xfffff)<<s for x,s in zip(a,[40,20,0]))
 raise ValueError('Vector cannot be packed')
def unpack(v):
 step=2**((v>>60)-15);a=[(v>>s)&0xfffff for s in [40,20,0]];return np.array([x-(1<<20) if x&(1<<19) else x for x in a])*step

def reduced_keys(values,tolerance):
 keep={0,len(values)-1};pending=[(0,len(values)-1)]
 while pending:
  first,last=pending.pop()
  if last-first<2:continue
  fraction=np.arange(1,last-first)/(last-first)
  expected=values[first]+fraction[:,None]*(values[last]-values[first])
  error=np.max(np.abs(values[first+1:last]-expected),axis=1);at=int(np.argmax(error))
  if error[at]>tolerance:
   split=first+1+at;keep.add(split);pending.extend([(first,split),(split,last)])
 return sorted(keep)

def write_body(path,transforms,ids,frames,reduce=False):
 key=bytearray();vectors=bytearray();table=[]
 for bid in ids:
  channels=transforms[bid];table.append(((len(key)//4)<<16)|(bid<<4)|len(channels))
  for op,values in channels:
   values=np.asarray(values);constant=np.max(np.abs(values-values[0]))<1e-8
   times=[0] if constant else reduced_keys(values,.001 if op==0 else .005) if reduce else list(range(len(values)))
   values=values[times]
   count=len(values);first=len(vectors)//32;key+=struct.pack('<HHI',op,count,first)+struct.pack('<'+str(count)+'H',*times);key+=bytes((-len(key))%4)
   for i,v in enumerate(values):
    end=values[min(i+1,count-1)];delta=end-v
    vectors+=struct.pack('<4Q',pack(v),pack(delta),0,0)
 # Header frames includes last key; native clips also use inclusive final frame.
 header=struct.pack('<8sIfHHIII',b'_A2G0400',32+4*len(ids)+len(key)+len(vectors),30.,frames-1,len(ids)<<4,len(key),len(vectors)//32,0)
 out=header+struct.pack('<'+str(len(ids))+'I',*table)+key+vectors;path.write_bytes(out)
 # Validate every encoded field/offset and numerical round trip.
 for bid,channels in transforms.items():
  for op,vals in channels:
   for v in vals:
    if np.max(np.abs(unpack(pack(v))-v))>.02:raise ValueError('Packing precision failure')
 return len(out)

def camera(path,rows,template):
 # Preserve the verified camera header metadata, replace all tracks and offsets.
 frames=len(rows);b=bytearray(template[:48]);struct.pack_into('<I',b,32,1);b+=struct.pack('<4I',1,0,1,0);track=len(b);b+=bytes(80);struct.pack_into('<I',b,track,102)
 rows=np.array(rows);channels=np.column_stack([rows[:,:6]*100,np.radians(rows[:,6:8]),np.ones(frames)])
 for c in range(9):
  start=len(b);assert (start-track)%16==0
  struct.pack_into('<ii',b,track+4+c*8,frames,(start-track)//16)
  for f in range(frames):
   v=channels[f,c];nextv=channels[min(f+1,frames-1),c];b+=struct.pack('<4f',0,0,nextv-v,v)
  b+=struct.pack('<'+str(frames)+'f',*[(f+1)/30 for f in range(frames)]);b+=bytes((-len(b))%16)
 struct.pack_into('<I',b,8,len(b)//16);struct.pack_into('<f',b,16,(frames-1)/30);path.write_bytes(b)

def main():
 src,dst,sw,tw=skeletons();out=ROOT/'prototype';(out/'Clips').mkdir(parents=True,exist_ok=True);(out/'Cameras').mkdir(exist_ok=True)
 templateRoot=ROOT.parent/'animation_browser/AnimationBrowser';native=(templateRoot/'Clips/0x0143fbdc.g1a').read_bytes();n=u(native,18,'H')[0]>>4;ids=[(u(native,32+i*4,'I')[0]>>4)&1023 for i in range(n)];assert all(i in dst for i in ids)
 # Animation axes are not the costume's angled skin bind pose. In particular,
 # elbows bend about LR Z; using the 45-degree TMC arm bind introduced twist.
 basis={i:sw[i].T@tw[bid] for i,bid in enumerate(MAP)}
 left=np.array([[1.,0,0],[0,0,-1],[0,1,0]])
 right=np.array([[-1.,0,0],[0,0,1],[0,1,0]])
 for i in (17,8,4,5):basis[i]=left
 for i in (19,14,10,11):basis[i]=right
 # Match native channel presence; do not impose costume bind translations on
 # arm joints whose placement is supplied by LR's live character skeleton.
 native_ops={}
 for ix in range(n):
  entry=u(native,32+ix*4,'I')[0];bid=(entry>>4)&1023;at=32+4*n+(entry>>16)*4;ops=[]
  for _ in range(entry&15):
   op,count,first=u(native,at,'HHI');ops.append(op);at=(at+8+count*2+3)&~3
  native_ops[bid]=ops
 catalog=[];cams=[];report=[]
 for kind,suffix in [('WIN','120'),('WIN','122'),('WIN','124'),('ENTRY','100'),('ENTRY','101'),('ENTRY','102')]:
  source=f'KASUMI_MOT_{kind}_{suffix}' if kind!='TAG_ENTRY' else 'KASUMI_MOT_TAG_ENTRY'
  data=json.loads((ROOT/'decoded'/(source+'.json')).read_text());curves=np.array(data['motions'][0]['actions'][0]['channels']);frames=curves.shape[1];trans={bid:[(0,[]),(1,[])] for bid in ids};previous={}
  # Source hand track order is named by its TMC nodes (130..163).
  finger_ids=[32,40,50,36,34,42,52,46,56,60,44,54,58,None,30,38,48]
  hand_curves={};finger_map={}
  for side,start in enumerate([130,147]):
   motion=next(m for m in data['motions'] if m['root']==('OPT_Hand_Left_Root' if side==0 else 'OPT_Hand_Right_Root'))
   raw=motion['actions'][0]['channels'];assert len(raw)==153
   dense=[]
   for channel in raw:
    assert len(channel)==frames
    keys=[i for i,v in enumerate(channel) if v is not None];assert keys and keys[0]==0 and keys[-1]==frames-1
    # Dense clips preserve every sample; sparse curves use linear key interpolation.
    dense.append(np.interp(np.arange(frames),keys,[channel[i] for i in keys]))
   hand_curves.update({start+i:np.array(dense[i*9:(i+1)*9]) for i in range(17)})
   for i,bid in enumerate(finger_ids):
    if bid is not None:
     finger_map[start+i]=bid+side
     assert bid+side in ids
     source_parent=src[start+i][0]
     expected=19+side if source_parent==start+13 else finger_ids[source_parent-start]+side
     assert dst[bid+side][0]==expected
  for frame in range(frames):
   world={}
   def get(i):
    if i not in world:
     p=src[i][0];r=euler(hand_curves[i][3:6,frame]) if i in hand_curves else euler(curves[i*9+3:i*9+6,frame]);world[i]=get(p)@r if p<21 or p in hand_curves else r
    return world[i]
   target={bid:get(i)@basis[i] for i,bid in enumerate(MAP)}
   # Carry the wrist basis correction through the hand, preserving finger locals.
   for i,bid in finger_map.items():
    wrist=5 if i<147 else 11
    old_wrist=get(wrist)@sw[wrist].T@tw[MAP[wrist]]
    correction=target[MAP[wrist]]@old_wrist.T
    target[bid]=correction@get(i)@sw[i].T@tw[bid]
   target[0]=np.eye(3);target[1]=np.eye(3)
   def target_world(bid):
    if bid not in target:
     p,r,_=dst[bid];target[bid]=target_world(p)@r if p in dst else r
    return target[bid]
   for bid in ids:
    p,bind,t=dst[bid];local=target_world(p).T@target_world(bid) if p in dst else target_world(bid);v,q=rotvec(local,previous.get(bid));previous[bid]=q
    pos=curves[:3,frame]*100 if bid==1 else t
    trans[bid][0][1].append(v);trans[bid][1][1].append(pos)
  trans={bid:[channel for channel in channels if channel[0] in native_ops[bid]] for bid,channels in trans.items()}
  name=f'KAS_DOA5_{kind}_{suffix}_PORT_TEST.g1a';hid=zlib.crc32(name.encode());rel=f'Clips/0x{hid:08x}.g1a';size=write_body(out/rel,trans,ids,frames)
  camrel=f'Cameras/0x{hid:08x}.g1a';camera(out/camrel,data['cameras'][0]['eye_target_tilt_fov'],(ROOT.parent/'animation_browser/kasumi_camera_test.g1a').read_bytes())
  category='Victory' if kind=='WIN' else 'Intro'
  catalog.append(f'KAS\t{category}\t{name}\t{rel}');cams.append(f'{name}\t{camrel}');report.append(dict(name=name,frames=frames,bones=n,bytes=size,seconds=(frames-1)/30))
 (out/'catalog.append.tsv').write_text('\n'.join(catalog)+'\n');(out/'cameras.append.tsv').write_text('\n'.join(cams)+'\n');(out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()

