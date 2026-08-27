"""
validaciones.py
Validadores reutilizables para los formularios.

Centraliza las reglas que hoy están repetidas dentro de cada `registrar()`
(número > 0, entero, fecha, correo, requerido). Devuelven tuplas
(ok, valor) o booleanos, sin tocar la interfaz.
"""

from datetime import datetime


def es_vacio(texto) -> bool:
    return not (texto or "").strip()


def numero(texto):
    """(ok, float). ok=False si no es un número válido."""
    try:
        return True, float(str(texto).strip())
    except (TypeError, ValueError):
        return False, None


def numero_positivo(texto):
    """(ok, float). ok=False si no es un número > 0."""
    ok, valor = numero(texto)
    return (ok and valor > 0), valor


def entero_positivo(texto):
    """(ok, int). ok=False si no es un entero > 0."""
    try:
        valor = int(float(str(texto).strip()))
    except (TypeError, ValueError):
        return False, None
    return (valor > 0), valor


def fecha_valida(texto) -> bool:
    t = (texto or "").strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            datetime.strptime(t, fmt)
            return True
        except ValueError:
            continue
    return False


def correo_valido(texto) -> bool:
    t = (texto or "").strip()
    return "@" in t and "." in t.split("@")[-1] and 0 < len(t) <= 100
