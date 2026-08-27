import os
import tkinter as tk
from tkinter import messagebox, ttk

import auth
import ui_utils
import repositorio

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from PIL import Image, ImageTk

COLORS = ui_utils.COLORS
FONT_FAMILY = ui_utils.FONT_FAMILY


class HistoricoApp:
    PAGE = "historico"

    def __init__(self, root, on_navigate=None, on_logout=None):
        self.root = root
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.root.title("VorTrack - Histórico e Informes")
        self.root.minsize(1024, 700)
        ui_utils.maximize_window(self.root)
        self.root.configure(bg=COLORS["background"])

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(self.base_dir, "VorTrack icon.png")

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

        # Indicadores calculados en vivo desde la base de datos
        try:
            k = repositorio.indicadores_resumen()
        except Exception as exc:  # noqa: BLE001
            k = {"pet_recolectado": 0, "filamento_producido": 0, "desperdicio": 0,
                 "objetos_impresos": 0, "responsables": 0, "botellas": 0}
            messagebox.showwarning("Base de datos", f"No se pudieron cargar los indicadores:\n{exc}")

        kpis = [
            ("PET recolectado", f"{k['pet_recolectado']:g} kg", "🧴"),
            ("Filamento producido", f"{k['filamento_producido']:g} kg", "🧵"),
            ("Desperdicio", f"{k['desperdicio']:.2f} kg", "♻"),
            ("Objetos impresos", str(k['objetos_impresos']), "🖨"),
            ("Responsables", str(k['responsables']), "👥"),
            ("Botellas recolectadas", str(k['botellas']), "🍾"),
        ]

        # Fila de indicadores (KPIs)
        kpi_row = tk.Frame(outer, bg=COLORS["background"])
        kpi_row.pack(fill="x", pady=(0, 20))
        for titulo, valor, icono in kpis:
            self._kpi_card(kpi_row, titulo, valor, icono)

        # Fila inferior: ranking (gamificación) + proyecciones lado a lado
        bottom = tk.Frame(outer, bg=COLORS["background"])
        bottom.pack(fill="both", expand=True)
        bottom.grid_columnconfigure(0, weight=1)
        bottom.grid_columnconfigure(1, weight=1)
        bottom.grid_rowconfigure(0, weight=1)
        self._build_ranking(bottom)
        self._build_proyecciones(bottom)

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
        tk.Label(inner, text=valor, bg=COLORS["surface_container"], fg=COLORS["white"],
                 font=(FONT_FAMILY, 24, "bold")).pack(anchor="w", pady=(4, 0))
        tk.Label(inner, text=titulo, bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"],
                 font=(FONT_FAMILY, 10)).pack(anchor="w")

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

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Hist.Treeview", background=COLORS["surface"], foreground=COLORS["on_surface"],
                        rowheight=38, fieldbackground=COLORS["surface"], bordercolor=COLORS["outline_variant"],
                        borderwidth=0, font=(FONT_FAMILY, 11))
        style.map('Hist.Treeview', background=[('selected', COLORS["surface_low"])])
        style.configure("Hist.Treeview.Heading", background=COLORS["surface_high"],
                        foreground=COLORS["on_surface_variant"], relief="flat", font=(FONT_FAMILY, 11, "bold"))
        style.map("Hist.Treeview.Heading", background=[('active', COLORS["surface_bright"])])

        tree_frame = tk.Frame(panel, bg=COLORS["surface_container"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        scroll = ttk.Scrollbar(tree_frame)
        scroll.pack(side="right", fill="y")

        cols = ("puesto", "estudiante", "pet", "jornadas", "botellas", "puntos")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", style="Hist.Treeview", yscrollcommand=scroll.set)
        tree.heading("puesto", text="Puesto")
        tree.heading("estudiante", text="Estudiante")
        tree.heading("pet", text="PET aportado (kg)")
        tree.heading("jornadas", text="Jornadas")
        tree.heading("botellas", text="Botellas")
        tree.heading("puntos", text="Puntos")
        tree.column("puesto", width=80, anchor="center", stretch=True)
        tree.column("estudiante", width=220, anchor="w", stretch=True)
        tree.column("pet", width=160, anchor="center", stretch=True)
        tree.column("jornadas", width=110, anchor="center", stretch=True)
        tree.column("botellas", width=110, anchor="center", stretch=True)
        tree.column("puntos", width=110, anchor="center", stretch=True)
        tree.pack(fill="both", expand=True)
        scroll.config(command=tree.yview)

        try:
            filas = repositorio.ranking_participacion()
        except Exception:  # noqa: BLE001
            filas = []
        for puesto, (nombre, pet, jornadas, botellas) in enumerate(filas, start=1):
            pet_val = float(pet) if pet is not None else 0.0
            puntos = int(round(pet_val * 100))  # gamificación: 100 pts por kg de PET
            tree.insert("", "end", values=(
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

        # Catálogos para el cálculo
        try:
            self._proy_prod = repositorio.listar_producciones()          # (id, etiqueta, PesoObtenido_kg)
            self._proy_modelos = repositorio.listar_modelos_admin()      # (id, nombre, cat, tiempo_h, peso_g)
        except Exception:  # noqa: BLE001
            self._proy_prod, self._proy_modelos = [], []

        sel = tk.Frame(panel, bg=COLORS["surface_container"])
        sel.pack(fill="x", padx=20, pady=(0, 4))
        lbl = "Filamento producido:"
        if ctk:
            ctk.CTkLabel(sel, text=lbl, font=(FONT_FAMILY, 12, "bold"), text_color=COLORS["on_surface_variant"]).pack(anchor="w")
        else:
            tk.Label(sel, text=lbl, font=(FONT_FAMILY, 10, "bold"), bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"]).pack(anchor="w")

        prod_values = ["Seleccione filamento..."] + [lab for _, lab, _ in self._proy_prod]
        self._proy_peso_by_lbl = {lab: float(peso or 0) for _, lab, peso in self._proy_prod}
        if ctk:
            self._proy_combo = ctk.CTkOptionMenu(sel, values=prod_values, height=34, command=self._proy_calcular,
                                                 fg_color=COLORS["surface_lowest"], button_color=COLORS["surface_lowest"],
                                                 button_hover_color=COLORS["outline_variant"], dropdown_fg_color=COLORS["surface_container"],
                                                 dropdown_hover_color=COLORS["outline_variant"], text_color=COLORS["on_surface"])
            self._proy_combo.set(prod_values[0])
            self._proy_combo.pack(fill="x", pady=(2, 6))
            self._proy_var = None
        else:
            self._proy_var = tk.StringVar(value=prod_values[0])
            self._proy_combo = tk.OptionMenu(sel, self._proy_var, *prod_values, command=self._proy_calcular)
            self._proy_combo.config(bg=COLORS["surface_lowest"], fg=COLORS["on_surface"], highlightthickness=0, bd=0)
            self._proy_combo.pack(fill="x", pady=(2, 6))

        self._proy_msg = tk.Label(panel, text="Elige un filamento para ver cuántas piezas alcanzan.",
                                  bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"],
                                  font=(FONT_FAMILY, 10), wraplength=520, justify="left")
        self._proy_msg.pack(anchor="w", padx=20, pady=(0, 8))

        tf = tk.Frame(panel, bg=COLORS["surface_container"])
        tf.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        sb = ttk.Scrollbar(tf); sb.pack(side="right", fill="y")
        cols = ("modelo", "piezas", "porpieza", "sobrante", "tiempo")
        self._proy_tree = ttk.Treeview(tf, columns=cols, show="headings", style="Hist.Treeview", yscrollcommand=sb.set)
        self._proy_tree.heading("modelo", text="Modelo")
        self._proy_tree.heading("piezas", text="Piezas posibles")
        self._proy_tree.heading("porpieza", text="g/pieza")
        self._proy_tree.heading("sobrante", text="Sobrante (g)")
        self._proy_tree.heading("tiempo", text="Tiempo total (h)")
        self._proy_tree.column("modelo", width=170, anchor="w", stretch=True)
        self._proy_tree.column("piezas", width=120, anchor="center", stretch=True)
        self._proy_tree.column("porpieza", width=90, anchor="center", stretch=True)
        self._proy_tree.column("sobrante", width=110, anchor="center", stretch=True)
        self._proy_tree.column("tiempo", width=120, anchor="center", stretch=True)
        self._proy_tree.pack(fill="both", expand=True)
        sb.config(command=self._proy_tree.yview)

    def _proy_calcular(self, _choice=None):
        for it in self._proy_tree.get_children():
            self._proy_tree.delete(it)
        etiqueta = self._proy_combo.get() if ctk else self._proy_var.get()
        peso_kg = self._proy_peso_by_lbl.get(etiqueta)
        if peso_kg is None:
            self._proy_msg.configure(text="Elige un filamento para ver cuántas piezas alcanzan.")
            return
        disponible_g = peso_kg * 1000.0
        mejor = None
        for _id, nombre, _cat, tiempo_h, peso_g in self._proy_modelos:
            if not peso_g or float(peso_g) <= 0:
                self._proy_tree.insert("", "end", values=(nombre, "—", "—", "—", "—"))
                continue
            pg = float(peso_g)
            piezas = int(disponible_g // pg)
            sobrante = disponible_g - piezas * pg
            tiempo_total = (float(tiempo_h) * piezas) if tiempo_h else 0
            self._proy_tree.insert("", "end", values=(
                nombre, piezas, f"{pg:g}", f"{sobrante:.0f}", f"{tiempo_total:g}" if tiempo_h else "—"))
            if mejor is None or piezas > mejor[1]:
                mejor = (nombre, piezas, sobrante)
        if mejor and mejor[1] > 0:
            self._proy_msg.configure(text=(
                f"Con {peso_kg:g} kg ({disponible_g:.0f} g) de filamento alcanza para "
                f"{mejor[1]} {mejor[0]}, sobrando ~{mejor[2]:.0f} g. Mira la tabla para cada modelo."))
        else:
            self._proy_msg.configure(text="No alcanza para ningún modelo con ese filamento (o faltan pesos estimados en los modelos).")

    # --- Acciones / navegación ---
    def generar_informe(self):
        messagebox.showinfo("Generar informe",
                            "La generación de informes en PDF estará disponible próximamente.")

    def ir_a_inicio(self):
        if self.on_navigate:
            self.on_navigate("inicio")

    def ir_a_historico(self):
        # Ya estamos en histórico.
        return

    def on_registrar_select(self, choice):
        if hasattr(self, "registrar_btn") and ctk:
            self.registrar_btn.set("REGISTRAR ▾")
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
        import login_ui
        login_ui.main()
    else:
        main()
