"""
repo_produccion.py
Repositorio de transformaciones (tabla ProduccionFilamento).
"""

from datos.repositorio_base import RepositorioBase, parse_fecha


class RepoProduccion(RepositorioBase):
    def listar_para_combo(self):
        """(IdProduccion, etiqueta, PesoObtenido) para el desplegable de Impresión."""
        filas = self._query(
            "SELECT IdProduccion, Fecha, Color, PesoObtenido FROM ProduccionFilamento "
            "ORDER BY Fecha DESC, IdProduccion DESC")
        out = []
        for idp, fecha, color, peso in filas:
            peso = float(peso) if peso is not None else 0.0
            f = f"{fecha:%d/%m/%Y}" if fecha else "s/f"
            etiqueta = f"#{idp} · {f} · {color or 'sin color'} ({peso:g} kg)"
            out.append((idp, etiqueta, peso))
        return out

    def crear(self, id_jornada, fecha, color, diametro, peso_obtenido, metros, observaciones):
        return self._ejecutar(
            "INSERT INTO ProduccionFilamento "
            "(IdJornada, Fecha, Color, Diametro, PesoObtenido, MetrosProduccion, Observaciones) "
            "OUTPUT INSERTED.IdProduccion VALUES (?, ?, ?, ?, ?, ?, ?)",
            (id_jornada, parse_fecha(fecha), color or None, diametro,
             peso_obtenido, metros, observaciones or None),
            return_id=True)

    def recientes(self, limite=50):
        return self._query(
            f"SELECT TOP {int(limite)} p.Fecha, j.IdJornada, p.Color, p.Diametro, "
            "j.PesoPET, p.PesoObtenido, p.MetrosProduccion, p.Observaciones "
            "FROM ProduccionFilamento p "
            "LEFT JOIN JornadasRecoleccion j ON p.IdJornada = j.IdJornada "
            "ORDER BY p.Fecha DESC, p.IdProduccion DESC")

    def listar_admin(self, limite=300):
        return self._query(
            f"SELECT TOP {int(limite)} p.IdProduccion, p.Fecha, p.IdJornada, p.Color, "
            "p.Diametro, p.PesoObtenido, p.MetrosProduccion, p.Observaciones "
            "FROM ProduccionFilamento p ORDER BY p.Fecha DESC, p.IdProduccion DESC")

    def obtener(self, id_produccion):
        return self._query(
            "SELECT IdProduccion, IdJornada, Fecha, Color, Diametro, PesoObtenido, "
            "MetrosProduccion, Observaciones FROM ProduccionFilamento WHERE IdProduccion = ?",
            (id_produccion,), fetch="one")

    def actualizar(self, id_produccion, id_jornada, fecha, color, diametro, peso_obtenido, metros, obs):
        self._ejecutar(
            "UPDATE ProduccionFilamento SET IdJornada=?, Fecha=?, Color=?, Diametro=?, "
            "PesoObtenido=?, MetrosProduccion=?, Observaciones=? WHERE IdProduccion=?",
            (id_jornada, parse_fecha(fecha), color or None, diametro, peso_obtenido, metros,
             obs or None, id_produccion))

    def eliminar(self, id_produccion):
        fila = self._query("SELECT COUNT(*) FROM FabricacionObjetos WHERE IdProduccion = ?",
                           (id_produccion,), fetch="one")
        if fila and fila[0] > 0:
            raise RuntimeError(
                "No se puede eliminar: la producción tiene impresiones asociadas. "
                "Elimine primero esas impresiones.")
        self._ejecutar("DELETE FROM ProduccionFilamento WHERE IdProduccion = ?", (id_produccion,))
