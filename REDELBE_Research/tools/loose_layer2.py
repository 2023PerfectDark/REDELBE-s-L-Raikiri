"""Read user-facing Layer2 folders; never mutate source mods."""
import configparser,csv,hashlib,re
from pathlib import Path
from lr_resources import read_index,extract,names_from_rnk

EXTENSIONS={'.g1m','.g1t','.grp','.oid','.oidex','.mtl','.ktid','.kts','.g1a','.srsa','.srst','.swg'}

def character_slot(cfg):
 # Legacy REDELBE mods sometimes have paired or unmatched wrapper quotes.
 # Only trim wrappers; retain strict validation of the actual slot identifier.
 for section in ('Costume','Hair','Face'):
  value=cfg.get(section,'slot',fallback='').strip().strip('\"\'').strip()
  if value:return value
 return ''
def folders(game):
 for relative in ('REDELBE_LR/Layer2','REDELBE/Layer2'):
  root=Path(game)/relative
  if not root.exists():continue
  for folder in sorted(root.iterdir()):
   if folder.is_dir() and (folder/'mod.ini').is_file():
    if not folder.resolve().is_relative_to(root.resolve()):raise ValueError('Layer2 link leaves its root')
    yield folder

def fingerprint(game):
 rows=[]
 for folder in folders(game):
  for p in sorted(folder.rglob('*')):
   if p.is_file() and (p.suffix.lower() in EXTENSIONS or p.name.lower()=='mod.ini'):
    if not p.resolve().is_relative_to(folder.resolve()):raise ValueError('Layer2 asset link leaves its folder')
    rows.append((str(p.relative_to(game)),hashlib.sha256(p.read_bytes()).hexdigest()))
 return rows

def prepare(game,staging,known_ids):
 definitions=[];settings={};lookup=None
 def name_lookup():
  result={}
  # Retail LR can omit the RNK name payload. Use installed editor/explorer
  # name tables when available; all IDs still require native registration.
  for relative in ('KashiraProjects/Name2Hash/DOA6LR.csv','Name2Hash/DOA6LR.csv','RDBExplorer/Databases/DOA6LR.csv'):
   table=Path(game)/relative
   if not table.is_file():continue
   with table.open(encoding='utf-8-sig',newline='') as stream:
    for row in csv.reader(stream):
     if len(row)!=2:continue
     try:fid=int(row[0],16)
     except ValueError:continue
     result.setdefault(row[1].replace('\\','/').split('/')[-1].lower(),set()).add(fid)
  for db in (Path(game)/'fdata_package').glob('*.rdb'):
   _,entries,name_id=read_index(db)
   match=[e for e in entries if e['id']==name_id]
   if len(match)!=1:continue
   try:names=names_from_rnk(extract(db,match[0]))
   except (ValueError,FileNotFoundError):continue
   for fid,strings in names.items():
    for text in strings:result.setdefault(text.replace('\\','/').split('/')[-1].lower(),set()).add(fid)
  return result
 for folder in folders(game):
  cfg=configparser.ConfigParser(interpolation=None);cfg.read(folder/'mod.ini',encoding='utf-8-sig')
  settings[folder.name]=(folder/'mod.ini').read_text(encoding='utf-8-sig')
  assets=[p for p in sorted(folder.rglob('*')) if p.is_file() and p.suffix.lower() in EXTENSIONS]
  if not assets:continue # a settings-only override for an existing Kashira mod
  slot=character_slot(cfg)
  if not re.fullmatch(r'[A-Z0-9]+_(COS|HAIR|FACE)_[0-9]+[a-z]?',slot):
   raise ValueError(folder.name+': loose character Layer2 needs a valid costume/hair/face slot; stage conversion is not implemented')
  destination=Path(staging)/str(len(definitions));destination.mkdir(parents=True)
  seen=set()
  for p in assets:
   if not p.resolve().is_relative_to(folder.resolve()):raise ValueError('Layer2 asset link leaves its folder')
   if re.fullmatch(r'0x[0-9a-fA-F]{8}',p.stem):fid=int(p.stem,16)
   else:
    if lookup is None:lookup=name_lookup()
    ids=lookup.get(p.name.lower(),set())
    if len(ids)!=1:raise ValueError(folder.name+': unknown or ambiguous LR filename '+p.name+'; this legacy mod needs a port')
    fid=next(iter(ids))
   if fid not in known_ids and p.suffix.lower()!='.g1t':raise ValueError(folder.name+': '+p.name+' maps to '+hex(fid)+', which is not registered in LR; this asset needs porting or a restoration mapping')
   if fid in seen:raise ValueError(folder.name+': duplicate resource '+hex(fid))
   seen.add(fid);(destination/f'0x{fid:08x}{p.suffix.lower()}').write_bytes(p.read_bytes())
  definitions.append((slot,cfg.get('General','name',fallback=folder.name),str(destination)))
 return definitions,settings

def apply_settings(package,definitions,settings):
 catalog=[line.split('\t') for line in (Path(package)/'layer2.tsv').read_text().splitlines()]
 for number,(_,name,_) in enumerate(definitions):
  if name not in settings:continue
  source=configparser.ConfigParser(interpolation=None);source.read_string(settings[name])
  ini=(Path(package)/catalog[number][2]).parent/'mod.ini'
  target=configparser.ConfigParser(interpolation=None);target.read(ini,encoding='utf-8-sig')
  for section in source.sections():
   if section.lower() in ('general','costume','hair','face','privatemodel'):continue
   target[section]=dict(source[section])
  with ini.open('w',encoding='utf-8') as stream:target.write(stream)
