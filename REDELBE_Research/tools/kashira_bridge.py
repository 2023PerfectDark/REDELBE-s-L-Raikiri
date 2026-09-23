"""Kashira project/profile bridge for REDELBE LR. No game archive is written.

Marked Layer2 packages place files three levels below Content_Legacy, which
Kashira Editor reads recursively and KtmodPackage.LegacyPath deliberately ignores.
The manager controls availability; REDELBE controls runtime selection.
"""
from pathlib import Path, PurePosixPath
import argparse,contextlib,ctypes,hashlib,json,os,re,shutil,struct,subprocess,sys,time,uuid,zipfile
from build_layer2_package import build,slot_hash
from verify_layer2_package import verify
from lr_resources import read_index
from runtime_paths import internal_path

MARKER='Content_Legacy/redelbe_layer2.json'
PARTS=('root.rdb','root.rdx','system.rdb','system.rdx')
BRIDGE_VERSION=10

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def read_json(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def write_json(path,value):Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')

def safe_child(root,relative):
    root=Path(root).resolve();rel=PurePosixPath(str(relative).replace('\\','/'))
    if rel.is_absolute() or not rel.parts or any(p in ('..','.') or ':' in p for p in rel.parts):raise ValueError('Unsafe relative path')
    target=root.joinpath(*rel.parts).resolve()
    if not target.is_relative_to(root):raise ValueError('Path leaves root')
    return target

def validate_marker(meta):
    if meta.get('schema')!=1 or meta.get('mode')!='Layer2' or meta.get('target','').lower()!='doa6lr':raise ValueError('Unsupported Layer2 marker')
    if not re.fullmatch(r'[A-Z0-9]+_(?:COS|HAIR|FACE)_[0-9]+[a-z]?',meta.get('slot','')):raise ValueError('Invalid costume/hair/face slot')
    if not meta.get('name') or any(c in meta['name'] for c in '\t\r\n'):raise ValueError('Invalid mod name')
    p=PurePosixPath(meta.get('assets',''))
    if len(p.parts)<3 or p.parts[0]!='Content_Legacy':raise ValueError('Layer2 assets must be nested below Content_Legacy/group/slot')
    uuid.UUID(meta['id'])
    return meta

def profiles_enabled(document,installed):
    available={n.lower():n for n in installed}
    active=document.get('Active','Default').lower()
    profile=next((p for p in document.get('Profiles',[]) if p.get('Name','').lower()==active),None)
    if profile is None:return sorted(installed,key=str.lower)
    result=[];seen=set()
    for item in profile.get('Mods',[]):
        key=item.get('Mod','').lower()
        if key in available and key not in seen:
            seen.add(key)
            if item.get('Enabled',True):result.append(available[key])
    result.extend(n for n in sorted(installed,key=str.lower) if n.lower() not in seen)
    return result

def newer_project_source(game,file,meta,project_path):
    """A newer built package must not be shadowed by an old registered project.

    Editor payload edits win only while newer than the installed build. Project
    display metadata alone is not a payload edit. Missing local projects permit
    using a distributed package normally.
    """
    if not project_path:return meta,None,[]
    p=safe_child(game,project_path)
    if not p.exists():return meta,None,[]
    dto=read_json(p)
    if dto.get('TargetGame','').lower()!='doa6lr':raise ValueError('Editor project targets another game')
    project=p.parent;marker=project/MARKER;current=validate_marker(read_json(marker))
    if current['id']!=meta['id']:raise ValueError('Project/package identity differs')
    assets=safe_child(project,current['assets'])
    if not assets.is_dir():raise ValueError('Project asset directory missing')
    stamps=[];latest=marker.stat().st_mtime_ns
    for asset in sorted(assets.rglob('*')):
        if asset.is_file():
            if asset.is_symlink() or not asset.resolve().is_relative_to(project.resolve()):raise ValueError('Linked asset outside project')
            stat=asset.stat();stamps.append((str(asset),stat.st_size,stat.st_mtime_ns))
            latest=max(latest,stat.st_mtime_ns)
    if latest>file.stat().st_mtime_ns:return current,project,stamps
    return meta,None,stamps

def unpack_container(path):
    data=path.read_bytes()
    if data[:8]!=b'IDRK0000':raise ValueError('Not a prepared resource container')
    size,csize=struct.unpack_from('<QI',data,8);usize=struct.unpack_from('<Q',data,24)[0]
    if size!=len(data) or csize!=usize or csize>size-48:raise ValueError('Unexpected prepared container')
    return data[-csize:]

def export_project(directory,package):
    directory=Path(directory);meta=validate_marker(read_json(directory/MARKER))
    safe_child(directory,meta['assets'])
    with zipfile.ZipFile(package,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        z.writestr('mod.ini','Target = DOA6LR\nDescription = REDELBE Layer2; available in-game when selected.\n')
        for file in sorted((directory/'Content_Legacy').rglob('*')):
            if file.is_file():z.write(file,file.relative_to(directory).as_posix())

def make_projects(package,output):
    """Create a deployable set of editor projects from the verified 21-mod package."""
    package=Path(package);output=Path(output)
    if output.exists():raise ValueError('Output must be a new directory')
    verify(package);output.mkdir(parents=True)
    mods=output/'Mods';mods.mkdir();projects=output/'KashiraProjects';projects.mkdir()
    catalog=[line.split('\t') for line in (package/'layer2.tsv').read_text().splitlines() if line]
    source_manifest=read_json(package/'manifest.json');config={'schema':1,'projects':{}}
    now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    for number,(hash_text,name,table) in enumerate(catalog,1):
        slot=next(e['slot'] for e in source_manifest['assets'] if e['mod']==number)
        identity=str(uuid.uuid5(uuid.NAMESPACE_URL,'redelbe-lr/'+slot+'/'+name))
        folder=f'REDELBE LR - {number:04d} - '+re.sub(r'[<>:"/\\|?*]','_',name)
        project=projects/f'REDELBE_LR_{number:04d}';assets=project/'Content_Legacy/REDELBE_Layer2'/slot
        assets.mkdir(parents=True)
        for line in (package/table).read_text().splitlines():
            _,target=line.split('\t');payload=unpack_container(safe_child(package,target))
            ext={b'_M1G':'g1m',b'GT1G':'g1t'}.get(payload[:4])
            if ext is None:raise ValueError('Initial collection contains an unsupported asset type')
            (assets/(Path(target).stem+'.'+ext)).write_bytes(payload)
        meta={'schema':1,'mode':'Layer2','target':'doa6lr','id':identity,'slot':slot,'name':name,
              'assets':f'Content_Legacy/REDELBE_Layer2/{slot}'}
        write_json(project/MARKER,meta)
        project_file=project/'project.ktproj'
        write_json(project_file,{'SchemaVersion':1,'Name':folder,'TargetGame':'doa6lr','Author':'',
                   'Description':'REDELBE Layer2 project. Edit files inside Content_Legacy/REDELBE_Layer2.',
                   'CreatedUtc':now,'ModifiedUtc':now})
        export_project(project,mods/(folder+'.ktmod'))
        config['projects'][folder]=project_file.relative_to(output).as_posix()
        print(f'Prepared editor project {number}/{len(catalog)}: {name}',flush=True)
    write_json(output/'bridge.json',config)

def game_closed(game):
    # A reader (Steam, indexing, antivirus) can hold the EXE without running it.
    # Check actual process images instead of using exclusive file access.
    if os.name!='nt':return
    from ctypes import wintypes as W
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    class Entry(ctypes.Structure):
        _fields_=[('dwSize',W.DWORD),('cntUsage',W.DWORD),('pid',W.DWORD),('heap',ctypes.c_size_t),
                  ('module',W.DWORD),('threads',W.DWORD),('parent',W.DWORD),('priority',W.LONG),
                  ('flags',W.DWORD),('exe',W.WCHAR*260)]
    k.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD];k.CreateToolhelp32Snapshot.restype=W.HANDLE
    k.Process32FirstW.argtypes=[W.HANDLE,ctypes.POINTER(Entry)];k.Process32FirstW.restype=W.BOOL
    k.Process32NextW.argtypes=k.Process32FirstW.argtypes;k.Process32NextW.restype=W.BOOL
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
    k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,ctypes.POINTER(W.DWORD)]
    k.QueryFullProcessImageNameW.restype=W.BOOL;k.CloseHandle.argtypes=[W.HANDLE]
    snapshot=k.CreateToolhelp32Snapshot(2,0)
    if snapshot==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    target=os.path.normcase(os.path.abspath(game/'DOA6LR.exe'))
    try:
        entry=Entry();entry.dwSize=ctypes.sizeof(entry)
        more=k.Process32FirstW(snapshot,ctypes.byref(entry))
        while more:
            if entry.exe.lower()=='doa6lr.exe':
                process=k.OpenProcess(0x1000,False,entry.pid)
                if not process:
                    error=ctypes.get_last_error()
                    if error!=87:raise RuntimeError(f'Cannot verify DOA6LR process {entry.pid}: Windows error {error}')
                else:
                    try:
                        path=ctypes.create_unicode_buffer(32768);size=W.DWORD(len(path))
                        if not k.QueryFullProcessImageNameW(process,0,path,ctypes.byref(size)):
                            raise RuntimeError(f'Cannot read DOA6LR process {entry.pid} executable path')
                        if os.path.normcase(os.path.abspath(path.value))==target:
                            raise RuntimeError(f'The backup game is still running (PID {entry.pid}). Close it before synchronizing REDELBE.')
                    finally:k.CloseHandle(process)
            more=k.Process32NextW(snapshot,ctypes.byref(entry))
    finally:k.CloseHandle(snapshot)

def input_plan(game):
    config=read_json(internal_path(game,'bridge.json'))
    installed={};stamps=[]
    for p in sorted((game/'_Kashira/Mods').glob('*.ktmod')):
        installed[p.stem]=p
    profile_path=game/'_Kashira/profiles.json'
    profile=read_json(profile_path) if profile_path.exists() else {}
    enabled=profiles_enabled(profile,list(installed))
    candidates=[];seen=set()
    for name in enabled:
        file=installed[name]
        with zipfile.ZipFile(file) as z:
            if MARKER not in z.namelist():continue
            meta=validate_marker(json.loads(z.read(MARKER)))
        if meta['id'] in seen:raise ValueError('Duplicate Layer2 package identity')
        seen.add(meta['id'])
        project_path=config.get('projects',{}).get(name)
        meta,project,project_stamps=newer_project_source(game,file,meta,project_path)
        stamps.extend(project_stamps)
        candidates.append((name,file,meta,project))
        stamps.append((str(file),file.stat().st_size,file.stat().st_mtime_ns,meta))
    indices={n:digest(game/'fdata_package'/n) for n in PARTS}
    restoration=config.get('legacy_restoration')
    if restoration:
        plan=safe_child(game,restoration)
        stamps.append((str(plan),digest(plan)))
        from legacy_restoration import load_plan
        _,payloads=load_plan(plan)
        stamps.extend((fid,hashlib.sha256(data).hexdigest()) for fid,(_,data) in sorted(payloads.items()))
    from rrpreview import fingerprint
    stamps.extend(fingerprint(game))
    from loose_layer2 import fingerprint as layer2_fingerprint
    stamps.extend(layer2_fingerprint(game))
    for name in ('hair_colors.tsv','records.json','cache.json'):
        p=game/'REDELBE_LR/HairColorSupport'/name
        stamps.append(('hair_support/'+name,digest(p) if p.is_file() else None))
    key=hashlib.sha256(json.dumps([BRIDGE_VERSION,config,profile,indices,stamps],sort_keys=True).encode()).hexdigest()
    return key,indices,candidates

def materialize(file,meta,project,destination,known_ids=None,skipped=None):
    destination.mkdir(parents=True)
    if project:
        source=safe_child(project,meta['assets'])
        if not source.is_dir():raise ValueError('Project asset directory missing')
        files=[(p.name,p.read_bytes) for p in sorted(source.rglob('*')) if p.is_file()]
        context=contextlib.nullcontext()
    else:
        context=zipfile.ZipFile(file)
        files=None
    with context as archive:
        if files is None:
            prefix=meta['assets'].rstrip('/')+'/'
            files=[(PurePosixPath(e.filename).name,lambda e=e:archive.read(e))
                   for e in archive.infolist() if not e.is_dir() and e.filename.startswith(prefix)]
        seen=set()
        for name,read in files:
            if not re.fullmatch(r'0x[0-9a-fA-F]{8}\.[a-zA-Z0-9]+',name):
                raise ValueError(f'Layer2 preparation requires LR hash-named assets: {name}')
            key=name.split('.')[0].lower()
            if key in seen:raise ValueError('Duplicate resource ID in project')
            if known_ids is not None and int(key,16) not in known_ids and Path(name).suffix.lower()!='.g1t':
                if skipped is not None:skipped.append({'mod':meta['name'],'file':name,'reason':'Resource ID absent from LR indexes; Kashira legacy Apply also skips it'})
                continue
            seen.add(key);(destination/name).write_bytes(read())
    if not seen:raise ValueError('No registered Layer2 assets; new private IDs must be registered before use')
    return meta['slot'],meta['name'],str(destination)

def sync(game):
    game=Path(game).resolve();game_closed(game)
    if not (game/'DOA6LR.exe').is_file():raise ValueError('DOA6LR.exe missing from selected folder')
    root=game/'REDELBE_LR';root.mkdir(exist_ok=True)
    if not (internal_path(game,'bridge.json')).exists():write_json(internal_path(game,'bridge.json'),{'projects':{}})
    adapter=internal_path(game,'bridge_tools')/'REDELBE_Kashira_Prepare.exe'
    if adapter.exists():
        from kashira_bundle import prepare_core
        prepare_core(game,adapter)
        result=subprocess.run([str(adapter),'prepare',str(game)],capture_output=True,text=True)
        (game/'REDELBE_LR/kashira_prepare.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError('Kashira costume preparation failed: '+result.stderr.strip())
        if result.stdout:print(result.stdout,flush=True)
    key,indices,candidates=input_plan(game)
    root=game/'REDELBE_LR';state_path=root/'bridge_state.json';active=root/'active_package.txt'
    report={'bridge_version':BRIDGE_VERSION,'active_profile':read_json(game/'_Kashira/profiles.json').get('Active','Default') if (game/'_Kashira/profiles.json').exists() else 'Default',
            'mods':[{'package':n,'slot':m['slot'],'name':m['name'],'source':'saved project' if p else 'built package',
                     'path':str(p/m['assets']) if p else str(f)} for n,f,m,p in candidates]}
    write_json(root/'bridge_sources.json',report)
    if state_path.exists() and active.exists():
        state=read_json(state_path)
        if state.get('fingerprint')==key and safe_child(root,active.read_text().strip()).joinpath('manifest.json').exists():
            return {'status':'unchanged','mods':len(candidates)}
    generation='sets/'+time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]
    target=safe_child(root,generation);staging=root/'bridge_staging'/uuid.uuid4().hex
    staging.mkdir(parents=True)
    definitions=[];skipped=[]
    known_ids={e['id'] for db in ('root','system') for e in read_index(game/'fdata_package'/f'{db}.rdb')[1]}
    config=read_json(internal_path(game,'bridge.json'));restoration=None
    if config.get('legacy_restoration'):
        restoration=safe_child(game,config['legacy_restoration'])
        from legacy_restoration import load_plan
        _,payloads=load_plan(restoration);known_ids.update(payloads)
    for number,(_,file,meta,project) in enumerate(candidates):
        definitions.append(materialize(file,meta,project,staging/str(number),known_ids,skipped))
    recipes={i+1:m.get('private_model_recipe',{}) for i,(_,_,m,_) in enumerate(candidates)}
    from loose_layer2 import prepare as prepare_loose,apply_settings
    loose,settings=prepare_loose(game,staging/'loose_layer2',known_ids)
    definitions.extend(loose)
    from rrpreview import prepare as prepare_rrpreview
    definitions.extend(prepare_rrpreview(game,staging/'rrpreview'))
    from legacy_texture_donors import prepare as prepare_donors
    report['texture_donors']=prepare_donors(game,definitions,known_ids)
    report['skipped_unregistered_assets']=skipped;write_json(root/'bridge_sources.json',report)
    build(game,target,definitions,restoration)
    from hair_color_support import prepare as prepare_hair_colors
    prepare_hair_colors(game,target)
    apply_settings(target,definitions,settings)
    from automatic_private_models import prepare as prepare_private
    report['private_models']=prepare_private(game,target,definitions,recipes)
    write_json(root/'bridge_sources.json',report)
    for item in report['private_models']:
        print(('Private models: ' if item['status']=='isolated' else 'Classic activation (isolation unavailable): ')+item['name']+((': '+item['reason']) if item['reason'] else ''),flush=True)
    result=verify(target)
    if indices!={n:digest(game/'fdata_package'/n) for n in PARTS}:raise RuntimeError('Kashira changed archives during preparation; retry when Apply finishes')
    # Tables in each immutable generation are relative to its own root. Switch
    # the loader to a complete, verified generation with one atomic rename.
    temporary=root/'active_package.next';temporary.write_text(generation+'\n')
    os.replace(temporary,active)
    write_json(state_path,{'fingerprint':key,'generation':generation,'verification':result,
                          'packages':[n for n,_,_,_ in candidates],'baselines':indices})
    # Only our newly generated input staging is removed; output generations are
    # retained as checkpoints. Never remove projects, mod packages or archives.
    resolved=staging.resolve()
    if resolved.parent==(root/'bridge_staging').resolve():shutil.rmtree(resolved)
    return {'status':'synchronized','generation':generation,**result}

def main():
    ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='command',required=True)
    p=sp.add_parser('make-projects');p.add_argument('package',type=Path);p.add_argument('output',type=Path)
    p=sp.add_parser('sync');p.add_argument('game',type=Path)
    p=sp.add_parser('export');p.add_argument('project',type=Path);p.add_argument('package',type=Path)
    p=sp.add_parser('install');p.add_argument('source',type=Path);p.add_argument('game',type=Path)
    p=sp.add_parser('uninstall');p.add_argument('game',type=Path);p.add_argument('--mode',choices=('all','keep-mods'),required=True)
    a=ap.parse_args()
    if a.command=='make-projects':make_projects(a.package,a.output)
    elif a.command=='export':export_project(a.project,a.package)
    elif a.command=='install':
        from portable_install import install
        install(a.source,a.game)
    elif a.command=='uninstall':
        from uninstall_release import uninstall
        uninstall(a.game,a.mode)
    else:
        error_path=a.game/'REDELBE_LR/bridge_last_error.txt'
        try:
            result=sync(a.game)
            error_path.write_text('',encoding='utf-8')
            print(json.dumps(result,indent=2),flush=True)
        except Exception as exc:
            # Only write into an existing installation's REDELBE directory.
            if error_path.parent.is_dir():error_path.write_text(str(exc),encoding='utf-8')
            raise

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(f'REDELBE Kashira sync failed: {exc}',file=sys.stderr,flush=True)
        sys.exit(1)
