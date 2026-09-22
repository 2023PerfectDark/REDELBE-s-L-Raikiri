import zipfile,json,hashlib
from pathlib import Path
p=Path('packages/REDELBE_LR_0.3_RC4.zip')
with zipfile.ZipFile(p) as z:
 prefix='REDELBE_LR_Package/'
 manifest=json.loads(z.read(prefix+'release_manifest.json'))
 for name,sha in manifest.items():assert hashlib.sha256(z.read(prefix+name)).hexdigest()==sha,name
 assert not any(n.lower().endswith(('.g1m','.g1t','.ktmod','.srsa')) for n in z.namelist())
 print('PASS:',len(manifest),'runtime hashes; no example mod assets bundled')
