"""Prepare a local animation browsing library from the owner's installed game.

Never distribute the generated Clips directory. No game archives are modified.
"""
import argparse, json, re
from pathlib import Path
from lr_resources import read_index, extract

def prepare(game,catalog,output):
    from types import SimpleNamespace
    a=SimpleNamespace(game=Path(game),catalog=Path(catalog),output=Path(output))
    rows=json.loads(a.catalog.read_text(encoding='utf-8'))['animations']
    a.output.mkdir(parents=True,exist_ok=True);(a.output/'Clips').mkdir(exist_ok=True)
    indexes={};lines=[];errors=[];camera_lines=[]
    (a.output/'Cameras').mkdir(exist_ok=True)
    by_camera={r['name']:r for r in rows if r['role']=='camera'}
    camera_files={}
    for name,row in by_camera.items():
        try:
            path=a.game/'fdata_package'/(row['index']+'.rdb')
            if path not in indexes:indexes[path]={e['id']:e for e in read_index(path)[1]}
            data=extract(path,indexes[path][int(row['id'],16)])
            if data[:8]!=b'_A1G2400':continue
            target='Cameras/'+row['id']+'.g1a'
            (a.output/target).write_bytes(data);camera_files[name]=target
            if re.fullmatch(r'[A-Z0-9]{3}_CAMERA_700[01]_CHRSEL\.g1a',name):camera_lines.append('@'+row['character']+'\t'+target)
        except (OSError,ValueError,KeyError) as exc:errors.append(dict(name=name,error=str(exc)))
    for row in sorted(rows,key=lambda r:(r['character'],r['category']!='Victory',r['name'])):
        if row['role']!='motion':continue
        try:
            path=a.game/'fdata_package'/(row['index']+'.rdb')
            if path not in indexes:indexes[path]={e['id']:e for e in read_index(path)[1]}
            data=extract(path,indexes[path][int(row['id'],16)])
            if data[:8]!=b'_A2G0400':continue
            name=re.sub(r'[^A-Za-z0-9_.-]','_',row['name'])
            target='Clips/'+row['id']+'.g1a'
            (a.output/target).write_bytes(data)
            lines.append('\t'.join([row['character'],row['category'],name,target]))
            match=re.fullmatch(r'([A-Z0-9]{3})(\d+)_(.+)\.g1a',row['name'])
            if match:
                candidate=f'{match[1]}_CAMERA_{int(match[2])}_{match[3]}.g1a'
                if candidate in camera_files:camera_lines.append(name+'\t'+camera_files[candidate])
        except (OSError,ValueError,KeyError) as exc:errors.append(dict(name=row['name'],error=str(exc)))
    (a.output/'catalog.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (a.output/'cameras.tsv').write_text('\n'.join(camera_lines)+'\n',encoding='utf-8')
    (a.output/'preparation.json').write_text(json.dumps(dict(prepared=len(lines),errors=errors),indent=2))
    return dict(prepared=len(lines),errors=len(errors))

def main():
    p=argparse.ArgumentParser();p.add_argument('game',type=Path);p.add_argument('catalog',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    print(json.dumps(prepare(a.game,a.catalog,a.output)))
if __name__=='__main__':main()
