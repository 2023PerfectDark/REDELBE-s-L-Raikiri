"""Find literal bytes or relative calls in the saved main-module image."""
import bisect,json,struct,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
b=(root/'analysis/lr_baseline.bin').read_bytes()
nt=struct.unpack_from('<I',b,0x3c)[0];opt=nt+24
rva,size=struct.unpack_from('<II',b,opt+112+24)
funcs=[struct.unpack_from('<III',b,p) for p in range(rva,rva+size,12)];starts=[f[0] for f in funcs]
def owner(p):
    i=bisect.bisect_right(starts,p)-1
    return hex(funcs[i][0]) if i>=0 and funcs[i][0]<=p<funcs[i][1] else None
for term in sys.argv[1:]:
    needle=bytes.fromhex(term);p=0;found=[]
    while True:
        p=b.find(needle,p)
        if p<0:break
        found.append({'rva':hex(p),'function':owner(p)});p+=1
    print(json.dumps({'bytes':term,'matches':found}))
