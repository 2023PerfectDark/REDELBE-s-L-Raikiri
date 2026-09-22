import struct,json
from pathlib import Path
b=Path('analysis/lr_updated.bin').read_bytes();base=json.loads(Path('analysis/lr_updated.json').read_text())['modules'][0]['base']
for addr in [0x4cac3d0]:
 for o in range(0,0x70,8):print(hex(addr+o),hex(struct.unpack_from('<Q',b,addr+o)[0]-base))
