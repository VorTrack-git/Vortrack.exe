"""
widgets.py
Fábrica de widgets: centraliza la creación de controles de interfaz para que la
rama customtkinter (ctk) y la rama tkinter puro (tk) vivan en un solo lugar.

Reemplaza los helpers duplicados que hoy están copiados en cada `*_ui.py`
(`create_label`, `_make_entry`, `_make_combo`, `_hint`, textbox, botón, título,
tarjeta, tabla). Cada método crea el widget, lo empaqueta (salvo la tabla y la
tarjeta, que se posicionan desde el llamador) y devuelve el widget para poder
consultarlo/limpiarlo luego.

Uso:
    fw = FabricaWidgets()                 # usa la paleta/tipografía por defecto
    fw.label_campo(form, "Fecha")
    entry = fw.entry(form, "Ej. 20")
    combo, var = fw.combo(form, ["A", "B"])   # var es None en ctk

SOLID: SRP (solo crea widgets), OCP/DRY (el `if ctk` vive aquí una sola vez).
"""

import tkinter as tk
from tkinter import ttk

from ui_tema import COLORS, FONT_FAMILY

try:
    # pyrefly: ignore [missing-import]
    import customtkinter as ctk
except ImportError:
    ctk = None


class FabricaWidgets:
    """Crea widgets estilizados de forma uniforme para ctk y tk."""

    def __init__(self, colors=None, font_family=None):
        self.c = colors or COLORS
        self.font = font_family or FONT_FAMILY

    # ---- indica si estamos en modo customtkinter --------------------------
    @property
    def usa_ctk(self):
        return ctk is not None

    # ---- etiquetas --------------------------------------------------------
    def label_campo(self, parent, texto, pady=(0, 0)):
        """Etiqueta de campo en negrita (equivale a create_label/_label)."""
        c = self.c
        if ctk:
            lbl = ctk.CTkLabel(parent, text=texto, font=(self.font, 12, "bold"),
                               text_color=c["on_surface_variant"])
        else:
            lbl = tk.Label(parent, text=texto, font=(self.font, 10, "bold"),
                           bg=c["surface_container"], fg=c["on_surface_variant"])
        lbl.pack(anchor="w", pady=pady)
        return lbl

    def titulo(self, parent, texto, **pack_kwargs):
        """Título cyan de una tarjeta/panel."""
        c = self.c
        if ctk:
            lbl = ctk.CTkLabel(parent, text=texto, font=(self.font, 18, "bold"),
                               text_color=c["primary_fixed"])
        else:
            lbl = tk.Label(parent, text=texto, font=(self.font, 16, "bold"),
                           bg=c["surface_container"], fg=c["primary_fixed"])
        lbl.pack(**(pack_kwargs or {"pady": (20, 15)}))
        return lbl

    def hint(self, parent, texto):
        """Texto de ayuda pequeño y tenue bajo un campo (equivale a _hint)."""
        c = self.c
        if ctk:
            lbl = ctk.CTkLabel(parent, text=texto, font=(self.font, 10),
                               text_color=c["on_surface_variant"], wraplength=340, justify="left")
            lbl.pack(anchor="w", pady=(0, 12))
        else:
            lbl = tk.Label(parent, text=texto, font=(self.font, 8), bg=c["surface_container"],
                           fg=c["on_surface_variant"], wraplength=340, justify="left")
            lbl.pack(anchor="w", pady=(0, 10))
        return lbl

    # ---- entradas ---------------------------------------------------------
    def entry(self, parent, placeholder="", pady_ctk=(2, 12), pady_tk=(2, 10)):
        """Campo de texto de una línea (equivale a _make_entry)."""
        c = self.c
        if ctk:
            e = ctk.CTkEntry(parent, placeholder_text=placeholder, height=35,
                             fg_color=c["surface_lowest"], border_color=c["outline_variant"],
                             text_color=c["on_surface"], font=(self.font, 13))
            e.pack(fill="x", pady=pady_ctk)
        else:
            e = tk.Entry(parent, bg=c["surface_lowest"], fg=c["on_surface"],
                         insertbackground=c["on_surface"], relief="flat", font=(self.font, 12),
                         readonlybackground=c["surface_low"])
            e.pack(fill="x", pady=pady_tk, ipady=5)
        return e

    def combo(self, parent, values, command=None, pady_ctk=(2, 12), pady_tk=(2, 10)):
        """Desplegable. Devuelve (widget, var) — var es None en ctk (equivale a _make_combo)."""
        c = self.c
        if ctk:
            cb = ctk.CTkOptionMenu(
                parent, values=values, height=35,
                fg_color=c["surface_lowest"], button_color=c["surface_lowest"],
                button_hover_color=c["outline_variant"], dropdown_fg_color=c["surface_container"],
                dropdown_hover_color=c["outline_variant"], text_color=c["on_surface"],
                command=command)
            cb.set(values[0])
            cb.pack(fill="x", pady=pady_ctk)
            return cb, None
        var = tk.StringVar(value=values[0])
        if command:
            cb = tk.OptionMenu(parent, var, *values, command=command)
        else:
            cb = tk.OptionMenu(parent, var, *values)
        cb.config(bg=c["surface_lowest"], fg=c["on_surface"],
                  activebackground=c["surface_high"], activeforeground=c["on_surface"],
                  highlightthickness=0, bd=0)
        cb.pack(fill="x", pady=pady_tk)
        return cb, var

    def textbox(self, parent, placeholder="Opcional...", pady_ctk=(2, 25), pady_tk=(2, 15)):
        """Área de texto multilínea con placeholder. Devuelve el widget."""
        c = self.c
        if ctk:
            tb = ctk.CTkTextbox(parent, height=80, fg_color=c["surface_lowest"],
                                border_color=c["outline_variant"], border_width=1,
                                text_color=c["on_surface"], font=(self.font, 13))
            if placeholder:
                tb.insert("1.0", placeholder)
                tb.bind("<FocusIn>", lambda _e: self._clear_placeholder(tb, placeholder))
            tb.pack(fill="x", pady=pady_ctk)
        else:
            tb = tk.Text(parent, height=4, width=1, bg=c["surface_lowest"], fg=c["on_surface"],
                         insertbackground=c["on_surface"], relief="flat", font=(self.font, 12), wrap="word")
            if placeholder:
                tb.insert("1.0", placeholder)
                tb.bind("<FocusIn>", lambda _e: self._clear_placeholder(tb, placeholder))
            tb.pack(fill="x", pady=pady_tk, ipady=4)
        return tb

    @staticmethod
    def _clear_placeholder(textbox, placeholder):
        if textbox.get("1.0", "end-1c").strip() == placeholder:
            textbox.delete("1.0", "end")

    # ---- botones ----------------------------------------------------------
    def boton(self, parent, texto, command, tipo="primario", pack_kwargs=None):
        """Botón de acción. `tipo`: 'primario' (verde), 'neutro', 'peligro'."""
        c = self.c
        paletas = {
            "primario": (c["success"], c["success_hover"], c["white"]),
            "neutro":   (c["surface_high"], c["surface_bright"], c["on_surface"]),
            "peligro":  (c["error_container"], c["error"], c["white"]),
        }
        fg, hover, text_color = paletas.get(tipo, paletas["primario"])
        if ctk:
            b = ctk.CTkButton(parent, text=texto, font=(self.font, 14, "bold"), height=45,
                              fg_color=fg, hover_color=hover, text_color=text_color,
                              corner_radius=8, command=command)
        else:
            b = tk.Button(parent, text=texto, bg=fg, fg=text_color,
                          activebackground=hover, activeforeground=text_color,
                          relief="flat", font=(self.font, 11, "bold"),
                          padx=16, pady=8, cursor="hand2", bd=0, command=command)
        b.pack(**(pack_kwargs if pack_kwargs is not None else {"fill": "x"}))
        return b

    # ---- contenedores -----------------------------------------------------
    def tarjeta(self, parent, **kwargs):
        """Tarjeta/panel con borde cyan. El llamador la posiciona (pack/grid)."""
        c = self.c
        if ctk:
            return ctk.CTkFrame(parent, fg_color=c["surface_container"],
                                border_color=c["primary_fixed"], border_width=1,
                                corner_radius=12, **kwargs)
        return tk.Frame(parent, bg=c["surface_container"], bd=1, relief="solid", **kwargs)

    # ---- tablas -----------------------------------------------------------
    def estilo_tabla(self, style_name):
        """Configura y devuelve el nombre de estilo ttk para una Treeview oscura."""
        c = self.c
        style = ttk.Style()
        style.theme_use("default")
        style.configure(style_name, background=c["surface"], foreground=c["on_surface"],
                        rowheight=35, fieldbackground=c["surface"],
                        bordercolor=c["outline_variant"], borderwidth=0, font=(self.font, 11))
        style.map(style_name, background=[("selected", c["surface_low"])])
        heading = f"{style_name}.Heading"
        style.configure(heading, background=c["surface_high"], foreground=c["on_surface_variant"],
                        relief="flat", font=(self.font, 11, "bold"))
        style.map(heading, background=[("active", c["surface_bright"])])
        return style_name

    def tabla(self, parent, columnas, style_name, yscrollcommand=None):
        """Crea una Treeview estilizada (solo encabezados). Devuelve el widget.

        `columnas`: lista de (id, titulo, ancho, anchor). El llamador la empaqueta.
        """
        self.estilo_tabla(style_name)
        cols = [col[0] for col in columnas]
        tree = ttk.Treeview(parent, columns=cols, show="headings", style=style_name,
                            yscrollcommand=yscrollcommand)
        for col_id, titulo, ancho, anchor in columnas:
            tree.heading(col_id, text=titulo)
            tree.column(col_id, width=ancho, anchor=anchor, stretch=True)
        return tree
