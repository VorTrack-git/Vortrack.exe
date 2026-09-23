import os
import tkinter as tk
from tkinter import messagebox, ttk

import servicios.auth as auth
import interfaz.ui_utils as ui_utils
import datos.repositorio as repositorio
from interfaz.ui_tema import COLORS, FONT_FAMILY
from interfaz.ui_cargando import cargar_con_spinner, ejecutar_con_spinner
from interfaz.widgets import FabricaWidgets
from servicios.servicio_informe import ServicioInforme
from servicios.servicio_proyeccion import ServicioProyeccion

try:
    import customtkinter as ctk
except ImportError:
    ctk = None


class HistoricoApp:
    PAGE = "historico"

    def __init__(self, root, on_navigate=None, on_logout=None, datos=None, proyeccion=None, fabrica=None,
                 informe=None):
        self.root = root
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.datos = datos or repositorio
        self.proyeccion = proyeccion or ServicioProyeccion()
        self.informe = informe or ServicioInforme(self.datos)
        self._generando = False
        self.fw = fabrica or FabricaWidgets()
        self.root.title("VorTrack - Histórico e Informes")
        self.root.minsize(1024, 700)
        ui_utils.maximize_window(self.root)
        self.root.configure(bg=COLORS["background"])

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = ui_utils.ruta_logo("VorTrack icon.png")

        ui_utils.set_window_icon(self.root)

        if ctk:
            ctk.set_appearance_mode("Dark")
            ctk.set_default_color_theme("blue")

        self.setup_ui()

    def load_ctk_image(self, path, size):
        return ui_utils.load_image(path, size)

    def setup_ui(self):
        self.main_container = tk.Frame(self.root, bg=COLORS["background"])
        self.main_container.pack(fill="both", expand=True)
        ui_utils.build_app_navbar(self)
        self.build_main_content()
        ui_utils.build_app_footer(self)

    def build_main_content(self):
        outer = tk.Frame(self.main_container, bg=COLORS["background"])
        outer.pack(fill="both", expand=True, padx=40, pady=20)

        # Encabezado + botón de informe
        header = tk.Frame(outer, bg=COLORS["background"])
        header.pack(fill="x", pady=(0, 16))

        tk.Label(header, text="Histórico e Informes", fg=COLORS["primary_container"],
                 bg=COLORS["background"], font=(FONT_FAMILY, 26, "bold")).pack(side="left")

        if ctk:
            ctk.CTkButton(header, text="GENERAR INFORME   ⭳", fg_color=COLORS["secondary_container"],
                          hover_color=COLORS["primary_container"], text_color=COLORS["white"],
                          font=(FONT_FAMILY, 11, "bold"), height=40, width=210, corner_radius=14,
                          command=self.generar_informe).pack(side="right")
        else:
            tk.Button(header, text="GENERAR INFORME  ⭳", fg=COLORS["white"], bg=COLORS["secondary_container"],
                      activebackground=COLORS["primary_container"], activeforeground=COLORS["white"],
                      font=(FONT_FAMILY, 11, "bold"), bd=0, padx=20, pady=8, cursor="hand2",
                      command=self.generar_informe).pack(side="right")

        # Cuerpo con los datos: el spinner lo tapa mientras llegan las consultas.
        cuerpo = self._cuerpo = tk.Frame(outer, bg=COLORS["background"])
        cuerpo.pack(fill="both", expand=True)

        # Fila de indicadores (KPIs); los valores se rellenan en _poblar_indicadores.
        kpi_row = tk.Frame(cuerpo, bg=COLORS["background"])
        kpi_row.pack(fill="x", pady=(0, 20))
        self._kpi_valores = {}
        for clave, titulo, icono in [
            ("pet_recolectado", "PET recolectado", "🧴"),
            ("filamento_producido", "Filamento producido", "🧵"),
            ("desperdicio", "Desperdicio", "♻"),
            ("objetos_impresos", "Objetos impresos", "🖨"),
            ("responsables", "Responsables", "👥"),
            ("botellas", "Botellas recolectadas", "🍾"),
        ]:
            self._kpi_valores[clave] = self._kpi_card(kpi_row, titulo, "—", icono)

        # Fila inferior: ranking (gamificación) + proyecciones lado a lado
        bottom = tk.Frame(cuerpo, bg=COLORS["background"])
        bottom.pack(fill="both", expand=True)
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        bottom.grid_rowconfigure(0, weight=1)
        self._build_ranking(bottom)
        self._build_proyecciones(bottom)

        # Consultas en paralelo con spinner encima del cuerpo; al terminar se rellenan los paneles.
        cargar_con_spinner(cuerpo, {
            "indicadores": (self.datos.indicadores_resumen, "Calculando indicadores…"),
            "ranking": (self.datos.ranking_participacion, "Consultando ranking de participación…"),
            "producciones": (self.datos.listar_producciones, "Obteniendo filamentos producidos…"),
            "modelos": (self.datos.listar_modelos_admin, "Cargando modelos…"),
        }, self._poblar)

    def _poblar(self, cargas):
        self._cargas = cargas
        self._poblar_indicadores()
        self._poblar_ranking()
        self._poblar_proyecciones()

    def _poblar_indicadores(self):
        try:
            k = self._cargas["indicadores"].result()
        except Exception as exc:  # noqa: BLE001
            k = {"pet_recolectado": 0, "filamento_producido": 0, "desperdicio": 0,
                 "objetos_impresos": 0, "responsables": 0, "botellas": 0}
            messagebox.showwarning("Base de datos", f"No se pudieron cargar los indicadores:\n{exc}")
        textos = {
            "pet_recolectado": f"{k['pet_recolectado']:g} kg",
            "filamento_producido": f"{k['filamento_producido']:g} kg",
            "desperdicio": f"{k['desperdicio']:.2f} kg",
            "objetos_impresos": str(k['objetos_impresos']),
            "responsables": str(k['responsables']),
            "botellas": str(k['botellas']),
        }
        for clave, texto in textos.items():
            self._kpi_valores[clave].configure(text=texto)

    def _kpi_card(self, parent, titulo, valor, icono):
        if ctk:
            card = ctk.CTkFrame(parent, fg_color=COLORS["surface_container"],
                                border_color=COLORS["outline_variant"], border_width=1, corner_radius=14)
            card.pack(side="left", expand=True, fill="both", padx=6)
        else:
            card = tk.Frame(parent, bg=COLORS["surface_container"], bd=1, relief="solid")
            card.pack(side="left", expand=True, fill="both", padx=6)

        inner = tk.Frame(card, bg=COLORS["surface_container"])
        inner.pack(fill="both", expand=True, padx=16, pady=14)

        tk.Label(inner, text=icono, bg=COLORS["surface_container"], fg=COLORS["primary_fixed"],
                 font=(FONT_FAMILY, 18)).pack(anchor="w")
        lbl_valor = tk.Label(inner, text=valor, bg=COLORS["surface_container"], fg=COLORS["white"],
                             font=(FONT_FAMILY, 24, "bold"))
        lbl_valor.pack(anchor="w", pady=(4, 0))
        tk.Label(inner, text=titulo, bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"],
                 font=(FONT_FAMILY, 10)).pack(anchor="w")
        return lbl_valor

    def _build_ranking(self, parent):
        if ctk:
            panel = ctk.CTkFrame(parent, fg_color=COLORS["surface_container"],
                                 border_color=COLORS["primary_fixed"], border_width=1, corner_radius=12)
        else:
            panel = tk.Frame(parent, bg=COLORS["surface_container"], bd=1, relief="solid")
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        if ctk:
            ctk.CTkLabel(panel, text="Ranking de participación", font=(FONT_FAMILY, 18, "bold"),
                         text_color=COLORS["primary_fixed"]).pack(pady=(20, 15), padx=20, anchor="w")
        else:
            tk.Label(panel, text="Ranking de participación", font=(FONT_FAMILY, 16, "bold"),
                     bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(pady=(20, 15), padx=20, anchor="w")

        tree_frame = tk.Frame(panel, bg=COLORS["surface_container"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        scroll = ttk.Scrollbar(tree_frame)
        scroll.pack(side="right", fill="y")

        columnas = [
            ("puesto", "Puesto", 80, "center"),
            ("estudiante", "Estudiante", 220, "w"),
            ("pet", "PET aportado (kg)", 160, "center"),
            ("jornadas", "Jornadas", 110, "center"),
            ("botellas", "Botellas", 110, "center"),
            ("puntos", "Puntos", 110, "center"),
        ]
        self._ranking_tree = self.fw.tabla(tree_frame, columnas, "Hist.Treeview", yscrollcommand=scroll.set)
        self._ranking_tree.pack(fill="both", expand=True)
        scroll.config(command=self._ranking_tree.yview)

    def _poblar_ranking(self):
        try:
            filas = self._cargas["ranking"].result()
        except Exception:  # noqa: BLE001
            filas = []
        for puesto, (nombre, pet, jornadas, botellas) in enumerate(filas, start=1):
            pet_val = float(pet) if pet is not None else 0.0
            puntos = int(round(pet_val * 100))  # gamificación: 100 pts por kg de PET
            self._ranking_tree.insert("", "end", values=(
                puesto, nombre, f"{pet_val:g}", jornadas, botellas, puntos))

    def _build_proyecciones(self, parent):
        """Panel de predicciones: con un filamento producido, cuántas piezas de
        cada modelo alcanzan a hacerse y cuánto sobra."""
        if ctk:
            panel = ctk.CTkFrame(parent, fg_color=COLORS["surface_container"],
                                 border_color=COLORS["primary_fixed"], border_width=1, corner_radius=12)
        else:
            panel = tk.Frame(parent, bg=COLORS["surface_container"], bd=1, relief="solid")
        panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        if ctk:
            ctk.CTkLabel(panel, text="Proyecciones de producción", font=(FONT_FAMILY, 18, "bold"),
                         text_color=COLORS["primary_fixed"]).pack(pady=(20, 6), padx=20, anchor="w")
        else:
            tk.Label(panel, text="Proyecciones de producción", font=(FONT_FAMILY, 16, "bold"),
                     bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(pady=(20, 6), padx=20, anchor="w")

        # El desplegable se crea en _poblar_proyecciones, cuando llegan los catálogos.
        self._proy_sel = tk.Frame(panel, bg=COLORS["surface_container"])
        self._proy_sel.pack(fill="x", padx=20, pady=(0, 4))
        lbl = "Filamento producido:"
        if ctk:
            ctk.CTkLabel(self._proy_sel, text=lbl, font=(FONT_FAMILY, 12, "bold"), text_color=COLORS["on_surface_variant"]).pack(anchor="w")
        else:
            tk.Label(self._proy_sel, text=lbl, font=(FONT_FAMILY, 10, "bold"), bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"]).pack(anchor="w")

        self._proy_msg = tk.Label(panel, text="Elige un filamento para ver cuántas piezas alcanzan.",
                                  bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"],
                                  font=(FONT_FAMILY, 10), wraplength=520, justify="left")
        self._proy_msg.pack(anchor="w", padx=20, pady=(0, 8))

        tf = tk.Frame(panel, bg=COLORS["surface_container"])
        tf.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        sb = ttk.Scrollbar(tf); sb.pack(side="right", fill="y")
        columnas = [
            ("modelo", "Modelo", 170, "w"),
            ("piezas", "Piezas posibles", 120, "center"),
            ("porpieza", "g/pieza", 90, "center"),
            ("sobrante", "Sobrante (g)", 110, "center"),
            ("tiempo", "Tiempo total (min)", 120, "center"),
        ]
        self._proy_tree = self.fw.tabla(tf, columnas, "Hist.Treeview", yscrollcommand=sb.set)
        self._proy_tree.pack(fill="both", expand=True)
        sb.config(command=self._proy_tree.yview)

    def _poblar_proyecciones(self):
        # Catálogos para el cálculo
        try:
            self._proy_prod = self._cargas["producciones"].result()     # (id, etiqueta, PesoObtenido_kg)
            self._proy_modelos = self._cargas["modelos"].result()       # (id, nombre, cat, tiempo_h, peso_g)
        except Exception:  # noqa: BLE001
            self._proy_prod, self._proy_modelos = [], []

        prod_values = ["Seleccione filamento..."] + [lab for _, lab, _ in self._proy_prod]
        self._proy_peso_by_lbl = {lab: float(peso or 0) for _, lab, peso in self._proy_prod}
        self._proy_combo, self._proy_var = self.fw.combo(
            self._proy_sel, prod_values, command=self._proy_calcular, pady_ctk=(2, 6), pady_tk=(2, 6))

    def _proy_calcular(self, _choice=None):
        for it in self._proy_tree.get_children():
            self._proy_tree.delete(it)
        etiqueta = self._proy_combo.get() if ctk else self._proy_var.get()
        peso_kg = self._proy_peso_by_lbl.get(etiqueta)
        if peso_kg is None:
            self._proy_msg.configure(text="Elige un filamento para ver cuántas piezas alcanzan.")
            return
        # Cálculo delegado al servicio de proyección (SRP/DIP).
        filas, mejor, disponible_g = self.proyeccion.piezas_por_filamento(peso_kg, self._proy_modelos)
        for nombre, piezas, g_pieza, sobrante, tiempo_total in filas:
            if piezas is None:
                self._proy_tree.insert("", "end", values=(nombre, "—", "—", "—", "—"))
                continue
            self._proy_tree.insert("", "end", values=(
                nombre, piezas, f"{g_pieza:g}", f"{sobrante:.0f}",
                f"{tiempo_total:g}" if tiempo_total is not None else "—"))
        if mejor and mejor[1] > 0:
            self._proy_msg.configure(text=(
                f"Con {peso_kg:g} kg ({disponible_g:.0f} g) de filamento alcanza para "
                f"{mejor[1]} {mejor[0]}, sobrando ~{mejor[2]:.0f} g. Mira la tabla para cada modelo."))
        else:
            self._proy_msg.configure(text="No alcanza para ningún modelo con ese filamento (o faltan pesos estimados en los modelos).")

    # --- Acciones / navegación ---
    def generar_informe(self):
        """Genera el informe PDF en un hilo (spinner por etapas) y lo guarda en Descargas."""
        if self._generando:
            return
        self._generando = True
        usuario = auth.get_current_user()
        ejecutar_con_spinner(
            self._cuerpo,
            lambda reportar: self.informe.generar(usuario=usuario, progreso=reportar),
            self._informe_listo, titulo="Generando informe…")

    def _informe_listo(self, futuro):
        self._generando = False
        try:
            ruta = futuro.result()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Generar informe", f"No se pudo generar el informe PDF:\n\n{exc}")
            return
        if messagebox.askyesno("Informe descargado",
                               f"El informe se guardó en tu carpeta de Descargas:\n\n{ruta.name}\n\n"
                               "¿Deseas abrirlo ahora?"):
            try:
                os.startfile(ruta)  # abre con el visor de PDF predeterminado (Windows)
            except (AttributeError, OSError) as exc:
                messagebox.showwarning("Abrir informe", f"No se pudo abrir el archivo:\n{exc}\n\nRuta: {ruta}")

    def ir_a_inicio(self):
        if self.on_navigate:
            self.on_navigate("inicio")

    def ir_a_historico(self):
        # Ya estamos en histórico.
        return

    def on_registrar_select(self, choice):
        destinos = {"Recolección": "recoleccion", "Transformación": "transformacion", "Impresión": "impresion"}
        target = destinos.get(choice)
        if target and self.on_navigate:
            self.on_navigate(target)

    def logout(self):
        if messagebox.askyesno("Cerrar sesión", "¿Desea cerrar sesión en VorTrack?"):
            if self.on_logout:
                self.on_logout()
            else:
                auth.logout()
                self.root.destroy()


def main():
    auth.require_auth()
    root = ctk.CTk() if ctk else tk.Tk()
    HistoricoApp(root)
    root.mainloop()


if __name__ == "__main__":
    try:
        auth.require_auth()
    except RuntimeError as exc:
        messagebox.showerror("Acceso restringido", str(exc))
        import interfaz.login_ui as login_ui
        login_ui.main()
    else:
        main()
