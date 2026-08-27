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


class RecoleccionesForm(ctk.CTkFrame if ctk else tk.Frame):
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
        # Título
        self.fw.titulo(self, "Nueva Recolección", pady=(25, 20))

        # Contenedor del formulario con scroll (evita que se corten campos/botón)
        form_frame = ui_utils.scrollable_form(
            self, COLORS["surface_container"], fill="both", expand=True, padx=30, pady=(0, 20))

        # 1. Fecha del Registro
        self.fw.label_campo(form_frame, "Fecha del Registro")

        # Patch ttk style so DateEntry's internal Entry widget uses dark colors
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

        # Catálogos desde la base de datos (FK obligatorias)
        try:
            self.responsables = self.datos.listar_responsables()
            self.lugares = self.datos.listar_lugares()
        except Exception as exc:  # noqa: BLE001
            self.responsables, self.lugares = [], []
            messagebox.showwarning(
                "Base de datos", f"No se pudieron cargar los catálogos:\n{exc}")
        self._resp_by_name = {n: i for i, n in self.responsables}
        self._lug_by_name = {n: i for i, n in self.lugares}

        # 2. Estudiante / Responsable
        self.fw.label_campo(form_frame, "Estudiante / Responsable")
        resp_values = ["Seleccione responsable..."] + [n for _, n in self.responsables]
        self.resp_combo, self.resp_var = self.fw.combo(form_frame, resp_values)
        self.fw.hint(form_frame, "Se le asignarán los puntos automáticamente")

        # 3. Lugar de recolección
        self.fw.label_campo(form_frame, "Lugar de recolección")
        lug_values = ["Seleccione lugar..."] + [n for _, n in self.lugares]
        self.lug_combo, self.lug_var = self.fw.combo(form_frame, lug_values)

        # 4. Cantidad de botellas
        self.fw.label_campo(form_frame, "Cantidad de botellas")
        self.botellas_entry = self.fw.entry(form_frame, "Ej. 20")

        # 5. Peso PET (kg)
        self.fw.label_campo(form_frame, "Peso PET (kg) aprovechado")
        self.peso_entry = self.fw.entry(form_frame, "Ej. 2.5")

        # 6. Observaciones
        self.fw.label_campo(form_frame, "Observaciones")
        self.obs_textbox = self.fw.textbox(form_frame, "Opcional...")

        # 7. Botón Registrar
        self.fw.boton(form_frame, "Registrar PET", self.registrar, tipo="primario")

    def registrar(self):
        fecha = self.date_entry.get()
        resp_name = self.resp_combo.get() if ctk else self.resp_var.get()
        lug_name = self.lug_combo.get() if ctk else self.lug_var.get()
        botellas = self.botellas_entry.get().strip()
        peso = self.peso_entry.get().strip()

        obs = self.obs_textbox.get("1.0", "end-1c")
        if obs.strip() == "Opcional...":
            obs = ""

        id_resp = self._resp_by_name.get(resp_name)
        id_lug = self._lug_by_name.get(lug_name)
        if id_resp is None:
            messagebox.showwarning("Error", "Debe seleccionar un responsable.")
            return
        if id_lug is None:
            messagebox.showwarning("Error", "Debe seleccionar un lugar de recolección.")
            return
        if validaciones.es_vacio(peso):
            messagebox.showwarning("Error", "Debe ingresar el peso de PET aprovechado.")
            return
        ok_peso, peso_val = validaciones.numero(peso)
        if not ok_peso:
            messagebox.showwarning("Error", "El peso debe ser un número válido.")
            return
        botellas_val = None
        if botellas:
            ok_bot, botellas_val = validaciones.entero_positivo(botellas)
            if not ok_bot:
                messagebox.showwarning("Error", "La cantidad de botellas debe ser un número entero.")
                return

        try:
            id_jornada = self.datos.crear_jornada(fecha, id_lug, id_resp, botellas_val, peso_val, obs)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error al guardar",
                                 f"No se pudo registrar en la base de datos:\n\n{exc}")
            return

        messagebox.showinfo("Recolección Registrada", f"Jornada #{id_jornada} registrada correctamente.")

        self.botellas_entry.delete(0, 'end')
        self.peso_entry.delete(0, 'end')
        self.obs_textbox.delete("1.0", "end")
        self.obs_textbox.insert("1.0", "Opcional...")
        if ctk:
            self.resp_combo.set("Seleccione responsable...")
            self.lug_combo.set("Seleccione lugar...")
        else:
            self.resp_var.set("Seleccione responsable...")
            self.lug_var.set("Seleccione lugar...")

        if self.on_register_callback:
            self.on_register_callback()


class RecentRecordsFrame(ctk.CTkFrame if ctk else tk.Frame):
    def __init__(self, parent, datos=None, fabrica=None, **kwargs):
        self.datos = datos or repositorio
        self.fw = fabrica or FabricaWidgets()
        if ctk:
            super().__init__(parent, fg_color=COLORS["surface_container"], border_color=COLORS["primary_fixed"], border_width=1, corner_radius=12, **kwargs)
        else:
            super().__init__(parent, bg=COLORS["surface_container"], bd=1, relief="solid", **kwargs)

        self.setup_ui()

    def setup_ui(self):
        self.fw.titulo(self, "Últimos Registros", pady=(20, 15), padx=20, anchor="w")

        tree_frame = tk.Frame(self, bg=COLORS["surface_container"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")

        columnas = [
            ("fecha", "Fecha", 95, "center"),
            ("responsable", "Responsable", 150, "w"),
            ("lugar", "Lugar", 150, "w"),
            ("botellas", "Botellas", 80, "center"),
            ("peso", "Peso PET (kg)", 110, "center"),
            ("observaciones", "Observaciones", 220, "w"),
        ]
        self.tree = self.fw.tabla(tree_frame, columnas, "Recent.Treeview", yscrollcommand=tree_scroll.set)
        self.tree.pack(fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)

        self.recargar()

    def recargar(self):
        """Recarga la tabla desde la base de datos."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            filas = self.datos.recolecciones_recientes()
        except Exception:  # noqa: BLE001
            return
        for fecha, resp, lugar, botellas, peso, obs in filas:
            f = fecha.strftime("%d/%m/%Y") if hasattr(fecha, "strftime") else str(fecha)
            peso_txt = f"{float(peso):g}" if peso is not None else ""
            bot_txt = str(botellas) if botellas is not None else ""
            self.tree.insert("", "end", values=(f, resp or "", lugar or "", bot_txt, peso_txt, obs or ""))


class RecoleccionesApp:
    def __init__(self, root, on_navigate=None, on_logout=None, datos=None, fabrica=None):
        self.root = root
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.datos = datos or repositorio
        self.fw = fabrica or FabricaWidgets()
        self.root.title("VorTrack - Recolecciones")
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
        # y el panel de registros ocupando el resto. Evita que el form invada la derecha.
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=0, minsize=440)
        self.canvas_frame.grid_columnconfigure(1, weight=1)

        self.form = RecoleccionesForm(self.canvas_frame, on_register_callback=self.on_new_record,
                                      datos=self.datos, fabrica=self.fw)
        self.form.grid(row=0, column=0, sticky="nsew", padx=(0, 20), pady=10)

        self.recent_records = RecentRecordsFrame(self.canvas_frame, datos=self.datos, fabrica=self.fw)
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

        if choice == "Recolección":
            # Ya estamos en la página de recolecciones.
            return
        destinos = {"Transformación": "transformacion", "Impresión": "impresion"}
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

    RecoleccionesApp(root)
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
