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

class RecoleccionesForm(ctk.CTkFrame if ctk else tk.Frame):
    def __init__(self, parent, on_register_callback=None, **kwargs):
        self.on_register_callback = on_register_callback
        if ctk:
            super().__init__(parent, fg_color=COLORS["surface_container"], border_color=COLORS["primary_fixed"], border_width=1, corner_radius=12, **kwargs)
        else:
            super().__init__(parent, bg=COLORS["surface_container"], bd=1, relief="solid", **kwargs)
            
        self.setup_ui()

    def setup_ui(self):
        # Título
        if ctk:
            title = ctk.CTkLabel(self, text="Nueva Recolección", font=(FONT_FAMILY, 20, "bold"), text_color=COLORS["primary_fixed"])
            title.pack(pady=(25, 20))
        else:
            tk.Label(self, text="Nueva Recolección", font=(FONT_FAMILY, 16, "bold"), bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(pady=(20, 15))

        # Contenedor del formulario
        if ctk:
            form_frame = ctk.CTkFrame(self, fg_color="transparent")
        else:
            form_frame = tk.Frame(self, bg=COLORS["surface_container"])
        form_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # 1. Fecha del Registro
        self.create_label(form_frame, "Fecha del Registro")

        # Patch ttk style so DateEntry's internal Entry widget uses dark colors
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
                    form_frame,
                    placeholder_text="DD/MM/YYYY",
                    height=35,
                    fg_color=COLORS["surface_lowest"],
                    border_color=COLORS["outline_variant"],
                    text_color=COLORS["on_surface"],
                    font=(FONT_FAMILY, 13)
                )
                self.date_entry.insert(0, current_date)
                self.date_entry.pack(fill="x", pady=(2, 15))
            else:
                self.date_entry = tk.Entry(form_frame)
                self.date_entry.insert(0, current_date)
                self.date_entry.pack(fill="x", pady=(2, 10))

        # 2. Estudiante / Aportante
        self.create_label(form_frame, "Estudiante / Aportante")
        
        estudiantes = ["Seleccione estudiante...", "Arnaldo", "Miguel", "Juan", "María"]
        
        if ctk:
            self.student_combo = ctk.CTkOptionMenu(
                form_frame,
                values=estudiantes,
                height=35,
                fg_color=COLORS["surface_lowest"],
                button_color=COLORS["surface_lowest"],
                button_hover_color=COLORS["outline_variant"],
                dropdown_fg_color=COLORS["surface_container"],
                dropdown_hover_color=COLORS["outline_variant"],
                text_color=COLORS["on_surface"]
            )
            self.student_combo.set(estudiantes[0])
            self.student_combo.pack(fill="x", pady=(2, 2))
            
            # Subtítulo (Hint)
            hint_lbl = ctk.CTkLabel(form_frame, text="Se le asignarán los puntos automáticamente", font=(FONT_FAMILY, 10), text_color=COLORS["on_surface_variant"], wraplength=340, justify="left")
            hint_lbl.pack(anchor="w", pady=(0, 15))
        else:
            self.student_var = tk.StringVar(value=estudiantes[0])
            self.student_combo = tk.OptionMenu(form_frame, self.student_var, *estudiantes)
            self.student_combo.config(
                bg=COLORS["surface_lowest"], fg=COLORS["on_surface"],
                activebackground=COLORS["surface_high"], activeforeground=COLORS["on_surface"],
                highlightthickness=0, bd=0
            )
            self.student_combo.pack(fill="x", pady=(2, 2))
            tk.Label(form_frame, text="Se le asignarán los puntos automáticamente", font=(FONT_FAMILY, 8), bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"], wraplength=340, justify="left").pack(anchor="w", pady=(0, 10))

        # 3. Peso (kg)
        self.create_label(form_frame, "Peso (kg) aprovechado")
        
        if ctk:
            self.peso_entry = ctk.CTkEntry(
                form_frame,
                placeholder_text="Ej. 2.5",
                height=35,
                fg_color=COLORS["surface_lowest"],
                border_color=COLORS["outline_variant"],
                text_color=COLORS["on_surface"],
                font=(FONT_FAMILY, 13)
            )
            self.peso_entry.pack(fill="x", pady=(2, 15))
        else:
            self.peso_entry = tk.Entry(
                form_frame,
                bg=COLORS["surface_lowest"],
                fg=COLORS["on_surface"],
                insertbackground=COLORS["on_surface"],
                relief="flat",
                font=(FONT_FAMILY, 12)
            )
            self.peso_entry.pack(fill="x", pady=(2, 10), ipady=5)

        # 4. Observaciones
        self.create_label(form_frame, "Observaciones")
        
        if ctk:
            self.obs_textbox = ctk.CTkTextbox(
                form_frame,
                height=80,
                fg_color=COLORS["surface_lowest"],
                border_color=COLORS["outline_variant"],
                border_width=1,
                text_color=COLORS["on_surface"],
                font=(FONT_FAMILY, 13)
            )
            self.obs_textbox.insert("1.0", "Opcional...")
            self.obs_textbox.bind("<FocusIn>", lambda e: self.clear_placeholder(self.obs_textbox, "Opcional..."))
            self.obs_textbox.pack(fill="x", pady=(2, 25))
        else:
            self.obs_textbox = tk.Text(
                form_frame,
                height=4,
                width=1,  # el ancho real lo da fill="x"; evita el default de 80 columnas
                bg=COLORS["surface_lowest"],
                fg=COLORS["on_surface"],
                insertbackground=COLORS["on_surface"],
                relief="flat",
                font=(FONT_FAMILY, 12),
                wrap="word"
            )
            self.obs_textbox.pack(fill="x", pady=(2, 15), ipady=4)

        # 5. Botón Registrar
        if ctk:
            btn_registrar = ctk.CTkButton(
                form_frame,
                text="Registrar PET",
                font=(FONT_FAMILY, 14, "bold"),
                height=45,
                fg_color=COLORS["success"],
                hover_color=COLORS["success_hover"],
                text_color=COLORS["white"],
                corner_radius=8,
                command=self.registrar
            )
            btn_registrar.pack(fill="x")
        else:
            tk.Button(form_frame, text="Registrar PET", bg=COLORS["success"], fg=COLORS["white"], command=self.registrar).pack(fill="x")

    def create_label(self, parent, text):
        if ctk:
            lbl = ctk.CTkLabel(parent, text=text, font=(FONT_FAMILY, 12, "bold"), text_color=COLORS["on_surface_variant"])
            lbl.pack(anchor="w")
        else:
            tk.Label(parent, text=text, font=(FONT_FAMILY, 10, "bold"), bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"]).pack(anchor="w")

    def clear_placeholder(self, textbox, placeholder):
        content = textbox.get("1.0", "end-1c")
        if content.strip() == placeholder:
            textbox.delete("1.0", "end")

    def registrar(self):
        fecha = self.date_entry.get()
        estudiante = self.student_combo.get() if ctk else self.student_var.get()
        peso = self.peso_entry.get()

        obs = self.obs_textbox.get("1.0", "end-1c")
        if obs.strip() == "Opcional...":
            obs = ""

        if not peso.strip():
            messagebox.showwarning("Error", "Debe ingresar el peso aprovechado.")
            return
            
        try:
            float(peso)
        except ValueError:
            messagebox.showwarning("Error", "El peso debe ser un número válido.")
            return
            
        if estudiante == "Seleccione estudiante...":
            messagebox.showwarning("Error", "Debe seleccionar un estudiante.")
            return

        msg = f"Registro Exitoso:\n\nFecha: {fecha}\nEstudiante: {estudiante}\nPeso: {peso} kg\nObservaciones: {obs}"
        messagebox.showinfo("Recolección Registrada", msg)
        
        if self.on_register_callback:
            self.on_register_callback(fecha, estudiante, peso, obs)
            
        self.peso_entry.delete(0, 'end')
        self.obs_textbox.delete("1.0", "end")
        self.obs_textbox.insert("1.0", "Opcional...")
        if ctk:
            self.student_combo.set("Seleccione estudiante...")
        else:
            self.student_var.set("Seleccione estudiante...")


class RecentRecordsFrame(ctk.CTkFrame if ctk else tk.Frame):
    def __init__(self, parent, **kwargs):
        if ctk:
            super().__init__(parent, fg_color=COLORS["surface_container"], border_color=COLORS["primary_fixed"], border_width=1, corner_radius=12, **kwargs)
        else:
            super().__init__(parent, bg=COLORS["surface_container"], bd=1, relief="solid", **kwargs)
            
        self.setup_ui()

    def setup_ui(self):
        if ctk:
            title = ctk.CTkLabel(self, text="Últimos Registros", font=(FONT_FAMILY, 18, "bold"), text_color=COLORS["primary_fixed"])
            title.pack(pady=(20, 15), padx=20, anchor="w")
        else:
            tk.Label(self, text="Últimos Registros", font=(FONT_FAMILY, 16, "bold"), bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(pady=(20, 15), padx=20, anchor="w")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Recent.Treeview",
                        background=COLORS["surface"],
                        foreground=COLORS["on_surface"],
                        rowheight=35,
                        fieldbackground=COLORS["surface"],
                        bordercolor=COLORS["outline_variant"],
                        borderwidth=0,
                        font=(FONT_FAMILY, 11))
        style.map('Recent.Treeview', background=[('selected', COLORS["surface_low"])])
        style.configure("Recent.Treeview.Heading",
                        background=COLORS["surface_high"],
                        foreground=COLORS["on_surface_variant"],
                        relief="flat",
                        font=(FONT_FAMILY, 11, "bold"))
        style.map("Recent.Treeview.Heading", background=[('active', COLORS["surface_bright"])])

        tree_frame = tk.Frame(self, bg=COLORS["surface_container"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")

        columns = ("fecha", "estudiante", "peso", "observaciones")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Recent.Treeview", yscrollcommand=tree_scroll.set)
        
        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("estudiante", text="Estudiante")
        self.tree.heading("peso", text="Peso (kg)")
        self.tree.heading("observaciones", text="Observaciones")

        self.tree.column("fecha", width=120, anchor="center", stretch=True)
        self.tree.column("estudiante", width=200, anchor="w", stretch=True)
        self.tree.column("peso", width=120, anchor="center", stretch=True)
        self.tree.column("observaciones", width=350, anchor="w", stretch=True)

        self.tree.pack(fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)

        # Datos de prueba iniciales
        self.insert_record("07/08/2026", "Arnaldo", "2.5", "Botellas limpias")
        self.insert_record("07/08/2026", "María", "1.2", "")
        self.insert_record("06/08/2026", "Juan", "5.0", "Incluye tapas")

    def insert_record(self, fecha, estudiante, peso, obs):
        self.tree.insert("", "0", values=(fecha, estudiante, peso, obs))


class RecoleccionesApp:
    def __init__(self, root, on_navigate=None, on_logout=None):
        self.root = root
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.root.title("VorTrack - Recolecciones")
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
        navbar_outer = tk.Frame(self.main_container, bg=COLORS["surface_container"], height=70)
        navbar_outer.pack(fill="x", side="top")
        navbar_outer.pack_propagate(False)

        # Bottom Border
        border_bottom = tk.Frame(self.main_container, bg=COLORS["outline_variant"], height=1)
        border_bottom.pack(fill="x", side="top")

        navbar_content = tk.Frame(navbar_outer, bg=COLORS["surface_container"])
        navbar_content.pack(fill="both", expand=True, padx=24, pady=10)

        # Left: Brand Logo & Title
        brand_frame = tk.Frame(navbar_content, bg=COLORS["surface_container"])
        brand_frame.pack(side="left")

        # Navbar Icon
        self.nav_icon_img = self.load_ctk_image(self.icon_path, size=(38, 38))
        if self.nav_icon_img:
            if ctk:
                icon_lbl = ctk.CTkLabel(brand_frame, image=self.nav_icon_img, text="")
            else:
                icon_lbl = tk.Label(brand_frame, image=self.nav_icon_img, bg=COLORS["surface_container"])
            icon_lbl.pack(side="left", padx=(0, 10))

        brand_text = tk.Label(
            brand_frame,
            text="VorTrack",
            fg=COLORS["primary_fixed"],
            bg=COLORS["surface_container"],
            font=(FONT_FAMILY, 20, "bold")
        )
        brand_text.pack(side="left")

        # Center Navigation Menu
        nav_items_frame = tk.Frame(navbar_content, bg=COLORS["surface_container"])
        nav_items_frame.pack(side="left", expand=True)

        # Item 1: Quienes Somos (vuelve a la página de inicio)
        lbl_quienes = tk.Label(
            nav_items_frame,
            text="QUIÉNES SOMOS",
            fg=COLORS["on_surface_variant"],
            bg=COLORS["surface_container"],
            font=(FONT_FAMILY, 10, "bold"),
            cursor="hand2"
        )
        lbl_quienes.pack(side="left", padx=16)
        lbl_quienes.bind("<Button-1>", lambda _e: self.ir_a_inicio())

        # Item 2: Registrar Dropdown Button
        if ctk:
            self.registrar_btn = ctk.CTkOptionMenu(
                nav_items_frame,
                values=["REGISTRAR ▾", "Recolección", "Transformación", "Impresión"],
                fg_color=COLORS["surface_container"],
                button_color=COLORS["surface_high"],
                button_hover_color=COLORS["surface_bright"],
                text_color=COLORS["on_surface_variant"],
                dropdown_fg_color=COLORS["surface_container"],
                dropdown_hover_color=COLORS["surface_bright"],
                dropdown_text_color=COLORS["on_surface"],
                font=(FONT_FAMILY, 11, "bold"),
                dynamic_resizing=False,
                width=130,
                height=32,
                corner_radius=12,
                command=self.on_registrar_select
            )
            self.registrar_btn.set("REGISTRAR ▾")
            self.registrar_btn.pack(side="left", padx=10)
        else:
            registrar_btn = tk.Menubutton(
                nav_items_frame,
                text="REGISTRAR ▾",
                fg=COLORS["on_surface_variant"],
                bg=COLORS["surface_container"],
                activebackground=COLORS["surface_bright"],
                activeforeground=COLORS["primary_fixed"],
                font=(FONT_FAMILY, 10, "bold"),
                bd=0,
                cursor="hand2"
            )
            registrar_menu = tk.Menu(registrar_btn, tearoff=0, bg=COLORS["surface_container"], fg=COLORS["on_surface"])
            registrar_menu.add_command(label="Recolección", command=lambda: self.on_registrar_select("Recolección"))
            registrar_menu.add_command(label="Transformación", command=lambda: self.on_registrar_select("Transformación"))
            registrar_menu.add_command(label="Impresión", command=lambda: self.on_registrar_select("Impresión"))
            registrar_btn.config(menu=registrar_menu)
            registrar_btn.pack(side="left", padx=16)

        # Item 3: Histórico Informes
        if ctk:
            btn_historico = ctk.CTkButton(
                nav_items_frame,
                text="HISTÓRICO INFORMES",
                fg_color="transparent",
                hover_color=COLORS["surface_bright"],
                text_color=COLORS["on_surface_variant"],
                font=(FONT_FAMILY, 11, "bold"),
                height=32,
                corner_radius=12,
                command=lambda: print("Navigating to Histórico Informes")
            )
            btn_historico.pack(side="left", padx=10)
        else:
            lbl_historico = tk.Label(
                nav_items_frame,
                text="HISTÓRICO INFORMES",
                fg=COLORS["on_surface_variant"],
                bg=COLORS["surface_container"],
                font=(FONT_FAMILY, 10, "bold"),
                cursor="hand2"
            )
            lbl_historico.pack(side="left", padx=16)

        # Right Action: Logout Button
        if ctk:
            btn_logout = ctk.CTkButton(
                navbar_content,
                text="Logout",
                fg_color=COLORS["surface_low"],
                hover_color=COLORS["surface_bright"],
                border_color=COLORS["outline_variant"],
                border_width=1,
                text_color=COLORS["on_surface"],
                font=(FONT_FAMILY, 11, "bold"),
                corner_radius=12,
                width=100,
                height=36,
                command=self.logout
            )
            btn_logout.pack(side="right")
        else:
            btn_logout = tk.Button(
                navbar_content,
                text="Logout",
                fg=COLORS["on_surface"],
                bg=COLORS["surface_low"],
                activebackground=COLORS["surface_bright"],
                activeforeground=COLORS["primary_fixed"],
                font=(FONT_FAMILY, 10, "bold"),
                bd=1,
                relief="solid",
                padx=16,
                pady=6,
                cursor="hand2",
                command=self.logout
            )
            btn_logout.pack(side="right")

    def build_main_content(self):
        self.canvas_frame = tk.Frame(self.main_container, bg=COLORS["background"])
        self.canvas_frame.pack(fill="both", expand=True, padx=40, pady=20)

        # grid con anchos deterministas: el formulario a la izquierda (ancho fijo)
        # y el panel de registros ocupando el resto. Evita que el form invada la derecha.
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=0, minsize=440)
        self.canvas_frame.grid_columnconfigure(1, weight=1)

        self.form = RecoleccionesForm(self.canvas_frame, on_register_callback=self.on_new_record)
        self.form.grid(row=0, column=0, sticky="nsew", padx=(0, 20), pady=10)

        self.recent_records = RecentRecordsFrame(self.canvas_frame)
        self.recent_records.grid(row=0, column=1, sticky="nsew", pady=10)

    def on_new_record(self, fecha, estudiante, peso, obs):
        self.recent_records.insert_record(fecha, estudiante, peso, obs)

    def build_footer(self):
        border_top = tk.Frame(self.main_container, bg=COLORS["outline_variant"], height=1)
        border_top.pack(fill="x", side="top")

        footer_frame = tk.Frame(self.main_container, bg=COLORS["surface_lowest"], height=65)
        footer_frame.pack(fill="x", side="bottom")
        footer_frame.pack_propagate(False)

        footer_content = tk.Frame(footer_frame, bg=COLORS["surface_lowest"])
        footer_content.pack(fill="both", expand=True, padx=24, pady=10)

        left_foot = tk.Frame(footer_content, bg=COLORS["surface_lowest"])
        left_foot.pack(side="left")

        brand_lbl = tk.Label(left_foot, text="VorTrack", fg=COLORS["primary_fixed"], bg=COLORS["surface_lowest"], font=(FONT_FAMILY, 12, "bold"))
        brand_lbl.pack(side="left", padx=(0, 10))

        copy_lbl = tk.Label(left_foot, text="© 2026 desarrollado por Miguel Ruiz Ramirez", fg=COLORS["on_surface_variant"], bg=COLORS["surface_lowest"], font=(FONT_FAMILY, 9))
        copy_lbl.pack(side="left")

        right_foot = tk.Frame(footer_content, bg=COLORS["surface_lowest"])
        right_foot.pack(side="right")

        for link in ["Privacidad", "Términos de Uso", "Contacto", "Soporte Técnico"]:
            lbl_link = tk.Label(right_foot, text=link, fg=COLORS["on_surface_variant"], bg=COLORS["surface_lowest"], font=(FONT_FAMILY, 9, "bold"))
            lbl_link.pack(side="left", padx=10)
            ui_utils.bind_footer_link(
                lbl_link, self.root, link,
                base_fg=COLORS["on_surface_variant"],
                hover_fg=COLORS["primary_fixed"]
            )

    def ir_a_inicio(self):
        if self.on_navigate:
            self.on_navigate("inicio")

    def on_registrar_select(self, choice):
        # Restaura la etiqueta del menú (solo en la versión ctk).
        if hasattr(self, "registrar_btn") and ctk:
            self.registrar_btn.set("REGISTRAR ▾")

        if choice == "Recolección":
            # Ya estamos en la página de recolecciones.
            return
        if choice in ("Transformación", "Impresión"):
            messagebox.showinfo(choice, f"El módulo de {choice} estará disponible próximamente.")

    def logout(self):
        if messagebox.askyesno("Cerrar sesión", "¿Desea cerrar sesión en VorTrack?"):
            if self.on_logout:
                self.on_logout()
            else:
                auth.logout()
                self.root.destroy()

def main():
    auth.require_auth()

    if ctk:
        root = ctk.CTk()
    else:
        root = tk.Tk()
        
    RecoleccionesApp(root)
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
