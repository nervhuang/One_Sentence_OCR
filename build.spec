# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['one_sentence_ocr.py'],
    pathex=[],
    binaries=[
        (r'C:\Program Files\Tesseract-OCR\tesseract.exe', 'tesseract'),
    ],
    datas=[
        (r'C:\Program Files\Tesseract-OCR\tessdata', 'tessdata'),
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'pytesseract',
        'pyperclip',
        'pynput',
        'pynput.keyboard',
        'PIL',
        'PIL.Image',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='One_Sentence_OCR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
