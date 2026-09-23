import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from uninstall_release import uninstall

class UninstallTests(unittest.TestCase):
    def setup_game(self,base):
        game=Path(base)/'Game';game.mkdir()
        app=game/"REDELBE's Last Raikiri";root=app/'REDELBE LR'
        data=app/'_REDELBE_Runtime (Not important to you)'/'Data'
        data.mkdir(parents=True);root.mkdir()
        protected=['DOA6LR.exe','Kashira-win-x64.exe','KashiraEditor-win-x64.exe',
                   '_Kashira/Mods/user.ktmod','fdata_package/root.rdb']
        for name in protected+['dinput8.dll','REDELBE_LR_Launcher.exe']:
            p=game/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(name.encode())
        # Even a bad manifest must never authorize deletion of game/Kashira files.
        manifest={n:hashlib.sha256((game/n).read_bytes()).hexdigest() for n in protected+['dinput8.dll','REDELBE_LR_Launcher.exe']}
        (data/'installed_files.json').write_text(json.dumps(manifest))
        for name in ['branding.ini','update_info.txt','cache.json','nested/private.ini','Layer2/Test/model.bin','RRPreview/voice.srsa']:
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('keep or remove')
        return game,app,root,protected

    @patch('kashira_bridge.game_closed')
    def test_keep_archive_exact_scope(self,_):
        with tempfile.TemporaryDirectory() as d:
            game,app,root,protected=self.setup_game(d)
            result=uninstall(game,'keep-mods')
            self.assertFalse(app.exists());self.assertFalse((game/'dinput8.dll').exists())
            for n in protected:self.assertEqual((game/n).read_bytes(),n.encode())
            with zipfile.ZipFile(result['archive']) as z:
                self.assertEqual(set(z.namelist()),{'REDELBE LR/branding.ini','REDELBE LR/update_info.txt',
                    'REDELBE LR/Layer2/Test/model.bin','REDELBE LR/RRPreview/voice.srsa'})

    @patch('kashira_bridge.game_closed')
    def test_all_preserves_changed_loader_and_restores_package(self,_):
        with tempfile.TemporaryDirectory() as d:
            game,app,root,protected=self.setup_game(d)
            (game/'dinput8.dll').write_bytes(b'other loader')
            original=root/'kashira_backups/original.ktmod';original.parent.mkdir();original.write_bytes(b'original')
            package=game/'_Kashira/Mods/user.ktmod';package.write_bytes(b'converted')
            (root/'converted_packages.json').write_text(json.dumps([{'package':'_Kashira/Mods/user.ktmod',
                'original':original.relative_to(game).as_posix(),'converted_sha256':hashlib.sha256(b'converted').hexdigest()}]))
            result=uninstall(game,'all')
            self.assertFalse(app.exists());self.assertIsNone(result['archive'])
            self.assertEqual((game/'dinput8.dll').read_bytes(),b'other loader')
            self.assertEqual(package.read_bytes(),b'original')
            for n in protected:
                if n!='_Kashira/Mods/user.ktmod':self.assertEqual((game/n).read_bytes(),n.encode())

    @patch('kashira_bridge.game_closed')
    def test_external_link_rejected_before_deletion(self,_):
        import _winapi
        with tempfile.TemporaryDirectory() as d:
            game,app,root,_=self.setup_game(d)
            outside=Path(d)/'Protected';outside.mkdir();(outside/'keep.txt').write_text('keep')
            link=root/'external';_winapi.CreateJunction(str(outside),str(link))
            try:
                with self.assertRaises(ValueError):uninstall(game,'all')
                self.assertTrue(app.exists());self.assertEqual((outside/'keep.txt').read_text(),'keep')
            finally:link.rmdir()

if __name__=='__main__':unittest.main()
