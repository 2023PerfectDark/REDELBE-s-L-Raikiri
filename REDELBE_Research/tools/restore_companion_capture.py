"""Restore offline unhooked bytes from the previously generated signature."""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
p=root/'analysis/isolation/resolver_3767200.bin'
b=bytearray(p.read_bytes())
header=(root/'experiments/hair_color/native_test/private_companion_pattern.h').read_text()
data=re.search(r'privateCompanion","([^"]+)',header).group(1)
raw=bytes(int(x,16) for x in re.findall(r'\\x([0-9a-f]{2})',data))
assert len(raw)==150 and raw[:5]==bytes.fromhex('48895c2408')
b[0xc0:0x156]=raw
p.write_bytes(b)
print('Restored unhooked resolver capture from original signature bytes')
