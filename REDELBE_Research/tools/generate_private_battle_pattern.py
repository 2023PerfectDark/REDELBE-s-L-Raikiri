from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'python_deps'))
import capstone
root=Path(__file__).resolve().parents[1]
data=(root/'analysis/lr_updated.bin').read_bytes()[0x39e1870:0x39e1999]
c=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);c.detail=True
mask=bytearray([255]*len(data))
for i in c.disasm(data,0):
 if i.mnemonic=='call' and i.bytes[0]==0xe8:
  mask[i.address+i.imm_offset:i.address+i.imm_offset+i.imm_size]=bytes(i.imm_size)
 if any(o.type==capstone.x86.X86_OP_MEM and o.mem.base==capstone.x86.X86_REG_RIP for o in i.operands):
  mask[i.address+i.disp_offset:i.address+i.disp_offset+i.disp_size]=bytes(i.disp_size)
def esc(b):return ''.join('\\x%02x'%x for x in b)
(root/'experiments/hair_color/native_test/private_battle_pattern.h').write_text(
 '#pragma once\n// Read-only native capture; relocated calls/data addresses masked.\n'
 f'static const GamePattern privateBattlePattern={{"privateBattle","{esc(data)}","{esc(mask)}",{len(data)},0}};\n')
print('Generated battle owner pattern:',len(data),'bytes')
