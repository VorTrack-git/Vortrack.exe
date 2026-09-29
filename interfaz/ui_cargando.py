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

# Tiempo mínimo del spinner en pantalla (una vez que aparece), para que no parpadee.
SPINNER_MIN_S = 0.35
SONDEO_MS = 50
# Mientras el spinner aún no aparece se sondea más seguido, para terminar apenas llegue el dato.
SONDEO_OCULTO_MS = 20
# Si una tarea sobre contenido ya visible tarda menos que esto, ni siquiera se muestra el spinner.
RETARDO_S = 0.15
# Cuánto se deja ver el 100 % antes de quitar el spinner.
PAUSA_100_MS = 120


class SpinnerCarga:
    TAMANO = 96
    GROSOR = 7
    INTERVALO_MS = 30
    # Suavizado: fracción de la distancia que avanza el % mostrado en cada cuadro.
    AVANCE_REAL = 0.22      # hacia el progreso real (consultas terminadas)
    AVANCE_FINAL = 0.4      # tramo final, cuando ya terminó todo
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
            # Con todo listo se cierra el anillo más rápido: el dato ya llegó, no hay que hacer esperar.
            avance, minimo = (self.AVANCE_FINAL, 4.0) if self._objetivo >= 100.0 else (self.AVANCE_REAL, 1.0)
            self._mostrado += max((self._objetivo - self._mostrado) * avance, minimo)
            self._mostrado = min(self._mostrado, self._objetivo)
        elif self._mostrado < self._techo:
            self._mostrado += (self._techo - self._mostrado) * self.AVANCE_ESPERA
        pct = min(self._mostrado, 100.0)
        # Tk no dibuja un arco de 360° exactos: al 100 % se usa 359.9.
        self._canvas.itemconfigure(self._arco, extent=-min(3.6 * pct, 359.9))
        self._canvas.itemconfigure(self._pct, text=f"{int(pct)}%")
        self._job = self.frame.after(self.INTERVALO_MS, self._animar)


def _vigilar(spinner, pool, progreso, al_listo, retardo_s):
    """Bucle de sondeo común a `cargar_con_spinner` y `ejecutar_con_spinner`.

    `progreso()` devuelve (hechas, total, texto, detalle) y se llama en el hilo
    principal. El spinner solo aparece si el trabajo tarda más de `retardo_s`:
    si la base responde antes, se termina directo y no hay parpadeo. Una vez
    visible, se mantiene al menos SPINNER_MIN_S y llega al 100 % antes de irse.
    """
    inicio = time.perf_counter()
    visible_desde = None

    def terminar():
        if spinner.activo():
            spinner.ocultar()
            al_listo()

    def sondear():
        nonlocal visible_desde
        if not spinner.activo():  # la página/sección se cerró mientras trabajaba
            pool.shutdown(wait=False)
            return
        hechas, total, texto, detalle = progreso()
        listo = hechas >= total
        ahora = time.perf_counter()
        if visible_desde is None:
            if listo:  # respondió antes del retardo: sin spinner
                pool.shutdown(wait=False)
                terminar()
                return
            if ahora - inicio >= retardo_s:
                spinner.mostrar()
                visible_desde = ahora
        spinner.set_progreso(hechas, total)
        spinner.set_texto(texto, detalle)
        if visible_desde is None or not listo or not spinner.completo() \
                or ahora - visible_desde < SPINNER_MIN_S:
            spinner.frame.after(SONDEO_MS if visible_desde is not None else SONDEO_OCULTO_MS, sondear)
            return
        pool.shutdown(wait=False)
        spinner.frame.after(PAUSA_100_MS, terminar)

    sondear()


def cargar_con_spinner(contenedor, cargas, al_terminar, titulo="Obteniendo datos…", retardo_s=0.0):
    """Lanza todas las consultas a la vez en hilos y muestra un spinner con % sobre `contenedor`.

    `cargas` es {clave: (funcion, mensaje)}; cada función corre en su propio hilo
    (y abre su propia conexión). El hilo principal sondea con `after`; el % es la
    proporción de consultas terminadas. Cuando terminan todas (y el anillo llega
    al 100 %), quita el spinner y llama `al_terminar(futuros)` con {clave: Future};
    `futuro.result()` devuelve el dato o relanza la excepción.
    Con `retardo_s` > 0 el spinner solo aparece si la carga tarda más que eso
    (útil al refrescar algo que ya está en pantalla).
    Los widgets solo se tocan en el hilo principal (Tkinter no es thread-safe).
    """
    pool = ThreadPoolExecutor(max_workers=len(cargas))
    futuros = {clave: pool.submit(funcion) for clave, (funcion, _) in cargas.items()}
    total = len(futuros)
    spinner = SpinnerCarga(contenedor, texto=titulo, detalle=f"0 de {total} consultas listas")
    spinner.set_progreso(0, total)
    if retardo_s <= 0:
        spinner.mostrar()

    def progreso():
        pendientes = [clave for clave, f in futuros.items() if not f.done()]
        hechas = total - len(pendientes)
        if pendientes:
            return hechas, total, cargas[pendientes[0]][1], f"{hechas} de {total} consultas listas"
        return total, total, "¡Listo!", f"{total} de {total} consultas listas"

    _vigilar(spinner, pool, progreso, lambda: al_terminar(futuros), max(retardo_s, 0.0))
    return futuros


def ejecutar_con_spinner(contenedor, tarea, al_terminar, titulo="Procesando…", retardo_s=RETARDO_S):
    """Corre `tarea(reportar)` en un hilo con el spinner encima de `contenedor`.

    La tarea avisa su avance llamando `reportar(hechos, total, texto)` (desde su
    hilo: solo se guarda el dato, el hilo principal lo lee al sondear). Al
    terminar, quita el spinner y llama `al_terminar(futuro)`; `futuro.result()`
    devuelve lo que retornó la tarea o relanza su excepción. Por defecto el
    spinner solo aparece si la tarea tarda más de RETARDO_S.
    """
    estado = {"hechos": 0, "total": 1, "texto": titulo}

    def reportar(hechos, total, texto=None):
        estado.update(hechos=hechos, total=total, texto=texto or estado["texto"])

    pool = ThreadPoolExecutor(max_workers=1)
    futuro = pool.submit(tarea, reportar)
    spinner = SpinnerCarga(contenedor, texto=titulo, detalle="")
    spinner.set_progreso(0, 1)
    if retardo_s <= 0:
        spinner.mostrar()

    def progreso():
        total = max(estado["total"], 1)
        if futuro.done():
            return total, total, estado["texto"], ""
        hechos = min(estado["hechos"], total - 1)  # hasta que el hilo termine no es el 100 %
        return hechos, total, estado["texto"], f"Paso {hechos + 1} de {total}"

    _vigilar(spinner, pool, progreso, lambda: al_terminar(futuro), max(retardo_s, 0.0))
    return futuro


def resultado(precarga, clave, funcion):
    """Dato precargado en `precarga[clave]` (Future) o, si no hay, lo consulta en el momento.

    Así los formularios siguen funcionando solos (sin spinner) y con la precarga
    paralela; en ambos casos una falla de la base se relanza igual.
    """
    if precarga and clave in precarga:
        return precarga[clave].result()
    return funcion()
