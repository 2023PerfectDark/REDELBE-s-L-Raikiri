"""Explicit, bounded uninstall; never delete game or Kashira content."""
from pathlib import Path
import hashlib,json,os,shutil,time,zipfile
from runtime_paths import internal_path

ROOT_FILES={'dinput8.dll','REDELBE_LR.asi','REDELBE_LR_Sync.exe',
            'REDELBE_LR_Launcher.exe','Sync REDELBE Layer2.cmd','Remove REDELBE LR.cmd'}
MOD_DIRS=('Layer2','RRPreview','StageVidPreviews','AuraSounds')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def uninstall(game,mode):
    from kashira_bridge import game_closed,safe_child
    if mode not in ('all','keep-mods'):raise ValueError('Choose all or keep-mods explicitly.')
    game=Path(game).resolve();game_closed(game)
    if not (game/'DOA6LR.exe').is_file():raise ValueError('DOA6LR.exe not found.')
    app=game/"REDELBE's Last Raikiri";alias=game/'REDELBE_LR'
    if app.is_symlink() or app.resolve()!=app or not app.is_dir():
        raise ValueError('Expected a physical REDELBE installation inside the game folder.')
    root=app/'REDELBE LR'
    # Reject unexpected links before reading, archiving or recursively deleting.
    for base,dirs,files in os.walk(app,followlinks=False):
        for name in dirs+files:
            p=Path(base)/name
            if p.is_symlink() or getattr(p,'is_junction',lambda:False)():
                raise ValueError('Unexpected link inside installation; preserved: '+str(p))
    if os.path.lexists(alias) and alias.resolve()!=root.resolve():
        raise ValueError('REDELBE_LR points outside this installation; nothing removed.')
    manifest=json.loads(internal_path(game,'installed_files.json').read_text())
    remove=[];preserved=[]
    for name in ROOT_FILES:
        p=game/name
        if p.exists():
            if p.is_symlink() or name not in manifest or sha(p)!=manifest[name]:preserved.append(str(p))
            else:remove.append(p)
    restores=[];journal=root/'converted_packages.json'
    if journal.exists():
        for row in reversed(json.loads(journal.read_text())):
            p=safe_child(game,row['package']);original=safe_child(game,row['original'])
            if not p.is_relative_to((game/'_Kashira/Mods').resolve()):
                raise ValueError('Unexpected converted-package destination; uninstall stopped.')
            if p.exists() and sha(p).lower()==row['converted_sha256'].lower():
                if not original.is_file():raise ValueError('Missing original Kashira package: '+str(original))
                restores.append((original,p))
    archive=None
    if mode=='keep-mods':
        archive=game/('REDELBE LR Saved Mods '+time.strftime('%Y%m%d_%H%M%S')+'.zip')
        with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,allowZip64=True) as z:
            if root.exists():
                for p in sorted(root.iterdir()):
                    if p.is_file() and p.suffix.lower() in ('.txt','.ini'):
                        z.write(p,'REDELBE LR/'+p.name)
                for name in MOD_DIRS:
                    for p in sorted((root/name).rglob('*')):
                        if p.is_file():z.write(p,'REDELBE LR/'+p.relative_to(root).as_posix())
        with zipfile.ZipFile(archive) as z:
            if z.testzip() is not None:raise ValueError('Archive validation failed; installation retained.')
    for original,p in restores:shutil.copy2(original,p)
    for p in remove:
        if os.name=='nt':
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(str(p),128)
        p.unlink()
    if os.path.lexists(alias):
        # Only unlink the verified compatibility junction, never its target.
        if getattr(alias,'is_junction',lambda:False)():os.rmdir(alias)
        elif alias.is_symlink():alias.unlink()
        else:raise ValueError('Expected compatibility link, not a physical root directory.')
    if app.resolve().parent!=game:raise ValueError('Unsafe uninstall target.')
    shutil.rmtree(app)
    result={'status':'uninstalled','mode':mode,'archive':str(archive) if archive else None,
            'preserved_unrecognized_root_files':preserved}
    print(json.dumps(result,indent=2));return result
