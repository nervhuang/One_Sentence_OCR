#!/bin/bash
# Installation verification script for One Sentence OCR

echo "========================================"
echo "One Sentence OCR - Installation Check"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ $PYTHON_VERSION found"
else
    echo "✗ Python 3 is not installed"
    exit 1
fi

# Check pip
echo ""
echo "Checking pip..."
if command -v pip3 &> /dev/null || command -v pip &> /dev/null; then
    if command -v pip3 &> /dev/null; then
        PIP_VERSION=$(pip3 --version)
    else
        PIP_VERSION=$(pip --version)
    fi
    echo "✓ $PIP_VERSION found"
else
    echo "✗ pip is not installed"
    exit 1
fi

# Check Tesseract OCR
echo ""
echo "Checking Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -n 1)
    echo "✓ $TESSERACT_VERSION found"
else
    echo "✗ Tesseract OCR is not installed"
    echo ""
    echo "Please install Tesseract OCR:"
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "  macOS: brew install tesseract"
    echo "  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki"
    echo ""
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt
else
    pip install -r requirements.txt
fi

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Run test suite
echo ""
echo "Running test suite..."
python3 test_setup.py

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✓ Installation verified successfully!"
    echo "========================================"
    echo ""
    echo "To run the application:"
    echo "  python3 one_sentence_ocr.py"
    echo ""
    exit 0
else
    echo ""
    echo "✗ Installation verification failed"
    exit 1
fi
