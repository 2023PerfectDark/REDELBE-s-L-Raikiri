"""Prepare the release hair palette from the user's own LR resources."""
from pathlib import Path
import argparse,json,struct,subprocess,sys,tempfile
from lr_resources import read_index,extract
from build_layer2_package import wrap

def prepare(game,bundle,only=None,output=None):
    game=Path(game);bundle=Path(bundle)
    source=game/'fdata_package/root.rdb'
    raw,entries,_=read_index(source);entries={e['id']:e for e in entries}
    catalog=(bundle/'hair_colors.tsv').read_text()
    ids=sorted({int(line.split('\t')[1],16) for line in catalog.splitlines()})
    palette=json.loads((bundle/'palette.json').read_text())
    out=Path(output) if output else game/'REDELBE_LR/HairColorSupport'
    (out/'HairColors').mkdir(parents=True,exist_ok=True)
    (out/'vanilla/data').mkdir(parents=True,exist_ok=True)
    patches={}
    with tempfile.TemporaryDirectory() as temp:
        src=Path(temp)/'source.g1t';dst=Path(temp)/'color.g1t'
        for index,fid in enumerate(ids):
            if only is not None and fid!=only:continue
            e=entries[fid]
            if e['c_size']!=13:raise ValueError(f'Unsupported updated resource layout: {fid:08x}')
            original=extract(source,e);src.write_bytes(original)
            baseline=wrap(raw,e,original)
            (out/'vanilla/data'/f'0x{fid:08x}.file').write_bytes(baseline)
            pos=e['rdb_offset'];size=e['entry_size'];record=bytearray(raw[pos:pos+size])
            struct.pack_into('<I',record,44,0x20000)
            struct.pack_into('<H',record,size-13,0xc01)
            struct.pack_into('<I',record,size-7,len(baseline))
            patches[f'{fid:08x}']=record.hex()
            for color in palette:
                if not color['rgb']:continue
                dst.unlink(missing_ok=True)
                subprocess.run([str(bundle/'hair_texture.exe'),str(src),str(dst),color['rgb']],check=True,capture_output=True)
                (out/'HairColors'/f"{fid:08x}_{color['name']}.file").write_bytes(wrap(raw,e,dst.read_bytes()))
            print(f'Prepared hair texture {index+1}/{len(ids)}',flush=True)
    if only is None:
        (out/'records.json').write_text(json.dumps(patches))
        (out/'hair_colors.tsv').write_text(catalog)
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game',type=Path);parser.add_argument('--no-pause',action='store_true');args=parser.parse_args()
    try:
        home=Path(sys.executable if getattr(sys,'frozen',False) else __file__).resolve().parent
        game=args.game or next(p for p in (home,*home.parents) if (p/'DOA6LR.exe').is_file())
        bundle=Path(getattr(sys,'_MEIPASS',home))/'hair_support'
        print('Preparing 16 hair colors locally. Allow about 27 GB of free disk space.')
        prepare(game,bundle)
        print('Hair colors prepared. Close the game and launch through REDELBE to synchronize.')
    except Exception as exc:
        print('Preparation failed:',exc)
        if not args.no_pause:input('Press Enter to close.')
        raise SystemExit(1)
    if not args.no_pause:input('Press Enter to close.')
