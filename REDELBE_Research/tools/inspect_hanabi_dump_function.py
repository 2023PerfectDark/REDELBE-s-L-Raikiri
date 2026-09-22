"""Inspect a bounded function and readable registers at a crash site."""
import sys,struct,bisect
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'python_deps'))
import capstone
from inspect_tina_dump import mem,base,ctx,u
root=Path(__file__).resolve().parents[1]
b=(root/'analysis/lr_updated.bin').read_bytes();p=struct.unpack_from('<I',b,60)[0]
pr,ps=struct.unpack_from('<II',b,p+160)
fs=[(a,z) for a,z,_ in struct.iter_unpack('<III',b[pr:pr+ps])];starts=[a for a,z in fs]
target=int(sys.argv[2],16);a,z=fs[bisect.bisect_right(starts,target)-1]
assert a<=target<z
code=mem(base+a,z-a);source='dump'
if len(code)!=z-a:code=b[a:z];source='saved baseline'
c=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
lines=[f'FUNCTION {a:x}-{z:x} ({source})']
lines.extend(f'{i.address:x} {i.mnemonic} {i.op_str}' for i in c.disasm(code,a))
(root/f'analysis/isolation/crash_function_{target:x}.asm').write_text('\n'.join(lines))
print('\n'.join(lines))
