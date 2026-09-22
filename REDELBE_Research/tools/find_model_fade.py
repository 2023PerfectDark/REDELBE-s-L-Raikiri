import re
from pathlib import Path
b=Path('analysis/lr_updated.bin').read_bytes()
for m in re.finditer(rb'[ -~]{6,150}',b):
 s=m.group().decode()
 if ('model::' in s and any(w in s for w in ('fade','alpha','visible','request','completed'))) or ('fade' in s.lower() and 'character' in s.lower()):print(hex(m.start()),s)
