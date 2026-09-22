"""Clone native LR material chains without mutating any original object.

This is an offline preparation primitive. It does not claim runtime isolation:
the caller must bind the returned material/model references to a distinct actor.
"""
import struct
from dok_patch import records, props, u

class Database:
    def __init__(self, data):
        self.original=bytes(data)
        self.header=bytes(data[:u(data,8)])
        self.items={}
        for r in records(data):
            if r[2] in self.items:raise ValueError('Duplicate object ID')
            self.items[r[2]]=bytes(data[r[0]:r[0]+((r[1]+3)&~3)])
        if len(self.items)!=u(data,16):raise ValueError('Object count mismatch')
        self.original_items=dict(self.items)

    def values(self, oid, key):
        b=self.items[oid];r=(0,u(b,8),u(b,12),u(b,16),u(b,20))
        found=[(t,n,o,s) for k,t,n,o,s in props(b,r) if k==key]
        if len(found)!=1:raise ValueError('Missing or duplicate property')
        t,n,o,s=found[0]
        if t!=5 or s!=4*n:raise ValueError('Expected UInt32 property')
        return list(struct.unpack_from('<'+'I'*n,b,o))

    def scalar(self,oid,key):
        v=self.values(oid,key)
        if len(v)!=1:raise ValueError('Expected scalar reference')
        return v[0]

    def clone(self, source, target, changes):
        if target in self.items:raise ValueError('Clone ID collision')
        b=bytearray(self.items[source]);r=(0,u(b,8),u(b,12),u(b,16),u(b,20))
        found=set()
        for k,t,n,o,s in props(b,r):
            if k not in changes:continue
            if k in found or t!=5 or n!=1:raise ValueError('Expected unique scalar reference')
            struct.pack_into('<I',b,o,changes[k]);found.add(k)
        if found!=set(changes):raise ValueError('Clone property missing')
        struct.pack_into('<I',b,12,target);self.items[target]=bytes(b)
        return target

    def clone_arrays(self,source,target,changes):
        if target in self.items:raise ValueError('Clone ID collision')
        b=self.items[source];r=(0,u(b,8),u(b,12),u(b,16),u(b,20))
        meta=bytearray();values=bytearray();found=set()
        for k,t,n,o,s in props(b,r):
            data=b[o:o+s]
            if k in changes:
                if t!=5:raise ValueError('Expected UInt32 reference array')
                data=struct.pack('<'+'I'*len(changes[k]),*changes[k]);n=len(changes[k]);found.add(k)
            meta+=struct.pack('<III',t,n,k);values+=data
        if found!=set(changes):raise ValueError('Array property missing')
        result=bytearray(b[:24])+meta+values
        struct.pack_into('<II',result,8,len(result),target)
        result+=b'\0'*((-len(result))%4);self.items[target]=bytes(result)
        return target

    def serialize(self):
        if any(self.items.get(k)!=v for k,v in self.original_items.items()):
            raise ValueError('An original object was modified')
        b=bytearray(self.header)
        for oid in sorted(self.items):b+=self.items[oid]
        struct.pack_into('<I',b,16,len(self.items));struct.pack_into('<I',b,24,len(b))
        return bytes(b)

class MaterialCloner:
    TEXTURE=0x6c7321d2
    TBC=0xf92c5190
    KTID=0x7a1e1ef8

    def __init__(self, databases, extract_resource, allocate_resource, reserved_resources):
        self.databases=databases;self.extract=extract_resource;self.allocate_resource=allocate_resource
        self.used_objects={oid for d in databases.values() for oid in d.items}
        self.used_resources=set(reserved_resources);self.next_object=0x0fb80000
        self.assets={};self.audit=[]

    def locate(self,oid):
        matches=[d for d in self.databases.values() if oid in d.items]
        if len(matches)!=1:raise ValueError(f'Missing/ambiguous object {oid:08x}')
        return matches[0]

    def oid(self):
        while self.next_object in self.used_objects:self.next_object+=1
        v=self.next_object;self.used_objects.add(v);return v

    def asset(self, original, payload, extension):
        fid=self.allocate_resource()
        if fid in self.used_resources:raise ValueError('Resource ID collision')
        self.used_resources.add(fid)
        self.assets[fid]={'source':original,'payload':bytes(payload),'extension':extension}
        return fid

    def binding(self,tbc,replacements,payload_override=None):
        db=self.locate(tbc);ktid=db.scalar(tbc,self.KTID)
        payload=bytearray(self.extract(ktid) if payload_override is None else payload_override)
        if len(payload)%8 or not payload:raise ValueError('Invalid texture binding table')
        seen=set()
        for off in range(0,len(payload),8):
            index,old=struct.unpack_from('<II',payload,off)
            if index in seen:raise ValueError('Duplicate texture binding index')
            seen.add(index)
            texdb=self.locate(old);oldasset=texdb.scalar(old,self.TEXTURE)
            # Keep an independent object even for textures not replaced by this mod.
            # Replaced payloads additionally receive independent file IDs.
            newasset=oldasset
            if oldasset in replacements:
                newasset=self.asset(oldasset,replacements[oldasset],'.g1t')
            newoid=texdb.clone(old,self.oid(),{self.TEXTURE:newasset})
            struct.pack_into('<I',payload,off+4,newoid)
            self.audit.append({'texture_object':old,'private_object':newoid,'original_resource':oldasset,'private_resource':newasset})
        newktid=self.asset(ktid,payload,'.ktid')
        return db.clone(tbc,self.oid(),{self.KTID:newktid})

    def material(self,mbe,replacements):
        db=self.locate(mbe)
        tbc=self.binding(db.scalar(mbe,self.TBC),replacements)
        return db.clone(mbe,self.oid(),{self.TBC:tbc})
