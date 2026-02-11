# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Add the project root to path
sys.path.insert(0, r'D:\PycharmProjects\One_Sentence_OCR')

# Collect ALL PyQt5 modules and data
hidden_imports = [
    'PyQt5',
    'pytesseract',
    'pyperclip',
    'pynput',
    'pynput.keyboard',
    'PIL',
]

# Dynamically collect all PyQt5 submodules
try:
    hidden_imports.extend(collect_submodules('PyQt5'))
except Exception as e:
    print(f"Warning: Could not collect PyQt5 submodules: {e}")

block_cipher = None

a = Analysis(
    ['one_sentence_ocr.py'],
    pathex=[],
    binaries=[
        (r'C:\Program Files\Tesseract-OCR\tesseract.exe', 'tesseract'),
    ],
    datas=[
        (r'C:\Program Files\Tesseract-OCR\tessdata', 'tessdata'),
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Collect PyQt5 data files
pyqt5_datas = collect_data_files('PyQt5')
a.datas.extend(pyqt5_datas)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
