"""
seed_usuario.py
Crea (o actualiza) el primer usuario de VorTrack en la base de datos.

- Asegura que exista el rol "Administrador" en la tabla Roles.
- Pide la contraseña por consola (no se muestra ni se guarda en el código),
  la hashea con SHA-256 y crea el usuario en la tabla Usuarios.

Uso (en tu terminal):
    python seed_usuario.py
"""

import getpass
import hashlib
import os as _os, sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

import datos.db as db

USUARIO = "vortrack.soporte@gmail.com"
NOMBRES = "Administrador"
APELLIDOS = "VorTrack"
ROL = "Administrador"
ESTADO = "Activo"


def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()


def _get_or_create_rol(cursor, nombre: str) -> int:
    cursor.execute("SELECT IdRol FROM Roles WHERE Nombre = ?", nombre)
    fila = cursor.fetchone()
    if fila:
        print(f"Rol '{nombre}' ya existe (IdRol={fila[0]}).")
        return fila[0]
    cursor.execute("INSERT INTO Roles (Nombre) OUTPUT INSERTED.IdRol VALUES (?)", nombre)
    id_rol = cursor.fetchone()[0]
    print(f"Rol '{nombre}' creado (IdRol={id_rol}).")
    return id_rol


def main():
    try:
        conn = db.get_connection()
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] No se pudo conectar a la base de datos: {exc}")
        return

    cursor = conn.cursor()
    id_rol = _get_or_create_rol(cursor, ROL)

    cursor.execute("SELECT IdUsuario FROM Usuarios WHERE Usuario = ?", USUARIO)
    existe = cursor.fetchone()

    pwd = getpass.getpass(f"Contraseña para {USUARIO}: ")
    pwd2 = getpass.getpass("Confírmala: ")
    if not pwd or pwd != pwd2:
        print("[CANCELADO] Las contraseñas están vacías o no coinciden.")
        conn.close()
        return

    hashed = _hash(pwd)

    if existe:
        cursor.execute(
            "UPDATE Usuarios SET Contrasena = ?, Estado = ?, IdRol = ? WHERE Usuario = ?",
            hashed, ESTADO, id_rol, USUARIO,
        )
        print(f"Usuario '{USUARIO}' ya existía: contraseña actualizada.")
    else:
        cursor.execute(
            "INSERT INTO Usuarios (Nombres, Apellidos, Usuario, Contrasena, IdRol, Estado) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            NOMBRES, APELLIDOS, USUARIO, hashed, id_rol, ESTADO,
        )
        print(f"Usuario '{USUARIO}' creado.")

    conn.commit()
    conn.close()
    print("Listo. Ya puedes iniciar sesión en VorTrack con ese usuario.")


if __name__ == "__main__":
    main()
