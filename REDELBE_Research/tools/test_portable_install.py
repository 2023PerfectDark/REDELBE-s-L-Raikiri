import hashlib,json,tempfile,unittest
from pathlib import Path
from portable_install import install,uninstall
from runtime_paths import internal_path
class PortableTests(unittest.TestCase):
 def fixture(self,root):
  source=root/'Package';source.mkdir();game=root/'Unrelated path with spaces';game.mkdir()
  files={'dinput8.dll':b'owned loader','REDELBE_LR/bridge_tools/helper.exe':b'helper'}
  for name,data in files.items():
   p=source/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  (source/'release_manifest.json').write_text(json.dumps({n:hashlib.sha256(v).hexdigest() for n,v in files.items()}))
  for name in ('DOA6LR.exe','Kashira-win-x64.exe','KashiraEditor-win-x64.exe'):(game/name).write_bytes(b'fixture')
  return source,game
 def test_install_remove_preserves_user_files_and_restores_conversion(self):
  with tempfile.TemporaryDirectory() as d:
   source,game=self.fixture(Path(d));user=game/'my-project.ktproj';user.write_text('keep')
   install(source,game);mod=game/'_Kashira/Mods/example.ktmod';mod.parent.mkdir(parents=True);mod.write_bytes(b'converted')
   original=game/'REDELBE_LR/kashira_backups/original.ktmod';original.parent.mkdir(parents=True);original.write_bytes(b'original')
   (game/'REDELBE_LR/converted_packages.json').write_text(json.dumps([{'package':mod.relative_to(game).as_posix(),'original':original.relative_to(game).as_posix(),'converted_sha256':hashlib.sha256(b'converted').hexdigest()}]))
   uninstall(game)
   self.assertFalse((game/'dinput8.dll').exists());self.assertFalse((game/'REDELBE_LR.asi').exists())
   self.assertEqual(user.read_text(),'keep');self.assertEqual(mod.read_bytes(),b'original')
   self.assertTrue(list(game.glob('REDELBE_LR_Removed_*')))
   install(source,game);self.assertTrue((game/'dinput8.dll').exists())
 def test_existing_settings_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   source,game=self.fixture(Path(d));name='REDELBE_LR/REDELBE.ini'
   (source/name).write_text('[UI]\ncharacter_roster_transitions=true\n')
   manifest=json.loads((source/'release_manifest.json').read_text());manifest[name]=hashlib.sha256((source/name).read_bytes()).hexdigest()
   (source/'release_manifest.json').write_text(json.dumps(manifest))
   (game/name).parent.mkdir();(game/name).write_text('; custom\n[UI]\ncharacter_roster_transitions=false\n[Future]\nkey=value\n')
   before=(game/name).read_bytes();install(source,game)
   self.assertEqual((game/name).read_bytes(),before)
   self.assertEqual(json.loads(internal_path(game,'installed_files.json').read_text())[name],hashlib.sha256(before).hexdigest())
 def test_foreign_proxy_conflict_has_no_install_side_effects(self):
  with tempfile.TemporaryDirectory() as d:
   source,game=self.fixture(Path(d));(game/'dinput8.dll').write_bytes(b'other loader')
   with self.assertRaises(ValueError):install(source,game)
   self.assertEqual((game/'dinput8.dll').read_bytes(),b'other loader');self.assertFalse((game/'REDELBE_LR').exists())
 def test_tampered_release_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   source,game=self.fixture(Path(d));(source/'dinput8.dll').write_bytes(b'changed')
   with self.assertRaises(ValueError):install(source,game)
   self.assertFalse((game/'REDELBE_LR').exists())
if __name__=='__main__':unittest.main()
