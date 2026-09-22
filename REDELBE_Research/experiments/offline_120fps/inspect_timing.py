"""Read-only mapped-image timing investigation; never writes game memory."""
import argparse
import bisect
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/python_deps'))
import capstone

p = argparse.ArgumentParser()
p.add_argument('targets', nargs='+', help='hex RVA to find code references to')
p.add_argument('--output', type=Path, required=True)
args = p.parse_args()
b = (ROOT / 'analysis/lr_updated.bin').read_bytes()
pe = struct.unpack_from('<I', b, 60)[0]
opt = pe + 24
exception, size = struct.unpack_from('<II', b, opt + 112 + 24)
functions = [struct.unpack_from('<III', b, n)[:2]
             for n in range(exception, exception + size, 12)]
starts = [a for a, _ in functions]
targets = {int(x, 16) for x in args.targets}
hits = {t: set() for t in targets}
section_count = struct.unpack_from('<H', b, pe + 6)[0]
section_table = opt + struct.unpack_from('<H', b, pe + 20)[0]
for n in range(section_count):
    header = section_table + n * 40
    length, start = struct.unpack_from('<II', b, header + 8)
    flags = struct.unpack_from('<I', b, header + 36)[0]
    if not flags & 0x20000000:
        continue
    end = min(start + length, len(b))
    # Candidate encodings only; decode enclosing unwind-bounded function below.
    for prefix in (b'\x48\x8d', b'\x4c\x8d', b'\x48\x8b', b'\x4c\x8b', b'\xff\x15', b'\xff\x25', b'\xe8', b'\xe9'):
        at = start
        while True:
            at = b.find(prefix, at, end)
            if at < 0:
                break
            if prefix[0] in (0x48, 0x4c):
                if b[at + 2] & 0xc7 != 5:
                    at += 1
                    continue
                disp, total = at + 3, 7
            else:
                disp, total = at + len(prefix), len(prefix) + 4
            if at + total <= end:
                target = at + total + struct.unpack_from('<i', b, disp)[0]
                if target in hits:
                    hits[target].add(at)
            at += 1
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
report = []
for target, addresses in hits.items():
    for at in sorted(addresses):
        index = bisect.bisect_right(starts, at) - 1
        if index < 0:
            continue
        begin, end = functions[index]
        if not begin <= at < end:
            continue
        instructions = list(md.disasm(b[begin:end], begin))
        if at not in {i.address for i in instructions}:
            continue
        report.append({'target': hex(target), 'reference': hex(at),
                       'function': hex(begin), 'size': end - begin,
                       'instructions': [f'{i.address:08x} {i.mnemonic} {i.op_str}'
                                        for i in instructions]})
args.output.write_text(json.dumps(report, indent=2), encoding='utf-8')
for r in report:
    print(r['target'], r['reference'], r['function'], r['size'])
