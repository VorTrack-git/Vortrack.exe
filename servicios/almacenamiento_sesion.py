"""
almacenamiento_sesion.py
Persistencia local del identificador "recordado" (autocompletar el login).

Se separa de la autenticación (SRP): guardar/leer un archivo es una
responsabilidad distinta a validar credenciales.
"""

import json
import os


class AlmacenamientoSesion:
    def __init__(self, ruta=None):
        base = os.path.dirname(os.path.abspath(__file__))
        self._ruta = ruta or os.path.join(base, ".vortrack_remember.json")

    def guardar(self, username):
        try:
            with open(self._ruta, "w", encoding="utf-8") as f:
                json.dump({"username": (username or "").strip()}, f, ensure_ascii=False)
        except OSError as exc:
            print(f"No se pudo guardar la sesión recordada: {exc}")

    def limpiar(self):
        try:
            if os.path.exists(self._ruta):
                os.remove(self._ruta)
        except OSError as exc:
            print(f"No se pudo eliminar la sesión recordada: {exc}")

    def cargar(self):
        if not os.path.exists(self._ruta):
            return None
        try:
            with open(self._ruta, encoding="utf-8") as f:
                data = json.load(f)
            username = data.get("username", "").strip()
            return username or None
        except (OSError, json.JSONDecodeError) as exc:
            print(f"No se pudo leer la sesión recordada: {exc}")
            return None
