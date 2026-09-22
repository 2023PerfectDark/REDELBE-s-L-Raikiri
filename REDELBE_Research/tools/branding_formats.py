exec(open('tools/find_branding.py').read().split('targets={}')[0])
import sys
sys.path.insert(0,'tools/python_deps')
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64)
for m in re.finditer(rb'\x4c\x63\xc0\x48\x8d\x94\x24....\x48\x8b\xcb\xe8',b,re.S):
 start=int(owner(m.start()),16)
 print('\n',hex(start))
 for i in md.disasm(b[start:m.start()],start):
  if i.address>start+0x35:print(hex(i.address),i.mnemonic,i.op_str)
