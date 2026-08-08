"""Utilidades de interfaz compartidas por los módulos de VorTrack."""

import os
from tkinter import messagebox

# pyrefly: ignore [missing-import]
from PIL import Image, ImageTk

try:
    # pyrefly: ignore [missing-import]
    import customtkinter as ctk
except ImportError:
    ctk = None


def center_window(root, width, height, taskbar_ratio=0.92):
    """Centra la ventana en pantalla evitando que quede bajo la barra de tareas."""
    root.update_idletasks()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    usable_h = int(screen_h * taskbar_ratio)
    height = min(height, usable_h)
    width = min(width, screen_w)

    x = max((screen_w - width) // 2, 0)
    y = max((usable_h - height) // 2, 0)
    root.geometry(f"{width}x{height}+{x}+{y}")


def load_image(path, size):
    """Carga una imagen como CTkImage o ImageTk según la librería disponible."""
    if not os.path.exists(path):
        return None
    img = Image.open(path)
    if ctk:
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    img_resized = img.resize(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img_resized)


def open_footer_link(root, link_text):
    """Acción asociada a cada enlace del pie de página, compartida por los módulos."""
    if link_text in ("Soporte Técnico", "Contacto"):
        # Import diferido para evitar dependencias circulares al cargar el módulo.
        import soporte_dialog
        soporte_dialog.abrir_soporte(root)
    elif link_text == "Privacidad":
        messagebox.showinfo(
            "Privacidad",
            "La política de privacidad de VorTrack estará disponible próximamente.",
        )
    elif link_text == "Términos de Uso":
        messagebox.showinfo(
            "Términos de Uso",
            "Los términos de uso de VorTrack estarán disponibles próximamente.",
        )


def bind_footer_link(label, root, link_text, base_fg, hover_fg):
    """Hace clicable un enlace del footer con efecto hover."""
    label.configure(cursor="hand2")
    label.bind("<Button-1>", lambda _e: open_footer_link(root, link_text))
    label.bind("<Enter>", lambda _e: label.configure(fg=hover_fg))
    label.bind("<Leave>", lambda _e: label.configure(fg=base_fg))
