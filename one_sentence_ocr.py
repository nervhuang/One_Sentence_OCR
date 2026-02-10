#!/usr/bin/env python3
"""
One Sentence OCR - A screenshot tool with system tray support.
Captures selected screen area and copies to clipboard.
"""
import sys
import os
import threading
import configparser
from datetime import datetime

# Set Tesseract path BEFORE importing pytesseract
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

# Import and configure pytesseract early
try:
    import pytesseract
    pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except ImportError:
    pass

from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QWidget, 
                             QVBoxLayout, QLabel, QPushButton, QMessageBox, QTextEdit, QMenuBar, QMainWindow)
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal, QObject, QEvent
from PyQt5.QtGui import QIcon, QPixmap, QCursor, QPainter, QPen, QColor
from PIL import Image
import pyperclip
import io


def save_selection_to_config(x, y, width, height, remove_newlines=None):
    """Save the selection box dimensions and options to config.ini"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    
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
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    
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
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    try:
        if os.path.exists(config_path):
            config.read(config_path)
            
            if 'options' in config:
                remove_newlines = config['options'].get('remove_newlines', 'False')
                ocr_language = config['options'].get('ocr_language', 'chi_sim+eng')
                return remove_newlines.lower() == 'true', ocr_language
    except (ValueError, KeyError, configparser.Error):
        pass
    
    return False, 'chi_sim+eng'


def load_ocr_language_from_config():
    """Load OCR language setting from config.ini"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    try:
        if os.path.exists(config_path):
            config.read(config_path)
            
            if 'options' in config:
                return config['options'].get('ocr_language', 'chi_sim+eng')
    except (ValueError, KeyError, configparser.Error):
        pass
    
    return 'chi_sim+eng'


def save_options_to_config(remove_newlines, ocr_language='chi_sim+eng'):
    """Save options to config.ini"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    
    # Read existing config
    if os.path.exists(config_path):
        config.read(config_path)
    
    # Ensure options section exists
    if 'options' not in config:
        config['options'] = {}
    
    # Update options
    config['options']['remove_newlines'] = str(remove_newlines)
    config['options']['ocr_language'] = str(ocr_language)
    
    # Write to file
    with open(config_path, 'w') as f:
        config.write(f)


class OCRWorker(QObject):
    """Worker class for performing OCR using Tesseract OCR."""
    ocr_complete = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.ocr_language = load_ocr_language_from_config()
    
    def set_language(self, language):
        """Set the OCR language to use."""
        self.ocr_language = language
    
    def perform_ocr(self, image):
        """Perform OCR on the given PIL image using Tesseract."""
        try:
            import os
            import sys
            
            # Ensure environment and paths are set (do this every time)
            os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
            os.environ['PATH'] = r'C:\Program Files\Tesseract-OCR\;' + os.environ.get('PATH', '')
            
            # Import pytesseract fresh
            import pytesseract
            
            # Set the command path explicitly
            tesseract_exe = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            pytesseract.pytesseract.pytesseract_cmd = tesseract_exe
            
            # Verify file exists
            if not os.path.exists(tesseract_exe):
                self.ocr_complete.emit(
                    f"Error: Tesseract executable not found at:\n{tesseract_exe}"
                )
                return
            
            from PIL import Image
            
            # Ensure image is PIL Image format
            if not isinstance(image, Image.Image):
                self.ocr_complete.emit("Error: Invalid image format")
                return
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR with selected language
            try:
                text = pytesseract.image_to_string(image, lang=self.ocr_language)
            except Exception as e:
                # Check if it's a language pack issue
                error_str = str(e).lower()
                if any(x in error_str for x in ['chi_sim', 'chi_tra', 'jpn', 'language', 'osd']):
                    # Try fallback to English only
                    try:
                        text = pytesseract.image_to_string(image, lang='eng')
                        if text:
                            text = f"[Fallback to English]\n{text}"
                    except Exception as e2:
                        raise Exception(f"OCR failed with configured language and English fallback: {str(e)}")
                else:
                    raise e
            
            if not text or not text.strip():
                text = "No text detected"
            
            self.ocr_complete.emit(text)
            
        except Exception as e:
            import traceback
            self.ocr_complete.emit(f"OCR Error: {str(e)}")


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
        self.remove_newlines, self.ocr_language = load_options_from_config()
        
        # Initialize OCR worker
        self.ocr_worker = OCRWorker()
        self.ocr_worker.set_language(self.ocr_language)
        self.ocr_worker.ocr_complete.connect(self.display_result)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('One Sentence OCR')
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
        
        option_menu.addSeparator()
        
        # Add language submenu
        language_menu = option_menu.addMenu('Language')
        
        # Language options
        self.language_actions = {}
        languages = {
            'Simplified Chinese': 'chi_sim',
            'Simplified Chinese + English': 'chi_sim+eng',
            'Traditional Chinese': 'chi_tra',
            'Traditional Chinese + English': 'chi_tra+eng',
            'Japanese': 'jpn',
            'Japanese + English': 'jpn+eng',
            'English': 'eng',
            'Multi-language (Sim + Tra + Jpn + Eng)': 'chi_sim+chi_tra+jpn+eng'
        }
        
        for label, lang_code in languages.items():
            action = language_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(self.ocr_language == lang_code)
            action.triggered.connect(lambda checked, lang=lang_code, lbl=label: self.set_ocr_language(lang, lbl))
            self.language_actions[lang_code] = action
        
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
        layout.addWidget(self.text_display)
        
    def display_result(self, text):
        """Display OCR result in the text area."""
        # Process text if remove newlines option is enabled
        if self.remove_newlines:
            text = text.replace('\n', '')
        
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
        save_options_to_config(self.remove_newlines, self.ocr_language)
    
    def set_ocr_language(self, language, label):
        """Set the OCR language."""
        self.ocr_language = language
        self.ocr_worker.set_language(language)
        
        # Uncheck all language actions and check the selected one
        for action in self.language_actions.values():
            action.setChecked(False)
        if language in self.language_actions:
            self.language_actions[language].setChecked(True)
        
        # Save the language to config.ini immediately
        save_options_to_config(self.remove_newlines, language)
        
        # Show confirmation
        self.text_display.setPlainText(f"Language changed to: {label}")
        

    
    def start_capture(self):
        """Start the screen area selection process."""
        # Reload options from config before capturing
        self.remove_newlines, self.ocr_language = load_options_from_config()
        self.ocr_worker.set_language(self.ocr_language)
        self.remove_newlines_action.setChecked(self.remove_newlines)
        
        self.hide()
        self.selection_window = SelectionWindow(self)
        self.selection_window.show()
    
    def close_application(self):
        """Close the application."""
        import sys
        sys.exit(0)
    
    def closeEvent(self, event):
        """Handle window close event - close the application."""
        event.accept()
        import sys
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
            self.start_capture()
    
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
        """Setup Ctrl+F12 hotkey in a background thread."""
        from pynput.keyboard import Key, Listener
        
        ctrl_pressed = False
        
        def on_press(key):
            nonlocal ctrl_pressed
            try:
                if key == Key.ctrl_l or key == Key.ctrl_r:
                    ctrl_pressed = True
                elif key == Key.f12:
                    if ctrl_pressed:
                        # Emit signal to trigger capture in main thread
                        self.hotkey_signals.hotkey_pressed.emit()
            except AttributeError:
                pass
        
        def on_release(key):
            nonlocal ctrl_pressed
            try:
                if key == Key.ctrl_l or key == Key.ctrl_r:
                    ctrl_pressed = False
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
