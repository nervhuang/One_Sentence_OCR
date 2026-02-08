# One_Sentence_OCR

Windows OCR tool with a global hotkey and a draggable capture frame.

## Requirements

- **Windows 10 (version 1809 or later) or Windows 11**
- Python 3.9 or newer

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Notes

- Default hotkey: Ctrl+F12 (editable in the app UI).
- Minimize to tray; use the tray menu to show or exit.
- OCR uses Windows 11 built-in engine via WinRT.
