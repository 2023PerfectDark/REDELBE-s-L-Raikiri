"""Prepare 20 local DOA6 ports for LR testing; never writes to a game directory.

Only textures with existing unique LR resources are retained, matching the
known-working LR Attitude Dress port. Every omission is recorded for review.
This validates binary layout/mapping, not in-game visual compatibility.
"""
from pathlib import Path
import json,hashlib,shutil,collections
from audit_ayane_import import BASE,GAME,chunks
from build_layer2_package import build
from verify_layer2_package import verify

SELECTED=[
    '(DoA6) Casual Sinful Autumn Punk SFW (Ayane)',
    '(DOAX3S) Sweety SFW Non-Breakable (Ayane)',
    '(DoAXVV) Yom Office Wear Non-Breakable (Ayane)',
    'Ayane Classic DoA4 Costume 2',
    'Ayane Xmas 2019 XNALara-XPS',
    '(Classic) NG2 Chinese Dress (Ayane)',
    '(Classic) November Throwback DoA2U Banshee (Ayane)',
    '(Classic) November Throwback DoA2U Tracksuit 1 (Ayane)',
    '(Classic) November Throwback DoA2U Tracksuit 2 (Ayane)',
    '(Classic) November Throwback DoA5 Raging God - Nine of Violet (Ayane)',
    '(Classic) November Throwback DoAD C2 (Ayane)',
    '(Classic) November Throwback DoAX2 Saga 1 (Ayane)',
    '(DoA Halloween 23) GitS Major Motoko Kusanagi Cosplay 2045 Suit (Ayane)',
    '(DoA Halloween 23) Hiyori Sarugaki Cosplay (Ayane)',
    '(DoA6) Duke Nukem Kate Holsom Cosplay (Ayane)',
    '(DoA6) Ninja Gaiden 2 (Ayane)',
    '(DoA6) TFD Freyna Cosplay Viper Suit (Ayane)',
    '(DoA6) Yoga pants (Ayane)',
    '(NG2Black) Phantom Butterfly 2025 (Ayane)',
    '(DoA2U) Costume 10 (Ayane)',
]

def main():
    audit={r['name']:r for r in json.loads((BASE/'analysis/ayane_import_audit.json').read_text())}
    missing=[n for n in SELECTED if n not in audit]
    if missing:raise ValueError(f'Candidate names not found: {missing}')
    staged=BASE/'test_assets/ayane_twenty'
    package=BASE/'packages/layer2_ayane_21'
    if staged.exists() or package.exists():raise ValueError('Use fresh output directories')
    # The user's visually confirmed reference is byte-identical to the old
    # Attitude Dress model and all 55 mapped legacy files. Its extra EXTR chunk
    # therefore is not treated as an incompatible model version.
    reference=BASE/'test_assets/ayane_full/0x63438245.g1m'
    approved_chunks=chunks(reference.read_bytes())
    reference_mod=audit['(DOA6) Attitude Dress 4K (Ayane) v1']
    for f in reference_mod['files']:
        target=reference.parent/(f['id']+f['extension'])
        if target.read_bytes()!=Path(f['source']).read_bytes():raise ValueError('Reference port differs')
    definitions=[('AYA_COS_001','Ayane Test',str(reference.parent))]
    report=[]
    for number,name in enumerate(SELECTED,2):
        mod=audit[name]
        disallowed=[e for e in mod['errors'] if not e.startswith(('Model chunk sequence differs:','Resource not unique:'))]
        if disallowed:raise ValueError(f'{name}: {disallowed}')
        files=mod['files'];models=[f for f in files if f['extension']=='.g1m']
        if len(models)!=1 or chunks(Path(models[0]['source']).read_bytes())!=approved_chunks:raise ValueError(f'Model layout differs: {name}')
        ids=[f['id'] for f in files]
        if len(ids)!=len(set(ids)):raise ValueError('Duplicate target ID')
        destination=staged/f'{number:04d}_{mod["slot"]}'
        destination.mkdir(parents=True)
        manifest=[]
        for f in files:
            target=destination/(f['id']+f['extension']);shutil.copyfile(f['source'],target)
            manifest.append(dict(**f,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
        definitions.append((mod['slot'],name,str(destination)))
        omissions=[e.split(': ',1)[1] for e in mod['errors'] if e.startswith('Resource not unique:')]
        report.append(dict(number=number,name=name,slot=mod['slot'],source=mod['path'],assets=manifest,
                           omitted_legacy_textures=omissions,visual_validation='pending'))
        print(f'Staged {number}/21: {name} ({len(files)} mapped assets; {len(omissions)} legacy-only textures omitted)',flush=True)
    (BASE/'analysis/ayane_twenty_import.json').write_text(json.dumps(report,indent=2))
    build(GAME,package,definitions)
    result=verify(package)
    (BASE/'evidence/layer2_21_package_verification.json').write_text(json.dumps(result,indent=2))
    rows=['# Ayane Layer2 test collection','',
          'Installed only in the Last Round backup copy. All slots start on Default.',
          'The 20 additions are experimental ports from the local DOA6 collection.',
          'Binary versions and resource mappings were checked; their appearance still needs in-game testing.',
          'Legacy textures absent from LR were omitted, following the working Attitude Dress reference port.',
          'Per-file details and omissions: `analysis/ayane_twenty_import.json`.','',
          '| Slot | Mod |','|---|---|','| AYA_COS_001 | Ayane Test (existing) |']
    rows.extend(f'| {r["slot"]} | {r["name"]} |' for r in report)
    rows+=['','Random only considers mods belonging to the costume the game selects.',
           'AYA_COS_001: 6 mods + Default (6/7 mod chance, conditional on that slot).',
           'AYA_COS_105: 15 mods + Default (15/16 mod chance, conditional on that slot).',
           'Other costume slots still have no replacement.']
    (BASE/'AYANE_21_MODS.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    print(json.dumps(result),flush=True)

if __name__=='__main__':main()
