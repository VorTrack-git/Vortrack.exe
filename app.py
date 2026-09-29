"""Punto de entrada principal de VorTrack."""

import tkinter as tk
from tkinter import messagebox

import servicios.auth as auth
import interfaz.inicio_ui as inicio_ui
import interfaz.login_ui as login_ui
import interfaz.recolec_ui as recolec_ui
import interfaz.transformacion_ui as transformacion_ui
import interfaz.impresion_ui as impresion_ui
import interfaz.historico_ui as historico_ui
import interfaz.admin_ui as admin_ui
import interfaz.ui_ventana as ui_ventana
from contenedor import Contenedor
from interfaz.widgets import FabricaWidgets

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

# Raíz de composición: se construyen una sola vez las dependencias concretas
# (capa de datos + servicios) y la fábrica de widgets, y se inyectan en la UI.
_cont = Contenedor()
_fabrica = FabricaWidgets()

PAGINAS = ("inicio", "recoleccion", "transformacion", "impresion", "historico", "admin")

# Fundido de entrada de la ventana nueva (pasos × intervalo ≈ 150 ms).
FUNDIDO_PASOS = 8
FUNDIDO_MS = 18


class Navegador:
    """Orquesta las ventanas de la app con transiciones suaves.

    Hay una sola raíz Tk (oculta) que mantiene vivo el bucle de eventos; cada
    pantalla es una Toplevel. Al navegar, la ventana nueva se construye
    invisible (alpha 0) encima de la actual, aparece con un fundido y solo
    entonces se cierra la anterior: nunca se ve el escritorio entre pantallas.
    """

    def __init__(self):
        self.root = ctk.CTk() if ctk else tk.Tk()
        self.root.withdraw()
        ui_ventana.set_window_icon(self.root)
        self.ventana = None          # Toplevel visible
        self._en_transicion = False  # evita navegar dos veces con un doble clic
        # Los messagebox sin parent se centran en la ventana visible, no en la raíz oculta.
        ui_ventana.dialogos_sobre(lambda: self.ventana)

    # ------------------------------------------------------------- ciclo
    def run(self):
        self._abrir(self._construir_login)
        self.root.mainloop()
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def salir(self):
        self.root.quit()

    # ----------------------------------------------------------- destinos
    def ir(self, destino):
        """Callback `on_navigate` de todas las páginas."""
        if destino == "logout":
            auth.logout()
            self._abrir(self._construir_login)
        elif destino in PAGINAS:
            self._abrir(lambda win: self._construir_pagina(win, destino))
        else:  # 'exit' u otro valor desconocido
            self.salir()

    def _al_iniciar_sesion(self):
        if not auth.is_authenticated():
            return
        # El administrador entra a su panel; el resto, al sistema normal.
        self.ir("admin" if auth.is_admin() else "inicio")

    # -------------------------------------------------------- construcción
    def _construir_login(self, win):
        login_ui.LoginApp(win, on_success=self._al_iniciar_sesion)

    def _construir_pagina(self, win, page):
        # El panel de administración solo es accesible para administradores.
        if page == "admin" and not auth.is_admin():
            page = "inicio"
        nav = {"on_navigate": self.ir, "on_logout": lambda: self.ir("logout")}
        if page == "admin":
            admin_ui.AdminApp(win, datos=_cont.datos, **nav)
        elif page == "recoleccion":
            recolec_ui.RecoleccionesApp(win, datos=_cont.datos, fabrica=_fabrica, **nav)
        elif page == "transformacion":
            transformacion_ui.TransformacionApp(win, datos=_cont.datos, fabrica=_fabrica, **nav)
        elif page == "impresion":
            impresion_ui.ImpresionApp(win, datos=_cont.datos, proyeccion=_cont.proyeccion,
                                      fabrica=_fabrica, **nav)
        elif page == "historico":
            historico_ui.HistoricoApp(win, datos=_cont.datos, proyeccion=_cont.proyeccion,
                                      fabrica=_fabrica, informe=_cont.informe, **nav)
        else:
            inicio_ui.VorTrackApp(win, **nav)

    # ---------------------------------------------------------- transición
    def _abrir(self, construir):
        """Abre la ventana nueva y, cuando ya se ve completa, cierra la anterior."""
        if self._en_transicion:
            return
        self._en_transicion = True
        anterior = self.ventana

        win = ctk.CTkToplevel(self.root) if ctk else tk.Toplevel(self.root)
        self._set_alpha(win, 0.0)
        try:
            construir(win)
        except Exception as exc:  # noqa: BLE001
            # Si la página nueva falla al construirse, se queda la actual.
            self._destruir(win)
            self._en_transicion = False
            messagebox.showerror("VorTrack", f"No se pudo abrir la pantalla:\n{exc}")
            if anterior is None:
                self.salir()
            return

        win.protocol("WM_DELETE_WINDOW", self.salir)
        self.ventana = win
        # Se pinta todo (todavía invisible) antes de mostrarla, para que no
        # aparezca a medio dibujar.
        try:
            win.update_idletasks()
        except tk.TclError:
            pass
        self._fundido(win, anterior, 1)

    def _fundido(self, win, anterior, paso):
        try:
            if not win.winfo_exists():
                return
        except tk.TclError:
            return
        self._set_alpha(win, paso / FUNDIDO_PASOS)
        if paso == 1:
            win.lift()
            win.focus_force()
        if paso < FUNDIDO_PASOS:
            win.after(FUNDIDO_MS, self._fundido, win, anterior, paso + 1)
            return
        # La nueva ya está opaca encima: ahora sí se cierra la anterior.
        self._destruir(anterior)
        self._en_transicion = False

    @staticmethod
    def _set_alpha(win, valor):
        try:
            win.attributes("-alpha", valor)
        except tk.TclError:
            pass  # el gestor de ventanas no soporta transparencia: se muestra directo

    @staticmethod
    def _destruir(win):
        if win is None:
            return
        try:
            win.destroy()
        except tk.TclError:
            pass


def run():
    """Ejecuta el ciclo login -> app (con navegación entre páginas) -> logout -> login."""
    Navegador().run()


if __name__ == "__main__":
    run()
