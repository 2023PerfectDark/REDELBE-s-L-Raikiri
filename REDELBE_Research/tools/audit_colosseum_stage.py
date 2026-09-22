"""Read-only comparison of the requested Colosseum environment mod and both games."""
from pathlib import Path
import collections, hashlib, json
import legacy_resources as legacy
import lr_resources as lr
from dok_patch import records, props

def inspect(data):
    rows=list(records(data)); values={}
    for row in rows:
        for key,kind,count,offset,size in props(data,row):
            identity=(row[2],key)
            if identity in values:raise ValueError('Duplicate object/property identity')
            values[identity]=(row[3],kind,count,data[offset:offset+size])
    return rows,values

def main():
    out=Path('analysis/colosseum');out.mkdir(exist_ok=True)
    old=lr.GAME.with_name('Dead or Alive 6');fid=0xe12b64ff
    source=old/'REDELBE/Layer2/DoA Colosseum Aftenoon (E3 Key Art)/KIDS/Envs_S0401CLS_env.motor.kidsscndb.kidsobjdb'
    blobs={'mod':source.read_bytes()}
    for path in old.glob('*.rdb'):
        index=legacy.index(path)
        if fid in index:
            if 'doa6' in blobs:raise ValueError('Ambiguous legacy resource')
            blobs['doa6']=legacy.extract(index[fid])
    for name in ('root','system'):
        path=lr.GAME/'fdata_package'/f'{name}.rdb'
        for entry in lr.read_index(path)[1]:
            if entry['id']==fid:
                if 'lr' in blobs:raise ValueError('Ambiguous LR resource')
                blobs['lr']=lr.extract(path,entry)
    if set(blobs)!={'mod','doa6','lr'}:raise ValueError('Missing baseline')
    report={'source':str(source),'resource_id':hex(fid),'runtime_crash_reproduced':False};maps={};ids={}
    for name,data in blobs.items():
        (out/(name+'.kidsobjdb')).write_bytes(data)
        rows,values=inspect(data);maps[name]=values;ids[name]={r[2] for r in rows}
        report[name]={'bytes':len(data),'header_version':int.from_bytes(data[12:16],'little'),'objects':len(rows),'properties':len(values),'sha256':hashlib.sha256(data).hexdigest()}
    report['lr_objects_absent_from_mod']=len(ids['lr']-ids['mod'])
    report['shared_lr_mod_objects']=len(ids['lr']&ids['mod'])
    changes=[]
    for identity,value in maps['mod'].items():
        before=maps['doa6'].get(identity);current=maps['lr'].get(identity)
        if before==value:continue
        changes.append({'object':hex(identity[0]),'property':hex(identity[1]),
            'exists_in_doa6':before is not None,'exists_in_lr':current is not None,
            'same_schema':bool(current and value[:3]==current[:3]),
            'lr_matches_doa6':bool(before and current==before)})
    report['changed_properties']=changes
    report['interpretation']='Whole-file compatibility is not established. LR has newer schema and different objects. Transfer validated environment values into an LR baseline; do not relabel the legacy header or blindly replace the database.'
    (out/'audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='changed_properties'},indent=2))
if __name__=='__main__':main()
