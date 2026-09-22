"""Bounds-checked DOA5 victory motion/camera decoder, research output only.
Format cross-check: dtk mnr DOA5PC Motion Importer 1.0.0 (public author folder).
No Blender dependency; unsupported encodings fail instead of guessing.
"""
import json, math, struct
from pathlib import Path

def unpack(data,off,fmt):
 n=struct.calcsize('<'+fmt)
 if off<0 or off+n>len(data):raise ValueError(f'Out of bounds {off:x}/{len(data):x}')
 return struct.unpack_from('<'+fmt,data,off)
def container(data,off,magic):
 if data[off:off+len(magic)]!=magic:raise ValueError('Wrong container')
 size,n,used,_,table=unpack(data,off+16,'5I')
 if size<48 or off+size>len(data) or n>1024 or table+n*4>size:raise ValueError('Invalid container')
 offsets=unpack(data,off+table,f'{n}I')
 if any(x and (x<48 or x>=size) for x in offsets):raise ValueError('Invalid subchunk')
 return data[off:off+size],offsets

def channel(data,off):
 if data[off:off+2]!=b'\x00\x07':return sparse_channel(data,off)
 pos=off+2;values=[]
 while len(values)<100000:
  a,b,tag=unpack(data,pos,'3B');pos+=3;count=a+256*b
  if tag==128:
   tail=unpack(data,pos,'B')[0];values.append(int.from_bytes(bytes([a,b,tail]),'little',signed=True));return [v/16384 for v in values]
  if tag in (125,126,127):
   if not values or count<1:raise ValueError('Invalid delta run')
   if tag==125:
    unpack(data,pos,'B');pos+=1;values.extend([values[-1]]*count)
   else:
    fmt='b' if tag==127 else 'h';diffs=unpack(data,pos,str(count)+fmt);pos+=count*struct.calcsize(fmt)
    for d in diffs:values.append(values[-1]+d)
  else:values.append(int.from_bytes(bytes([a,b,tag]),'little',signed=True))
 raise ValueError('Excessive channel length')
def sparse_channel(data,off):
 # Preserve sparse samples; absent keys are NOT silently interpolated.
 pos=off;values=[];pending=None
 for step in range(100000):
  high,low=unpack(data,pos,'2B');pos+=2
  flags=high&0xf8;packed=(high&7)*256+low;span,kind=divmod(packed,4)
  if flags in (0xa8,0x98,0x48):
   width={0xa8:10,0x98:8,0x48:4}[flags]
   raw=bytes(unpack(data,pos,f'{width}B'));pos+=width
   if span<2:raise ValueError('Invalid extended sparse span')
   values.append(int.from_bytes(raw[:4],'big',signed=True)/10000)
   pending=len(values);values.extend([None]*(span-1));continue
  if kind not in (0,1,3):raise ValueError('Unknown sparse key kind')
  width=6 if kind==3 else 2
  raw=bytes(unpack(data,pos,f'{width}B'));pos+=width
  prefix=(flags>>4)|(0xf0 if flags>127 else 0)
  v=int.from_bytes(bytes([prefix])+raw[:2],'big',signed=flags>127)/10000
  values.append(v)
  if pending is not None:
   values[pending]=v;pending=None
  if kind==0:return values
  if span<1:raise ValueError('Invalid sparse span')
  values.extend([None]*(span-1))
 raise ValueError('Unterminated sparse channel')
def decode(path):
 data,tdp=container(path.read_bytes(),0,b'tdpack');mpm,parts=container(data,tdp[2],b'char_dat');motions=[]
 for part in parts:
  if not part:continue
  motion,sections=container(mpm,part,b'char_dat')
  _,actions,bones,_=unpack(motion,sections[3],'4I');start=sections[3]+16;end=motion.index(0,start);root=motion[start:end].decode('ascii')
  if actions>1000 or bones>512:raise ValueError('Excessive action or bone count')
  tracks=[];base=sections[0]
  for action in unpack(motion,base,f'{actions}I'):
   offsets=unpack(motion,base+action,f'{bones*9}I')
   try:curves=[channel(motion,base+o) for o in offsets]
   except ValueError as error:
    tracks.append(dict(unsupported=str(error)));continue
   lengths=sorted(set(map(len,curves)))
   tracks.append(dict(lengths=lengths,channels=curves))
  motions.append(dict(root=root,bones=bones,actions=tracks))
 cam=tdp[1];table=unpack(data,cam+4,'I')[0];cameras=[]
 for i in range(1000):
  info=unpack(data,cam+table+4*i,'I')[0]
  if not info:break
  frames,unknown,por,eye,tilt,fov=unpack(data,cam+info,'6I')
  if frames>100000:raise ValueError('Excessive camera length')
  rows=[list(unpack(data,cam+eye+f*12,'3f'))+list(unpack(data,cam+por+f*12,'3f'))+[unpack(data,cam+tilt+f*4,'f')[0],unpack(data,cam+fov+f*4,'f')[0]] for f in range(frames)]
  if any(not math.isfinite(v) for row in rows for v in row):raise ValueError('Nonfinite camera')
  cameras.append(dict(frames=frames,eye_target_tilt_fov=rows))
 else:raise ValueError('Unterminated camera list')
 return dict(source=path.name,motions=motions,cameras=cameras)
if __name__=='__main__':
 root=Path(__file__).resolve().parents[1]/'experiments/doa5_victory_port';out=root/'decoded';out.mkdir(exist_ok=True)
 for p in root.glob('*.tdpack'):
  try:
   result=decode(p);(out/(p.stem+'.json')).write_text(json.dumps(result,separators=(',',':')))
   print(p.name,[(m['root'],m['bones'],[a.get('lengths',a.get('unsupported')) for a in m['actions']]) for m in result['motions']], 'camera frames',[c['frames'] for c in result['cameras']])
  except ValueError as e:print(p.name,'FAILED',e)




