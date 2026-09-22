import sys
sys.path.insert(0,'tools')
from audit_ayane_import import resources
from lr_resources import extract
from dok_patch import records,props
b=extract(*resources[0x6d011726][0])
for r in records(b):
 if r[3]==0xdac911d7:
  for k,t,n,p,l in props(b,r):
   if k==0x4d269345:
    names=b[p:p+l].decode('ascii').split('\0');print('names',len(names),'hair',sum('_HAIR_' in x for x in names),'face',sum('_FACE_' in x for x in names));print([s for s in names if 'KAS_HAIR' in s][:10])
