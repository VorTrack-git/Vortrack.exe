"""
ui_imagenes.py
Carga de imágenes para la interfaz (CTkImage o ImageTk según la librería).
"""

import os

# pyrefly: ignore [missing-import]
from PIL import Image, ImageTk

try:
    # pyrefly: ignore [missing-import]
    import customtkinter as ctk
except ImportError:
    ctk = None


def load_image(path, size):
    """Carga una imagen como CTkImage o ImageTk según la librería disponible."""
    if not os.path.exists(path):
        return None
    img = Image.open(path)
    if ctk:
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    img_resized = img.resize(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img_resized)
