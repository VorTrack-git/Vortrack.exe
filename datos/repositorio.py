"""
repositorio.py
Fachada de compatibilidad de la capa de datos de VorTrack.

La lógica real vive ahora en repositorios por entidad (repo_*.py). Este módulo
conserva las funciones que usa el resto del código y delega en las clases, para
migrar a la nueva estructura sin romper nada. La cadena de trazabilidad es:

    Lugar + Responsable -> JornadaRecoleccion -> ProduccionFilamento
                                              -> FabricacionObjetos (Modelo)
"""

from datos.repositorio_base import parse_fecha  # noqa: F401  (re-exportado)
from datos.repo_catalogos import RepoLugares, RepoModelos, RepoResponsables
from datos.repo_jornadas import RepoJornadas
from datos.repo_produccion import RepoProduccion
from datos.repo_fabricacion import RepoFabricacion
from datos.repo_usuarios import RepoUsuarios
from datos.repo_indicadores import RepoIndicadores

_lugares = RepoLugares()
_modelos = RepoModelos()
_responsables = RepoResponsables()
_jornadas = RepoJornadas()
_produccion = RepoProduccion()
_fabricacion = RepoFabricacion()
_usuarios = RepoUsuarios()
_indicadores = RepoIndicadores()


# --- Catálogos ---
def listar_responsables():
    return _responsables.listar()


def listar_lugares():
    return _lugares.listar()


def listar_modelos():
    return _modelos.listar()


def listar_jornadas():
    return _jornadas.listar_para_combo()


def listar_producciones():
    return _produccion.listar_para_combo()


def peso_pet_jornada(id_jornada):
    return _jornadas.peso_pet(id_jornada)


# --- Recolección ---
def crear_jornada(fecha, id_lugar, id_responsable, cantidad_botellas, peso_pet, observaciones):
    return _jornadas.crear(fecha, id_lugar, id_responsable, cantidad_botellas, peso_pet, observaciones)


def recolecciones_recientes(limite=50):
    return _jornadas.recientes(limite)


# --- Transformación ---
def crear_produccion(id_jornada, fecha, color, diametro, peso_obtenido, metros, observaciones):
    return _produccion.crear(id_jornada, fecha, color, diametro, peso_obtenido, metros, observaciones)


def producciones_recientes(limite=50):
    return _produccion.recientes(limite)


# --- Impresión ---
def crear_fabricacion(id_modelo, id_produccion, fecha, cantidad, peso_utilizado, tiempo_min, estado):
    return _fabricacion.crear(id_modelo, id_produccion, fecha, cantidad, peso_utilizado, tiempo_min, estado)


def fabricaciones_recientes(limite=50):
    return _fabricacion.recientes(limite)


# --- Indicadores ---
def indicadores_resumen():
    return _indicadores.resumen()


def ranking_participacion(limite=10):
    return _indicadores.ranking(limite)


# --- Estudiantes ---
def listar_estudiantes():
    return _usuarios.listar_estudiantes()


def crear_estudiante(nombres, apellidos, correo, telefono, contrasena):
    return _usuarios.crear_estudiante(nombres, apellidos, correo, telefono, contrasena)


def actualizar_estudiante(id_usuario, nombres, apellidos, correo, telefono, contrasena, estado):
    return _usuarios.actualizar_estudiante(id_usuario, nombres, apellidos, correo, telefono, contrasena, estado)


def eliminar_estudiante(id_usuario):
    return _usuarios.eliminar_estudiante(id_usuario)


# --- Admin: Recolecciones ---
def recolecciones_admin(limite=300):
    return _jornadas.listar_admin(limite)


def obtener_jornada(id_jornada):
    return _jornadas.obtener(id_jornada)


def actualizar_jornada(id_jornada, fecha, id_lugar, id_responsable, botellas, peso, obs):
    return _jornadas.actualizar(id_jornada, fecha, id_lugar, id_responsable, botellas, peso, obs)


def eliminar_jornada(id_jornada):
    return _jornadas.eliminar(id_jornada)


# --- Admin: Transformaciones ---
def producciones_admin(limite=300):
    return _produccion.listar_admin(limite)


def obtener_produccion(id_produccion):
    return _produccion.obtener(id_produccion)


def actualizar_produccion(id_produccion, id_jornada, fecha, color, diametro, peso_obtenido, metros, obs):
    return _produccion.actualizar(id_produccion, id_jornada, fecha, color, diametro, peso_obtenido, metros, obs)


def eliminar_produccion(id_produccion):
    return _produccion.eliminar(id_produccion)


# --- Admin: Impresiones ---
def fabricaciones_admin(limite=300):
    return _fabricacion.listar_admin(limite)


def obtener_fabricacion(id_fab):
    return _fabricacion.obtener(id_fab)


def actualizar_fabricacion(id_fab, id_modelo, id_produccion, fecha, cantidad, peso, tiempo, estado):
    return _fabricacion.actualizar(id_fab, id_modelo, id_produccion, fecha, cantidad, peso, tiempo, estado)


def eliminar_fabricacion(id_fab):
    return _fabricacion.eliminar(id_fab)


# --- Admin: Lugares ---
def listar_lugares_admin():
    return _lugares.listar_admin()


def crear_lugar(nombre, descripcion):
    return _lugares.crear(nombre, descripcion)


def actualizar_lugar(id_lugar, nombre, descripcion):
    return _lugares.actualizar(id_lugar, nombre, descripcion)


def eliminar_lugar(id_lugar):
    return _lugares.eliminar(id_lugar)


# --- Admin: Modelos ---
def listar_modelos_admin():
    return _modelos.listar_admin()


def crear_modelo(nombre, categoria, tiempo_estimado, peso_estimado):
    return _modelos.crear(nombre, categoria, tiempo_estimado, peso_estimado)


def actualizar_modelo(id_modelo, nombre, categoria, tiempo_estimado, peso_estimado):
    return _modelos.actualizar(id_modelo, nombre, categoria, tiempo_estimado, peso_estimado)


def eliminar_modelo(id_modelo):
    return _modelos.eliminar(id_modelo)
