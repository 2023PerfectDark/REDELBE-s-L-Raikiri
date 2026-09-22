"""Add independently addressed character model chains to a staged generation.

Native game databases and each mod's unpacked payloads are the inputs. No logs,
fixed PC paths, original DOA6 installation or running game are required.
"""
import configparser,hashlib,json,re,struct
from pathlib import Path
from dok_patch import u,props
from lr_resources import read_index,extract
from build_layer2_package import wrap,slot_hash
from isolated_material_chain import Database,MaterialCloner
from private_model_preparation import clone_model,MOTOR,MODELS,MODEL_FILES
from model_slot_registry import NAMES,SETTINGS,validate_registry,extend_registry,PrivateSlotNames

DB_IDS=(0xb290631c,0x2082ad97,0xd956e4a2)
SCN=0x6d011726

def prepare(game,package,definitions,recipes=None):
 game=Path(game);package=Path(package);recipes=recipes or {}
 resources={e['id']:(p,e) for p in (game/'fdata_package').glob('*.rdb') for e in read_index(p)[1]}
 vanilla=dict(line.split('\t') for line in (package/'vanilla.tsv').read_text().splitlines())
 def payload(fid):
  key=f'fdata_package/data/0x{fid:08x}.file'
  if key in vanilla:
   b=(package/vanilla[key]).read_bytes()
   if u(b,44)&0x400000:raise ValueError('Prepared baseline must be decoded')
   return b[-u(b,16):]
  return extract(*resources[fid])
 dbs={fid:Database(payload(fid)) for fid in DB_IDS};scn=Database(payload(SCN))
 root=next(oid for oid,b in scn.items.items() if u(b,16)==0xdac911d7)
 b=scn.items[root];r=(0,u(b,8),root,u(b,16),u(b,20))
 registry={k:(t,n,b[o:o+s]) for k,t,n,o,s in props(b,r)}
 names=validate_registry(registry)
 settings=dict(zip(names,struct.unpack('<'+'I'*len(names),registry[SETTINGS][2])))
 allocator=PrivateSlotNames(names);newslots={};nextid=0x0fa90000
 reserved=set(resources)|{int(Path(k).stem,16) for k in vanilla}
 def allocate():
  nonlocal nextid
  while nextid in reserved:nextid+=1
  result=nextid;reserved.add(result);nextid+=1;return result
 cloner=MaterialCloner(dbs,payload,allocate,reserved)
 def direct_files(name):
  cs=settings[name];db=cloner.locate(cs);motor=db.scalar(cs,MOTOR)
  models=cloner.locate(motor).values(motor,MODELS)
  if len(models)!=1:raise ValueError('Multiple models in '+name)
  dm=models[0];db=cloner.locate(dm)
  return {db.scalar(dm,key) for key,_ in MODEL_FILES if db.scalar(dm,key)}
 related_cache={}
 def related_files(name):
  if name in related_cache:return related_cache[name]
  cs=settings[name];db=cloner.locate(cs);motor=db.scalar(cs,MOTOR);md=cloner.locate(motor)
  dm=md.scalar(motor,MODELS);result=direct_files(name)
  materials=set(db.values(cs,0x24c114f6))|set(md.values(motor,0x34cf9e5c)[1::2]);materials.discard(0)
  for oid in [dm,*materials]:
   obj=cloner.locate(oid);tbc=obj.scalar(oid,MaterialCloner.TBC);ktid=cloner.locate(tbc).scalar(tbc,MaterialCloner.KTID)
   result.add(ktid)
   for _,tex in struct.iter_unpack('<II',payload(ktid)):
    result.add(cloner.locate(tex).scalar(tex,MaterialCloner.TEXTURE))
  related_cache[name]=result;return result
 reports=[];success={}
 for number,(slot,name,directory) in enumerate(definitions,1):
  if not re.fullmatch(r'[A-Z0-9]+_(COS|HAIR|FACE)_[0-9]+[a-z]?',slot):continue
  row={'mod':number,'name':name,'slot':slot,'status':'classic','reason':''};reports.append(row)
  prior_keys={k:set(db.items) for k,db in dbs.items()};prior_assets=set(cloner.assets);prior_audit=len(cloner.audit)
  try:
   if slot not in settings:raise ValueError('Slot absent from current native registry')
   files={int(p.stem,16):p.read_bytes() for p in Path(directory).rglob('*') if p.is_file() and re.fullmatch(r'0x[0-9a-fA-F]{8}\.[a-zA-Z0-9]+',p.name)}
   recipe=recipes.get(number,{})
   aliases=[(int(target,0),int(source,0)) for target,source in recipe.get('texture_aliases',{}).items()]
   for _ in range(len(aliases)+1):
    changed=False
    for target,source in aliases:
     if source in files and target not in files:files[target]=files[source];changed=True
     elif target in files and source not in files:files[source]=files[target];changed=True
    if not changed:break
   chosen=[slot]
   # Extra supplied face/hair meshes identify their own source slots. Never
   # guess between multiple hairstyles or borrow an opposing fighter's model.
   for kind in ('COS','FACE','HAIR'):
    if kind=='COS' or kind==slot.split('_')[1]:continue
    candidates=[]
    for candidate in names:
     if not candidate.startswith(slot.split('_')[0]+'_'+kind+'_'):continue
     if not re.fullmatch(r'[A-Z0-9]+_(COS|HAIR|FACE)_[0-9]+[a-z]?',candidate):continue
     try:
      if related_files(candidate)&files.keys():candidates.append(candidate)
     except (ValueError,KeyError):continue
    chosen.extend(candidates)
   # Database/shader replacements need their own parser; preserve classic
   # activation and report the limitation instead of silently dropping them.
   if any(data[:4] in (b'_DOK',b'_N1G') for data in files.values()):
    raise ValueError('Database or animation replacement needs a dedicated isolation adapter')
   routes={};local_slots={};consumed=set()
   for source in chosen:
    part_recipe=recipe.get('models',{}).get(source,{})
    binding=bytes.fromhex(part_recipe['binding_hex']) if 'binding_hex' in part_recipe else None
    if binding is not None:
     binding=bytearray(binding)
     for old_text,record_hex in part_recipe.get('texture_objects',{}).items():
      old=int(old_text,0);record=bytearray.fromhex(record_hex)
      if u(record,12)!=old:raise ValueError('Texture recipe object ID mismatch')
      target=cloner.oid();struct.pack_into('<I',record,12,target)
      dbs[DB_IDS[0]].items[target]=bytes(record)
      # Ensure its texture exists before adding the recipe object.
      texture=dbs[DB_IDS[0]].scalar(target,MaterialCloner.TEXTURE);payload(texture)
      for off in range(0,len(binding),8):
       if u(binding,off+4)==old:struct.pack_into('<I',binding,off+4,target)
    first_audit=len(cloner.audit);first_assets=set(cloner.assets)
    cs=clone_model(cloner,settings[source],files,binding_override=binding,rebuild_materials=part_recipe.get('rebuild_materials',False))
    consumed.update(a['original_resource'] for a in cloner.audit[first_audit:])
    consumed.update(cloner.assets[k]['source'] for k in set(cloner.assets)-first_assets)
    hidden=allocator.allocate(source);local_slots[hidden]=cs;routes[source]=hidden
   for _ in range(len(aliases)+1):
    before=len(consumed)
    for target,source in aliases:
     if target in consumed or source in consumed:consumed.update((target,source))
    if len(consumed)==before:break
   visual={fid for fid,data in files.items() if data[:4] in (b'GT1G',b'_M1G')}
   if visual-consumed:raise ValueError('Unmapped visual resources '+','.join(hex(i) for i in sorted(visual-consumed))+'; parts='+','.join(chosen))
   newslots.update(local_slots);success[number]={'routes':routes,'assets':set(cloner.assets)-prior_assets,'consumed':consumed}
   row.update(status='isolated',reason='',models=routes)
  except (ValueError,KeyError,struct.error) as exc:
   for k,db in dbs.items():
    for oid in set(db.items)-prior_keys[k]:del db.items[oid]
   for fid in set(cloner.assets)-prior_assets:del cloner.assets[fid]
   del cloner.audit[prior_audit:]
   row['reason']=str(exc)
 if not success:
  (package/'private_models.json').write_text(json.dumps(reports,indent=2));return reports
 # Only extend the registry after every individual clone transaction completes.
 changes=extend_registry(registry,newslots,allocator.sources);metadata=bytearray();values=bytearray()
 for key,t,n,o,s in props(b,r):
  data=b[o:o+s]
  if key in changes:t,n,data=changes[key]
  metadata+=struct.pack('<III',t,n,key);values+=data
 newroot=bytearray(b[:24])+metadata+values;struct.pack_into('<I',newroot,8,len(newroot));newroot+=b'\0'*((-len(newroot))%4)
 scn.items[root]=bytes(newroot);scn.original_items[root]=bytes(newroot)
 manifest=json.loads((package/'manifest.json').read_text());raw,entries,_=read_index(game/'fdata_package/root.rdb')
 overlay=package/'overlay/root.rdb';shadow=overlay.read_bytes() if overlay.exists() else raw
 rr={};pos=u(shadow,8)
 while pos<len(shadow):
  n=struct.unpack_from('<Q',shadow,pos+8)[0];rr[u(shadow,pos+36)]=bytearray(shadow[pos:pos+((n+3)&~3)]);pos+=(n+3)&~3
 def place(fid,data,source):
  if source in resources:
   path,entry=resources[source];entry=dict(entry);source_raw=path.read_bytes()
  else:
   template=rr[source];entry=dict(next(e for e in entries if e['type_id']==u(template,40) and e['c_size']==13));source_raw=raw
  if entry['c_size']!=13:raise ValueError('Unsupported private resource index encoding')
  record=bytearray(source_raw[entry['rdb_offset']:entry['rdb_offset']+((entry['entry_size']+3)&~3)])
  struct.pack_into('<I',record,36,fid);entry['id']=fid
  container=bytearray(wrap(source_raw,entry,data));struct.pack_into('<I',container,36,fid)
  target=f'vanilla/data/0x{fid:08x}.file';(package/target).parent.mkdir(parents=True,exist_ok=True);(package/target).write_bytes(container)
  vanilla[f'fdata_package/data/0x{fid:08x}.file']=target
  if fid in rr:record=rr[fid]
  ext=struct.unpack_from('<Q',record,8)[0]-u(record,16)
  struct.pack_into('<I',record,44,0x20000);struct.pack_into('<H',record,ext,0xc01);struct.pack_into('<I',record,ext+6,len(container));struct.pack_into('<Q',record,24,len(data));rr[fid]=record
  manifest['dependencies']=[x for x in manifest.get('dependencies',[]) if int(x['id'],16)!=fid]
  manifest['dependencies'].append({'id':hex(fid),'sha256':hashlib.sha256(data).hexdigest()})
 for fid,db in {**dbs,SCN:scn}.items():place(fid,db.serialize(),fid)
 for fid,asset in cloner.assets.items():place(fid,asset['payload'],asset['source'])
 header=bytearray(shadow[:u(shadow,8)]);struct.pack_into('<I',header,16,len(rr));overlay.write_bytes(header+b''.join(rr[k] for k in sorted(rr)))
 redirects=dict(line.split('\t') for line in (package/'redirects.tsv').read_text().splitlines());redirects['fdata_package/root.rdb']='overlay/root.rdb'
 (package/'redirects.tsv').write_text(''.join(k+'\t'+v+'\n' for k,v in redirects.items()))
 baselines=dict(line.split('\t') for line in (package/'baselines.tsv').read_text().splitlines())
 for ext in ('rdb','rdx'):
  key='fdata_package/root.'+ext;baselines[key]=hashlib.sha256((game/key).read_bytes()).hexdigest()
 (package/'baselines.tsv').write_text(''.join(k+'\t'+v+'\n' for k,v in baselines.items()))
 (package/'vanilla.tsv').write_text(''.join(k+'\t'+v+'\n' for k,v in vanilla.items()))
 catalog=[line.split('\t') for line in (package/'layer2.tsv').read_text().splitlines()]
 for number,result in success.items():
  table=package/catalog[number-1][2];old=dict(line.split('\t') for line in table.read_text().splitlines())
  # Retain non-model additions (e.g. sounds); remove all consumed shared IDs.
  old={k:v for k,v in old.items() if int(Path(k).stem,16) not in result['consumed']}
  manifest['assets']=[a for a in manifest['assets'] if a['mod']!=number or int(a['id'],16) not in result['consumed']]
  fid=min(result['assets']);key=f'fdata_package/data/0x{fid:08x}.file';old[key]=vanilla[key]
  digest=hashlib.sha256(cloner.assets[fid]['payload']).hexdigest()
  manifest['assets'].append({'mod':number,'id':hex(fid),'slot':definitions[number-1][0],'payload_sha256':digest,'vanilla_sha256':digest})
  table.write_text(''.join(k+'\t'+v+'\n' for k,v in old.items()))
  ini=table.parent/'mod.ini';cfg=configparser.ConfigParser(interpolation=None);cfg.read(ini,encoding='utf-8-sig')
  cfg['PrivateModel']={'enabled':'1','count':str(len(result['routes']))}
  for index,(source,hidden) in enumerate(result['routes'].items()):
   cfg['PrivateModel']['source_'+str(index)]=hex(slot_hash(source));cfg['PrivateModel']['work_'+str(index)]=hex(slot_hash(hidden))
  with ini.open('w',encoding='utf-8') as stream:cfg.write(stream)
 (package/'manifest.json').write_text(json.dumps(manifest,indent=2))
 (package/'private_models.json').write_text(json.dumps(reports,indent=2))
 return reports
