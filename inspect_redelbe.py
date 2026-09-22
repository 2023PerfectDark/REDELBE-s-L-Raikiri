"""Read-only PE and XML signature triage; never loads or changes game binaries."""
from pathlib import Path
import hashlib
import json
import re
import struct
import zipfile
import xml.etree.ElementTree as ET

ARCHIVE = Path(r'C:\Users\Owner\Downloads\Compressed\redelbe_30_2.zip')
BASE = Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common')
OUT = Path(__file__).resolve().parent / 'analysis'

def pe_info(data):
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    assert data[pe:pe+4] == b'PE\0\0'
    machine, count = struct.unpack_from('<HH', data, pe+4)
    opt_size = struct.unpack_from('<H', data, pe+20)[0]
    opt = pe+24
    assert struct.unpack_from('<H', data, opt)[0] == 0x20b
    sections = []
    for i in range(count):
        off = opt+opt_size+i*40
        vs, va, size, raw = struct.unpack_from('<IIII', data, off+8)
        flags = struct.unpack_from('<I', data, off+36)[0]
        sections.append(dict(name=data[off:off+8].rstrip(b'\0').decode('ascii', 'replace'),
                             rva=va, virtual_size=vs, raw_size=size, raw_offset=raw,
                             executable=bool(flags & 0x20000000)))
    def offset(rva):
        for s in sections:
            if s['rva'] <= rva < s['rva']+max(s['virtual_size'], s['raw_size']):
                return s['raw_offset']+rva-s['rva']
        if rva < struct.unpack_from('<I', data, opt+60)[0]:
            return rva
        raise ValueError(hex(rva))
    imports = []
    import_rva = struct.unpack_from('<I', data, opt+120)[0]
    if import_rva:
        pos = offset(import_rva)
        while any(data[pos:pos+20]):
            name = offset(struct.unpack_from('<I', data, pos+12)[0])
            imports.append(data[name:data.index(b'\0', name)].decode('ascii'))
            pos += 20
    return dict(machine=hex(machine), sections=sections, imports=imports)

def signature(code):
    compact = re.sub(r'\s+', '', code).upper()
    if len(compact) % 2:
        raise ValueError(code)
    pattern = b''
    for i in range(0, len(compact), 2):
        pair = compact[i:i+2]
        if pair == 'XX':
            pattern += b'.'
        elif re.fullmatch('[0-9A-F]{2}', pair):
            pattern += re.escape(bytes.fromhex(pair))
        else:
            raise ValueError(pair)
    return re.compile(pattern, re.DOTALL)

def main():
    OUT.mkdir(exist_ok=True)
    report = {'method': 'Raw executable-section scan of concatenated XML Instruction bytes; XX wildcard. Ignores search_start, enabled settings, runtime unpacking, and patch ordering. This is triage, not a loader emulation or compatibility verdict.', 'binaries': {}, 'patches': []}
    games = {}
    for key, rel in [('DOA6', 'Dead or Alive 6/DOA6.exe'), ('DOA6LR', 'Dead or Alive 6 Last Round/DOA6LR.exe')]:
        path = BASE/rel
        data = path.read_bytes()
        info = pe_info(data)
        info.update(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        report['binaries'][key] = info
        games[key] = (data, info)
    with zipfile.ZipFile(ARCHIVE) as z:
        dll = z.read('dinput8.dll')
        installed = (BASE/'Dead or Alive 6/dinput8.dll').read_bytes()
        report['loader'] = {'sha256': hashlib.sha256(dll).hexdigest(), 'matches_installed_reference': dll == installed, **pe_info(dll)}
        report['archive_sha256'] = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
        for name in z.namelist():
            if not (name.startswith('REDELBE/Patches/') and name.endswith('.xml')):
                continue
            xml = z.read(name).decode('utf-8-sig')
            # Bundled comments contain literal '<' in attributes; normalize only
            # that invalid XML character, without changing instruction patterns.
            xml = re.sub(r'"[^"\n]*"', lambda m: m[0].replace('<', '&lt;'), xml)
            xml = re.sub(r'"(?=[A-Za-z_][\w:.-]*\s*=)', '" ', xml)
            for patch in ET.fromstring(xml).findall('Patch'):
                codes = [n.attrib['code'] for n in patch.findall('Instruction')]
                entry = {'file': name, **patch.attrib}
                if not codes:
                    entry['skipped'] = 'No Instruction elements'
                else:
                    try:
                        rx = signature(''.join(codes))
                        for key, (data, info) in games.items():
                            matches = []
                            for s in info['sections']:
                                if s['executable']:
                                    block = data[s['raw_offset']:s['raw_offset']+s['raw_size']]
                                    matches.extend(hex(s['rva']+m.start()) for m in rx.finditer(block))
                            entry[key] = matches
                    except ValueError as ex:
                        entry['skipped'] = str(ex)
                report['patches'].append(entry)
    report['summary'] = {key: {'patterns_with_matches': sum(bool(p.get(key)) for p in report['patches']), 'patterns_scanned': sum(key in p for p in report['patches'])} for key in games}
    (OUT/'redelbe_static_triage.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'summary': report['summary'], 'matches_installed_reference': report['loader']['matches_installed_reference'], 'game_imports': {k:v['imports'] for k,v in report['binaries'].items()}}, indent=2))

if __name__ == '__main__':
    main()
