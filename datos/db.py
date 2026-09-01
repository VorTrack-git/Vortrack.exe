"""
Conexión a SQL Server para VorTrack (pyodbc, autenticación SQL).

La configuración (servidor, base, usuario y CONTRASEÑA) se lee de un archivo
local `db_config.ini` que NO se versiona, o de variables de entorno
VORTRACK_DB_* (que tienen prioridad). Así las credenciales nunca quedan en el
código ni en el repositorio.
"""

import os
import configparser

try:
    import pyodbc
except ImportError:  # pragma: no cover
    pyodbc = None

# db.py vive en datos/; el db_config.ini está en la raíz del repo (un nivel arriba).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(BASE_DIR)
CONFIG_FILE = os.path.join(RAIZ, "db_config.ini")

# Valores por defecto (los sensibles quedan vacíos a propósito).
DEFAULTS = {
    "driver": "ODBC Driver 18 for SQL Server",
    "server": "",
    "port": "1433",
    "database": "vortrack_db",
    "username": "",
    "password": "",
    "encrypt": "yes",
    "trust_server_certificate": "yes",
}


def _load_settings():
    cfg = dict(DEFAULTS)
    if os.path.exists(CONFIG_FILE):
        parser = configparser.ConfigParser()
        parser.read(CONFIG_FILE, encoding="utf-8")
        if parser.has_section("database"):
            for key in cfg:
                if parser.has_option("database", key):
                    cfg[key] = parser.get("database", key).strip()
    # Las variables de entorno sobrescriben el archivo.
    for key in cfg:
        env = os.environ.get("VORTRACK_DB_" + key.upper())
        if env:
            cfg[key] = env
    return cfg


def _connection_string(cfg):
    server = cfg["server"]
    if cfg.get("port"):
        server = f"{server},{cfg['port']}"
    return (
        f"DRIVER={{{cfg['driver']}}};"
        f"SERVER={server};"
        f"DATABASE={cfg['database']};"
        f"UID={cfg['username']};"
        f"PWD={cfg['password']};"
        f"Encrypt={cfg['encrypt']};"
        f"TrustServerCertificate={cfg['trust_server_certificate']};"
    )


def get_connection():
    """Abre y devuelve una conexión pyodbc. Lanza RuntimeError si falta config."""
    if pyodbc is None:
        raise RuntimeError("Falta instalar pyodbc:  pip install pyodbc")

    cfg = _load_settings()
    if not cfg["server"] or not cfg["username"]:
        raise RuntimeError(
            "Conexión sin configurar. Copia db_config.example.ini a db_config.ini "
            "y completa server, database, username y password."
        )
    return pyodbc.connect(_connection_string(cfg), timeout=5)


def test_connection():
    """Prueba la conexión. Devuelve (ok: bool, mensaje: str)."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT @@VERSION")
        version = cur.fetchone()[0].splitlines()[0].strip()
        cur.execute("SELECT COUNT(*) FROM sys.tables WHERE is_ms_shipped = 0")
        n_tablas = cur.fetchone()[0]
        conn.close()
        return True, f"Conexión OK · {version} · {n_tablas} tablas de usuario"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


if __name__ == "__main__":
    ok, msg = test_connection()
    print(("[OK] " if ok else "[ERROR] ") + msg)
