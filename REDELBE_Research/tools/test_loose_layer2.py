import tempfile,unittest
from pathlib import Path
from loose_layer2 import prepare,apply_settings,fingerprint

class LooseTests(unittest.TestCase):
 def test_hashed_assets_settings_and_fingerprint(self):
  with tempfile.TemporaryDirectory() as d:
   game=Path(d);folder=game/'REDELBE_LR/Layer2/Test';folder.mkdir(parents=True)
   (folder/'mod.ini').write_text('[General]\ntype=costume\n[Costume]\nslot=AYA_COS_001\n[Aura]\nenabled=true\n')
   asset=folder/'0x12345678.g1t';asset.write_bytes(b'GT1Gtest')
   before=fingerprint(game);definitions,settings=prepare(game,game/'staging',{0x12345678})
   self.assertEqual(definitions[0][:2],('AYA_COS_001','Test'))
   self.assertEqual((Path(definitions[0][2])/asset.name).read_bytes(),asset.read_bytes())
   asset.write_bytes(b'GT1Gedit');self.assertNotEqual(before,fingerprint(game))
   package=game/'out';package.mkdir();(package/'layer2.tsv').write_text('00000001\tTest\tredirects.tsv\n')
   (package/'mod.ini').write_text('[General]\ntype=costume\n[Costume]\nslot=AYA_COS_001\n')
   apply_settings(package,definitions,settings)
   self.assertIn('enabled = true',(package/'mod.ini').read_text())
 def test_settings_only_folder_is_not_duplicate_mod(self):
  with tempfile.TemporaryDirectory() as d:
   game=Path(d);folder=game/'REDELBE_LR/Layer2/Test';folder.mkdir(parents=True)
   (folder/'mod.ini').write_text('[Aura]\nenabled=true\n')
   definitions,settings=prepare(game,game/'staging',set())
   self.assertEqual(definitions,[]);self.assertIn('Test',settings)
if __name__=='__main__':unittest.main()
