"""
ui_dialogos.py
Diálogos modales, formularios con scroll y enlaces del pie de página.
"""

import tkinter as tk

try:
    # pyrefly: ignore [missing-import]
    import customtkinter as ctk
except ImportError:
    ctk = None


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
