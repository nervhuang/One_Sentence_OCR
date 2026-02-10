# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import get_module_file_attribute, collect_submodules, collect_data_files

# Add current venv to path
venv_lib = r'D:\PycharmProjects\One_Sentence_OCR\.venv\Lib\site-packages'

a = Analysis(
    ['one_sentence_ocr.py'],
    pathex=[venv_lib],
    binaries=[],
    datas=[
        ('.venv\\Lib\\site-packages\\PyQt5', 'PyQt5'),
        ('.venv\\Lib\\site-packages\\PIL', 'PIL'),
        ('.venv\\Lib\\site-packages\\pyperclip', 'pyperclip'),
        ('.venv\\Lib\\site-packages\\pynput', 'pynput'),
    ],
    hiddenimports=[
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageGrab',
        'PIL.PngImagePlugin',
        'PIL.BmpImagePlugin',
        'PIL.TiffImagePlugin',
        'PIL.JpegImagePlugin',
        'pyperclip',
        'pyperclip.windows',
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._win32',
        'pynput.mouse',
        'pynput.mouse._win32',
        'pytesseract',
        'pkgutil',
        'distutils',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        'io',
        'threading',
        'configparser',
        'datetime',
    ],
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
