"""Scan the supplied REDELBE XML signatures in a read-only runtime snapshot."""
import sys, json, re, xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from inspect_redelbe import signature
sys.path.insert(0, str(Path(__file__).resolve().parent/'python_deps'))
import pefile

base=Path(__file__).resolve().parents[1]
inp=Path(sys.argv[1]); data=inp.read_bytes(); pe=pefile.PE(data=data, fast_load=True)
sections=[dict(rva=s.VirtualAddress,virtual_size=s.Misc_VirtualSize,executable=bool(s.Characteristics & 0x20000000)) for s in pe.sections]
report=[]
for path in (base/'original/REDELBE/Patches').glob('*.xml'):
    xml=path.read_text(encoding='utf-8-sig')
    xml=re.sub(r'"[^"\n]*"',lambda m:m[0].replace('<','&lt;'),xml)
    xml=re.sub(r'"(?=[A-Za-z_][\w:.-]*\s*=)','" ',xml)
    for p in ET.fromstring(xml).findall('Patch'):
        codes=[n.attrib['code'] for n in p.findall('Instruction')]
        if not codes: continue
        rx=signature(''.join(codes)); matches=[]
        for s in sections:
            if s['executable']:
                matches.extend(hex(s['rva']+m.start()) for m in rx.finditer(data[s['rva']:s['rva']+s['virtual_size']]))
        report.append(dict(file=path.name,**p.attrib,matches=matches))
out=inp.with_suffix('.signatures.json'); out.write_text(json.dumps(report,indent=2))
print(json.dumps(dict(scanned=len(report),matched=sum(bool(p['matches']) for p in report),unique=sum(len(p['matches'])==1 for p in report),results=[p for p in report if p['matches']]),indent=2))
