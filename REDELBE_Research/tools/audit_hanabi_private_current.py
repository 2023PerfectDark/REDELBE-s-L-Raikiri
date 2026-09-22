"""Audit current vanilla LR texture references without changing game files."""
import json
from pathlib import Path
from lr_resources import read_index, extract, GAME
from dok_patch import records, props, u

ROOT = Path(__file__).resolve().parents[1]

def main():
    resources = {}
    for db in (GAME/'fdata_package').glob('*.rdb'):
        for entry in read_index(db)[1]:
            resources.setdefault(entry['id'], []).append((db, entry))
    db = extract(*resources[0xd956e4a2][0])
    refs = {}
    for rec in records(db):
        for key, kind, count, offset, size in props(db, rec):
            if key == 0x6c7321d2 and count == 1 and size == 4:
                refs[rec[2]] = u(db, offset)
    audit = json.loads((ROOT/'analysis/isolation/reference_audit.json').read_text())
    mod = next(m for m in audit['mods'] if 'Hanabi' in m['name'])
    result = []
    for texture in mod['textures']:
        targets = []
        for old in texture['old_records']:
            current = refs.get(old['oid'])
            targets.append(dict(object=old['oid'], name=old['name'], current_resource=current,
                                consumers=[oid for oid, fid in refs.items() if fid == current] if current is not None else [],
                                original_resource=old['resource']))
        result.append(dict(file=texture['file'], ids=texture['ids'], targets=targets))
    output = ROOT/'analysis/isolation/hanabi_current_private_audit.json'
    output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'textures':len(result), 'targets':sum(len(r['targets']) for r in result),
                      'missing_objects':sum(t['current_resource'] is None for r in result for t in r['targets']),
                      'shared_targets':sum(len(t['consumers'])>1 for r in result for t in r['targets']),
                      'report':str(output)}, indent=2))

if __name__ == '__main__':
    main()
