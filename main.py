import asyncio
import ctypes
import io
import threading
import tkinter as tk
from tkinter import ttk

import keyboard
import mss
from PIL import Image, ImageDraw
import pystray

from winrt.windows.graphics.imaging import BitmapDecoder
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream


def set_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        return
    except Exception:
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def create_tray_icon_image(size=64):
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, size - 8, size - 8), outline=(30, 30, 30, 255), width=4)
    draw.line((16, size // 2, size - 16, size // 2), fill=(30, 30, 30, 255), width=3)
    return image


async def ocr_pil_image(image):
    with io.BytesIO() as buffer:
        image.save(buffer, format="BMP")
        data = buffer.getvalue()

    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream)
    writer.write_bytes(data)
    await writer.store_async()
    await writer.flush_async()
    stream.seek(0)

    decoder = await BitmapDecoder.create_async(stream)
    software_bitmap = await decoder.get_software_bitmap_async()
    engine = OcrEngine.try_create_from_user_profile_languages()
    result = await engine.recognize_async(software_bitmap)
    return result.text or ""


class OverlayWindow:
    def __init__(self, root, on_confirm, on_cancel):
        self.root = root
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.window = tk.Toplevel(root)
        self.window.title("Capture")
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", 0.3)
        self.window.configure(bg="#000000")
        self.window.resizable(True, True)
        self.window.minsize(200, 120)
        self.window.geometry("600x300+200+200")
        self.window.protocol("WM_DELETE_WINDOW", self.cancel)

        self.toolbar = tk.Frame(self.window, bg="#f0f0f0")
        self.toolbar.pack(side="bottom", fill="x")
        self.confirm_button = ttk.Button(self.toolbar, text="Confirm", command=self.confirm)
        self.cancel_button = ttk.Button(self.toolbar, text="Cancel", command=self.cancel)
        self.confirm_button.pack(side="right", padx=8, pady=6)
        self.cancel_button.pack(side="right", padx=8, pady=6)

        self.window.bind("<ButtonPress-1>", self.start_move)
        self.window.bind("<B1-Motion>", self.do_move)
        self._move_start = None

    def start_move(self, event):
        self._move_start = (event.x_root, event.y_root)

    def do_move(self, event):
        if not self._move_start:
            return
        dx = event.x_root - self._move_start[0]
        dy = event.y_root - self._move_start[1]
        x = self.window.winfo_x() + dx
        y = self.window.winfo_y() + dy
        self.window.geometry(f"+{x}+{y}")
        self._move_start = (event.x_root, event.y_root)

    def confirm(self):
        self.on_confirm(self.get_geometry())
        self.destroy()

    def cancel(self):
        self.on_cancel()
        self.destroy()

    def destroy(self):
        if self.window.winfo_exists():
            self.window.destroy()

    def get_geometry(self):
        self.window.update_idletasks()
        x = self.window.winfo_rootx()
        y = self.window.winfo_rooty()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        return x, y, width, height


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("One Sentence OCR")
        self.root.geometry("420x220")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)
        self.root.bind("<Unmap>", self.on_minimize)

        self.hotkey_var = tk.StringVar(value="ctrl+f12")
        self.status_var = tk.StringVar(value="Ready")
        self.current_hotkey = None
        self.overlay = None
        self.tray_icon = None

        self.build_ui()
        self.register_hotkey(self.hotkey_var.get())
        self.setup_tray()

    def build_ui(self):
        container = ttk.Frame(self.root, padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Global Hotkey").pack(anchor="w")
        hotkey_row = ttk.Frame(container)
        hotkey_row.pack(fill="x", pady=6)
        ttk.Entry(hotkey_row, textvariable=self.hotkey_var).pack(side="left", fill="x", expand=True)
        ttk.Button(hotkey_row, text="Apply", command=self.apply_hotkey).pack(side="left", padx=8)

        ttk.Button(container, text="Show Capture Frame", command=self.show_overlay).pack(fill="x", pady=4)
        ttk.Label(container, textvariable=self.status_var, foreground="#555555").pack(anchor="w", pady=8)

        hint = "Minimize to tray. Use hotkey to capture text."
        ttk.Label(container, text=hint, foreground="#666666").pack(anchor="w")

    def setup_tray(self):
        image = create_tray_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("Show", self.on_tray_show),
            pystray.MenuItem("Exit", self.on_tray_exit),
        )
        self.tray_icon = pystray.Icon("OneSentenceOCR", image, "One Sentence OCR", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def on_tray_show(self, _icon, _item):
        self.root.after(0, self.show_main)

    def on_tray_exit(self, _icon, _item):
        self.root.after(0, self.shutdown)

    def apply_hotkey(self):
        self.register_hotkey(self.hotkey_var.get())

    def register_hotkey(self, hotkey):
        if self.current_hotkey:
            keyboard.remove_hotkey(self.current_hotkey)
            self.current_hotkey = None
        if hotkey.strip():
            self.current_hotkey = keyboard.add_hotkey(hotkey, self.show_overlay)
            self.status_var.set(f"Hotkey set: {hotkey}")
        else:
            self.status_var.set("Hotkey cleared")

    def show_overlay(self):
        if self.overlay:
            return
        self.overlay = OverlayWindow(self.root, self.capture_region, self.on_overlay_cancel)

    def on_overlay_cancel(self):
        self.overlay = None
        self.status_var.set("Capture cancelled")

    def capture_region(self, geometry):
        self.overlay = None
        x, y, width, height = geometry
        if width < 5 or height < 5:
            self.status_var.set("Selection too small")
            return
        self.status_var.set("Capturing...")
        image = self.grab_screen(x, y, width, height)
        threading.Thread(target=self.run_ocr, args=(image,), daemon=True).start()

    def grab_screen(self, x, y, width, height):
        with mss.mss() as sct:
            monitor = {"left": int(x), "top": int(y), "width": int(width), "height": int(height)}
            shot = sct.grab(monitor)
            return Image.frombytes("RGB", shot.size, shot.rgb)

    def run_ocr(self, image):
        try:
            text = asyncio.run(ocr_pil_image(image))
        except Exception as exc:
            self.root.after(0, lambda: self.status_var.set(f"OCR failed: {exc}"))
            return
        self.root.after(0, lambda: self.on_ocr_done(text))

    def on_ocr_done(self, text):
        cleaned = text.strip()
        if not cleaned:
            self.status_var.set("No text detected")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(cleaned)
        self.status_var.set("Text copied to clipboard")

    def show_main(self):
        self.root.deiconify()
        self.root.state("normal")
        self.root.lift()

    def hide_to_tray(self):
        self.root.withdraw()
        self.status_var.set("Running in tray")

    def on_minimize(self, _event):
        if self.root.state() == "iconic":
            self.hide_to_tray()

    def shutdown(self):
        if self.current_hotkey:
            keyboard.remove_hotkey(self.current_hotkey)
            self.current_hotkey = None
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()


def main():
    set_dpi_awareness()
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
