#!/usr/bin/env python3
"""
One Sentence OCR - A screenshot tool with system tray support.
Captures selected screen area and copies to clipboard.
"""
import sys
import os
import threading

# Set Tesseract path BEFORE importing pytesseract
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

# Import and configure pytesseract early
try:
    import pytesseract
    pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except ImportError:
    pass

from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QWidget, 
                             QVBoxLayout, QLabel, QPushButton, QMessageBox, QTextEdit)
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QPixmap, QCursor, QPainter, QPen, QColor
from PIL import Image
import pyperclip
import io


class OCRWorker(QObject):
    """Worker class for performing OCR using Tesseract OCR."""
    ocr_complete = pyqtSignal(str)
    
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
            
            # Perform OCR with explicit configuration
            try:
                # Try with Chinese + English
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            except Exception as e:
                # Check if it's a language pack issue
                error_str = str(e).lower()
                if any(x in error_str for x in ['chi_sim', 'chi_tra', 'language', 'osd']):
                    # Fallback to English only
                    try:
                        text = pytesseract.image_to_string(image, lang='eng')
                    except Exception as e2:
                        raise Exception(f"English OCR also failed: {str(e2)}")
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
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        # Capture the entire screen first
        screen = QApplication.primaryScreen()
        self.screenshot = screen.grabWindow(0)
        
        # Set window flags and geometry
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setMouseTracking(True)  # Enable mouseMoveEvent without button press
        
        # Set geometry to match screen
        screen_geometry = screen.geometry()
        self.setGeometry(screen_geometry)
        
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
            if 'l' in edge or edge == 'left':
                new_rect.setLeft(pos.x())
            elif 'r' in edge or edge == 'right':
                new_rect.setRight(pos.x())
        
        # Handle vertical edges
        if edge in ['tl', 'tr', 'top', 'bottom', 'bl', 'br']:
            if 't' in edge or edge == 'top':
                new_rect.setTop(pos.y())
            elif 'b' in edge or edge == 'bottom':
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
        if self.selection_rect.width() > 10 and self.selection_rect.height() > 10:
            x, y, w, h = (self.selection_rect.x(), self.selection_rect.y(), 
                         self.selection_rect.width(), self.selection_rect.height())
            
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


class OCRWindow(QWidget):
    """Main draggable and resizable window for displaying OCR results."""
    
    def __init__(self, tray_icon):
        super().__init__()
        self.tray_icon = tray_icon
        self.dragging = False
        self.offset = QPoint()
        
        # Initialize OCR worker
        self.ocr_worker = OCRWorker()
        self.ocr_worker.ocr_complete.connect(self.display_result)
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('One Sentence OCR')
        self.setGeometry(100, 100, 400, 300)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        
        # Title label
        title_label = QLabel('OCR Result:')
        title_label.setStyleSheet('font-weight: bold; font-size: 14px;')
        layout.addWidget(title_label)
        
        # Text display area
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setPlaceholderText('OCR results will appear here...')
        layout.addWidget(self.text_display)
        
        # Button layout
        button_layout = QVBoxLayout()
        
        # Copy to clipboard button
        self.copy_button = QPushButton('Copy to Clipboard')
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        self.copy_button.setEnabled(False)
        button_layout.addWidget(self.copy_button)
        
        # New capture button
        self.capture_button = QPushButton('New Capture')
        self.capture_button.clicked.connect(self.start_capture)
        button_layout.addWidget(self.capture_button)
        
        # Close button
        self.close_button = QPushButton('Minimize to Tray')
        self.close_button.clicked.connect(self.hide)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def display_result(self, text):
        """Display OCR result in the text area."""
        self.text_display.setPlainText(text)
        self.copy_button.setEnabled(bool(text.strip()))
        self.show()
        self.raise_()
        self.activateWindow()
        
    def copy_to_clipboard(self):
        """Copy the OCR result to clipboard."""
        text = self.text_display.toPlainText()
        if text:
            pyperclip.copy(text)
            QMessageBox.information(self, 'Success', 'Text copied to clipboard!')
    
    def start_capture(self):
        """Start the screen area selection process."""
        self.hide()
        self.selection_window = SelectionWindow(self)
        self.selection_window.show()
    
    def mousePressEvent(self, event):
        """Enable window dragging."""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        """Handle window dragging."""
        if self.dragging:
            self.move(self.pos() + event.pos() - self.offset)
    
    def mouseReleaseEvent(self, event):
        """Stop window dragging."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
    
    def closeEvent(self, event):
        """Handle window close event - minimize to tray instead."""
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            'One Sentence OCR',
            'Application minimized to system tray',
            QSystemTrayIcon.Information,
            2000
        )


class SystemTrayApp:
    """Main application with system tray support."""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon()
        self.setup_tray_icon()
        
        # Create main window
        self.window = OCRWindow(self.tray_icon)
        
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
        
        # Show window action
        show_action = tray_menu.addAction('Show Window')
        show_action.triggered.connect(self.show_window)
        
        # New capture action
        capture_action = tray_menu.addAction('New Capture')
        capture_action.triggered.connect(self.start_capture)
        
        tray_menu.addSeparator()
        
        # Quit action
        quit_action = tray_menu.addAction('Quit')
        quit_action.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
        
    def tray_icon_activated(self, reason):
        """Handle tray icon click."""
        if reason == QSystemTrayIcon.Trigger:
            self.show_window()
    
    def show_window(self):
        """Show the main window."""
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
    
    def start_capture(self):
        """Start a new screen capture."""
        self.window.start_capture()
    
    def quit_app(self):
        """Quit the application."""
        self.tray_icon.hide()
        self.app.quit()
    
    def run(self):
        """Run the application."""
        self.tray_icon.showMessage(
            'One Sentence OCR',
            'Application started. Right-click the tray icon for options.',
            QSystemTrayIcon.Information,
            2000
        )
        return self.app.exec_()


def main():
    """Main entry point."""
    app = SystemTrayApp()
    sys.exit(app.run())


if __name__ == '__main__':
    main()
