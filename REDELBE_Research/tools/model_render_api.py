import re
from pathlib import Path
b=Path('analysis/lr_updated.bin').read_bytes()
for m in re.finditer(rb'[ -~]{6,150}',b[0x4c97000:0x4c97900]):print(hex(m.start()+0x4c97000),m.group().decode())
