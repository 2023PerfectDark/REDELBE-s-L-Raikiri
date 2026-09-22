import struct,unittest
from isolated_material_chain import Database,MaterialCloner

def database(rows):
 b=bytearray(b'_DOK0000'+struct.pack('<IIIII',28,14,len(rows),0,0))
 for oid,key,value in rows:
  b+=b'IDOK0000'+struct.pack('<IIII',40,oid,1,1)+struct.pack('<III',5,1,key)+struct.pack('<I',value)
 struct.pack_into('<I',b,24,len(b));return bytes(b)

class IsolationTests(unittest.TestCase):
 def test_two_clones_keep_vanilla_and_each_other_independent(self):
  raw=database([(10,MaterialCloner.TBC,20),(20,MaterialCloner.KTID,100),(30,MaterialCloner.TEXTURE,200)])
  db=Database(raw);seq=iter(range(1000,1020))
  clone=MaterialCloner({'db':db},lambda fid:struct.pack('<II',0,30),lambda:next(seq),{100,200})
  a=clone.material(10,{200:b'first'});b=clone.material(10,{200:b'second'})
  self.assertNotEqual(a,b)
  self.assertEqual(db.scalar(10,MaterialCloner.TBC),20)
  self.assertEqual(db.scalar(30,MaterialCloner.TEXTURE),200)
  private=[r for r in clone.assets.values() if r['extension']=='.g1t']
  self.assertEqual([r['payload'] for r in private],[b'first',b'second'])
  reparsed=Database(db.serialize())
  for oid,record in db.original_items.items():self.assertEqual(reparsed.items[oid],record)

 def test_colliding_file_id_rejected(self):
  db=Database(database([(20,MaterialCloner.KTID,100),(30,MaterialCloner.TEXTURE,200)]))
  clone=MaterialCloner({'db':db},lambda _:struct.pack('<II',0,30),lambda:200,{200})
  with self.assertRaisesRegex(ValueError,'collision'):clone.binding(20,{200:b'x'})

 def test_custom_mesh_keeps_its_own_binding_order(self):
  db=Database(database([(20,MaterialCloner.KTID,100),(30,MaterialCloner.TEXTURE,200),(31,MaterialCloner.TEXTURE,201)]))
  seq=iter(range(1000,1020))
  native=struct.pack('<IIII',0,30,1,31)
  custom=struct.pack('<II',0,31)
  clone=MaterialCloner({'db':db},lambda _:native,lambda:next(seq),{100,200,201})
  tbc=clone.binding(20,{201:b'custom skin'},custom)
  ktid=clone.assets[db.scalar(tbc,MaterialCloner.KTID)]['payload']
  self.assertEqual(len(ktid),8)
  _,oid=struct.unpack('<II',ktid)
  self.assertEqual(clone.assets[db.scalar(oid,MaterialCloner.TEXTURE)]['payload'],b'custom skin')
  self.assertEqual(db.scalar(31,MaterialCloner.TEXTURE),201)

 def test_original_mutation_rejected(self):
  db=Database(database([(30,MaterialCloner.TEXTURE,200)]))
  db.items[30]=db.items[30][:-1]+b'x'
  with self.assertRaisesRegex(ValueError,'original'):db.serialize()

if __name__=='__main__':unittest.main()
