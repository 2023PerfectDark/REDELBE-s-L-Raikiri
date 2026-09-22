"""Verify the experimental recolorer against all three mips of a real LR texture."""
from pathlib import Path
import struct, json
root=Path(__file__).parent
original=(root/'8346fa03.g1t').read_bytes()
decoded=(root/'kok_decoded.g1t').read_bytes()
colored=(root/'kok_blonde.g1t').read_bytes()
assert len(decoded)==len(colored)==22020152
assert decoded[:56]==colored[:56]
assert decoded[56+3::4]==colored[56+3::4], 'Alpha changed'
assert decoded[56:]!=colored[56:]
assert original[:8]==colored[:8]
assert original[12:37]==colored[12:37]
assert original[38:56]==colored[38:56]
assert colored[37]==9
assert struct.unpack_from('<I',colored,8)[0]==len(colored)
print(json.dumps(dict(mips=3,width=2048,height=2048,alpha_pixels_verified=len(colored[59::4]),size=len(colored),status='passed')))
