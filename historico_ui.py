import os
import tkinter as tk
from tkinter import messagebox, ttk

import auth
import ui_utils

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from PIL import Image, ImageTk

COLORS = ui_utils.COLORS
FONT_FAMILY = ui_utils.FONT_FAMILY

# Indicadores de ejemplo (en memoria, sin backend todavía).
KPIS = [
    ("PET recolectado", "12.5 kg", "🧴"),
    ("Filamento producido", "9.8 kg", "🧵"),
    ("Desperdicio", "2.7 kg", "♻"),
    ("Objetos impresos", "24", "🖨"),
    ("Estudiantes activos", "8", "👥"),
    ("CO₂ evitado (est.)", "31 kg", "🌱"),
]

# Ranking de participación (gamificación).
RANKING = [
    ("1", "Arnaldo", "5.0", "8", "480"),
    ("2", "María", "3.7", "6", "360"),
    ("3", "Juan", "2.4", "6", "300"),
    ("4", "Otros", "1.4", "4", "160"),
]


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

        if os.path.exists(self.icon_path):
            try:
                icon_img = Image.open(self.icon_path)
                self.icon_photo = ImageTk.PhotoImage(icon_img)
                self.root.iconphoto(False, self.icon_photo)
            except Exception:
                pass

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

        # Fila de indicadores (KPIs)
        kpi_row = tk.Frame(outer, bg=COLORS["background"])
        kpi_row.pack(fill="x", pady=(0, 20))
        for titulo, valor, icono in KPIS:
            self._kpi_card(kpi_row, titulo, valor, icono)

        # Panel de ranking (gamificación)
        self._build_ranking(outer)

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
            panel.pack(fill="both", expand=True)
        else:
            panel = tk.Frame(parent, bg=COLORS["surface_container"], bd=1, relief="solid")
            panel.pack(fill="both", expand=True)

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

        cols = ("puesto", "estudiante", "pet", "impresiones", "puntos")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", style="Hist.Treeview", yscrollcommand=scroll.set)
        tree.heading("puesto", text="Puesto")
        tree.heading("estudiante", text="Estudiante")
        tree.heading("pet", text="PET aportado (kg)")
        tree.heading("impresiones", text="Impresiones")
        tree.heading("puntos", text="Puntos")
        tree.column("puesto", width=90, anchor="center", stretch=True)
        tree.column("estudiante", width=220, anchor="w", stretch=True)
        tree.column("pet", width=180, anchor="center", stretch=True)
        tree.column("impresiones", width=140, anchor="center", stretch=True)
        tree.column("puntos", width=140, anchor="center", stretch=True)
        tree.pack(fill="both", expand=True)
        scroll.config(command=tree.yview)

        for row in RANKING:
            tree.insert("", "end", values=row)

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
