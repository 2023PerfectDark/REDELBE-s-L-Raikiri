from pathlib import Path
import sys,struct,re
sys.path.insert(0,str(Path(__file__).parent/'python_deps'))
import capstone
root=Path(__file__).resolve().parents[1];data=(root/'analysis/lr_baseline.bin').read_bytes()
nt=struct.unpack_from('<I',data,0x3c)[0];rva,size=struct.unpack_from('<II',data,nt+24+112+24)
functions=dict((a,b) for a,b,_ in struct.iter_unpack('<III',data[rva:rva+size]))
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
for p,end in functions.items():
    if end-p<0x80 or end-p>0x700:continue
    if b'\xfe\xff\xff\xff' not in data[p:p+0x50]:continue
    instructions=list(md.disasm(data[p:p+0x80],p))
    firstcall=next((i for i,v in enumerate(instructions) if v.mnemonic=='call'),len(instructions))
    incoming=instructions[:firstcall]
    if not any(i.op_str.endswith(', r9') for i in incoming):continue
    if not any('r8b' in i.op_str for i in incoming):continue
    if not any(i.op_str.endswith(', rdx') for i in incoming):continue
    if any(i.op_str.endswith(' + 0x19], 0') for i in instructions):continue
    print(hex(p),hex(end-p),' | '.join(f'{i.mnemonic} {i.op_str}' for i in instructions[:25]))
