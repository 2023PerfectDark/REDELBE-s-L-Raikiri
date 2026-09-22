from pathlib import Path
import re
b=Path('analysis/lr_updated.bin').read_bytes()
for m in re.finditer(rb'[ -~]{6,180}',b):
 s=m.group()
 if any(x in s.lower() for x in (b'version',b'title')) and m.start()<0x8700000:print(hex(m.start()),s)
