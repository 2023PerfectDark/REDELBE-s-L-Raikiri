from pathlib import Path
import sys,re
sys.path.insert(0,str(Path(__file__).parent/'python_deps'))
import capstone
root=Path(__file__).resolve().parents[1];b=(root/'analysis/lr_updated.bin').read_bytes()
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
out=['#pragma once']
for name,a,z in [('previewMusicWrapper',0x37aa380,0x37aa3de),('previewMusicNative',0x37cf280,0x37cf2b6)]:
 data=b[a:z];mask=bytearray([255]*len(data))
 for i in md.disasm(data,a):
  if (i.group(capstone.CS_GRP_JUMP) or i.group(capstone.CS_GRP_CALL)) and i.imm_size and not a<=i.operands[0].imm<z:
   off=i.address-a+i.imm_offset;mask[off:off+i.imm_size]=bytes(i.imm_size)
  if any(op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP for op in i.operands):
   off=i.address-a+i.disp_offset;mask[off:off+4]=bytes(4)
 pattern=b''.join(re.escape(bytes([v])) if m else b'.' for v,m in zip(data,mask))
 hits=[m.start() for m in re.finditer(pattern,b,re.S)];assert hits==[a],hits
 def lit(x):return '"'+''.join('\\x%02x'%v for v in x)+'"'
 out.append('static const GamePattern '+name+'={"'+name+'",'+lit(data)+','+lit(mask)+','+str(len(data))+',0};')
(root/'experiments/stage_video/preview_music_patterns.h').write_text('\n'.join(out)+'\n')
print('Both music patterns uniquely validated on LR 1.11')
