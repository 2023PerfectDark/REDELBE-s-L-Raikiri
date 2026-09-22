"""Offline search for the native battle costume/face/hair getter sites."""
from pathlib import Path
import sys,struct,bisect
sys.path.insert(0,str(Path(__file__).parent/'python_deps'))
import capstone
root=Path(__file__).resolve().parents[1]
b=(root/'analysis/lr_updated.bin').read_bytes()
p=struct.unpack_from('<I',b,60)[0]
pr,ps=struct.unpack_from('<II',b,p+24+112+24)
funcs=[(a,z) for a,z,u in struct.iter_unpack('<III',b[pr:pr+ps])]
starts=[a for a,z in funcs]
c=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
lines=[];pos=0
while True:
 pos=b.find(bytes.fromhex('4d580858'),pos)
 if pos<0:break
 ix=bisect.bisect_right(starts,pos)-1
 a,z=funcs[ix]
 if a<=pos<z:
  lines.append(f'FUNCTION {a:x}-{z:x}, KEY {pos:x}')
  lines.extend(f'{i.address:x} {i.mnemonic} {i.op_str}' for i in c.disasm(b[a:z],a) if pos-45<=i.address<pos+65)
 pos+=1
(root/'analysis/isolation/battle_slot_readers.asm').write_text('\n'.join(lines))
print('\n'.join(lines))
