"""
admin_ui.py
Panel de administración de VorTrack. Solo accesible para el rol Administrador.

Ofrece CRUD sobre:
  - Estudiantes  (cuentas de login = Usuarios rol Estudiante + Responsables)
  - Recolecciones (JornadasRecoleccion)

Los cambios se guardan en la base y se reflejan en el resto del sistema al
recargar cada página. Todas las consultas corren en hilos con el spinner
encima de la sección (las de cada sección, en paralelo), así la ventana nunca
se congela mientras responde la base.
"""

import os
import tkinter as tk
from tkinter import messagebox, ttk

import servicios.auth as auth
import interfaz.ui_utils as ui_utils
import datos.repositorio as repositorio
import servicios.validaciones as validaciones
from interfaz.ui_cargando import RETARDO_S, cargar_con_spinner, ejecutar_con_spinner
from interfaz.ui_tema import COLORS, FONT_FAMILY

try:
    import customtkinter as ctk
except ImportError:
    ctk = None


class AdminApp:
    PAGE = "admin"

    def __init__(self, root, on_navigate=None, on_logout=None, datos=None):
        self.root = root
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.datos = datos or repositorio
        self.root.title("VorTrack - Panel de administración")
        self.root.minsize(1024, 700)
        ui_utils.maximize_window(self.root)
        self.root.configure(bg=COLORS["background"])
        ui_utils.set_window_icon(self.root)
        if ctk:
            ctk.set_appearance_mode("Dark")
            ctk.set_default_color_theme("blue")

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = ui_utils.ruta_logo("VorTrack icon.png")

        self._seccion = "estudiantes"
        self._ocupado = False  # hay una consulta/guardado en curso en la sección
        self._est_selected = None
        self._rec_selected = None

        self.main_container = tk.Frame(self.root, bg=COLORS["background"])
        self.main_container.pack(fill="both", expand=True)
        self._build_topbar()

        self.content = tk.Frame(self.main_container, bg=COLORS["background"])
        self.content.pack(fill="both", expand=True)
        self._show_estudiantes()

    # ---------------------------------------------------------------- widgets
    def _card(self, parent):
        if ctk:
            c = ctk.CTkFrame(parent, fg_color=COLORS["surface_container"],
                             border_color=COLORS["primary_fixed"], border_width=1, corner_radius=12)
        else:
            c = tk.Frame(parent, bg=COLORS["surface_container"], bd=1, relief="solid")
        return c

    def _label(self, parent, text):
        if ctk:
            ctk.CTkLabel(parent, text=text, font=(FONT_FAMILY, 12, "bold"),
                         text_color=COLORS["on_surface_variant"]).pack(anchor="w", pady=(8, 0))
        else:
            tk.Label(parent, text=text, font=(FONT_FAMILY, 10, "bold"), bg=COLORS["surface_container"],
                     fg=COLORS["on_surface_variant"]).pack(anchor="w", pady=(8, 0))

    def _field(self, parent, label):
        self._label(parent, label)
        if ctk:
            e = ctk.CTkEntry(parent, height=34, fg_color=COLORS["surface_lowest"],
                             border_color=COLORS["outline_variant"], text_color=COLORS["on_surface"],
                             font=(FONT_FAMILY, 13))
            e.pack(fill="x", pady=(2, 0))
        else:
            e = tk.Entry(parent, bg=COLORS["surface_lowest"], fg=COLORS["on_surface"],
                         insertbackground=COLORS["on_surface"], relief="flat", font=(FONT_FAMILY, 12))
            e.pack(fill="x", pady=(2, 0), ipady=4)
        return e

    def _combo(self, parent, label, values):
        self._label(parent, label)
        if ctk:
            cb = ctk.CTkOptionMenu(parent, values=values, height=34,
                                   fg_color=COLORS["surface_lowest"], button_color=COLORS["surface_lowest"],
                                   button_hover_color=COLORS["outline_variant"],
                                   dropdown_fg_color=COLORS["surface_container"],
                                   dropdown_hover_color=COLORS["outline_variant"], text_color=COLORS["on_surface"])
            cb.set(values[0])
            cb.pack(fill="x", pady=(2, 0))
            return cb, None
        var = tk.StringVar(value=values[0])
        cb = tk.OptionMenu(parent, var, *values)
        cb.config(bg=COLORS["surface_lowest"], fg=COLORS["on_surface"], activebackground=COLORS["surface_high"],
                  activeforeground=COLORS["on_surface"], highlightthickness=0, bd=0)
        cb.pack(fill="x", pady=(2, 0))
        return cb, var

    def _button(self, parent, text, command, color=None, side="left"):
        color = color or COLORS["secondary_container"]
        if ctk:
            b = ctk.CTkButton(parent, text=text, command=command, height=38, corner_radius=8,
                              fg_color=color, hover_color=COLORS["primary_container"],
                              text_color=COLORS["white"], font=(FONT_FAMILY, 12, "bold"))
            b.pack(side=side, padx=4, pady=(14, 0), fill="x", expand=True)
        else:
            b = tk.Button(parent, text=text, command=command, bg=color, fg=COLORS["white"],
                          activebackground=COLORS["primary_container"], activeforeground=COLORS["white"],
                          relief="flat", bd=0, font=(FONT_FAMILY, 11, "bold"), padx=10, pady=8, cursor="hand2")
            b.pack(side=side, padx=4, pady=(14, 0), fill="x", expand=True)
        return b

    def _tree(self, parent, columns, headings, widths, style_name):
        style = ttk.Style()
        style.theme_use("default")
        style.configure(style_name, background=COLORS["surface"], foreground=COLORS["on_surface"],
                        rowheight=32, fieldbackground=COLORS["surface"], bordercolor=COLORS["outline_variant"],
                        borderwidth=0, font=(FONT_FAMILY, 11))
        style.map(style_name, background=[('selected', COLORS["secondary_container"])])
        style.configure(style_name + ".Heading", background=COLORS["surface_high"],
                        foreground=COLORS["on_surface_variant"], relief="flat", font=(FONT_FAMILY, 11, "bold"))
        style.map(style_name + ".Heading", background=[('active', COLORS["surface_bright"])])

        frame = tk.Frame(parent, bg=COLORS["surface_container"])
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        sb = ttk.Scrollbar(frame)
        sb.pack(side="right", fill="y")
        tree = ttk.Treeview(frame, columns=columns, show="headings", style=style_name, yscrollcommand=sb.set)
        for col, head, w in zip(columns, headings, widths):
            tree.heading(col, text=head, command=lambda c=col, t=None: self._sort_tree(tree, c))
            anchor = "center" if w[1] else "w"
            tree.column(col, width=w[0], anchor=anchor, stretch=True)
        tree.pack(fill="both", expand=True)
        sb.config(command=tree.yview)
        return tree

    def _sort_tree(self, tree, col):
        """Ordena la tabla al hacer clic en el encabezado (organizar)."""
        data = [(tree.set(k, col), k) for k in tree.get_children("")]
        def _key(v):
            try:
                return float(str(v[0]).replace(",", "."))
            except ValueError:
                return str(v[0]).lower()
        reverse = getattr(tree, "_sort_reverse", {}).get(col, False)
        data.sort(key=_key, reverse=reverse)
        for i, (_, k) in enumerate(data):
            tree.move(k, "", i)
        if not hasattr(tree, "_sort_reverse"):
            tree._sort_reverse = {}
        tree._sort_reverse[col] = not reverse

    def _title(self, parent, text):
        if ctk:
            ctk.CTkLabel(parent, text=text, font=(FONT_FAMILY, 18, "bold"),
                         text_color=COLORS["primary_fixed"]).pack(anchor="w", padx=16, pady=(16, 12))
        else:
            tk.Label(parent, text=text, font=(FONT_FAMILY, 15, "bold"), bg=COLORS["surface_container"],
                     fg=COLORS["primary_fixed"]).pack(anchor="w", padx=16, pady=(16, 12))

    # ----------------------------------------------------------------- topbar
    def _build_topbar(self):
        bar = tk.Frame(self.main_container, bg=COLORS["surface_container"], height=64)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)
        tk.Frame(self.main_container, bg=COLORS["outline_variant"], height=1).pack(fill="x", side="top")

        left = tk.Frame(bar, bg=COLORS["surface_container"])
        left.pack(side="left", padx=20)
        icon = ui_utils.load_image(self.icon_path, (34, 34))
        if icon:
            self._navicon = icon
            (ctk.CTkLabel(left, image=icon, text="") if ctk
             else tk.Label(left, image=icon, bg=COLORS["surface_container"])).pack(side="left", padx=(0, 10))
        tk.Label(left, text="VorTrack · Administración", fg=COLORS["primary_fixed"],
                 bg=COLORS["surface_container"], font=(FONT_FAMILY, 17, "bold")).pack(side="left")

        # Selector de sección
        seg = tk.Frame(bar, bg=COLORS["surface_container"])
        seg.pack(side="left", padx=30)
        self._seg_buttons = {}
        secciones = [("estudiantes", "ESTUDIANTES"), ("lugares", "LUGARES"), ("modelos", "MODELOS"),
                     ("recolecciones", "RECOLECCIONES"), ("transformaciones", "TRANSFORMACIONES"),
                     ("impresiones", "IMPRESIONES")]
        for key, text in secciones:
            b = tk.Label(seg, text=text, font=(FONT_FAMILY, 10, "bold"), cursor="hand2",
                         bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"], padx=8, pady=6)
            b.pack(side="left", padx=4)
            b.bind("<Button-1>", lambda _e, k=key: self._cambiar_seccion(k))
            self._seg_buttons[key] = b

        right = tk.Frame(bar, bg=COLORS["surface_container"])
        right.pack(side="right", padx=20)
        tk.Button(right, text="Ir al sistema", command=self.ir_al_sistema, bg=COLORS["surface_low"],
                  fg=COLORS["on_surface"], activebackground=COLORS["surface_bright"], relief="flat", bd=0,
                  font=(FONT_FAMILY, 10, "bold"), padx=14, pady=6, cursor="hand2").pack(side="left", padx=6)
        tk.Button(right, text="Logout", command=self.logout, bg=COLORS["surface_low"], fg=COLORS["on_surface"],
                  activebackground=COLORS["surface_bright"], relief="solid", bd=1,
                  font=(FONT_FAMILY, 10, "bold"), padx=14, pady=6, cursor="hand2").pack(side="left", padx=6)

    def _cambiar_seccion(self, key):
        self._seccion = key
        for k, b in self._seg_buttons.items():
            b.configure(fg=COLORS["primary_fixed"] if k == key else COLORS["on_surface_variant"])
        {"estudiantes": self._show_estudiantes,
         "lugares": self._show_lugares,
         "modelos": self._show_modelos,
         "recolecciones": self._show_recolecciones,
         "transformaciones": self._show_transformaciones,
         "impresiones": self._show_impresiones}[key]()

    def _clear_content(self):
        # Lo que estuviera en curso muere con la sección (su spinner se destruye).
        self._ocupado = False
        for w in self.content.winfo_children():
            w.destroy()

    # ------------------------------------------------------------ ESTUDIANTES
    def _show_estudiantes(self):
        self._clear_content()
        self._cambiar_seg_highlight("estudiantes")
        self._est_selected = None

        wrap = self._wrap = tk.Frame(self.content, bg=COLORS["background"])
        wrap.pack(fill="both", expand=True, padx=30, pady=20)
        wrap.grid_columnconfigure(0, weight=0, minsize=360)
        wrap.grid_columnconfigure(1, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        # --- Formulario ---
        form = self._card(wrap)
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        fi = tk.Frame(form, bg=COLORS["surface_container"])
        fi.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(fi, text="Datos del estudiante", font=(FONT_FAMILY, 16, "bold"),
                 bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(anchor="w", pady=(0, 4))

        self.e_nombres = self._field(fi, "Nombres")
        self.e_apellidos = self._field(fi, "Apellidos")
        self.e_correo = self._field(fi, "Correo (usuario de acceso)")
        self.e_telefono = self._field(fi, "Teléfono")
        self.e_pass = self._field(fi, "Contraseña")
        self.e_estado_combo, self.e_estado_var = self._combo(fi, "Estado", ["Activo", "Inactivo"])

        row1 = tk.Frame(fi, bg=COLORS["surface_container"]); row1.pack(fill="x")
        self._button(row1, "Guardar nuevo", self._est_guardar_nuevo, COLORS["success"])
        self._button(row1, "Editar", self._est_actualizar, COLORS["secondary_container"])
        row2 = tk.Frame(fi, bg=COLORS["surface_container"]); row2.pack(fill="x")
        self._button(row2, "Refrescar", self._est_refrescar, COLORS["surface_high"])

        # --- Tabla ---
        tablecard = self._card(wrap)
        tablecard.grid(row=0, column=1, sticky="nsew")
        self._title(tablecard, "Estudiantes registrados")
        cols = ("id", "nombres", "apellidos", "correo", "telefono", "pass", "estado")
        heads = ("#", "Nombres", "Apellidos", "Correo", "Teléfono", "Contraseña", "Estado")
        widths = [(45, True), (110, False), (110, False), (200, False), (110, True), (120, False), (80, True)]
        self.est_tree = self._tree(tablecard, cols, heads, widths, "AdmEst.Treeview")
        self.est_tree.bind("<<TreeviewSelect>>", self._est_on_select)

        actions = tk.Frame(tablecard, bg=COLORS["surface_container"])
        actions.pack(fill="x", padx=16, pady=(0, 14))
        tk.Button(actions, text="Eliminar seleccionado", command=self._est_eliminar,
                  bg=COLORS["error_container"], fg=COLORS["white"], activebackground="#b71c1c",
                  relief="flat", bd=0, font=(FONT_FAMILY, 11, "bold"), padx=14, pady=7, cursor="hand2").pack(side="left")

        # Al abrir la sección se "presiona" Refrescar para mostrar los datos de una vez.
        self._est_refrescar()

    @staticmethod
    def _est_valores(n, fila):
        # Se muestra un número de fila secuencial (#) en vez del IdUsuario interno.
        idu, nom, ape, correo, tel, pwd, estado = fila
        return idu, (n, nom or "", ape or "", correo or "", tel or "", pwd or "", estado or "")

    def _cambiar_seg_highlight(self, key):
        if hasattr(self, "_seg_buttons"):
            for k, b in self._seg_buttons.items():
                b.configure(fg=COLORS["primary_fixed"] if k == key else COLORS["on_surface_variant"])

    def _est_recargar(self):
        self._cargar_tabla(self.est_tree, self.datos.listar_estudiantes, self._est_valores, "Cargando estudiantes…")

    def _est_operar(self, escribir, titulo, **kw):
        self._operar(escribir, self.est_tree, self.datos.listar_estudiantes, self._est_valores, titulo, **kw)

    def _est_on_select(self, _event=None):
        sel = self.est_tree.selection()
        if not sel:
            return
        vals = self.est_tree.item(sel[0], "values")
        self._est_selected = int(sel[0])  # iid = IdUsuario real (no la columna visible)
        self._set(self.e_nombres, vals[1]); self._set(self.e_apellidos, vals[2])
        self._set(self.e_correo, vals[3]); self._set(self.e_telefono, vals[4])
        self._set(self.e_pass, vals[5])
        if ctk:
            self.e_estado_combo.set(vals[6] or "Activo")
        else:
            self.e_estado_var.set(vals[6] or "Activo")

    def _est_leer(self):
        nombres = self.e_nombres.get().strip()
        apellidos = self.e_apellidos.get().strip()
        correo = self.e_correo.get().strip()
        telefono = self.e_telefono.get().strip()
        pwd = self.e_pass.get().strip()
        estado = self.e_estado_combo.get() if ctk else self.e_estado_var.get()
        if not nombres or not apellidos:
            messagebox.showwarning("Error", "Nombres y apellidos son obligatorios."); return None
        if not correo:
            messagebox.showwarning("Error", "El correo es obligatorio (es el usuario de acceso)."); return None
        if len(correo) > 100:
            messagebox.showwarning("Error", "El correo es demasiado largo (máx. 100)."); return None
        if not pwd:
            messagebox.showwarning("Error", "La contraseña es obligatoria."); return None
        return nombres, apellidos, correo, telefono, pwd, estado

    def _est_guardar_nuevo(self):
        datos = self._est_leer()
        if not datos:
            return
        nombres, apellidos, correo, telefono, pwd, _estado = datos
        self._est_operar(lambda: self.datos.crear_estudiante(nombres, apellidos, correo, telefono, pwd),
                         "Guardando estudiante…", titulo_error="Error al guardar",
                         ok=("Estudiante", "Estudiante creado correctamente."), despues=self._est_limpiar)

    def _est_actualizar(self):
        if self._est_selected is None:
            messagebox.showwarning("Error", "Seleccione un estudiante de la tabla para actualizar."); return
        datos = self._est_leer()
        if not datos:
            return
        nombres, apellidos, correo, telefono, pwd, estado = datos
        idu = self._est_selected
        self._est_operar(lambda: self.datos.actualizar_estudiante(idu, nombres, apellidos, correo, telefono, pwd, estado),
                         "Actualizando estudiante…", titulo_error="Error al actualizar",
                         ok=("Estudiante", "Estudiante actualizado."))

    def _est_eliminar(self):
        if self._est_selected is None:
            messagebox.showwarning("Error", "Seleccione un estudiante para eliminar."); return
        if not messagebox.askyesno("Confirmar", "¿Eliminar este estudiante? Esta acción no se puede deshacer."):
            return
        idu = self._est_selected
        self._est_operar(lambda: self.datos.eliminar_estudiante(idu), "Eliminando estudiante…",
                         titulo_error="Error al eliminar", titulo_aviso="Error al eliminar", despues=self._est_limpiar)

    def _est_limpiar(self):
        self._est_selected = None
        for e in (self.e_nombres, self.e_apellidos, self.e_correo, self.e_telefono, self.e_pass):
            e.delete(0, "end")
        if ctk:
            self.e_estado_combo.set("Activo")
        else:
            self.e_estado_var.set("Activo")

    def _est_refrescar(self):
        """Recarga la tabla desde la base y limpia el formulario."""
        self._est_recargar()
        self._est_limpiar()

    # ----------------------------------------------------------------- LUGARES
    def _show_lugares(self):
        self._clear_content()
        self._cambiar_seg_highlight("lugares")
        self._lug_selected = None

        wrap = self._wrap = tk.Frame(self.content, bg=COLORS["background"])
        wrap.pack(fill="both", expand=True, padx=30, pady=20)
        wrap.grid_columnconfigure(0, weight=0, minsize=340)
        wrap.grid_columnconfigure(1, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        form = self._card(wrap); form.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        fi = tk.Frame(form, bg=COLORS["surface_container"]); fi.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(fi, text="Datos del lugar", font=(FONT_FAMILY, 16, "bold"),
                 bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(anchor="w", pady=(0, 4))
        self.l_nombre = self._field(fi, "Nombre del lugar")
        self.l_desc = self._field(fi, "Descripción")
        row1 = tk.Frame(fi, bg=COLORS["surface_container"]); row1.pack(fill="x")
        self._button(row1, "Guardar nuevo", self._lug_guardar, COLORS["success"])
        self._button(row1, "Editar", self._lug_editar, COLORS["secondary_container"])
        row2 = tk.Frame(fi, bg=COLORS["surface_container"]); row2.pack(fill="x")
        self._button(row2, "Refrescar", self._lug_refrescar, COLORS["surface_high"])

        tablecard = self._card(wrap); tablecard.grid(row=0, column=1, sticky="nsew")
        self._title(tablecard, "Lugares de recolección")
        cols = ("num", "nombre", "desc")
        heads = ("#", "Nombre", "Descripción")
        widths = [(50, True), (200, False), (320, False)]
        self.lug_tree = self._tree(tablecard, cols, heads, widths, "AdmLug.Treeview")
        self.lug_tree.bind("<<TreeviewSelect>>", self._lug_on_select)
        acc = tk.Frame(tablecard, bg=COLORS["surface_container"]); acc.pack(fill="x", padx=16, pady=(0, 14))
        tk.Button(acc, text="Eliminar seleccionado", command=self._lug_eliminar, bg=COLORS["error_container"],
                  fg=COLORS["white"], activebackground="#b71c1c", relief="flat", bd=0,
                  font=(FONT_FAMILY, 11, "bold"), padx=14, pady=7, cursor="hand2").pack(side="left")
        self._lug_refrescar()

    @staticmethod
    def _lug_valores(n, fila):
        idl, nombre, desc = fila
        return idl, (n, nombre or "", desc or "")

    def _lug_recargar(self):
        self._cargar_tabla(self.lug_tree, self.datos.listar_lugares_admin, self._lug_valores, "Cargando lugares…")

    def _lug_operar(self, escribir, titulo, **kw):
        self._operar(escribir, self.lug_tree, self.datos.listar_lugares_admin, self._lug_valores, titulo, **kw)

    def _lug_on_select(self, _e=None):
        sel = self.lug_tree.selection()
        if not sel:
            return
        self._lug_selected = int(sel[0])
        vals = self.lug_tree.item(sel[0], "values")
        self._set(self.l_nombre, vals[1]); self._set(self.l_desc, vals[2])

    def _lug_guardar(self):
        nombre = self.l_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Error", "El nombre del lugar es obligatorio."); return
        desc = self.l_desc.get().strip()
        self._lug_operar(lambda: self.datos.crear_lugar(nombre, desc), "Guardando lugar…",
                         titulo_error="Error al guardar", titulo_aviso="No se pudo guardar",
                         ok=("Lugar", "Lugar creado."), despues=self._lug_limpiar)

    def _lug_editar(self):
        if self._lug_selected is None:
            messagebox.showwarning("Error", "Seleccione un lugar de la tabla."); return
        nombre = self.l_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Error", "El nombre del lugar es obligatorio."); return
        idl, desc = self._lug_selected, self.l_desc.get().strip()
        self._lug_operar(lambda: self.datos.actualizar_lugar(idl, nombre, desc), "Actualizando lugar…",
                         titulo_error="Error al actualizar", titulo_aviso="No se pudo actualizar",
                         ok=("Lugar", "Lugar actualizado."))

    def _lug_eliminar(self):
        if self._lug_selected is None:
            messagebox.showwarning("Error", "Seleccione un lugar para eliminar."); return
        if not messagebox.askyesno("Confirmar", "¿Eliminar este lugar?"):
            return
        idl = self._lug_selected
        self._lug_operar(lambda: self.datos.eliminar_lugar(idl), "Eliminando lugar…",
                         titulo_error="No se puede eliminar", titulo_aviso="No se puede eliminar",
                         despues=self._lug_limpiar)

    def _lug_limpiar(self):
        self._lug_selected = None
        self.l_nombre.delete(0, "end"); self.l_desc.delete(0, "end")

    def _lug_refrescar(self):
        self._lug_recargar()
        self._lug_limpiar()

    # ----------------------------------------------------------------- MODELOS
    def _show_modelos(self):
        self._clear_content()
        self._cambiar_seg_highlight("modelos")
        self._mod_selected = None

        wrap = self._wrap = tk.Frame(self.content, bg=COLORS["background"])
        wrap.pack(fill="both", expand=True, padx=30, pady=20)
        wrap.grid_columnconfigure(0, weight=0, minsize=340)
        wrap.grid_columnconfigure(1, weight=1)
        wrap.grid_rowconfigure(0, weight=1)

        form = self._card(wrap); form.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        fi = tk.Frame(form, bg=COLORS["surface_container"]); fi.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(fi, text="Modelo de impresión", font=(FONT_FAMILY, 16, "bold"),
                 bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(anchor="w", pady=(0, 4))
        self.m_nombre = self._field(fi, "Nombre del modelo")
        self.m_categoria = self._field(fi, "Categoría")
        self.m_tiempo = self._field(fi, "Tiempo estimado (min)")
        self.m_peso = self._field(fi, "Peso estimado (g)")
        row1 = tk.Frame(fi, bg=COLORS["surface_container"]); row1.pack(fill="x")
        self._button(row1, "Guardar nuevo", self._mod_guardar, COLORS["success"])
        self._button(row1, "Editar", self._mod_editar, COLORS["secondary_container"])
        row2 = tk.Frame(fi, bg=COLORS["surface_container"]); row2.pack(fill="x")
        self._button(row2, "Refrescar", self._mod_refrescar, COLORS["surface_high"])

        tablecard = self._card(wrap); tablecard.grid(row=0, column=1, sticky="nsew")
        self._title(tablecard, "Modelos de material didáctico")
        cols = ("num", "nombre", "categoria", "tiempo", "peso")
        heads = ("#", "Nombre", "Categoría", "Tiempo (min)", "Peso (g)")
        widths = [(50, True), (190, False), (150, False), (110, True), (100, True)]
        self.mod_tree = self._tree(tablecard, cols, heads, widths, "AdmMod.Treeview")
        self.mod_tree.bind("<<TreeviewSelect>>", self._mod_on_select)
        acc = tk.Frame(tablecard, bg=COLORS["surface_container"]); acc.pack(fill="x", padx=16, pady=(0, 14))
        tk.Button(acc, text="Eliminar seleccionado", command=self._mod_eliminar, bg=COLORS["error_container"],
                  fg=COLORS["white"], activebackground="#b71c1c", relief="flat", bd=0,
                  font=(FONT_FAMILY, 11, "bold"), padx=14, pady=7, cursor="hand2").pack(side="left")
        self._mod_refrescar()

    @staticmethod
    def _mod_valores(n, fila):
        idm, nombre, cat, tiempo, peso = fila
        return idm, (n, nombre or "", cat or "",
                     f"{float(tiempo):g}" if tiempo is not None else "",
                     f"{float(peso):g}" if peso is not None else "")

    def _mod_recargar(self):
        self._cargar_tabla(self.mod_tree, self.datos.listar_modelos_admin, self._mod_valores, "Cargando modelos…")

    def _mod_operar(self, escribir, titulo, **kw):
        self._operar(escribir, self.mod_tree, self.datos.listar_modelos_admin, self._mod_valores, titulo, **kw)

    def _mod_on_select(self, _e=None):
        sel = self.mod_tree.selection()
        if not sel:
            return
        self._mod_selected = int(sel[0])
        vals = self.mod_tree.item(sel[0], "values")
        self._set(self.m_nombre, vals[1]); self._set(self.m_categoria, vals[2])
        self._set(self.m_tiempo, vals[3]); self._set(self.m_peso, vals[4])

    def _mod_leer(self):
        nombre = self.m_nombre.get().strip()
        if not nombre:
            messagebox.showwarning("Error", "El nombre del modelo es obligatorio."); return None
        tiempo = None
        t = self.m_tiempo.get().strip()
        if t:
            ok, val = validaciones.numero(t)
            if not ok:
                messagebox.showwarning("Error", "El tiempo debe ser un número en minutos (ej. 58)."); return None
            tiempo = val
        peso = None
        p = self.m_peso.get().strip()
        if p:
            ok, peso = validaciones.numero(p)
            if not ok:
                messagebox.showwarning("Error", "El peso debe ser un número."); return None
        return nombre, self.m_categoria.get().strip(), tiempo, peso

    def _mod_guardar(self):
        datos = self._mod_leer()
        if not datos:
            return
        self._mod_operar(lambda: self.datos.crear_modelo(*datos), "Guardando modelo…",
                         titulo_error="Error al guardar", titulo_aviso="No se pudo guardar",
                         ok=("Modelo", "Modelo creado."), despues=self._mod_limpiar)

    def _mod_editar(self):
        if self._mod_selected is None:
            messagebox.showwarning("Error", "Seleccione un modelo de la tabla."); return
        datos = self._mod_leer()
        if not datos:
            return
        idm = self._mod_selected
        self._mod_operar(lambda: self.datos.actualizar_modelo(idm, *datos), "Actualizando modelo…",
                         titulo_error="Error al actualizar", titulo_aviso="No se pudo actualizar",
                         ok=("Modelo", "Modelo actualizado."))

    def _mod_eliminar(self):
        if self._mod_selected is None:
            messagebox.showwarning("Error", "Seleccione un modelo para eliminar."); return
        if not messagebox.askyesno("Confirmar", "¿Eliminar este modelo?"):
            return
        idm = self._mod_selected
        self._mod_operar(lambda: self.datos.eliminar_modelo(idm), "Eliminando modelo…",
                         titulo_error="No se puede eliminar", titulo_aviso="No se puede eliminar",
                         despues=self._mod_limpiar)

    def _mod_limpiar(self):
        self._mod_selected = None
        for e in (self.m_nombre, self.m_categoria, self.m_tiempo, self.m_peso):
            e.delete(0, "end")

    def _mod_refrescar(self):
        self._mod_recargar()
        self._mod_limpiar()

    # ---------------------------------------------------------- RECOLECCIONES
    def _show_recolecciones(self):
        self._clear_content()
        self._cambiar_seg_highlight("recolecciones")
        self._rec_selected = None
        self._resp_by_name, self._lug_by_name = {}, {}

        wrap = self._wrap = tk.Frame(self.content, bg=COLORS["background"])
        wrap.pack(fill="both", expand=True, padx=30, pady=20)
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_columnconfigure(1, weight=0, minsize=340)
        wrap.grid_rowconfigure(0, weight=1)

        # --- Tabla ---
        tablecard = self._card(wrap)
        tablecard.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        self._title(tablecard, "Recolecciones (clic en encabezado para ordenar)")
        cols = ("id", "fecha", "responsable", "lugar", "botellas", "peso", "obs")
        heads = ("ID", "Fecha", "Responsable", "Lugar", "Botellas", "Peso (kg)", "Observaciones")
        widths = [(45, True), (95, True), (140, False), (140, False), (75, True), (85, True), (180, False)]
        self.rec_tree = self._tree(tablecard, cols, heads, widths, "AdmRec.Treeview")
        self.rec_tree.bind("<<TreeviewSelect>>", self._rec_on_select)
        actions = tk.Frame(tablecard, bg=COLORS["surface_container"])
        actions.pack(fill="x", padx=16, pady=(0, 14))
        tk.Button(actions, text="Eliminar seleccionada", command=self._rec_eliminar,
                  bg=COLORS["error_container"], fg=COLORS["white"], activebackground="#b71c1c",
                  relief="flat", bd=0, font=(FONT_FAMILY, 11, "bold"), padx=14, pady=7, cursor="hand2").pack(side="left")

        # --- Formulario de edición ---
        form = self._card(wrap)
        form.grid(row=0, column=1, sticky="nsew")
        fi = tk.Frame(form, bg=COLORS["surface_container"])
        fi.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(fi, text="Editar recolección", font=(FONT_FAMILY, 16, "bold"),
                 bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(anchor="w", pady=(0, 4))

        self.r_fecha = self._field(fi, "Fecha (dd/mm/aaaa)")
        self.r_resp_combo, self.r_resp_var = self._combo(fi, "Responsable", ["Seleccione..."])
        self.r_lug_combo, self.r_lug_var = self._combo(fi, "Lugar", ["Seleccione..."])
        self.r_botellas = self._field(fi, "Cantidad de botellas")
        self.r_peso = self._field(fi, "Peso PET (kg)")
        self.r_obs = self._field(fi, "Observaciones")

        self._button(fi, "Editar recolección", self._rec_actualizar, COLORS["secondary_container"])

        # Tabla y catálogos de los combos se consultan a la vez.
        self._cargar({
            "filas": (self.datos.recolecciones_admin, "Cargando recolecciones…"),
            "responsables": (self.datos.listar_responsables, "Cargando responsables…"),
            "lugares": (self.datos.listar_lugares, "Cargando lugares…"),
        }, self._rec_poblar)

    def _rec_poblar(self, futuros):
        responsables = self._catalogo(futuros, "responsables", "los responsables")
        lugares = self._catalogo(futuros, "lugares", "los lugares")
        self._resp_by_name = {n: i for i, n in responsables}
        self._lug_by_name = {n: i for i, n in lugares}
        self._combo_valores(self.r_resp_combo, self.r_resp_var, ["Seleccione..."] + [n for _, n in responsables])
        self._combo_valores(self.r_lug_combo, self.r_lug_var, ["Seleccione..."] + [n for _, n in lugares])
        self._llenar(self.rec_tree, futuros["filas"], self._rec_valores)

    @staticmethod
    def _rec_valores(_n, fila):
        idj, fecha, resp, lugar, botellas, peso, obs = fila
        f = fecha.strftime("%d/%m/%Y") if hasattr(fecha, "strftime") else str(fecha)
        return idj, (idj, f, resp or "", lugar or "",
                     botellas if botellas is not None else "",
                     f"{float(peso):g}" if peso is not None else "", obs or "")

    def _rec_operar(self, escribir, titulo, **kw):
        self._operar(escribir, self.rec_tree, self.datos.recolecciones_admin, self._rec_valores, titulo, **kw)

    def _rec_on_select(self, _event=None):
        sel = self.rec_tree.selection()
        if not sel:
            return
        self._rec_selected = int(sel[0])
        vals = self.rec_tree.item(sel[0], "values")
        self._set(self.r_fecha, vals[1])
        self._set_combo(self.r_resp_combo, self.r_resp_var, vals[2])
        self._set_combo(self.r_lug_combo, self.r_lug_var, vals[3])
        self._set(self.r_botellas, vals[4]); self._set(self.r_peso, vals[5]); self._set(self.r_obs, vals[6])

    def _rec_actualizar(self):
        if self._rec_selected is None:
            messagebox.showwarning("Error", "Seleccione una recolección de la tabla."); return
        fecha = self.r_fecha.get().strip()
        resp_name = self.r_resp_combo.get() if ctk else self.r_resp_var.get()
        lug_name = self.r_lug_combo.get() if ctk else self.r_lug_var.get()
        id_resp = self._resp_by_name.get(resp_name)
        id_lug = self._lug_by_name.get(lug_name)
        if id_resp is None or id_lug is None:
            messagebox.showwarning("Error", "Seleccione responsable y lugar válidos."); return
        peso = self.r_peso.get().strip()
        botellas = self.r_botellas.get().strip()
        ok_peso, peso_val = validaciones.numero(peso)
        if not ok_peso:
            messagebox.showwarning("Error", "El peso debe ser un número válido."); return
        botellas_val = None
        if botellas:
            ok_bot, botellas_val = validaciones.entero_positivo(botellas)
            if not ok_bot:
                messagebox.showwarning("Error", "Botellas debe ser un entero."); return
        obs = self.r_obs.get().strip()
        idj = self._rec_selected
        self._rec_operar(lambda: self.datos.actualizar_jornada(idj, fecha, id_lug, id_resp, botellas_val, peso_val, obs),
                         "Actualizando recolección…", titulo_error="Error al actualizar",
                         titulo_aviso="Error al actualizar", ok=("Recolección", "Recolección actualizada."))

    def _rec_eliminar(self):
        if self._rec_selected is None:
            messagebox.showwarning("Error", "Seleccione una recolección para eliminar."); return
        if not messagebox.askyesno("Confirmar", "¿Eliminar esta recolección?"):
            return
        idj = self._rec_selected
        self._rec_selected = None
        self._rec_operar(lambda: self.datos.eliminar_jornada(idj), "Eliminando recolección…",
                         titulo_error="No se puede eliminar", titulo_aviso="No se puede eliminar")

    # -------------------------------------------------------- TRANSFORMACIONES
    def _show_transformaciones(self):
        self._clear_content()
        self._cambiar_seg_highlight("transformaciones")
        self._trans_selected = None
        self._jornada_lbl_by_id, self._jornada_id_by_lbl = {}, {}

        wrap = self._wrap = tk.Frame(self.content, bg=COLORS["background"])
        wrap.pack(fill="both", expand=True, padx=30, pady=20)
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_columnconfigure(1, weight=0, minsize=340)
        wrap.grid_rowconfigure(0, weight=1)

        tablecard = self._card(wrap)
        tablecard.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        self._title(tablecard, "Transformaciones (clic en encabezado para ordenar)")
        cols = ("id", "fecha", "jornada", "color", "diam", "salido", "metros", "obs")
        heads = ("ID", "Fecha", "Jornada", "Color", "Diám (mm)", "Salido (kg)", "Metros", "Observaciones")
        widths = [(40, True), (90, True), (70, True), (100, False), (80, True), (90, True), (80, True), (150, False)]
        self.trans_tree = self._tree(tablecard, cols, heads, widths, "AdmTr.Treeview")
        self.trans_tree.bind("<<TreeviewSelect>>", self._trans_on_select)
        acc = tk.Frame(tablecard, bg=COLORS["surface_container"]); acc.pack(fill="x", padx=16, pady=(0, 14))
        tk.Button(acc, text="Eliminar seleccionada", command=self._trans_eliminar, bg=COLORS["error_container"],
                  fg=COLORS["white"], activebackground="#b71c1c", relief="flat", bd=0,
                  font=(FONT_FAMILY, 11, "bold"), padx=14, pady=7, cursor="hand2").pack(side="left")

        form = self._card(wrap); form.grid(row=0, column=1, sticky="nsew")
        fi = tk.Frame(form, bg=COLORS["surface_container"]); fi.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(fi, text="Editar transformación", font=(FONT_FAMILY, 16, "bold"),
                 bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(anchor="w", pady=(0, 4))
        self.t_fecha = self._field(fi, "Fecha (dd/mm/aaaa)")
        self.t_jornada_combo, self.t_jornada_var = self._combo(fi, "Jornada de origen", ["Seleccione..."])
        self.t_color = self._field(fi, "Color")
        self.t_diam = self._field(fi, "Diámetro (mm)")
        self.t_salido = self._field(fi, "Peso salido (kg)")
        self.t_metros = self._field(fi, "Metros producidos")
        self.t_obs = self._field(fi, "Observaciones")
        self._button(fi, "Editar transformación", self._trans_editar, COLORS["secondary_container"])

        self._cargar({
            "filas": (self.datos.producciones_admin, "Cargando transformaciones…"),
            "jornadas": (self.datos.listar_jornadas, "Cargando jornadas…"),
        }, self._trans_poblar)

    def _trans_poblar(self, futuros):
        jornadas = self._catalogo(futuros, "jornadas", "las jornadas")
        self._jornada_lbl_by_id = {i: lab for i, lab, _ in jornadas}
        self._jornada_id_by_lbl = {lab: i for i, lab, _ in jornadas}
        self._combo_valores(self.t_jornada_combo, self.t_jornada_var,
                            ["Seleccione..."] + [lab for _, lab, _ in jornadas])
        self._llenar(self.trans_tree, futuros["filas"], self._trans_valores)

    @staticmethod
    def _trans_valores(_n, fila):
        idp, fecha, idj, color, diam, salido, metros, obs = fila
        f = fecha.strftime("%d/%m/%Y") if hasattr(fecha, "strftime") else (str(fecha) if fecha else "")
        return idp, (idp, f, f"#{idj}" if idj is not None else "", color or "",
                     f"{float(diam):g}" if diam is not None else "",
                     f"{float(salido):g}" if salido is not None else "",
                     f"{float(metros):g}" if metros is not None else "", obs or "")

    def _trans_operar(self, escribir, titulo, **kw):
        self._operar(escribir, self.trans_tree, self.datos.producciones_admin, self._trans_valores, titulo, **kw)

    def _trans_on_select(self, _e=None):
        sel = self.trans_tree.selection()
        if not sel:
            return
        self._trans_selected = int(sel[0])
        vals = self.trans_tree.item(sel[0], "values")
        self._set(self.t_fecha, vals[1])
        idj = str(vals[2]).lstrip("#")
        lbl = self._jornada_lbl_by_id.get(int(idj)) if idj.isdigit() else None
        self._set_combo(self.t_jornada_combo, self.t_jornada_var, lbl)
        self._set(self.t_color, vals[3]); self._set(self.t_diam, vals[4])
        self._set(self.t_salido, vals[5]); self._set(self.t_metros, vals[6]); self._set(self.t_obs, vals[7])

    def _trans_editar(self):
        if self._trans_selected is None:
            messagebox.showwarning("Error", "Seleccione una transformación de la tabla."); return
        jlbl = self.t_jornada_combo.get() if ctk else self.t_jornada_var.get()
        id_jornada = self._jornada_id_by_lbl.get(jlbl)
        if id_jornada is None:
            messagebox.showwarning("Error", "Seleccione una jornada de origen válida."); return
        ok_s, salido_val = validaciones.numero(self.t_salido.get().strip())
        ok_m, metros_val = validaciones.numero(self.t_metros.get().strip())
        if not (ok_s and ok_m):
            messagebox.showwarning("Error", "Peso salido y metros deben ser numéricos."); return
        diam_val = None
        d = self.t_diam.get().strip()
        if d:
            ok_d, diam_val = validaciones.numero(d)
            if not ok_d:
                messagebox.showwarning("Error", "Diámetro inválido."); return
        idp, fecha = self._trans_selected, self.t_fecha.get().strip()
        color, obs = self.t_color.get().strip(), self.t_obs.get().strip()
        self._trans_operar(lambda: self.datos.actualizar_produccion(idp, id_jornada, fecha, color, diam_val,
                                                                     salido_val, metros_val, obs),
                           "Actualizando transformación…", titulo_error="Error al actualizar",
                           titulo_aviso="Error al actualizar", ok=("Transformación", "Transformación actualizada."))

    def _trans_eliminar(self):
        if self._trans_selected is None:
            messagebox.showwarning("Error", "Seleccione una transformación para eliminar."); return
        if not messagebox.askyesno("Confirmar", "¿Eliminar esta transformación?"):
            return
        idp = self._trans_selected
        self._trans_selected = None
        self._trans_operar(lambda: self.datos.eliminar_produccion(idp), "Eliminando transformación…",
                           titulo_error="No se puede eliminar", titulo_aviso="No se puede eliminar")

    # ------------------------------------------------------------- IMPRESIONES
    def _show_impresiones(self):
        self._clear_content()
        self._cambiar_seg_highlight("impresiones")
        self._imp_selected = None
        self._modelo_id_by_name, self._prod_lbl_by_id, self._prod_id_by_lbl = {}, {}, {}

        wrap = self._wrap = tk.Frame(self.content, bg=COLORS["background"])
        wrap.pack(fill="both", expand=True, padx=30, pady=20)
        wrap.grid_columnconfigure(0, weight=1)
        wrap.grid_columnconfigure(1, weight=0, minsize=340)
        wrap.grid_rowconfigure(0, weight=1)

        tablecard = self._card(wrap)
        tablecard.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        self._title(tablecard, "Impresiones (clic en encabezado para ordenar)")
        cols = ("id", "fecha", "modelo", "prod", "cantidad", "peso", "tiempo", "estado")
        heads = ("ID", "Fecha", "Modelo", "Filamento", "Piezas", "Peso (g)", "Tiempo (min)", "Estado")
        widths = [(40, True), (90, True), (150, False), (75, True), (65, True), (80, True), (95, True), (95, True)]
        self.imp_tree = self._tree(tablecard, cols, heads, widths, "AdmIm.Treeview")
        self.imp_tree.bind("<<TreeviewSelect>>", self._imp_on_select)
        acc = tk.Frame(tablecard, bg=COLORS["surface_container"]); acc.pack(fill="x", padx=16, pady=(0, 14))
        tk.Button(acc, text="Eliminar seleccionada", command=self._imp_eliminar, bg=COLORS["error_container"],
                  fg=COLORS["white"], activebackground="#b71c1c", relief="flat", bd=0,
                  font=(FONT_FAMILY, 11, "bold"), padx=14, pady=7, cursor="hand2").pack(side="left")

        form = self._card(wrap); form.grid(row=0, column=1, sticky="nsew")
        fi = tk.Frame(form, bg=COLORS["surface_container"]); fi.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(fi, text="Editar impresión", font=(FONT_FAMILY, 16, "bold"),
                 bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(anchor="w", pady=(0, 4))
        self.i_fecha = self._field(fi, "Fecha (dd/mm/aaaa)")
        self.i_modelo_combo, self.i_modelo_var = self._combo(fi, "Modelo", ["Seleccione..."])
        self.i_prod_combo, self.i_prod_var = self._combo(fi, "Filamento (producción)", ["Seleccione..."])
        self.i_cantidad = self._field(fi, "Cantidad de piezas")
        self.i_peso = self._field(fi, "Peso utilizado (g)")
        self.i_tiempo = self._field(fi, "Tiempo (min)")
        self.i_estado_combo, self.i_estado_var = self._combo(fi, "Estado", ["En proceso", "Finalizado", "Fallido"])
        self._button(fi, "Editar impresión", self._imp_editar, COLORS["secondary_container"])

        self._cargar({
            "filas": (self.datos.fabricaciones_admin, "Cargando impresiones…"),
            "modelos": (self.datos.listar_modelos, "Cargando modelos…"),
            "producciones": (self.datos.listar_producciones, "Cargando filamentos…"),
        }, self._imp_poblar)

    def _imp_poblar(self, futuros):
        modelos = self._catalogo(futuros, "modelos", "los modelos")
        producciones = self._catalogo(futuros, "producciones", "los filamentos")
        self._modelo_id_by_name = {n: i for i, n in modelos}
        self._prod_lbl_by_id = {i: lab for i, lab, _ in producciones}
        self._prod_id_by_lbl = {lab: i for i, lab, _ in producciones}
        self._combo_valores(self.i_modelo_combo, self.i_modelo_var, ["Seleccione..."] + [n for _, n in modelos])
        self._combo_valores(self.i_prod_combo, self.i_prod_var,
                            ["Seleccione..."] + [lab for _, lab, _ in producciones])
        self._llenar(self.imp_tree, futuros["filas"], self._imp_valores)

    @staticmethod
    def _imp_valores(_n, fila):
        idf, fecha, _idm, modelo, idp, cant, peso, tiempo, estado = fila
        f = fecha.strftime("%d/%m/%Y") if hasattr(fecha, "strftime") else (str(fecha) if fecha else "")
        return idf, (idf, f, modelo or "", f"#{idp}" if idp is not None else "",
                     cant if cant is not None else "",
                     f"{float(peso):g}" if peso is not None else "",
                     tiempo if tiempo is not None else "", estado or "")

    def _imp_operar(self, escribir, titulo, **kw):
        self._operar(escribir, self.imp_tree, self.datos.fabricaciones_admin, self._imp_valores, titulo, **kw)

    def _imp_on_select(self, _e=None):
        sel = self.imp_tree.selection()
        if not sel:
            return
        self._imp_selected = int(sel[0])
        vals = self.imp_tree.item(sel[0], "values")
        self._set(self.i_fecha, vals[1])
        self._set_combo(self.i_modelo_combo, self.i_modelo_var, vals[2])
        idp = str(vals[3]).lstrip("#")
        plbl = self._prod_lbl_by_id.get(int(idp)) if idp.isdigit() else None
        self._set_combo(self.i_prod_combo, self.i_prod_var, plbl)
        self._set(self.i_cantidad, vals[4]); self._set(self.i_peso, vals[5]); self._set(self.i_tiempo, vals[6])
        self._set_combo(self.i_estado_combo, self.i_estado_var, vals[7])

    def _imp_editar(self):
        if self._imp_selected is None:
            messagebox.showwarning("Error", "Seleccione una impresión de la tabla."); return
        modelo_name = self.i_modelo_combo.get() if ctk else self.i_modelo_var.get()
        plbl = self.i_prod_combo.get() if ctk else self.i_prod_var.get()
        estado = self.i_estado_combo.get() if ctk else self.i_estado_var.get()
        id_modelo = self._modelo_id_by_name.get(modelo_name)
        id_prod = self._prod_id_by_lbl.get(plbl)
        if id_modelo is None or id_prod is None:
            messagebox.showwarning("Error", "Seleccione modelo y producción válidos."); return
        ok_c, cantidad = validaciones.entero_positivo(self.i_cantidad.get().strip())
        ok_p, peso = validaciones.numero(self.i_peso.get().strip())
        ok_t, tiempo_f = validaciones.numero(self.i_tiempo.get().strip())
        if not (ok_c and ok_p and ok_t):
            messagebox.showwarning("Error", "Piezas, peso y tiempo deben ser numéricos."); return
        tiempo = int(tiempo_f)
        idf, fecha = self._imp_selected, self.i_fecha.get().strip()
        self._imp_operar(lambda: self.datos.actualizar_fabricacion(idf, id_modelo, id_prod, fecha,
                                                                    cantidad, peso, tiempo, estado),
                         "Actualizando impresión…", titulo_error="Error al actualizar",
                         titulo_aviso="Error al actualizar", ok=("Impresión", "Impresión actualizada."))

    def _imp_eliminar(self):
        if self._imp_selected is None:
            messagebox.showwarning("Error", "Seleccione una impresión para eliminar."); return
        if not messagebox.askyesno("Confirmar", "¿Eliminar esta impresión?"):
            return
        idf = self._imp_selected
        self._imp_selected = None
        self._imp_operar(lambda: self.datos.eliminar_fabricacion(idf), "Eliminando impresión…",
                         titulo_error="Error al eliminar", titulo_aviso="Error al eliminar")

    # ------------------------------------------------------- carga en paralelo
    def _ocupar(self, al_terminar):
        """Marca la sección como ocupada y devuelve el callback que la libera.

        El spinner solo aparece si la base tarda más de RETARDO_S; mientras
        tanto, esto evita que un doble clic lance la misma operación dos veces.
        Devuelve None si ya había algo en curso.
        """
        if self._ocupado:
            return None
        self._ocupado = True

        def liberar(*args):
            self._ocupado = False
            al_terminar(*args)
        return liberar

    def _cargar(self, cargas, al_terminar, titulo="Obteniendo datos…"):
        """Lanza las consultas de la sección a la vez, con el spinner encima."""
        al_terminar = self._ocupar(al_terminar)
        if al_terminar:
            cargar_con_spinner(self._wrap, cargas, al_terminar, titulo=titulo, retardo_s=RETARDO_S)

    def _cargar_tabla(self, tree, listar, valores, texto):
        """Recarga solo la tabla (en un hilo, con spinner)."""
        self._cargar({"filas": (listar, texto)}, lambda f: self._llenar(tree, f["filas"], valores), titulo=texto)

    def _llenar(self, tree, futuro, valores):
        """Vuelca en la tabla el resultado de una consulta (Future)."""
        try:
            filas = futuro.result()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Base de datos", f"No se pudo cargar la lista:\n{exc}")
            return
        self._llenar_filas(tree, filas, valores)

    @staticmethod
    def _llenar_filas(tree, filas, valores):
        tree.delete(*tree.get_children())
        for n, fila in enumerate(filas, start=1):
            iid, vals = valores(n, fila)
            tree.insert("", "end", iid=str(iid), values=vals)

    def _operar(self, escribir, tree, listar, valores, titulo, ok=None,
                titulo_error="Error", titulo_aviso="Error", despues=None):
        """Guarda/edita/elimina en un hilo y, en el mismo hilo, relee la tabla.

        `escribir` no debe leer widgets (corre fuera del hilo principal): los
        valores del formulario se toman antes de llamar. Un ValueError se
        muestra como aviso (validación de negocio); otra excepción, como error.
        """
        def tarea(reportar):
            reportar(0, 2, titulo)
            escribir()
            reportar(1, 2, "Actualizando la tabla…")
            try:
                return listar(), None
            except Exception as exc:  # noqa: BLE001
                return None, exc

        def al_terminar(futuro):
            try:
                filas, error_lista = futuro.result()
            except ValueError as exc:
                messagebox.showwarning(titulo_aviso, str(exc)); return
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror(titulo_error, str(exc)); return
            if error_lista is not None:
                messagebox.showerror("Base de datos", f"Se guardó, pero no se pudo recargar la lista:\n{error_lista}")
            else:
                self._llenar_filas(tree, filas, valores)
            if despues:
                despues()
            if ok:
                messagebox.showinfo(*ok)

        al_terminar = self._ocupar(al_terminar)
        if al_terminar:
            ejecutar_con_spinner(self._wrap, tarea, al_terminar, titulo=titulo)

    def _catalogo(self, futuros, clave, nombre):
        """Resultado de un catálogo precargado; si falla, lista vacía y aviso."""
        try:
            return futuros[clave].result()
        except Exception as exc:  # noqa: BLE001
            messagebox.showwarning("Base de datos", f"No se pudieron cargar {nombre}:\n{exc}")
            return []

    def _combo_valores(self, combo, var, values):
        """Cambia las opciones de un combo ya creado (cuando llegan los catálogos)."""
        if ctk:
            combo.configure(values=values)
            combo.set(values[0])
            return
        menu = combo["menu"]
        menu.delete(0, "end")
        for v in values:
            menu.add_command(label=v, command=tk._setit(var, v))
        var.set(values[0])

    # -------------------------------------------------------------- utilidades
    def _set(self, entry, value):
        entry.delete(0, "end")
        if value not in (None, ""):
            entry.insert(0, str(value))

    def _set_combo(self, combo, var, value):
        if ctk:
            combo.set(value or "Seleccione...")
        else:
            var.set(value or "Seleccione...")

    # ------------------------------------------------------------- navegación
    def ir_al_sistema(self):
        if self.on_navigate:
            self.on_navigate("inicio")

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
    AdminApp(root)
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
