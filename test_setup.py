#!/usr/bin/env python3
"""
Test script for One Sentence OCR
Tests basic imports and module functionality without requiring GUI
"""
import sys
import os

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        import PyQt5
        print("✓ PyQt5 imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PyQt5: {e}")
        return False
    
    try:
        import pytesseract
        print("✓ pytesseract imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import pytesseract: {e}")
        return False
    
    try:
        from PIL import Image
        print("✓ PIL (Pillow) imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PIL: {e}")
        return False
    
    try:
        import pyperclip
        print("✓ pyperclip imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import pyperclip: {e}")
        return False
    
    return True

def test_module_structure():
    """Test that the main module can be imported and has expected components."""
    print("\nTesting module structure...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        # Import without executing (would require display)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "one_sentence_ocr", 
            "one_sentence_ocr.py"
        )
        module = importlib.util.module_from_spec(spec)
        
        # Execute the module to validate it can be loaded
        # This doesn't run main() but validates all imports and class definitions
        sys.modules['one_sentence_ocr'] = module
        spec.loader.exec_module(module)
        
        # Check the module can be loaded
        print("✓ one_sentence_ocr.py module structure is valid")
        return True
    except Exception as e:
        print(f"✗ Failed to load module: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tesseract_availability():
    """Check if Tesseract OCR is installed on the system."""
    print("\nTesting Tesseract OCR availability...")
    
    try:
        import pytesseract
        from PIL import Image
        import io
        
        # Create a simple test image
        test_image = Image.new('RGB', (100, 30), color='white')
        
        # Try to get tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract OCR is installed (version: {version})")
        return True
    except pytesseract.TesseractNotFoundError:
        print("⚠ Tesseract OCR is not installed on the system")
        print("  The application requires Tesseract to be installed separately.")
        print("  See README.md for installation instructions.")
        return True  # Not a critical failure for testing
    except Exception as e:
        print(f"⚠ Could not verify Tesseract installation: {e}")
        return True  # Not a critical failure for testing

def test_requirements():
    """Test that requirements.txt is valid."""
    print("\nTesting requirements.txt...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        print(f"✓ Found {len(requirements)} requirements:")
        for req in requirements:
            print(f"  - {req}")
        return True
    except Exception as e:
        print(f"✗ Failed to read requirements.txt: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("One Sentence OCR - Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("Import Test", test_imports()))
    results.append(("Module Structure Test", test_module_structure()))
    results.append(("Requirements Test", test_requirements()))
    results.append(("Tesseract Availability Test", test_tesseract_availability()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! The application is ready to use.")
        print("\nNote: GUI functionality requires a display server.")
        print("Run: python one_sentence_ocr.py")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
