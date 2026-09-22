from pathlib import Path
import json,hashlib,subprocess,shutil,uuid,zipfile
root=Path.cwd();paths=json.loads((root/'analysis/release_staging/paths.json').read_text());release=Path(paths['release']);payload=Path(paths['payload']);game=root/'analysis/release_tests'/('Game with spaces '+uuid.uuid4().hex[:8]);shutil.copytree(release,game)
for name in ('DOA6LR.exe','Kashira-win-x64.exe','KashiraEditor-win-x64.exe'):(game/name).write_bytes(b'fixture - not a game')
(game/'user project.txt').write_text('preserve')
subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(game/'_REDELBE_Runtime/Install.ps1')],check=True)
manifest=json.loads((payload/'release_manifest.json').read_text())
for name,digest in manifest.items():assert hashlib.sha256((game/name).read_bytes()).hexdigest()==digest,name
assert not list(game.rglob('*.pdb'));assert (game/'REDELBE_LR/REDELBE.ini').is_file()
subprocess.run([str(game/'REDELBE_LR_Sync.exe'),'uninstall',str(game)],check=True)
assert (game/'user project.txt').read_text()=='preserve';assert not (game/'dinput8.dll').exists()
# Fresh conflicting loader: installer must leave it untouched.
(game/'dinput8.dll').write_bytes(b'foreign-loader')
r=subprocess.run([str(payload/'REDELBE_LR_Sync.exe'),'install',str(payload),str(game)],capture_output=True)
assert r.returncode and (game/'dinput8.dll').read_bytes()==b'foreign-loader'
# Public text must not include machine/workspace paths or experimental files.
for p in list(release.rglob('*'))+list(payload.rglob('*')):
 if p.is_file() and p.suffix.lower() in ('.txt','.md','.html','.ini','.json','.ps1','.cmd'):
  text=p.read_text(encoding='utf-8-sig',errors='replace');assert 'C:\\Users\\Owner' not in text and 'G:\\Dead or Alive Only' not in text,p
report={'install_wrapper':True,'payload_files_verified':len(manifest),'uninstall_preserves_user_files':True,'foreign_loader_rejected':True,'personal_paths_in_text':False,'fixture':str(game)}
(root/'analysis/release_staging/verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
