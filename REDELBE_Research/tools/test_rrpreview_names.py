from pathlib import Path
import tempfile
from srs_audio_core import output_bank_name,Document
from rrpreview import inputs
assert output_bank_name('lr_SE1_Common_SV.srsa')=='SE1_Common_SV.srsa'
assert output_bank_name('lr_unknown.srsa')=='lr_unknown.srsa'
assert output_bank_name('SE1_Common_SV.srsa')=='SE1_Common_SV.srsa'
with tempfile.TemporaryDirectory(prefix='rrpreview-names-') as td:
    root=Path(td);doc=Document('analysis/moka/lr_SE1_Common_SV.srsa')
    out=root/'export';doc.save(out)
    assert (out/'SE1_Common_SV.srsa').is_file() and (out/'SE1_Common_SV.srst').is_file()
    assert not (out/'lr_SE1_Common_SV.srsa').exists()
    check=Document(out/'SE1_Common_SV.srsa');assert check.a==doc.a and check.t==doc.t
    directory=root/'REDELBE_LR/RRPreview';directory.mkdir(parents=True)
    (directory/'lr_SE1_Common_SV.srsa').write_bytes(b'test')
    try:inputs(root)
    except ValueError as error:assert 'Unrecognized RRPreview audio filename' in str(error)
    else:raise AssertionError('Unrecognized bank was silently ignored')
print('PASS canonical save names, paired save/reopen, unknown-name guard')
