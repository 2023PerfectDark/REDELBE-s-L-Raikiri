from pathlib import Path
import tempfile,json,collections,struct
from srs_library import Library,CATEGORIES,planar_wav
from srs_audio_core import ffmpeg
lib=Library(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6\RRPreview.rdb')
assert len(lib.banks)==294 and len(lib.rows)==11880 and not lib.errors
with tempfile.TemporaryDirectory() as tmp:
 tmp=Path(tmp)
 for tag in CATEGORIES:
  row=next(r for r in lib.rows if r['category']==tag);ext,data=lib.audio(row);p=tmp/(tag+ext);p.write_bytes(data);ffmpeg(['-i',p,'-f','null','-'])
 # Check planar decoder against independent FFmpeg decode of a mono block stream.
 row=next(r for r in lib.rows if r['category']=='Character' and r['codec']=='ms-adpcm');b=lib.bank(row['bank']);p,e=next((p,e) for p,e in b.entries if b.info(p,e)['id']==f"0x{row['id']:08x}" and b.info(p,e)['codec']=='ms-adpcm');info=b.info(p,e)
 original=tmp/'mono.wav';original.write_bytes(b.audio(p,e)[1]);reference=ffmpeg(['-i',original,'-f','s16le','-'])
 decoded=planar_wav(e,info)[1][44:];assert decoded==reference,(len(decoded),len(reference))
 for channels in (2,4):
  found=False
  for fid in lib.banks:
   bank=lib.bank(fid)
   for p,e in bank.entries:
    info=bank.info(p,e)
    if info['codec']=='ms-adpcm' and info['channels']==channels:
     ext,data=planar_wav(e,info);p=tmp/f'channels{channels}.wav';p.write_bytes(data);ffmpeg(['-i',p,'-f','null','-']);found=True;break
   if found:break
  assert found
 rows=[next(r for r in lib.rows if r['category']==tag) for tag in CATEGORIES];lib.export_tracks(rows,tmp/'tracks');manifest=json.loads((tmp/'tracks/tracks.json').read_text());assert len(manifest)==4
 assert all(not r['file'].startswith('0x') for r in manifest)
report={'banks':len(lib.banks),'tracks':len(lib.rows),'categories':dict(collections.Counter(r['category'] for r in lib.rows)),'bank_errors':lib.errors,'checks':['all banks indexed','four categories decoded by FFmpeg','planar decoder matches FFmpeg mono','2/4 channel PCM accepted','readable export filenames and hash manifest']}
Path('analysis/audio/library_verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
