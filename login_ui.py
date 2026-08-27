import os
import tkinter as tk
from tkinter import messagebox

import auth
import ui_utils
import validaciones

try:
    # pyrefly: ignore [missing-import]
    import customtkinter as ctk
except ImportError:
    ctk = None

# ---------------------------------------------------------
# COLOR PALETTE (Matched from the HTML provided)
# ---------------------------------------------------------
COLORS = {
    "background": "#051424",
    "surface": "#0d1117",              # For input fields
    "surface_container": "#122131",    # Glass panel simulation
    "surface_high": "#1c2b3c",
    "surface_bright": "#2c3a4c",
    "primary": "#dbfcff",
    "primary_fixed": "#7df4ff",
    "primary_container": "#00f0ff",
    "secondary_container": "#0056fd",
    "on_surface": "#d4e4fa",
    "on_surface_variant": "#b9cacb",
    "outline_variant": "#3b494b",
    "white": "#ffffff",
    "footer": "#010f1f"
}

FONT_FAMILY = "Segoe UI"

class LoginApp:
    def __init__(self, root, on_success=None, servicio_auth=None):
        self.root = root
        self.on_success = on_success
        # Servicio de autenticación inyectable (por defecto, el facade auth que
        # envuelve ServicioAuth). Permite sustituirlo en pruebas.
        self.autenticador = servicio_auth or auth
        self.root.title("VorTrack - Login")
        self.root.minsize(860, 700)
        ui_utils.maximize_window(self.root)
        self.root.configure(bg=COLORS["background"])
        
        # Paths for images
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.logo_path = os.path.join(self.base_dir, "Vortrack logo.png")
        self.icon_path = os.path.join(self.base_dir, "VorTrack icon.png")
        
        # Ícono de la ventana (logo transparente, sin el cuadro oscuro)
        ui_utils.set_window_icon(self.root)

        # Configure CustomTkinter settings
        if ctk:
            ctk.set_appearance_mode("Dark")

        self.setup_ui()
        self._load_remembered_user()
        self.root.bind("<Return>", lambda _event: self.login())

    def _draw_bg_glow(self, event=None):
        """Dibuja el círculo de brillo centrado, escalado al tamaño actual del lienzo."""
        w = self.bg_canvas.winfo_width()
        h = self.bg_canvas.winfo_height()
        self.bg_canvas.delete("glow")
        diameter = int(min(w, h) * 1.15)
        cx, cy = w // 2, h // 2
        self.bg_canvas.create_oval(
            cx - diameter // 2, cy - diameter // 2,
            cx + diameter // 2, cy + diameter // 2,
            fill="#081d33",  # tinte cian-azulado sutil sobre el fondo
            outline="",
            tags="glow",
        )

    def setup_ui(self):
        # Master container
        self.main_container = tk.Frame(self.root, bg=COLORS["background"])
        self.main_container.pack(fill="both", expand=True)

        # Draw a subtle center glow in the background using Canvas.
        # Se redibuja al cambiar el tamaño para quedar centrado en cualquier resolución.
        self.bg_canvas = tk.Canvas(self.main_container, bg=COLORS["background"], highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.bg_canvas.bind("<Configure>", self._draw_bg_glow)

        # ---------------------------------------------------------
        # LOGIN CARD
        # ---------------------------------------------------------
        card_width = 480
        card_height = 540 if ctk else 650
        
        if ctk:
            self.card = ctk.CTkFrame(
                self.main_container,
                width=card_width,
                height=card_height,
                fg_color=COLORS["surface_container"],
                border_color=COLORS["primary_fixed"],
                border_width=1,
                corner_radius=16
            )
            self.card.place(relx=0.5, rely=0.5, anchor="center")
            self.card.pack_propagate(False)
        else:
            self.card = tk.Frame(self.main_container, bg=COLORS["surface_container"], width=card_width, height=card_height, bd=1, relief="solid")
            self.card.place(relx=0.5, rely=0.5, anchor="center")
            self.card.pack_propagate(False)

        # Top border accent logic (gradient simulated with a colored frame)
        accent_frame = tk.Frame(self.card, bg=COLORS["primary_fixed"], height=3)
        accent_frame.pack(side="top", fill="x")

        # --- Logo ---
        self.logo_img = ui_utils.load_image(self.icon_path, size=(110, 110))
        if self.logo_img:
            if ctk:
                logo_lbl = ctk.CTkLabel(self.card, image=self.logo_img, text="")
            else:
                logo_lbl = tk.Label(self.card, image=self.logo_img, bg=COLORS["surface_container"])
            logo_lbl.pack(pady=(35, 10))
        else:
            # Fallback solo si la imagen no existe en disco
            tk.Label(self.card, text="[Logo]", bg=COLORS["surface_container"], fg=COLORS["white"]).pack(pady=(40, 10))

        # --- Titles ---
        if ctk:
            title = ctk.CTkLabel(self.card, text="VorTrack", font=(FONT_FAMILY, 34, "bold"), text_color=COLORS["primary_container"])
            title.pack()
            sub = ctk.CTkLabel(self.card, text="Gestión, Seguimiento y Transformación", font=(FONT_FAMILY, 14), text_color=COLORS["on_surface_variant"])
            sub.pack(pady=(0, 25))
        else:
            tk.Label(self.card, text="VorTrack", font=(FONT_FAMILY, 30, "bold"), bg=COLORS["surface_container"], fg=COLORS["primary_container"]).pack()
            tk.Label(self.card, text="Gestión, Seguimiento y Transformación", font=(FONT_FAMILY, 12), bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"]).pack(pady=(0, 20))

        # --- Form Area ---
        if ctk:
            form_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        else:
            form_frame = tk.Frame(self.card, bg=COLORS["surface_container"])
        form_frame.pack(fill="both", expand=True, padx=40)

        self.remember_var = tk.BooleanVar(value=False)
        self._build_form(form_frame)

        # ---------------------------------------------------------
        # FOOTER
        # ---------------------------------------------------------
        border_top = tk.Frame(self.root, bg=COLORS["outline_variant"], height=1)
        border_top.pack(side="bottom", fill="x")

        footer = tk.Frame(self.root, bg=COLORS["footer"], height=55)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)
        
        copy_lbl = tk.Label(
            footer,
            text="© 2026 desarrollado por Miguel Ruiz Ramirez",
            fg=COLORS["on_surface_variant"],
            bg=COLORS["footer"],
            font=(FONT_FAMILY, 10)
        )
        copy_lbl.pack(expand=True)

    def _build_form(self, form_frame):
        if ctk:
            user_lbl = ctk.CTkLabel(form_frame, text="IDENTIFICADOR", font=(FONT_FAMILY, 12, "bold"), text_color=COLORS["on_surface_variant"])
            user_lbl.pack(anchor="w")
            self.user_entry = ctk.CTkEntry(
                form_frame,
                placeholder_text="vortrack.soporte@gmail.com",
                height=45,
                fg_color=COLORS["surface"],
                border_color=COLORS["outline_variant"],
                text_color=COLORS["on_surface"],
                font=(FONT_FAMILY, 14),
                corner_radius=8
            )
            self.user_entry.pack(fill="x", pady=(2, 16))

            pass_lbl = ctk.CTkLabel(form_frame, text="CREDENCIAL DE ACCESO", font=(FONT_FAMILY, 12, "bold"), text_color=COLORS["on_surface_variant"])
            pass_lbl.pack(anchor="w")

            pass_row = ctk.CTkFrame(form_frame, fg_color="transparent")
            pass_row.pack(fill="x", pady=(2, 10))
            self.pass_entry = ctk.CTkEntry(
                pass_row,
                placeholder_text="••••••••",
                show="*",
                height=45,
                fg_color=COLORS["surface"],
                border_color=COLORS["outline_variant"],
                text_color=COLORS["on_surface"],
                font=(FONT_FAMILY, 14),
                corner_radius=8
            )
            self.pass_entry.pack(side="left", fill="x", expand=True)
            self.toggle_pass_btn = ctk.CTkButton(
                pass_row,
                text="Ver",
                width=70,
                height=45,
                fg_color=COLORS["surface_high"],
                hover_color=COLORS["surface_bright"],
                text_color=COLORS["on_surface"],
                font=(FONT_FAMILY, 12, "bold"),
                corner_radius=8,
                command=self._toggle_password
            )
            self.toggle_pass_btn.pack(side="left", padx=(8, 0))

            options_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
            options_frame.pack(fill="x", pady=(5, 20))

            remember_cb = ctk.CTkCheckBox(
                options_frame,
                text="Recordar sesión",
                variable=self.remember_var,
                font=(FONT_FAMILY, 12),
                text_color=COLORS["on_surface_variant"],
                fg_color=COLORS["primary_fixed"],
                hover_color=COLORS["primary_container"],
                border_color=COLORS["outline_variant"],
                checkbox_height=20,
                checkbox_width=20,
                corner_radius=4
            )
            remember_cb.pack(side="left")

            forgot_btn = ctk.CTkButton(
                options_frame,
                text="¿Olvidó su credencial?",
                font=(FONT_FAMILY, 12, "underline"),
                text_color=COLORS["primary_fixed"],
                fg_color="transparent",
                hover_color=COLORS["surface_container"],
                width=0,
                height=20,
                command=self.forgot_password
            )
            forgot_btn.pack(side="right")

            login_btn = ctk.CTkButton(
                form_frame,
                text="INICIAR SESIÓN",
                font=(FONT_FAMILY, 15, "bold"),
                height=48,
                fg_color=COLORS["secondary_container"],
                hover_color=COLORS["primary_container"],
                text_color=COLORS["white"],
                corner_radius=8,
                command=self.login
            )
            login_btn.pack(fill="x", pady=(10, 5))
            return

        user_lbl = tk.Label(form_frame, text="IDENTIFICADOR", font=(FONT_FAMILY, 12, "bold"), bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"])
        user_lbl.pack(anchor="w")
        self.user_entry = tk.Entry(form_frame, bg=COLORS["surface"], fg=COLORS["on_surface"], insertbackground=COLORS["on_surface"], font=(FONT_FAMILY, 14), relief="flat")
        self.user_entry.pack(fill="x", ipady=8, pady=(2, 16))

        pass_lbl = tk.Label(form_frame, text="CREDENCIAL DE ACCESO", font=(FONT_FAMILY, 12, "bold"), bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"])
        pass_lbl.pack(anchor="w")

        pass_row = tk.Frame(form_frame, bg=COLORS["surface_container"])
        pass_row.pack(fill="x", pady=(2, 10))
        self.pass_entry = tk.Entry(pass_row, show="*", bg=COLORS["surface"], fg=COLORS["on_surface"], insertbackground=COLORS["on_surface"], font=(FONT_FAMILY, 14), relief="flat")
        self.pass_entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.toggle_pass_btn = tk.Button(
            pass_row,
            text="Ver",
            bg=COLORS["surface_high"],
            fg=COLORS["on_surface"],
            activebackground=COLORS["surface_bright"],
            activeforeground=COLORS["primary_fixed"],
            font=(FONT_FAMILY, 11, "bold"),
            relief="flat",
            bd=0,
            padx=14,
            cursor="hand2",
            command=self._toggle_password
        )
        self.toggle_pass_btn.pack(side="left", fill="y", padx=(8, 0))

        options_frame = tk.Frame(form_frame, bg=COLORS["surface_container"])
        options_frame.pack(fill="x", pady=(5, 20))

        remember_cb = tk.Checkbutton(
            options_frame,
            text="Recordar sesión",
            variable=self.remember_var,
            bg=COLORS["surface_container"],
            fg=COLORS["on_surface_variant"],
            selectcolor=COLORS["surface"],
            activebackground=COLORS["surface_container"],
            activeforeground=COLORS["on_surface_variant"],
            font=(FONT_FAMILY, 12)
        )
        remember_cb.pack(side="left")

        forgot_btn = tk.Button(
            options_frame,
            text="¿Olvidó su credencial?",
            bg=COLORS["surface_container"],
            fg=COLORS["primary_fixed"],
            activebackground=COLORS["surface_container"],
            activeforeground=COLORS["primary_fixed"],
            relief="flat",
            borderwidth=0,
            font=(FONT_FAMILY, 12, "underline"),
            cursor="hand2",
            command=self.forgot_password
        )
        forgot_btn.pack(side="right")

        login_btn = tk.Button(
            form_frame,
            text="INICIAR SESIÓN",
            bg=COLORS["secondary_container"],
            fg=COLORS["white"],
            activebackground=COLORS["primary_container"],
            activeforeground=COLORS["white"],
            font=(FONT_FAMILY, 15, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.login
        )
        login_btn.pack(fill="x", ipady=10, pady=(10, 5))

    def _toggle_password(self):
        """Alterna entre mostrar y ocultar la contraseña."""
        self.pass_visible = not getattr(self, "pass_visible", False)
        self.pass_entry.configure(show="" if self.pass_visible else "*")
        self.toggle_pass_btn.configure(text="Ocultar" if self.pass_visible else "Ver")

    def _load_remembered_user(self):
        remembered = self.autenticador.load_remembered_user()
        if remembered:
            self.user_entry.insert(0, remembered)
            self.remember_var.set(True)

    # ---------------------------------------------------------
    # ACTIONS
    # ---------------------------------------------------------
    def forgot_password(self):
        import soporte_dialog
        messagebox.showinfo(
            "Recuperar Credencial",
            "Para restablecer su contraseña, escriba al correo de soporte:\n\n"
            f"{soporte_dialog.SOPORTE_EMAIL}",
        )

    def login(self):
        user = self.user_entry.get()
        pwd = self.pass_entry.get()

        if validaciones.es_vacio(user) or validaciones.es_vacio(pwd):
            messagebox.showwarning("Campos Requeridos", "Por favor ingrese su identificador y credencial de acceso.")
            return

        try:
            autenticado = self.autenticador.authenticate(user, pwd)
        except auth.DatabaseUnavailable as exc:
            messagebox.showerror(
                "Error de conexión",
                "No se pudo conectar a la base de datos:\n\n"
                f"{exc}\n\nRevise db_config.ini y que el servidor esté accesible."
            )
            return

        if not autenticado:
            messagebox.showerror(
                "Acceso Denegado",
                "Identificador o credencial incorrectos.\n\nVerifique sus datos e intente nuevamente."
            )
            self.pass_entry.delete(0, "end")
            self.pass_entry.focus_set()
            return

        if self.remember_var.get():
            self.autenticador.save_remembered_user(user)
        else:
            self.autenticador.clear_remembered_user()

        if self.on_success:
            self.on_success()
            return

        print("Login Exitoso. Iniciando VorTrack...")
        self.root.destroy()

        try:
            import inicio_ui
            inicio_ui.main()
        except ImportError:
            messagebox.showerror("Error de Inicio", "No se encontró el módulo principal de la aplicación (inicio_ui.py).")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error al iniciar la aplicación:\n{e}")

def main():
    try:
        from app import run
        run()
    except ImportError:
        if ctk:
            root = ctk.CTk()
        else:
            root = tk.Tk()

        LoginApp(root)
        root.mainloop()

if __name__ == "__main__":
    main()
