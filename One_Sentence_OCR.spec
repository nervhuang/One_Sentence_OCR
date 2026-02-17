# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# Collect PyQt5 data and binaries
pyqt_data = collect_all('PyQt5')
datas = [
    (pyqt_data[0][i][0], pyqt_data[0][i][1]) for i in range(len(pyqt_data[0]))
]
binaries = [
    (pyqt_data[1][i][0], pyqt_data[1][i][1]) for i in range(len(pyqt_data[1]))
]
hiddenimports = pyqt_data[2] + [
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'winocr',
    'winrt',
    'PIL',
    'PIL.Image',
    'pyperclip',
    'pynput',
    'pynput.keyboard',
    'configparser',
]

a = Analysis(
    ['one_sentence_ocr.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='one_sentence_ocr',
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
    icon=None,
)
