# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['one_sentence_ocr.py'],
    pathex=[],
    binaries=[],
    datas=[('.venv\\Lib\\site-packages\\PyQt5', 'PyQt5')],
    hiddenimports=['pkgutil', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'distutils'],
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
    [],
    exclude_binaries=True,
    name='One_Sentence_OCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='One_Sentence_OCR',
)
