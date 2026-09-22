# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:/Users/Owner/OneDrive/Documents/ChatGPT/Revers E REDELBE/REDELBE_Research/tools/animation_library_setup.py'],
    pathex=['C:/Users/Owner/OneDrive/Documents/ChatGPT/Revers E REDELBE/REDELBE_Research/tools'],
    binaries=[],
    datas=[('C:/Users/Owner/OneDrive/Documents/ChatGPT/Revers E REDELBE/REDELBE_Research/tools/animation_names.json', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    name='Prepare Animation Library',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
