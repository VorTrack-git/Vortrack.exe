"""
repo_fabricacion.py
Repositorio de impresiones (tabla FabricacionObjetos).
"""

from datos.repositorio_base import RepositorioBase, parse_fecha


class RepoFabricacion(RepositorioBase):
    def crear(self, id_modelo, id_produccion, fecha, cantidad, peso_utilizado, tiempo_min, estado):
        return self._ejecutar(
            "INSERT INTO FabricacionObjetos "
            "(IdModelo, IdProduccion, Fecha, Cantidad, PesoUtilizado, TiempoImpresion, Estado) "
            "OUTPUT INSERTED.IdFabricacion VALUES (?, ?, ?, ?, ?, ?, ?)",
            (id_modelo, id_produccion, parse_fecha(fecha), cantidad,
             peso_utilizado, tiempo_min, estado or None),
            return_id=True)

    def recientes(self, limite=50):
        return self._query(
            f"SELECT TOP {int(limite)} f.Fecha, m.Nombre, f.Cantidad, f.PesoUtilizado, "
            "f.TiempoImpresion, f.Estado, f.IdProduccion "
            "FROM FabricacionObjetos f "
            "LEFT JOIN Modelos m ON f.IdModelo = m.IdModelo "
            "ORDER BY f.Fecha DESC, f.IdFabricacion DESC")

    def listar_admin(self, limite=300):
        return self._query(
            f"SELECT TOP {int(limite)} f.IdFabricacion, f.Fecha, f.IdModelo, m.Nombre, "
            "f.IdProduccion, f.Cantidad, f.PesoUtilizado, f.TiempoImpresion, f.Estado "
            "FROM FabricacionObjetos f LEFT JOIN Modelos m ON f.IdModelo = m.IdModelo "
            "ORDER BY f.Fecha DESC, f.IdFabricacion DESC")

    def obtener(self, id_fab):
        return self._query(
            "SELECT IdFabricacion, IdModelo, IdProduccion, Fecha, Cantidad, PesoUtilizado, "
            "TiempoImpresion, Estado FROM FabricacionObjetos WHERE IdFabricacion = ?",
            (id_fab,), fetch="one")

    def actualizar(self, id_fab, id_modelo, id_produccion, fecha, cantidad, peso, tiempo, estado):
        self._ejecutar(
            "UPDATE FabricacionObjetos SET IdModelo=?, IdProduccion=?, Fecha=?, Cantidad=?, "
            "PesoUtilizado=?, TiempoImpresion=?, Estado=? WHERE IdFabricacion=?",
            (id_modelo, id_produccion, parse_fecha(fecha), cantidad, peso, tiempo, estado, id_fab))

    def eliminar(self, id_fab):
        self._ejecutar("DELETE FROM FabricacionObjetos WHERE IdFabricacion = ?", (id_fab,))
