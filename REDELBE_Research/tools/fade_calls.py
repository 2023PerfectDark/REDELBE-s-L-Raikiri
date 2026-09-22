exec(open('tools/find_branding.py').read().split('targets={}')[0])
for m in re.finditer(b'\xe8....',b[:0x4200000],re.S):
 p=m.start()
 if p+5+struct.unpack_from('<i',b,p+1)[0]==0x2d579f0:print(hex(p),owner(p))
