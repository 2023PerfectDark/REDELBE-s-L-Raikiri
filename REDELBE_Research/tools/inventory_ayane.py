from pathlib import Path
import configparser,json,collections,struct
root=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6\REDELBE\Layer2')
out=[]
for folder in sorted(root.iterdir()):
    if not folder.is_dir() or 'ayane' not in folder.name.lower():continue
    ini=folder/'mod.ini'
    if not ini.exists():continue
    cp=configparser.ConfigParser(strict=False,interpolation=None)
    try:cp.read_string(ini.read_text(encoding='utf-8-sig'))
    except Exception:continue
    slot=cp.get('Costume','slot',fallback='').strip('" ')
    work=cp.get('Costume','work',fallback=slot).strip('" ')
    if slot not in ('AYA_COS_001','AYA_COS_105') or work!=slot:continue
    files=[p for p in folder.rglob('*') if p.is_file() and p.suffix.lower() in ('.g1m','.g1t','.ktid','.grp','.mtl','.oid','.oidex','.rigbin')]
    model=[p for p in files if p.stem==slot and p.suffix.lower()=='.g1m']
    if len(model)!=1:continue
    with model[0].open('rb') as f:head=f.read(24)
    out.append(dict(name=folder.name,slot=slot,path=str(folder),files=len(files),types=dict(collections.Counter(p.suffix for p in files)),model_header=head.hex()))
target=Path(__file__).resolve().parents[1]/'analysis/ayane_mod_inventory.json'
target.write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'mods':len(out),'slots':dict(collections.Counter(x['slot'] for x in out)),'inventory':str(target)}))
for item in out:
    if not any(t in item['name'].lower() for t in ('nude','nsfw','slut','bikini','swimsuit','broken','malfunction','possessed','gyaru','lingerie','pubes')):
        print(item['slot'],item['name'],item['types'],item['model_header'][:16])
