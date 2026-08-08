"""Punto de entrada principal de VorTrack."""

import tkinter as tk
from tkinter import messagebox

import auth
import inicio_ui
import login_ui
import recolec_ui
import transformacion_ui

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


def show_main_app(page: str = "inicio") -> str:
    """
    Muestra una página de la aplicación autenticada.
    Retorna la próxima acción: 'inicio', 'recoleccion', 'logout' o 'exit'.
    """
    result = {"next": "exit"}

    root = _create_root()

    def navigate(destino):
        result["next"] = destino
        root.quit()

    def on_logout():
        result["next"] = "logout"
        root.quit()

    if page == "recoleccion":
        recolec_ui.RecoleccionesApp(root, on_navigate=navigate, on_logout=on_logout)
    elif page == "transformacion":
        transformacion_ui.TransformacionApp(root, on_navigate=navigate, on_logout=on_logout)
    else:
        inicio_ui.VorTrackApp(root, on_navigate=navigate, on_logout=on_logout)

    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.mainloop()

    try:
        root.destroy()
    except tk.TclError:
        pass

    return result["next"]


def run():
    """Ejecuta el ciclo login -> app (con navegación entre páginas) -> logout -> login."""
    while True:
        if not show_login():
            break

        if not auth.is_authenticated():
            continue

        page = "inicio"
        while True:
            action = show_main_app(page)
            if action in ("inicio", "recoleccion", "transformacion"):
                page = action
                continue
            if action == "logout":
                auth.logout()
                break  # vuelve al login
            # 'exit': el usuario cerró la ventana -> terminar la app
            return


if __name__ == "__main__":
    run()
