"""Offline tests for malformed indexes and generated replacement payloads."""
import hashlib, json, struct, tempfile, unittest
from pathlib import Path
from lr_resources import read_index, extract, GAME
from build_overlay import build

class ResourceTests(unittest.TestCase):
    def test_installed_entry_counts(self):
        for name,count in [('root',81154),('system',96198)]:
            _,es,_=read_index(GAME/f'fdata_package/{name}.rdb')
            self.assertEqual(len(es),count)

    def test_rejects_corrupt_entry_bounds(self):
        raw=bytearray((GAME/'fdata_package/root.rdb').read_bytes())
        struct.pack_into('<Q',raw,32+8,len(raw)+1)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'root.rdb';p.write_bytes(raw)
            p.with_suffix('.rdx').write_bytes((GAME/'fdata_package/root.rdx').read_bytes())
            with self.assertRaisesRegex(ValueError,'bounds'): read_index(p)

    def test_all_generated_payloads(self):
        p=Path(__file__).resolve().parents[1]/'packages/ayane_full_test'
        manifest=json.loads((p/'manifest.json').read_text())
        _,es,_=read_index(p/'overlay/root.rdb');lookup={e['id']:e for e in es}
        self.assertEqual(len(manifest['assets']),56)
        for asset in manifest['assets']:
            payload=extract(p/'overlay/root.rdb',lookup[int(asset['id'],16)])
            self.assertEqual(hashlib.sha256(payload).hexdigest(),asset['payload_sha256'])
        original=(GAME/'fdata_package/root.rdb').read_bytes()
        generated=(p/'overlay/root.rdb').read_bytes()
        self.assertEqual(len(original),len(generated))
        # Changes are allowed only in metadata fields for the selected resources.
        allowed=set()
        for a in manifest['assets']:
            e=lookup[int(a['id'],16)];o=e['rdb_offset'];ext=o+e['entry_size']-13
            for start,size in [(o+24,8),(o+44,4),(ext,2),(ext+6,4)]:allowed.update(range(start,start+size))
        self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(original,generated))))

    def test_rejects_unknown_asset(self):
        with tempfile.TemporaryDirectory() as d:
            mods=Path(d)/'mods';mods.mkdir();(mods/'0xffffffff.g1m').write_bytes(b'G1M_0000')
            with self.assertRaisesRegex(ValueError,'expected unique'):build(GAME,mods,Path(d)/'out')

if __name__=='__main__':unittest.main(verbosity=2)
