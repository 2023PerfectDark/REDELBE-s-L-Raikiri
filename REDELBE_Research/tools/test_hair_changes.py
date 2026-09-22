from pathlib import Path
p=Path('prototype/test_layer2_state.cpp');s=p.read_text();s=s.replace('    Layer2Selection s;','''    Layer2Selection hair;
    assert(hair.current(0,123,456)==0);
    assert(hair.cycle(0,123,2,1,456)==1);
    assert(hair.current(0,123,789)==0); // Different face, different available head mods.
    assert(hair.current(1,123,456)==0); // Other player stays Vanilla.
    assert(hair.cycle(0,123,2,-1,456)==0);
    assert(hair.cycle(0,123,2,-1,456)==2);
    Layer2Selection s;''');p.write_text(s)
p=Path('tools/test_kashira_bridge.py');s=p.read_text();s=s.replace('class BridgeTests(unittest.TestCase):','''class BridgeTests(unittest.TestCase):
    def test_hair_head_markers(self):
        for slot in ('KAS_HAIR_002','KOK_FACE_001'):
            meta={'schema':1,'mode':'Layer2','target':'doa6lr','id':str(uuid.uuid4()),'slot':slot,'name':'Hair example','assets':'Content_Legacy/Layer2/'+slot}
            self.assertEqual(validate_marker(meta)['slot'],slot)
        meta['slot']='KAS_STAGE_001'
        with self.assertRaises(ValueError):validate_marker(meta)
''');p.write_text(s)
