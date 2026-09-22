import sys,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'python_deps'))
import capstone
b=Path('analysis/lr_baseline.bin').read_bytes()
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
instructions=list(md.disasm(b[0x22c4000:0x22e9000],0x22c4000))
# skipdata allows alignment bytes between native functions.
md.skipdata=True
instructions=list(md.disasm(b[0x22c4000:0x22e9000],0x22c4000))
for i in instructions:
 if i.mnemonic=='call' and i.op_str=='0x22ca6e0':print('INITIALIZER CALL',hex(i.address))
for start,size in [(0x22cbe80,0x110),(0x22cbfd0,0x100)]:
 for x in md.disasm(b[start:start+size],start):print(hex(x.address),x.mnemonic,x.op_str)
