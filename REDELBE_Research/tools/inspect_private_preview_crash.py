"""Bounded register/instruction and candidate return-address report from a dump."""
import sys,struct,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'python_deps'))
import capstone,pefile
from lr_resources import GAME
from inspect_tina_dump import d,streams,u,mem,base,ctx,e
rip=u('Q',ctx+248)[0];rsp=u('Q',ctx+152)[0]
registers={name:hex(u('Q',ctx+off)[0]) for name,off in [('rax',120),('rcx',128),('rdx',136),('rbx',144),('rsp',152),('rbp',160),('rsi',168),('rdi',176),('r8',184),('r9',192),('r10',200),('r11',208),('r12',216),('r13',224),('r14',232),('r15',240)]}
pe=pefile.PE(str(GAME/'DOA6LR.exe'),fast_load=True)
code=mem(rip,64);cs=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
instructions=[f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in cs.disasm(code,rip-base)]
stack=mem(rsp,512);candidates=[hex(v-base) for v, in struct.iter_unpack('<Q',stack[:len(stack)//8*8]) if base<=v<base+pe.OPTIONAL_HEADER.SizeOfImage]
result={'rip_rva':hex(rip-base),'registers':registers,'instructions':instructions,'candidate_stack_rvas':candidates}
pe.parse_data_directories(directories=[3])
for caller in (0x22cf216,0x22cb4fc):
 fn=next((f.struct for f in pe.DIRECTORY_ENTRY_EXCEPTION if f.struct.BeginAddress<=caller<f.struct.EndAddress),None)
 if fn:
  decoded=list(cs.disasm(mem(base+fn.BeginAddress,min(fn.EndAddress-fn.BeginAddress,16384)),fn.BeginAddress))
  relevant=[i for i in decoded if caller-130<=i.address<=caller+20]
  result[hex(caller)]=[f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in relevant]
(Path(__file__).resolve().parents[1]/'analysis/isolation/private_preview_crash.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
