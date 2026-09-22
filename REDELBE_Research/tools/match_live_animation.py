"""Compare observed compact animation headers with local game resources.

Read-only: names are reported only when header and converted bone table match.
This does not establish that a clip is unused or safe to play on another model.
"""
import argparse, csv, json, struct
from pathlib import Path
from lr_resources import read_index, extract

def compact_g1a(data):
    if len(data)<32 or data[:8] not in (b'_A2G0300',b'_A2G0400',b'_A2G0500'):
        raise ValueError('Unsupported animation format')
    size,fps,frames,packed_bones,key_size,vectors=struct.unpack_from('<IfHHII',data,8)
    bones=packed_bones>>4
    if size!=len(data) or not 0<fps<=240 or not frames or not 0<bones<=1024:
        raise ValueError('Invalid animation header')
    header=28 if data[4:8]==b'0300' else 32
    key_start=header+bones*4
    vector_start=key_start+key_size
    if vector_start+vectors*32>len(data):raise ValueError('Invalid section bounds')
    table=bytearray(data[header:key_start])
    # LR's compact 0400 payload retains the original table encoding. Its
    # version flag selects the decoder; do not apply the editor's 0500 conversion.
    return fps,frames,bones,bytes(table)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('game',type=Path);ap.add_argument('snapshot',type=Path)
    ap.add_argument('--character',default='HON');a=ap.parse_args()
    snapshot=json.loads(a.snapshot.read_text());wanted=[]
    for sample in snapshot['samples']:
        obj=next((x for x in sample['objects'] if x['label']=='motion_payload'),None)
        if not obj:continue
        raw=bytes.fromhex(obj['raw'])
        if len(raw)<64:continue
        fps,frames=struct.unpack_from('<fH',raw);bones=struct.unpack_from('<H',raw,8)[0]
        wanted.append((fps,frames,bones,raw[48:48+bones*4],obj['address']))
    names={}
    with (a.game/'KashiraProjects/Name2Hash/DOA6LR.csv').open(encoding='utf-8-sig') as f:
        for row in csv.reader(f):
            if len(row)==2 and row[1].startswith(a.character) and row[1].lower().endswith('.g1a'):
                names[int(row[0],16)]=row[1]
    matches=[];errors=0;checked=0
    for db in ('root','system'):
        path=a.game/'fdata_package'/f'{db}.rdb'
        for entry in read_index(path)[1]:
            if entry['id'] not in names:continue
            try:fps,frames,bones,table=compact_g1a(extract(path,entry))
            except (ValueError,OSError):errors+=1;continue
            checked+=1
            for f,n,b,t,address in wanted:
                if (fps,frames,bones)==(f,n,b) and table==t:
                    matches.append(dict(name=names[entry['id']],id=hex(entry['id']),payload=address))
    print(json.dumps(dict(checked=checked,unsupported_or_unavailable=errors,matches=matches),indent=2))
if __name__=='__main__':main()
