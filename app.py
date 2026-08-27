"""Punto de entrada principal de VorTrack."""

import tkinter as tk
from tkinter import messagebox

import auth
import inicio_ui
import login_ui
import recolec_ui
import transformacion_ui
import impresion_ui
import historico_ui
import admin_ui
from contenedor import Contenedor
from widgets import FabricaWidgets

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

# Raíz de composición: se construyen una sola vez las dependencias concretas
# (capa de datos + servicios) y la fábrica de widgets, y se inyectan en la UI.
_cont = Contenedor()
_fabrica = FabricaWidgets()


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

    # El panel de administración solo es accesible para administradores.
    if page == "admin" and not auth.is_admin():
        page = "inicio"

    if page == "admin":
        admin_ui.AdminApp(root, on_navigate=navigate, on_logout=on_logout, datos=_cont.datos)
    elif page == "recoleccion":
        recolec_ui.RecoleccionesApp(root, on_navigate=navigate, on_logout=on_logout,
                                    datos=_cont.datos, fabrica=_fabrica)
    elif page == "transformacion":
        transformacion_ui.TransformacionApp(root, on_navigate=navigate, on_logout=on_logout,
                                            datos=_cont.datos, fabrica=_fabrica)
    elif page == "impresion":
        impresion_ui.ImpresionApp(root, on_navigate=navigate, on_logout=on_logout,
                                  datos=_cont.datos, proyeccion=_cont.proyeccion, fabrica=_fabrica)
    elif page == "historico":
        historico_ui.HistoricoApp(root, on_navigate=navigate, on_logout=on_logout,
                                  datos=_cont.datos, proyeccion=_cont.proyeccion, fabrica=_fabrica)
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

        # El administrador entra a su panel; el resto, al sistema normal.
        page = "admin" if auth.is_admin() else "inicio"
        while True:
            action = show_main_app(page)
            if action in ("inicio", "recoleccion", "transformacion", "impresion", "historico", "admin"):
                page = action
                continue
            if action == "logout":
                auth.logout()
                break  # vuelve al login
            # 'exit': el usuario cerró la ventana -> terminar la app
            return


if __name__ == "__main__":
    run()
