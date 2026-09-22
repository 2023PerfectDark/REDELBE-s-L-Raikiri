from pathlib import Path
import sys,os,json
root=Path('REDELBE_Research').resolve();sys.path.insert(0,str(root/'external/victory_asr'))
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING']='1'
from faster_whisper import WhisperModel
model=WhisperModel('base',device='cpu',compute_type='int8',cpu_threads=4,download_root=str(root/'external/victory_asr_models'))
p=root/'experiments/doa5_victory_port/audio_candidates';result=[]
for f in sorted(p.glob('*.wav')):
 lang='en' if '_EN_' in f.name else 'ja'
 segments,info=model.transcribe(str(f),language=lang,beam_size=5,condition_on_previous_text=False,vad_filter=False)
 text=' '.join(s.text for s in segments);result.append(dict(file=f.name,text=text,language=lang,verification='automatic transcription; verify against original event data'))
 print(f.name,text.encode('ascii','backslashreplace').decode(),flush=True)
(p/'transcripts_unverified.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf8')
