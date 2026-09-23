"""Read-only, on-demand audio library for original DOA6 RRPreview.rdb."""
from pathlib import Path
import re,struct,json
from functools import lru_cache
from legacy_resources import index,extract,u32,u64
from lr_resources import names_from_rnk
import lr_resources
from srs_lr_names import NAMES as LR_NAMES
from rrpreview_names import NAMES
from srsa_lr import Bank,AUDIO,u,COEFF,chunk
from srs_names import bank_names

CATEGORIES=('Character','Music','SFX','Announcer')
CHARACTERS=set('AYA KAS KOK TIN HEL HON MAR NIC SNK MAI RYU HYT HTM LEI JAN ZAC BAS BAY BRA ELI LIS MIL RIG NYO MOM RAC DGO PHF RID CRI MNT'.split())

def planar_wav(e,r):
    """The game stores each ADPCM channel separately; export interleaved PCM."""
    from array import array
    adapt=(230,230,230,230,307,409,512,614,768,614,512,409,307,230,230,230)
    h=r['header'];channels=[]
    for channel in range(r['channels']):
        start=h+u(e,h+u(e,h+48)+4*channel);size=u(e,h+u(e,h+52)+4*channel)
        if start+size>len(e) or size%r['block']:raise ValueError('Invalid planar channel bounds')
        pcm=array('h')
        for p in range(start,start+size,r['block']):
            predictor=e[p];delta,s1,s2=struct.unpack_from('<hhh',e,p+1)
            if predictor>=len(COEFF) or delta<0:raise ValueError('Invalid ADPCM predictor')
            c1,c2=COEFF[predictor];pcm.extend((s2,s1))
            for byte in e[p+7:p+r['block']]:
                for nibble in (byte>>4,byte&15):
                    value=max(-32768,min(32767,int((s1*c1+s2*c2)/256)+(nibble if nibble<8 else nibble-16)*delta))
                    pcm.append(value);s2,s1=s1,value;delta=max(16,adapt[nibble]*delta//256)
        if len(pcm)<r['samples']:raise ValueError('Truncated channel')
        channels.append(pcm[:r['samples']])
    interleaved=array('h',[0])*(r['samples']*r['channels'])
    for i,pcm in enumerate(channels):interleaved[i::r['channels']]=pcm
    fmt=struct.pack('<HHIIHH',1,r['channels'],r['rate'],r['rate']*r['channels']*2,r['channels']*2,16)
    data=b'WAVE'+chunk(b'fmt ',fmt)+chunk(b'data',interleaved.tobytes())
    return '.wav',b'RIFF'+struct.pack('<I',len(data))+data

def category(name):
    tokens=set(re.split(r'[^A-Z0-9]+',name.upper()))
    if 'SV' in tokens:return 'Announcer'
    if 'BGM' in tokens:return 'Music'
    if 'STG' not in tokens and tokens.intersection(('CHA','EV','NV','QV','MV')):return 'Character'
    return 'SFX'

def language(bank,name,tag):
    tokens=set(re.split(r'[^A-Z0-9]+',(bank+' '+name).upper()))
    if tokens.intersection(('US','EN','ENG')):return 'ENG'
    if tokens.intersection(('JP','JPN')):return 'JP'
    # Unsuffixed character voice banks are the original Japanese bank set.
    if tag=='Character' and name and name.lower()!='dummy':return 'JP'
    return 'Other / shared'

class Resource:
    """Range access avoids loading the 1.2 GB music stream bank into RAM."""
    def __init__(self,e):
        if e.get('lr'):
            self.file,offset=lr_resources.container_for(e['path'],e)
            with self.file.open('rb') as f:f.seek(offset);h=f.read(48)
            if len(h)!=48 or h[:8]!=b'IDRK0000' or u32(h,36)!=e['id']:raise ValueError('LR resource header mismatch')
            size,cs,self.size=u64(h,8),u32(h,16),u64(h,24)
            if size<48+cs or offset+size>self.file.stat().st_size:raise ValueError('LR resource bounds')
            self.data=lr_resources.extract(e['path'],e) if cs!=self.size else None
            self.offset=offset+size-cs
            return
        m=re.fullmatch(r'([\da-fA-F]+)@([\da-fA-F]+)(?:#([\da-fA-F]+))?(?:&([\da-fA-F]+))?',e['address'])
        if m:
            self.file=Path(str(e['path'])+'.bin'+(str(int(m[3],16)) if m[3] else '')+('_'+str(int(m[4],16)) if m[4] else ''))
            offset,length=int(m[1],16),int(m[2],16)
        elif not e['address']:
            self.file=e['path'].parent/'data'/f"0x{e['id']:08x}.file";offset=0;length=self.file.stat().st_size
        else:raise ValueError('Unsupported archive address')
        with self.file.open('rb') as f:f.seek(offset);h=f.read(48)
        if len(h)!=48 or h[:8]!=b'IDRK0000' or u32(h,36)!=e['id']:raise ValueError('Resource header mismatch')
        size,cs,self.size=u64(h,8),u32(h,16),u64(h,24)
        if size>length or size<48+cs or offset+size>self.file.stat().st_size:raise ValueError('Resource bounds')
        self.data=extract(e) if cs!=self.size else None
        self.offset=offset+size-cs
    def read(self,p,n):
        if p<0 or n<0 or p+n>self.size:raise ValueError('Audio range outside resource')
        if self.data is not None:return self.data[p:p+n]
        with self.file.open('rb') as f:f.seek(self.offset+p);b=f.read(n)
        if len(b)!=n:raise ValueError('Truncated audio resource')
        return b
    def copy(self,target):
        with Path(target).open('xb') as f:
            for p in range(0,self.size,4*1024*1024):f.write(self.read(p,min(4*1024*1024,self.size-p)))

class Library:
    def __init__(self,path,progress=None):
        report=progress or (lambda value,label:None)
        report(0,'Locating audio resources')
        self.path=Path(path).resolve();self.rows=[];self.banks={};self.errors=[]
        self.is_lr=self.path.is_dir() or self.path.with_suffix('.rdx').exists()
        names={fid:name for name,fid in NAMES.items() if name.endswith(('.srsa','.srst'))}
        if self.is_lr:
            names.update(LR_NAMES);self.index={};rnk={}
            folder=self.path if self.path.is_dir() else self.path.parent
            if (folder/'fdata_package').is_dir():folder=folder/'fdata_package'
            paths=sorted(folder.glob('*.rdb'))
            if not paths:raise ValueError('Choose the LR game folder containing fdata_package.')
            for number,db in enumerate(paths):
                report(int(30*number/len(paths)),'Reading resource index: '+db.name)
                _,entries,nid=lr_resources.read_index(db)
                for e in entries:
                    if e['type_id'] in (3151208237,221529933):
                        if e['id'] in self.index:raise ValueError('Duplicate LR audio resource')
                        self.index[e['id']]=dict(e,path=db,lr=True,type=e['type_id'])
                try:rnk.update(names_from_rnk(lr_resources.extract(db,next(e for e in entries if e['id']==nid))))
                except (OSError,ValueError,StopIteration):pass # Retail builds omit the name database.
        else:
            self.index=index(self.path)
            rnk=names_from_rnk(extract(self.index[u32(self.path.read_bytes(),20)]))
        report(30,'Resource indexes loaded')
        for fid,values in rnk.items():
            for value in values:
                m=re.fullmatch(r'R_(SRSA|SRST)［([^/\\]+)］',value)
                if m:names[fid]=m[2]+'.'+m[1].lower()
        byname={name.lower():fid for fid,name in names.items()}
        audio_banks=[(fid,e) for fid,e in self.index.items() if e['type']==3151208237]
        for number,(fid,e) in enumerate(audio_banks):
            report(30+int(55*number/max(1,len(audio_banks))),f'Indexing sound bank {number+1} of {len(audio_banks)}')
            name=names.get(fid,f'unnamed_bank_{fid:08x}.srsa');tag=category(name)
            bankrow={'id':fid,'name':name,'category':tag,'pair':byname.get(str(Path(name).with_suffix('.srst')).lower())}
            self.banks[fid]=bankrow
            try:
                bank=self.bank(fid);readable=bank_names(bank)
                for p,record in bank.entries:
                    if u(record,0)!=AUDIO:continue
                    info=bank.info(p,record);track=u(record,8);trackname=readable.get(track,'')
                    chars=sorted(set(re.split(r'[^A-Z0-9]+',(name+' '+trackname).upper())) & CHARACTERS)
                    self.rows.append(dict(bank=fid,id=track,name=trackname,bank_name=name,category=tag,character=', '.join(chars),codec=info['codec'],language=language(name,trackname,tag)))
            except Exception as exc:self.errors.append(name+': '+str(exc))
        # Match unnamed stream pairs by all referenced record IDs and offsets.
        for number,(fid,row) in enumerate(self.banks.items()):
            report(85+int(10*number/max(1,len(self.banks))),'Matching streamed audio pairs')
            if row['pair'] is not None:continue
            bank=self.bank(fid);refs=[]
            for p,e in bank.entries:
                info=bank.info(p,e)
                if info['codec']=='external-ogg':refs.append((u(e,info['header']+52)-16,u(e,8)))
            if not refs:continue
            matches=[]
            for stream_id,entry in self.index.items():
                if entry['type']!=221529933:continue
                try:
                    stream=Resource(entry)
                    if all(u(stream.read(pos,12),0)==0x15f4d409 and u(stream.read(pos,12),8)==track for pos,track in refs):matches.append(stream_id)
                except (OSError,ValueError):continue
            if len(matches)==1:row['pair']=matches[0]
            else:self.errors.append(row['name']+': unable to uniquely identify SRST pair')
        self.rows.sort(key=lambda r:(r['category'],r['bank_name'].lower(),r['name'],r['id']))
        report(95,'Preparing the audio library display')
    @lru_cache(maxsize=2)
    def bank(self,fid):
        e=self.index[fid]
        return Bank(lr_resources.extract(e['path'],e) if e.get('lr') else extract(e))
    def audio(self,row):
        bank=self.bank(row['bank'])
        p,e=next((p,e) for p,e in bank.entries if u(e,0)==AUDIO and u(e,8)==row['id'])
        info=bank.info(p,e)
        if info['codec']=='ms-adpcm' and info['channels']>1:return planar_wav(e,info)
        if info['codec']!='external-ogg':return bank.audio(p,e)
        pair=self.banks[row['bank']]['pair']
        if pair not in self.index:raise ValueError('Matching SRST is missing')
        stream=Resource(self.index[pair]);h=info['header'];pos=u(e,h+52)-16
        header=stream.read(pos,64)
        if u(header,0)!=0x15f4d409 or u(header,8)!=row['id'] or header[32:36]!=b'KOVS':raise ValueError('Stream reference mismatch')
        n=u(header,36)
        if n+64>u(header,4) or u(header,16)!=u(e,h+56):raise ValueError('Stream length mismatch')
        audio=bytearray(stream.read(pos+64,n))
        for i in range(min(256,len(audio))):audio[i]^=i
        if audio[:4]!=b'OggS':raise ValueError('Invalid Ogg payload')
        return '.ogg',bytes(audio)
    def export_bank(self,fid,target):
        from srs_audio_core import publish_folder
        row=self.banks[fid]
        def write(folder):
            Resource(self.index[fid]).copy(folder/row['name'])
            if row['pair'] in self.index:Resource(self.index[row['pair']]).copy(folder/Path(row['name']).with_suffix('.srst'))
        publish_folder(target,write)
        return Path(target)/row['name']
    def export_tracks(self,rows,target):
        from srs_audio_core import publish_folder
        def write(folder):
            manifest=[];used=set()
            for row in rows:
                ext,data=self.audio(row);stem=re.sub(r'[^A-Za-z0-9_. -]','_',row['name'] or 'unnamed_track')[:120].rstrip(' .') or 'unnamed_track'
                name=stem+ext;n=2
                while name.lower() in used:name=f'{stem}_{n}{ext}';n+=1
                used.add(name.lower());(folder/name).write_bytes(data)
                manifest.append(dict(row,file=name,id=f"0x{row['id']:08x}",bank=f"0x{row['bank']:08x}"))
            (folder/'tracks.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
        publish_folder(target,write)
