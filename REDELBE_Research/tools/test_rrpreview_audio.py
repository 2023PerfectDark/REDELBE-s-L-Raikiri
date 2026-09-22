"""Integration verification using locally extracted Moka/LR bank fixtures."""
from pathlib import Path
from rrpreview_audio import merge,paired
from srsa_lr import u
p=Path('analysis/moka')
la,lt,ma,mt=[(p/n).read_bytes() for n in ['lr_SE1_Common_SV.srsa','lr_SE1_Common_SV.srst','mod_SE1_Common_SV.srsa','mod_SE1_Common_SV.srst']]
a,t,r=merge(la,lt,ma,mt)
assert r['changed_streams']==13 and r['preserved_lr_only']==26 and r['lr_voices']==802
old,old_t,old_a=paired(la,lt);new,new_t,new_a=paired(a,t);_,mod_t,mod_a=paired(ma,mt)
assert set(old_a)==set(new_a)
for fid,(_,record) in new_t.items():
    source=mod_t if fid in mod_t else old_t
    assert record==source[fid][1]
for (pos,e),(npos,ne) in zip(old.entries,new.entries):
    info=old.info(pos,e)
    if info['codec']=='metadata':assert e==ne
    else:
        h=info['header'];fid=u(e,8)
        if fid not in mod_t or old_t[fid][1]==mod_t[fid][1]:
            expected=bytearray(e);expected[h+52:h+56]=ne[h+52:h+56]
            assert expected==ne
assert merge(la,lt,la,lt)[:2]==(la,lt)
for bad_a,bad_t in [(ma,mt[:-1]),(ma,lt),(ma[:-1],mt)]:
    try:merge(la,lt,bad_a,bad_t)
    except ValueError:pass
    else:raise AssertionError('Accepted corrupt/mismatched bank pair')
(p/'ported_SE1_Common_SV.srsa').write_bytes(a);(p/'ported_SE1_Common_SV.srst').write_bytes(t)
print('Moka: 13 replacements, 26 LR-only voices and metadata preserved; self-merge and invalid-pair guards pass')
