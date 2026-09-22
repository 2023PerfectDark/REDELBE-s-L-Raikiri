exec(open('tools/find_branding.py').read().split('targets={}')[0])
for m in re.finditer(rb'\x48\x8d\x05....\x48\x89\x44\x24\x20',b,re.S):
 p=m.start()
 if b'\x4c\x63\xc0' in b[p:p+160]: print(hex(p),owner(p),b[p:p+140].hex())
