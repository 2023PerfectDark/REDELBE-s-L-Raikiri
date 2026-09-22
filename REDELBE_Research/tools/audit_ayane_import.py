from pathlib import Path
import csv,json,struct,collections
from lr_resources import read_index,extract
BASE=Path(__file__).resolve().parents[1]
LR=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round')
GAME=LR.with_name(LR.name+' - Backup 2026-09-15_210415')
names=collections.defaultdict(set)
for row in csv.reader((LR/'KashiraProjects/Name2Hash/DOA6LR.csv').open(encoding='utf-8-sig')):
    if len(row)==2:names[row[1].lower()].add(int(row[0],16))
resources={}
for idx in ('root','system'):
    path=GAME/'fdata_package'/f'{idx}.rdb'
    for e in read_index(path)[1]:resources.setdefault(e['id'],[]).append((path,e))
def chunks(b):
    pos=struct.unpack_from('<I',b,12)[0];out=[]
    for _ in range(struct.unpack_from('<I',b,20)[0]):
        sig=b[pos:pos+8].decode('ascii');size=struct.unpack_from('<I',b,pos+8)[0]
        if size<12 or pos+size>len(b):raise ValueError('Invalid model chunk')
        out.append(sig);pos+=size
    if pos!=len(b):raise ValueError('Model length/chunks mismatch')
    return out
if __name__=='__main__':
    reports=[];headers={}
    for mod in json.loads((BASE/'analysis/ayane_mod_inventory.json').read_text()):
        if mod['types'].get('.g1m')!=1 or set(mod['types'])!={'.g1m','.g1t'}:continue
        errors=[];files=[]
        for p in sorted(Path(mod['path']).rglob('*')):
            if p.suffix.lower() not in ('.g1m','.g1t'):continue
            ids=names.get(p.name.lower(),set())
            if len(ids)!=1:errors.append(f'Name not unique: {p.name}');continue
            fid=next(iter(ids));entries=resources.get(fid,[])
            if len(entries)!=1:errors.append(f'Resource not unique: {p.name}');continue
            if fid not in headers:
                original=extract(*entries[0]);headers[fid]=(original[:8],chunks(original) if p.suffix.lower()=='.g1m' else None)
            with p.open('rb') as stream:head=stream.read(8)
            if head!=headers[fid][0]:errors.append(f'Header/version differs: {p.name} {head!r} {headers[fid][0]!r}')
            if p.suffix.lower()=='.g1m':
                seq=chunks(p.read_bytes())
                if seq!=headers[fid][1]:errors.append(f'Model chunk sequence differs: {seq} vs {headers[fid][1]}')
            files.append(dict(source=str(p),id=f'0x{fid:08x}',extension=p.suffix.lower(),size=p.stat().st_size))
        reports.append(dict(name=mod['name'],slot=mod['slot'],path=mod['path'],errors=errors,files=files))
    (BASE/'analysis/ayane_import_audit.json').write_text(json.dumps(reports,indent=2))
    clean=[r for r in reports if not r['errors']]
    print(json.dumps(dict(audited=len(reports),clean=len(clean),errors=collections.Counter(e.split(':')[0] for r in reports for e in r['errors'])),indent=2))
    for r in reports[:3]:print(r['name'],r['errors'][:5])
