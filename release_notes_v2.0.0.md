Release v2.0.0

Highlights:
- Switched OCR engine to Windows OCR API for improved special-symbol recognition (may require Windows OCR language packs).
- UI: added language buttons (中文 / 日文), yellow highlight for selected language, bold 14pt fonts, and persisted language/window geometry.
- Reduced aggressive preprocessing and improved symbol/spacing handling for CJK and Japanese kana.
- Packaged Windows executable and ZIP asset for distribution.

Install notes:
If OCR languages are not recognized, install the Windows OCR language packs (run PowerShell as Administrator):
Add-WindowsCapability -Online -Name "Language.OCR~~~zh-TW~0.0.1.0"
Add-WindowsCapability -Online -Name "Language.OCR~~~ja-JP~0.0.1.0"

Assets in this release:
- One_Sentence_OCR.exe
- One_Sentence_OCR-v2.0.0.zip
