"""Validate hook bytes and instruction boundaries against the saved LR image."""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/python_deps'))
import capstone

image=(ROOT/'analysis/lr_baseline.bin').read_bytes()
source=(ROOT/'prototype/layer2_runtime.h').read_text()
decoder=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
decoder.detail=True
report=[]
for address,pattern in re.findall(r'\{base\+0x([0-9a-f]+),bytes\("([0-9a-f ]+)"\)',source):
    address=int(address,16);expected=bytes.fromhex(pattern)
    assert image[address:address+len(expected)]==expected,f'Bytes differ at {address:x}'
    instructions=list(decoder.disasm(expected,address))
    assert len(expected)>=14 and sum(i.size for i in instructions)==len(expected),'Partial instruction'
    for instruction in instructions:
        assert not instruction.group(capstone.CS_GRP_JUMP) and not instruction.group(capstone.CS_GRP_CALL),'Relative control flow'
        for operand in instruction.operands:
            assert not (operand.type==capstone.x86.X86_OP_MEM and operand.mem.base==capstone.x86.X86_REG_RIP),'RIP-relative operand'
    report.append(dict(rva=hex(address),length=len(expected),instructions=len(instructions)))
assert len(report)==8
release=bytes.fromhex('40 57 48 83 ec 50 48 c7 44 24 28 fe ff ff ff')
assert image[0x22dbff0:0x22dbff0+len(release)]==release,'Native release signature differs'
result={'verified_prologues':report,'result':'PASS'}
(ROOT/'evidence/layer2_reload_hook_validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
