"""Offline discovery only: named script entrypoints, signature fragments, unwind ranges."""
from pathlib import Path
import bisect, json, re, struct, sys
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
data = (root/'analysis/lr_baseline.bin').read_bytes()
nt = struct.unpack_from('<I',data,0x3c)[0]
opt = nt + 24
image_base = struct.unpack_from('<Q',data,opt+24)[0]
exception_rva, exception_size = struct.unpack_from('<II',data,opt+112+3*8)
functions = [struct.unpack_from('<III',data,p) for p in range(exception_rva,exception_rva+exception_size,12)]
starts = [f[0] for f in functions]
def function(rva):
    i = bisect.bisect_right(starts,rva)-1
    return hex(functions[i][0]) if i >= 0 and functions[i][0] <= rva < functions[i][1] else None
def offsets(needle):
    p = 0
    while True:
        p = data.find(needle,p)
        if p < 0: break
        yield p
        p += 1

strings = []
terms = ['request_character','is_cached','play_anime','set_pane_text','cos_in_p','cos_out_p','select_randomness','get_default_glasses']
if '--random' in sys.argv: terms=['random']
for term in terms:
    for pos in offsets(term.encode()):
        begin = data.rfind(b'\0',max(0,pos-100),pos)+1
        end = data.find(b'\0',pos,pos+150)
        strings.append({'term':term,'rva':hex(begin),'text':data[begin:end].decode('ascii','replace')})
targets = {int(s['rva'],16) for s in strings}
xrefs = []
for match in re.finditer(rb'[\x48\x4c]\x8d[\x05\x0d\x15\x1d\x25\x2d\x35\x3d]....',data,re.S):
    p = match.start()
    target = p+7+struct.unpack_from('<i',data,p+3)[0]
    if target in targets:
        xrefs.append({'instruction':hex(p),'target':hex(target),'function':function(p)})
patterns = {}
xml = re.sub(r'<!--.*?-->','',(root/'source/Patches/layer2.xml').read_text(),flags=re.S)
for patch in re.finditer(r'<Patch\s+name="([^"]+)"[^>]*>(.*?)</Patch>',xml,re.S):
    name, body = patch.groups()
    wanted=['PatchSRARTA','PatchSRSV','PatchSRVS','PatchSRFT'] if '--random' in sys.argv else ['PatchMRCWI','PatchLPA','PatchICM','PatchICF','LocateMO','LocateLSPTU','PatchMGDG','PatchCLRICtor']
    if name not in wanted: continue
    instructions = [s.replace(' ','') for s in re.findall(r'<Instruction\s+code="([^"]+)"',body)]
    patterns[name] = []
    for count in [2,3,4]:
        for start in range(len(instructions)-count+1):
            text = ''.join(instructions[start:start+count])
            if sum(text[i:i+2]!='XX' for i in range(0,len(text),2)) < 8: continue
            regex = b''.join(b'.' if text[i:i+2]=='XX' else re.escape(bytes.fromhex(text[i:i+2])) for i in range(0,len(text),2))
            matches = list(re.finditer(regex,data,re.S))
            if 0 < len(matches) <= 12:
                patterns[name].append({'instruction_span':[start,count],'matches':[{'rva':hex(m.start()),'function':function(m.start())} for m in matches]})
result = {'strings':strings,'xrefs':xrefs,'fragments':patterns}
(root/('analysis/random_candidates.json' if '--random' in sys.argv else 'analysis/layer2_candidates.json')).write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
