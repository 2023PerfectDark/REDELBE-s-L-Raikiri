import sys
exec(open('tools/find_branding.py').read().split('targets={}')[0])
targets={int(s,16) for s in sys.argv[1:]}
for m in re.finditer(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....',b,re.S):
 p=m.start(); t=p+7+struct.unpack_from('<i',b,p+3)[0]
 if t in targets:print(hex(p),owner(p),hex(t))
