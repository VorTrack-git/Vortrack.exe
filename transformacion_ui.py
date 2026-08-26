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

RESPONSABLES = ["Seleccione responsable...", "Arnaldo", "Miguel", "Juan", "María"]


class TransformacionForm(ctk.CTkFrame if ctk else tk.Frame):
    """Formulario para registrar la producción de filamento 3D a partir de PET (extrusión)."""

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
            title = ctk.CTkLabel(self, text="Nueva Transformación", font=(FONT_FAMILY, 20, "bold"), text_color=COLORS["primary_fixed"])
            title.pack(pady=(25, 4))
            sub = ctk.CTkLabel(self, text="Producción de filamento 3D (extrusión de PET)", font=(FONT_FAMILY, 11), text_color=COLORS["on_surface_variant"])
            sub.pack(pady=(0, 16))
        else:
            tk.Label(self, text="Nueva Transformación", font=(FONT_FAMILY, 16, "bold"), bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(pady=(20, 2))
            tk.Label(self, text="Producción de filamento 3D (extrusión de PET)", font=(FONT_FAMILY, 9), bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"]).pack(pady=(0, 12))

        # Contenedor del formulario
        if ctk:
            form_frame = ctk.CTkFrame(self, fg_color="transparent")
        else:
            form_frame = tk.Frame(self, bg=COLORS["surface_container"])
        form_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # 1. Fecha del Registro
        self.create_label(form_frame, "Fecha del Registro")

        # Estilo ttk para que el Entry interno del DateEntry use colores oscuros
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

        # 2. Jornada de recolección (origen del PET; su PesoPET es el peso ingresado)
        try:
            self.jornadas = repositorio.listar_jornadas()
        except Exception as exc:  # noqa: BLE001
            self.jornadas = []
            messagebox.showwarning("Base de datos", f"No se pudieron cargar las jornadas:\n{exc}")
        self._jornada_by_label = {lab: (idj, peso) for idj, lab, peso in self.jornadas}

        self.create_label(form_frame, "Jornada de recolección (origen del PET)")
        jornada_values = ["Seleccione jornada..."] + [lab for _, lab, _ in self.jornadas]
        self.jornada_combo, self.jornada_var = self._make_combo(
            form_frame, jornada_values, command=self._on_jornada)

        # 3. Peso ingresado (kg) — automático desde la jornada seleccionada
        self.create_label(form_frame, "Peso ingresado (kg) — PET de la jornada")
        self.ingresado_entry = self._make_entry(form_frame, "")
        self._set_readonly(self.ingresado_entry, "—")

        # 4. Peso salido (kg)
        self.create_label(form_frame, "Peso salido (kg) — filamento")
        self.salido_entry = self._make_entry(form_frame, "Ej. 1.7")
        self.salido_entry.bind("<KeyRelease>", self._update_desperdicio)

        # 5. Desperdicio (kg) — calculado automáticamente (ingresado - salido)
        self.create_label(form_frame, "Desperdicio (kg) — automático")
        self.desperdicio_entry = self._make_entry(form_frame, "")
        self._set_readonly(self.desperdicio_entry, "—")

        # 6. Color del filamento
        self.create_label(form_frame, "Color del filamento")
        self.color_entry = self._make_entry(form_frame, "Ej. Translúcido, Azul...")

        # 7. Diámetro (mm)
        self.create_label(form_frame, "Diámetro (mm)")
        self.diam_entry = self._make_entry(form_frame, "Ej. 1.75")

        # 8. Metros de filamento producidos
        self.create_label(form_frame, "Metros de filamento producidos")
        self.metros_entry = self._make_entry(form_frame, "Ej. 560")

        # 7. Observaciones
        self.create_label(form_frame, "Observaciones")

        if ctk:
            self.obs_textbox = ctk.CTkTextbox(
                form_frame,
                height=70,
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
                height=3,
                width=1,  # el ancho real lo da fill="x"; evita el default de 80 columnas
                bg=COLORS["surface_lowest"],
                fg=COLORS["on_surface"],
                insertbackground=COLORS["on_surface"],
                relief="flat",
                font=(FONT_FAMILY, 12),
                wrap="word"
            )
            self.obs_textbox.pack(fill="x", pady=(2, 15), ipady=4)

        # 8. Botón Registrar
        if ctk:
            btn_registrar = ctk.CTkButton(
                form_frame,
                text="Registrar Filamento",
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
            tk.Button(form_frame, text="Registrar Filamento", bg=COLORS["success"], fg=COLORS["white"], command=self.registrar).pack(fill="x")

    def _make_entry(self, parent, placeholder):
        """Crea un campo de texto (ctk o tk) con el estilo del formulario."""
        if ctk:
            entry = ctk.CTkEntry(
                parent,
                placeholder_text=placeholder,
                height=35,
                fg_color=COLORS["surface_lowest"],
                border_color=COLORS["outline_variant"],
                text_color=COLORS["on_surface"],
                font=(FONT_FAMILY, 13)
            )
            entry.pack(fill="x", pady=(2, 15))
        else:
            entry = tk.Entry(
                parent,
                bg=COLORS["surface_lowest"],
                fg=COLORS["on_surface"],
                insertbackground=COLORS["on_surface"],
                relief="flat",
                font=(FONT_FAMILY, 12),
                readonlybackground=COLORS["surface_low"]
            )
            entry.pack(fill="x", pady=(2, 10), ipady=5)
        return entry

    def _make_combo(self, parent, values, command=None):
        """Desplegable (ctk o tk). Devuelve (widget, var) — var es None en ctk."""
        if ctk:
            cb = ctk.CTkOptionMenu(
                parent, values=values, height=35, command=command,
                fg_color=COLORS["surface_lowest"], button_color=COLORS["surface_lowest"],
                button_hover_color=COLORS["outline_variant"], dropdown_fg_color=COLORS["surface_container"],
                dropdown_hover_color=COLORS["outline_variant"], text_color=COLORS["on_surface"])
            cb.set(values[0])
            cb.pack(fill="x", pady=(2, 15))
            return cb, None
        var = tk.StringVar(value=values[0])
        cb = tk.OptionMenu(parent, var, *values, command=command)
        cb.config(bg=COLORS["surface_lowest"], fg=COLORS["on_surface"],
                  activebackground=COLORS["surface_high"], activeforeground=COLORS["on_surface"],
                  highlightthickness=0, bd=0)
        cb.pack(fill="x", pady=(2, 10))
        return cb, var

    def _on_jornada(self, choice):
        """Al elegir jornada, muestra su PesoPET como 'peso ingresado' y recalcula."""
        info = self._jornada_by_label.get(choice)
        self._set_readonly(self.ingresado_entry, f"{info[1]:.2f}" if info else "—")
        self._update_desperdicio()

    def _set_readonly(self, entry, text):
        """Escribe un valor en un campo y lo deja de solo lectura."""
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, text)
        entry.configure(state="disabled" if ctk else "readonly")

    def _update_desperdicio(self, event=None):
        """Recalcula el desperdicio en vivo a partir del peso ingresado y salido."""
        try:
            ingresado = float(self.ingresado_entry.get())
            salido = float(self.salido_entry.get())
            desperdicio = ingresado - salido
            texto = f"{desperdicio:.2f}" if desperdicio >= 0 else "—"
        except ValueError:
            texto = "—"
        self._set_readonly(self.desperdicio_entry, texto)

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
        jornada_label = self.jornada_combo.get() if ctk else self.jornada_var.get()
        salido = self.salido_entry.get().strip()
        metros = self.metros_entry.get().strip()
        color = self.color_entry.get().strip()
        diam = self.diam_entry.get().strip()

        obs = self.obs_textbox.get("1.0", "end-1c")
        if obs.strip() == "Opcional...":
            obs = ""

        info = self._jornada_by_label.get(jornada_label)
        if info is None:
            messagebox.showwarning("Error", "Debe seleccionar la jornada de recolección de origen.")
            return
        id_jornada, ingresado_val = info

        if not salido:
            messagebox.showwarning("Error", "Debe ingresar el peso salido (filamento).")
            return
        try:
            salido_val = float(salido)
        except ValueError:
            messagebox.showwarning("Error", "El peso salido debe ser un número válido.")
            return
        if salido_val <= 0:
            messagebox.showwarning("Error", "El peso salido debe ser mayor que cero.")
            return
        if salido_val > ingresado_val:
            messagebox.showwarning(
                "Error", f"El peso salido no puede superar el ingresado ({ingresado_val:g} kg).")
            return

        if not metros:
            messagebox.showwarning("Error", "Debe ingresar los metros de filamento producidos.")
            return
        try:
            metros_val = float(metros)
        except ValueError:
            messagebox.showwarning("Error", "Los metros deben ser un número válido.")
            return
        if metros_val <= 0:
            messagebox.showwarning("Error", "Los metros deben ser mayores que cero.")
            return

        diam_val = None
        if diam:
            try:
                diam_val = float(diam)
            except ValueError:
                messagebox.showwarning("Error", "El diámetro debe ser un número válido.")
                return

        try:
            id_prod = repositorio.crear_produccion(
                id_jornada, fecha, color or None, diam_val, salido_val, metros_val, obs)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error al guardar",
                                 f"No se pudo registrar en la base de datos:\n\n{exc}")
            return

        desperdicio_val = ingresado_val - salido_val
        messagebox.showinfo(
            "Transformación Registrada",
            f"Producción #{id_prod} registrada.\nDesperdicio calculado: {desperdicio_val:.2f} kg")

        self.salido_entry.delete(0, 'end')
        self.metros_entry.delete(0, 'end')
        self.color_entry.delete(0, 'end')
        self.diam_entry.delete(0, 'end')
        self._set_readonly(self.ingresado_entry, "—")
        self._set_readonly(self.desperdicio_entry, "—")
        self.obs_textbox.delete("1.0", "end")
        self.obs_textbox.insert("1.0", "Opcional...")
        if ctk:
            self.jornada_combo.set("Seleccione jornada...")
        else:
            self.jornada_var.set("Seleccione jornada...")

        if self.on_register_callback:
            self.on_register_callback()


class RecentTransformacionesFrame(ctk.CTkFrame if ctk else tk.Frame):
    def __init__(self, parent, **kwargs):
        if ctk:
            super().__init__(parent, fg_color=COLORS["surface_container"], border_color=COLORS["primary_fixed"], border_width=1, corner_radius=12, **kwargs)
        else:
            super().__init__(parent, bg=COLORS["surface_container"], bd=1, relief="solid", **kwargs)

        self.setup_ui()

    def setup_ui(self):
        if ctk:
            title = ctk.CTkLabel(self, text="Historial de Filamento", font=(FONT_FAMILY, 18, "bold"), text_color=COLORS["primary_fixed"])
            title.pack(pady=(20, 15), padx=20, anchor="w")
        else:
            tk.Label(self, text="Historial de Filamento", font=(FONT_FAMILY, 16, "bold"), bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(pady=(20, 15), padx=20, anchor="w")

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Transf.Treeview",
                        background=COLORS["surface"],
                        foreground=COLORS["on_surface"],
                        rowheight=35,
                        fieldbackground=COLORS["surface"],
                        bordercolor=COLORS["outline_variant"],
                        borderwidth=0,
                        font=(FONT_FAMILY, 11))
        style.map('Transf.Treeview', background=[('selected', COLORS["surface_low"])])
        style.configure("Transf.Treeview.Heading",
                        background=COLORS["surface_high"],
                        foreground=COLORS["on_surface_variant"],
                        relief="flat",
                        font=(FONT_FAMILY, 11, "bold"))
        style.map("Transf.Treeview.Heading", background=[('active', COLORS["surface_bright"])])

        tree_frame = tk.Frame(self, bg=COLORS["surface_container"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")

        columns = ("fecha", "jornada", "ingresado", "salido", "desperdicio", "color", "diametro", "metros", "observaciones")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", style="Transf.Treeview", yscrollcommand=tree_scroll.set)

        self.tree.heading("fecha", text="Fecha")
        self.tree.heading("jornada", text="Jornada")
        self.tree.heading("ingresado", text="Ingresado (kg)")
        self.tree.heading("salido", text="Salido (kg)")
        self.tree.heading("desperdicio", text="Desperdicio (kg)")
        self.tree.heading("color", text="Color")
        self.tree.heading("diametro", text="Diám. (mm)")
        self.tree.heading("metros", text="Metros (m)")
        self.tree.heading("observaciones", text="Observaciones")

        self.tree.column("fecha", width=90, anchor="center", stretch=True)
        self.tree.column("jornada", width=70, anchor="center", stretch=True)
        self.tree.column("ingresado", width=100, anchor="center", stretch=True)
        self.tree.column("salido", width=90, anchor="center", stretch=True)
        self.tree.column("desperdicio", width=110, anchor="center", stretch=True)
        self.tree.column("color", width=100, anchor="w", stretch=True)
        self.tree.column("diametro", width=85, anchor="center", stretch=True)
        self.tree.column("metros", width=90, anchor="center", stretch=True)
        self.tree.column("observaciones", width=170, anchor="w", stretch=True)

        self.tree.pack(fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)

        self.recargar()

    def recargar(self):
        """Recarga el historial desde la base de datos."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            filas = repositorio.producciones_recientes()
        except Exception:  # noqa: BLE001
            return
        for fecha, id_jornada, color, diametro, peso_pet, peso_obt, metros, obs in filas:
            f = fecha.strftime("%d/%m/%Y") if hasattr(fecha, "strftime") else (str(fecha) if fecha else "")
            ingresado = float(peso_pet) if peso_pet is not None else 0.0
            salido = float(peso_obt) if peso_obt is not None else 0.0
            desperdicio = max(ingresado - salido, 0.0)
            self.tree.insert("", "end", values=(
                f, f"#{id_jornada}" if id_jornada is not None else "",
                f"{ingresado:g}", f"{salido:g}", f"{desperdicio:.2f}",
                color or "", f"{float(diametro):g}" if diametro is not None else "",
                f"{float(metros):g}" if metros is not None else "", obs or ""))


class TransformacionApp:
    def __init__(self, root, on_navigate=None, on_logout=None):
        self.root = root
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.root.title("VorTrack - Transformación")
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
        navbar_outer = tk.Frame(self.main_container, bg=COLORS["surface_container"], height=70)
        navbar_outer.pack(fill="x", side="top")
        navbar_outer.pack_propagate(False)

        border_bottom = tk.Frame(self.main_container, bg=COLORS["outline_variant"], height=1)
        border_bottom.pack(fill="x", side="top")

        navbar_content = tk.Frame(navbar_outer, bg=COLORS["surface_container"])
        navbar_content.pack(fill="both", expand=True, padx=24, pady=10)

        # Left: Brand Logo & Title
        brand_frame = tk.Frame(navbar_content, bg=COLORS["surface_container"])
        brand_frame.pack(side="left")

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
                command=self.ir_a_historico
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
            lbl_historico.bind("<Button-1>", lambda _e: self.ir_a_historico())

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
        # y el panel de registros ocupando el resto.
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=0, minsize=440)
        self.canvas_frame.grid_columnconfigure(1, weight=1)

        self.form = TransformacionForm(self.canvas_frame, on_register_callback=self.on_new_record)
        self.form.grid(row=0, column=0, sticky="nsew", padx=(0, 20), pady=10)

        self.recent_records = RecentTransformacionesFrame(self.canvas_frame)
        self.recent_records.grid(row=0, column=1, sticky="nsew", pady=10)

    def on_new_record(self):
        self.recent_records.recargar()

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

        if choice == "Transformación":
            # Ya estamos en la página de transformación.
            return
        destinos = {"Recolección": "recoleccion", "Impresión": "impresion"}
        if choice in destinos and self.on_navigate:
            self.on_navigate(destinos[choice])

    def ir_a_historico(self):
        if self.on_navigate:
            self.on_navigate("historico")

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

    TransformacionApp(root)
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
