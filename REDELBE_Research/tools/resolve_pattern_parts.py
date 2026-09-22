import json,sys,struct
from pathlib import Path
sys.path.insert(0,'tools/python_deps')
import capstone
src=Path(r'C:\Users\Owner\OneDrive\Documents\ChatGPT\AI vs AI DoA6LR\pattern_parts_v3_5_1_signatures.json')
b=Path('analysis/lr_updated.bin').read_bytes()
old=Path(r'C:\Users\Owner\OneDrive\Documents\ChatGPT\AI vs AI DoA6LR\doa6lr_loaded.bin').read_bytes()
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
pe=struct.unpack_from('<I',old,0x3c)[0];dr,ds=struct.unpack_from('<II',old,pe+0x18+0x70+3*8)
fs=list(struct.iter_unpack('<III',old[dr:dr+ds]))
def pattern(at):
 a,z,_=next(f for f in fs if f[0]<=at<f[1]);s=old[a:z];mask=bytearray([255]*len(s))
 for i in md.disasm(s,0):
  if any(o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP for o in i.operands):mask[i.address+i.disp_offset:i.address+i.disp_offset+i.disp_size]=bytes(i.disp_size)
  if i.mnemonic in ('call','jmp') and i.operands[0].type==capstone.x86.X86_OP_IMM:mask[i.address+i.imm_offset:i.address+i.imm_offset+i.imm_size]=bytes(i.imm_size)
 return s,mask
def find(s,mask):
 anchor=s[:next((i for i,v in enumerate(mask) if not v),len(s))];hits=[];p=0
 while True:
  p=b.find(anchor,p)
  if p<0:break
  if all(not m or b[p+i]==s[i] for i,m in enumerate(mask)):hits.append(p)
  p+=1
 return hits
items=[]
s,m=pattern(0x2309100);hits=find(s,m);assert len(hits)==1,hits
allocator=hits[0];items.append(dict(name='allocator',bytes=s.hex(),mask=m.hex(),rva=allocator));print('allocator',hex(allocator),len(s))
for name,v in json.loads(src.read_text())['signatures'].items():
 s,m=pattern(int(v['baseline_rva'],16));hits=find(s,m)
 if name=='lr33Push':hits=[p for p in hits if b[p+len(s)-5]==0xe9 and p+len(s)+struct.unpack_from('<i',b,p+len(s)-4)[0]==allocator]
 if name=='lr33GetSetting':
  assert 1<=len(hits)<=2
  roots={p+0x2e+struct.unpack_from('<i',b,p+0x2a)[0] for p in hits};assert len(roots)==1,roots
 else:assert len(hits)==1,(name,hits)
 r=hits[0];print(name,hex(r),len(s));items.append(dict(name=name,bytes=s.hex(),mask=m.hex(),rva=r))
 for i in md.disasm(b[r:r+min(len(s),65)],r):print(hex(i.address),i.mnemonic,i.op_str)
Path('analysis/pattern_parts_lr_patterns.json').write_text(json.dumps(items,indent=2))
def literal(h):return '"'+''.join('\\x'+h[i:i+2] for i in range(0,len(h),2))+'"'
lines=['#pragma once','struct PartsPattern {const char* name;const char* bytes;const char* mask;size_t size;};','static const PartsPattern partsPatterns[]={']
for v in items:lines.append('{"'+v['name']+'",'+literal(v['bytes'])+','+literal(v['mask'])+','+str(len(v['bytes'])//2)+'},')
lines.append('};');Path('experiments/mouse_menu/pattern_parts_patterns.h').write_text('\n'.join(lines)+'\n')
