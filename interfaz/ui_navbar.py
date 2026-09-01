"""
ui_navbar.py
Barra de navegación y pie de página estándar de las pantallas autenticadas.
"""

import tkinter as tk

from interfaz.ui_tema import COLORS, FONT_FAMILY
from interfaz.ui_dialogos import bind_footer_link

try:
    # pyrefly: ignore [missing-import]
    import customtkinter as ctk
except ImportError:
    ctk = None


def build_app_navbar(app):
    """Construye la barra de navegación estándar de las páginas autenticadas.

    Espera que `app` tenga: main_container, icon_path, load_ctk_image(),
    y los callbacks ir_a_inicio(), ir_a_historico(), on_registrar_select(choice)
    y logout(). Guarda `app.registrar_btn` en la versión ctk.
    """
    COL = COLORS
    navbar_outer = tk.Frame(app.main_container, bg=COL["surface_container"], height=70)
    navbar_outer.pack(fill="x", side="top")
    navbar_outer.pack_propagate(False)

    tk.Frame(app.main_container, bg=COL["outline_variant"], height=1).pack(fill="x", side="top")

    navbar_content = tk.Frame(navbar_outer, bg=COL["surface_container"])
    navbar_content.pack(fill="both", expand=True, padx=24, pady=10)

    brand_frame = tk.Frame(navbar_content, bg=COL["surface_container"])
    brand_frame.pack(side="left")

    app.nav_icon_img = app.load_ctk_image(app.icon_path, size=(38, 38))
    if app.nav_icon_img:
        if ctk:
            icon_lbl = ctk.CTkLabel(brand_frame, image=app.nav_icon_img, text="")
        else:
            icon_lbl = tk.Label(brand_frame, image=app.nav_icon_img, bg=COL["surface_container"])
        icon_lbl.pack(side="left", padx=(0, 10))

    tk.Label(brand_frame, text="VorTrack", fg=COL["primary_fixed"], bg=COL["surface_container"], font=(FONT_FAMILY, 20, "bold")).pack(side="left")

    nav_items_frame = tk.Frame(navbar_content, bg=COL["surface_container"])
    nav_items_frame.pack(side="left", expand=True)

    lbl_quienes = tk.Label(nav_items_frame, text="QUIÉNES SOMOS", fg=COL["on_surface_variant"], bg=COL["surface_container"], font=(FONT_FAMILY, 10, "bold"), cursor="hand2")
    lbl_quienes.pack(side="left", padx=16)
    lbl_quienes.bind("<Button-1>", lambda _e: app.ir_a_inicio())

    if ctk:
        app.registrar_btn = ctk.CTkOptionMenu(
            nav_items_frame, values=["REGISTRAR ▾", "Recolección", "Transformación", "Impresión"],
            fg_color=COL["surface_container"], button_color=COL["surface_high"], button_hover_color=COL["surface_bright"],
            text_color=COL["on_surface_variant"], dropdown_fg_color=COL["surface_container"], dropdown_hover_color=COL["surface_bright"],
            dropdown_text_color=COL["on_surface"], font=(FONT_FAMILY, 11, "bold"), dynamic_resizing=False,
            width=130, height=32, corner_radius=12, command=app.on_registrar_select
        )
        app.registrar_btn.set("REGISTRAR ▾")
        app.registrar_btn.pack(side="left", padx=10)
    else:
        registrar_btn = tk.Menubutton(nav_items_frame, text="REGISTRAR ▾", fg=COL["on_surface_variant"], bg=COL["surface_container"],
                                      activebackground=COL["surface_bright"], activeforeground=COL["primary_fixed"], font=(FONT_FAMILY, 10, "bold"), bd=0, cursor="hand2")
        registrar_menu = tk.Menu(registrar_btn, tearoff=0, bg=COL["surface_container"], fg=COL["on_surface"])
        for et in ("Recolección", "Transformación", "Impresión"):
            registrar_menu.add_command(label=et, command=lambda e=et: app.on_registrar_select(e))
        registrar_btn.config(menu=registrar_menu)
        registrar_btn.pack(side="left", padx=16)

    if ctk:
        btn_hist = ctk.CTkButton(nav_items_frame, text="HISTÓRICO INFORMES", fg_color="transparent", hover_color=COL["surface_bright"],
                                 text_color=COL["on_surface_variant"], font=(FONT_FAMILY, 11, "bold"), height=32, corner_radius=12, command=app.ir_a_historico)
        btn_hist.pack(side="left", padx=10)
    else:
        lbl_hist = tk.Label(nav_items_frame, text="HISTÓRICO INFORMES", fg=COL["on_surface_variant"], bg=COL["surface_container"], font=(FONT_FAMILY, 10, "bold"), cursor="hand2")
        lbl_hist.pack(side="left", padx=16)
        lbl_hist.bind("<Button-1>", lambda _e: app.ir_a_historico())

    # Acceso al panel de administración (solo para administradores).
    import servicios.auth as auth
    if auth.is_admin() and getattr(app, "on_navigate", None):
        if ctk:
            ctk.CTkButton(nav_items_frame, text="⚙ ADMIN", fg_color="transparent", hover_color=COL["surface_bright"],
                          text_color=COL["primary_fixed"], font=(FONT_FAMILY, 11, "bold"), height=32, corner_radius=12,
                          command=lambda: app.on_navigate("admin")).pack(side="left", padx=10)
        else:
            lbl_adm = tk.Label(nav_items_frame, text="⚙ ADMIN", fg=COL["primary_fixed"], bg=COL["surface_container"],
                               font=(FONT_FAMILY, 10, "bold"), cursor="hand2")
            lbl_adm.pack(side="left", padx=16)
            lbl_adm.bind("<Button-1>", lambda _e: app.on_navigate("admin"))

    if ctk:
        btn_logout = ctk.CTkButton(navbar_content, text="Logout", fg_color=COL["surface_low"], hover_color=COL["surface_bright"],
                                   border_color=COL["outline_variant"], border_width=1, text_color=COL["on_surface"],
                                   font=(FONT_FAMILY, 11, "bold"), corner_radius=12, width=100, height=36, command=app.logout)
        btn_logout.pack(side="right")
    else:
        btn_logout = tk.Button(navbar_content, text="Logout", fg=COL["on_surface"], bg=COL["surface_low"], activebackground=COL["surface_bright"],
                               activeforeground=COL["primary_fixed"], font=(FONT_FAMILY, 10, "bold"), bd=1, relief="solid", padx=16, pady=6, cursor="hand2", command=app.logout)
        btn_logout.pack(side="right")


def build_app_footer(app):
    """Construye el pie de página estándar (marca + enlaces con acción)."""
    COL = COLORS
    tk.Frame(app.main_container, bg=COL["outline_variant"], height=1).pack(fill="x", side="top")
    footer_frame = tk.Frame(app.main_container, bg=COL["surface_lowest"], height=65)
    footer_frame.pack(fill="x", side="bottom")
    footer_frame.pack_propagate(False)

    footer_content = tk.Frame(footer_frame, bg=COL["surface_lowest"])
    footer_content.pack(fill="both", expand=True, padx=24, pady=10)

    left_foot = tk.Frame(footer_content, bg=COL["surface_lowest"])
    left_foot.pack(side="left")
    tk.Label(left_foot, text="VorTrack", fg=COL["primary_fixed"], bg=COL["surface_lowest"], font=(FONT_FAMILY, 12, "bold")).pack(side="left", padx=(0, 10))
    tk.Label(left_foot, text="© 2026 desarrollado por Miguel Ruiz Ramirez", fg=COL["on_surface_variant"], bg=COL["surface_lowest"], font=(FONT_FAMILY, 9)).pack(side="left")

    right_foot = tk.Frame(footer_content, bg=COL["surface_lowest"])
    right_foot.pack(side="right")
    for link in ["Privacidad", "Términos de Uso", "Contacto", "Soporte Técnico"]:
        lbl_link = tk.Label(right_foot, text=link, fg=COL["on_surface_variant"], bg=COL["surface_lowest"], font=(FONT_FAMILY, 9, "bold"))
        lbl_link.pack(side="left", padx=10)
        bind_footer_link(lbl_link, app.root, link, base_fg=COL["on_surface_variant"], hover_fg=COL["primary_fixed"])
