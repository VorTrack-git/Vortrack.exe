"""
repositorio_base.py
Base común de los repositorios de VorTrack.

`RepositorioBase` recibe una fábrica de conexión (por defecto db.get_connection),
lo que invierte la dependencia hacia la infraestructura (DIP) y facilita las
pruebas. Provee los helpers de consulta/ejecución que antes vivían privados en
`repositorio.py`.
"""

from datetime import date, datetime

import datos.db as db


class RepositorioBase:
    def __init__(self, conexion_factory=None):
        self._conexion = conexion_factory or db.get_connection

    def _abrir(self):
        """Abre una conexión (para operaciones de varias sentencias)."""
        return self._conexion()

    def _query(self, sql, params=(), fetch="all"):
        conn = self._conexion()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            if fetch == "all":
                return cur.fetchall()
            if fetch == "one":
                return cur.fetchone()
            return None
        finally:
            conn.close()

    def _ejecutar(self, sql, params=(), return_id=False):
        conn = self._conexion()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            new_id = cur.fetchone()[0] if return_id else None
            conn.commit()
            return new_id
        finally:
            conn.close()

    def _valor(self, sql):
        """Devuelve el primer valor de una consulta escalar como float (0 si null)."""
        row = self._query(sql, fetch="one")
        v = row[0] if row else 0
        return float(v) if v is not None else 0.0


def es_error_duplicado(exc):
    """True si la excepción de la base es una violación de clave única (nombre repetido)."""
    texto = " ".join(str(a) for a in getattr(exc, "args", ())) or str(exc)
    texto = texto.upper()
    return "2627" in texto or "2601" in texto or "UNIQUE KEY" in texto or "UNIQUE CONSTRAINT" in texto


def parse_fecha(valor):
    """Convierte la fecha del formulario (str dd/mm/aaaa o date) a datetime.date."""
    if isinstance(valor, (date, datetime)):
        return valor if isinstance(valor, date) else valor.date()
    texto = str(valor).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    return date.today()
