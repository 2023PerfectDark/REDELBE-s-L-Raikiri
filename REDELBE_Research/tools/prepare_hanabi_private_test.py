"""Stage a current-LR Hanabi texture isolation test; never write to the game."""
import hashlib, json, shutil
from pathlib import Path
from lr_resources import GAME, read_index, extract
from dok_patch import records, props, u, patch
from legacy_restoration import load_plan
from build_layer2_package import build
from verify_layer2_package import verify
from kashira_bridge import export_project

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'packages/hanabi_private_main_test'

def write(path, data):
    path.write_text(json.dumps(data,indent=2),encoding='utf-8')

def main():
    if OUT.exists():raise ValueError('Preserve existing test output before rebuilding')
    config=json.loads((GAME/'REDELBE_LR/bridge.json').read_text(encoding='utf-8-sig'))
    base=GAME/config['legacy_restoration']
    plan,_=load_plan(base)
    resources={}
    for path in (GAME/'fdata_package').glob('*.rdb'):
        for e in read_index(path)[1]:resources.setdefault(e['id'],[]).append((path,e))
    audit=json.loads((ROOT/'analysis/isolation/hanabi_current_private_audit.json').read_text())
    OUT.mkdir(parents=True)
    backup=GAME.with_name('Dead or Alive 6 Last Round - Backup 2026-09-15_210415')
    outfit=OUT/'REDELBE_LR_Hanabi'
    hair=OUT/'REDELBE_LR_Hanabi_Hair_Head'
    shutil.copytree(backup/'KashiraProjects/REDELBE_LR_Hanabi',outfit)
    shutil.copytree(GAME/'KashiraProjects/REDELBE_LR_Hanabi_Hair_Head',hair)
    deps=OUT/'dependencies';shutil.copytree(base.parent,deps)
    # Preserve every existing dependency, adding outfit support references.
    outfitplan,_=load_plan(outfit/'REDELBE_Dependencies/restoration_plan.json')
    known={r['id'] for r in plan['resources']}
    keys={(c.get('database',0xd956e4a2),c['oid'],c.get('property',0x6c7321d2)) for c in plan['changes']}
    for c in outfitplan['changes']:
        key=(c.get('database',0xd956e4a2),c['oid'],c.get('property',0x6c7321d2))
        if key not in keys:plan['changes'].append(c);keys.add(key)
    for r in outfitplan['resources']:
        if r['id'] not in known:
            shutil.copyfile(outfit/'REDELBE_Dependencies/restored'/f"0x{r['id']:08x}{r.get('extension','.g1t')}",deps/'restored'/f"0x{r['id']:08x}{r.get('extension','.g1t')}")
            plan['resources'].append(r);known.add(r['id'])
    mapping={};proof=[]
    for row in audit:
        if len(row['targets'])!=1:raise ValueError('Ambiguous texture object')
        t=row['targets'][0];current=t['current_resource']
        seed=('redelbe-lr/private/kokoro/hanabi/'+row['file']).encode()
        fid=int.from_bytes(hashlib.sha256(seed).digest()[:4],'little')
        if fid in resources or fid in known:raise ValueError('Private ID collision')
        known.add(fid);mapping[t['original_resource']]=fid
        baseline=extract(*resources[current][0])
        (deps/'restored'/f'0x{fid:08x}.g1t').write_bytes(baseline)
        plan['resources'].append(dict(id=fid,type=resources[current][0][1]['type_id'],size=len(baseline),sha256=hashlib.sha256(baseline).hexdigest(),extension='.g1t',baseline_resource=current))
        plan['changes']=[c for c in plan['changes'] if not (c.get('database',0xd956e4a2)==0xd956e4a2 and c['oid']==t['object'] and c.get('property',0x6c7321d2)==0x6c7321d2)]
        plan['changes'].append(dict(database=0xd956e4a2,oid=t['object'],lr_resource=current,old_resource=fid,name=row['file']))
        proof.append(dict(source=row['file'],old=t['original_resource'],private=fid,baseline=current))
    # Refresh vanilla fallback bytes for all merged references against this title update.
    for c in plan['changes']:
        r=next(r for r in plan['resources'] if r['id']==c['old_resource'])
        b=extract(*resources[c['lr_resource']][0])
        (deps/'restored'/f"0x{r['id']:08x}{r.get('extension','.g1t')}").write_bytes(b)
        r.update(size=len(b),sha256=hashlib.sha256(b).hexdigest(),baseline_resource=c['lr_resource'])
    write(deps/'restoration_plan.json',plan)
    definitions=[]
    for project in (outfit,hair):
        meta=json.loads((project/'Content_Legacy/redelbe_layer2.json').read_text())
        assets=project/meta['assets']
        for old,new in mapping.items():
            source=assets/f'0x{old:08x}.g1t'
            if source.exists():source.rename(assets/f'0x{new:08x}.g1t')
        write(project/'private_texture_mapping.json',proof)
        definitions.append((meta['slot'],meta['name'],assets))
        name=json.loads((project/'project.ktproj').read_text(encoding='utf-8-sig'))['Name']
        export_project(project,OUT/(name+'.ktmod'))
    before=extract(*resources[0xd956e4a2][0])
    changes=[c for c in plan['changes'] if c.get('database',0xd956e4a2)==0xd956e4a2]
    after=patch(before,changes)
    allowed=set()
    targets={c['oid'] for c in changes}
    for rec in records(before):
        if rec[2] in targets:
            for key,kind,n,offset,size in props(before,rec):
                if key==0x6c7321d2:allowed.update(range(offset,offset+size))
    assert all(i in allowed for i,(a,b) in enumerate(zip(before,after)) if a!=b)
    build(GAME,OUT/'verified_overlay',definitions,deps/'restoration_plan.json')
    result=verify(OUT/'verified_overlay')
    write(OUT/'verification.json',dict(private_textures=proof,overlay=result,unrelated_database_bytes_unchanged=True,live_test_pending=True))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
