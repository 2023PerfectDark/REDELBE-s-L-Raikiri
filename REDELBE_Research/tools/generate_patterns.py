"""Build-only: derive relocation-masked function signatures from the working build."""
import sys,struct,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'python_deps'))
import capstone
BASE=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common')
def pe(path):
 b=path.read_bytes();p=struct.unpack_from('<I',b,60)[0];n=struct.unpack_from('<H',b,p+6)[0];s=struct.unpack_from('<H',b,p+20)[0]
 size=struct.unpack_from('<I',b,p+24+56)[0];out=bytearray(size);sections=[]
 for i in range(n):
  o=p+24+s+i*40;vs,va,raw,off=struct.unpack_from('<IIII',b,o+8);out[va:va+raw]=b[off:off+raw]
  sections.append((b[o:o+8].rstrip(b'\0').decode(),va,vs))
 pr,ps=struct.unpack_from('<II',b,p+24+112+3*8)
 funcs=[(a,z) for a,z,u in struct.iter_unpack('<III',out[pr:pr+ps])]
 return bytes(out),funcs,sections

targets={'titleText':0x21c1df0,'caption':0x21c1e90,'release':0x22dbff0,'defaults':0x22ca6e0,'request':0x22c8270,'layout':0x21beda0,'random':0x3919430,'load':0x2a3f740,'cache0':0x22c6220,'cache1':0x22c6260,'cache2':0x22c6310,'cache3':0x22c63b0,'scale':0x22cc6e0,'keyboard':0xe4aea3,'randomCaller1':0x39a7c61,'randomCaller2':0x39b0fdc}
if '--crossfade-experimental' in sys.argv:targets['previewRender']=0x302b780
targets.update(layoutShow=0x21bd100,layoutHide=0x21bd430)
targets.update(layoutObject=0x21c3e20,rosterColor=0x172fd00)
targets.update(animationReset=0x21bf270,animationPlaying=0x21bf3d0)
_,funcs,_=pe(BASE/'Dead or Alive 6 Last Round - Backup 2026-09-15_210415/DOA6LR.exe')
old=Path('analysis/lr_baseline.bin').read_bytes()
new=Path('analysis/lr_updated.bin').read_bytes() if Path('analysis/lr_updated.bin').exists() else old
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
output={}
for name,rva in targets.items():
 a,z=next((a,z) for a,z in funcs if a<=rva<z)
 data=old[a:z];mask=bytearray(b'\xff'*len(data))
 for ins in md.disasm(data,a):
  relative=ins.group(capstone.CS_GRP_JUMP) or ins.group(capstone.CS_GRP_CALL)
  if relative and ins.imm_size and not (a<=ins.operands[0].imm<z):
   off=ins.address-a+ins.imm_offset;mask[off:off+ins.imm_size]=b'\0'*ins.imm_size
  if any(op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP for op in ins.operands):
   # RIP-relative addressing always encodes disp32. Capstone 5 reports disp_size=2
   # for some 66-prefixed SIMD instructions despite their four-byte displacement.
   off=ins.address-a+ins.disp_offset;mask[off:off+4]=b'\0'*4
 runs=[];start=0
 for i in range(len(mask)+1):
  if i==len(mask) or not mask[i]:
   if i>start:runs.append((start,i-start))
   start=i+1
 anchor,length=max(runs,key=lambda x:x[1]);needle=data[anchor:anchor+length]
 def matches(blob):
  hits=[];pos=0
  while True:
   p=blob.find(needle,pos)
   if p<0:break
   pos=p+1;b=p-anchor
   if b>=0 and b+len(data)<=len(blob) and all(not m or blob[b+i]==data[i] for i,m in enumerate(mask)):hits.append(b)
  return hits
 hits=matches(new)
 output[name]={'old':a,'offset':rva-a,'size':len(data),'data':data.hex(),'mask':mask.hex(),'anchor':anchor,'anchor_size':length,'new_matches':hits,'old_matches':matches(old)}
 print(name,hex(a),len(data),'new',*[hex(h) for h in hits])
Path('analysis/pattern_candidates.json').write_text(json.dumps(output,indent=2))
lines=['#pragma once','// Generated relocation-masked complete functions; no game resources or user paths.',
       'struct GamePattern { const char* name; const char* data; const char* mask; unsigned size; unsigned offset; };']
lines.append('static const GamePattern gamePatterns[]={')
for name,p in output.items():
 def literal(s):return '\n'.join('"'+''.join('\\x'+s[i:i+2] for i in range(start,min(start+2048,len(s)),2))+'"' for start in range(0,len(s),2048))
 lines.append('{"'+name+'",'+literal(p['data'])+','+literal(p['mask'])+','+str(p['size'])+','+str(p['offset'])+'},')
lines.append('};')
Path('prototype/game_patterns_data.h').write_text('\n'.join(lines)+'\n')
