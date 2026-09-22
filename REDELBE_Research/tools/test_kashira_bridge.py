import json,tempfile,unittest,uuid,zipfile,os
from pathlib import Path
from kashira_bridge import profiles_enabled,safe_child,validate_marker,materialize,export_project,MARKER,newer_project_source

class BridgeTests(unittest.TestCase):
    def test_hair_head_markers(self):
        for slot in ('KAS_HAIR_002','KOK_FACE_001'):
            meta={'schema':1,'mode':'Layer2','target':'doa6lr','id':str(uuid.uuid4()),'slot':slot,'name':'Hair example','assets':'Content_Legacy/Layer2/'+slot}
            self.assertEqual(validate_marker(meta)['slot'],slot)
        meta['slot']='KAS_STAGE_001'
        with self.assertRaises(ValueError):validate_marker(meta)

    def test_new_build_and_later_loose_edit_both_reach_runtime(self):
        with tempfile.TemporaryDirectory() as d:
            game=Path(d);project=game/'project';assets=project/'Content_Legacy/Layer2/AYA_COS_001'
            assets.mkdir(parents=True);asset=assets/'0x12345678.g1t';asset.write_bytes(b'GT1Gold-project')
            meta={'schema':1,'mode':'Layer2','target':'doa6lr','id':str(uuid.uuid4()),'slot':'AYA_COS_001','name':'Example','assets':'Content_Legacy/Layer2/AYA_COS_001'}
            marker=project/MARKER;marker.write_text(json.dumps(meta))
            (project/'project.ktproj').write_text(json.dumps({'TargetGame':'doa6lr'}))
            package=game/'Example.ktmod'
            with zipfile.ZipFile(package,'w') as z:
                z.writestr(MARKER,json.dumps(meta));z.writestr(meta['assets']+'/0x12345678.g1t',b'GT1Gnew-build')
            os.utime(marker,ns=(1000000000,1000000000));os.utime(asset,ns=(1000000000,1000000000));os.utime(package,ns=(2000000000,2000000000))
            selected,loose,_=newer_project_source(game,package,meta,'project/project.ktproj')
            self.assertIsNone(loose)
            materialize(package,selected,loose,game/'built')
            self.assertEqual((game/'built/0x12345678.g1t').read_bytes(),b'GT1Gnew-build')
            asset.write_bytes(b'GT1Glater-edit');os.utime(asset,ns=(3000000000,3000000000))
            selected,loose,_=newer_project_source(game,package,meta,'project/project.ktproj')
            self.assertEqual(loose,project)
            materialize(package,selected,loose,game/'edited')
            self.assertEqual((game/'edited/0x12345678.g1t').read_bytes(),b'GT1Glater-edit')
    def test_profiles(self):
        self.assertEqual(profiles_enabled({},['B','a']),['a','B'])
        p={'Active':'test','Profiles':[{'Name':'Test','Mods':[{'Mod':'B','Enabled':False},{'Mod':'a'},{'Mod':'A'},{'Mod':'missing'}]}]}
        self.assertEqual(profiles_enabled(p,['a','B','new']),['a','new'])
        p['Profiles'][0]['Mods']=[{'Mod':n,'Enabled':False} for n in ['a','B']]
        self.assertEqual(profiles_enabled(p,['a','B']),[])

    def test_paths(self):
        with tempfile.TemporaryDirectory() as d:
            for p in ['../x','C:/x','/x','x/../../y']:
                with self.assertRaises(ValueError):safe_child(d,p)
            self.assertEqual(safe_child(d,'a/b'),Path(d).resolve()/'a/b')

    def test_editor_package_roundtrip_and_duplicates(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);project=root/'project';assets=project/'Content_Legacy/REDELBE_Layer2/AYA_COS_001'
            assets.mkdir(parents=True);(assets/'0x12345678.g1t').write_bytes(b'GT1Gsample')
            meta={'schema':1,'mode':'Layer2','target':'doa6lr','id':str(uuid.uuid4()),'slot':'AYA_COS_001','name':'Sample','assets':'Content_Legacy/REDELBE_Layer2/AYA_COS_001'}
            (project/MARKER).write_text(json.dumps(meta));package=root/'sample.ktmod'
            export_project(project,package)
            slot,name,_=materialize(package,meta,None,root/'out')
            self.assertEqual((slot,name),('AYA_COS_001','Sample'))
            self.assertEqual((root/'out/0x12345678.g1t').read_bytes(),b'GT1Gsample')
            (assets/'0xafbec60c.g1t').write_bytes(b'GT1Gunused')
            skipped=[]
            materialize(package,meta,project,root/'known-only',{0x12345678},skipped)
            self.assertEqual([p.name for p in (root/'known-only').iterdir()],['0x12345678.g1t'])
            self.assertEqual(skipped[0]['file'],'0xafbec60c.g1t')
            (assets/'0x12345678.g1m').write_bytes(b'_M1Gduplicate')
            with self.assertRaises(ValueError):materialize(package,meta,project,root/'duplicate')

if __name__=='__main__':unittest.main()
