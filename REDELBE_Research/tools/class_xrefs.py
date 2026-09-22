"""Offline MSVC x64 RTTI constructor/vtable discovery, no process changes."""
from pathlib import Path
import struct,re,json,sys,bisect
root=Path(__file__).resolve().parents[1]
data=(root/'analysis/lr_baseline.bin').read_bytes()
info=json.loads((root/'analysis/lr_baseline.json').read_text())
base=info['modules'][0]['base']
nt=struct.unpack_from('<I',data,0x3c)[0];opt=nt+24
rva,size=struct.unpack_from('<II',data,opt+112+24)
funcs=[struct.unpack_from('<III',data,p) for p in range(rva,rva+size,12)]
starts=[f[0] for f in funcs]
def owner(p):
    i=bisect.bisect_right(starts,p)-1
    return hex(funcs[i][0]) if i>=0 and p<funcs[i][1] else None
def offsets(needle):
    p=0
    while True:
        p=data.find(needle,p)
        if p<0:return
        yield p;p+=1
for match in re.finditer(rb'\.\?A[VU][^\0]{1,300}\0',data):
    if sys.argv[1].encode() not in match[0]:continue
    td=match.start()-16
    print('Type',hex(td),match[0])
    for ref in offsets(struct.pack('<I',td)):
        col=ref-12
        if col<0 or struct.unpack_from('<I',data,col)[0]!=1:continue
        if struct.unpack_from('<I',data,col+20)[0]!=col:continue
        print('COL',hex(col))
        # A snapshot contains relocated pointers; its own RTTI self field lets us
        # infer the base by checking candidate pointers ending at the COL offset.
        for pointer in offsets(struct.pack('<Q',base+col)):
            vtable=pointer+8
            print('Vtable',hex(vtable))
            for lea in re.finditer(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....',data,re.S):
                p=lea.start()
                if p+7+struct.unpack_from('<i',data,p+3)[0]==vtable:
                    print('reference',hex(p),'function',owner(p))
