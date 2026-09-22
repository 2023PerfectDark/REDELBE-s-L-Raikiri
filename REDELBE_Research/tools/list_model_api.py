from pathlib import Path
import re
b=Path('analysis/lr_updated.bin').read_bytes()
for m in re.finditer(rb'[ -~]{6,150}',b[0x4933300:0x4933b00]):print(hex(m.start()+0x4933300),m.group().decode())
