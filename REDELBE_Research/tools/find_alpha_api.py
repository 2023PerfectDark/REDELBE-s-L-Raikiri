import re
from pathlib import Path
b=Path('analysis/lr_updated.bin').read_bytes()
for m in re.finditer(rb'[ -~]{5,150}',b[0x4200000:0x4d40000]):
 s=m.group().decode()
 if any(w in s.lower() for w in ('fade','opacity','alpha')) and not any(w in s.lower() for w in ('caustic','wetcharacter')):print(hex(m.start()+0x4200000),s)
