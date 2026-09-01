"""
servicio_auth.py
Servicio de autenticación de VorTrack: login, sesión y roles.

Depende de un repositorio de usuarios (abstracción `RepoUsuariosProto`) y de un
almacenamiento para el "recordar usuario", ambos inyectables (DIP). Acepta
contraseñas hasheadas (admin) o en texto plano (estudiantes).
"""

import hashlib
from typing import Optional

from datos.repo_usuarios import RepoUsuarios
from servicios.almacenamiento_sesion import AlmacenamientoSesion


class DatabaseUnavailable(Exception):
    """La base de datos no está accesible (config, red o driver)."""


class ServicioAuth:
    def __init__(self, repo_usuarios=None, almacenamiento=None):
        self._repo = repo_usuarios or RepoUsuarios()
        self._recordado = almacenamiento or AlmacenamientoSesion()
        self._session: Optional[dict] = None

    @staticmethod
    def _hash(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _password_matches(self, entrada, almacenada) -> bool:
        if almacenada is None:
            return False
        guardada = str(almacenada)
        es_hash = len(guardada) == 64 and all(c in "0123456789abcdefABCDEF" for c in guardada)
        if es_hash:
            return guardada.lower() == self._hash(entrada).lower()
        return guardada == entrada

    # --- sesión ---
    def autenticar(self, username: str, password: str) -> bool:
        user = (username or "").strip()
        pwd = password
        if not user or not pwd:
            return False
        try:
            row = self._repo.buscar_para_login(user)
        except Exception as exc:  # noqa: BLE001
            self._session = None
            raise DatabaseUnavailable(str(exc)) from exc
        if row is None or not self._password_matches(pwd, row.Contrasena):
            self._session = None
            return False
        self._session = {
            "id": row.IdUsuario,
            "username": row.Usuario,
            "nombres": row.Nombres,
            "apellidos": row.Apellidos,
            "id_rol": row.IdRol,
            "rol": row.Rol,
        }
        return True

    def logout(self) -> None:
        self._session = None

    def autenticado(self) -> bool:
        return self._session is not None

    def es_admin(self) -> bool:
        return bool(self._session) and self._session.get("rol") == "Administrador"

    def usuario_actual(self) -> Optional[dict]:
        return self._session.copy() if self._session else None

    def requerir_auth(self) -> dict:
        u = self.usuario_actual()
        if u is None:
            raise RuntimeError("Debe iniciar sesión para acceder a VorTrack.")
        return u

    # --- recordar usuario ---
    def recordar_usuario(self, username: str) -> None:
        self._recordado.guardar(username)

    def olvidar_usuario(self) -> None:
        self._recordado.limpiar()

    def cargar_recordado(self) -> Optional[str]:
        return self._recordado.cargar()
