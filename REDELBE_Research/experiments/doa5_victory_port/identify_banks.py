from pathlib import Path
import sys,json,subprocess
root=Path('REDELBE_Research').resolve();sys.path[:0]=[str(root/'external/victory_asr'),str(root/'tools')]
from faster_whisper import WhisperModel
from extract_doa5_voice_candidates import streams
r=root/'experiments/doa5_victory_port';g=Path('C:/SteamLibrary/steamapps/common/Dead or Alive 5 Last Round');out=r/'bank_identification';out.mkdir(exist_ok=True)
model=WhisperModel(str(next((root/'external/victory_asr_models/models--Systran--faster-whisper-base/snapshots').iterdir())),device='cpu',compute_type='int8',cpu_threads=4)
result=[]
for line in (r/'lrs-5.19/dat/snd.dat').read_text().splitlines():
 f=line.split()
 if len(f)!=2 or not f[0].startswith('CHAR_VOICE_') or not f[0].endswith('_EN.l1g'):continue
 b=(g/f[1]).read_bytes()
 for i,ogg in streams(b):
  if i>=2:break
  p=out/f'{f[0]}_{i}.ogg';p.write_bytes(ogg);segments,_=model.transcribe(str(p),language='en',beam_size=5,condition_on_previous_text=False)
  text=' '.join(x.text for x in segments);result.append(dict(bank=f[0],index=i,text=text));print(f[0],i,text.encode('ascii','backslashreplace').decode(),flush=True)
(out/'transcripts_unverified.json').write_text(json.dumps(result,indent=2))
