import struct,unittest
from model_slot_registry import *
class RegistryTests(unittest.TestCase):
 def fixture(self):
  name='KOK_COS_001';blob=name.encode()+b'\0'
  return {NAMES:(1,len(blob),blob),**{k:(5,1,struct.pack('<I',slot_hash(name) if k==KEYS else i+20)) for i,k in enumerate(ARRAYS)}}
 def test_all_parallel_arrays_extended(self):
  p=extend_registry(self.fixture(),{'KOK_COS_901':123})
  self.assertEqual(validate_registry(p),['KOK_COS_001','KOK_COS_901'])
  self.assertEqual(struct.unpack('<II',p[SETTINGS][2]),(21,123))
 def test_mismatched_lengths_rejected(self):
  p=self.fixture();p[SETTINGS]=(5,2,b'\0'*8)
  with self.assertRaisesRegex(ValueError,'different lengths'):validate_registry(p)
 def test_many_mods_get_distinct_names(self):
  allocator=PrivateSlotNames(['KOK_COS_001','KOK_COS_901'])
  names=[allocator.allocate('KOK_COS_001') for _ in range(500)]
  self.assertEqual(len(set(names)),500)
  self.assertEqual(len({slot_hash(n) for n in names}),500)
  self.assertNotIn('KOK_COS_901',names)
 def test_explicit_source_retains_parallel_metadata(self):
  names=PrivateSlotNames(['KOK_COS_001'])
  name=names.allocate('KOK_COS_001')
  p=extend_registry(self.fixture(),{name:123},names.sources)
  for key in ARRAYS[2:]:
   self.assertEqual(struct.unpack('<II',p[key][2])[0],struct.unpack('<II',p[key][2])[1])
if __name__=='__main__':unittest.main()
