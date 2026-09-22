from pathlib import Path
import zipfile,json,collections,sys
sys.stdout.reconfigure(encoding='utf-8')
base=Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common')
old=base/'Dead or Alive 6'
lr=base/'Dead or Alive 6 Last Round - Backup 2026-09-15_210415'
out=Path('analysis/isolation');out.mkdir(exist_ok=True)
for path in lr.glob('*xml.zip'):
 with zipfile.ZipFile(path) as z:
  print(path.name,[(f.filename,f.file_size) for f in z.infolist()][:25])
  for f in z.infolist():
   if 'MaterialEditor' in f.filename:
    with z.open(f) as stream: print(stream.read(1600).decode('utf-8-sig',errors='replace'))
mods=[]
for name in ['(DoAxNaruto) Hanabi Hyuga (Adult)','(DoAxFF) Tifa Lockhart v2.0 (OG FF7R)']:
 p=old/'REDELBE/Layer2'/name
 files=[{'path':str(f.relative_to(p)),'bytes':f.stat().st_size} for f in p.rglob('*') if f.is_file()]
 print(name,(p/'mod.ini').read_text(),collections.Counter(Path(f['path']).suffix for f in files))
 print([f['path'] for f in files if Path(f['path']).suffix not in ('.g1t',)])
 mods.append({'name':name,'root':str(p),'files':files})
(out/'inputs.json').write_text(json.dumps(mods,indent=2))
