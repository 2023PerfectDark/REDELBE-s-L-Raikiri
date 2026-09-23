"""SRS Audio Studio LR: format-aware conversion and immutable bank editing."""
from pathlib import Path
import hashlib,json,os,re,shutil,struct,subprocess,sys,tempfile,math
from srsa_lr import Bank,u,put,align,ogg_info,read_wav,AUDIO,wrapped
from rrpreview_audio import paired
from audio_adpcm import encode
from srs_names import bank_names
VERSION='0.3.16'

def rrpreview_game(folder):
    for parent in [Path(folder).resolve(),*Path(folder).resolve().parents]:
        if parent.name.lower()=='rrpreview' and parent.parent.name.lower() in ('redelbe_lr','redelbe lr'):
            for game in parent.parents:
                if (game/'DOA6LR.exe').is_file():return game
    return None

def synchronize(game):
    game=Path(game).resolve();exe=game/'REDELBE_LR_Sync.exe'
    if not (game/'DOA6LR.exe').is_file() or not exe.is_file():return False,'Select a DOA6LR folder with REDELBE_LR_Sync.exe installed.'
    preview=game/'REDELBE_LR/RRPreview'
    if not any(p.is_file() and p.suffix.lower() in ('.srsa','.srst') for p in preview.rglob('*')):
        return False,'No replacement sound banks were found in '+str(preview.resolve())+'. Save your edited bank into this folder first. Sync does not import unsaved edits or files saved elsewhere.'
    try:
        result=subprocess.run([str(exe),'sync',str(game)],capture_output=True,text=True,encoding='utf-8',errors='replace',creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=600)
    except Exception as error:return False,str(error)
    if result.returncode:return False,(result.stderr or result.stdout)[-2500:]
    return True,'RRPreview synchronized. Launch the game to hear the saved audio.'

def batch_files(folder,rows):
    folder=Path(folder);by_name={};by_export={}
    for fid,row in rows.items():
        if row.get('name'):by_name.setdefault(row['name'].lower(),[]).append(fid)
    manifest=folder/'tracks.json'
    if manifest.is_file():
        for row in json.loads(manifest.read_text(encoding='utf-8')):
            if row.get('file'):by_export.setdefault(Path(row['file']).stem.lower(),[]).append(int(row['id'],16))
    items={}
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() not in ('.mp3','.wav','.ogg'):continue
        match=re.fullmatch(r'0x([0-9a-fA-F]{8})(?:__[A-Za-z0-9_.-]+)?',path.stem)
        candidates=[int(match[1],16)] if match else by_export.get(path.stem.lower(),by_name.get(path.stem.lower(),[]))
        if len(set(candidates))!=1:raise ValueError('Unknown or ambiguous audio name: '+path.name+'. Keep tracks.json with extracted audio.')
        fid=candidates[0]
        if fid not in rows:raise ValueError('Track not in this bank: '+path.name)
        if fid in items:raise ValueError('Duplicate replacement for '+path.name)
        items[fid]=path
    if not items:raise ValueError('No MP3, WAV or OGG replacements found.')
    return items

def output_bank_name(path):
    name=Path(path).name
    # Workspace comparison fixtures used lr_ before the actual game filename.
    # Only remove that prefix when the remainder is a known resource name.
    if name.lower().startswith('lr_'):
        from rrpreview_names import NAMES
        if name[3:].lower() in NAMES:return name[3:]
    return name

def encoder_path():
    base=Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parents[1]/'packages/SRS_Audio_Studio_LR'
    candidates=[base/'bin/ffmpeg.exe',base/'ffmpeg.exe']
    for parent in [base,*base.parents]:
        if (parent/'DOA6LR.exe').is_file():
            candidates.extend((parent/'SRS Audio Studio LR/bin/ffmpeg.exe',parent/'bin/ffmpeg.exe'));break
    for path in candidates:
        if path.is_file():return path
    raise ValueError('FFmpeg is missing. Keep the bin folder beside SRS, or run Setup FFmpeg.cmd in its original app folder.')

def ffmpeg(arguments):
    result=subprocess.run([str(encoder_path()),'-hide_banner','-loglevel','error','-nostdin',*map(str,arguments)],capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),timeout=600)
    if result.returncode:raise ValueError('Audio conversion failed: '+result.stderr.decode('utf-8','replace')[-3000:])
    return result.stdout

def convert(source,info,gain=1.0):
    source=Path(source).resolve()
    if source.suffix.lower() not in ('.wav','.mp3','.ogg'):raise ValueError('Choose an MP3, WAV or OGG file.')
    if not source.is_file():raise ValueError('Replacement file does not exist.')
    rate,channels=info['rate'],info['channels']
    common=['-protocol_whitelist','file,pipe','-i',source,'-map','0:a:0','-vn','-sn','-dn','-map_metadata','-1','-ar',rate,'-ac',channels]
    if gain!=1.0:common+=['-af',f'volume={gain:.12g}']
    if info['codec']=='ms-adpcm':
        if channels!=1:raise ValueError('This version supports mono MS-ADPCM only.')
        pcm=ffmpeg(common+['-c:a','pcm_s16le','-f','s16le','pipe:1'])
        if len(pcm)>rate*2*1800:raise ValueError('Voice replacement exceeds 30 minutes.')
        audio=encode(pcm,rate,info['block']);check=read_wav(audio)
        if check['rate']!=rate or check['block']!=info['block']:raise ValueError('ADPCM conversion verification failed')
        return audio
    if info['codec'] in ('ogg','external-ogg'):
        audio=ffmpeg(common+['-c:a','libvorbis','-q:a','5','-f','ogg','pipe:1'])
        ch,sr,samples=ogg_info(audio)
        if (ch,sr)!=(channels,rate) or not samples:raise ValueError('Ogg conversion verification failed')
        return audio
    raise ValueError('Unsupported destination codec')

def levels(path,info):
    from array import array
    pcm=array('f',ffmpeg(['-protocol_whitelist','file,pipe','-i',path,'-map','0:a:0','-vn','-ar',info['rate'],'-ac',info['channels'],'-f','f32le','pipe:1']))
    if not pcm:raise ValueError('Audio contains no samples')
    if any(not math.isfinite(x) for x in pcm):raise ValueError('Audio contains invalid samples')
    return math.sqrt(sum(x*x for x in pcm)/len(pcm)),max(abs(x) for x in pcm)

def matched_conversion(source,reference,info):
    with tempfile.TemporaryDirectory(prefix='srs-volume-') as tmp:
        ext,data=reference;path=Path(tmp)/('original'+ext);path.write_bytes(data)
        target,_=levels(path,info);current,peak=levels(source,info)
        if target<1e-7 or current<1e-7:
            gain=1.0;status='Skipped: original or replacement is silent'
        else:
            requested=target/current;gain=min(requested,0.98/max(peak,1e-12))
            status='Peak-limited' if gain<requested else 'Matched'
        return convert(source,info,gain),{'method':'RMS','gain_db':20*math.log10(gain),'status':status}

def external_audio(entry):
    payload=bytearray(entry[64:64+u(entry,36)])
    for i in range(min(256,len(payload))):payload[i]^=i
    ogg_info(payload)
    return bytes(payload)

def replace_external(a,t,fid,audio):
    bank,streams,tracks=paired(a,t)
    if fid not in tracks:raise ValueError('Selected stream not found')
    channels,rate,samples=ogg_info(audio);_,old,h=tracks[fid]
    if channels!=u(old,h+12):raise ValueError('Channel count mismatch')
    out=bytearray(t[:80]);new_a=bytearray(a)
    for track_id,(pos,record) in streams.items():
        entry=record
        if track_id==fid:
            scrambled=bytearray(audio)
            for i in range(min(256,len(scrambled))):scrambled[i]^=i
            entry=bytearray(record[:64])+scrambled
            entry+=bytes(align(len(entry))-len(entry))
            put(entry,4,len(entry));put(entry,16,len(audio)+32);put(entry,36,len(audio))
        p,e,header=tracks[track_id]
        put(new_a,p+header+52,len(out)+16);put(new_a,p+header+56,u(entry,16))
        if track_id==fid:
            put(new_a,p+header+24,rate);put(new_a,p+header+28,(samples+15)&~15)
        out+=entry
    struct.pack_into('<Q',out,8,len(out));put(out,40,len(out)-16);put(out,44,len(out)-16)
    check,new_streams,_=paired(bytes(new_a),bytes(out))
    if external_audio(new_streams[fid][1])!=audio:raise ValueError('Stream replacement did not roundtrip')
    for track_id in streams:
        if track_id!=fid and streams[track_id][1]!=new_streams[track_id][1]:raise ValueError('Unrelated stream changed')
    for (pos,e),(_,new_e) in zip(bank.entries,check.entries):
        expected=bytearray(e)
        if u(e,0)==AUDIO:
            header=bank.info(pos,e)['header'];identity=u(e,8)
            offsets=(24,28,52,56) if identity==fid else (52,56)
            for offset in offsets:expected[header+offset:header+offset+4]=new_e[header+offset:header+offset+4]
        if expected!=new_e:raise ValueError('Unexpected SRSA metadata change')
    return bytes(new_a),bytes(out)

class Document:
    def __init__(self,path,pair=None,progress=None):
        report=progress or (lambda value,label:None)
        report(0,'Locating the sound bank')
        from srs_pairs import resolve
        self.path,pair=resolve(path,pair=pair)
        raw=self.path.read_bytes();self.raw_a=raw[:4]==b'KTSR';self.raw_t=False
        report(25,'Reading audio metadata')
        self.a=wrapped(raw,b'ASRS');self.t=None;self.changes={};self.replacement_inputs={};self.volume_reports={}
        bank=Bank(self.a)
        report(45,'Checking streamed audio')
        if any(bank.info(p,e)['codec']=='external-ogg' for p,e in bank.entries):
            if not pair.is_file():raise ValueError('This bank uses streamed audio. Place '+pair.name+' beside the SRSA and open again.')
            raw=pair.read_bytes();self.raw_t=raw[:4]==b'KTSR'
            self.t=wrapped(raw,b'TSRS');paired(self.a,self.t)
        report(70,'Indexing tracks and readable names')
        self.original_a=self.a;self.original_t=self.t;self.refresh()
        report(95,'Preparing the bank editor display')

    def refresh(self):
        self.bank=Bank(self.a);self.rows={};self.entries={};self.streams={}
        names=bank_names(self.bank)
        if self.t is not None:self.streams=paired(self.a,self.t)[1]
        for pos,e in self.bank.entries:
            info=self.bank.info(pos,e)
            if info['codec']=='metadata':continue
            fid=u(e,8)
            info['name']=names.get(fid,'')
            if info['codec']=='external-ogg':
                h=info['header'];info.update(channels=u(e,h+12),rate=u(e,h+24),samples=u(e,h+28))
            info['seconds']=info.get('samples',0)/max(1,info.get('rate',1))
            self.rows[fid]=info;self.entries[fid]=(pos,e)

    def audio(self,fid):
        info=self.rows[fid]
        if info['codec']=='external-ogg':return '.ogg',external_audio(self.streams[fid][1])
        if info['codec']=='ms-adpcm' and info['channels']>1:
            from srs_library import planar_wav
            return planar_wav(self.entries[fid][1],info)
        return self.bank.audio(*self.entries[fid])

    def original_audio(self,fid):
        bank=Bank(self.original_a)
        p,e=next((p,e) for p,e in bank.entries if u(e,0)==AUDIO and u(e,8)==fid)
        info=bank.info(p,e)
        if info['codec']=='external-ogg':
            pos=u(e,info['header']+52)-16;size=u(self.original_t,pos+4)
            return '.ogg',external_audio(self.original_t[pos:pos+size])
        return bank.audio(p,e)

    def replace(self,fid,source,match_volume=True):
        if fid not in self.rows:raise ValueError('Select an audio entry first')
        source=Path(source);raw=(source.suffix.lower(),source.read_bytes())
        if match_volume:audio,report=matched_conversion(source,self.original_audio(fid),self.rows[fid])
        else:audio=convert(source,self.rows[fid]);report={'status':'Off'}
        self.commit_audio(fid,audio)
        self.changes[fid]=str(source.resolve());self.replacement_inputs[fid]=raw;self.volume_reports[fid]=report

    def commit_audio(self,fid,audio):
        if self.rows[fid]['codec']=='external-ogg':a,t=replace_external(self.a,self.t,fid,audio)
        else:a,t=self.bank.replace(fid,audio),self.t
        # Validate before committing changes to the working document.
        Bank(a)
        if t is not None:paired(a,t)
        self.a,self.t=a,t;self.refresh()

    def match_replacements(self,ids):
        ids=list(ids)
        if not ids or any(fid not in self.replacement_inputs for fid in ids):raise ValueError('Select an imported replacement. Original tracks are not changed.')
        previous=(self.a,self.t,dict(self.volume_reports))
        try:
            with tempfile.TemporaryDirectory(prefix='srs-rematch-') as tmp:
                for fid in ids:
                    ext,data=self.replacement_inputs[fid];p=Path(tmp)/('source'+ext);p.write_bytes(data)
                    audio,report=matched_conversion(p,self.original_audio(fid),self.rows[fid]);self.commit_audio(fid,audio);self.volume_reports[fid]=report
        except Exception:
            self.a,self.t,self.volume_reports=previous;self.refresh();raise
        return len(ids)

    def reset(self):
        self.a,self.t=self.original_a,self.original_t;self.changes={};self.replacement_inputs={};self.volume_reports={};self.refresh()

    def export(self,folder):
        def populate(target):
            rows=[];used=set()
            for fid,info in self.rows.items():
                row=dict(info)
                if info['codec'] in ('ogg','external-ogg','ms-adpcm'):
                    ext,data=self.audio(fid)
                    label=re.sub(r'[^A-Za-z0-9_.-]','_',info.get('name','')).rstrip('. ')[:120] or 'unnamed_track'
                    if label.upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}:label='_'+label
                    name=label+ext;number=2
                    while name.lower() in used:name=label+'_'+str(number)+ext;number+=1
                    used.add(name.lower())
                    (target/name).write_bytes(data);row['file']=name
                rows.append(row)
            (target/'tracks.json').write_text(json.dumps(rows,indent=2))
        publish_folder(folder,populate)

    def save(self,folder):
        def populate(target):
            output_name=output_bank_name(self.path)
            wire_a=self.a[16:] if self.raw_a else self.a
            (target/output_name).write_bytes(wire_a)
            if self.t is not None:(target/Path(output_name).with_suffix('.srst')).write_bytes(self.t[16:] if self.raw_t else self.t)
            manifest={'tool':'SRS Audio Studio LR '+VERSION,'source_bank':self.path.name,'source_sha256':hashlib.sha256(self.original_a).hexdigest(),'output_sha256':hashlib.sha256(self.a).hexdigest(),'replacements':{f'0x{k:08x}':Path(v).name for k,v in self.changes.items()},'paired_srst':self.t is not None}
            manifest['output_bank']=output_name
            manifest['volume_matching']={f'0x{k:08x}':v for k,v in self.volume_reports.items()}
            if self.t is not None:manifest['srst_sha256']=hashlib.sha256(self.t).hexdigest()
            (target/'edit_manifest.json').write_text(json.dumps(manifest,indent=2))
        publish_folder(folder,populate)

def publish_folder(folder,populate):
    folder=Path(folder).resolve()
    if folder.exists():raise ValueError('Choose a new output folder. Existing folders are never overwritten.')
    if not folder.parent.is_dir():raise ValueError('The output parent folder does not exist.')
    staging=Path(tempfile.mkdtemp(prefix='.srs-export-',dir=folder.parent))
    try:
        populate(staging)
        if folder.exists():raise ValueError('Output folder appeared while saving; choose another name.')
        staging.rename(folder)
    finally:
        if staging.exists():shutil.rmtree(staging)









