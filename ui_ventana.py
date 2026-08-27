"""
ui_ventana.py
Utilidades de ventana: maximizar y fijar el ícono.
"""

import os
import tkinter as tk

# pyrefly: ignore [missing-import]
from PIL import Image, ImageTk

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def maximize_window(root):
    """Abre la ventana maximizada (ocupa toda la pantalla y conserva la barra de título).

    En tkinter puro basta llamar state('zoomed') una vez, pero customtkinter
    reajusta la geometría durante su init, así que hay que reintentar el
    maximizado de forma diferida (cuando ya corre el bucle de eventos).
    """
    def _apply():
        try:
            if not root.winfo_exists():
                return
            root.state("zoomed")  # Windows y la mayoría de Tk en Windows
        except tk.TclError:
            try:
                root.attributes("-zoomed", True)  # algunos entornos Linux
            except tk.TclError:
                try:
                    root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
                except tk.TclError:
                    pass

    root.update_idletasks()
    _apply()               # intento inmediato (funciona en tkinter puro)
    root.after(60, _apply)  # reintento diferido (necesario en customtkinter)


def set_window_icon(root):
    """Fija el ícono de la ventana usando VorTrack.ico (logo transparente).

    En Windows usa iconbitmap con el .ico (nítido en barra de título y de
    tareas). Si falla, cae a iconphoto con el PNG transparente. Se reintenta
    de forma diferida porque customtkinter puede sobreescribir el ícono al
    inicializarse.
    """
    ico = os.path.join(_BASE_DIR, "VorTrack.ico")
    png = os.path.join(_BASE_DIR, "VorTrack_icon_transparent.png")
    if not os.path.exists(png):
        png = os.path.join(_BASE_DIR, "VorTrack icon.png")

    def _apply():
        try:
            if not root.winfo_exists():
                return
        except Exception:
            return
        if os.name == "nt" and os.path.exists(ico):
            try:
                root.iconbitmap(ico)
                return
            except Exception:
                pass
        if os.path.exists(png):
            try:
                photo = ImageTk.PhotoImage(Image.open(png))
                root._vortrack_icon = photo  # mantener la referencia viva
                root.iconphoto(True, photo)
            except Exception:
                pass

    _apply()
    try:
        root.after(300, _apply)
    except Exception:
        pass
