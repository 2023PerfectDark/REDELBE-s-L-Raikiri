"""Build reversible, native-resource Kasumi match test profiles."""
from pathlib import Path
import json, struct, zlib
import math
import numpy as np
from port_kasumi_victories import pack, unpack
from lr_resources import GAME, read_index, extract
from rrpreview_names import NAMES

ROOT = Path(__file__).resolve().parents[1]/'experiments/doa5_victory_port'
OUT = ROOT/'match_test'
SOURCE = ROOT/'prototype'

def match_rate(data):
    """Encode the same motion on LR's 60-frame match timeline."""
    out = bytearray(data)
    fps, end, packed = struct.unpack_from('<fHH',out,12)
    assert fps == 30 and end < 32768
    bones = packed >> 4
    table_end = 32 + bones*4
    for i in range(bones):
        entry = struct.unpack_from('<I',out,32+i*4)[0]
        pos = table_end + (entry >> 16)*4
        for _ in range(entry & 15):
            _, count, _ = struct.unpack_from('<HHI',out,pos)
            for j in range(count):
                at = pos+8+j*2
                key = struct.unpack_from('<H',out,at)[0]
                assert key <= end
                struct.pack_into('<H',out,at,key*2)
            pos = (pos+8+count*2+3)&~3
    struct.pack_into('<fH',out,12,60.,end*2)
    assert (end*2)/60 == end/fps
    return bytes(out)

def match_camera(data, original):
    """Keep ported camera motion, extending its constant tail to the LR slot."""
    out = bytearray(data)
    duration = max(struct.unpack_from('<f',data,16)[0],
                   struct.unpack_from('<f',original,16)[0])
    table = (struct.unpack_from('<I',out,32)[0]+2)*16
    track = table+struct.unpack_from('<i',out,table+8)[0]*16
    assert struct.unpack_from('<I',out,track)[0] == 102
    for channel in range(9):
        count, offset = struct.unpack_from('<ii',out,track+4+channel*8)
        coeff = track+offset*16
        times = coeff+count*16
        assert count > 0 and times+count*4 <= len(out)
        # Exporter already writes a constant final segment. Extend only that
        # segment; all preceding source camera motion stays byte-identical.
        assert struct.unpack_from('<3f',out,coeff+(count-1)*16) == (0.,0.,0.)
        old_end = struct.unpack_from('<f',out,times+(count-1)*4)[0]
        struct.pack_into('<f',out,times+(count-1)*4,max(old_end,duration+1/60))
    struct.pack_into('<f',out,16,duration)
    return bytes(out)

def hold_body(data, original, loop=False):
    """Append a held pose through the original slot's full frame range."""
    fps,end,packed=struct.unpack_from('<fHH',data,12)
    oldfps,oldend=struct.unpack_from('<fH',original,12)
    target=max(end,round(oldend/oldfps*fps))
    if loop:target=max(target,end+60)
    assert target < 65536
    if target == end:return data
    bones=packed>>4; keybase=32+bones*4
    oldkeys=struct.unpack_from('<I',data,20)[0]
    vectorbase=keybase+oldkeys
    keys=bytearray(); vectors=bytearray(); table=[]
    for i in range(bones):
        entry=struct.unpack_from('<I',data,32+i*4)[0]
        table.append(((len(keys)//4)<<16)|(entry&65535))
        pos=keybase+(entry>>16)*4
        for _ in range(entry&15):
            op,count,first=struct.unpack_from('<HHI',data,pos)
            times=list(struct.unpack_from('<'+str(count)+'H',data,pos+8))
            values=data[vectorbase+first*32:vectorbase+(first+count)*32]
            assert len(values)==count*32
            # Generated terminal polynomial is constant; retain its value.
            assert values[-24:]==bytes(24)
            newfirst=len(vectors)//32
            if loop:
                first_value=unpack(struct.unpack_from('<Q',values,0)[0])
                last_value=unpack(struct.unpack_from('<Q',values,len(values)-32)[0])
                start=max(end,target-60)
                if times[-1]<start:
                    times.append(start);values+=values[-32:]
                def quat(v):
                    n=np.linalg.norm(v)
                    return np.r_[v*(math.sin(n/2)/n if n>1e-9 else .5),math.cos(n/2)]
                qa,qb=quat(last_value),quat(first_value)
                if np.dot(qa,qb)<0:qb=-qb
                def at(t):
                    if t>=1:return first_value
                    s=t*t*(3-2*t)
                    if op!=0:return last_value+(first_value-last_value)*s
                    # LR interpolates stored rotation vectors. Converting a
                    # quaternion back across its sign branch can insert a 2pi
                    # jump before the final key. Stay in the source vector
                    # branch throughout the return, including the endpoint.
                    return last_value+(first_value-last_value)*s
                # Replace the terminal constant with a smooth return, then
                # end on exactly the first pose so the wrap has no pose jump.
                values=values[:-32]; times=times[:-1]
                for frame in range(start,target+1):
                    v=at((frame-start)/(target-start)); nextv=at(min(1,(frame+1-start)/(target-start)))
                    times.append(frame);values+=struct.pack('<4Q',pack(v),pack(nextv-v),0,0)
                vectors+=values
            else:
                times.append(target);vectors+=values+values[-32:]
            keys+=struct.pack('<HHI',op,len(times),newfirst)+struct.pack('<'+str(len(times))+'H',*times)
            keys+=bytes((-len(keys))%4)
            pos=(pos+8+count*2+3)&~3
    out=bytearray(data[:32])+struct.pack('<'+str(bones)+'I',*table)+keys+vectors
    struct.pack_into('<I',out,8,len(out));struct.pack_into('<H',out,16,target)
    struct.pack_into('<II',out,20,len(keys),len(vectors)//32)
    return bytes(out)

def pull_camera_back(data, factor=1.15):
    out=bytearray(data); table=(struct.unpack_from('<I',out,32)[0]+2)*16
    track=table+struct.unpack_from('<i',out,table+8)[0]*16
    for axis in range(3):
        n,off=struct.unpack_from('<ii',out,track+4+axis*8)
        m,aimoff=struct.unpack_from('<ii',out,track+4+(axis+3)*8)
        assert n==m
        eye,aim=track+off*16,track+aimoff*16
        assert out[eye+n*16:eye+n*20]==out[aim+n*16:aim+n*20]
        for i in range(n*4):
            e=struct.unpack_from('<f',out,eye+i*4)[0];a=struct.unpack_from('<f',out,aim+i*4)[0]
            struct.pack_into('<f',out,eye+i*4,a+(e-a)*factor)
    return bytes(out)
resources = {}
for db in ('root', 'system'):
    path = GAME/'fdata_package'/f'{db}.rdb'
    for e in read_index(path)[1]:
        resources[e['id']] = (path, e)

manifest = []
for phase, numbers, slots in [('ENTRY', (100,101,102), ('7010','7110')),
                               ('WIN', (120,122,124), ('7020','7120'))]:
    for number in numbers:
        name = f'KAS_DOA5_{phase}_{number}_PORT_TEST.g1a'
        source_id = zlib.crc32(name.encode())
        for slot in slots:
            suffix = 'ent' if phase == 'ENTRY' else 'win'
            for kind, target_name in [('Clips',f'kas0{slot}_{suffix}.g1a'),
                                      ('Cameras',f'kas_camera_{slot}_{suffix}.g1a'),
                                      ('Faces',f'kas_facial_{slot}_{suffix}.g1a')]:
                source = SOURCE/('FacesDeltas' if kind=='Faces' else kind)/f'0x{source_id:08x}.g1a'
                data = source.read_bytes()
                fid = NAMES[target_name]
                original = extract(*resources[fid])
                assert data[:8] == original[:8], (source, target_name)
                data = (hold_body(match_rate(data),original,phase=='WIN') if kind == 'Clips' else
                        match_camera(pull_camera_back(data) if phase=='WIN' and number==120 else data,original) if kind == 'Cameras' else
                        hold_body(match_rate(data),extract(*resources[NAMES[f'kas0{slot}_{suffix}.g1a']]),phase=='WIN'))
                if kind != 'Cameras':
                    assert struct.unpack_from('<H',data,18)[0]>>4 == (57 if kind=='Clips' else 344)
                    assert struct.unpack_from('<I',data,8)[0] == len(data)
                dest = OUT/f'{phase}_{number}'/f'0x{fid:08x}.g1a'
                dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(data)
                manifest.append(dict(phase=phase,number=number,kind=kind,target=target_name,id=f'{fid:08x}',bytes=len(data)))
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
(OUT/'README.txt').write_text('Kasumi normal-match test\n\nDefault: ENTRY 102 and WIN 120, with 60-fps body tracks and original LR faces and ported cameras with a held final view.\nBoth native Kasumi intro/victory slots are replaced so either player can test.\nOriginal game dialogue and scene timing remain; ported faces, DOA5 voice synchronization and teleport effects are unfinished.\nUse offline Versus, allow the intro to play and have Kasumi win without skipping.\n\nClose the game before changing profiles. Run Apply match test.cmd and choose an intro and victory.\nChoose Disable to restore the normal resources. The sync step must finish successfully before launching.\nThese are resource replacements, not an offline-only runtime hook: disable before online play.\n')
print(f'Validated {len(manifest)} assets across six profiles: {OUT}')


