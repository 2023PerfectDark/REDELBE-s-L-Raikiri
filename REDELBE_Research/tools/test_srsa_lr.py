"""Real-bank extraction, identity roundtrip and changed-length replacement tests."""
from pathlib import Path
import struct,json
from srsa_lr import Bank,read_wav,chunk,ogg_info,u
root=Path('analysis/audio');counts={'banks':0,'wav':0,'ogg':0,'external':0,'changed_length_tests':0}
for path in root.glob('*.srsa'):
 bank=Bank(path.read_bytes());counts['banks']+=1;ogg_tracks=[];tested_wav=False
 for p,e in bank.entries:
  info=bank.info(p,e)
  if info['codec']=='external-ogg':counts['external']+=1;continue
  if info['codec'] not in ('ms-adpcm','ogg'):continue
  ext,b=bank.audio(p,e);counts['wav' if ext=='.wav' else 'ogg']+=1
  assert bank.replace(int(info['id'],16),b)==bank.data
  if ext=='.ogg':ogg_info(b);ogg_tracks.append((p,e,b))
  elif not tested_wav:
   w=read_wav(b);padded=b[12:70] # fmt chunk (8 + 50 bytes)
   body=b'WAVE'+padded+chunk(b'fact',struct.pack('<I',w['samples_per_block']))+chunk(b'data',w['data'][:w['block']])
   replacement=b'RIFF'+struct.pack('<I',len(body))+body
   result=bank.replace(int(info['id'],16),replacement)
   assert len(result)!=len(bank.data);Bank(result)
   (root/'Kokoro_ADPCM_replacement_test.srsa.test').write_bytes(result)
   counts['changed_length_tests']+=1;tested_wav=True
 if len(ogg_tracks)>1:
  first=ogg_tracks[0];other=next((t for t in ogg_tracks[1:] if len(t[2])!=len(first[2])),None)
  if other:
   result=bank.replace(u(first[1],8),other[2]);check=Bank(result)
   assert len(result)!=len(bank.data)
   assert check.audio(*next(t for t in check.entries if u(t[1],0)==0x70cbccc5 and u(t[1],8)==u(first[1],8)))[1]==other[2]
   counts['changed_length_tests']+=1
# Corrupt entry lengths are rejected instead of hanging or overwriting inputs.
bad=bytearray(bank.data);struct.pack_into('<I',bad,84,0)
try:Bank(bad);raise AssertionError('Malformed bank accepted')
except ValueError:pass
(root/'verification.json').write_text(json.dumps(counts,indent=2));print('PASS',counts)
