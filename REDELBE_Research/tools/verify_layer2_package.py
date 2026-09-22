"""Read-only verification of the prepared Layer2 package and its vanilla fallback."""
import argparse, hashlib, json, struct
from pathlib import Path

def digest_container(path, resource):
    data=path.read_bytes()
    if data[:8]!=b'IDRK0000': raise ValueError(f'Bad container: {path}')
    size,compressed=struct.unpack_from('<QI',data,8)
    unpacked=struct.unpack_from('<Q',data,24)[0]
    identifier=struct.unpack_from('<I',data,36)[0]
    if size!=len(data) or compressed!=unpacked or identifier!=resource:
        raise ValueError(f'Bad container metadata: {path}')
    return hashlib.sha256(data[len(data)-compressed:]).hexdigest()

def verify(root):
    manifest=json.loads((root/'manifest.json').read_text())
    catalog=[line.split('\t') for line in (root/'layer2.tsv').read_text().splitlines() if line and not line.startswith('#')]
    if len(catalog)!=manifest['mods']: raise ValueError('Catalog count mismatch')
    tables={}
    for number,(_,name,table) in enumerate(catalog,1):
        tables[number]=dict(line.split('\t') for line in (root/table).read_text().splitlines())
    vanilla=dict(line.split('\t') for line in (root/'vanilla.tsv').read_text().splitlines())
    for entry in manifest.get('dependencies',[]):
        identifier=int(entry['id'],16);source=f'fdata_package/data/0x{identifier:08x}.file'
        if digest_container(root/vanilla[source],identifier)!=entry['sha256']:raise ValueError('Restoration dependency hash mismatch')
    for entry in manifest['assets']:
        identifier=int(entry['id'],16)
        source=f'fdata_package/data/0x{identifier:08x}.file'
        for path,expected in [(tables[entry['mod']][source],entry['payload_sha256']),
                              (vanilla[source],entry['vanilla_sha256'])]:
            target=(root/path).resolve()
            if not target.is_relative_to(root.resolve()): raise ValueError('Path leaves package')
            if digest_container(target,identifier)!=expected: raise ValueError(f'Payload hash mismatch: {target}')
    return {'verified_mods':len(catalog),'verified_mod_assets':len(manifest['assets']),
            'verified_vanilla_assets':len(vanilla),'default':manifest['default']}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('package',type=Path)
    print(json.dumps(verify(parser.parse_args().package),indent=2))
