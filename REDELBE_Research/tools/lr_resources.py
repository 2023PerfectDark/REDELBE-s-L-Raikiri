"""Strict read-only DOA6LR RDB/RDX reader. Generated files stay in the workspace.

Field interpretation cross-checked against eterniti/eternity_common RdbFile.h.
"""
from pathlib import Path
import argparse, collections, hashlib, json, struct, zlib

GAME=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round')
def u32(b,p): return struct.unpack_from('<I',b,p)[0]
def u64(b,p): return struct.unpack_from('<Q',b,p)[0]

def read_index(path):
    data=path.read_bytes()
    if data[:8]!=b'_DRK0000' or len(data)<32: raise ValueError('Bad RDB header')
    rdx=path.with_suffix('.rdx').read_bytes()
    if len(rdx)%8: raise ValueError('Bad RDX length')
    packages={a:c for a,b,c in struct.iter_unpack('<HHI',rdx)}
    entries=[]; pos=u32(data,8)
    while pos<len(data):
        pos=(pos+3)&~3
        if pos==len(data): break
        if data[pos:pos+8]!=b'IDRK0000': raise ValueError(f'Bad entry at {pos:x}')
        size=u64(data,pos+8); csize=u32(data,pos+16)
        if size<48 or pos+size>len(data) or csize>size-48: raise ValueError('Bad entry bounds')
        e=dict(rdb_offset=pos,entry_size=size,c_size=csize,file_size=u64(data,pos+24),type=u32(data,pos+32),id=u32(data,pos+36),type_id=u32(data,pos+40),flags=u32(data,pos+44))
        if csize in (13,17):
            ep=pos+size-csize; flags=struct.unpack_from('<H',data,ep)[0]
            if csize==13: off,full,pkg=struct.unpack_from('<IIH',data,ep+2)
            else:
                off,full,pkg=struct.unpack_from('<IIH',data,ep+6); off+=data[ep+2]<<32
            e.update(ext_flags=flags,offset=off,full_size=full,package_id=pkg,package_hash=packages.get(pkg))
        entries.append(e); pos+=size
    if len(entries)!=u32(data,16): raise ValueError('Entry count mismatch')
    return data,entries,u32(data,20)

def container_for(path,e):
    if e.get('ext_flags')==0xc01:
        return path.parent/'data'/f"0x{e['id']:08x}.file",0
    # 0x1401 records use the same index layout but may refer to omitted debug
    # containers. Keep this distinct from claiming their payloads are available.
    if e.get('ext_flags') not in (0x401,0x1401) or e.get('package_hash') is None: raise ValueError('Not an addressable entry')
    name=f"0x{e['package_hash']:08x}.fdata"
    direct=path.parent/name
    if direct.exists(): return direct,e['offset']
    found=list(path.parent.rglob(name))
    if len(found)!=1: raise FileNotFoundError(f'Expected one {name}, got {len(found)}')
    return found[0],e['offset']

def extract(path,e):
    container,offset=container_for(path,e)
    with container.open('rb') as f:
        f.seek(offset); header=f.read(48)
        if header[:8]!=b'IDRK0000': raise ValueError('Bad container IDRK')
        size=u64(header,8); csize=u32(header,16); usize=u64(header,24)
        if size<48+csize or usize>512*1024*1024: raise ValueError('Invalid payload size')
        if u32(header,36)!=e['id']: raise ValueError('Container resource ID mismatch')
        f.seek(offset+size-csize); payload=f.read(csize)
        if len(payload)!=csize: raise ValueError('Truncated payload')
    # Compressed chunks can coincidentally occupy exactly the decoded size.
    # The container compression flag remains authoritative in that case.
    if csize==usize and not (u32(header,44)&0x400000): return payload
    out=bytearray(); p=0
    while p<len(payload) and len(out)<usize:
        if p+10>len(payload): raise ValueError('Truncated chunk header')
        n=struct.unpack_from('<H',payload,p)[0]; p+=10
        if p+n>len(payload): raise ValueError('Truncated chunk')
        chunk=zlib.decompress(payload[p:p+n]); p+=n; out.extend(chunk)
    if len(out)!=usize: raise ValueError(f'Decompressed size mismatch {len(out)} != {usize}')
    return bytes(out)

def names_from_rnk(data):
    if data[:8]!=b'_RNK0000': raise ValueError('Bad RNK')
    names={}; pos=u32(data,8)
    while True:
        pos=data.find(b'IRNK0000',pos)
        if pos<0: break
        size,fid,count=struct.unpack_from('<III',data,pos+8)
        if size<20 or pos+size>len(data) or 20+count*4>size: raise ValueError('Bad RNK entry')
        strings=[]
        for j in range(count):
            q=pos+u32(data,pos+20+4*j)
            if not pos<=q<pos+size: raise ValueError('Bad RNK string offset')
            end=data.index(0,q,pos+size); strings.append(data[q:end].decode('utf-8'))
        names[fid]=strings; pos+=size
    return names

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--game',type=Path,default=GAME); ap.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'analysis/resources'); a=ap.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    summary={}
    for path in sorted((a.game/'fdata_package').glob('*.rdb')):
        data,entries,name_id=read_index(path); counts=collections.Counter(hex(e.get('ext_flags',0)) for e in entries)
        name_entries=[e for e in entries if e['id']==name_id]
        names={}; error=None
        try:
            if len(name_entries)!=1: raise ValueError('Name DB not unique')
            rnk=extract(path,name_entries[0]); names=names_from_rnk(rnk)
        except Exception as ex: error=str(ex)
        for e in entries:
            if e['id'] in names: e['names']=names[e['id']]
        out=dict(source=str(path),sha256=hashlib.sha256(data).hexdigest(),name_db_id=hex(name_id),entries=entries)
        (a.output/(path.stem+'.json')).write_text(json.dumps(out,indent=2),encoding='utf-8')
        summary[path.name]=dict(entries=len(entries),extended_flags=counts,names=len(names),name_error=error)
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))
if __name__=='__main__': main()
