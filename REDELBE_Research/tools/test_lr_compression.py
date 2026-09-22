import io,struct,unittest,zlib
from pathlib import Path
from unittest.mock import patch
from lr_resources import extract

class CompressionTests(unittest.TestCase):
 def test_equal_compressed_and_decoded_sizes(self):
  chunk=bytes.fromhex('14008fd6f4065f9d72a0789c93570a376000021e060440660300197000e10000')
  decoded=zlib.decompress(chunk[10:30]);self.assertEqual(len(chunk),len(decoded))
  for flags,data in [(0x400000,chunk),(0,decoded)]:
   with self.subTest(flags=flags):
    header=bytearray(48);header[:8]=b'IDRK0000'
    struct.pack_into('<Q',header,8,48+len(data));struct.pack_into('<I',header,16,len(data))
    struct.pack_into('<Q',header,24,len(decoded));struct.pack_into('<I',header,36,1);struct.pack_into('<I',header,44,flags)
    with patch.object(Path,'open',return_value=io.BytesIO(header+data)):
     self.assertEqual(extract(Path('root.rdb'),{'id':1,'ext_flags':0xc01}),decoded)
if __name__=='__main__':unittest.main()
