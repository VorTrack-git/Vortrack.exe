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
