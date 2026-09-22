"""Regression: an EXE reader is not a game; a running exact image is."""
import ctypes,os,shutil,subprocess,time
from pathlib import Path
from ctypes import wintypes as W
from kashira_bridge import game_closed
root=Path(__file__).resolve().parents[1]/'analysis/process_guard_fixture'
root.mkdir(parents=True,exist_ok=True)
exe=root/'DOA6LR.exe'
shutil.copy2(Path(os.environ['SystemRoot'])/'System32/cmd.exe',exe)
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.CreateFileW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,ctypes.c_void_p,W.DWORD,W.DWORD,W.HANDLE];k.CreateFileW.restype=W.HANDLE
k.CloseHandle.argtypes=[W.HANDLE]
reader=k.CreateFileW(str(exe),0x80000000,1,None,3,0,None)
assert reader!=ctypes.c_void_p(-1).value
try:
    exclusive=k.CreateFileW(str(exe),0x80000000,0,None,3,0,None)
    assert exclusive==ctypes.c_void_p(-1).value,'Test must reproduce the old exclusive-access failure'
    game_closed(root)
finally:k.CloseHandle(reader)
print('PASS: existing EXE read handle does not falsely report a running game.')
child=subprocess.Popen([str(exe),'/d','/c','set /p REDELBE_TEST_WAIT='],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
    time.sleep(0.3);assert child.poll() is None
    try:game_closed(root)
    except RuntimeError as e:assert f'PID {child.pid}' in str(e),str(e)
    else:raise AssertionError('Running exact image was not blocked')
    game_closed(root/'different_installation')
    print('PASS: exact running image is blocked with PID; another installation is not.')
finally:
    child.terminate();child.communicate(timeout=5)
game_closed(root)
print('PASS: synchronization permitted after the test process exits.')
