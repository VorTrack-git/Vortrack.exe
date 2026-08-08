import os
import tkinter as tk


from tkinter import messagebox, ttk
from datetime import datetime

import auth
import ui_utils
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

RESPONSABLES = ["Seleccione responsable...", "Arnaldo", "Miguel", "Juan", "María"]
ESTADOS = ["Seleccione estado...", "Exitosa", "Con fallas", "Fallida"]


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

        # 2. Responsable
        self.create_label(form_frame, "Responsable")
        if ctk:
            self.resp_combo = ctk.CTkOptionMenu(
                form_frame, values=RESPONSABLES, height=35,
                fg_color=COLORS["surface_lowest"], button_color=COLORS["surface_lowest"],
                button_hover_color=COLORS["outline_variant"], dropdown_fg_color=COLORS["surface_container"],
                dropdown_hover_color=COLORS["outline_variant"], text_color=COLORS["on_surface"]
            )
            self.resp_combo.set(RESPONSABLES[0])
            self.resp_combo.pack(fill="x", pady=(2, 15))
        else:
            self.resp_var = tk.StringVar(value=RESPONSABLES[0])
            self.resp_combo = tk.OptionMenu(form_frame, self.resp_var, *RESPONSABLES)
            self.resp_combo.config(bg=COLORS["surface_lowest"], fg=COLORS["on_surface"],
                                   activebackground=COLORS["surface_high"], activeforeground=COLORS["on_surface"],
                                   highlightthickness=0, bd=0)
            self.resp_combo.pack(fill="x", pady=(2, 10))

        # 3. Objeto / material didáctico
        self.create_label(form_frame, "Objeto / material didáctico")
        self.objeto_entry = self._make_entry(form_frame, "Ej. Engranaje, molécula, regla...")

        # 4. Cantidad de piezas
        self.create_label(form_frame, "Cantidad de piezas")
        self.piezas_entry = self._make_entry(form_frame, "Ej. 3")

        # 5. Filamento utilizado (g)
        self.create_label(form_frame, "Filamento utilizado (g)")
        self.filamento_entry = self._make_entry(form_frame, "Ej. 120")

        # 6. Tiempo de impresión (h)
        self.create_label(form_frame, "Tiempo de impresión (h)")
        self.tiempo_entry = self._make_entry(form_frame, "Ej. 2.5")

        # 7. Estado
        self.create_label(form_frame, "Estado")
        if ctk:
            self.estado_combo = ctk.CTkOptionMenu(
                form_frame, values=ESTADOS, height=35,
                fg_color=COLORS["surface_lowest"], button_color=COLORS["surface_lowest"],
                button_hover_color=COLORS["outline_variant"], dropdown_fg_color=COLORS["surface_container"],
                dropdown_hover_color=COLORS["outline_variant"], text_color=COLORS["on_surface"]
            )
            self.estado_combo.set(ESTADOS[0])
            self.estado_combo.pack(fill="x", pady=(2, 15))
        else:
            self.estado_var = tk.StringVar(value=ESTADOS[0])
            self.estado_combo = tk.OptionMenu(form_frame, self.estado_var, *ESTADOS)
            self.estado_combo.config(bg=COLORS["surface_lowest"], fg=COLORS["on_surface"],
                                     activebackground=COLORS["surface_high"], activeforeground=COLORS["on_surface"],
                                     highlightthickness=0, bd=0)
            self.estado_combo.pack(fill="x", pady=(2, 10))

        # 8. Observaciones
        self.create_label(form_frame, "Observaciones")
        if ctk:
            self.obs_textbox = ctk.CTkTextbox(
                form_frame, height=70, fg_color=COLORS["surface_lowest"],
                border_color=COLORS["outline_variant"], border_width=1,
                text_color=COLORS["on_surface"], font=(FONT_FAMILY, 13)
            )
            self.obs_textbox.insert("1.0", "Opcional...")
            self.obs_textbox.bind("<FocusIn>", lambda e: self.clear_placeholder(self.obs_textbox, "Opcional..."))
            self.obs_textbox.pack(fill="x", pady=(2, 25))
        else:
            self.obs_textbox = tk.Text(
                form_frame, height=3, width=1,
                bg=COLORS["surface_lowest"], fg=COLORS["on_surface"],
                insertbackground=COLORS["on_surface"], relief="flat",
                font=(FONT_FAMILY, 12), wrap="word"
            )
            self.obs_textbox.pack(fill="x", pady=(2, 15), ipady=4)

        # 9. Botón Registrar
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
        responsable = self.resp_combo.get() if ctk else self.resp_var.get()
        estado = self.estado_combo.get() if ctk else self.estado_var.get()
        objeto = self.objeto_entry.get().strip()
        piezas = self.piezas_entry.get()
        filamento = self.filamento_entry.get()
        tiempo = self.tiempo_entry.get()

        obs = self.obs_textbox.get("1.0", "end-1c")
        if obs.strip() == "Opcional...":
            obs = ""

        if responsable == RESPONSABLES[0]:
            messagebox.showwarning("Error", "Debe seleccionar un responsable.")
            return
        if not objeto:
            messagebox.showwarning("Error", "Debe indicar el objeto o material didáctico.")
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
            tiempo_val = float(tiempo)
        except ValueError:
            messagebox.showwarning("Error", "El filamento (g) y el tiempo (h) deben ser números válidos.")
            return
        if filamento_val <= 0 or tiempo_val <= 0:
            messagebox.showwarning("Error", "El filamento y el tiempo deben ser mayores que cero.")
            return

        if estado == ESTADOS[0]:
            messagebox.showwarning("Error", "Debe seleccionar el estado de la impresión.")
            return

        msg = (f"Impresión Registrada:\n\n"
               f"Fecha: {fecha}\nResponsable: {responsable}\nObjeto: {objeto}\n"
               f"Piezas: {piezas_val}\nFilamento: {filamento_val} g\nTiempo: {tiempo_val} h\n"
               f"Estado: {estado}\nObservaciones: {obs}")
        messagebox.showinfo("Impresión Registrada", msg)

        if self.on_register_callback:
            self.on_register_callback(
                fecha, responsable, objeto, str(piezas_val),
                f"{filamento_val:g}", f"{tiempo_val:g}", estado, obs
            )

        self.objeto_entry.delete(0, 'end')
        self.piezas_entry.delete(0, 'end')
        self.filamento_entry.delete(0, 'end')
        self.tiempo_entry.delete(0, 'end')
        self.obs_textbox.delete("1.0", "end")
        self.obs_textbox.insert("1.0", "Opcional...")
        if ctk:
            self.resp_combo.set(RESPONSABLES[0])
            self.estado_combo.set(ESTADOS[0])
        else:
            self.resp_var.set(RESPONSABLES[0])
            self.estado_var.set(ESTADOS[0])


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

        columns = ("fecha", "responsable", "objeto", "piezas", "filamento", "tiempo", "estado", "observaciones")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Impr.Treeview", yscrollcommand=tree_scroll.set)

        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("responsable", text="Responsable")
        self.tree.heading("objeto", text="Objeto")
        self.tree.heading("piezas", text="Piezas")
        self.tree.heading("filamento", text="Filamento (g)")
        self.tree.heading("tiempo", text="Tiempo (h)")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("observaciones", text="Observaciones")

        self.tree.column("fecha", width=95, anchor="center", stretch=True)
        self.tree.column("responsable", width=110, anchor="w", stretch=True)
        self.tree.column("objeto", width=160, anchor="w", stretch=True)
        self.tree.column("piezas", width=70, anchor="center", stretch=True)
        self.tree.column("filamento", width=100, anchor="center", stretch=True)
        self.tree.column("tiempo", width=90, anchor="center", stretch=True)
        self.tree.column("estado", width=90, anchor="center", stretch=True)
        self.tree.column("observaciones", width=180, anchor="w", stretch=True)

        self.tree.pack(fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)

        # Datos de prueba iniciales
        self.insert_record("07/08/2026", "Arnaldo", "Engranaje didáctico", "4", "120", "2.5", "Exitosa", "Buen acabado")
        self.insert_record("06/08/2026", "María", "Molécula H₂O", "1", "45", "1.0", "Con fallas", "Warping leve")
        self.insert_record("05/08/2026", "Juan", "Regla graduada", "6", "90", "1.8", "Exitosa", "")

    def insert_record(self, fecha, responsable, objeto, piezas, filamento, tiempo, estado, obs):
        self.tree.insert("", "0", values=(fecha, responsable, objeto, piezas, filamento, tiempo, estado, obs))


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

    def on_new_record(self, *values):
        self.recent_records.insert_record(*values)

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
