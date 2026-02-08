@echo off
REM Installation script for One Sentence OCR (Windows)
echo ========================================
echo One Sentence OCR - Installation Script
echo ========================================
echo.

REM Check Python version
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://www.python.org/
    pause
    exit /b 1
)

python --version
echo.

REM Check pip
echo Checking pip installation...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] pip is not installed
    echo Please install pip or reinstall Python with pip enabled
    pause
    exit /b 1
)

pip --version
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo Installing Python dependencies from requirements.txt...
echo This may take a few minutes...
echo.
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.

REM Check Tesseract
echo Checking for Tesseract OCR...
tesseract --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Tesseract OCR is not installed
    echo.
    echo The application requires Tesseract OCR to work.
    echo Please download and install from:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo After installation, make sure tesseract.exe is in your PATH
    echo or set the path in the Python code.
    echo.
) else (
    tesseract --version
    echo.
    echo [OK] Tesseract OCR is installed
    echo.
)

REM Run test suite
echo Running test suite...
echo.
python test_setup.py

echo.
echo ========================================
echo Setup Information
echo ========================================
echo.
echo To run the application:
echo   python one_sentence_ocr.py
echo.
echo If you see import errors, make sure you're in the virtual environment:
echo   .venv\Scripts\activate
echo   python one_sentence_ocr.py
echo.
pause
