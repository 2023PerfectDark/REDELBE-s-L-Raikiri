"""Merge matching streamed Ogg voices into LR banks, preserving LR-only cues."""
import struct
from srsa_lr import Bank,u,put,ogg_info,wrapped

def streams(data):
    data=wrapped(data,b'TSRS')
    if len(data)<80 or data[:4]!=b'TSRS' or data[16:20]!=b'KTSR':raise ValueError('Expected SRST')
    if struct.unpack_from('<Q',data,8)[0]!=len(data) or u(data,40)!=len(data)-16 or u(data,44)!=len(data)-16:raise ValueError('SRST length mismatch')
    result={};p=80
    while p<len(data):
        if p+64>len(data):raise ValueError('Truncated SRST record')
        sig,size,fid,header,kovs=struct.unpack_from('<IIIII',data,p)
        if sig!=0x15f4d409 or header!=32 or size<64 or size%16 or p+size>len(data):raise ValueError('Unsupported SRST record')
        if data[p+32:p+36]!=b'KOVS' or kovs!=32+u(data,p+36) or kovs+32>size:raise ValueError('Invalid streamed Ogg bounds')
        if fid in result:raise ValueError('Duplicate stream ID')
        result[fid]=(p,data[p:p+size]);p+=size
    return result

def paired(srsa,srst):
    bank=Bank(srsa);table=streams(srst);audio={}
    for p,e in bank.entries:
        info=bank.info(p,e)
        if info['codec']=='metadata':continue
        if info['codec']!='external-ogg':raise ValueError('This bank is not wholly streamed Ogg')
        fid=u(e,8);h=info['header']
        if fid not in table:raise ValueError('SRSA voice missing from SRST')
        pos,stream=table[fid]
        if u(e,h+52)!=pos+16 or u(e,h+56)!=u(stream,16):raise ValueError('Mismatched SRSA/SRST pair')
        audio[fid]=(p,e,h)
    if set(audio)!=set(table):raise ValueError('Unreferenced SRST voice')
    return bank,table,audio

def merge(lr_a,lr_t,mod_a,mod_t):
    bank,original,lr_audio=paired(lr_a,lr_t)
    _,replacement,mod_audio=paired(mod_a,mod_t)
    if not (original.keys()&replacement.keys()):raise ValueError('No matching voice IDs')
    out=bytearray(lr_t[:80]);updates={};changed=0;sample_counts={};replaced=set()
    for fid,(oldpos,entry) in original.items():
        chosen=replacement.get(fid,(oldpos,entry))[1]
        if fid in replacement:
            # Validate the actual Ogg format independently of the source bank.
            payload=bytearray(chosen[64:64+u(chosen,36)])
            for i in range(min(256,len(payload))):payload[i]^=i
            channels,rate,samples=ogg_info(payload)
            _,e,h=mod_audio[fid]
            if channels!=u(e,h+12) or rate!=u(e,h+24):raise ValueError('Ogg/SRSA format mismatch')
            sample_counts[fid]=(samples+15)&~15
            if chosen[32:32+u(chosen,16)]!=entry[32:32+u(entry,16)]:
                changed+=1;replaced.add(fid)
        updates[fid]=(len(out)+16,u(chosen,16))
        out+=chosen
    struct.pack_into('<Q',out,8,len(out));put(out,40,len(out)-16);put(out,44,len(out)-16)
    a=bytearray(lr_a)
    for fid,(p,e,h) in lr_audio.items():
        if fid in replaced:
            _,me,mh=mod_audio[fid]
            for offset in (12,24,28,36):put(a,p+h+offset,u(me,mh+offset))
            put(a,p+h+28,sample_counts[fid])
        offset,size=updates[fid];put(a,p+h+52,offset);put(a,p+h+56,size)
    check,table,_=paired(bytes(a),bytes(out))
    for fid in original.keys()-replacement.keys():
        if table[fid][1]!=original[fid][1]:raise ValueError('LR-only audio changed')
    for (p,e),(q,new) in zip(bank.entries,check.entries):
        if bank.info(p,e)['codec']=='metadata' and e!=new:raise ValueError('LR cue metadata changed')
    return bytes(a),bytes(out),{'lr_voices':len(original),'matching_voices':len(original.keys()&replacement.keys()),'changed_streams':changed,'preserved_lr_only':len(original.keys()-replacement.keys()),'ignored_legacy_only':len(replacement.keys()-original.keys())}
