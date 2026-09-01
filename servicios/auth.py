"""
auth.py
Fachada de autenticación de VorTrack.

La lógica vive ahora en `servicio_auth.ServicioAuth`. Este módulo mantiene la
API que usa el resto del código (login, sesión, roles, recordar usuario) y
delega en una única instancia del servicio, para no cambiar los llamadores.
"""

from typing import Optional

from servicios.servicio_auth import ServicioAuth, DatabaseUnavailable  # noqa: F401  (re-exportado)

_servicio = ServicioAuth()


def authenticate(username: str, password: str) -> bool:
    return _servicio.autenticar(username, password)


def logout() -> None:
    _servicio.logout()


def is_authenticated() -> bool:
    return _servicio.autenticado()


def is_admin() -> bool:
    return _servicio.es_admin()


def get_current_user() -> Optional[dict]:
    return _servicio.usuario_actual()


def require_auth() -> dict:
    return _servicio.requerir_auth()


def save_remembered_user(username: str) -> None:
    _servicio.recordar_usuario(username)


def clear_remembered_user() -> None:
    _servicio.olvidar_usuario()


def load_remembered_user() -> Optional[str]:
    return _servicio.cargar_recordado()
