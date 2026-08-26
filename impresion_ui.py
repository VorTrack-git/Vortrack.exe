import os
import tkinter as tk


from tkinter import messagebox, ttk
from datetime import datetime

import auth
import ui_utils
import repositorio
try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None

from PIL import Image, ImageTk

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

COLORS = {
    "background": "#051424",
    "surface_lowest": "#010f1f",
    "surface_low": "#0d1c2d",
    "surface_container": "#122131",
    "surface_high": "#1c2b3c",
    "surface_highest": "#273647",
    "surface_bright": "#2c3a4c",
    "primary": "#dbfcff",
    "primary_fixed": "#7df4ff",
    "primary_fixed_dim": "#00dbe9",
    "primary_container": "#00f0ff",
    "secondary_container": "#0056fd",
    "on_surface": "#d4e4fa",
    "on_surface_variant": "#b9cacb",
    "outline_variant": "#3b494b",
    "error": "#ffb4ab",
    "error_container": "#93000a",
    "white": "#ffffff",
    "success": "#2e7d32",
    "success_hover": "#1b5e20",
    "surface": "#0d1117"
}

FONT_FAMILY = "Segoe UI"

# Estados permitidos por el CHECK constraint de FabricacionObjetos.Estado
ESTADOS = ["Seleccione estado...", "En proceso", "Finalizado", "Fallido"]


class ImpresionForm(ctk.CTkFrame if ctk else tk.Frame):
    """Formulario para registrar impresiones 3D de material didáctico."""

    def __init__(self, parent, on_register_callback=None, **kwargs):
        self.on_register_callback = on_register_callback
        if ctk:
            super().__init__(parent, fg_color=COLORS["surface_container"], border_color=COLORS["primary_fixed"], border_width=1, corner_radius=12, **kwargs)
        else:
            super().__init__(parent, bg=COLORS["surface_container"], bd=1, relief="solid", **kwargs)

        self.setup_ui()

    def setup_ui(self):
        if ctk:
            title = ctk.CTkLabel(self, text="Nueva Impresión", font=(FONT_FAMILY, 20, "bold"), text_color=COLORS["primary_fixed"])
            title.pack(pady=(25, 4))
            sub = ctk.CTkLabel(self, text="Fabricación de material didáctico (impresión 3D)", font=(FONT_FAMILY, 11), text_color=COLORS["on_surface_variant"])
            sub.pack(pady=(0, 16))
        else:
            tk.Label(self, text="Nueva Impresión", font=(FONT_FAMILY, 16, "bold"), bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(pady=(20, 2))
            tk.Label(self, text="Fabricación de material didáctico (impresión 3D)", font=(FONT_FAMILY, 9), bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"]).pack(pady=(0, 12))

        if ctk:
            form_frame = ctk.CTkFrame(self, fg_color="transparent")
        else:
            form_frame = tk.Frame(self, bg=COLORS["surface_container"])
        form_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # 1. Fecha del Registro
        self.create_label(form_frame, "Fecha del Registro")

        _style = ttk.Style()
        _style.theme_use("default")
        _style.configure("DateEntry",
                         fieldbackground=COLORS["surface_lowest"],
                         background=COLORS["surface_lowest"],
                         foreground=COLORS["on_surface"],
                         arrowcolor=COLORS["primary_fixed"],
                         bordercolor=COLORS["outline_variant"],
                         lightcolor=COLORS["outline_variant"],
                         darkcolor=COLORS["outline_variant"])
        _style.map("DateEntry",
                   fieldbackground=[("readonly", COLORS["surface_lowest"])],
                   foreground=[("readonly", COLORS["on_surface"])])

        if DateEntry:
            self.date_entry = DateEntry(
                form_frame,
                width=12,
                background=COLORS["primary_fixed"],
                foreground=COLORS["background"],
                bordercolor=COLORS["outline_variant"],
                headersbackground=COLORS["surface_container"],
                headersforeground=COLORS["on_surface"],
                selectbackground=COLORS["primary_fixed"],
                selectforeground=COLORS["background"],
                normalbackground=COLORS["surface_lowest"],
                normalforeground=COLORS["on_surface"],
                weekendbackground=COLORS["surface_low"],
                weekendforeground=COLORS["on_surface"],
                othermonthforeground=COLORS["on_surface_variant"],
                othermonthbackground=COLORS["surface_low"],
                othermonthweforeground=COLORS["on_surface_variant"],
                othermonthwebackground=COLORS["surface_low"],
                date_pattern='dd/mm/yyyy',
                font=(FONT_FAMILY, 12)
            )
            self.date_entry.pack(fill="x", pady=(2, 15), ipady=5)
        else:
            current_date = datetime.now().strftime("%d/%m/%Y")
            if ctk:
                self.date_entry = ctk.CTkEntry(
                    form_frame, placeholder_text="DD/MM/YYYY", height=35,
                    fg_color=COLORS["surface_lowest"], border_color=COLORS["outline_variant"],
                    text_color=COLORS["on_surface"], font=(FONT_FAMILY, 13)
                )
                self.date_entry.insert(0, current_date)
                self.date_entry.pack(fill="x", pady=(2, 15))
            else:
                self.date_entry = tk.Entry(form_frame)
                self.date_entry.insert(0, current_date)
                self.date_entry.pack(fill="x", pady=(2, 10))

        # Catálogos desde la base de datos (FK obligatorias)
        try:
            self.modelos = repositorio.listar_modelos()
            self.producciones = repositorio.listar_producciones()
        except Exception as exc:  # noqa: BLE001
            self.modelos, self.producciones = [], []
            messagebox.showwarning("Base de datos", f"No se pudieron cargar los catálogos:\n{exc}")
        self._modelo_by_name = {n: i for i, n in self.modelos}
        self._prod_by_label = {lab: idp for idp, lab, _ in self.producciones}

        # 2. Modelo (material didáctico)
        self.create_label(form_frame, "Modelo (material didáctico)")
        modelo_values = ["Seleccione modelo..."] + [n for _, n in self.modelos]
        self.modelo_combo, self.modelo_var = self._make_combo(form_frame, modelo_values)

        # 3. Producción de filamento utilizada
        self.create_label(form_frame, "Filamento utilizado (producción)")
        prod_values = ["Seleccione producción..."] + [lab for _, lab, _ in self.producciones]
        self.prod_combo, self.prod_var = self._make_combo(form_frame, prod_values)

        # 4. Cantidad de piezas
        self.create_label(form_frame, "Cantidad de piezas")
        self.piezas_entry = self._make_entry(form_frame, "Ej. 3")

        # 5. Peso de filamento utilizado (g)
        self.create_label(form_frame, "Peso de filamento utilizado (g)")
        self.filamento_entry = self._make_entry(form_frame, "Ej. 120")

        # 6. Tiempo de impresión (min)
        self.create_label(form_frame, "Tiempo de impresión (min)")
        self.tiempo_entry = self._make_entry(form_frame, "Ej. 150")

        # 7. Estado
        self.create_label(form_frame, "Estado")
        self.estado_combo, self.estado_var = self._make_combo(form_frame, ESTADOS)

        # 8. Botón Registrar
        if ctk:
            btn_registrar = ctk.CTkButton(
                form_frame, text="Registrar Impresión", font=(FONT_FAMILY, 14, "bold"),
                height=45, fg_color=COLORS["success"], hover_color=COLORS["success_hover"],
                text_color=COLORS["white"], corner_radius=8, command=self.registrar
            )
            btn_registrar.pack(fill="x")
        else:
            tk.Button(form_frame, text="Registrar Impresión", bg=COLORS["success"], fg=COLORS["white"], command=self.registrar).pack(fill="x")

    def _make_entry(self, parent, placeholder):
        if ctk:
            entry = ctk.CTkEntry(
                parent, placeholder_text=placeholder, height=35,
                fg_color=COLORS["surface_lowest"], border_color=COLORS["outline_variant"],
                text_color=COLORS["on_surface"], font=(FONT_FAMILY, 13)
            )
            entry.pack(fill="x", pady=(2, 15))
        else:
            entry = tk.Entry(
                parent, bg=COLORS["surface_lowest"], fg=COLORS["on_surface"],
                insertbackground=COLORS["on_surface"], relief="flat", font=(FONT_FAMILY, 12)
            )
            entry.pack(fill="x", pady=(2, 10), ipady=5)
        return entry

    def _make_combo(self, parent, values):
        """Desplegable (ctk o tk). Devuelve (widget, var) — var es None en ctk."""
        if ctk:
            cb = ctk.CTkOptionMenu(
                parent, values=values, height=35,
                fg_color=COLORS["surface_lowest"], button_color=COLORS["surface_lowest"],
                button_hover_color=COLORS["outline_variant"], dropdown_fg_color=COLORS["surface_container"],
                dropdown_hover_color=COLORS["outline_variant"], text_color=COLORS["on_surface"])
            cb.set(values[0])
            cb.pack(fill="x", pady=(2, 15))
            return cb, None
        var = tk.StringVar(value=values[0])
        cb = tk.OptionMenu(parent, var, *values)
        cb.config(bg=COLORS["surface_lowest"], fg=COLORS["on_surface"],
                  activebackground=COLORS["surface_high"], activeforeground=COLORS["on_surface"],
                  highlightthickness=0, bd=0)
        cb.pack(fill="x", pady=(2, 10))
        return cb, var

    def create_label(self, parent, text):
        if ctk:
            ctk.CTkLabel(parent, text=text, font=(FONT_FAMILY, 12, "bold"), text_color=COLORS["on_surface_variant"]).pack(anchor="w")
        else:
            tk.Label(parent, text=text, font=(FONT_FAMILY, 10, "bold"), bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"]).pack(anchor="w")

    def clear_placeholder(self, textbox, placeholder):
        if textbox.get("1.0", "end-1c").strip() == placeholder:
            textbox.delete("1.0", "end")

    def registrar(self):
        fecha = self.date_entry.get()
        modelo_name = self.modelo_combo.get() if ctk else self.modelo_var.get()
        prod_label = self.prod_combo.get() if ctk else self.prod_var.get()
        estado = self.estado_combo.get() if ctk else self.estado_var.get()
        piezas = self.piezas_entry.get().strip()
        filamento = self.filamento_entry.get().strip()
        tiempo = self.tiempo_entry.get().strip()

        id_modelo = self._modelo_by_name.get(modelo_name)
        id_prod = self._prod_by_label.get(prod_label)
        if id_modelo is None:
            messagebox.showwarning("Error", "Debe seleccionar un modelo.")
            return
        if id_prod is None:
            messagebox.showwarning("Error", "Debe seleccionar la producción de filamento utilizada.")
            return

        try:
            piezas_val = int(piezas)
        except ValueError:
            messagebox.showwarning("Error", "La cantidad de piezas debe ser un número entero.")
            return
        if piezas_val <= 0:
            messagebox.showwarning("Error", "La cantidad de piezas debe ser mayor que cero.")
            return

        try:
            filamento_val = float(filamento)
        except ValueError:
            messagebox.showwarning("Error", "El peso de filamento (g) debe ser un número válido.")
            return
        try:
            tiempo_val = int(float(tiempo))
        except ValueError:
            messagebox.showwarning("Error", "El tiempo (min) debe ser un número válido.")
            return
        if filamento_val <= 0 or tiempo_val <= 0:
            messagebox.showwarning("Error", "El filamento y el tiempo deben ser mayores que cero.")
            return

        if estado == ESTADOS[0]:
            messagebox.showwarning("Error", "Debe seleccionar el estado de la impresión.")
            return

        try:
            id_fab = repositorio.crear_fabricacion(
                id_modelo, id_prod, fecha, piezas_val, filamento_val, tiempo_val, estado)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error al guardar",
                                 f"No se pudo registrar en la base de datos:\n\n{exc}")
            return

        messagebox.showinfo("Impresión Registrada", f"Fabricación #{id_fab} registrada correctamente.")

        self.piezas_entry.delete(0, 'end')
        self.filamento_entry.delete(0, 'end')
        self.tiempo_entry.delete(0, 'end')
        if ctk:
            self.modelo_combo.set("Seleccione modelo...")
            self.prod_combo.set("Seleccione producción...")
            self.estado_combo.set(ESTADOS[0])
        else:
            self.modelo_var.set("Seleccione modelo...")
            self.prod_var.set("Seleccione producción...")
            self.estado_var.set(ESTADOS[0])

        if self.on_register_callback:
            self.on_register_callback()


class RecentImpresionesFrame(ctk.CTkFrame if ctk else tk.Frame):
    def __init__(self, parent, **kwargs):
        if ctk:
            super().__init__(parent, fg_color=COLORS["surface_container"], border_color=COLORS["primary_fixed"], border_width=1, corner_radius=12, **kwargs)
        else:
            super().__init__(parent, bg=COLORS["surface_container"], bd=1, relief="solid", **kwargs)
        self.setup_ui()

    def setup_ui(self):
        if ctk:
            ctk.CTkLabel(self, text="Historial de Impresiones", font=(FONT_FAMILY, 18, "bold"), text_color=COLORS["primary_fixed"]).pack(pady=(20, 15), padx=20, anchor="w")
        else:
            tk.Label(self, text="Historial de Impresiones", font=(FONT_FAMILY, 16, "bold"), bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(pady=(20, 15), padx=20, anchor="w")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Impr.Treeview",
                        background=COLORS["surface"], foreground=COLORS["on_surface"],
                        rowheight=35, fieldbackground=COLORS["surface"],
                        bordercolor=COLORS["outline_variant"], borderwidth=0, font=(FONT_FAMILY, 11))
        style.map('Impr.Treeview', background=[('selected', COLORS["surface_low"])])
        style.configure("Impr.Treeview.Heading",
                        background=COLORS["surface_high"], foreground=COLORS["on_surface_variant"],
                        relief="flat", font=(FONT_FAMILY, 11, "bold"))
        style.map("Impr.Treeview.Heading", background=[('active', COLORS["surface_bright"])])

        tree_frame = tk.Frame(self, bg=COLORS["surface_container"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")

        columns = ("fecha", "modelo", "produccion", "piezas", "filamento", "tiempo", "estado")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Impr.Treeview", yscrollcommand=tree_scroll.set)

        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("modelo", text="Modelo")
        self.tree.heading("produccion", text="Filamento")
        self.tree.heading("piezas", text="Piezas")
        self.tree.heading("filamento", text="Peso (g)")
        self.tree.heading("tiempo", text="Tiempo (min)")
        self.tree.heading("estado", text="Estado")

        self.tree.column("fecha", width=95, anchor="center", stretch=True)
        self.tree.column("modelo", width=190, anchor="w", stretch=True)
        self.tree.column("produccion", width=90, anchor="center", stretch=True)
        self.tree.column("piezas", width=70, anchor="center", stretch=True)
        self.tree.column("filamento", width=90, anchor="center", stretch=True)
        self.tree.column("tiempo", width=100, anchor="center", stretch=True)
        self.tree.column("estado", width=100, anchor="center", stretch=True)

        self.tree.pack(fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)

        self.recargar()

    def recargar(self):
        """Recarga el historial desde la base de datos."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            filas = repositorio.fabricaciones_recientes()
        except Exception:  # noqa: BLE001
            return
        for fecha, modelo, cantidad, peso, tiempo, estado, id_prod in filas:
            f = fecha.strftime("%d/%m/%Y") if hasattr(fecha, "strftime") else (str(fecha) if fecha else "")
            peso_txt = f"{float(peso):g}" if peso is not None else ""
            self.tree.insert("", "end", values=(
                f, modelo or "", f"#{id_prod}" if id_prod is not None else "",
                cantidad if cantidad is not None else "", peso_txt,
                tiempo if tiempo is not None else "", estado or ""))


class ImpresionApp:
    PAGE = "impresion"

    def __init__(self, root, on_navigate=None, on_logout=None):
        self.root = root
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.root.title("VorTrack - Impresión")
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
        self.build_navbar()
        self.build_main_content()
        self.build_footer()

    def build_navbar(self):
        ui_utils.build_app_navbar(self)

    def build_main_content(self):
        self.canvas_frame = tk.Frame(self.main_container, bg=COLORS["background"])
        self.canvas_frame.pack(fill="both", expand=True, padx=40, pady=20)

        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=0, minsize=440)
        self.canvas_frame.grid_columnconfigure(1, weight=1)

        self.form = ImpresionForm(self.canvas_frame, on_register_callback=self.on_new_record)
        self.form.grid(row=0, column=0, sticky="nsew", padx=(0, 20), pady=10)

        self.recent_records = RecentImpresionesFrame(self.canvas_frame)
        self.recent_records.grid(row=0, column=1, sticky="nsew", pady=10)

    def on_new_record(self):
        self.recent_records.recargar()

    def build_footer(self):
        ui_utils.build_app_footer(self)

    # --- Navegación ---
    def ir_a_inicio(self):
        if self.on_navigate:
            self.on_navigate("inicio")

    def ir_a_historico(self):
        if self.on_navigate:
            self.on_navigate("historico")

    def on_registrar_select(self, choice):
        if hasattr(self, "registrar_btn") and ctk:
            self.registrar_btn.set("REGISTRAR ▾")
        destinos = {"Recolección": "recoleccion", "Transformación": "transformacion", "Impresión": "impresion"}
        target = destinos.get(choice)
        if target and target != self.PAGE and self.on_navigate:
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
    ImpresionApp(root)
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
