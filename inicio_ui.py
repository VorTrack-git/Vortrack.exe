import os
import sys
import tkinter as tk
from tkinter import messagebox

import auth
import ui_utils
# pyrefly: ignore [missing-import]
from PIL import Image, ImageTk

try:
    # pyrefly: ignore [missing-import]
    import customtkinter as ctk
except ImportError:
    ctk = None

# ---------------------------------------------------------
# COLOR PALETTE (From Web Application Material/Tailwind Theme)
# ---------------------------------------------------------
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
    "white": "#ffffff"
}

FONT_FAMILY = "Segoe UI"  # Fallback for Windows cross-compatibility

class VorTrackApp:
    def __init__(self, root, on_logout=None, on_navigate=None):
        self.root = root
        self.on_logout = on_logout
        self.on_navigate = on_navigate
        self.current_user = auth.get_current_user()
        self.root.title("VorTrack - Quiénes somos")
        self.root.minsize(1024, 700)
        ui_utils.maximize_window(self.root)
        self.root.configure(bg=COLORS["background"])

        # Load Images
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.join(self.base_dir, "VorTrack icon.png")
        self.logo_path = os.path.join(self.base_dir, "Vortrack logo.png")

        # Ícono de la ventana (logo transparente, sin el cuadro oscuro)
        ui_utils.set_window_icon(self.root)

        # Configure CustomTkinter settings if available
        if ctk:
            ctk.set_appearance_mode("Dark")
            ctk.set_default_color_theme("blue")

        self.setup_ui()

    def load_ctk_image(self, path, size):
        """Helper to create CTkImage or ImageTk depending on library availability."""
        return ui_utils.load_image(path, size)

    def setup_ui(self):
        # Master container
        self.main_container = tk.Frame(self.root, bg=COLORS["background"])
        self.main_container.pack(fill="both", expand=True)

        # 2. TOP NAVBAR
        self.build_navbar()

        # 3. MAIN CONTENT AREA (Scrollable / Flexible canvas)
        self.build_main_content()

        # 4. FOOTER
        self.build_footer()

    # ---------------------------------------------------------
    # 2. TOP NAVBAR
    # ---------------------------------------------------------
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

        # Item 1: Quienes Somos (Active)
        quienes_frame = tk.Frame(nav_items_frame, bg=COLORS["surface_container"])
        quienes_frame.pack(side="left", padx=16)

        lbl_quienes = tk.Label(
            quienes_frame, 
            text="QUIÉNES SOMOS", 
            fg=COLORS["primary_fixed"], 
            bg=COLORS["surface_container"],
            font=(FONT_FAMILY, 10, "bold"),
            cursor="hand2"
        )
        lbl_quienes.pack(side="top")

        # Cyan underline for active tab
        underline = tk.Frame(quienes_frame, bg=COLORS["primary_fixed"], height=2, width=110)
        underline.pack(side="bottom", fill="x", pady=(3, 0))

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

    # ---------------------------------------------------------
    # 3. MAIN CONTENT CANVAS
    # ---------------------------------------------------------
    def build_main_content(self):
        # Scrollable / Grid Frame Container
        self.canvas_frame = tk.Frame(self.main_container, bg=COLORS["background"])
        self.canvas_frame.pack(fill="both", expand=True, padx=40, pady=20)

        # Left Column Frame (Hero Image / Logo showcase)
        left_col = tk.Frame(self.canvas_frame, bg=COLORS["background"])
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 20))

        # Hero Logo Card Container (Glass Panel style)
        if ctk:
            glass_card = ctk.CTkFrame(
                left_col,
                fg_color=COLORS["surface_container"],
                border_color=COLORS["primary_fixed_dim"],
                border_width=1,
                corner_radius=20
            )
            glass_card.pack(expand=True, padx=10, pady=10)
        else:
            glass_card = tk.Frame(
                left_col,
                bg=COLORS["surface_container"],
                bd=1,
                relief="solid"
            )
            glass_card.pack(expand=True, padx=10, pady=10)

        # Glow Image Showcase (Adjusted to match card frame aspect ratio)
        self.hero_logo_img = self.load_ctk_image(self.logo_path, size=(450, 365))
        if self.hero_logo_img:
            if ctk:
                hero_lbl = ctk.CTkLabel(glass_card, image=self.hero_logo_img, text="")
            else:
                hero_lbl = tk.Label(glass_card, image=self.hero_logo_img, bg=COLORS["surface_container"])
            hero_lbl.pack(expand=True, padx=8, pady=8)

        # Right Column Frame (Text content, description & features)
        right_col = tk.Frame(self.canvas_frame, bg=COLORS["background"])
        right_col.pack(side="right", fill="both", expand=True, padx=(20, 0))

        # Badge Pill
        badge_frame = tk.Frame(right_col, bg=COLORS["background"])
        badge_frame.pack(anchor="w", pady=(10, 8))

        if ctk:
            badge_lbl = ctk.CTkLabel(
                badge_frame,
                text="●   GESTIÓN  ·  SEGUIMIENTO  ·  TRANSFORMACIÓN",
                fg_color=COLORS["surface_high"],
                text_color=COLORS["primary_fixed"],
                font=(FONT_FAMILY, 10, "bold"),
                corner_radius=15
            )
            badge_lbl.pack(padx=14, pady=6)
        else:
            badge_lbl = tk.Label(
                badge_frame,
                text="●   GESTIÓN  ·  SEGUIMIENTO  ·  TRANSFORMACIÓN",
                fg=COLORS["primary_fixed"],
                bg=COLORS["surface_high"],
                font=(FONT_FAMILY, 9, "bold"),
                padx=12,
                pady=4
            )
            badge_lbl.pack()

        # Main Title (VorTrack)
        title_lbl = tk.Label(
            right_col,
            text="VorTrack",
            fg=COLORS["primary_container"],
            bg=COLORS["background"],
            font=(FONT_FAMILY, 38, "bold"),
            anchor="w"
        )
        title_lbl.pack(fill="x", pady=(0, 16))

        # Description Box (Glass Card with cyan left accent line)
        if ctk:
            desc_card = ctk.CTkFrame(
                right_col,
                fg_color=COLORS["surface_container"],
                border_color=COLORS["outline_variant"],
                border_width=1,
                corner_radius=16
            )
            desc_card.pack(fill="x", pady=(0, 20))
        else:
            desc_card = tk.Frame(
                right_col,
                bg=COLORS["surface_container"],
                bd=1,
                relief="solid"
            )
            desc_card.pack(fill="x", pady=(0, 20))

        # Left cyan accent strip
        accent_strip = tk.Frame(desc_card, bg=COLORS["primary_fixed_dim"], width=5)
        accent_strip.pack(side="left", fill="y")

        desc_content = tk.Frame(desc_card, bg=COLORS["surface_container"])
        desc_content.pack(side="left", fill="both", expand=True, padx=18, pady=16)

        p1_text = (
            "Es un software de escritorio que apoya la gestión y realización "
            "del proyecto TRANSRE/SC, del Instituto San Carlos de la Salle."
        )
        lbl_p1 = tk.Label(
            desc_content,
            text=p1_text,
            fg=COLORS["on_surface"],
            bg=COLORS["surface_container"],
            font=(FONT_FAMILY, 11),
            wraplength=520,
            justify="left"
        )
        lbl_p1.pack(anchor="w", pady=(0, 8))

        p2_text = (
            "Permite el registro, organización, consulta y análisis de la información "
            "generada durante el proceso de aprovechamiento de residuos de tereftalato de polietileno (PET) "
            "para la fabricación de material didáctico."
        )
        lbl_p2 = tk.Label(
            desc_content,
            text=p2_text,
            fg=COLORS["on_surface_variant"],
            bg=COLORS["surface_container"],
            font=(FONT_FAMILY, 10),
            wraplength=520,
            justify="left"
        )
        lbl_p2.pack(anchor="w")

        # Feature Cards (3 Columns Grid)
        features_frame = tk.Frame(right_col, bg=COLORS["background"])
        features_frame.pack(fill="x", pady=(0, 20))

        self.create_feature_card(
            features_frame, 
            icon="🛣️", 
            title="Trazabilidad", 
            sub="Fortalecer el control de procesos."
        )
        self.create_feature_card(
            features_frame, 
            icon="📊", 
            title="Indicadores", 
            sub="Facilitar la generación de métricas."
        )
        self.create_feature_card(
            features_frame, 
            icon="💡", 
            title="Decisiones", 
            sub="Apoyar la toma de decisiones."
        )

        # Primary Action Button: Explorar Sistema
        if ctk:
            btn_explorar = ctk.CTkButton(
                right_col,
                text="EXPLORAR SISTEMA   ➔",
                fg_color=COLORS["secondary_container"],
                hover_color=COLORS["primary_container"],
                text_color=COLORS["white"],
                font=(FONT_FAMILY, 11, "bold"),
                height=46,
                width=240,
                corner_radius=16,
                command=self.explorar_sistema
            )
            btn_explorar.pack(anchor="w", pady=6)
        else:
            btn_explorar = tk.Button(
                right_col,
                text="EXPLORAR SISTEMA   ➔",
                fg=COLORS["white"],
                bg=COLORS["secondary_container"],
                activebackground=COLORS["primary_container"],
                activeforeground=COLORS["surface_lowest"],
                font=(FONT_FAMILY, 11, "bold"),
                bd=0,
                padx=24,
                pady=12,
                cursor="hand2",
                command=self.explorar_sistema
            )
            btn_explorar.pack(anchor="w", pady=6)

    def create_feature_card(self, parent, icon, title, sub):
        """Helper to create feature card boxes."""
        if ctk:
            card = ctk.CTkFrame(
                parent,
                fg_color=COLORS["surface_container"],
                border_color=COLORS["outline_variant"],
                border_width=1,
                corner_radius=12,
                width=165
            )
            card.pack(side="left", expand=True, fill="both", padx=4)
        else:
            card = tk.Frame(
                parent,
                bg=COLORS["surface_container"],
                bd=1,
                relief="solid"
            )
            card.pack(side="left", expand=True, fill="both", padx=4, pady=4)

        card_content = tk.Frame(card, bg=COLORS["surface_container"])
        card_content.pack(fill="both", expand=True, padx=12, pady=12)

        lbl_icon = tk.Label(
            card_content,
            text=icon,
            font=(FONT_FAMILY, 16),
            bg=COLORS["surface_container"]
        )
        lbl_icon.pack(anchor="w", pady=(0, 4))

        lbl_title = tk.Label(
            card_content,
            text=title,
            fg=COLORS["white"],
            bg=COLORS["surface_container"],
            font=(FONT_FAMILY, 11, "bold")
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            card_content,
            text=sub,
            fg=COLORS["on_surface_variant"],
            bg=COLORS["surface_container"],
            font=(FONT_FAMILY, 9),
            wraplength=140,
            justify="left"
        )
        lbl_sub.pack(anchor="w", pady=(2, 0))

    # ---------------------------------------------------------
    # 4. FOOTER
    # ---------------------------------------------------------
    def build_footer(self):
        # Border top line
        border_top = tk.Frame(self.main_container, bg=COLORS["outline_variant"], height=1)
        border_top.pack(fill="x", side="top")

        footer_frame = tk.Frame(self.main_container, bg=COLORS["surface_lowest"], height=65)
        footer_frame.pack(fill="x", side="bottom")
        footer_frame.pack_propagate(False)

        footer_content = tk.Frame(footer_frame, bg=COLORS["surface_lowest"])
        footer_content.pack(fill="both", expand=True, padx=24, pady=10)

        # Left Footer Text
        left_foot = tk.Frame(footer_content, bg=COLORS["surface_lowest"])
        left_foot.pack(side="left")

        brand_lbl = tk.Label(
            left_foot,
            text="VorTrack",
            fg=COLORS["primary_fixed"],
            bg=COLORS["surface_lowest"],
            font=(FONT_FAMILY, 12, "bold")
        )
        brand_lbl.pack(side="left", padx=(0, 10))

        copy_lbl = tk.Label(
            left_foot,
            text="© 2026 desarrollado por Miguel Ruiz Ramirez",
            fg=COLORS["on_surface_variant"],
            bg=COLORS["surface_lowest"],
            font=(FONT_FAMILY, 9)
        )
        copy_lbl.pack(side="left")

        # Right Footer Links
        right_foot = tk.Frame(footer_content, bg=COLORS["surface_lowest"])
        right_foot.pack(side="right")

        links = ["Privacidad", "Términos de Uso", "Contacto", "Soporte Técnico"]
        for link in links:
            lbl_link = tk.Label(
                right_foot,
                text=link,
                fg=COLORS["on_surface_variant"],
                bg=COLORS["surface_lowest"],
                font=(FONT_FAMILY, 9, "bold")
            )
            lbl_link.pack(side="left", padx=10)
            ui_utils.bind_footer_link(
                lbl_link, self.root, link,
                base_fg=COLORS["on_surface_variant"],
                hover_fg=COLORS["primary_fixed"]
            )

    # ---------------------------------------------------------
    # ACTIONS
    # ---------------------------------------------------------
    def on_registrar_select(self, choice):
        # Restaura la etiqueta del menú (solo en la versión ctk).
        if hasattr(self, "registrar_btn") and ctk:
            self.registrar_btn.set("REGISTRAR ▾")

        destinos = {"Recolección": "recoleccion", "Transformación": "transformacion", "Impresión": "impresion"}
        if choice in destinos:
            if self.on_navigate:
                self.on_navigate(destinos[choice])
            else:
                messagebox.showinfo(choice, f"El módulo de {choice} se abre desde la aplicación principal.")

    def ir_a_historico(self):
        if self.on_navigate:
            self.on_navigate("historico")
        else:
            messagebox.showinfo("Histórico e Informes", "Disponible desde la aplicación principal.")

    def explorar_sistema(self):
        if self.on_navigate:
            self.on_navigate("recoleccion")
        else:
            messagebox.showinfo("VorTrack", "Iniciando explorador del sistema TRANSRE/SC...")

    def logout(self):
        if messagebox.askyesno("Cerrar sesión", "¿Desea cerrar sesión en VorTrack?"):
            if self.on_logout:
                self.on_logout()
            else:
                auth.logout()
                self.root.destroy()


def main(on_logout=None):
    if ctk:
        root = ctk.CTk()
    else:
        root = tk.Tk()

    VorTrackApp(root, on_logout=on_logout)
    root.mainloop()

if __name__ == "__main__":
    try:
        from app import run
        run()
    except ImportError:
        try:
            auth.require_auth()
        except RuntimeError as exc:
            messagebox.showerror("Acceso restringido", str(exc))
            import login_ui
            login_ui.main()
        else:
            main()
