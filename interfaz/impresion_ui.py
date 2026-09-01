import os
import tkinter as tk

from tkinter import messagebox, ttk
from datetime import datetime

import servicios.auth as auth
import interfaz.ui_utils as ui_utils
import datos.repositorio as repositorio
import servicios.validaciones as validaciones
from interfaz.ui_tema import COLORS, FONT_FAMILY
from interfaz.widgets import FabricaWidgets
from servicios.servicio_proyeccion import ServicioProyeccion

try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

# Estados permitidos por el CHECK constraint de FabricacionObjetos.Estado
ESTADOS = ["Seleccione estado...", "En proceso", "Finalizado", "Fallido"]


class ImpresionForm(ctk.CTkFrame if ctk else tk.Frame):
    """Formulario para registrar impresiones 3D de material didáctico."""

    def __init__(self, parent, on_register_callback=None, datos=None, proyeccion=None, fabrica=None, **kwargs):
        self.on_register_callback = on_register_callback
        self.datos = datos or repositorio
        self.proyeccion = proyeccion or ServicioProyeccion()
        self.fw = fabrica or FabricaWidgets()
        if ctk:
            super().__init__(parent, fg_color=COLORS["surface_container"], border_color=COLORS["primary_fixed"], border_width=1, corner_radius=12, **kwargs)
        else:
            super().__init__(parent, bg=COLORS["surface_container"], bd=1, relief="solid", **kwargs)

        self.setup_ui()

    def setup_ui(self):
        # Título + subtítulo
        if ctk:
            ctk.CTkLabel(self, text="Nueva Impresión", font=(FONT_FAMILY, 20, "bold"), text_color=COLORS["primary_fixed"]).pack(pady=(25, 4))
            ctk.CTkLabel(self, text="Fabricación de material didáctico (impresión 3D)", font=(FONT_FAMILY, 11), text_color=COLORS["on_surface_variant"]).pack(pady=(0, 16))
        else:
            tk.Label(self, text="Nueva Impresión", font=(FONT_FAMILY, 16, "bold"), bg=COLORS["surface_container"], fg=COLORS["primary_fixed"]).pack(pady=(20, 2))
            tk.Label(self, text="Fabricación de material didáctico (impresión 3D)", font=(FONT_FAMILY, 9), bg=COLORS["surface_container"], fg=COLORS["on_surface_variant"]).pack(pady=(0, 12))

        # Contenedor del formulario con scroll (evita que se corten campos/botón)
        form_frame = ui_utils.scrollable_form(
            self, COLORS["surface_container"], fill="both", expand=True, padx=30, pady=(0, 20))

        # 1. Fecha del Registro
        self.fw.label_campo(form_frame, "Fecha del Registro")

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
                    form_frame, placeholder_text="DD/MM/YYYY", height=35,
                    fg_color=COLORS["surface_lowest"], border_color=COLORS["outline_variant"],
                    text_color=COLORS["on_surface"], font=(FONT_FAMILY, 13)
                )
                self.date_entry.insert(0, current_date)
                self.date_entry.pack(fill="x", pady=(2, 15))
            else:
                self.date_entry = tk.Entry(form_frame)
                self.date_entry.insert(0, current_date)
                self.date_entry.pack(fill="x", pady=(2, 10))

        # Catálogos desde la base de datos (FK obligatorias)
        try:
            self.modelos = self.datos.listar_modelos_admin()   # (id, nombre, cat, tiempo_h, peso_g)
            self.producciones = self.datos.listar_producciones()
        except Exception as exc:  # noqa: BLE001
            self.modelos, self.producciones = [], []
            messagebox.showwarning("Base de datos", f"No se pudieron cargar los catálogos:\n{exc}")
        self._modelo_by_name = {row[1]: row[0] for row in self.modelos}
        # estimados por modelo: (tiempo_estimado_horas, peso_estimado_gramos)
        self._modelo_estimados = {row[1]: (row[3], row[4]) for row in self.modelos}
        self._prod_by_label = {lab: idp for idp, lab, _ in self.producciones}

        # 2. Modelo (material didáctico)
        self.fw.label_campo(form_frame, "Modelo (material didáctico)")
        modelo_values = ["Seleccione modelo..."] + [row[1] for row in self.modelos]
        self.modelo_combo, self.modelo_var = self.fw.combo(form_frame, modelo_values, command=self._proyectar)

        # 3. Producción de filamento utilizada
        self.fw.label_campo(form_frame, "Filamento utilizado (producción)")
        prod_values = ["Seleccione producción..."] + [lab for _, lab, _ in self.producciones]
        self.prod_combo, self.prod_var = self.fw.combo(form_frame, prod_values)

        # 4. Cantidad de piezas
        self.fw.label_campo(form_frame, "Cantidad de piezas")
        self.piezas_entry = self.fw.entry(form_frame, "Ej. 3")
        self.piezas_entry.bind("<KeyRelease>", self._proyectar)

        # 5. Peso de filamento utilizado (g)
        self.fw.label_campo(form_frame, "Peso de filamento utilizado (g)")
        self.filamento_entry = self.fw.entry(form_frame, "Ej. 120")

        # 6. Tiempo de impresión (min)
        self.fw.label_campo(form_frame, "Tiempo de impresión (min)")
        self.tiempo_entry = self.fw.entry(form_frame, "Ej. 150")

        # 7. Estado
        self.fw.label_campo(form_frame, "Estado")
        self.estado_combo, self.estado_var = self.fw.combo(form_frame, ESTADOS)

        # 8. Botón Registrar
        self.fw.boton(form_frame, "Registrar Impresión", self.registrar, tipo="primario")

    def _proyectar(self, _event=None):
        """Proyecta peso (g) y tiempo (min) según el modelo elegido y la cantidad."""
        nombre = self.modelo_combo.get() if ctk else self.modelo_var.get()
        est = self._modelo_estimados.get(nombre)
        if not est:
            return
        tiempo_h, peso_g = est
        peso_total, tiempo_min = self.proyeccion.proyeccion_impresion(
            tiempo_h, peso_g, self.piezas_entry.get().strip())
        if peso_total is not None:
            self.filamento_entry.delete(0, "end")
            self.filamento_entry.insert(0, f"{peso_total:g}")
        if tiempo_min is not None:
            self.tiempo_entry.delete(0, "end")
            self.tiempo_entry.insert(0, f"{tiempo_min}")

    def registrar(self):
        fecha = self.date_entry.get()
        modelo_name = self.modelo_combo.get() if ctk else self.modelo_var.get()
        prod_label = self.prod_combo.get() if ctk else self.prod_var.get()
        estado = self.estado_combo.get() if ctk else self.estado_var.get()
        piezas = self.piezas_entry.get().strip()
        filamento = self.filamento_entry.get().strip()
        tiempo = self.tiempo_entry.get().strip()

        id_modelo = self._modelo_by_name.get(modelo_name)
        id_prod = self._prod_by_label.get(prod_label)
        if id_modelo is None:
            messagebox.showwarning("Error", "Debe seleccionar un modelo.")
            return
        if id_prod is None:
            messagebox.showwarning("Error", "Debe seleccionar la producción de filamento utilizada.")
            return

        ok_piezas, piezas_val = validaciones.entero_positivo(piezas)
        if not ok_piezas:
            messagebox.showwarning("Error", "La cantidad de piezas debe ser un número entero mayor que cero.")
            return

        ok_fil, filamento_val = validaciones.numero_positivo(filamento)
        if not ok_fil:
            messagebox.showwarning("Error", "El peso de filamento (g) debe ser un número mayor que cero.")
            return
        ok_t, _tiempo_float = validaciones.numero_positivo(tiempo)
        if not ok_t:
            messagebox.showwarning("Error", "El tiempo (min) debe ser un número mayor que cero.")
            return
        tiempo_val = int(_tiempo_float)

        if estado == ESTADOS[0]:
            messagebox.showwarning("Error", "Debe seleccionar el estado de la impresión.")
            return

        try:
            id_fab = self.datos.crear_fabricacion(
                id_modelo, id_prod, fecha, piezas_val, filamento_val, tiempo_val, estado)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error al guardar",
                                 f"No se pudo registrar en la base de datos:\n\n{exc}")
            return

        messagebox.showinfo("Impresión Registrada", f"Fabricación #{id_fab} registrada correctamente.")

        self.piezas_entry.delete(0, 'end')
        self.filamento_entry.delete(0, 'end')
        self.tiempo_entry.delete(0, 'end')
        if ctk:
            self.modelo_combo.set("Seleccione modelo...")
            self.prod_combo.set("Seleccione producción...")
            self.estado_combo.set(ESTADOS[0])
        else:
            self.modelo_var.set("Seleccione modelo...")
            self.prod_var.set("Seleccione producción...")
            self.estado_var.set(ESTADOS[0])

        if self.on_register_callback:
            self.on_register_callback()


class RecentImpresionesFrame(ctk.CTkFrame if ctk else tk.Frame):
    def __init__(self, parent, datos=None, fabrica=None, **kwargs):
        self.datos = datos or repositorio
        self.fw = fabrica or FabricaWidgets()
        if ctk:
            super().__init__(parent, fg_color=COLORS["surface_container"], border_color=COLORS["primary_fixed"], border_width=1, corner_radius=12, **kwargs)
        else:
            super().__init__(parent, bg=COLORS["surface_container"], bd=1, relief="solid", **kwargs)
        self.setup_ui()

    def setup_ui(self):
        self.fw.titulo(self, "Historial de Impresiones", pady=(20, 15), padx=20, anchor="w")

        tree_frame = tk.Frame(self, bg=COLORS["surface_container"])
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        tree_scroll = ttk.Scrollbar(tree_frame)
        tree_scroll.pack(side="right", fill="y")

        columnas = [
            ("fecha", "Fecha", 95, "center"),
            ("modelo", "Modelo", 190, "w"),
            ("produccion", "Filamento", 90, "center"),
            ("piezas", "Piezas", 70, "center"),
            ("filamento", "Peso (g)", 90, "center"),
            ("tiempo", "Tiempo (min)", 100, "center"),
            ("estado", "Estado", 100, "center"),
        ]
        self.tree = self.fw.tabla(tree_frame, columnas, "Impr.Treeview", yscrollcommand=tree_scroll.set)
        self.tree.pack(fill="both", expand=True)
        tree_scroll.config(command=self.tree.yview)

        self.recargar()

    def recargar(self):
        """Recarga el historial desde la base de datos."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        try:
            filas = self.datos.fabricaciones_recientes()
        except Exception:  # noqa: BLE001
            return
        for fecha, modelo, cantidad, peso, tiempo, estado, id_prod in filas:
            f = fecha.strftime("%d/%m/%Y") if hasattr(fecha, "strftime") else (str(fecha) if fecha else "")
            peso_txt = f"{float(peso):g}" if peso is not None else ""
            self.tree.insert("", "end", values=(
                f, modelo or "", f"#{id_prod}" if id_prod is not None else "",
                cantidad if cantidad is not None else "", peso_txt,
                tiempo if tiempo is not None else "", estado or ""))


class ImpresionApp:
    PAGE = "impresion"

    def __init__(self, root, on_navigate=None, on_logout=None, datos=None, proyeccion=None, fabrica=None):
        self.root = root
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.datos = datos or repositorio
        self.proyeccion = proyeccion or ServicioProyeccion()
        self.fw = fabrica or FabricaWidgets()
        self.root.title("VorTrack - Impresión")
        self.root.minsize(1024, 700)
        ui_utils.maximize_window(self.root)
        self.root.configure(bg=COLORS["background"])

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_path = ui_utils.ruta_logo("VorTrack icon.png")

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

        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=0, minsize=440)
        self.canvas_frame.grid_columnconfigure(1, weight=1)

        self.form = ImpresionForm(self.canvas_frame, on_register_callback=self.on_new_record,
                                  datos=self.datos, proyeccion=self.proyeccion, fabrica=self.fw)
        self.form.grid(row=0, column=0, sticky="nsew", padx=(0, 20), pady=10)

        self.recent_records = RecentImpresionesFrame(self.canvas_frame, datos=self.datos, fabrica=self.fw)
        self.recent_records.grid(row=0, column=1, sticky="nsew", pady=10)

    def on_new_record(self):
        self.recent_records.recargar()

    # --- Navegación ---
    def ir_a_inicio(self):
        if self.on_navigate:
            self.on_navigate("inicio")

    def ir_a_historico(self):
        if self.on_navigate:
            self.on_navigate("historico")

    def on_registrar_select(self, choice):
        if hasattr(self, "registrar_btn") and ctk:
            self.registrar_btn.set("REGISTRAR ▾")
        destinos = {"Recolección": "recoleccion", "Transformación": "transformacion", "Impresión": "impresion"}
        target = destinos.get(choice)
        if target and target != self.PAGE and self.on_navigate:
            self.on_navigate(target)

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
    ImpresionApp(root)
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
