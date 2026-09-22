import sys,json
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'python_deps'))
import capstone
b=Path(__file__).resolve().parents[1];data=(b/'analysis/lr_baseline.bin').read_bytes()
imports=json.loads((b/'analysis/binary_details.json').read_text())['target']['imports']
imap={int(i['rva'],16):dll+'!'+i['name'] for dll,items in imports.items() for i in items}
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
for arg in sys.argv[1:]:
    start,size=(int(x,16) for x in arg.split(':'));print(f'RVA {start:x}')
    for i in md.disasm(data[start:start+size],start):
        extra=[]
        for op in i.operands:
            if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
                addr=i.address+i.size+op.mem.disp
                if addr in imap:extra.append(imap[addr])
                elif 0<=addr<len(data):
                    raw=data[addr:addr+120]
                    if i.mnemonic=='lea':
                        extra.append(repr(raw.split(b'\0')[0]));extra.append(repr(raw.decode('utf-16le','replace').split('\0')[0]))
        print(f'{i.address:08x} {i.bytes.hex():32} {i.mnemonic:8} {i.op_str} {" | ".join(extra)}')
