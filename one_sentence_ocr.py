#!/usr/bin/env python3
"""
One Sentence OCR - A minimal OCR application with system tray support.
"""
import sys
import os

# Check for required dependencies
try:
    from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QWidget
    from PyQt5.QtWidgets import QVBoxLayout, QLabel, QTextEdit, QPushButton, QMessageBox
    from PyQt5.QtCore import Qt, QPoint, QRect
    from PyQt5.QtGui import QIcon, QPixmap, QCursor, QPainter, QPen, QColor
except ImportError as e:
    print(f"Error: Failed to import PyQt5: {e}")
    print("\nPlease install PyQt5:")
    print("  pip install PyQt5")
    sys.exit(1)

try:
    import pytesseract
except ImportError:
    print("Error: Failed to import pytesseract")
    print("\nPlease install pytesseract:")
    print("  pip install pytesseract")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Failed to import PIL")
    print("\nPlease install Pillow:")
    print("  pip install Pillow")
    sys.exit(1)

try:
    import pyperclip
except ImportError:
    print("Error: Failed to import pyperclip")
    print("\nPlease install pyperclip:")
    print("  pip install pyperclip")
    sys.exit(1)


class SelectionWindow(QWidget):
    """Window for selecting a screen area for OCR."""
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Capture the entire screen
        screen = QApplication.primaryScreen()
        self.screenshot = screen.grabWindow(0)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.selecting = False
        
    def paintEvent(self, event):
        """Draw the selection rectangle."""
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.screenshot)
        
        if self.selecting:
            # Draw semi-transparent overlay
            painter.fillRect(self.rect(), QColor(0, 0, 0, 100))
            
            # Draw clear rectangle for selection
            rect = QRect(self.begin, self.end).normalized()
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            
            # Draw selection border
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            pen = QPen(QColor(0, 255, 0), 2)
            painter.setPen(pen)
            painter.drawRect(rect)
    
    def mousePressEvent(self, event):
        """Start selection."""
        if event.button() == Qt.LeftButton:
            self.begin = event.pos()
            self.end = self.begin
            self.selecting = True
            self.update()
    
    def mouseMoveEvent(self, event):
        """Update selection."""
        if self.selecting:
            self.end = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Complete selection and perform OCR."""
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            rect = QRect(self.begin, self.end).normalized()
            
            if rect.width() > 10 and rect.height() > 10:
                # Capture the selected area
                x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
                
                # Convert QPixmap to PIL Image
                img = self.screenshot.copy(x, y, w, h)
                buffer = img.toImage()
                buffer = buffer.convertToFormat(4)  # Format_RGB32
                
                width = buffer.width()
                height = buffer.height()
                ptr = buffer.bits()
                ptr.setsize(buffer.byteCount())
                arr = bytes(ptr)
                
                # Create PIL Image
                pil_image = Image.frombytes('RGB', (width, height), arr, 'raw', 'BGRA')
                
                # Perform OCR
                # Note: Default language is English. For other languages, install appropriate
                # Tesseract language packs and modify the lang parameter (e.g., 'chi_sim' for Chinese)
                try:
                    text = pytesseract.image_to_string(pil_image, lang='eng')
                    self.main_window.display_result(text)
                except Exception as e:
                    self.main_window.display_result(f"OCR Error: {str(e)}")
            
            self.close()
    
    def keyPressEvent(self, event):
        """Cancel selection with Escape key."""
        if event.key() == Qt.Key_Escape:
            self.close()


class OCRWindow(QWidget):
    """Main draggable and resizable window for displaying OCR results."""
    
    def __init__(self, tray_icon):
        super().__init__()
        self.tray_icon = tray_icon
        self.init_ui()
        self.dragging = False
        self.offset = QPoint()
        
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
