import struct,unittest
from build_layer2_package import validate_payload
class Tables(unittest.TestCase):
 def test_material_counts_may_change(self):
  original=struct.pack('<IIII',0,0,0,0)
  edited=struct.pack('<IIIIIII',1,1,0,0,0x12345678,1,0)
  validate_payload(edited,original,{'type_id':0xb340861a},'.mtl')
  with self.assertRaises(ValueError):validate_payload(edited[:-4],original,{'type_id':0xb340861a},'.mtl')
 def test_oid_header_may_change_but_type_must_match(self):
  validate_payload(struct.pack('<III',1243,0,12),struct.pack('<III',1041,0,12),{'type_id':0x1ab40ae8},'.oid')
  with self.assertRaises(ValueError):validate_payload(b'GT1G'+b'\0'*8,b'_M1G'+b'\0'*8,{'type_id':1},'.oid')
 def test_regular_signature_still_checked(self):
  with self.assertRaises(ValueError):validate_payload(b'GT1G0000',b'_M1G0000',{'type_id':1},'.g1m')
if __name__=='__main__':unittest.main()
