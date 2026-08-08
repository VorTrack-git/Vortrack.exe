"""Autenticación local para VorTrack."""

import hashlib
import json
import os
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REMEMBER_FILE = os.path.join(BASE_DIR, ".vortrack_remember.json")

# Usuario demo hasta conectar una base de datos real.
_USERS = {
    "vortrack.soporte@gmail.com": hashlib.sha256("12345678".encode("utf-8")).hexdigest(),
}

_session: Optional[dict] = None


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def authenticate(username: str, password: str) -> bool:
    """Valida credenciales y abre sesión si son correctas."""
    global _session

    user = username.strip()
    pwd = password

    if not user or not pwd:
        return False

    stored_hash = _USERS.get(user)
    if stored_hash is None or stored_hash != _hash_password(pwd):
        _session = None
        return False

    _session = {"username": user}
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
