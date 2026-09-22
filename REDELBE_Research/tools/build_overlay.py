"""Prepare isolated RDB/.file replacements for hash-named, LR-native assets.

Does not modify the game. Does not convert old assets or implement Layer2 slots.
"""
import argparse, hashlib, json, re, struct
from pathlib import Path
from lr_resources import GAME, read_index, extract

def build(game, mods, output):
    files=sorted(p for p in mods.rglob('*') if p.is_file() and re.fullmatch(r'0x[0-9a-fA-F]{8}\.[a-zA-Z0-9]+',p.name))
    if not files: raise ValueError('No hash-named assets found')
    if output.exists() and any(output.iterdir()): raise ValueError('Output must be empty to avoid mixing packages')
    indexes={}
    for name in ('root','system'):
        path=game/'fdata_package'/f'{name}.rdb'; raw,entries,_=read_index(path)
        indexes[name]=(raw,entries,path)
    assets=[]; seen=set()
    for path in files:
        fid=int(path.stem,16)
        if fid in seen: raise ValueError(f'Duplicate resource {fid:08x}')
        seen.add(fid)
        matches=[(name,raw,e,ip) for name,(raw,es,ip) in indexes.items() for e in es if e['id']==fid]
        if len(matches)!=1: raise ValueError(f'{path.name}: expected unique existing resource; found {len(matches)}')
        name,raw,e,ip=matches[0]
        if e['c_size']!=13 or e.get('ext_flags') not in (0x401,0xc01): raise ValueError(f'{path.name}: unsupported entry encoding')
        payload=path.read_bytes()
        if len(payload)>0xffffffff: raise ValueError('Payload exceeds supported 32-bit size')
        # Check asset family against the existing payload; prevents wrapping a DDS
        # or an IDRK .file as if it were an unpacked G1T/G1M.
        original=extract(ip,e)
        if len(payload)<8 or payload[:4]!=original[:4]: raise ValueError(f'{path.name}: payload family differs from installed resource')
        if payload[:4]==b'IDRK': raise ValueError('Use unpacked assets, not IDRK containers')
        assets.append((name,raw,e,path,payload))
    output.mkdir(parents=True,exist_ok=True)
    (output/'overlay/data').mkdir(parents=True,exist_ok=True)
    patched={}; manifest=[]; redirects=[]
    for name,raw,e,path,payload in assets:
        data=patched.setdefault(name,bytearray(raw)); pos=e['rdb_offset']; prefix_size=e['entry_size']-e['c_size']
        header=bytearray(raw[pos:pos+prefix_size])
        struct.pack_into('<Q',header,8,len(header)+len(payload))
        struct.pack_into('<I',header,16,len(payload))
        struct.pack_into('<Q',header,24,len(payload))
        struct.pack_into('<I',header,44,0)
        container=bytes(header)+payload
        rel=f"overlay/data/0x{e['id']:08x}.file"
        (output/rel).write_bytes(container)
        struct.pack_into('<Q',data,pos+24,len(payload))
        struct.pack_into('<I',data,pos+44,0x20000)
        ext=pos+e['entry_size']-13
        struct.pack_into('<H',data,ext,0xc01)
        struct.pack_into('<I',data,ext+6,len(container))
        redirects.append(f"fdata_package/data/0x{e['id']:08x}.file\t{rel}")
        manifest.append(dict(id=hex(e['id']),index=name,source=str(path.resolve()),payload_sha256=hashlib.sha256(payload).hexdigest(),original_payload_sha256=hashlib.sha256(extract(indexes[name][2],e)).hexdigest(),container=rel))
    for name,data in patched.items():
        (output/f'overlay/{name}.rdb').write_bytes(data)
        redirects.insert(0,f'fdata_package/{name}.rdb\toverlay/{name}.rdb')
    (output/'redirects.tsv').write_text('\n'.join(redirects)+'\n',encoding='utf-8')
    baselines=[]
    for name in patched:
        for ext in ('rdb','rdx'):
            rel=f'fdata_package/{name}.{ext}'
            baselines.append(rel+'\t'+hashlib.sha256((game/rel).read_bytes()).hexdigest())
    (output/'baselines.tsv').write_text('\n'.join(baselines)+'\n',encoding='utf-8')
    result=dict(status='Prepared; game validation required',game=str(game),base_indexes={name:hashlib.sha256(indexes[name][0]).hexdigest() for name in patched},assets=manifest)
    (output/'manifest.json').write_text(json.dumps(result,indent=2))
    # Round-trip using unchanged RDX tables copied only into the workspace.
    for name in patched:
        (output/f'overlay/{name}.rdx').write_bytes((game/f'fdata_package/{name}.rdx').read_bytes())
        _,entries,_=read_index(output/f'overlay/{name}.rdb')
        for a in manifest:
            if a['index']==name:
                entry=next(e for e in entries if e['id']==int(a['id'],16))
                if hashlib.sha256(extract(output/f'overlay/{name}.rdb',entry)).hexdigest()!=a['payload_sha256']: raise AssertionError('Generated payload failed round trip')
    print(json.dumps(dict(assets=len(manifest),indexes=list(patched),output=str(output),round_trip='passed')))
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('mods',type=Path); ap.add_argument('output',type=Path); ap.add_argument('--game',type=Path,default=GAME); a=ap.parse_args(); build(a.game,a.mods,a.output)
