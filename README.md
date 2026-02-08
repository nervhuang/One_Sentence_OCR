# One_Sentence_OCR

A minimal OCR (Optical Character Recognition) application with system tray support for quickly capturing and recognizing text from any part of your screen.

## Features

- 🖥️ **System Tray Integration**: Runs minimized in the system tray for quick access
- 🖱️ **Draggable & Resizable Window**: User-friendly interface that can be moved and resized
- 📸 **Screen Area Selection**: Select any area of your screen to perform OCR
- 📋 **Clipboard Support**: Automatically copy recognized text to clipboard
- ⚡ **Fast & Lightweight**: Minimal dependencies and quick recognition

## Requirements

- Python 3.7 or higher
- Tesseract OCR engine (system dependency)

### Installing Tesseract

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## Installation

### Quick Install (Linux/macOS)

Run the automated installation script:
```bash
git clone https://github.com/nervhuang/One_Sentence_OCR.git
cd One_Sentence_OCR
chmod +x install.sh
./install.sh
```

The script will:
- Verify Python and pip installation
- Check for Tesseract OCR
- Install Python dependencies
- Run tests to verify the setup

### Manual Installation

1. Clone the repository:
```bash
git clone https://github.com/nervhuang/One_Sentence_OCR.git
cd One_Sentence_OCR
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

Or install using setup.py:
```bash
pip install -e .
```

3. Verify installation:
```bash
python3 test_setup.py
```

## Usage

Run the application:
```bash
python one_sentence_ocr.py
```

Or if installed via setup.py:
```bash
one-sentence-ocr
```

### Using the Application

1. **Starting the App**: The application will minimize to your system tray upon startup
2. **New Capture**: 
   - Right-click the tray icon and select "New Capture"
   - Or click the "New Capture" button in the main window
3. **Select Area**: Click and drag to select the screen area containing text
4. **View Results**: The recognized text will appear in the main window
5. **Copy to Clipboard**: Click "Copy to Clipboard" to copy the recognized text

### Keyboard Shortcuts

- `ESC`: Cancel area selection
- Click tray icon: Show main window

## Development

### Project Structure

```
One_Sentence_OCR/
├── one_sentence_ocr.py  # Main application file
├── requirements.txt      # Python dependencies
├── setup.py             # Installation script
├── README.md            # Documentation
└── .gitignore          # Git ignore rules
```

### Dependencies

- **PyQt5**: GUI framework for the application window and system tray
- **pytesseract**: Python wrapper for Tesseract OCR engine
- **Pillow**: Image processing library
- **pyperclip**: Cross-platform clipboard support

## Troubleshooting

### Tesseract Not Found

If you get an error about Tesseract not being found, make sure:
1. Tesseract is installed on your system
2. Tesseract is in your system PATH

On Windows, you may need to set the path manually in the code:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Display Issues on Linux

If you encounter display issues on Linux, make sure you have the required Qt platform plugins:
```bash
sudo apt-get install python3-pyqt5
```

## License

MIT License - feel free to use this project for any purpose.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
