"""
ui_desplegable.py
Menú desplegable animado de la barra de navegación (p. ej. "REGISTRAR").

Una sola etiqueta con una flecha (chevron) dibujada en un Canvas: al abrir, la
flecha gira hacia arriba y el panel de opciones se desliza hacia abajo; al
cerrar, el movimiento se invierte. Se cierra también al elegir una opción, al
hacer clic fuera o con Escape. Está hecho con widgets tk, así que se ve y
funciona igual con o sin customtkinter.
"""

import math
import tkinter as tk

from interfaz.ui_tema import COLORS, FONT_FAMILY


def _ease_out(t):
    return 1 - (1 - t) ** 3


class MenuDesplegable:
    DURACION_MS = 200
    CUADRO_MS = 15
    SEPARACION = 8        # px entre el botón y el panel
    ANCHO_MIN = 190

    def __init__(self, parent, texto, opciones, on_select, activo=None, font_size=10):
        """`opciones`: lista de etiquetas; `on_select(etiqueta)` al elegir una;
        `activo`: etiqueta de la página actual (se resalta en el panel)."""
        c = COLORS
        self._on_select = on_select
        self._bg = c["surface_container"]
        self._bg_hover = c["surface_bright"]
        self._fg = c["on_surface_variant"]
        self._fg_on = c["primary_fixed"]
        self._progreso = 0.0   # 0 = cerrado, 1 = abierto
        self._destino = 0.0
        self._job = None
        self._hover = False
        self._al_cerrar = None  # acción pendiente al terminar de cerrarse (p. ej. navegar)

        # --- Botón: texto + chevron ---
        self.boton = tk.Frame(parent, bg=self._bg, cursor="hand2", padx=12, pady=6)
        self._lbl = tk.Label(self.boton, text=texto, bg=self._bg, fg=self._fg,
                             font=(FONT_FAMILY, font_size, "bold"), cursor="hand2")
        self._lbl.pack(side="left")
        self._flecha = tk.Canvas(self.boton, width=16, height=16, bg=self._bg,
                                 highlightthickness=0, cursor="hand2")
        self._flecha.pack(side="left", padx=(6, 0))
        self._chevron = self._flecha.create_line(0, 0, 0, 0, fill=self._fg, width=2,
                                                 capstyle="round", joinstyle="round")
        self._dibujar_flecha()

        for w in (self.boton, self._lbl, self._flecha):
            w.bind("<Button-1>", lambda _e: self.alternar())
            w.bind("<Enter>", lambda _e: self._set_hover(True))
            w.bind("<Leave>", lambda _e: self._set_hover(False))

        # --- Panel: marco con borde (clip) + contenido que se desliza dentro ---
        self._top = parent.winfo_toplevel()
        self.panel = tk.Frame(self._top, bg=c["outline_variant"])
        self._contenido = tk.Frame(self.panel, bg=self._bg)
        for etiqueta in opciones:
            self._crear_opcion(etiqueta, etiqueta == activo, font_size)

        self._top.bind("<Button-1>", self._clic_fuera, add="+")
        self._top.bind("<Escape>", lambda _e: self.cerrar(), add="+")
        self._top.bind("<Configure>", lambda _e: self._reubicar(), add="+")

    def pack(self, **kwargs):
        self.boton.pack(**kwargs)

    # --- API ---
    def abierto(self):
        return self._destino == 1.0

    def alternar(self):
        self.cerrar() if self.abierto() else self.abrir()

    def abrir(self):
        self._destino = 1.0
        self._reubicar()
        self.panel.lift()
        self._animar()

    def cerrar(self, despues=None):
        if self._destino == 0.0 and self._progreso == 0.0:
            if despues:
                despues()
            return
        self._destino = 0.0
        self._al_cerrar = despues
        self._animar()

    # --- Internos ---
    def _crear_opcion(self, etiqueta, es_activa, font_size):
        fila = tk.Frame(self._contenido, bg=self._bg, cursor="hand2")
        fila.pack(fill="x")
        acento = tk.Frame(fila, bg=self._fg_on if es_activa else self._bg, width=3)
        acento.pack(side="left", fill="y")
        lbl = tk.Label(fila, text=etiqueta, bg=self._bg, anchor="w", cursor="hand2",
                       fg=self._fg_on if es_activa else COLORS["on_surface"],
                       font=(FONT_FAMILY, font_size, "bold" if es_activa else "normal"),
                       padx=16, pady=9)
        lbl.pack(side="left", fill="x", expand=True)

        def hover(dentro):
            color = self._bg_hover if dentro else self._bg
            fila.configure(bg=color)
            lbl.configure(bg=color, fg=self._fg_on if (dentro or es_activa) else COLORS["on_surface"])
            if not es_activa:
                acento.configure(bg=color)

        def elegir(_e=None):
            self.cerrar(despues=lambda: self._on_select(etiqueta))

        for w in (fila, lbl, acento):
            w.bind("<Enter>", lambda _e: hover(True))
            w.bind("<Leave>", lambda _e: hover(False))
            w.bind("<Button-1>", elegir)

    def _set_hover(self, dentro):
        self._hover = dentro
        self._pintar_boton()

    def _pintar_boton(self):
        resaltado = self._hover or self._progreso > 0
        bg = self._bg_hover if self._hover else self._bg
        fg = self._fg_on if resaltado else self._fg
        for w in (self.boton, self._lbl, self._flecha):
            w.configure(bg=bg)
        self._lbl.configure(fg=fg)
        self._flecha.itemconfigure(self._chevron, fill=fg)

    def _dibujar_flecha(self):
        """Chevron '⌄' rotado 0°→180° según el progreso (abajo → arriba)."""
        ang = math.pi * _ease_out(self._progreso)
        cx, cy = 8, 8
        coords = []
        for x, y in ((-4.5, -2.2), (0, 2.3), (4.5, -2.2)):
            coords += [cx + x * math.cos(ang) - y * math.sin(ang),
                       cy + x * math.sin(ang) + y * math.cos(ang)]
        self._flecha.coords(self._chevron, *coords)

    def _medidas(self):
        self._contenido.update_idletasks()
        ancho = max(self._contenido.winfo_reqwidth(), self.boton.winfo_width(), self.ANCHO_MIN) + 2
        alto = self._contenido.winfo_reqheight() + 2
        return ancho, alto

    def _reubicar(self):
        if self._progreso == 0 and self._destino == 0:
            return
        try:
            x = self.boton.winfo_rootx() - self._top.winfo_rootx()
            y = self.boton.winfo_rooty() - self._top.winfo_rooty() + self.boton.winfo_height() + self.SEPARACION
        except tk.TclError:
            return
        ancho, alto = self._medidas()
        visible = max(int(alto * _ease_out(self._progreso)), 1)
        self.panel.place(x=x, y=y, width=ancho, height=visible)
        # El contenido baja junto con el borde inferior (efecto de deslizamiento).
        self._contenido.place(x=1, y=visible - alto + 1, width=ancho - 2, height=alto - 2)

    def _animar(self):
        if self._job is not None:
            return
        self._paso()

    def _paso(self):
        self._job = None
        try:
            if not self.boton.winfo_exists():
                return
        except tk.TclError:
            return
        delta = self.CUADRO_MS / self.DURACION_MS
        if self._progreso < self._destino:
            self._progreso = min(self._progreso + delta, 1.0)
        elif self._progreso > self._destino:
            self._progreso = max(self._progreso - delta, 0.0)

        self._dibujar_flecha()
        self._pintar_boton()
        if self._progreso > 0:
            self._reubicar()
        else:
            self.panel.place_forget()

        if self._progreso != self._destino:
            self._job = self.boton.after(self.CUADRO_MS, self._paso)
        elif self._progreso == 0:
            despues, self._al_cerrar = self._al_cerrar, None
            if despues:
                despues()

    def _clic_fuera(self, event):
        if not self.abierto():
            return
        ruta = str(event.widget)
        for w in (self.boton, self.panel):
            if ruta == str(w) or ruta.startswith(str(w) + "."):
                return
        self.cerrar()
