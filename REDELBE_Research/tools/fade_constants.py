from pathlib import Path
import struct
b=Path('analysis/lr_updated.bin').read_bytes()
for p in [0x22cfbd9,0x22cfbf1]:
 addr=p+8+struct.unpack_from('<i',b,p+4)[0]
 print(hex(addr),struct.unpack_from('<f',b,addr)[0])
