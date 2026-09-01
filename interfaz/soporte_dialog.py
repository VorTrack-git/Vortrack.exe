"""
soporte_dialog.py
Ventana de Soporte Técnico compartida para todos los módulos de VorTrack.
"""
import tkinter as tk

COLORS = {
    "background":         "#051424",
    "surface_container":  "#122131",
    "surface_high":       "#1c2b3c",
    "surface_highest":    "#273647",
    "surface_bright":     "#2c3a4c",
    "primary_fixed":      "#7df4ff",
    "primary_fixed_dim":  "#00dbe9",
    "on_surface":         "#d4e4fa",
    "on_surface_variant": "#b9cacb",
    "outline_variant":    "#3b494b",
}

FONT_FAMILY = "Segoe UI"
SOPORTE_EMAIL = "vortrack.soporte@gmail.com"


def abrir_soporte(parent_root):
    """Abre la ventana modal de Soporte Técnico."""
    dialog = tk.Toplevel(parent_root)
    dialog.title("Soporte Técnico — VorTrack")
    dialog.geometry("480x370")
    dialog.resizable(False, False)
    dialog.configure(bg=COLORS["background"])
    dialog.grab_set()
    dialog.transient(parent_root)

    # Centrar respecto al padre
    parent_root.update_idletasks()
    px = parent_root.winfo_x() + (parent_root.winfo_width() // 2) - 240
    py = parent_root.winfo_y() + (parent_root.winfo_height() // 2) - 185
    dialog.geometry(f"480x370+{px}+{py}")

    # Borde superior decorativo (acento cyan)
    tk.Frame(dialog, bg=COLORS["primary_fixed"], height=3).pack(fill="x", side="top")

    # Contenedor principal
    body = tk.Frame(dialog, bg=COLORS["surface_container"])
    body.pack(fill="both", expand=True, padx=24, pady=20)

    # Icono grande
    tk.Label(
        body, text="\U0001f6e0\ufe0f", font=(FONT_FAMILY, 36),
        bg=COLORS["surface_container"]
    ).pack(pady=(8, 2))

    # Titulo
    tk.Label(
        body, text="\u00bfNecesit\u00e1s ayuda?",
        font=(FONT_FAMILY, 18, "bold"),
        bg=COLORS["surface_container"],
        fg=COLORS["primary_fixed"]
    ).pack()

    # Mensaje amigable
    tk.Label(
        body,
        text="Nuestro equipo est\u00e1 listo para asistirte.\n"
             "Report\u00e1 tu problema o sugerencia y\n"
             "te responderemos a la brevedad. \U0001f60a",
        font=(FONT_FAMILY, 10),
        bg=COLORS["surface_container"],
        fg=COLORS["on_surface_variant"],
        justify="center"
    ).pack(pady=(6, 14))

    # Separador
    tk.Frame(body, bg=COLORS["outline_variant"], height=1).pack(fill="x", pady=(0, 14))

    # Caja del correo
    email_frame = tk.Frame(
        body, bg=COLORS["surface_highest"],
        padx=14, pady=10
    )
    email_frame.pack(fill="x")

    tk.Label(
        email_frame, text="\u2709  Correo de soporte:",
        font=(FONT_FAMILY, 9),
        bg=COLORS["surface_highest"],
        fg=COLORS["on_surface_variant"]
    ).pack(anchor="w")

    email_val = tk.Label(
        email_frame, text=SOPORTE_EMAIL,
        font=(FONT_FAMILY, 13, "bold"),
        bg=COLORS["surface_highest"],
        fg=COLORS["primary_fixed"],
        cursor="hand2"
    )
    email_val.pack(anchor="w", pady=(2, 0))

    tk.Label(
        email_frame, text="(clic para copiar al portapapeles)",
        font=(FONT_FAMILY, 8),
        bg=COLORS["surface_highest"],
        fg=COLORS["on_surface_variant"]
    ).pack(anchor="w")

    # Mensaje de confirmacion de copia (inicialmente oculto)
    copy_confirm = tk.Label(
        body, text="\u2714  \u00a1Correo copiado al portapapeles!",
        font=(FONT_FAMILY, 9, "bold"),
        bg=COLORS["surface_container"],
        fg=COLORS["primary_fixed_dim"]
    )

    def _on_copy(e=None):
        dialog.clipboard_clear()
        dialog.clipboard_append(SOPORTE_EMAIL)
        dialog.update()
        copy_confirm.pack(pady=(8, 0))
        dialog.after(2500, copy_confirm.pack_forget)

    email_val.bind("<Button-1>", _on_copy)

    # Boton Cerrar
    close_btn = tk.Button(
        body, text="  Cerrar  ",
        command=dialog.destroy,
        bg=COLORS["surface_high"],
        fg=COLORS["on_surface"],
        activebackground=COLORS["surface_bright"],
        activeforeground=COLORS["primary_fixed"],
        relief="flat",
        font=(FONT_FAMILY, 10, "bold"),
        padx=20, pady=6,
        cursor="hand2", bd=0
    )
    close_btn.pack(pady=(14, 0))
