"""Prepare portable, global RRPreview overrides from loose files."""
import hashlib,json,re
from pathlib import Path
from rrpreview_names import NAMES
from lr_resources import read_index,extract
from rrpreview_audio import merge

def inputs(game):
    root=Path(game)/'REDELBE_LR/RRPreview';found={}
    if not root.exists():return found
    for p in sorted(root.rglob('*')):
        if not p.is_file():continue
        if not p.resolve().is_relative_to(root.resolve()):raise ValueError('RRPreview link leaves folder')
        fid=NAMES.get(p.name.lower())
        if fid is None and re.fullmatch(r'0x[0-9a-fA-F]{8}\.[a-zA-Z0-9]+',p.name):fid=int(p.stem,16)
        if fid is None:
            if p.suffix.lower() in ('.srsa','.srst'):
                raise ValueError('Unrecognized RRPreview audio filename: '+p.name+'. Use the original game bank name, for example SE1_Common_SV.srsa (without lr_).')
            continue # archives, readmes and source documents are not loaded
        if fid in found:raise ValueError('Duplicate RRPreview resource: '+p.name)
        found[fid]=p
    return found

def fingerprint(game):
    return [(fid,str(p.relative_to(Path(game))),hashlib.sha256(p.read_bytes()).hexdigest()) for fid,p in sorted(inputs(game).items())]

def prepare(game,destination):
    files=inputs(game)
    if not files:return []
    resources={}
    for db in ('root','system'):
        path=Path(game)/'fdata_package'/f'{db}.rdb'
        for e in read_index(path)[1]:
            if e['id'] in files:
                if e['id'] in resources:raise ValueError('Ambiguous RRPreview ID')
                resources[e['id']]=(path,e)
    if set(files)-set(resources):raise ValueError('RRPreview contains a resource absent from LR')
    payloads={fid:p.read_bytes() for fid,p in files.items()};reports=[]
    for fid,p in files.items():
        if p.suffix.lower()!='.srsa':continue
        from srsa_lr import Bank,u
        old=Bank(payloads[fid]);base=extract(*resources[fid])
        if any(old.info(pos,e)['codec']=='external-ogg' for pos,e in old.entries):
            pair=NAMES.get(p.with_suffix('.srst').name.lower())
            if pair not in files:raise ValueError('RRPreview streamed bank needs its named SRST pair: '+p.name)
            payloads[fid],payloads[pair],report=merge(base,extract(*resources[pair]),payloads[fid],payloads[pair])
            reports.append({'bank':p.name,**report})
        else:
            required={(u(e,0),u(e,8)) for _,e in Bank(base).entries}
            provided={(u(e,0),u(e,8)) for _,e in old.entries}
            if not required<=provided:raise ValueError('Legacy embedded bank lacks LR cues: '+p.name)
    destination=Path(destination);destination.mkdir(parents=True)
    for fid,data in payloads.items():
        # A standalone SRST has offsets paired with its SRSA; reject half a pair.
        p=files[fid]
        if p.suffix.lower()=='.srst' and NAMES.get(p.with_suffix('.srsa').name.lower()) not in files:
            raise ValueError('RRPreview SRST requires its named SRSA pair: '+p.name)
        (destination/(f'0x{fid:08x}'+p.suffix.lower())).write_bytes(data)
    (destination/'audio_merge_report.json').write_text(json.dumps(reports,indent=2))
    print('RRPreview: '+json.dumps(reports))
    return [('RRPREVIEW','RRPreview global overrides',str(destination))]
