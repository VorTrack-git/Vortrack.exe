"""Utilidades de interfaz compartidas por los módulos de VorTrack."""

import os
import tkinter as tk
from tkinter import messagebox

# pyrefly: ignore [missing-import]
from PIL import Image, ImageTk

try:
    # pyrefly: ignore [missing-import]
    import customtkinter as ctk
except ImportError:
    ctk = None


FONT_FAMILY = "Segoe UI"

# Paleta compartida por los módulos de página.
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
    "surface": "#0d1117",
}


def maximize_window(root):
    """Abre la ventana maximizada (ocupa toda la pantalla y conserva la barra de título).

    En tkinter puro basta llamar state('zoomed') una vez, pero customtkinter
    reajusta la geometría durante su init, así que hay que reintentar el
    maximizado de forma diferida (cuando ya corre el bucle de eventos).
    """
    def _apply():
        try:
            if not root.winfo_exists():
                return
            root.state("zoomed")  # Windows y la mayoría de Tk en Windows
        except tk.TclError:
            try:
                root.attributes("-zoomed", True)  # algunos entornos Linux
            except tk.TclError:
                try:
                    root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
                except tk.TclError:
                    pass

    root.update_idletasks()
    _apply()               # intento inmediato (funciona en tkinter puro)
    root.after(60, _apply)  # reintento diferido (necesario en customtkinter)


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def set_window_icon(root):
    """Fija el ícono de la ventana usando VorTrack.ico (logo transparente).

    En Windows usa iconbitmap con el .ico (nítido en barra de título y de
    tareas). Si falla, cae a iconphoto con el PNG transparente. Se reintenta
    de forma diferida porque customtkinter puede sobreescribir el ícono al
    inicializarse.
    """
    ico = os.path.join(_BASE_DIR, "VorTrack.ico")
    png = os.path.join(_BASE_DIR, "VorTrack_icon_transparent.png")
    if not os.path.exists(png):
        png = os.path.join(_BASE_DIR, "VorTrack icon.png")

    def _apply():
        try:
            if not root.winfo_exists():
                return
        except Exception:
            return
        if os.name == "nt" and os.path.exists(ico):
            try:
                root.iconbitmap(ico)
                return
            except Exception:
                pass
        if os.path.exists(png):
            try:
                photo = ImageTk.PhotoImage(Image.open(png))
                root._vortrack_icon = photo  # mantener la referencia viva
                root.iconphoto(True, photo)
            except Exception:
                pass

    _apply()
    try:
        root.after(300, _apply)
    except Exception:
        pass


def scrollable_form(parent, bg, **pack_kwargs):
    """Crea un contenedor con scroll vertical y lo empaqueta en `parent`.

    Devuelve el frame donde se deben agregar los campos. Con customtkinter usa
    CTkScrollableFrame (scrollbar + rueda del ratón automáticos); sin él, un
    Canvas con barra de desplazamiento.
    """
    if ctk:
        sf = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        sf.pack(**pack_kwargs)
        return sf

    outer = tk.Frame(parent, bg=bg)
    outer.pack(**pack_kwargs)
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0)
    sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=sb.set)
    sb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    inner = tk.Frame(canvas, bg=bg)
    win = canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(win, width=e.width))
    _wheel = lambda e: canvas.yview_scroll(int(-e.delta / 120), "units")
    canvas.bind("<MouseWheel>", _wheel)
    inner.bind("<MouseWheel>", _wheel)
    return inner


def load_image(path, size):
    """Carga una imagen como CTkImage o ImageTk según la librería disponible."""
    if not os.path.exists(path):
        return None
    img = Image.open(path)
    if ctk:
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    img_resized = img.resize(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img_resized)


def open_footer_link(root, link_text):
    """Acción asociada a cada enlace del pie de página, compartida por los módulos."""
    # Imports diferidos para evitar dependencias circulares al cargar el módulo.
    if link_text in ("Soporte Técnico", "Contacto"):
        import soporte_dialog
        soporte_dialog.abrir_soporte(root)
    elif link_text == "Privacidad":
        import privacidad
        privacidad.abrir_privacidad(root)
    elif link_text == "Términos de Uso":
        import use_terms
        use_terms.abrir_terminos(root)


# Paleta mínima para los diálogos (coherente con los módulos).
_DIALOG_COLORS = {
    "background": "#051424",
    "surface_container": "#122131",
    "surface_lowest": "#010f1f",
    "surface_high": "#1c2b3c",
    "surface_bright": "#2c3a4c",
    "primary_fixed": "#7df4ff",
    "on_surface": "#d4e4fa",
    "on_surface_variant": "#b9cacb",
    "outline_variant": "#3b494b",
}


def text_dialog(parent_root, title, heading, body):
    """Muestra un diálogo modal con texto largo desplazable (para Privacidad / Términos)."""
    c = _DIALOG_COLORS
    font_family = "Segoe UI"

    dialog = tk.Toplevel(parent_root)
    dialog.title(title)
    dialog.configure(bg=c["background"])
    dialog.transient(parent_root)
    dialog.grab_set()

    width, height = 640, 620
    parent_root.update_idletasks()
    px = parent_root.winfo_rootx() + (parent_root.winfo_width() // 2) - (width // 2)
    py = parent_root.winfo_rooty() + (parent_root.winfo_height() // 2) - (height // 2)
    dialog.geometry(f"{width}x{height}+{max(px, 0)}+{max(py, 0)}")

    # Acento cyan superior
    tk.Frame(dialog, bg=c["primary_fixed"], height=3).pack(fill="x", side="top")

    body_frame = tk.Frame(dialog, bg=c["surface_container"])
    body_frame.pack(fill="both", expand=True, padx=20, pady=20)

    tk.Label(
        body_frame, text=heading, font=(font_family, 18, "bold"),
        bg=c["surface_container"], fg=c["primary_fixed"]
    ).pack(anchor="w", pady=(4, 12))

    text_wrap = tk.Frame(body_frame, bg=c["surface_container"])
    text_wrap.pack(fill="both", expand=True)

    scroll = tk.Scrollbar(text_wrap)
    scroll.pack(side="right", fill="y")

    text = tk.Text(
        text_wrap, wrap="word", bd=0, padx=14, pady=12,
        bg=c["surface_lowest"], fg=c["on_surface"],
        font=(font_family, 10), yscrollcommand=scroll.set,
        insertbackground=c["on_surface"], relief="flat"
    )
    text.pack(side="left", fill="both", expand=True)
    scroll.config(command=text.yview)

    text.insert("1.0", body.strip())
    text.configure(state="disabled")

    close_btn = tk.Button(
        body_frame, text="  Cerrar  ", command=dialog.destroy,
        bg=c["surface_high"], fg=c["on_surface"],
        activebackground=c["surface_bright"], activeforeground=c["primary_fixed"],
        relief="flat", font=(font_family, 10, "bold"),
        padx=20, pady=6, cursor="hand2", bd=0
    )
    close_btn.pack(pady=(14, 0))
    return dialog


def bind_footer_link(label, root, link_text, base_fg, hover_fg):
    """Hace clicable un enlace del footer con efecto hover."""
    label.configure(cursor="hand2")
    label.bind("<Button-1>", lambda _e: open_footer_link(root, link_text))
    label.bind("<Enter>", lambda _e: label.configure(fg=hover_fg))
    label.bind("<Leave>", lambda _e: label.configure(fg=base_fg))


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
    import auth
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
