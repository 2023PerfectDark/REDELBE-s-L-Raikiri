import re,struct,bisect
from pathlib import Path
b=Path('analysis/lr_updated.bin').read_bytes();nt=struct.unpack_from('<I',b,60)[0];rva,size=struct.unpack_from('<II',b,nt+24+112+24)
funcs=list(struct.iter_unpack('<III',b[rva:rva+size]));starts=[a for a,z,u in funcs]
def owner(p):
 i=bisect.bisect_right(starts,p)-1
 return hex(starts[i]) if i>=0 and p<funcs[i][1] else None
targets={}
for term in ('1.11','Ver.','v%d','%d.%02d','VERSION','version','ver.%s'):
 for enc in ('ascii','utf-16le'):
  needle=term.encode(enc);p=0
  while True:
   p=b.find(needle,p)
   if p<0:break
   if len(targets)<200:targets[p]=(term,enc)
   p+=len(needle)
for lea in re.finditer(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....',b,re.S):
 p=lea.start();target=p+7+struct.unpack_from('<i',b,p+3)[0]
 if target in targets:print(hex(p),owner(p),hex(target),targets[target],repr(b[target:target+65]))
print('1.11 strings',[(hex(a),v) for a,v in targets.items() if v[0]=='1.11'])
