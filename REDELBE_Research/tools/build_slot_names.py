"""Generate display names from the user's local LR name database, not asset IDs."""
from pathlib import Path
import csv,re,json
from build_layer2_package import slot_hash
root=Path(__file__).resolve().parents[1]
source=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round\KashiraProjects\Name2Hash\DOA6LR.csv')
names=set()
for row in csv.reader(source.open(encoding='utf-8-sig')):
    if len(row)==2:
        match=re.match(r'([A-Z0-9]+_COS_[0-9]+)[_.]',row[1])
        if match:names.add(match[1])
audit=root/'analysis/texture_audit/texture-sharing.json'
if audit.exists():
    names.update(row['slot'] for row in json.loads(audit.read_text())['costumes']
                 if re.fullmatch(r'[A-Z0-9]+_COS_[0-9]+',row['slot']))
seen={}
for name in sorted(names):
    h=slot_hash(name)
    if h in seen:raise ValueError(f'Slot hash collision: {name} / {seen[h]}')
    seen[h]=name
assert seen[0xafc8b47d]=='AYA_COS_001'
assert seen[0xc2d8bb18]=='AYA_COS_105'
lines=['#pragma once','#include <cstdint>','// Generated from local DOA6LR.csv and the LR singleton costume-name audit.',
       'struct Layer2SlotName { uint32_t hash; const char* name; };',
       'static const Layer2SlotName layer2SlotNames[]={']
lines += [f'    {{0x{h:08x},"{name}"}},' for h,name in sorted(seen.items())]
lines += ['};','']
(root/'prototype/layer2_slot_names.h').write_text('\n'.join(lines))
print(f'Generated {len(seen)} collision-free costume slot names')
evidence=root/'evidence/layer2_body_release_test.log'
if evidence.exists():
    observed={int(h,16) for h in re.findall(r'LAYER2 REQUEST P[12] costume=([0-9a-f]+)',evidence.read_text())}
    print('Previously observed slots:',{hex(h):seen.get(h,'UNKNOWN') for h in sorted(observed)})
