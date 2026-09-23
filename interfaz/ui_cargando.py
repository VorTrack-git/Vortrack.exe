"""
ui_cargando.py
Indicador de carga (spinner con porcentaje) reutilizable para las pantallas de VorTrack.

Se dibuja con un `tk.Canvas` (anillo de progreso con el % en el centro), así
funciona igual con o sin customtkinter. Se superpone a un contenedor con
`place` y lo tapa mientras llegan los datos; luego se quita con `ocultar()`.
"""

import time
import tkinter as tk
from concurrent.futures import ThreadPoolExecutor

from interfaz.ui_tema import COLORS, FONT_FAMILY

# Tiempo mínimo del spinner en pantalla, para que no parpadee si la base responde muy rápido.
SPINNER_MIN_S = 0.4
SONDEO_MS = 60
# Cuánto se deja ver el 100 % antes de quitar el spinner.
PAUSA_100_MS = 180


class SpinnerCarga:
    TAMANO = 96
    GROSOR = 7
    INTERVALO_MS = 30
    # Suavizado: fracción de la distancia que avanza el % mostrado en cada cuadro.
    AVANCE_REAL = 0.22      # hacia el progreso real (consultas terminadas)
    AVANCE_ESPERA = 0.025   # "arrastre" lento mientras la siguiente consulta sigue en curso

    def __init__(self, parent, texto="Cargando…", detalle="", bg=None):
        bg = bg or COLORS["background"]
        self.frame = tk.Frame(parent, bg=bg)
        caja = tk.Frame(self.frame, bg=bg)
        caja.place(relx=0.5, rely=0.45, anchor="center")

        t, g = self.TAMANO, self.GROSOR
        self._canvas = tk.Canvas(caja, width=t, height=t, bg=bg, highlightthickness=0)
        self._canvas.pack()
        self._canvas.create_oval(g, g, t - g, t - g, outline=COLORS["outline_variant"], width=g)
        self._arco = self._canvas.create_arc(g, g, t - g, t - g, start=90, extent=0,
                                             style="arc", outline=COLORS["primary_fixed"], width=g)
        self._pct = self._canvas.create_text(t / 2, t / 2, text="0%", fill=COLORS["white"],
                                             font=(FONT_FAMILY, 15, "bold"))

        self._texto = tk.Label(caja, text=texto, bg=bg, fg=COLORS["white"],
                               font=(FONT_FAMILY, 13, "bold"))
        self._texto.pack(pady=(14, 2))
        self._detalle = tk.Label(caja, text=detalle, bg=bg, fg=COLORS["on_surface_variant"],
                                 font=(FONT_FAMILY, 10))
        self._detalle.pack()

        self._mostrado = 0.0   # % dibujado (animado)
        self._objetivo = 0.0   # % real: consultas terminadas / total
        self._techo = 0.0      # hasta dónde puede "arrastrarse" mientras espera
        self._job = None

    def mostrar(self):
        """Tapa por completo el contenedor padre y arranca la animación."""
        self.frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.frame.lift()
        self._animar()

    def set_texto(self, texto=None, detalle=None):
        if texto is not None:
            self._texto.configure(text=texto)
        if detalle is not None:
            self._detalle.configure(text=detalle)

    def set_progreso(self, hechas, total):
        """Progreso real. Mientras falten consultas, el % sigue avanzando despacio
        pero sin llegar al siguiente tramo, para que no se vea congelado."""
        self._objetivo = 100.0 * hechas / total if total else 100.0
        if hechas >= total:
            self._techo = 100.0
        else:
            self._techo = self._objetivo + 0.85 * (100.0 / total)

    def completo(self):
        """True cuando el anillo ya muestra el 100 %."""
        return self._mostrado >= 100.0

    def activo(self):
        try:
            return bool(self.frame.winfo_exists())
        except tk.TclError:
            return False

    def ocultar(self):
        if self._job is not None:
            try:
                self.frame.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None
        if self.activo():
            self.frame.destroy()

    def _animar(self):
        if not self.activo():
            return
        if self._mostrado < self._objetivo:
            self._mostrado += max((self._objetivo - self._mostrado) * self.AVANCE_REAL, 1.0)
            self._mostrado = min(self._mostrado, self._objetivo)
        elif self._mostrado < self._techo:
            self._mostrado += (self._techo - self._mostrado) * self.AVANCE_ESPERA
        pct = min(self._mostrado, 100.0)
        # Tk no dibuja un arco de 360° exactos: al 100 % se usa 359.9.
        self._canvas.itemconfigure(self._arco, extent=-min(3.6 * pct, 359.9))
        self._canvas.itemconfigure(self._pct, text=f"{int(pct)}%")
        self._job = self.frame.after(self.INTERVALO_MS, self._animar)


def cargar_con_spinner(contenedor, cargas, al_terminar, titulo="Obteniendo datos…"):
    """Lanza todas las consultas a la vez en hilos y muestra un spinner con % sobre `contenedor`.

    `cargas` es {clave: (funcion, mensaje)}; cada función corre en su propio hilo
    (y abre su propia conexión). El hilo principal sondea con `after`; el % es la
    proporción de consultas terminadas. Cuando terminan todas (y el anillo llega
    al 100 %), quita el spinner y llama `al_terminar(futuros)` con {clave: Future};
    `futuro.result()` devuelve el dato o relanza la excepción.
    Los widgets solo se tocan en el hilo principal (Tkinter no es thread-safe).
    """
    pool = ThreadPoolExecutor(max_workers=len(cargas))
    futuros = {clave: pool.submit(funcion) for clave, (funcion, _) in cargas.items()}
    total = len(futuros)
    spinner = SpinnerCarga(contenedor, texto=titulo, detalle=f"0 de {total} consultas listas")
    spinner.set_progreso(0, total)
    spinner.mostrar()
    inicio = time.perf_counter()

    def terminar():
        if not spinner.activo():
            return
        spinner.ocultar()
        al_terminar(futuros)

    def sondear():
        if not spinner.activo():  # la página se cerró mientras cargaba
            pool.shutdown(wait=False)
            return
        pendientes = [clave for clave, f in futuros.items() if not f.done()]
        hechas = total - len(pendientes)
        spinner.set_progreso(hechas, total)
        if pendientes:
            spinner.set_texto(cargas[pendientes[0]][1], f"{hechas} de {total} consultas listas")
        else:
            spinner.set_texto("¡Listo!", f"{total} de {total} consultas listas")
        if pendientes or not spinner.completo() or time.perf_counter() - inicio < SPINNER_MIN_S:
            spinner.frame.after(SONDEO_MS, sondear)
            return
        pool.shutdown(wait=False)
        spinner.frame.after(PAUSA_100_MS, terminar)

    sondear()
    return futuros


def ejecutar_con_spinner(contenedor, tarea, al_terminar, titulo="Procesando…"):
    """Corre `tarea(reportar)` en un hilo con el spinner encima de `contenedor`.

    La tarea avisa su avance llamando `reportar(hechos, total, texto)` (desde su
    hilo: solo se guarda el dato, el hilo principal lo lee al sondear). Al
    terminar, quita el spinner y llama `al_terminar(futuro)`; `futuro.result()`
    devuelve lo que retornó la tarea o relanza su excepción.
    """
    estado = {"hechos": 0, "total": 1, "texto": titulo}

    def reportar(hechos, total, texto=None):
        estado.update(hechos=hechos, total=total, texto=texto or estado["texto"])

    pool = ThreadPoolExecutor(max_workers=1)
    futuro = pool.submit(tarea, reportar)
    spinner = SpinnerCarga(contenedor, texto=titulo, detalle="")
    spinner.set_progreso(0, 1)
    spinner.mostrar()
    inicio = time.perf_counter()

    def terminar():
        if spinner.activo():
            spinner.ocultar()
            al_terminar(futuro)

    def sondear():
        if not spinner.activo():  # la página se cerró mientras trabajaba
            pool.shutdown(wait=False)
            return
        listo = futuro.done()
        total = estado["total"]
        hechos = total if listo else estado["hechos"]
        spinner.set_progreso(hechos, total)
        spinner.set_texto(estado["texto"], "" if listo else f"Paso {min(hechos + 1, total)} de {total}")
        if not listo or not spinner.completo() or time.perf_counter() - inicio < SPINNER_MIN_S:
            spinner.frame.after(SONDEO_MS, sondear)
            return
        pool.shutdown(wait=False)
        spinner.frame.after(PAUSA_100_MS, terminar)

    sondear()
    return futuro


def resultado(precarga, clave, funcion):
    """Dato precargado en `precarga[clave]` (Future) o, si no hay, lo consulta en el momento.

    Así los formularios siguen funcionando solos (sin spinner) y con la precarga
    paralela; en ambos casos una falla de la base se relanza igual.
    """
    if precarga and clave in precarga:
        return precarga[clave].result()
    return funcion()
