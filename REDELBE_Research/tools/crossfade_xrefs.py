"""Read-only call/vtable references in the saved LR 1.11 image."""
import sys,json
exec(open('tools/find_branding.py').read().split('targets={}')[0])
base=json.loads(Path('analysis/lr_updated.json').read_text())['modules'][0]['base']
targets={int(s,16) for s in sys.argv[1:]}
for m in re.finditer(rb'[\xe8\xe9]....', b, re.S):
 p=m.start(); t=p+5+struct.unpack_from('<i',b,p+1)[0]
 if t in targets: print('branch',hex(t),hex(p),owner(p))
for t in sorted(targets):
 needle=struct.pack('<Q',base+t); pos=0
 while True:
  pos=b.find(needle,pos)
  if pos<0:break
  print('pointer',hex(t),hex(pos));pos+=8
