import struct,re,sys,bisect
from pathlib import Path
d=Path(sys.argv[1]).read_bytes()
def u(fmt,o):return struct.unpack_from('<'+fmt,d,o)
count,table=u('II',8);streams={}
for i in range(count):
    kind,size,rva=u('III',table+i*12);streams[kind]=(size,rva)
e=streams[6][1];tid=u('I',e)[0];ctxsize,ctx=u('II',e+160)
rsp=u('Q',ctx+152)[0];rip=u('Q',ctx+248)[0]
print('Exception thread',tid,'RSP',hex(rsp),'RIP',hex(rip))
m=streams[4][1];modules=[]
for i in range(u('I',m)[0]):
    o=m+4+i*108;base,size=u('QI',o);nrva=u('I',o+20)[0];n=u('I',nrva)[0]
    name=d[nrva+4:nrva+4+n].decode('utf-16-le');modules.append((base,size,Path(name).name))
symbols=[]
for line in Path('prototype/build/REDELBE_LR.map').read_text().splitlines():
    match=re.search(r'\s[0-9a-f]{4}:[0-9a-f]{8}\s+(\S+)\s+([0-9a-f]{16}) f ',line)
    if match:symbols.append((int(match[2],16)-0x180000000,match[1]))
symbols.sort();addresses=[a for a,n in symbols]
def desc(v):
    for base,size,name in modules:
        if base<=v<base+size:
            rva=v-base;label=name+'+'+hex(rva)
            if name=='REDELBE_LR.asi':
                ix=bisect.bisect_right(addresses,rva)-1
                if ix>=0:label+=' '+symbols[ix][1]+'+'+hex(rva-symbols[ix][0])
            return label
print(desc(rip))
t=streams[3][1]
for i in range(u('I',t)[0]):
    o=t+4+i*48
    if u('I',o)[0]!=tid:continue
    start,size,rva=u('QII',o+24)
    print('Stack',hex(start),size)
    for offset in range(max(0,rsp-start),size-7,8):
        value=u('Q',rva+offset)[0];label=desc(value)
        if label:print(hex(start+offset),label)
