from pathlib import Path
import sys,json,struct,subprocess,re,collections
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from lr_resources import GAME,read_index,extract
from build_layer2_package import wrap,slot_hash
from dok_patch import records,props,u
base=Path(__file__).parent
active=(GAME/'REDELBE_LR/active_package.txt').read_text().strip();source=GAME/'REDELBE_LR'/active
out=base/'expanded_palette_assets';out.mkdir(exist_ok=True);(out/'HairColors').mkdir(exist_ok=True);(out/'vanilla/data').mkdir(parents=True,exist_ok=True);(out/'overlay').mkdir(exist_ok=True)
path=GAME/'fdata_package/root.rdb';raw,entries,_=read_index(path);idx={e['id']:e for e in entries}
rows=json.loads((base/'expanded_candidates.json').read_text());albedos={int(r['resource'],16) for r in rows if r['kind']=='HAIR'}
mapping=set();missing=[]
char_db=extract(path,idx[0xb290631c]);texture_refs={}
for rec in records(char_db):
 for k,t,n,v,z in props(char_db,rec):
  if k==0x6c7321d2 and t==5 and n==1:texture_refs[rec[2]]=u(char_db,v)

names={int(h,16):n for h,n in (l.split(',',1) for l in (GAME/'KashiraProjects/Name2Hash/DOA6LR.csv').read_text(encoding='utf-8-sig').splitlines() if ',' in l)}
for fid,name in names.items():
 if not re.fullmatch(r'[A-Z]{3}_HAIR_\d{3}.ktid',name) or fid not in idx:continue
 b=extract(path,idx[fid]);assert len(b)%8==0
 targets={texture_refs.get(tex,0) for _,tex in struct.iter_unpack('<II',b)}&albedos
 if not targets:missing.append(name[:-5])
 for tex in targets:mapping.add((name[:-5],tex))
# Verified material objects also cover new resources absent from the older name CSV.
for r in rows:
 if r['kind']=='HAIR':mapping.add((r['character']+'_HAIR_'+r['slot'],int(r['resource'],16)))
old=(source/'hair_colors.tsv').read_text();mapping.update((l,int(i,16)) for h,i,l in (line.split('\t') for line in old.splitlines()))
# Raidou's independently named hair albedo lives on his face model, not skin.
for r in rows:
 if r['character']=='RID' and r['kind']=='FACE':
  for slot in ['000','011','107']:mapping.add(('RID_HAIR_'+slot,int(r['resource'],16)))
# Do not guess face-atlas recolors or absent hair meshes.
shadow=bytearray((source/'overlay/root.rdb').read_bytes());positions={};p=struct.unpack_from('<I',shadow,8)[0]
while p<len(shadow):
 p=(p+3)&~3
 if p==len(shadow):break
 assert shadow[p:p+8]==b'IDRK0000'
 size=struct.unpack_from('<Q',shadow,p+8)[0];positions[struct.unpack_from('<I',shadow,p+36)[0]]=(p,size,struct.unpack_from('<I',shadow,p+16)[0]);p+=size
vanilla=(source/'vanilla.tsv').read_text();colors={r['name']:r['rgb'] for r in json.loads((base/'palette.json').read_text()) if r['rgb']}
for number,fid in enumerate(sorted({f for _,f in mapping}),1):
 if all((source/'HairColors'/f'{fid:08x}_{n}.file').exists() for n in colors):continue
 e=idx[fid];assert e['c_size']==13
 original=extract(path,e);src=out/'HairColors'/f'{fid:08x}.g1t';src.write_bytes(original);baseline=wrap(raw,e,original)
 (out/'vanilla/data'/f'0x{fid:08x}.file').write_bytes(baseline)
 line=f'fdata_package/data/0x{fid:08x}.file\tvanilla/data/0x{fid:08x}.file\n'
 if line not in vanilla:vanilla+=line
 pos,size,csize=positions[fid];assert csize==13
 struct.pack_into('<I',shadow,pos+44,0x20000);struct.pack_into('<H',shadow,pos+size-13,0xc01);struct.pack_into('<I',shadow,pos+size-7,len(baseline))
 for name,rgb in colors.items():
  dest=out/'HairColors'/f'{fid:08x}_{name}.file'
  if dest.exists():continue
  tmp=out/'HairColors'/f'{fid:08x}_{name}.g1t'
  subprocess.run([str(base/'native_test/build/hair_texture.exe'),str(src),str(tmp),rgb],check=True,capture_output=True)
  dest.write_bytes(wrap(raw,e,tmp.read_bytes()));tmp.unlink()
 src.unlink();print('Prepared',number,f'{fid:08x}',flush=True)
(out/'hair_colors.tsv').write_text(''.join(f'{slot_hash(h):08x}\t{f:08x}\t{h}\n' for h,f in sorted(mapping)))
(out/'vanilla.tsv').write_text(vanilla);(out/'overlay/root.rdb').write_bytes(shadow)
report=dict(active=active,hairstyles=len({h for h,f in mapping}),characters=sorted({h[:3] for h,f in mapping}),unmapped=sorted(set(missing)-{h for h,f in mapping}))
(out/'coverage.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
