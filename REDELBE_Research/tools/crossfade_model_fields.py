import sys
from pathlib import Path
sys.path.insert(0,str(Path('tools/python_deps').resolve()))
import capstone
exec(open('tools/find_branding.py').read().split('targets={}')[0])
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
for a,z,u in funcs:
 if not 0x3000000<=a<0x3050000:continue
 for i in md.disasm(b[a:z],a):
  if i.mnemonic.startswith(('movss','mulss','comiss','ucomiss')) and any(op.type==capstone.x86.X86_OP_MEM and 0x120<=op.mem.disp<=0x13c and op.mem.base not in [capstone.x86.X86_REG_RSP,capstone.x86.X86_REG_RBP] for op in i.operands):
   print(hex(a),hex(i.address),i.mnemonic,i.op_str)
