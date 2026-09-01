"""
contenedor.py
Raíz de composición de VorTrack: construye las dependencias concretas (capa de
datos y servicios) en un único lugar y las expone para inyectarlas en la UI.

Las pantallas reciben `datos` y `proyeccion` por constructor y dependen solo de
su interfaz pública (DIP), no de los módulos globales. `app.py` crea un
Contenedor y reparte estas dependencias a cada página.
"""

import datos.repositorio as repositorio
from servicios.servicio_proyeccion import ServicioProyeccion


class Contenedor:
    """Agrupa las dependencias de la aplicación (datos + servicios)."""

    def __init__(self, datos=None, proyeccion=None):
        # `datos`: fachada de repositorios (misma interfaz pública que repositorio).
        self.datos = datos or repositorio
        # `proyeccion`: servicio de proyecciones/predicciones de producción.
        self.proyeccion = proyeccion or ServicioProyeccion()
