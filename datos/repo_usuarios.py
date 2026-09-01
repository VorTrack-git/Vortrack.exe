"""
repo_usuarios.py
Repositorio de usuarios: consulta de login y CRUD de estudiantes.

Un estudiante se materializa como una fila en Usuarios (cuenta de acceso) y una
en Responsables (aportante en las recolecciones), enlazadas por el correo.
"""

from datos.repositorio_base import RepositorioBase


class RepoUsuarios(RepositorioBase):
    # ------------------------------------------------------------------ login
    def buscar_para_login(self, usuario):
        """Fila del usuario activo (con su rol) o None. Para autenticación."""
        return self._query(
            "SELECT u.IdUsuario, u.Nombres, u.Apellidos, u.Usuario, u.Contrasena, "
            "u.IdRol, r.Nombre AS Rol "
            "FROM Usuarios u LEFT JOIN Roles r ON u.IdRol = r.IdRol "
            "WHERE u.Usuario = ? AND u.Estado = 'Activo'",
            (usuario,), fetch="one")

    # ------------------------------------------------------------- estudiantes
    def listar_estudiantes(self):
        """(IdUsuario, Nombres, Apellidos, Correo, Telefono, Contrasena, Estado)."""
        return self._query(
            "SELECT u.IdUsuario, u.Nombres, u.Apellidos, u.Usuario, r.Telefono, "
            "u.Contrasena, u.Estado "
            "FROM Usuarios u "
            "JOIN Roles ro ON u.IdRol = ro.IdRol AND ro.Nombre = 'Estudiante' "
            "LEFT JOIN Responsables r ON r.Email = u.Usuario "
            "ORDER BY u.Nombres, u.Apellidos")

    def _id_rol_estudiante(self, cur):
        cur.execute("SELECT IdRol FROM Roles WHERE Nombre = 'Estudiante'")
        r = cur.fetchone()
        if r:
            return r[0]
        cur.execute("INSERT INTO Roles (Nombre) OUTPUT INSERTED.IdRol VALUES ('Estudiante')")
        return cur.fetchone()[0]

    def crear_estudiante(self, nombres, apellidos, correo, telefono, contrasena):
        correo = (correo or "").strip()
        conn = self._abrir()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM Usuarios WHERE Usuario = ?", correo)
            if cur.fetchone()[0] > 0:
                raise ValueError("Ya existe una cuenta con ese correo.")
            id_rol = self._id_rol_estudiante(cur)
            nombre_completo = f"{nombres} {apellidos}".strip()
            cur.execute("SELECT COUNT(*) FROM Responsables WHERE Email = ?", correo)
            if cur.fetchone()[0] == 0:
                cur.execute(
                    "INSERT INTO Responsables (NombreResponsable, Email, Telefono) VALUES (?, ?, ?)",
                    nombre_completo, correo, (telefono or None))
            cur.execute(
                "INSERT INTO Usuarios (Nombres, Apellidos, Usuario, Contrasena, IdRol, Estado) "
                "OUTPUT INSERTED.IdUsuario VALUES (?, ?, ?, ?, ?, 'Activo')",
                nombres, apellidos, correo, contrasena, id_rol)
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
        finally:
            conn.close()

    def actualizar_estudiante(self, id_usuario, nombres, apellidos, correo, telefono, contrasena, estado):
        correo = (correo or "").strip()
        conn = self._abrir()
        try:
            cur = conn.cursor()
            cur.execute("SELECT Usuario FROM Usuarios WHERE IdUsuario = ?", id_usuario)
            row = cur.fetchone()
            correo_anterior = row[0] if row else None
            cur.execute("SELECT COUNT(*) FROM Usuarios WHERE Usuario = ? AND IdUsuario <> ?",
                        correo, id_usuario)
            if cur.fetchone()[0] > 0:
                raise ValueError("Ya existe otra cuenta con ese correo.")
            cur.execute(
                "UPDATE Usuarios SET Nombres=?, Apellidos=?, Usuario=?, Contrasena=?, Estado=? "
                "WHERE IdUsuario=?",
                nombres, apellidos, correo, contrasena, estado, id_usuario)
            nombre_completo = f"{nombres} {apellidos}".strip()
            cur.execute(
                "UPDATE Responsables SET NombreResponsable=?, Email=?, Telefono=? WHERE Email=?",
                nombre_completo, correo, (telefono or None), correo_anterior)
            conn.commit()
        finally:
            conn.close()

    def eliminar_estudiante(self, id_usuario):
        conn = self._abrir()
        try:
            cur = conn.cursor()
            cur.execute("SELECT Usuario FROM Usuarios WHERE IdUsuario = ?", id_usuario)
            row = cur.fetchone()
            correo = row[0] if row else None
            cur.execute("DELETE FROM Usuarios WHERE IdUsuario = ?", id_usuario)
            if correo:
                cur.execute("SELECT IdResponsable FROM Responsables WHERE Email = ?", correo)
                r = cur.fetchone()
                if r:
                    cur.execute("SELECT COUNT(*) FROM JornadasRecoleccion WHERE IdResponsable = ?", r[0])
                    if cur.fetchone()[0] == 0:
                        cur.execute("DELETE FROM Responsables WHERE IdResponsable = ?", r[0])
            conn.commit()
        finally:
            conn.close()
