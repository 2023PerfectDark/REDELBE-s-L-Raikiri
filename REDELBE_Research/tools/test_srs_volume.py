from pathlib import Path
import tempfile,math,json
from srs_audio_core import Document,ffmpeg,levels,matched_conversion
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp);info={'rate':48000,'channels':1,'codec':'ogg'}
 ref=p/'ref.wav';quiet=p/'quiet.wav';ffmpeg(['-f','lavfi','-i','sine=frequency=600:duration=1:sample_rate=48000','-c:a','pcm_s16le',ref]);ffmpeg(['-i',ref,'-af','volume=0.1',quiet]);audio,report=matched_conversion(quiet,('.wav',ref.read_bytes()),info);out=p/'out.ogg';out.write_bytes(audio);assert abs(20*math.log10(levels(out,info)[0]/levels(ref,info)[0]))<0.3;assert abs(report['gain_db']-20)<0.1
 doc=Document('analysis/audio/SE1_Common_CHA_KOK_US.srsa');fid=next(k for k,r in doc.rows.items() if r['codec']=='ms-adpcm' and r['seconds']>.2);original=doc.a;doc.replace(fid,quiet,False);assert doc.volume_reports[fid]['status']=='Off';quiet.unlink();doc.match_replacements([fid]);first=doc.audio(fid);doc.match_replacements([fid]);assert first==doc.audio(fid);assert doc.original_a==original;assert len(doc.changes)==1
 target=p/'saved';doc.save(target);assert json.loads((target/'edit_manifest.json').read_text())['volume_matching'];doc.reset();assert doc.a==original and not doc.volume_reports and not doc.replacement_inputs
 print('PASS: RMS match within 0.3 dB; +20 dB quiet input; selected/all backend; deleted import source retained; repeated apply stable; manifest/reset')
