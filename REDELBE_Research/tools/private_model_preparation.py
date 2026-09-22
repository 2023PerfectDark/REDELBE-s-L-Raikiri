"""Character-independent private model preparation for Layer2 generations.

The caller owns the generation, shared collision-safe allocators and registry.
No game files or original database records are modified by this module.
"""
import struct
from isolated_material_chain import MaterialCloner

MOTOR=0x68a6f779
MODELS=0x0b6e1578
MATERIALS=0x24c114f6
MATERIAL_NAMES=0x34cf9e5c
VARIATIONS=0xb3a1e5aa
MODEL_FILES=((0x8ab68b3f,'.g1m'),(0x3bbfd9a5,'.grp'),
             (0x7f0de9a3,'.mtl'),(0x8dfd0584,'.oidex'))

def clone_model(cloner,setting,replacements,*,binding_override=None,rebuild_materials=False):
 """Return an independent CharacterSetting for any native costume/face/hair.

 replacements maps LR resource IDs to unpacked bytes. Legacy ports may supply
 their original texture ordering after registering its referenced objects.
 Each invocation gets separate objects/resources even for identical source IDs.
 Callers must stage changes transactionally and verify model routes before use.
 """
 settings=cloner.locate(setting)
 motor=settings.scalar(setting,MOTOR);motors=cloner.locate(motor)
 models=motors.values(motor,MODELS)
 if len(models)!=1:raise ValueError('Private preparation needs one model per part')
 model=models[0];model_db=cloner.locate(model)
 mi=settings.values(setting,MATERIALS);mrnh=motors.values(motor,MATERIAL_NAMES)
 if len(mrnh)%2:raise ValueError('Invalid material-name pairs')
 material_map={}
 for mbe in sorted(set(mi)|set(mrnh[1::2])):
  if not mbe:continue
  db=cloner.locate(mbe);tbc=db.scalar(mbe,MaterialCloner.TBC)
  table_id=cloner.locate(tbc).scalar(tbc,MaterialCloner.KTID)
  changes={MaterialCloner.TBC:cloner.binding(tbc,replacements,replacements.get(table_id))}
  kts=db.scalar(mbe,0x0a3d837b)
  if kts in replacements:changes[0x0a3d837b]=cloner.asset(kts,replacements[kts],'.kts')
  material_map[mbe]=db.clone(mbe,cloner.oid(),changes)
 tbc=model_db.scalar(model,MaterialCloner.TBC)
 table_id=cloner.locate(tbc).scalar(tbc,MaterialCloner.KTID)
 private_tbc=cloner.binding(tbc,replacements,binding_override if binding_override is not None else replacements.get(table_id))
 changes={MaterialCloner.TBC:private_tbc};files={}
 for key,extension in MODEL_FILES:
  fid=model_db.scalar(model,key)
  if fid:
   data=replacements[fid] if fid in replacements else cloner.extract(fid)
   files[extension]=data;changes[key]=cloner.asset(fid,data,extension)
 private_model=model_db.clone(model,cloner.oid(),changes)
 new_mrnh=[material_map.get(v,v) if i%2 else v for i,v in enumerate(mrnh)]
 new_mi=[material_map.get(v,v) for v in mi]
 if rebuild_materials:
  from private_mesh_materials import materials,build
  mesh_materials=materials(files['.g1m'])
  if len(mrnh)!=2*len(mesh_materials):raise ValueError('Legacy mesh/material-name mismatch')
  table=cloner.assets[cloner.locate(private_tbc).scalar(private_tbc,MaterialCloner.KTID)]['payload']
  private_materials=[build(cloner,mrnh[2*i+1],slots,table) for i,slots in enumerate(mesh_materials)]
  new_mrnh=[v for i,mbe in enumerate(private_materials) for v in (mrnh[2*i],mbe)]
  new_mi=private_materials*settings.scalar(setting,VARIATIONS)
 # Catch the out-of-range legacy binding that previously hid/broke Hanabi.
 from private_mesh_materials import materials
 table=cloner.assets[cloner.locate(private_tbc).scalar(private_tbc,MaterialCloner.KTID)]['payload']
 indexes={i for i,_ in struct.iter_unpack('<II',table)}
 for material in materials(files['.g1m']):
  if any(index not in indexes for index,_,_ in material):
   raise ValueError('Mesh needs texture bindings absent from its private table')
 private_motor=motors.clone_arrays(motor,cloner.oid(),{MODELS:[private_model],MATERIAL_NAMES:new_mrnh})
 return settings.clone_arrays(setting,cloner.oid(),{MOTOR:[private_motor],MATERIALS:new_mi})
