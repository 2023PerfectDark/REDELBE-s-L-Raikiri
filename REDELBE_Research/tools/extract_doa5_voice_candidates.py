"""Extract local L1G/KOVS voice candidates; no automatic quote/pose assignment."""
from pathlib import Path
import argparse, hashlib, json, struct, subprocess

def streams(data):
    if len(data)<24 or data[:8]!=b'_L1G0000':
        raise ValueError('Not a supported L1G bank')
    total, header, reserved, count=struct.unpack_from('<4I',data,8)
    if total!=len(data) or not 0<count<=4096 or header!=24+4*count:
        raise ValueError('Invalid bank bounds')
    offsets=struct.unpack_from(f'<{count}I',data,24)
    previous=header
    for index,start in enumerate(offsets):
        end=offsets[index+1] if index+1<count else len(data)
        if start<previous or start+32>end or end>len(data) or data[start:start+4]!=b'KOVS':
            raise ValueError('Invalid KOVS entry')
        length=struct.unpack_from('<I',data,start+4)[0]
        if not 256<=length<=end-start-32:raise ValueError('Invalid Ogg length')
        ogg=bytearray(data[start+32:start+32+length])
        for i in range(256):ogg[i]^=i
        if ogg[:4]!=b'OggS':raise ValueError('Invalid decoded Ogg header')
        yield index,bytes(ogg)
        previous=end

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--game',type=Path,required=True)
    ap.add_argument('--names',type=Path,required=True);ap.add_argument('--ffmpeg',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--bank',default='005')
    a=ap.parse_args();a.output.mkdir(parents=True,exist_ok=True);report=[]
    for line in a.names.read_text().splitlines():
        fields=line.split()
        if len(fields)!=2:continue
        name,relative=fields
        if name not in [f'CHAR_VOICE_{a.bank}_{language}.l1g' for language in ('EN','JP')]:continue
        source=(a.game/relative).resolve()
        if not source.is_relative_to(a.game.resolve()):raise ValueError('Source path outside game')
        bank=source.read_bytes();language=name.rsplit('_',1)[1].split('.')[0]
        for index,ogg in streams(bank):
            target=a.output/f'voice_{a.bank}_{language}_{index:02}.ogg';target.write_bytes(ogg)
            subprocess.run([str(a.ffmpeg),'-v','error','-y','-i',str(target),'-c:a','pcm_s16le',str(target.with_suffix('.wav'))],check=True)
            report.append(dict(bank=name,index=index,language=language,source_sha256=hashlib.sha256(bank).hexdigest(),ogg=target.name,wav=target.with_suffix('.wav').name,pose_assignment=None))
    if {x['language'] for x in report}!={'EN','JP'}:raise ValueError('Both dub banks are required')
    (a.output/'inventory.json').write_text(json.dumps(report,indent=2))
    print(f'Extracted {len(report)} candidate clips; pose assignments remain unverified.')
if __name__=='__main__':main()
