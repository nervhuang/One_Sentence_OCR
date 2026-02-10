# -*- mode: python ; coding: utf-8 -*-
import os

# Use the project's virtual environment
venv_path = r'D:\PycharmProjects\One_Sentence_OCR\.venv'
site_packages = os.path.join(venv_path, r'Lib\site-packages')
pyqt5_path = os.path.join(site_packages, 'PyQt5')

a = Analysis(
    ['one_sentence_ocr.py'],
    pathex=[],
    binaries=[
        (r'C:\Program Files\Tesseract-OCR\tesseract.exe', 'tesseract'),
    ],
    datas=[
        (r'C:\Program Files\Tesseract-OCR\tessdata', 'tessdata'),
        # Include PyQt5 plugins and libraries
        (os.path.join(pyqt5_path, 'Qt5', 'plugins'), 'PyQt5/Qt5/plugins'),
        (os.path.join(pyqt5_path, 'Qt5', 'bin'), 'PyQt5/Qt5/bin'),
        (os.path.join(pyqt5_path, 'Qt5', 'qml'), 'PyQt5/Qt5/qml'),
        (os.path.join(pyqt5_path, 'Qt5', 'translations'), 'PyQt5/Qt5/translations'),
    ],
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui', 
        'PyQt5.QtWidgets',
        'PyQt5.sip',
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
