import json, shutil
from prepare_hanabi_private_test import OUT, write
from kashira_bridge import export_project

for project in (OUT/'REDELBE_LR_Hanabi',OUT/'REDELBE_LR_Hanabi_Hair_Head'):
    shutil.copytree(OUT/'dependencies',project/'REDELBE_Dependencies',dirs_exist_ok=True)
    mapping=json.loads((project/'private_texture_mapping.json').read_text())
    source_map=project/'source_mapping.json'
    if source_map.exists():
        rows=json.loads(source_map.read_text())
        for row in rows:
            replacement=next((m for m in mapping if m['old']==row.get('id')),None)
            if replacement:
                row['original_resource_id']=row['id'];row['id']=replacement['private']
                row['file']=f"0x{row['id']:08x}.g1t"
        write(source_map,rows)
    (project/'PRIVATE_TEXTURE_TEST.md').write_text('Hanabi private texture test\n\n16 texture resources use dedicated IDs. Original LR texture bytes are retained as Vanilla fallbacks. The separate Hanabi hair/head project uses the same private IDs for compatibility. This isolates these texture resource references, but does not yet prove that every material-object consumer is exclusive to Kokoro or that two simultaneous variants of Kokoro can differ. In-game cross-character testing remains required.\n',encoding='utf-8')
    name=json.loads((project/'project.ktproj').read_text(encoding='utf-8-sig'))['Name']
    export_project(project,OUT/(name+'.ktmod'))
print('Editable project mappings and merged dependencies exported.')
