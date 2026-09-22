"""Read-only LR match-mode probe. Does not enable or change frame rate."""
import argparse
import ctypes as c
from ctypes import wintypes as w
import json
from pathlib import Path
import re
import struct
import time

p = argparse.ArgumentParser()
p.add_argument('--pid', type=int, required=True)
p.add_argument('--base', type=lambda x: int(x, 0), required=True)
p.add_argument('--sample-seconds', type=float, default=0)
args = p.parse_args()
if not 0 <= args.sample_seconds <= 30:
    raise SystemExit('Sample duration must be between zero and 30 seconds')
image = (Path(__file__).resolve().parents[2] / 'analysis/lr_updated.bin').read_bytes()
pattern = rb'\x48\x8b\x0d.{4}\x33\xc0\x48\x85\xc9\x74\x0a\x80\xb9\xf8\x08\x00\x00\x05\x0f\x92\xc0'
matches = list(re.finditer(pattern, image, re.DOTALL))
globals_found = {m.start() + 7 + struct.unpack_from('<i', m.group(), 3)[0] for m in matches}
if not matches or len(globals_found) != 1:
    raise SystemExit('Online-state pattern is missing or ambiguous; no read attempted.')
match = matches[0]
k = c.WinDLL('kernel32', use_last_error=True)
k.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
k.OpenProcess.restype = w.HANDLE
k.CloseHandle.argtypes = [w.HANDLE]
k.ReadProcessMemory.argtypes = [w.HANDLE, c.c_void_p, c.c_void_p, c.c_size_t, c.POINTER(c.c_size_t)]
k.ReadProcessMemory.restype = w.BOOL
k.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
k.QueryFullProcessImageNameW.restype = w.BOOL
handle = k.OpenProcess(0x410, False, args.pid)  # query + read only
if not handle:
    raise c.WinError(c.get_last_error())
try:
    path = c.create_unicode_buffer(32768)
    length = w.DWORD(len(path))
    if not k.QueryFullProcessImageNameW(handle, 0, path, c.byref(length)):
        raise c.WinError(c.get_last_error())
    if Path(path.value).name.lower() != 'doa6lr.exe':
        raise RuntimeError('Selected process is not DOA6LR.exe')

    def read(address, size):
        out = c.create_string_buffer(size)
        got = c.c_size_t()
        if not k.ReadProcessMemory(handle, address, out, size, c.byref(got)) or got.value != size:
            raise c.WinError(c.get_last_error())
        return out.raw

    if read(args.base, 2) != b'MZ':
        raise RuntimeError('Module base does not point to a PE image')
    for candidate in matches:
        if read(args.base + candidate.start(), len(candidate.group())) != candidate.group():
            raise RuntimeError('Live online-state predicate differs from analyzed image; stopped')
    global_rva = match.start() + 7 + struct.unpack_from('<i', match.group(), 3)[0]
    owner = struct.unpack('<Q', read(args.base + global_rva, 8))[0]
    mode = read(owner + 0x8f8, 1)[0] if owner else None
    result = {'pid': args.pid, 'path': path.value,
                      'predicate_rva': hex(match.start()), 'global_rva': hex(global_rva),
                      'match_type': mode,
                      'native_online_predicate': mode is not None and mode < 5,
                      'offline_allowlisted': False,
                      'note': 'Values >=5 are not automatically approved as offline modes.'}
    # Resolve the native application through two independent FPS accessors.
    app_globals = set()
    for site in (0x372c074, 0x372bfd4):
        expected = image[site:site + 13]
        if expected[:3] != b'\x48\x8b\x05' or read(args.base + site, 13) != expected:
            raise RuntimeError('Live application FPS accessor differs; stopped')
        app_globals.add(site + 7 + struct.unpack_from('<i', expected, 3)[0])
    if len(app_globals) != 1:
        raise RuntimeError('Application FPS accessors disagree')
    app_global = app_globals.pop()
    app = struct.unpack('<Q', read(args.base + app_global, 8))[0]
    if app:
        fields = read(app + 0x540, 0x27)
        if struct.unpack('<Q', read(args.base + app_global, 8))[0] != app:
            raise RuntimeError('Application owner changed; discard sample')
        result['application_timing'] = {
            'global_rva': hex(app_global),
            'integers_by_offset': {hex(0x540 + n): struct.unpack_from('<I', fields, n)[0]
                                   for n in range(0, 0x14, 4)},
            'floats_by_offset': {hex(0x540 + n): struct.unpack_from('<f', fields, n)[0]
                                 for n in range(0x14, 0x24, 4)},
            'flags_564_566': list(fields[0x24:0x27]),
            'note': 'Observed native fields, not proof of independently adjustable rendering.'}
    if args.sample_seconds:
        # Verified scene::get_v_sync_num callback, not a guessed global pointer.
        site = 0x23c61e8
        expected = image[site:site + 17]
        if read(args.base + site, len(expected)) != expected:
            raise RuntimeError('Live scene accessor differs from analyzed image')
        scene_global = site + 7 + struct.unpack_from('<i', expected, 3)[0]
        scene = struct.unpack('<Q', read(args.base + scene_global, 8))[0]
        if not scene:
            raise RuntimeError('No scene manager')
        start = time.perf_counter()
        initial = struct.unpack('<Q', read(scene + 0x118, 8))[0]
        steps = set()
        samples = 0
        while time.perf_counter() - start < args.sample_seconds:
            if struct.unpack('<Q', read(args.base + scene_global, 8))[0] != scene:
                raise RuntimeError('Scene owner changed during sample; discard sample')
            steps.add(struct.unpack('<I', read(scene + 0xa0, 4))[0])
            samples += 1
            time.sleep(0.01)
        last = struct.unpack('<Q', read(scene + 0x118, 8))[0]
        elapsed = time.perf_counter() - start
        result['scene_sample'] = {'seconds': elapsed, 'samples': samples,
                                  'tick_steps': sorted(steps), 'counter_delta': last - initial,
                                  'scene_ticks_per_second': (last - initial) / elapsed,
                                  'note': 'Scene counter only; this is not measured rendered FPS.'}
    print(json.dumps(result, indent=2))
finally:
    k.CloseHandle(handle)
