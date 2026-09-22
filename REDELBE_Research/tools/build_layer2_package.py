"""Prepare native LR Layer2 assets with vanilla fallback; never modifies the game.

Catalog metadata is read on startup. Payload files stay on disk until requested.
Usage: build_layer2_package.py OUTPUT --mod AYA_COS_001 NAME ASSET_DIRECTORY
Repeat --mod for additional native, hash-named costume mods.
"""
import argparse, hashlib, json, re, shutil, struct
from pathlib import Path
from lr_resources import GAME, read_index, extract

def slot_hash(text):
    result=0;power=31
    for c in text:
        result=(result+ord(c)*power)&0xffffffff
        power=(power*31)&0xffffffff
    return result

def validate_payload(payload,original,entry,extension):
    if len(payload)<8 or payload[:4]==b'IDRK':raise ValueError('Expected an unpacked LR asset')
    ext=extension.lower()
    if ext in ('.oid','.oidex','.mtl'):
        # These are binary tables, not files with a fixed four-byte magic.
        # IDs cross-checked against Kashira.Core/Formats/AssetTypes.cs.
        expected={'.oid':0x1ab40ae8,'.oidex':0xe6a3c3bb,'.mtl':0xb340861a}[ext]
        if entry['type_id']!=expected:raise ValueError('Binary table extension does not match the registered LR resource type')
        if len(payload)%4:raise ValueError('Binary table must be aligned to 32-bit fields')
        if ext=='.mtl':
            if len(payload)<16:raise ValueError('Truncated material table header')
            names,materials,cloths,ponytails=struct.unpack_from('<IIII',payload)
            offset=16
            if names>(len(payload)-16)//8:raise ValueError('Material table name count exceeds bounds')
            for _ in range(names):
                if offset+8>len(payload):raise ValueError('Truncated material name record')
                _,count=struct.unpack_from('<II',payload,offset);offset+=8
                if count>(len(payload)-offset)//4:raise ValueError('Material index count exceeds bounds')
                offset+=count*4
            if offset+8*(cloths+ponytails)!=len(payload):raise ValueError('Material attachment table size mismatch')
        return
    if payload[:4]!=original[:4]:raise ValueError('Asset signature differs from the original LR resource')

def wrap(raw,entry,payload):
    pos=entry['rdb_offset']; prefix=entry['entry_size']-entry['c_size']
    header=bytearray(raw[pos:pos+prefix])
    struct.pack_into('<Q',header,8,prefix+len(payload))
    struct.pack_into('<I',header,16,len(payload))
    struct.pack_into('<Q',header,24,len(payload))
    struct.pack_into('<I',header,44,0)
    return bytes(header)+payload

def build(game,output,definitions,restoration=None):
    if output.exists() and any(output.iterdir()):raise ValueError('Output must be empty')
    index={};resources={}
    for name in ('root','system'):
        path=game/'fdata_package'/f'{name}.rdb';raw,entries,_=read_index(path)
        index[name]=(path,raw)
        for e in entries:resources.setdefault(e['id'],[]).append((name,e))
    restored={}
    if restoration:
        from legacy_restoration import merge
        restored=merge(index,resources,restoration)
    output.mkdir(parents=True,exist_ok=True)
    patched={};vanilla={};catalog=[];manifest=[]
    dependencies=[]
    for fid,original in restored.items():
        idx,e=resources[fid][0];_,raw=index[idx]
        target0=output/'vanilla/data'/f'0x{fid:08x}.file';target0.parent.mkdir(parents=True,exist_ok=True)
        baseline=wrap(raw,e,original);target0.write_bytes(baseline)
        vanilla[fid]=f'fdata_package/data/0x{fid:08x}.file\t'+target0.relative_to(output).as_posix()
        shadow=patched.setdefault(idx,bytearray(raw));pos=e['rdb_offset'];ext=pos+e['entry_size']-13
        struct.pack_into('<I',shadow,pos+44,0x20000);struct.pack_into('<H',shadow,ext,0xc01)
        struct.pack_into('<I',shadow,ext+6,len(baseline))
        dependencies.append({'id':hex(fid),'sha256':hashlib.sha256(original).hexdigest()})
    for number,(slot,name,directory) in enumerate(definitions,1):
        if not re.fullmatch(r'[A-Z0-9_]+',slot) or any(c in name for c in '\t\r\n'):raise ValueError('Invalid mod metadata')
        modpath=output/'Layer2'/f'{number:04d}_{slot}'
        (modpath/'data').mkdir(parents=True)
        files=sorted(p for p in Path(directory).rglob('*') if p.is_file() and re.fullmatch(r'0x[0-9a-fA-F]{8}\.[a-zA-Z0-9]+',p.name))
        if not files:raise ValueError(f'No hash-named assets in {directory}')
        redirects=[];seen=set()
        for file in files:
            fid=int(file.stem,16)
            if fid in seen:raise ValueError(f'Duplicate resource {fid:08x} in mod')
            seen.add(fid)
            entries=resources.get(fid,[])
            if len(entries)!=1:raise ValueError(f'Unknown/ambiguous resource {fid:08x}')
            idx,e=entries[0];path,raw=index[idx]
            if e['c_size']!=13 or e.get('ext_flags') not in (0x401,0xc01):raise ValueError('Unsupported RDB encoding')
            original=restored[fid] if fid in restored else extract(path,e);payload=file.read_bytes()
            try:validate_payload(payload,original,e,file.suffix)
            except ValueError as exc:raise ValueError(f'{name}: {file.name}: {exc}') from exc
            container=wrap(raw,e,payload)
            target=modpath/'data'/f'0x{fid:08x}.file';target.write_bytes(container)
            source=f'fdata_package/data/0x{fid:08x}.file'
            redirects.append(source+'\t'+target.relative_to(output).as_posix())
            if fid not in vanilla:
                target0=output/'vanilla/data'/f'0x{fid:08x}.file';target0.parent.mkdir(parents=True,exist_ok=True)
                baseline=wrap(raw,e,original);target0.write_bytes(baseline)
                vanilla[fid]=source+'\t'+target0.relative_to(output).as_posix()
                shadow=patched.setdefault(idx,bytearray(raw));pos=e['rdb_offset']
                struct.pack_into('<I',shadow,pos+44,0x20000)
                ext=pos+e['entry_size']-13
                struct.pack_into('<H',shadow,ext,0xc01)
                struct.pack_into('<I',shadow,ext+6,len(baseline))
            # Check each serialized payload without loading it in the game.
            assert container[len(container)-len(payload):]==payload
            manifest.append(dict(mod=number,id=hex(fid),slot=slot,payload_sha256=hashlib.sha256(payload).hexdigest(),vanilla_sha256=hashlib.sha256(original).hexdigest()))
        table=modpath/'redirects.tsv';table.write_text('\n'.join(redirects)+'\n',encoding='utf-8')
        kind,section=('rrpreview','RRPreview') if slot=='RRPREVIEW' else ('costume','Costume')
        (modpath/'mod.ini').write_text(f'[General]\ntype={kind}\nname={name}\n\n[{section}]\nslot={slot}\n',encoding='utf-8')
        catalog.append(f'{slot_hash(slot):08x}\t{name}\t{table.relative_to(output).as_posix()}')
    fixed=[];checks=[]
    (output/'overlay').mkdir()
    for name,raw in patched.items():
        (output/f'overlay/{name}.rdb').write_bytes(raw)
        fixed.append(f'fdata_package/{name}.rdb\toverlay/{name}.rdb')
        for ext in ('rdb','rdx'):
            rel=f'fdata_package/{name}.{ext}';checks.append(rel+'\t'+hashlib.sha256((game/rel).read_bytes()).hexdigest())
    for filename,lines in [('redirects.tsv',fixed),('baselines.tsv',checks),('vanilla.tsv',list(vanilla.values())),('layer2.tsv',catalog)]:
        (output/filename).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (output/'manifest.json').write_text(json.dumps({'format':'LR Layer2 native-ID 0.2','default':'vanilla','mods':len(definitions),'assets':manifest,'dependencies':dependencies},indent=2))
    print(json.dumps({'mods':len(definitions),'unique_resources':len(vanilla),'slot_hashes':{d[0]:hex(slot_hash(d[0])) for d in definitions},'output':str(output)}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);ap.add_argument('--game',type=Path,default=GAME)
    ap.add_argument('--mod',nargs=3,action='append',required=True,metavar=('SLOT','NAME','ASSETS'))
    args=ap.parse_args();build(args.game,args.output,args.mod)
