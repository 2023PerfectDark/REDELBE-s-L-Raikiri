"""Keep all native model-registry arrays aligned when adding hidden models."""
import struct
from build_layer2_package import slot_hash
NAMES=0x4d269345
KEYS=0x8af6c2ab
SETTINGS=0x8f9f2da6
ARRAYS=(KEYS,SETTINGS,0x1e132334,0x4c52fe59)
def validate_registry(p):
 kind,n,b=p[NAMES]
 if kind!=1 or n!=len(b) or not b.endswith(b'\0'):raise ValueError('Invalid registry name blob')
 names=b[:-1].decode('ascii').split('\0')
 if len(set(names))!=len(names):raise ValueError('Duplicate model name')
 for key in ARRAYS:
  t,count,data=p[key]
  if t!=5 or count!=len(names) or len(data)!=4*count:raise ValueError('Model registry arrays have different lengths')
 values=struct.unpack('<'+'I'*len(names),p[KEYS][2])
 if list(values)!=[slot_hash(name) for name in names]:raise ValueError('Model names and hashes disagree')
 return names
def extend_registry(p,newslots,sources=None):
 names=validate_registry(p);rows={name:[struct.unpack_from('<I',p[k][2],i*4)[0] for k in ARRAYS] for i,name in enumerate(names)}
 for name,setting in newslots.items():
  if name in rows:raise ValueError('Hidden model name already exists')
  source=sources[name] if sources is not None else name.replace('_901','_001')
  if source not in rows:raise ValueError('Missing source model for hidden slot: '+source)
  values=list(rows[source]);values[0]=slot_hash(name);values[1]=setting;rows[name]=values
 order=sorted(rows);blob=b''.join(name.encode('ascii')+b'\0' for name in order)
 result={NAMES:(1,len(blob),blob)}
 for i,key in enumerate(ARRAYS):result[key]=(5,len(order),struct.pack('<'+'I'*len(order),*(rows[n][i] for n in order)))
 validate_registry(result);return result

class PrivateSlotNames:
 """Reserve distinct names and hashes across all mods in one generation.

 Names retain the native character/part prefix. Their source is explicit;
 numeric suffixes must never be used to infer the original costume.
 """
 def __init__(self,names):
  self.names=set(names);self.hashes={slot_hash(n) for n in names};self.sources={}
 def allocate(self,source):
  import re
  match=re.fullmatch(r'([A-Z0-9]+_(?:COS|FACE|HAIR)_)[0-9]+[a-z]?',source)
  if not match or source not in self.names:raise ValueError('Unknown source model: '+source)
  for number in range(901,1000000):
   name=match[1]+str(number)
   key=slot_hash(name)
   if name not in self.names and key not in self.hashes:
    self.names.add(name);self.hashes.add(key);self.sources[name]=source
    return name
  raise ValueError('Private model namespace exhausted')
