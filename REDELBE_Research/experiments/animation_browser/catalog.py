"""Read-only LR animation inventory. Names are hints, not proof of usage."""
import csv, json, re, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
from lr_resources import GAME, read_index, extract

def main():
    output = Path(__file__).resolve().parent
    names = {}
    with (GAME / 'KashiraProjects/Name2Hash/DOA6LR.csv').open(encoding='utf-8-sig') as f:
        for row in csv.reader(f):
            if len(row) == 2:
                names.setdefault(int(row[0], 16), set()).add(row[1].strip())
    rows = []
    for db in ('root', 'system'):
        path = GAME / 'fdata_package' / (db + '.rdb')
        _, entries, _ = read_index(path)
        for entry in entries:
            labels = sorted(names.get(entry['id'], []))
            if not any(n.lower().endswith(('.g1a', '.g2a')) for n in labels):
                continue
            label = next(n for n in labels if n.lower().endswith(('.g1a', '.g2a')))
            row = dict(id=f"0x{entry['id']:08x}", index=db, names=labels,
                       character=label[:3], role='camera' if '_CAMERA_' in label else 'facial' if '_FACIAL_' in label else 'motion',
                       victory_name_hint='_WIN.' in label, usage='unknown', bytes=entry['file_size'])
            # Verify Kasumi victory payloads, without pretending G1A camera and
            # G2A body headers share a layout.
            if label.startswith('KAS') and '_WIN.' in label:
                try:
                    data = extract(path, entry)
                    row.update(payload_verified=True, signature=data[:8].decode('ascii'))
                    if data[:8] == b'_A2G0400':
                        size, fps, frames, bones = struct.unpack_from('<IfHH', data, 8)
                        if size != len(data) or not 0 < fps <= 240:
                            raise ValueError('Invalid G2A header')
                        row.update(frames=frames, fps=fps, seconds=frames/fps)
                except (OSError, ValueError) as ex:
                    row.update(payload_verified=False, error=str(ex))
            rows.append(row)
    by_name = {n:r['id'] for r in rows for n in r['names']}
    for row in rows:
        row['camera_candidates'] = []
        for name in row['names']:
            match = re.fullmatch(r'([A-Z]{3})0(\d{4})_(WIN|ENT|LOSE)\.g1a', name)
            if match:
                candidate = f'{match[1]}_CAMERA_{match[2]}_{match[3]}.g1a'
                if candidate in by_name:
                    row['camera_candidates'].append(dict(name=candidate, id=by_name[candidate], basis='name match; playback unverified'))
    (output/'catalog.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    kasumi = [r for r in rows if r['character']=='KAS' and r['victory_name_hint']]
    (output/'kasumi_victories.json').write_text(json.dumps(kasumi, indent=2), encoding='utf-8')
    print(json.dumps(dict(animations=len(rows),kasumi_victory_resources=len(kasumi),
                         verified=sum(r.get('payload_verified',False) for r in kasumi))))

if __name__ == '__main__':
    main()
