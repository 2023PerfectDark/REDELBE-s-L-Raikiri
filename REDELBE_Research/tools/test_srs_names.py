from pathlib import Path
import json,tempfile
from srsa_lr import Bank,u,put,AUDIO
from srs_names import bank_names,record_name,name_hash
from srs_audio_core import Document,batch_files,rrpreview_game
count=0
for path in [Path('analysis/moka/lr_SE1_Common_SV.srsa'),Path('analysis/moka/mod_SE1_Common_SV.srsa'),*Path('analysis/audio').glob('*.srsa')]:
    raw=path.read_bytes();bank=Bank(raw);names=bank_names(bank)
    for _,entry in bank.entries:
        if u(entry,0)!=AUDIO:continue
        fid=u(entry,8);assert names[fid] and name_hash(names[fid])==fid;count+=1
        bad=bytearray(entry);put(bad,24,len(bad)+100)
        assert record_name(raw,bad)==''
        bad=bytearray(entry);put(bad,8,fid^1)
        assert record_name(raw,bad)==''
    assert path.read_bytes()==raw
doc=Document('analysis/moka/lr_SE1_Common_SV.srsa')
assert doc.rows[0x4aa124ab]['name']=='sv_system_default_doa6_cappear'
with tempfile.TemporaryDirectory(prefix='srs-names-') as td:
    out=Path(td)/'tracks';doc.export(out)
    rows=json.loads((out/'tracks.json').read_text());row=next(r for r in rows if r['id']=='0x4aa124ab')
    assert row['file']=='sv_system_default_doa6_cappear.ogg'
    assert (out/row['file']).is_file()
    assert len(batch_files(out,doc.rows))==802
    assert batch_files(out,doc.rows)[0x4aa124ab].name==row['file']
    (out/'tracks.json').unlink()
    assert len(batch_files(out,doc.rows))==802
    duplicate=out/'0x4aa124ab.ogg';duplicate.write_bytes(b'duplicate')
    try:batch_files(out,doc.rows)
    except ValueError:pass
    else:raise AssertionError('Accepted duplicate readable/hash ID')
    game=Path(td)/'game';game.mkdir();(game/'DOA6LR.exe').write_bytes(b'fixture')
    assert rrpreview_game(game/'REDELBE_LR/RRPreview/newfolder')==game.resolve()
    assert rrpreview_game(out) is None
print('PASS',count,'audio names verified against stored hashes, invalid pointers/hash mismatches rejected, named export confirmed')
