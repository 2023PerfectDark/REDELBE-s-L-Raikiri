"""Read-only capture of the native component-name resolver."""
from pathlib import Path
import sys
source=(Path(__file__).parent/'read_private_lookup_code.py').read_text()
source=source[:source.index(' pe=pefile.PE')]+'''
 cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
 for start,size in ((0x3767200,0x1000),(0x2d51c30,0x140),(0x2a3f830,0x700)):
  buf=C.create_string_buffer(size);got=C.c_size_t()
  assert k.ReadProcessMemory(h,base+start,buf,size,C.byref(got))
  out=Path(__file__).resolve().parents[1]/f'analysis/isolation/resolver_{start:x}.bin'
  raw=buf.raw[:got.value]
  # Keep the original unhooked companion capture used to generate the signature.
  if start==0x3767200 and raw[0xc0:0xc2]==b'\\xff\\x25':
   out=out.with_name(out.stem+'_hooked.bin')
  out.write_bytes(raw)
  offset=16 if start==0x2a3f830 and raw[:2]==b'\\xff\\x25' else 0
  lines=[f'{i.address:x} {i.mnemonic} {i.op_str}' for i in cs.disasm(raw[offset:],start+offset)]
  out.with_suffix('.asm').write_text('\\n'.join(lines))
  print('\\n'.join(lines[:210]))
finally:k.CloseHandle(h)
'''
exec(compile(source,__file__,'exec'))
