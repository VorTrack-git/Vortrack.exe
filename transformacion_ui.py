import os
import tkinter as tk

from tkinter import messagebox, ttk
from datetime import datetime

import auth
import ui_utils
import repositorio
import validaciones
from ui_tema import COLORS, FONT_FAMILY
from widgets import FabricaWidgets

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None

try:
    import customtkinter as ctk
except ImportError:
    ctk = None


class TransformacionForm(ctk.CTkFrame if ctk else tk.Frame):
    """Formulario para registrar la producción de filamento 3D a partir de PET (extrusión)."""

    def __init__(self, parent, on_register_callback=None, datos=None, fabrica=None, **kwargs):
        self.on_register_callback = on_register_callback
        self.datos = datos or repositorio
        self.fw = fabrica or FabricaWidgets()
        if ctk:
            super().__init__(parent, fg_color=COLORS["surface_container"], border_color=COLORS["primary_fixed"], border_width=1, corner_radius=12, **kwargs)
        else:
            super().__init__(parent, bg=COLORS["surface_container"], bd=1, relief="solid", **kwargs)

        self.setup_ui()

    def setup_ui(self):
        # Título + subtítulo
        if ctk:
            ctk.CTkLabel(self, text="Nueva Transformación", font=(FONT_FAMILY, 20, "bold"), text_color=COLORS["primary_fixed"]).pack(pady=(25, 4))
            ctk.CTkLabel(self, text="Producción de filamento 3D (extrusión de PET)", font=(FONT_FAMILY, 11), text_color=COLORS["on_surface_variant"]).pack(pady=(0, 16))
        else:
            tk.Label(self, text="Nueva Transformación", font=(FONT_FAMILY, 16, "bold"), bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(pady=(20, 2))
            tk.Label(self, text="Producción de filamento 3D (extrusión de PET)", font=(FONT_FAMILY, 9), bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"]).pack(pady=(0, 12))

        # Contenedor del formulario con scroll (evita que se corten campos/botón)
        form_frame = ui_utils.scrollable_form(
            self, COLORS["surface_container"], fill="both", expand=True, padx=30, pady=(0, 20))

        # 1. Fecha del Registro
        self.fw.label_campo(form_frame, "Fecha del Registro")

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
            self.jornadas = self.datos.listar_jornadas()
        except Exception as exc:  # noqa: BLE001
            self.jornadas = []
            messagebox.showwarning("Base de datos", f"No se pudieron cargar las jornadas:\n{exc}")
        self._jornada_by_label = {lab: (idj, peso) for idj, lab, peso in self.jornadas}

        self.fw.label_campo(form_frame, "Jornada de recolección (origen del PET)")
        jornada_values = ["Seleccione jornada..."] + [lab for _, lab, _ in self.jornadas]
        self.jornada_combo, self.jornada_var = self.fw.combo(
            form_frame, jornada_values, command=self._on_jornada)

        # 3. Peso ingresado (kg) — automático desde la jornada seleccionada
        self.fw.label_campo(form_frame, "Peso ingresado (kg) — PET de la jornada")
        self.ingresado_entry = self.fw.entry(form_frame, "")
        self._set_readonly(self.ingresado_entry, "—")

        # 4. Peso salido (kg)
        self.fw.label_campo(form_frame, "Peso salido (kg) — filamento")
        self.salido_entry = self.fw.entry(form_frame, "Ej. 1.7")
        self.salido_entry.bind("<KeyRelease>", self._update_desperdicio)

        # 5. Desperdicio (kg) — calculado automáticamente (ingresado - salido)
        self.fw.label_campo(form_frame, "Desperdicio (kg) — automático")
        self.desperdicio_entry = self.fw.entry(form_frame, "")
        self._set_readonly(self.desperdicio_entry, "—")

        # 6. Color del filamento
        self.fw.label_campo(form_frame, "Color del filamento")
        self.color_entry = self.fw.entry(form_frame, "Ej. Translúcido, Azul...")

        # 7. Diámetro (mm)
        self.fw.label_campo(form_frame, "Diámetro (mm)")
        self.diam_entry = self.fw.entry(form_frame, "Ej. 1.75")

        # 8. Metros de filamento producidos
        self.fw.label_campo(form_frame, "Metros de filamento producidos")
        self.metros_entry = self.fw.entry(form_frame, "Ej. 560")

        # 9. Observaciones
        self.fw.label_campo(form_frame, "Observaciones")
        self.obs_textbox = self.fw.textbox(form_frame, "Opcional...")

        # 10. Botón Registrar
        self.fw.boton(form_frame, "Registrar Filamento", self.registrar, tipo="primario")

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

        if validaciones.es_vacio(salido):
            messagebox.showwarning("Error", "Debe ingresar el peso salido (filamento).")
            return
        ok_salido, salido_val = validaciones.numero_positivo(salido)
        if not ok_salido:
            messagebox.showwarning("Error", "El peso salido debe ser un número mayor que cero.")
            return
        if salido_val > ingresado_val:
            messagebox.showwarning(
                "Error", f"El peso salido no puede superar el ingresado ({ingresado_val:g} kg).")
            return

        if validaciones.es_vacio(metros):
            messagebox.showwarning("Error", "Debe ingresar los metros de filamento producidos.")
            return
        ok_metros, metros_val = validaciones.numero_positivo(metros)
        if not ok_metros:
            messagebox.showwarning("Error", "Los metros deben ser un número mayor que cero.")
            return

        diam_val = None
        if diam:
            ok_diam, diam_val = validaciones.numero(diam)
            if not ok_diam:
                messagebox.showwarning("Error", "El diámetro debe ser un número válido.")
                return

        try:
            id_prod = self.datos.crear_produccion(
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
    def __init__(self, parent, datos=None, fabrica=None, **kwargs):
        self.datos = datos or repositorio
        self.fw = fabrica or FabricaWidgets()
        if ctk:
            super().__init__(parent, fg_color=COLORS["surface_container"], border_color=COLORS["primary_fixed"], border_width=1, corner_radius=12, **kwargs)
        else:
            super().__init__(parent, bg=COLORS["surface_container"], bd=1, relief="solid", **kwargs)

        self.setup_ui()

    def setup_ui(self):
        self.fw.titulo(self, "Historial de Filamento", pady=(20, 15), padx=20, anchor="w")

        tree_frame = tk.Frame(self, bg=COLORS["surface_container"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")

        columnas = [
            ("fecha", "Fecha", 90, "center"),
            ("jornada", "Jornada", 70, "center"),
            ("ingresado", "Ingresado (kg)", 100, "center"),
            ("salido", "Salido (kg)", 90, "center"),
            ("desperdicio", "Desperdicio (kg)", 110, "center"),
            ("color", "Color", 100, "w"),
            ("diametro", "Diám. (mm)", 85, "center"),
            ("metros", "Metros (m)", 90, "center"),
            ("observaciones", "Observaciones", 170, "w"),
        ]
        self.tree = self.fw.tabla(tree_frame, columnas, "Transf.Treeview", yscrollcommand=tree_scroll.set)
        self.tree.pack(fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)

        self.recargar()

    def recargar(self):
        """Recarga el historial desde la base de datos."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            filas = self.datos.producciones_recientes()
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
    def __init__(self, root, on_navigate=None, on_logout=None, datos=None, fabrica=None):
        self.root = root
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.datos = datos or repositorio
        self.fw = fabrica or FabricaWidgets()
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

        ui_utils.build_app_navbar(self)
        self.build_main_content()
        ui_utils.build_app_footer(self)

    def build_main_content(self):
        self.canvas_frame = tk.Frame(self.main_container, bg=COLORS["background"])
        self.canvas_frame.pack(fill="both", expand=True, padx=40, pady=20)

        # grid con anchos deterministas: el formulario a la izquierda (ancho fijo)
        # y el panel de registros ocupando el resto.
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=0, minsize=440)
        self.canvas_frame.grid_columnconfigure(1, weight=1)

        self.form = TransformacionForm(self.canvas_frame, on_register_callback=self.on_new_record,
                                       datos=self.datos, fabrica=self.fw)
        self.form.grid(row=0, column=0, sticky="nsew", padx=(0, 20), pady=10)

        self.recent_records = RecentTransformacionesFrame(self.canvas_frame, datos=self.datos, fabrica=self.fw)
        self.recent_records.grid(row=0, column=1, sticky="nsew", pady=10)

    def on_new_record(self):
        self.recent_records.recargar()

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
