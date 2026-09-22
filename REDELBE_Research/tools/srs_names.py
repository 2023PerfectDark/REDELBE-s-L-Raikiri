"""Decode bank-owned track names; require the name to reproduce its stored hash."""
from srsa_lr import u,AUDIO

def name_hash(name):
    value=0;power=31
    for byte in name.encode('ascii'):
        value=(value+byte*power)&0xffffffff;power=(power*31)&0xffffffff
    return value

def record_name(bank,entry):
    kind=u(entry,0)
    offset_field=24 if kind==AUDIO else 40 if kind==0x368c88bd else None
    if offset_field is None or len(entry)<offset_field+4:return ''
    offset=u(entry,offset_field)
    if not offset_field+4<=offset<len(entry):return ''
    # LR name flags differ between some banks. Try both representations, but
    # accept only terminated printable ASCII whose hash matches the record ID.
    for encrypted in (False,True):
        key=u(bank,28);decoded=bytearray()
        for byte in entry[offset:offset+1024]:
            if encrypted:
                key=(0x343fd*key+0x269ec3)&0xffffffff;byte^=(key>>16)&255
            if byte==0:
                if decoded:
                    name=decoded.decode('ascii')
                    if name_hash(name)==u(entry,8):return name
                break
            if byte<32 or byte>126:break
            decoded.append(byte)
    return ''

def bank_names(bank):
    result={};ambiguous=set()
    for _,entry in bank.entries:
        name=record_name(bank.data,entry)
        if not name:continue
        fid=u(entry,8)
        if fid in result and result[fid]!=name:ambiguous.add(fid)
        result[fid]=name
    return {fid:name for fid,name in result.items() if fid not in ambiguous}
