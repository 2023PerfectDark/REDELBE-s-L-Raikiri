exec(open('tools/find_branding.py').read().split('targets={}')[0])
for pat in [rb'\x41\xb8\x00\x08\x00\x00',rb'\x48\xc7\x43\x18\x07\x00\x00\x00']:
 print('PATTERN')
 for m in re.finditer(pat,b):print(hex(m.start()),owner(m.start()))
for m in re.finditer(rb'[ -~]{4,100}',b):
 s=m.group()
 if (b'%' in s and (b'ver' in s.lower() or b'.' in s)) or b'txt_version' in s.lower():print(hex(m.start()),s)
