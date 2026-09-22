from pathlib import Path
import tempfile
from srs_audio_core import Document
from srs_pairs import choose_inputs

root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as folder:
    folder=Path(folder)
    a=(root/'analysis/moka/lr_SE1_Common_SV.srsa').read_bytes()
    t=(root/'analysis/moka/lr_SE1_Common_SV.srst').read_bytes()
    bank=folder/'BGM.SRSA';stream=folder/'BGM.SRST'
    bank.write_bytes(a);stream.write_bytes(t)
    first=Document(bank);second=Document(stream)
    assert first.rows==second.rows
    fid=next(iter(first.rows));assert first.audio(fid)==second.audio(fid)
    raw=folder/'Raw.srsa';rawstream=folder/'Raw.srst'
    raw.write_bytes(a[16:]);rawstream.write_bytes(t[16:])
    doc=Document(rawstream);assert doc.audio(fid)==first.audio(fid)
    doc.save(folder/'saved')
    assert (folder/'saved/Raw.srsa').read_bytes()==a[16:]
    assert (folder/'saved/Raw.srst').read_bytes()==t[16:]
    renamed=folder/'elsewhere.srst';stream.rename(renamed)
    calls=[]
    def picker(title,suffix):calls.append(suffix);return renamed
    picked,pair=choose_inputs(bank,picker)
    assert calls==['.srst'] and Document(picked,pair).audio(fid)==first.audio(fid)
    try:Document(renamed)
    except ValueError as exc:assert 'requires' in str(exc)
    else:raise AssertionError('SRST opened without SRSA')
print('Paired open, SRST entry, uppercase filenames, missing-pair picker, raw KTSR and unchanged save passed')
