import tempfile,unittest,os
from pathlib import Path
import hair_color_cache as cache

class CacheTests(unittest.TestCase):
 def test_lru_and_saved_choices(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);old=root/'00000001_01.file';new=root/'00000002_01.file'
   old.write_bytes(b'a'*60);new.write_bytes(b'b'*30)
   settings=root/'HairColors.prototype.ini';settings.write_text('saved choice')
   os.utime(old,(1,1));os.utime(new,(2,2))
   original=cache.LIMIT
   try:
    cache.LIMIT=100;cache.trim(root,50)
    self.assertFalse(old.exists());self.assertTrue(new.exists());self.assertEqual(settings.read_text(),'saved choice')
   finally:cache.LIMIT=original
 def test_oversized_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   with self.assertRaises(ValueError):cache.trim(Path(tmp),cache.LIMIT+1)

if __name__=='__main__':unittest.main()
