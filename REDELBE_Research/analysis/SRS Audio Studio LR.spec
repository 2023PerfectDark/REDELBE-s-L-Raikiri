# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:/Users/Owner/OneDrive/Documents/ChatGPT/Revers E REDELBE/REDELBE_Research/assets/srs.ico', 'assets')]
binaries = []
hiddenimports = []
tmp_ret = collect_all('tkinterdnd2')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:/Users/Owner/OneDrive/Documents/ChatGPT/Revers E REDELBE/REDELBE_Research/tools/srs_audio_studio.py'],
    pathex=['C:/Users/Owner/OneDrive/Documents/ChatGPT/Revers E REDELBE/REDELBE_Research/tools'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['C:/Users/Owner/OneDrive/Documents/ChatGPT/Revers E REDELBE/REDELBE_Research/tools/srs_bootstrap.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SRS Audio Studio LR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:/Users/Owner/OneDrive/Documents/ChatGPT/Revers E REDELBE/REDELBE_Research/assets/srs.ico'],
)
