"""MP3/WAV/OGG conversion across real embedded and streamed LR bank fixtures."""
from pathlib import Path
import hashlib,json,tempfile
from srs_audio_core import Document,ffmpeg,replace_external
from srsa_lr import Bank,read_wav,ogg_info

fixtures=Path('analysis');report=[]
with tempfile.TemporaryDirectory(prefix='srs-studio-test-') as tmp:
    root=Path(tmp);inputs=[]
    for ext,codec in [('wav','pcm_s16le'),('mp3','libmp3lame'),('ogg','libvorbis')]:
        path=root/('input.'+ext)
        ffmpeg(['-f','lavfi','-i','sine=frequency=620:sample_rate=44100:duration=0.31','-ac','2','-c:a',codec,path]);inputs.append(path)
    banks=[fixtures/'audio/SE1_Common_CHA_KOK_US.srsa',fixtures/'audio/EV_BAY.srsa',fixtures/'moka/lr_SE1_Common_SV.srsa']
    # Document resolves a pair by matching basename, just as the GUI does.
    pair=root/'SE1_Common_SV.srsa';pair.write_bytes(banks[2].read_bytes());pair.with_suffix('.srst').write_bytes((fixtures/'moka/lr_SE1_Common_SV.srst').read_bytes());banks[2]=pair
    for bankpath in banks:
        source_hash=hashlib.sha256(bankpath.read_bytes()).hexdigest()
        for audio in inputs:
            doc=Document(bankpath);fid=next(iter(doc.rows));before=doc.rows[fid].copy()
            old_other={k:hashlib.sha256(doc.audio(k)[1]).hexdigest() for k in doc.rows if k!=fid}
            doc.replace(fid,audio);ext,data=doc.audio(fid);converted=root/('check'+ext);converted.write_bytes(data)
            ffmpeg(['-i',converted,'-f','null','-']) # Independent FFmpeg decoder accepts every generated format.
            assert doc.rows[fid]['rate']==before['rate'] and doc.rows[fid]['channels']==before['channels']
            if ext=='.wav':assert read_wav(data)['block']==70
            assert old_other=={k:hashlib.sha256(doc.audio(k)[1]).hexdigest() for k in doc.rows if k!=fid}
            target=root/(bankpath.stem+'_'+audio.suffix[1:]);doc.save(target);loaded=Document(target/bankpath.name)
            assert loaded.audio(fid)==doc.audio(fid)
            try:doc.save(target)
            except ValueError:pass
            else:raise AssertionError('Overwrote existing output')
            doc.reset();assert doc.a==doc.original_a and doc.t==doc.original_t
            assert hashlib.sha256(bankpath.read_bytes()).hexdigest()==source_hash
            report.append({'bank':bankpath.name,'input':audio.suffix,'target':before['codec'],'sample_rate':before['rate'],'channels':before['channels'],'unrelated_audio_preserved':len(old_other)})
    doc=Document(banks[0]);fid=next(iter(doc.rows));original=doc.a
    bad=root/'bad.mp3';bad.write_bytes(b'not audio')
    try:doc.replace(fid,bad)
    except ValueError:pass
    else:raise AssertionError('Accepted invalid audio')
    assert doc.a==original
    doc.export(root/'extract');assert (root/'extract/tracks.json').is_file()
    missing=root/'missing.srsa';missing.write_bytes(banks[2].read_bytes())
    try:Document(missing)
    except ValueError:pass
    else:raise AssertionError('Accepted missing SRST')
Path('analysis/audio/studio_verification.json').write_text(json.dumps(report,indent=2))
print('PASS:',len(report),'format conversions; unrelated audio, save/reopen, source immutability, invalid input, extraction and missing-pair guards')
