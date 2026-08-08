"""Punto de entrada principal de VorTrack."""

import tkinter as tk
from tkinter import messagebox

import auth
import inicio_ui
import login_ui

try:
    import customtkinter as ctk
except ImportError:
    ctk = None


def _create_root():
    if ctk:
        return ctk.CTk()
    return tk.Tk()


def show_login() -> bool:
    """
    Muestra la pantalla de login.
    Retorna True si el usuario inició sesión, False si cerró la ventana.
    """
    result = {"authenticated": False}

    root = _create_root()

    def on_success():
        result["authenticated"] = True
        root.quit()

    login_ui.LoginApp(root, on_success=on_success)
    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()

    try:
        root.destroy()
    except tk.TclError:
        pass

    return result["authenticated"]


def show_main_app() -> bool:
    """
    Muestra la aplicación principal.
    Retorna True si el usuario cerró sesión (volver al login), False si salió de la app.
    """
    result = {"logout": False}

    root = _create_root()

    def on_logout():
        auth.logout()
        result["logout"] = True
        root.quit()

    inicio_ui.VorTrackApp(root, on_logout=on_logout)
    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()

    try:
        root.destroy()
    except tk.TclError:
        pass

    return result["logout"]


def run():
    """Ejecuta el ciclo login -> app -> logout -> login."""
    while True:
        if not show_login():
            break

        if not auth.is_authenticated():
            continue

        if not show_main_app():
            auth.logout()
            break


if __name__ == "__main__":
    run()
