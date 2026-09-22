"""SRSA LR: inspect/extract/replace embedded mono MS-ADPCM and Ogg audio.

Writes a NEW bank only. Unknown records and encrypted names are preserved.
Format reference: eterniti/eternity_common DOA6/SrsaFile.{h,cpp}, SrsCommon.h.
"""
import argparse,json,struct,hashlib
from pathlib import Path
AUDIO=0x70cbccc5
ADPCM={0xe96fd86a,0x27052510,0x2eb6ca6f}
OGG={0x7d43d038,0x7c002264,0x9f5292df}
COEFF=((256,0),(512,-256),(0,0),(192,64),(240,0),(460,-208),(392,-232))
def u(b,p):
 if p<0 or p+4>len(b):raise ValueError('Pointer outside record')
 return struct.unpack_from('<I',b,p)[0]
def put(b,p,v):struct.pack_into('<I',b,p,v)
def align(n):return (n+15)&~15
def chunk(tag,b):return tag+struct.pack('<I',len(b))+b+(b'\0' if len(b)%2 else b'')
def wrapped(data,magic):
 if data[:4]==b'KTSR':
  # Raw KTSR offsets are relative to its header; synthesize only the outer envelope.
  return magic+b'\0'*4+struct.pack('<Q',len(data)+16)+data
 return data
class Bank:
 def __init__(self,data):
  data=wrapped(data,b'ASRS')
  self.data=data;self.entries=[]
  if len(data)<80 or data[:4]!=b'ASRS' or data[16:20]!=b'KTSR':raise ValueError('Not an SRSA/KTSR bank')
  if u(data,8)!=len(data) or u(data,40)!=len(data)-16 or u(data,44)!=len(data)-16:raise ValueError('Bank length mismatch')
  p=80;seen=set()
  while p<len(data):
   size=u(data,p+4)
   if size<16 or p+size>len(data):raise ValueError('Entry length mismatch')
   e=data[p:p+size];sig,fid=u(e,0),u(e,8);key=(sig,fid)
   if key in seen:raise ValueError('Ambiguous duplicate record ID')
   seen.add(key);self.entries.append((p,e));p+=size
 def info(self,p,e):
  r={'id':f'0x{u(e,8):08x}','type':f'0x{u(e,0):08x}','bytes':len(e),'codec':'metadata'}
  if u(e,0)!=AUDIO:return r
  h=u(e,u(e,20));fmt=u(e,h);r.update(header=h,format=f'0x{fmt:08x}',codec='unsupported')
  if fmt in ADPCM:
   fp=h+u(e,h+40);dp=h+u(e,h+48);sp=h+u(e,h+52);start=h+u(e,dp);size=u(e,sp)
   if fp+4>len(e) or start+size>len(e) or start<h+56:
    r.update(codec='unsupported',reason='Unsupported or malformed ADPCM layout; this game variant has not been validated')
    return r
   samples,block=struct.unpack_from('<HH',e,fp)
   channels=u(e,h+12)
   r.update(codec='ms-adpcm',channels=channels,rate=u(e,h+20),samples=u(e,h+24),block=block,samples_per_block=samples,start=start,size=size,format_pointer=fp,size_pointer=sp)
   if not block or size%block:raise ValueError('Incomplete ADPCM block')
  elif fmt in OGG:
   kovs=16+u(e,h+52)-p
   if kovs<0 or kovs+32>len(e) or e[kovs:kovs+4]!=b'KOVS':r['codec']='external-ogg';return r
   size=u(e,kovs+4)
   if kovs+32+size>len(e):raise ValueError('Truncated Ogg payload')
   r.update(codec='ogg',channels=u(e,h+12),rate=u(e,h+24),samples=u(e,h+28),kovs=kovs,start=kovs+32,size=size)
  return r
 def audio(self,p,e):
  r=self.info(p,e)
  if r['codec']=='ms-adpcm':
   if r['channels']!=1 or r['samples_per_block']!=(r['block']-7)*2+2:raise ValueError('Only validated mono MS-ADPCM layout supported')
   fmt=struct.pack('<HHIIHHHHH',2,1,r['rate'],r['rate']*r['block']//r['samples_per_block'],r['block'],4,32,r['samples_per_block'],7)+b''.join(struct.pack('<hh',*v) for v in COEFF)
   wav=b'WAVE'+chunk(b'fmt ',fmt)+chunk(b'fact',struct.pack('<I',r['samples']))+chunk(b'data',e[r['start']:r['start']+r['size']])
   return '.wav',b'RIFF'+struct.pack('<I',len(wav))+wav
  if r['codec']=='ogg':
   b=bytearray(e[r['start']:r['start']+r['size']])
   for i in range(min(256,len(b))):b[i]^=i
   if b[:4]!=b'OggS':raise ValueError('Unexpected Ogg scrambling')
   return '.ogg',bytes(b)
  raise ValueError('Record is not supported embedded audio')
 def replace(self,fid,replacement):
  candidates=[(i,p,e) for i,(p,e) in enumerate(self.entries) if u(e,0)==AUDIO and u(e,8)==fid]
  if len(candidates)!=1:raise ValueError('Audio ID not unique/present')
  index,p,e=candidates[0];r=self.info(p,e);h=r['header']
  if self.audio(p,e)[1]==replacement:return self.data
  if r['codec']=='ms-adpcm':
   w=read_wav(replacement)
   if w['channels']!=r['channels']:raise ValueError('Channel count must match source')
   if w['coeff']!=COEFF or w['samples_per_block']!=(w['block']-7)*2+2:raise ValueError('Unsupported ADPCM coefficients/block format')
   data=w['data'];out=bytearray(e[:r['start']])+data+b'\0'*(align(len(data))-len(data))
   put(out,h+20,w['rate']);put(out,h+24,w['samples']);put(out,r['size_pointer'],len(data))
   struct.pack_into('<HH',out,r['format_pointer'],w['samples_per_block'],w['block'])
  elif r['codec']=='ogg':
   channels,rate,samples=ogg_info(replacement)
   if channels!=r['channels']:raise ValueError('Channel count must match source')
   data=bytearray(replacement)
   for i in range(min(256,len(data))):data[i]^=i
   out=bytearray(e[:r['start']])+data+b'\0'*(align(len(data))-len(data))
   put(out,r['kovs']+4,len(data));put(out,h+24,rate);put(out,h+28,samples);put(out,h+56,len(out)-r['kovs'])
  else:raise ValueError('External SRST audio replacement is not supported')
  put(out,4,len(out));put(out,h+4,len(out)-h)
  pieces=[];offset=80
  for i,(oldpos,entry) in enumerate(self.entries):
   edited=bytearray(out if i==index else entry)
   info=self.info(oldpos,entry)
   if info['codec']=='ogg':put(edited,info['header']+52,offset+info['kovs']-16)
   pieces.append(edited);offset+=len(edited)
  header=bytearray(self.data[:80]);put(header,8,offset);put(header,40,offset-16);put(header,44,offset-16)
  result=bytes(header)+b''.join(pieces);check=Bank(result)
  for i,((_,a),(_,b)) in enumerate(zip(self.entries,check.entries)):
   if i==index:continue
   ra=self.info(self.entries[i][0],a)
   expected=bytearray(a)
   if ra['codec']=='ogg':put(expected,ra['header']+52,check.entries[i][0]+ra['kovs']-16)
   if b!=expected:raise ValueError('Unrelated entry changed')
  _,decoded=check.audio(*check.entries[index])
  if r['codec']=='ogg' and decoded!=replacement:raise ValueError('Ogg roundtrip mismatch')
  if r['codec']=='ms-adpcm' and read_wav(decoded)!=read_wav(replacement):raise ValueError('ADPCM roundtrip mismatch')
  return result
def read_wav(b):
 if b[:4]!=b'RIFF' or b[8:12]!=b'WAVE' or u(b,4)+8!=len(b):raise ValueError('Expected RIFF WAVE')
 parts={};p=12
 while p<len(b):
  n=u(b,p+4)
  if p+8+n>len(b):raise ValueError('Truncated WAV chunk')
  tag=b[p:p+4]
  if tag in parts:raise ValueError('Duplicate WAV chunk')
  parts[tag]=b[p+8:p+8+n];p+=8+n+(n%2)
 fmt=parts.get(b'fmt ',b'');data=parts.get(b'data')
 if len(fmt)<22 or data is None:raise ValueError('WAV requires fmt/data')
 codec,ch,rate,avg,block,bits,extra,spb,ncoef=struct.unpack_from('<HHIIHHHHH',fmt)
 if codec!=2 or ch!=1 or bits!=4 or not block or not spb or len(data)%block or len(fmt)<22+4*ncoef:raise ValueError('Use mono MS-ADPCM WAV, not PCM WAV')
 samples=u(parts[b'fact'],0) if b'fact' in parts else len(data)//block*spb
 if not rate or samples>len(data)//block*spb:raise ValueError('Invalid WAV rate/sample count')
 return dict(channels=ch,rate=rate,block=block,samples_per_block=spb,samples=samples,coeff=tuple(struct.unpack_from('<hh',fmt,22+i*4) for i in range(ncoef)),data=data)
def ogg_info(b):
 p=0;packet=bytearray();ident=None;samples=0;serial=None;seq=0
 while p<len(b):
  if b[p:p+4]!=b'OggS' or p+27>len(b) or b[p+4]!=0:raise ValueError('Invalid Ogg page')
  granule,stream,num=struct.unpack_from('<QII',b,p+6)
  if serial is None:serial=stream
  if stream!=serial or num!=seq:raise ValueError('Chained/multiplexed Ogg unsupported')
  seq+=1;n=b[p+26];segments=b[p+27:p+27+n];q=p+27+n;end=q+sum(segments)
  if len(segments)!=n or end>len(b):raise ValueError('Truncated Ogg page')
  for length in segments:
   if ident is None:
    packet.extend(b[q:q+length])
    if length<255:
     if packet[:7]!=b'\x01vorbis' or len(packet)<30:raise ValueError('Expected Vorbis audio')
     ident=(packet[11],u(packet,12))
   q+=length
  if granule!=0xffffffffffffffff:samples=max(samples,granule)
  p=end
 if ident is None or samples>0xffffffff:raise ValueError('Unsupported Ogg sample count')
 return (*ident,samples)
def main():
 ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
 for command in ('list','extract','replace'):
  s=sub.add_parser(command);s.add_argument('bank',type=Path)
  if command=='extract':s.add_argument('output',type=Path)
  if command=='replace':s.add_argument('id',type=lambda s:int(s,0));s.add_argument('audio',type=Path);s.add_argument('output',type=Path)
 a=ap.parse_args();bank=Bank(a.bank.read_bytes())
 if a.command=='list':print(json.dumps([bank.info(p,e) for p,e in bank.entries],indent=2));return
 if a.command=='extract':
  if a.output.exists():raise ValueError('Use a new output directory')
  a.output.mkdir(parents=True);manifest=[]
  for p,e in bank.entries:
   info=bank.info(p,e)
   if info['codec'] in ('ms-adpcm','ogg'):
    ext,b=bank.audio(p,e);name=info['id']+ext;(a.output/name).write_bytes(b);info['file']=name
   manifest.append(info)
  (a.output/'tracks.json').write_text(json.dumps(manifest,indent=2));print('Extracted',sum('file' in r for r in manifest),'tracks');return
 if a.output.exists() or a.output.resolve()==a.bank.resolve():raise ValueError('Output must be a new file; input bank is never overwritten')
 result=bank.replace(a.id,a.audio.read_bytes());a.output.write_bytes(result);print('Verified new bank:',a.output,'SHA256',hashlib.sha256(result).hexdigest())
if __name__=='__main__':main()
