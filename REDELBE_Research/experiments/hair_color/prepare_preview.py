"""Build a standalone research package without changing installed game files.

Copies the existing prepared package so all previous mods are retained.
Adds named hair albedo candidates verified against the current database.
Shared-resource isolation still requires in-game verification.
"""
from pathlib import Path
import sys,struct,json,shutil,subprocess,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from lr_resources import read_index,extract
from build_layer2_package import wrap,slot_hash
from catalog_hair import catalog
def build(game,xml,out):
    if out.exists():raise ValueError('Output must not exist')
    active=(game/'REDELBE_LR/active_package.txt').read_text().strip()
    source=(game/'REDELBE_LR'/active).resolve()
    if not source.is_relative_to((game/'REDELBE_LR/sets').resolve()):raise ValueError('Invalid active package')
    shutil.copytree(source,out)
    path=game/'fdata_package/root.rdb';raw,entries,_=read_index(path);index={e['id']:e for e in entries}
    shadow=bytearray((out/'overlay/root.rdb').read_bytes())
    positions={};p=struct.unpack_from('<I',shadow,8)[0]
    while p<len(shadow):
        p=(p+3)&~3
        if p==len(shadow):break
        if shadow[p:p+8]!=b'IDRK0000':raise ValueError('Invalid prepared index')
        size=struct.unpack_from('<Q',shadow,p+8)[0];csize=struct.unpack_from('<I',shadow,p+16)[0]
        if size<48 or p+size>len(shadow):raise ValueError('Invalid prepared entry size')
        positions[struct.unpack_from('<I',shadow,p+36)[0]]=(p,size,csize);p+=size
    # The bridge appends private material resources to the original index.
    # Verify each original entry position before changing its external flags.
    from audit_catalog import audit
    rows=audit(xml,extract(path,index[0xd956e4a2]))
    colors={r['name']:r['rgb'] for r in json.loads((Path(__file__).parent/'palette.json').read_text()) if r['rgb']}
    dest=out/'HairColors';dest.mkdir(exist_ok=True)
    vanilla=(out/'vanilla.tsv').read_text();mapping=[];done=set()
    exe=Path(__file__).parent/'native_test/build/hair_texture.exe'
    for row in rows:
        fid=int(row['resource'],16)
        if fid not in done:
            e=index[fid]
            if e['c_size']!=13:raise ValueError('Unsupported RDB external record')
            original=extract(path,e);src=dest/f'{fid:08x}.g1t';src.write_bytes(original)
            base=wrap(raw,e,original);baseline=out/'vanilla/data'/f'0x{fid:08x}.file'
            if not baseline.exists():baseline.write_bytes(base);vanilla+=f'fdata_package/data/0x{fid:08x}.file\tvanilla/data/0x{fid:08x}.file\n'
            pos,size,csize=positions[fid];ext=pos+size-13
            if csize!=13:raise ValueError('Unsupported prepared resource entry')
            if shadow[pos:pos+8]!=b'IDRK0000' or struct.unpack_from('<I',shadow,pos+36)[0]!=fid:raise ValueError('Prepared entry offset mismatch')
            struct.pack_into('<I',shadow,pos+44,0x20000);struct.pack_into('<H',shadow,ext,0xc01);struct.pack_into('<I',shadow,ext+6,len(base))
            for name,rgb in colors.items():
                target=dest/f'{fid:08x}_{name}.g1t'
                subprocess.run([str(exe),str(src),str(target),rgb],check=True,capture_output=True)
                (dest/f'{fid:08x}_{name}.file').write_bytes(wrap(raw,e,target.read_bytes()))
                target.unlink() # Only generated intermediates inside new output.
            src.unlink()
            done.add(fid)
            print(f'Prepared {len(done)} hair albedos',flush=True)
        mapping.append(f'{slot_hash(row["hair_slot"]):08x}\t{fid:08x}\t{row["hair_slot"]}')
    (out/'overlay/root.rdb').write_bytes(shadow);(out/'vanilla.tsv').write_text(vanilla,encoding='utf-8')
    (out/'hair_colors.tsv').write_text('\n'.join(mapping)+'\n',encoding='utf-8')
    (out/'hair_color_research.json').write_text(json.dumps(dict(source=active,scope='DOA Central prototype only',rows=rows,colors=colors),indent=2))
    print(json.dumps(dict(hair_slots=len(set(r['hair_slot'] for r in rows)),characters=sorted(set(r['character'] for r in rows)),unique_albedos=len(done),output=str(out))))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('game',type=Path);p.add_argument('xml',type=Path);p.add_argument('output',type=Path);a=p.parse_args();build(a.game,a.xml,a.output)
