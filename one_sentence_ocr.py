#!/usr/bin/env python3
# type: ignore
"""
One Sentence OCR - A screenshot tool with system tray support.
Captures selected screen area and copies to clipboard.
Uses Windows OCR API for accurate text recognition.
"""
import sys
import os
import re
import threading
import configparser
import asyncio
import traceback
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QTextEdit, QMenuBar, QMainWindow)
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPixmap, QCursor, QPainter, QPen, QColor
from PIL import Image
import pyperclip
import io


def get_config_path():
    """Get the correct config.ini path for both script and exe execution."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller exe
        config_dir = os.path.dirname(sys.executable)
    else:
        # Running as Python script
        config_dir = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(config_dir, 'config.ini')


def save_selection_to_config(x, y, width, height, remove_newlines=None):
    """Save the selection box dimensions and options to config.ini"""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    
    # Read existing config or create new one
    if os.path.exists(config_path):
        config.read(config_path)
    else:
        config['selection'] = {}
    
    # Ensure sections exist
    if 'selection' not in config:
        config['selection'] = {}
    if 'options' not in config:
        config['options'] = {}
    
    # Update selection values
    config['selection']['x'] = str(x)
    config['selection']['y'] = str(y)
    config['selection']['width'] = str(width)
    config['selection']['height'] = str(height)
    config['selection']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Update options if provided
    if remove_newlines is not None:
        config['options']['remove_newlines'] = str(remove_newlines)
    
    # Write to file
    with open(config_path, 'w') as f:
        config.write(f)


def load_selection_from_config():
    """Load the last selection box dimensions from config.ini"""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    
    try:
        if os.path.exists(config_path):
            config.read(config_path)
            
            if 'selection' in config:
                x = int(config['selection'].get('x', 0))
                y = int(config['selection'].get('y', 0))
                width = int(config['selection'].get('width', 640))
                height = int(config['selection'].get('height', 360))
                return (x, y, width, height)
    except (ValueError, KeyError, configparser.Error):
        pass
    
    return None


def load_options_from_config():
    """Load options from config.ini"""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    
    try:
        if os.path.exists(config_path):
            config.read(config_path)
            
            if 'options' in config:
                remove_newlines = config['options'].get('remove_newlines', 'False')
                ocr_language = config['options'].get('ocr_language', 'chi_sim+eng')
                force_brackets = config['options'].get('force_brackets', 'False')
                return remove_newlines.lower() == 'true', ocr_language, force_brackets.lower() == 'true'
    except (ValueError, KeyError, configparser.Error):
        pass
    
    return False, 'chi_sim+eng', False


def load_hotkey_from_config():
    """Load hotkey setting from config.ini"""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    
    try:
        if os.path.exists(config_path):
            config.read(config_path)
            
            if 'hotkey' in config:
                hotkey_key = config['hotkey'].get('key', 'f12')
                hotkey_ctrl = config['hotkey'].get('ctrl', 'True').lower() == 'true'
                hotkey_alt = config['hotkey'].get('alt', 'False').lower() == 'true'
                hotkey_shift = config['hotkey'].get('shift', 'False').lower() == 'true'
                return (hotkey_key, hotkey_ctrl, hotkey_alt, hotkey_shift)
    except (ValueError, KeyError, configparser.Error):
        pass
    
    return ('f12', True, False, False)


def save_hotkey_to_config(key, ctrl=True, alt=False, shift=False):
    """Save hotkey setting to config.ini"""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    
    # Read existing config
    if os.path.exists(config_path):
        config.read(config_path)
    
    # Ensure hotkey section exists
    if 'hotkey' not in config:
        config['hotkey'] = {}
    
    # Update hotkey settings
    config['hotkey']['key'] = str(key).lower()
    config['hotkey']['ctrl'] = str(ctrl)
    config['hotkey']['alt'] = str(alt)
    config['hotkey']['shift'] = str(shift)
    
    # Write to file
    with open(config_path, 'w') as f:
        config.write(f)


def load_ocr_language_from_config():
    """Load OCR language setting from config.ini"""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    
    try:
        if os.path.exists(config_path):
            config.read(config_path)
            
            if 'options' in config:
                return config['options'].get('ocr_language', 'chi_sim+eng')
    except (ValueError, KeyError, configparser.Error):
        pass
    
    return 'chi_sim+eng'


def save_options_to_config(remove_newlines, ocr_language='chi_sim+eng', force_brackets=None):
    """Save options to config.ini"""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    
    # Read existing config
    if os.path.exists(config_path):
        config.read(config_path)
    
    # Ensure options section exists
    if 'options' not in config:
        config['options'] = {}
    
    # Update options
    config['options']['remove_newlines'] = str(remove_newlines)
    config['options']['ocr_language'] = str(ocr_language)
    
    # Update force_brackets if provided, otherwise preserve existing
    if force_brackets is not None:
        config['options']['force_brackets'] = str(force_brackets)
    elif 'force_brackets' not in config['options']:
        config['options']['force_brackets'] = 'False'
    
    # Write to file
    with open(config_path, 'w') as f:
        config.write(f)


def save_window_geometry_to_config(x, y, width, height):
    """Save window position and size to config.ini"""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    
    # Read existing config
    if os.path.exists(config_path):
        config.read(config_path)
    
    # Ensure window section exists
    if 'window' not in config:
        config['window'] = {}
    
    # Update window geometry
    config['window']['x'] = str(x)
    config['window']['y'] = str(y)
    config['window']['width'] = str(width)
    config['window']['height'] = str(height)
    
    # Write to file
    with open(config_path, 'w') as f:
        config.write(f)


def load_window_geometry_from_config():
    """Load window position and size from config.ini"""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    
    try:
        if os.path.exists(config_path):
            config.read(config_path)
            
            if 'window' in config:
                x = int(config['window'].get('x', 100))
                y = int(config['window'].get('y', 100))
                width = int(config['window'].get('width', 400))
                height = int(config['window'].get('height', 300))
                return (x, y, width, height)
    except (ValueError, KeyError, configparser.Error):
        pass
    
    return None


class OCRWorker(QObject):
    """Worker class for performing OCR using Windows OCR API (same as Win11 built-in)."""
    ocr_complete = pyqtSignal(str)
    
    # Mapping of config language codes to Windows OCR language tags
    LANGUAGE_MAP = {
        'chi_sim+eng': 'zh-Hans',      # Simplified Chinese
        'chi_tra+eng': 'zh-Hant',      # Traditional Chinese
        'chi_sim+chi_tra+eng': 'zh-Hans',  # Default to Simplified
        'chi_sim+chi_tra+jpn+eng': 'zh-Hans',  # Default to Simplified
        'jpn+eng': 'ja',               # Japanese
        'eng': 'en',                   # English
        'kor+eng': 'ko',               # Korean
    }
    
    def __init__(self):
        super().__init__()
        self.ocr_language = load_ocr_language_from_config()
    
    def set_language(self, language):
        """Set the OCR language to use."""
        self.ocr_language = language
    
    def _get_windows_language(self):
        """Convert config language to Windows OCR language tag."""
        return self.LANGUAGE_MAP.get(self.ocr_language, 'zh-Hans')
    
    def clean_ocr_text(self, text):
        """Clean OCR result - remove unwanted spaces between CJK characters and fix common OCR errors."""
        # Only remove truly problematic invisible/control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # Fix I/l confusion: uppercase I between lowercase letters should be lowercase l
        # e.g., "fIle" -> "file", "heIlo" -> "hello"
        text = re.sub(r'(?<=[a-z])I(?=[a-z])', 'l', text)
        
        # Fix I at the end of lowercase words (e.g., "finaI" -> "final")
        text = re.sub(r'(?<=[a-z])I(?=\s|$|[.,!?;:\)])', 'l', text)
        
        # Fix I after lowercase at start of word continuation (e.g., "alI" -> "all")
        text = re.sub(r'(?<=[a-z])I(?=[a-z])', 'l', text)
        
        # Remove spaces between Japanese hiragana characters
        text = re.sub(r'([\u3040-\u309f])\s+([\u3040-\u309f])', r'\1\2', text)
        
        # Remove spaces between Japanese katakana characters
        text = re.sub(r'([\u30a0-\u30ff])\s+([\u30a0-\u30ff])', r'\1\2', text)
        
        # Remove spaces between CJK characters (Chinese/Japanese kanji)
        text = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', text)
        
        # Remove spaces between hiragana and katakana
        text = re.sub(r'([\u3040-\u309f])\s+([\u30a0-\u30ff])', r'\1\2', text)
        text = re.sub(r'([\u30a0-\u30ff])\s+([\u3040-\u309f])', r'\1\2', text)
        
        # Remove spaces between hiragana/katakana and kanji
        text = re.sub(r'([\u3040-\u30ff])\s+([\u4e00-\u9fff])', r'\1\2', text)
        text = re.sub(r'([\u4e00-\u9fff])\s+([\u3040-\u30ff])', r'\1\2', text)
        
        # Remove spaces between CJK and Japanese punctuation
        text = re.sub(r'([\u3040-\u30ff\u4e00-\u9fff])\s+([。、！？「」『』（）・：；])', r'\1\2', text)
        text = re.sub(r'([。、！？「」『』（）・：；])\s+([\u3040-\u30ff\u4e00-\u9fff])', r'\1\2', text)

        # Remove spaces around special symbols (e.g. '☆','★','♪','•') between CJK
        text = re.sub(r'([\u4e00-\u9fff\u3040-\u30ff])\s+([☆★♪•·])', r'\1\2', text)
        text = re.sub(r'([☆★♪•·])\s+([\u4e00-\u9fff\u3040-\u30ff])', r'\1\2', text)
        
        # Remove spaces between ASCII alphanumerics and CJK characters (e.g. 'DL 版' -> 'DL版')
        text = re.sub(r'([A-Za-z0-9]+)\s+([\u4e00-\u9fff\u3040-\u30ff])', r'\1\2', text)
        text = re.sub(r'([\u4e00-\u9fff\u3040-\u30ff])\s+([A-Za-z0-9]+)', r'\1\2', text)

        # Replace roman-numeral-like connectors between tokens with '][' (e.g. 'DL Ⅱ 無修' -> 'DL][無修')
        # Only match roman numerals as whole words (avoid matching letters inside ASCII tokens like 'DL')
        text = re.sub(
            r'(?<=[A-Za-z0-9\u4e00-\u9fff\u3040-\u30ff])\s*\b(?:[\u2160-\u2188]+|[IVXLCDMivxlcdm]+)\b\s*(?=[A-Za-z0-9\u4e00-\u9fff\u3040-\u30ff])',
            '][',
            text
        )

        # Apply the patterns multiple times to catch all cases
        for _ in range(3):
            text = re.sub(r'([\u3040-\u30ff\u4e00-\u9fff])\s+([\u3040-\u30ff\u4e00-\u9fff])', r'\1\2', text)
        
        # Convert multiple spaces to single space (for remaining text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove extra newlines but keep intentional ones
        text = re.sub(r'\n\n+', '\n', text)
        
        return text.strip()
    
    def perform_ocr(self, image):
        """Perform OCR on the given PIL image using Windows OCR API."""
        try:
            from PIL import Image
            import winocr
            from winrt.windows.media.ocr import OcrEngine
            from winrt.windows.globalization import Language
            
            # Ensure image is PIL Image format
            if not isinstance(image, Image.Image):
                self.ocr_complete.emit("Error: Invalid image format")
                return
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get Windows language code
            win_lang = self._get_windows_language()
            
            # Check if the language is supported, try fallbacks
            languages_to_try = [win_lang]
            
            # Add fallback languages based on primary language
            if win_lang == 'zh-Hans':
                languages_to_try.extend(['zh-Hant', 'zh-CN', 'zh-TW', 'ja', 'en'])
            elif win_lang == 'zh-Hant':
                languages_to_try.extend(['zh-Hans', 'zh-TW', 'zh-CN', 'ja', 'en'])
            elif win_lang == 'ja':
                languages_to_try.extend(['zh-Hans', 'zh-Hant', 'en'])
            else:
                languages_to_try.extend(['en', 'zh-Hans', 'zh-Hant'])
            
            # Find first available language
            available_lang = None
            for lang in languages_to_try:
                try:
                    if OcrEngine.is_language_supported(Language(lang)):
                        available_lang = lang
                        break
                except:
                    continue
            
            if not available_lang:
                self.ocr_complete.emit(
                    "Error: No OCR language pack installed.\n\n"
                    "Please install a language pack by running PowerShell as Administrator:\n"
                    "Add-WindowsCapability -Online -Name \"Language.OCR~~~zh-TW~0.0.1.0\"\n"
                    "or\n"
                    "Add-WindowsCapability -Online -Name \"Language.OCR~~~zh-CN~0.0.1.0\""
                )
                return
            
            # Run Windows OCR asynchronously
            async def run_ocr():
                result = await winocr.recognize_pil(image, lang=available_lang)
                return result
            
            # Execute the async OCR
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(run_ocr())
            finally:
                loop.close()
            
            # Extract text from result
            if result and result.text:
                text = result.text
                text = self.clean_ocr_text(text)
            else:
                text = "No text detected"
            
            self.ocr_complete.emit(text)
            
        except Exception as e:
            self.ocr_complete.emit(f"OCR Error: {str(e)}\n{traceback.format_exc()}")


class SelectionWindow(QWidget):
    """Window for selecting a screen area for OCR with draggable and resizable frame."""
    
    HANDLE_SIZE = 8
    screenshot_ready = pyqtSignal(QPixmap)
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.screenshot = None
        self.screenshot_ready.connect(self._on_screenshot_ready)
        
        # Set window flags and geometry FIRST
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)  # Enable mouseMoveEvent without button press
        
        # Set geometry to match screen
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self.setGeometry(screen_geometry)
        
        # Capture screenshot in background thread to avoid blocking
        def capture_screenshot():
            screenshot = screen.grabWindow(0)
            self.screenshot_ready.emit(screenshot)
        
        thread = threading.Thread(target=capture_screenshot, daemon=True)
        thread.start()
        
        # Try to load last selection from config
        saved_selection = load_selection_from_config()
        
        if saved_selection:
            # Use saved selection, but clamp to screen bounds
            x, y, width, height = saved_selection
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            
            # Validate and clamp to screen
            x = max(0, min(x, screen_width - 20))
            y = max(0, min(y, screen_height - 20))
            width = max(20, min(width, screen_width - x))
            height = max(20, min(height, screen_height - y))
            
            self.selection_rect = QRect(x, y, width, height)
        else:
            # Create default selection rectangle (centered, 50% of screen)
            screen_width = screen_geometry.width()
            screen_height = screen_geometry.height()
            default_w = int(screen_width * 0.5)
            default_h = int(screen_height * 0.5)
            default_x = int((screen_width - default_w) / 2)
            default_y = int((screen_height - default_h) / 2)
            
            self.selection_rect = QRect(default_x, default_y, default_w, default_h)
        
        # Mouse interaction states
        self.dragging = False
        self.resizing = False
        self.resize_edge = None
        self.drag_start = QPoint()
        self.resize_edge = None  # 'tl', 'tr', 'bl', 'br', 'top', 'bottom', 'left', 'right'
        
    def _on_screenshot_ready(self, screenshot):
        """Called when screenshot is ready from background thread."""
        self.screenshot = screenshot
        self.update()  # Trigger repaint
        
    def get_handle_rects(self):
        """Get rects for all resize handles."""
        h = self.HANDLE_SIZE
        r = self.selection_rect
        handles = {
            'tl': QRect(r.left() - h // 2, r.top() - h // 2, h, h),
            'tr': QRect(r.right() - h // 2, r.top() - h // 2, h, h),
            'bl': QRect(r.left() - h // 2, r.bottom() - h // 2, h, h),
            'br': QRect(r.right() - h // 2, r.bottom() - h // 2, h, h),
            'top': QRect(r.left() + r.width() // 2 - h // 2, r.top() - h // 2, h, h),
            'bottom': QRect(r.left() + r.width() // 2 - h // 2, r.bottom() - h // 2, h, h),
            'left': QRect(r.left() - h // 2, r.top() + r.height() // 2 - h // 2, h, h),
            'right': QRect(r.right() - h // 2, r.top() + r.height() // 2 - h // 2, h, h),
        }
        return handles
    
    def get_edge_at_point(self, pos):
        """Determine which edge/handle is at the given point."""
        r = self.selection_rect
        px = pos.x()
        py = pos.y()
        tolerance = 12  # Pixel tolerance for edge detection
        
        # Get boundaries
        left = r.left()
        right = r.right()
        top = r.top()
        bottom = r.bottom()
        
        # Check corners first (must be in corner region)
        if px - left < tolerance and py - top < tolerance and px >= left and py >= top:
            return 'tl'
        if right - px < tolerance and py - top < tolerance and px <= right and py >= top:
            return 'tr'
        if px - left < tolerance and bottom - py < tolerance and px >= left and py <= bottom:
            return 'bl'
        if right - px < tolerance and bottom - py < tolerance and px <= right and py <= bottom:
            return 'br'
        
        # Check edges
        # Top edge
        if abs(py - top) < tolerance and left <= px <= right:
            return 'top'
        
        # Bottom edge
        if abs(py - bottom) < tolerance and left <= px <= right:
            return 'bottom'
        
        # Left edge
        if abs(px - left) < tolerance and top <= py <= bottom:
            return 'left'
        
        # Right edge
        if abs(px - right) < tolerance and top <= py <= bottom:
            return 'right'
        return None
    
    def paintEvent(self, event):
        """Draw the selection rectangle with handles."""
        painter = QPainter(self)
        
        # Only draw if screenshot is ready
        if self.screenshot:
            # Draw screenshot
            painter.drawPixmap(self.rect(), self.screenshot)
            
            # Draw semi-transparent overlay everywhere except the selection
            painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
            
            # Draw the selected area with full brightness (redraw from screenshot)
            painter.drawPixmap(self.selection_rect, self.screenshot, self.selection_rect)
            
            # Draw selection border (bright pink/magenta for visibility)
            pen = QPen(QColor(255, 20, 147), 10)
            painter.setPen(pen)
            painter.drawRect(self.selection_rect)
            
            # Draw resize handles (bright pink with larger size)
            painter.setPen(QPen(QColor(255, 20, 147), 3))
            painter.setBrush(QColor(255, 20, 147))
            handles = self.get_handle_rects()
            for handle_rect in handles.values():
                painter.drawRect(handle_rect)
            
            # Draw instruction text (bright pink)
            painter.setPen(QPen(QColor(255, 20, 147)))
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            painter.drawText(10, 30, 'Drag to move, drag handles to resize, Enter to confirm, Esc to cancel')
        else:
            # Show loading message while screenshot is being captured
            painter.fillRect(self.rect(), QColor(50, 50, 50))
            painter.setPen(QPen(QColor(255, 255, 255)))
            font = painter.font()
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, 'Capturing screen...')
        
    def mousePressEvent(self, event):
        """Handle mouse press for dragging or resizing."""
        if event.button() == Qt.LeftButton:
            edge = self.get_edge_at_point(event.pos())
            if edge:
                self.resizing = True
                self.resize_edge = edge
            elif self.selection_rect.contains(event.pos()):
                self.dragging = True
            else:
                # Click outside the selection area - cancel capture
                self.close()
                return
            
            self.drag_start = event.pos()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging or resizing."""
        # Always check current edge first
        current_edge = self.get_edge_at_point(event.pos())
        
        if self.dragging:
            # Dragging the selection
            delta = event.pos() - self.drag_start
            self.selection_rect.translate(delta)
            self.drag_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            self.update()
        elif self.resizing and self.resize_edge:
            # Resizing the selection
            self.resize_selection(event.pos())
            
            # Update cursor based on the original resize edge
            edge = self.resize_edge
            if edge in ['tl', 'br']:
                self.setCursor(Qt.SizeFDiagCursor)
            elif edge in ['tr', 'bl']:
                self.setCursor(Qt.SizeBDiagCursor)
            elif edge in ['top', 'bottom']:
                self.setCursor(Qt.SizeVerCursor)
            elif edge in ['left', 'right']:
                self.setCursor(Qt.SizeHorCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            
            self.update()
        else:
            # Normal movement - update cursor based on position
            if current_edge in ['tl', 'br']:
                self.setCursor(Qt.SizeFDiagCursor)
            elif current_edge in ['tr', 'bl']:
                self.setCursor(Qt.SizeBDiagCursor)
            elif current_edge in ['top', 'bottom']:
                self.setCursor(Qt.SizeVerCursor)
            elif current_edge in ['left', 'right']:
                self.setCursor(Qt.SizeHorCursor)
            elif self.selection_rect.contains(event.pos()):
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resizing = False
            self.resize_edge = None
            # Reset cursor to normal
            self.setCursor(Qt.ArrowCursor)
            self.update()
    
    def resize_selection(self, pos):
        """Resize the selection rectangle based on which edge is being dragged."""
        edge = self.resize_edge
        new_rect = QRect(self.selection_rect)
        
        # Handle horizontal edges
        if edge in ['tl', 'tr', 'left', 'right', 'bl', 'br']:
            if edge in ['tl', 'bl', 'left']:
                new_rect.setLeft(pos.x())
            elif edge in ['tr', 'br', 'right']:
                new_rect.setRight(pos.x())
        
        # Handle vertical edges
        if edge in ['tl', 'tr', 'top', 'bottom', 'bl', 'br']:
            if edge in ['tl', 'tr', 'top']:
                new_rect.setTop(pos.y())
            elif edge in ['bl', 'br', 'bottom']:
                new_rect.setBottom(pos.y())
        
        # Ensure minimum size and valid rect
        if new_rect.width() >= 20 and new_rect.height() >= 20:
            self.selection_rect = new_rect
    
    def keyPressEvent(self, event):
        """Handle keyboard input."""
        if event.key() == Qt.Key_Escape:
            self.close()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.perform_ocr()
    
    def perform_ocr(self):
        """Perform OCR on the selected area."""
        # Check if screenshot is ready
        if not self.screenshot:
            self.main_window.display_result("Error: Screenshot is still being captured, please wait a moment...")
            return
            
        if self.selection_rect.width() > 10 and self.selection_rect.height() > 10:
            x, y, w, h = (self.selection_rect.x(), self.selection_rect.y(), 
                         self.selection_rect.width(), self.selection_rect.height())
            
            # Save selection dimensions and options to config
            save_selection_to_config(x, y, w, h, self.main_window.remove_newlines)
            
            # Capture the selected area
            img = self.screenshot.copy(x, y, w, h)
            
            # Convert QPixmap to PIL Image using QBuffer
            from PyQt5.QtCore import QBuffer, QIODevice
            from PIL import Image as PILImage
            import io
            
            buf = QBuffer()
            buf.open(QIODevice.ReadWrite)
            img.save(buf, 'PNG')
            buf.seek(0)
            
            # Read bytes from QBuffer
            image_bytes = buf.data().data()
            buf.close()
            
            # Load as PIL Image
            pil_image = PILImage.open(io.BytesIO(image_bytes))
            pil_image = pil_image.convert('RGB')
            
            # Perform OCR in background thread
            self.main_window.display_result("Processing... (this may take a moment)")
            
            def ocr_thread():
                self.main_window.ocr_worker.perform_ocr(pil_image)
            
            thread = threading.Thread(target=ocr_thread)
            thread.daemon = True
            thread.start()
        
        self.close()


class OCRWindow(QMainWindow):
    """Main window for displaying OCR results."""
    
    def __init__(self, tray_icon):
        super().__init__()
        self.tray_icon = tray_icon
        self.dragging = False
        self.offset = QPoint()
        
        # Load options from config
        self.remove_newlines, self.ocr_language, self.force_brackets = load_options_from_config()
        
        # Initialize OCR worker
        self.ocr_worker = OCRWorker()
        self.ocr_worker.set_language(self.ocr_language)
        self.ocr_worker.ocr_complete.connect(self.display_result)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('One Sentence OCR')
        
        # Load saved window geometry or use default
        saved_geometry = load_window_geometry_from_config()
        if saved_geometry:
            x, y, width, height = saved_geometry
            self.setGeometry(x, y, width, height)
        else:
            self.setGeometry(100, 100, 400, 300)
        
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        # Create File menu with actions
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('File')
        
        new_capture_action = file_menu.addAction('New Capture')
        new_capture_action.triggered.connect(self.start_capture)
        
        minimize_action = file_menu.addAction('Minimize to Tray')
        minimize_action.triggered.connect(self.hide)
        
        file_menu.addSeparator()
        
        close_action = file_menu.addAction('Close Application')
        close_action.triggered.connect(self.close_application)
        
        # Create Option menu with actions
        option_menu = menu_bar.addMenu('Option')
        
        self.remove_newlines_action = option_menu.addAction('Remove Newlines')
        self.remove_newlines_action.setCheckable(True)
        self.remove_newlines_action.setChecked(self.remove_newlines)
        self.remove_newlines_action.triggered.connect(self.toggle_remove_newlines)
        
        # Main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Title label
        title_label = QLabel('OCR Result:')
        title_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        layout.addWidget(title_label)
        
        # Text display area
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setPlaceholderText('OCR results will appear here...')
        self.text_display.setStyleSheet('QTextEdit { font-weight: bold; font-size: 14pt; }')
        layout.addWidget(self.text_display)
        
        # Language buttons at the bottom
        button_layout = QHBoxLayout()
        
        self.chinese_btn = QPushButton('中文')
        self.chinese_btn.setCheckable(True)
        self.chinese_btn.setChecked(self.ocr_language in ['chi_sim+eng', 'chi_sim', 'chi_tra+eng', 'chi_tra'])
        self.chinese_btn.clicked.connect(lambda: self.set_ocr_language('chi_sim+eng', '中文'))
        self.chinese_btn.setStyleSheet(self._get_button_style(self.chinese_btn.isChecked()))
        button_layout.addWidget(self.chinese_btn)
        
        self.japanese_btn = QPushButton('日文')
        self.japanese_btn.setCheckable(True)
        self.japanese_btn.setChecked(self.ocr_language in ['jpn+eng', 'jpn'])
        self.japanese_btn.clicked.connect(lambda: self.set_ocr_language('jpn+eng', '日文'))
        self.japanese_btn.setStyleSheet(self._get_button_style(self.japanese_btn.isChecked()))
        button_layout.addWidget(self.japanese_btn)
        
        # Bracket force adjustment buttons (same row)
        self.force_brackets_btn = QPushButton('強制括弧轉換')
        self.force_brackets_btn.setCheckable(True)
        self.force_brackets_btn.setChecked(self.force_brackets)
        self.force_brackets_btn.clicked.connect(lambda: self.set_force_brackets(True))
        self.force_brackets_btn.setStyleSheet(self._get_button_style(self.force_brackets_btn.isChecked()))
        button_layout.addWidget(self.force_brackets_btn)

        self.no_force_brackets_btn = QPushButton('不強制括弧轉換')
        self.no_force_brackets_btn.setCheckable(True)
        self.no_force_brackets_btn.setChecked(not self.force_brackets)
        self.no_force_brackets_btn.clicked.connect(lambda: self.set_force_brackets(False))
        self.no_force_brackets_btn.setStyleSheet(self._get_button_style(self.no_force_brackets_btn.isChecked()))
        button_layout.addWidget(self.no_force_brackets_btn)

        layout.addLayout(button_layout)
    
    def _get_button_style(self, is_selected):
        """Get button style based on selection state."""
        if is_selected:
            return 'QPushButton { background-color: #FFD700; color: black; font-weight: bold; font-size: 14pt; padding: 8px; }'
        else:
            return 'QPushButton { background-color: #f0f0f0; color: black; font-weight: bold; font-size: 14pt; padding: 8px; }'
    
    def _update_language_buttons(self):
        """Update language button styles based on current selection."""
        is_chinese = self.ocr_language in ['chi_sim+eng', 'chi_sim', 'chi_tra+eng', 'chi_tra']
        is_japanese = self.ocr_language in ['jpn+eng', 'jpn']
        
        self.chinese_btn.setChecked(is_chinese)
        self.japanese_btn.setChecked(is_japanese)
        self.chinese_btn.setStyleSheet(self._get_button_style(is_chinese))
        self.japanese_btn.setStyleSheet(self._get_button_style(is_japanese))
        # Update bracket buttons style
        self.force_brackets_btn.setChecked(self.force_brackets)
        self.no_force_brackets_btn.setChecked(not self.force_brackets)
        self.force_brackets_btn.setStyleSheet(self._get_button_style(self.force_brackets_btn.isChecked()))
        self.no_force_brackets_btn.setStyleSheet(self._get_button_style(self.no_force_brackets_btn.isChecked()))
        
    def display_result(self, text):
        """Display OCR result in the text area."""
        # Process text if remove newlines option is enabled
        if self.remove_newlines:
            text = text.replace('\n', '')

        # Apply bracket normalization if force option enabled
        if getattr(self, 'force_brackets', False):
            text = self._normalize_brackets(text)
        
        self.text_display.setPlainText(text)
        
        # Auto-copy result to clipboard
        if text.strip():
            pyperclip.copy(text)
        
        self.show()
        self.raise_()
        self.activateWindow()
    
    def toggle_remove_newlines(self):
        """Toggle the remove newlines option."""
        self.remove_newlines = self.remove_newlines_action.isChecked()
        # Save the option to config.ini immediately
        save_options_to_config(self.remove_newlines, self.ocr_language, self.force_brackets)

    def set_force_brackets(self, force: bool):
        """Enable or disable forced bracket normalization and persist setting."""
        self.force_brackets = bool(force)
        # Update UI
        self._update_language_buttons()
        # Save current options including force_brackets
        save_options_to_config(self.remove_newlines, self.ocr_language, self.force_brackets)

    def _normalize_brackets(self, text: str) -> str:
        """Replace various full-width/cjk brackets with half-width ASCII equivalents."""
        if not text:
            return text
        mapping = {
            # parentheses / brackets (many variants and presentation forms)
            '（': '(', '）': ')', '﹙': '(', '﹚': ')', '︵': '(', '︶': ')',
            '❨': '(', '❩': ')', '❪': '(', '❫': ')',

            # square/angle/curly brackets
            '［': '[', '］': ']', '【': '[', '】': ']', '〔': '[', '〕': ']',
            '｛': '{', '｝': '}', '〖': '[', '〗': ']',

            # angle/chevrons
            '《': '<', '》': '>', '〈': '<', '〉': '>', '⟨': '<', '⟩': '>', '＜': '<', '＞': '>',

            # corner quotes and Japanese quote marks -> use ASCII quotes
            '「': '"', '」': '"', '『': '"', '』': '"', '“': '"', '”': '"', '‘': "'", '’': "'",

            # punctuation (fullwidth -> ASCII)
            '，': ',', '：': ':', '；': ';', '？': '?', '！': '!',
            '－': '-', '—': '-', '‒': '-', '–': '-', '〜': '~', '～': '~',
            '／': '/', '＼': '\\',

            # miscellaneous presentation forms
            '﹝': '[', '﹞': ']', '﹛': '{', '﹜': '}',
        }
        # Replace all occurrences
        for k, v in mapping.items():
            text = text.replace(k, v)

        # Remove spaces directly inside brackets (e.g. '( test )' -> '(test)')
        # After normalization we only expect ASCII brackets here
        # Remove space(s) after opening brackets
        text = re.sub(r"\(\s+", "(", text)
        text = re.sub(r"\[\s+", "[", text)
        text = re.sub(r"\{\s+", "{", text)
        text = re.sub(r"<\s+", "<", text)

        # Remove space(s) before closing brackets
        text = re.sub(r"\s+\)", ")", text)
        text = re.sub(r"\s+\]", "]", text)
        text = re.sub(r"\s+\}", "}", text)
        text = re.sub(r"\s+>", ">", text)

        return text
    
    def set_ocr_language(self, language, label):
        """Set the OCR language."""
        self.ocr_language = language
        self.ocr_worker.set_language(language)
        
        # Update button styles
        self._update_language_buttons()
        
        # Save the language to config.ini immediately
        save_options_to_config(self.remove_newlines, language, self.force_brackets)
        
        # Show confirmation
        self.text_display.setPlainText(f"Language changed to: {label}")
        

    
    def start_capture(self):
        """Start the screen area selection process."""
        # Reload options from config before capturing
        self.remove_newlines, self.ocr_language, self.force_brackets = load_options_from_config()
        self.ocr_worker.set_language(self.ocr_language)
        self.remove_newlines_action.setChecked(self.remove_newlines)
        self._update_language_buttons()
        
        self.hide()
        self.selection_window = SelectionWindow(self)
        self.selection_window.show()
    
    def close_application(self):
        """Close the application."""
        # Save window geometry before closing
        geometry = self.geometry()
        save_window_geometry_to_config(geometry.x(), geometry.y(), geometry.width(), geometry.height())
        sys.exit(0)
    
    def closeEvent(self, event):
        """Handle window close event - close the application."""
        # Save window geometry before closing
        geometry = self.geometry()
        save_window_geometry_to_config(geometry.x(), geometry.y(), geometry.width(), geometry.height())
        event.accept()
        sys.exit(0)


class SystemTrayApp:
    """Main application with system tray support."""
    
    class HotkeySignals(QObject):
        """Signal emitter for hotkey events."""
        hotkey_pressed = pyqtSignal()
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.hotkey_signals = self.HotkeySignals()
        
        # Set Windows native style
        self.app.setStyle('windowsvista')
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon()
        self.setup_tray_icon()
        
        # Create main window
        self.window = OCRWindow(self.tray_icon)
        
        # Connect hotkey signal to capture method
        self.hotkey_signals.hotkey_pressed.connect(self.start_capture)
        
        # Setup global hotkey listener (Ctrl+F12)
        self.setup_global_hotkey()
        
    def setup_tray_icon(self):
        """Setup the system tray icon and menu."""
        # Create a simple icon (a colored square)
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 120, 215))
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.white, 2))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, 'OCR')
        painter.end()
        
        icon = QIcon(pixmap)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip('One Sentence OCR')
        
        # Create tray menu
        tray_menu = QMenu()
        
        # New capture action
        capture_action = tray_menu.addAction('New Capture')
        capture_action.triggered.connect(self.start_capture)
        
        # Show window action
        show_window_action = tray_menu.addAction('Show Window')
        show_window_action.triggered.connect(self.show_window)
        
        tray_menu.addSeparator()
        
        # Close application action
        close_action = tray_menu.addAction('Close Application')
        close_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
        
    def tray_icon_activated(self, reason):
        """Handle tray icon click."""
        if reason == QSystemTrayIcon.Trigger:
            self.show_window()
    
    def minimize_to_tray(self):
        """Minimize the main window to tray."""
        self.window.hide()
        self.tray_icon.showMessage(
            'One Sentence OCR',
            'Application minimized to system tray',
            QSystemTrayIcon.Information,
            2000
        )
    
    def show_window(self):
        """Show the main window."""
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
    
    def start_capture(self):
        """Start a new screen capture."""
        self.window.start_capture()
    
    def setup_global_hotkey(self):
        """Setup global hotkey from config in a background thread."""
        from pynput.keyboard import Key, Listener
        
        # Load hotkey settings from config
        hotkey_key, hotkey_ctrl, hotkey_alt, hotkey_shift = load_hotkey_from_config()
        self.hotkey_config = (hotkey_key, hotkey_ctrl, hotkey_alt, hotkey_shift)
        
        # Map hotkey key string to pynput Key
        key_mapping = {
            'f12': Key.f12, 'f11': Key.f11, 'f10': Key.f10,
            'esc': Key.esc, 'tab': Key.tab, 'enter': Key.enter,
        }
        
        hotkey_pynput_key = key_mapping.get(hotkey_key.lower(), Key.f12)
        
        ctrl_pressed = False
        alt_pressed = False
        shift_pressed = False
        
        def on_press(key):
            nonlocal ctrl_pressed, alt_pressed, shift_pressed
            try:
                if key == Key.ctrl_l or key == Key.ctrl_r:
                    ctrl_pressed = True
                elif key == Key.alt_l or key == Key.alt_r:
                    alt_pressed = True
                elif key == Key.shift_l or key == Key.shift_r:
                    shift_pressed = True
                elif key == hotkey_pynput_key:
                    # Check if the required modifiers are pressed
                    # Logic: only check that required modifiers are pressed,
                    # ignore state of unrequired modifiers
                    modifiers_match = (
                        (not hotkey_ctrl or ctrl_pressed) and 
                        (not hotkey_alt or alt_pressed) and 
                        (not hotkey_shift or shift_pressed)
                    )
                    if modifiers_match:
                        # Emit signal to trigger capture in main thread
                        self.hotkey_signals.hotkey_pressed.emit()
            except AttributeError:
                pass
        
        def on_release(key):
            nonlocal ctrl_pressed, alt_pressed, shift_pressed
            try:
                if key == Key.ctrl_l or key == Key.ctrl_r:
                    ctrl_pressed = False
                elif key == Key.alt_l or key == Key.alt_r:
                    alt_pressed = False
                elif key == Key.shift_l or key == Key.shift_r:
                    shift_pressed = False
            except AttributeError:
                pass
        
        # Create and start listener in background
        listener = Listener(on_press=on_press, on_release=on_release)
        listener.start()
        self.hotkey_listener = listener
    
    def quit_app(self):
        """Quit the application."""
        # Stop the hotkey listener
        if hasattr(self, 'hotkey_listener'):
            self.hotkey_listener.stop()
        self.tray_icon.hide()
        self.app.quit()
    
    def run(self):
        """Run the application."""
        self.tray_icon.showMessage(
            'One Sentence OCR',
            'Application started. Use Ctrl+F12 to capture, or right-click tray icon.',
            QSystemTrayIcon.Information,
            3000
        )
        return self.app.exec_()


def main():
    """Main entry point."""
    app = SystemTrayApp()
    sys.exit(app.run())


if __name__ == '__main__':
    main()
