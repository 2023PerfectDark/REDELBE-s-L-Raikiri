import json,sys
from pathlib import Path
from lr_resources import read_index,extract
from kashira_bridge import input_plan
game=Path(sys.argv[1]);_,_,candidates=input_plan(game)
staging=max((game/'REDELBE_LR/bridge_staging').iterdir(),key=lambda p:p.stat().st_mtime_ns)
resources={}
for db in ('root','system'):
    path=game/'fdata_package'/f'{db}.rdb'
    for e in read_index(path)[1]:resources.setdefault(e['id'],[]).append((path,e))
bad=[]
for folder in staging.iterdir():
    for file in folder.iterdir():
        fid=int(file.stem,16);entries=resources.get(fid,[])
        if len(entries)!=1:continue
        path,e=entries[0];original=extract(path,e)
        with file.open('rb') as f:header=f.read(16)
        if len(header)<8 or header[:4]!=original[:4] or header[:4]==b'IDRK':
            bad.append({'mod':candidates[int(folder.name)][0],'file':file.name,'bytes':file.stat().st_size,
                        'original_bytes':len(original),'header':header.hex(),'original_header':original[:16].hex()})
print(json.dumps(bad,indent=2))
