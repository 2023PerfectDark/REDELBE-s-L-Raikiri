"""Run upstream PkgToolBox extraction with a read-only split-file adapter."""
import bisect
import builtins
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'external/PkgToolBox'))
from packages.package_ps4 import PackagePS4

GAME = Path(r'G:\Dead or Alive Only\SteamLibrary\steamapps\common\Dead or Alive 6 Last Round')
STEM = 'UP4108-CUSA12153_00-DOA6FULLGAME0000-A0126-V0100'
PARTS = [GAME / f'{STEM}_{i}.pkg' for i in range(8)]
OUTPUT = ROOT / 'analysis/ps4_hair_color/pkgtoolbox_test'
OUTPUT.mkdir(exist_ok=True)
native_open = builtins.open
native_size = os.path.getsize
sizes = [native_size(p) for p in PARTS]
starts = [0]
for size in sizes:
    starts.append(starts[-1] + size)

class JoinedReader(io.RawIOBase):
    def __init__(self):
        super().__init__()
        self.pos = 0
        self.files = [native_open(p, 'rb') for p in PARTS]
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, offset, whence=0):
        new = offset if whence == 0 else self.pos + offset if whence == 1 else starts[-1] + offset if whence == 2 else -1
        if new < 0: raise ValueError('invalid seek')
        self.pos = new
        return new
    def read(self, size=-1):
        remaining = max(0, starts[-1] - self.pos)
        count = remaining if size is None or size < 0 else min(size, remaining)
        chunks = []
        while count:
            index = bisect.bisect_right(starts, self.pos) - 1
            take = min(count, starts[index + 1] - self.pos)
            self.files[index].seek(self.pos - starts[index])
            data = self.files[index].read(take)
            if len(data) != take: raise EOFError('short physical part read')
            chunks.append(data)
            self.pos += take
            count -= take
        return b''.join(chunks)
    def readinto(self, buf):
        data = self.read(len(buf))
        buf[:len(data)] = data
        return len(data)
    def close(self):
        for fp in self.files: fp.close()
        super().close()

def is_joined(path):
    return isinstance(path, (str, bytes, os.PathLike)) and os.path.normcase(os.path.abspath(path)) == os.path.normcase(str(PARTS[0]))

@contextlib.contextmanager
def join_parts():
    def opened(path, mode='r', *args, **kwargs):
        if is_joined(path):
            if mode != 'rb': raise PermissionError('joined source is read only')
            return JoinedReader()
        return native_open(path, mode, *args, **kwargs)
    builtins.open = opened
    os.path.getsize = lambda path: starts[-1] if is_joined(path) else native_size(path)
    try: yield
    finally:
        builtins.open = native_open
        os.path.getsize = native_size

# Check the adapter against physical reads at every split boundary.
with JoinedReader() as joined:
    for i in range(1, 8):
        with native_open(PARTS[i - 1], 'rb') as left, native_open(PARTS[i], 'rb') as right:
            left.seek(-32, 2)
            expected = left.read(32) + right.read(32)
        joined.seek(starts[i] - 32)
        assert joined.read(64) == expected
    assert joined.seek(0, 2) == 32047955968

report = {'adapter_boundary_checks': 'passed', 'upstream_source_modified': False,
          'source_commit': '95f21e77d9f4e08fa1f2b3891df48d8791ee420b', 'results': []}
for label, path in [('delta', GAME / (STEM + '-DP.pkg')), ('full_update', PARTS[0])]:
    row = {'package': label}
    try:
        with join_parts() if label == 'full_update' else contextlib.nullcontext():
            pkg = PackagePS4(str(path))
            row['title'] = pkg.title_name
            row['title_id'] = pkg.title_id
            row['entry_count'] = len(pkg.files)
            row['dump_result'] = pkg.dump(str(OUTPUT / label / 'plaintext'))
            row['pfs_report'] = pkg.get_pfs_info()
            try:
                row['passcode_result'] = pkg.extract_with_passcode('0' * 32, str(OUTPUT / label / 'authenticated'))
            except Exception as exc:
                row['passcode_result'] = type(exc).__name__ + ': ' + str(exc)
    except Exception as exc:
        row['error'] = type(exc).__name__ + ': ' + str(exc)
        row['traceback'] = traceback.format_exc()
    report['results'].append(row)
    print(json.dumps(row, indent=2))
(OUTPUT / 'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
