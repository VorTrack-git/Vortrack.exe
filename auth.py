"""Autenticación de VorTrack contra la base de datos (tabla Usuarios)."""

import hashlib
import json
import os
from typing import Optional

import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REMEMBER_FILE = os.path.join(BASE_DIR, ".vortrack_remember.json")

_session: Optional[dict] = None


class DatabaseUnavailable(Exception):
    """La base de datos no está accesible (config, red o driver)."""


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _password_matches(entrada: str, almacenada) -> bool:
    """Acepta contraseñas hasheadas (admin) o en texto plano (estudiantes)."""
    if almacenada is None:
        return False
    guardada = str(almacenada)
    es_hash = len(guardada) == 64 and all(c in "0123456789abcdefABCDEF" for c in guardada)
    if es_hash:
        return guardada.lower() == _hash_password(entrada).lower()
    return guardada == entrada


def is_admin() -> bool:
    """True si la sesión activa pertenece a un administrador."""
    return bool(_session) and _session.get("rol") == "Administrador"


def authenticate(username: str, password: str) -> bool:
    """Valida credenciales contra la tabla Usuarios y abre sesión si son correctas."""
    global _session

    user = username.strip()
    pwd = password

    if not user or not pwd:
        return False

    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT u.IdUsuario, u.Nombres, u.Apellidos, u.Usuario, u.Contrasena, "
            "u.IdRol, r.Nombre AS Rol "
            "FROM Usuarios u LEFT JOIN Roles r ON u.IdRol = r.IdRol "
            "WHERE u.Usuario = ? AND u.Estado = 'Activo'",
            user,
        )
        row = cursor.fetchone()
        conn.close()
    except Exception as exc:  # noqa: BLE001
        _session = None
        # Se propaga para que la UI muestre el error real (no "credenciales incorrectas").
        raise DatabaseUnavailable(str(exc)) from exc

    if row is None or not _password_matches(pwd, row.Contrasena):
        _session = None
        return False

    _session = {
        "id": row.IdUsuario,
        "username": row.Usuario,
        "nombres": row.Nombres,
        "apellidos": row.Apellidos,
        "id_rol": row.IdRol,
        "rol": row.Rol,
    }
    return True


def logout() -> None:
    """Cierra la sesión activa."""
    global _session
    _session = None


def is_authenticated() -> bool:
    return _session is not None


def get_current_user() -> Optional[dict]:
    return _session.copy() if _session else None


def require_auth() -> dict:
    """Exige sesión activa; lanza RuntimeError si no hay usuario autenticado."""
    user = get_current_user()
    if user is None:
        raise RuntimeError("Debe iniciar sesión para acceder a VorTrack.")
    return user


def save_remembered_user(username: str) -> None:
    """Guarda el identificador para autocompletar en el próximo inicio."""
    try:
        with open(REMEMBER_FILE, "w", encoding="utf-8") as f:
            json.dump({"username": username.strip()}, f, ensure_ascii=False)
    except OSError as exc:
        print(f"No se pudo guardar la sesión recordada: {exc}")


def clear_remembered_user() -> None:
    """Elimina el identificador guardado."""
    try:
        if os.path.exists(REMEMBER_FILE):
            os.remove(REMEMBER_FILE)
    except OSError as exc:
        print(f"No se pudo eliminar la sesión recordada: {exc}")


def load_remembered_user() -> Optional[str]:
    """Devuelve el identificador guardado, si existe."""
    if not os.path.exists(REMEMBER_FILE):
        return None

    try:
        with open(REMEMBER_FILE, encoding="utf-8") as f:
            data = json.load(f)
        username = data.get("username", "").strip()
        return username or None
    except (OSError, json.JSONDecodeError) as exc:
        print(f"No se pudo leer la sesión recordada: {exc}")
        return None
