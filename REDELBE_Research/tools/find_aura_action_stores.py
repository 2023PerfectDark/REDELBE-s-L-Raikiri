from pathlib import Path
import sys,struct,re,bisect
sys.path.insert(0,str(Path(__file__).parent/'python_deps'))
import capstone
b=Path('analysis/lr_updated.bin').read_bytes();pe=struct.unpack_from('<I',b,60)[0];r,s=struct.unpack_from('<II',b,pe+24+112+24);fs=list(struct.iter_unpack('<III',b[r:r+s]));starts=[f[0] for f in fs]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);out=[]
for m in re.finditer(b'\x20\x4e\x00\x00',b[:0x4100000]):
 p=m.start();f=fs[bisect.bisect_right(starts,p)-1]
 if not f[0]<=p<f[1] or f[1]-f[0]>0x4000:continue
 ins=list(md.disasm(b[f[0]:f[1]],f[0]))
 for j,i in enumerate(ins):
  if i.address<=p<i.address+i.size and '0x4e20' in i.op_str and i.mnemonic=='mov' and '[' in i.op_str and i.op_str.endswith(', 0x4e20'):
   out.append('\nFUNCTION '+hex(f[0])+' size '+hex(f[1]-f[0]))
   out.extend(f'{x.address:x} {x.mnemonic} {x.op_str}' for x in ins[max(0,j-10):j+12])
Path('analysis/aura_action_code.txt').write_text('\n'.join(out));print('\n'.join(out))

