"""Exclude game-local proxy DLLs before importing audio or UI extensions."""
import os,sys,ctypes,faulthandler
from pathlib import Path
if os.name=='nt':
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.SetDefaultDllDirectories.argtypes=[ctypes.c_uint32]
    kernel.SetDefaultDllDirectories.restype=ctypes.c_int
    if not kernel.SetDefaultDllDirectories(0x800|0x400):raise ctypes.WinError(ctypes.get_last_error())
    _dll_directory=os.add_dll_directory(getattr(sys,'_MEIPASS',str(Path(sys.executable).parent)))
    _system_audio=ctypes.WinDLL(str(Path(os.environ['SystemRoot'])/'System32/winmm.dll'))
    logdir=Path(os.environ.get('LOCALAPPDATA',Path.home()))/'SRS Audio Studio LR'
    try:
        logdir.mkdir(parents=True,exist_ok=True)
        _crash_log=(logdir/'crash.log').open('a',encoding='utf8');faulthandler.enable(_crash_log)
    except OSError:pass
