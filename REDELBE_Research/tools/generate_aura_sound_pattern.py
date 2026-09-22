from pathlib import Path
import sys,re
sys.path.insert(0,str(Path(__file__).parent/'python_deps'))
import capstone
root=Path(__file__).resolve().parents[1];b=(root/'analysis/lr_updated.bin').read_bytes()
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
out=['#pragma once']
for name,a,z in [('auraGameSePattern',0x37aa250,0x37aa33f),('auraPausePattern',0x37eb460,0x37eb526),('auraResumePattern',0x37eaf40,0x37eaf6c)]:
 data=b[a:z];mask=bytearray([255]*len(data))
 for i in md.disasm(data,a):
  if (i.group(capstone.CS_GRP_JUMP) or i.group(capstone.CS_GRP_CALL)) and i.imm_size and not a<=i.operands[0].imm<z:
   off=i.address-a+i.imm_offset;mask[off:off+i.imm_size]=bytes(i.imm_size)
  if any(op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP for op in i.operands):
   off=i.address-a+i.disp_offset;mask[off:off+4]=bytes(4)
 pattern=b''.join(re.escape(bytes([v])) if m else b'.' for v,m in zip(data,mask))
 hits=[m.start() for m in re.finditer(pattern,b,re.S)];assert (a in hits and len(hits)==2) if name=="auraResumePattern" else hits==[a],hits
 def lit(x):return '"'+''.join('\\x%02x'%v for v in x)+'"'
 out.append('static const GamePattern '+name+'={"'+name+'",'+lit(data)+','+lit(mask)+','+str(len(data))+',0};')
(root/'experiments/aura/native_test/aura_sound_patterns.h').write_text('\n'.join(out)+'\n')
print('Game SE pattern uniquely validated on LR 1.11')

