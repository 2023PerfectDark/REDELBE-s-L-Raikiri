"""Prepare the release hair palette from the user's own LR resources."""
from pathlib import Path
import argparse,configparser,hashlib,json,shutil,struct,subprocess,sys,tempfile
from lr_resources import read_index,extract
from build_layer2_package import wrap

def remove_full_palette(game,bundle):
    game=Path(game).resolve();support=(game/'REDELBE_LR/HairColorSupport').resolve()
    if not support.is_relative_to(game):raise ValueError('Hair support folder leaves game directory')
    ids={int(line.split('\t')[1],16) for line in (support/'hair_colors.tsv').read_text().splitlines()}
    palette=json.loads((Path(bundle)/'palette.json').read_text())
    targets=[support/'vanilla/data'/f'0x{fid:08x}.file' for fid in ids]
    targets.extend(support/'HairColors'/f"{fid:08x}_{color['name']}.file" for fid in ids for color in palette if color['rgb'])
    if any(not p.resolve().is_relative_to(support) for p in targets):raise ValueError('Palette path leaves its generated folder')
    removed=0
    for p in targets:
        if p.is_file():removed+=p.stat().st_size;p.unlink()
    print(f'Removed {removed/(1024**3):.2f} GB of generated palette files. Saved choices were preserved.')

def prepare(game,bundle,only=None,output=None,mode='full'):
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
    if mode=='cache':
        if only is not None:raise ValueError('Cache setup requires the complete catalog')
        for fid in ids:
            e=entries[fid]
            if e['c_size']!=13:raise ValueError('Unsupported cache resource layout')
            pos=e['rdb_offset'];size=e['entry_size'];record=bytearray(raw[pos:pos+size])
            struct.pack_into('<I',record,44,0x20000);struct.pack_into('<H',record,size-13,0xc01)
            struct.pack_into('<I',record,size-7,size-13+e['file_size'])
            patches[f'{fid:08x}']=record.hex()
        if getattr(sys,'frozen',False):
            worker=out/'HairCacheWorker.exe'
            if Path(sys.executable).resolve()!=worker.resolve():shutil.copy2(sys.executable,worker)
        (out/'records.json').write_text(json.dumps(patches))
        (out/'hair_colors.tsv').write_text(catalog)
        (out/'cache.json').write_text(json.dumps({'mode':'cache','limit_bytes':1024**3,'source_hash':hashlib.sha256(raw+source.with_suffix('.rdx').read_bytes()).hexdigest()}))
        (out/'Cache').mkdir(exist_ok=True)
        return out
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
        (out/'cache.json').unlink(missing_ok=True)
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game',type=Path);parser.add_argument('--no-pause',action='store_true');parser.add_argument('--mode',choices=('full','cache'));parser.add_argument('--cache-request',type=lambda s:int(s,16));parser.add_argument('--color',type=int,default=0);parser.add_argument('--remove-full',action='store_true');args=parser.parse_args()
    try:
        home=Path(sys.executable if getattr(sys,'frozen',False) else __file__).resolve().parent
        game=args.game or next(p for p in (home,*home.parents) if (p/'DOA6LR.exe').is_file())
        bundle=Path(getattr(sys,'_MEIPASS',home))/'hair_support'
        if args.cache_request is not None:
            from hair_color_cache import request
            request(game,bundle,args.cache_request,args.color)
            raise SystemExit(0)
        cfg=configparser.ConfigParser(interpolation=None);cfg.read(game/'REDELBE_LR/REDELBE.ini',encoding='utf-8-sig')
        mode=args.mode or cfg.get('HairColors','storage_mode',fallback='full').strip().lower()
        if mode not in ('full','cache'):raise ValueError('HairColors storage_mode must be full or cache')
        print('Preparing a 1 GB on-demand cache.' if mode=='cache' else 'Preparing 16 hair colors locally. Allow about 27 GB of free disk space.')
        prepare(game,bundle,mode=mode)
        if mode=='cache':
            remove=args.remove_full
            if not remove and not args.no_pause:remove=input('Remove the old generated full palette to reclaim space? Saved choices stay. [y/N] ').strip().lower()=='y'
            if remove:remove_full_palette(game,bundle)
            else:print('Existing full-palette files are preserved; they are outside the 1 GB cache limit.')
        print('Hair colors prepared. Close the game and launch through REDELBE to synchronize.')
    except Exception as exc:
        print('Preparation failed:',exc)
        if not args.no_pause:input('Press Enter to close.')
        raise SystemExit(1)
    if not args.no_pause:input('Press Enter to close.')
