"""
repositorio.py
Capa de acceso a datos de VorTrack sobre SQL Server.

Centraliza todas las consultas e inserciones para que la interfaz no hable
SQL directamente. La cadena de trazabilidad del proyecto es:

    Lugar + Responsable -> JornadaRecoleccion -> ProduccionFilamento
                                              -> FabricacionObjetos (Modelo)
"""

from datetime import date, datetime

import db


# ---------------------------------------------------------------------------
# Utilidades internas
# ---------------------------------------------------------------------------
def _query(sql, params=(), fetch="all"):
    conn = db.get_connection()
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


def _execute(sql, params=(), return_id=False):
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        new_id = cur.fetchone()[0] if return_id else None
        conn.commit()
        return new_id
    finally:
        conn.close()


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


# ---------------------------------------------------------------------------
# Catálogos (para los desplegables)
# ---------------------------------------------------------------------------
def listar_responsables():
    """[(IdResponsable, NombreResponsable), ...] ordenados por nombre."""
    return [(r[0], r[1]) for r in _query(
        "SELECT IdResponsable, NombreResponsable FROM Responsables ORDER BY NombreResponsable")]


def listar_lugares():
    return [(r[0], r[1]) for r in _query(
        "SELECT IdLugar, NombreLugar FROM Lugares ORDER BY NombreLugar")]


def listar_modelos():
    return [(r[0], r[1]) for r in _query(
        "SELECT IdModelo, Nombre FROM Modelos ORDER BY Nombre")]


def listar_jornadas():
    """Para el desplegable de Transformación: (IdJornada, etiqueta, PesoPET)."""
    filas = _query(
        "SELECT j.IdJornada, j.Fecha, l.NombreLugar, j.PesoPET "
        "FROM JornadasRecoleccion j LEFT JOIN Lugares l ON j.IdLugar = l.IdLugar "
        "ORDER BY j.Fecha DESC, j.IdJornada DESC")
    out = []
    for idj, fecha, lugar, peso in filas:
        peso = float(peso) if peso is not None else 0.0
        etiqueta = f"#{idj} · {fecha:%d/%m/%Y} · {lugar or 'Sin lugar'} ({peso:g} kg PET)"
        out.append((idj, etiqueta, peso))
    return out


def listar_producciones():
    """Para el desplegable de Impresión: (IdProduccion, etiqueta, PesoObtenido)."""
    filas = _query(
        "SELECT IdProduccion, Fecha, Color, PesoObtenido FROM ProduccionFilamento "
        "ORDER BY Fecha DESC, IdProduccion DESC")
    out = []
    for idp, fecha, color, peso in filas:
        peso = float(peso) if peso is not None else 0.0
        f = f"{fecha:%d/%m/%Y}" if fecha else "s/f"
        etiqueta = f"#{idp} · {f} · {color or 'sin color'} ({peso:g} kg)"
        out.append((idp, etiqueta, peso))
    return out


def peso_pet_jornada(id_jornada):
    """PesoPET de una jornada (el 'peso ingresado' en la transformación)."""
    row = _query("SELECT PesoPET FROM JornadasRecoleccion WHERE IdJornada = ?",
                 (id_jornada,), fetch="one")
    return float(row[0]) if row and row[0] is not None else 0.0


# ---------------------------------------------------------------------------
# Recolección  ->  JornadasRecoleccion
# ---------------------------------------------------------------------------
def crear_jornada(fecha, id_lugar, id_responsable, cantidad_botellas, peso_pet, observaciones):
    return _execute(
        "INSERT INTO JornadasRecoleccion "
        "(Fecha, IdLugar, IdResponsable, CantidadBotellas, PesoPET, Observaciones) "
        "OUTPUT INSERTED.IdJornada VALUES (?, ?, ?, ?, ?, ?)",
        (parse_fecha(fecha), id_lugar, id_responsable,
         cantidad_botellas, peso_pet, observaciones or None),
        return_id=True)


def recolecciones_recientes(limite=50):
    return _query(
        f"SELECT TOP {int(limite)} j.Fecha, r.NombreResponsable, l.NombreLugar, "
        "j.CantidadBotellas, j.PesoPET, j.Observaciones "
        "FROM JornadasRecoleccion j "
        "LEFT JOIN Responsables r ON j.IdResponsable = r.IdResponsable "
        "LEFT JOIN Lugares l ON j.IdLugar = l.IdLugar "
        "ORDER BY j.Fecha DESC, j.IdJornada DESC")


# ---------------------------------------------------------------------------
# Transformación  ->  ProduccionFilamento
# ---------------------------------------------------------------------------
def crear_produccion(id_jornada, fecha, color, diametro, peso_obtenido, metros, observaciones):
    return _execute(
        "INSERT INTO ProduccionFilamento "
        "(IdJornada, Fecha, Color, Diametro, PesoObtenido, MetrosProduccion, Observaciones) "
        "OUTPUT INSERTED.IdProduccion VALUES (?, ?, ?, ?, ?, ?, ?)",
        (id_jornada, parse_fecha(fecha), color or None, diametro,
         peso_obtenido, metros, observaciones or None),
        return_id=True)


def producciones_recientes(limite=50):
    return _query(
        f"SELECT TOP {int(limite)} p.Fecha, j.IdJornada, p.Color, p.Diametro, "
        "j.PesoPET, p.PesoObtenido, p.MetrosProduccion, p.Observaciones "
        "FROM ProduccionFilamento p "
        "LEFT JOIN JornadasRecoleccion j ON p.IdJornada = j.IdJornada "
        "ORDER BY p.Fecha DESC, p.IdProduccion DESC")


# ---------------------------------------------------------------------------
# Impresión  ->  FabricacionObjetos
# ---------------------------------------------------------------------------
def crear_fabricacion(id_modelo, id_produccion, fecha, cantidad, peso_utilizado, tiempo_min, estado):
    return _execute(
        "INSERT INTO FabricacionObjetos "
        "(IdModelo, IdProduccion, Fecha, Cantidad, PesoUtilizado, TiempoImpresion, Estado) "
        "OUTPUT INSERTED.IdFabricacion VALUES (?, ?, ?, ?, ?, ?, ?)",
        (id_modelo, id_produccion, parse_fecha(fecha), cantidad,
         peso_utilizado, tiempo_min, estado or None),
        return_id=True)


def fabricaciones_recientes(limite=50):
    return _query(
        f"SELECT TOP {int(limite)} f.Fecha, m.Nombre, f.Cantidad, f.PesoUtilizado, "
        "f.TiempoImpresion, f.Estado, f.IdProduccion "
        "FROM FabricacionObjetos f "
        "LEFT JOIN Modelos m ON f.IdModelo = m.IdModelo "
        "ORDER BY f.Fecha DESC, f.IdFabricacion DESC")


# ---------------------------------------------------------------------------
# Histórico e indicadores (agregados)
# ---------------------------------------------------------------------------
def _valor(sql):
    row = _query(sql, fetch="one")
    v = row[0] if row else 0
    return float(v) if v is not None else 0.0


def indicadores_resumen():
    """Devuelve los KPIs del tablero calculados en vivo desde la base."""
    pet = _valor("SELECT ISNULL(SUM(PesoPET),0) FROM JornadasRecoleccion")
    filamento = _valor("SELECT ISNULL(SUM(PesoObtenido),0) FROM ProduccionFilamento")
    # Desperdicio = PET de jornadas usadas en producción - filamento obtenido
    consumido = _valor(
        "SELECT ISNULL(SUM(j.PesoPET),0) FROM ProduccionFilamento p "
        "JOIN JornadasRecoleccion j ON p.IdJornada = j.IdJornada")
    desperdicio = max(consumido - filamento, 0.0)
    objetos = int(_valor("SELECT ISNULL(SUM(Cantidad),0) FROM FabricacionObjetos"))
    responsables = int(_valor("SELECT COUNT(*) FROM Responsables"))
    botellas = int(_valor("SELECT ISNULL(SUM(CantidadBotellas),0) FROM JornadasRecoleccion"))
    return {
        "pet_recolectado": pet,
        "filamento_producido": filamento,
        "desperdicio": desperdicio,
        "objetos_impresos": objetos,
        "responsables": responsables,
        "botellas": botellas,
    }


def ranking_participacion(limite=10):
    """Ranking de responsables por PET aportado (gamificación)."""
    return _query(
        f"SELECT TOP {int(limite)} r.NombreResponsable, "
        "ISNULL(SUM(j.PesoPET),0) AS Pet, "
        "COUNT(j.IdJornada) AS Jornadas, "
        "ISNULL(SUM(j.CantidadBotellas),0) AS Botellas "
        "FROM Responsables r "
        "LEFT JOIN JornadasRecoleccion j ON j.IdResponsable = r.IdResponsable "
        "GROUP BY r.NombreResponsable "
        "ORDER BY Pet DESC")


# ---------------------------------------------------------------------------
# ADMINISTRACIÓN — CRUD de estudiantes (Usuarios rol Estudiante + Responsables)
# ---------------------------------------------------------------------------
def listar_estudiantes():
    """(IdUsuario, Nombres, Apellidos, Correo, Telefono, Contrasena, Estado)."""
    return _query(
        "SELECT u.IdUsuario, u.Nombres, u.Apellidos, u.Usuario, r.Telefono, "
        "u.Contrasena, u.Estado "
        "FROM Usuarios u "
        "JOIN Roles ro ON u.IdRol = ro.IdRol AND ro.Nombre = 'Estudiante' "
        "LEFT JOIN Responsables r ON r.Email = u.Usuario "
        "ORDER BY u.Nombres, u.Apellidos")


def _id_rol_estudiante(cur):
    cur.execute("SELECT IdRol FROM Roles WHERE Nombre = 'Estudiante'")
    r = cur.fetchone()
    if r:
        return r[0]
    cur.execute("INSERT INTO Roles (Nombre) OUTPUT INSERTED.IdRol VALUES ('Estudiante')")
    return cur.fetchone()[0]


def crear_estudiante(nombres, apellidos, correo, telefono, contrasena):
    """Crea el estudiante en Usuarios (login) y en Responsables (aportante)."""
    correo = (correo or "").strip()
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Usuarios WHERE Usuario = ?", correo)
        if cur.fetchone()[0] > 0:
            raise ValueError("Ya existe una cuenta con ese correo.")
        id_rol = _id_rol_estudiante(cur)
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


def actualizar_estudiante(id_usuario, nombres, apellidos, correo, telefono, contrasena, estado):
    correo = (correo or "").strip()
    conn = db.get_connection()
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


def eliminar_estudiante(id_usuario):
    conn = db.get_connection()
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


# ---------------------------------------------------------------------------
# ADMINISTRACIÓN — CRUD de recolecciones (JornadasRecoleccion)
# ---------------------------------------------------------------------------
def recolecciones_admin(limite=300):
    return _query(
        f"SELECT TOP {int(limite)} j.IdJornada, j.Fecha, r.NombreResponsable, l.NombreLugar, "
        "j.CantidadBotellas, j.PesoPET, j.Observaciones "
        "FROM JornadasRecoleccion j "
        "LEFT JOIN Responsables r ON j.IdResponsable = r.IdResponsable "
        "LEFT JOIN Lugares l ON j.IdLugar = l.IdLugar "
        "ORDER BY j.Fecha DESC, j.IdJornada DESC")


def obtener_jornada(id_jornada):
    return _query(
        "SELECT IdJornada, Fecha, IdLugar, IdResponsable, CantidadBotellas, PesoPET, Observaciones "
        "FROM JornadasRecoleccion WHERE IdJornada = ?", (id_jornada,), fetch="one")


def actualizar_jornada(id_jornada, fecha, id_lugar, id_responsable, botellas, peso, obs):
    _execute(
        "UPDATE JornadasRecoleccion SET Fecha=?, IdLugar=?, IdResponsable=?, "
        "CantidadBotellas=?, PesoPET=?, Observaciones=? WHERE IdJornada=?",
        (parse_fecha(fecha), id_lugar, id_responsable, botellas, peso, obs or None, id_jornada))


def eliminar_jornada(id_jornada):
    fila = _query("SELECT COUNT(*) FROM ProduccionFilamento WHERE IdJornada = ?",
                  (id_jornada,), fetch="one")
    if fila and fila[0] > 0:
        raise RuntimeError(
            "No se puede eliminar: la jornada tiene producciones de filamento asociadas. "
            "Elimine primero esas producciones.")
    _execute("DELETE FROM JornadasRecoleccion WHERE IdJornada = ?", (id_jornada,))


# ---------------------------------------------------------------------------
# ADMINISTRACIÓN — CRUD de transformaciones (ProduccionFilamento)
# ---------------------------------------------------------------------------
def producciones_admin(limite=300):
    return _query(
        f"SELECT TOP {int(limite)} p.IdProduccion, p.Fecha, p.IdJornada, p.Color, "
        "p.Diametro, p.PesoObtenido, p.MetrosProduccion, p.Observaciones "
        "FROM ProduccionFilamento p ORDER BY p.Fecha DESC, p.IdProduccion DESC")


def obtener_produccion(id_produccion):
    return _query(
        "SELECT IdProduccion, IdJornada, Fecha, Color, Diametro, PesoObtenido, "
        "MetrosProduccion, Observaciones FROM ProduccionFilamento WHERE IdProduccion = ?",
        (id_produccion,), fetch="one")


def actualizar_produccion(id_produccion, id_jornada, fecha, color, diametro, peso_obtenido, metros, obs):
    _execute(
        "UPDATE ProduccionFilamento SET IdJornada=?, Fecha=?, Color=?, Diametro=?, "
        "PesoObtenido=?, MetrosProduccion=?, Observaciones=? WHERE IdProduccion=?",
        (id_jornada, parse_fecha(fecha), color or None, diametro, peso_obtenido, metros,
         obs or None, id_produccion))


def eliminar_produccion(id_produccion):
    fila = _query("SELECT COUNT(*) FROM FabricacionObjetos WHERE IdProduccion = ?",
                  (id_produccion,), fetch="one")
    if fila and fila[0] > 0:
        raise RuntimeError(
            "No se puede eliminar: la producción tiene impresiones asociadas. "
            "Elimine primero esas impresiones.")
    _execute("DELETE FROM ProduccionFilamento WHERE IdProduccion = ?", (id_produccion,))


# ---------------------------------------------------------------------------
# ADMINISTRACIÓN — CRUD de impresiones (FabricacionObjetos)
# ---------------------------------------------------------------------------
def fabricaciones_admin(limite=300):
    return _query(
        f"SELECT TOP {int(limite)} f.IdFabricacion, f.Fecha, f.IdModelo, m.Nombre, "
        "f.IdProduccion, f.Cantidad, f.PesoUtilizado, f.TiempoImpresion, f.Estado "
        "FROM FabricacionObjetos f LEFT JOIN Modelos m ON f.IdModelo = m.IdModelo "
        "ORDER BY f.Fecha DESC, f.IdFabricacion DESC")


def obtener_fabricacion(id_fab):
    return _query(
        "SELECT IdFabricacion, IdModelo, IdProduccion, Fecha, Cantidad, PesoUtilizado, "
        "TiempoImpresion, Estado FROM FabricacionObjetos WHERE IdFabricacion = ?",
        (id_fab,), fetch="one")


def actualizar_fabricacion(id_fab, id_modelo, id_produccion, fecha, cantidad, peso, tiempo, estado):
    _execute(
        "UPDATE FabricacionObjetos SET IdModelo=?, IdProduccion=?, Fecha=?, Cantidad=?, "
        "PesoUtilizado=?, TiempoImpresion=?, Estado=? WHERE IdFabricacion=?",
        (id_modelo, id_produccion, parse_fecha(fecha), cantidad, peso, tiempo, estado, id_fab))


def eliminar_fabricacion(id_fab):
    _execute("DELETE FROM FabricacionObjetos WHERE IdFabricacion = ?", (id_fab,))


# ---------------------------------------------------------------------------
# ADMINISTRACIÓN — CRUD de Lugares
# ---------------------------------------------------------------------------
def listar_lugares_admin():
    return _query("SELECT IdLugar, NombreLugar, Descripcion FROM Lugares ORDER BY NombreLugar")


def crear_lugar(nombre, descripcion):
    return _execute(
        "INSERT INTO Lugares (NombreLugar, Descripcion) OUTPUT INSERTED.IdLugar VALUES (?, ?)",
        (nombre, descripcion or None), return_id=True)


def actualizar_lugar(id_lugar, nombre, descripcion):
    _execute("UPDATE Lugares SET NombreLugar=?, Descripcion=? WHERE IdLugar=?",
             (nombre, descripcion or None, id_lugar))


def eliminar_lugar(id_lugar):
    fila = _query("SELECT COUNT(*) FROM JornadasRecoleccion WHERE IdLugar = ?",
                  (id_lugar,), fetch="one")
    if fila and fila[0] > 0:
        raise RuntimeError("No se puede eliminar: el lugar tiene recolecciones asociadas.")
    _execute("DELETE FROM Lugares WHERE IdLugar = ?", (id_lugar,))


# ---------------------------------------------------------------------------
# ADMINISTRACIÓN — CRUD de Modelos (material didáctico a imprimir)
# ---------------------------------------------------------------------------
def listar_modelos_admin():
    return _query(
        "SELECT IdModelo, Nombre, Categoria, TiempoEstimado, PesoEstimado "
        "FROM Modelos ORDER BY Nombre")


def crear_modelo(nombre, categoria, tiempo_estimado, peso_estimado):
    return _execute(
        "INSERT INTO Modelos (Nombre, Categoria, TiempoEstimado, PesoEstimado) "
        "OUTPUT INSERTED.IdModelo VALUES (?, ?, ?, ?)",
        (nombre, categoria or None, tiempo_estimado, peso_estimado), return_id=True)


def actualizar_modelo(id_modelo, nombre, categoria, tiempo_estimado, peso_estimado):
    _execute(
        "UPDATE Modelos SET Nombre=?, Categoria=?, TiempoEstimado=?, PesoEstimado=? WHERE IdModelo=?",
        (nombre, categoria or None, tiempo_estimado, peso_estimado, id_modelo))


def eliminar_modelo(id_modelo):
    fila = _query("SELECT COUNT(*) FROM FabricacionObjetos WHERE IdModelo = ?",
                  (id_modelo,), fetch="one")
    if fila and fila[0] > 0:
        raise RuntimeError("No se puede eliminar: el modelo tiene impresiones asociadas.")
    _execute("DELETE FROM Modelos WHERE IdModelo = ?", (id_modelo,))
