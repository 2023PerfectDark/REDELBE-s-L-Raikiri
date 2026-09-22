exec(open('tools/find_branding.py').read().split('targets={}')[0])
for m in re.finditer(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....',b,re.S):
 p=m.start();t=p+7+struct.unpack_from('<i',b,p+3)[0]
 if t==0x4c970a0: print(hex(p),owner(p))
