"""
repo_catalogos.py
Repositorios de catálogos: Responsables, Lugares y Modelos.
"""

from repositorio_base import RepositorioBase


class RepoResponsables(RepositorioBase):
    def listar(self):
        return [(r[0], r[1]) for r in self._query(
            "SELECT IdResponsable, NombreResponsable FROM Responsables ORDER BY NombreResponsable")]


class RepoLugares(RepositorioBase):
    def listar(self):
        return [(r[0], r[1]) for r in self._query(
            "SELECT IdLugar, NombreLugar FROM Lugares ORDER BY NombreLugar")]

    def listar_admin(self):
        return self._query("SELECT IdLugar, NombreLugar, Descripcion FROM Lugares ORDER BY NombreLugar")

    def crear(self, nombre, descripcion):
        return self._ejecutar(
            "INSERT INTO Lugares (NombreLugar, Descripcion) OUTPUT INSERTED.IdLugar VALUES (?, ?)",
            (nombre, descripcion or None), return_id=True)

    def actualizar(self, id_lugar, nombre, descripcion):
        self._ejecutar("UPDATE Lugares SET NombreLugar=?, Descripcion=? WHERE IdLugar=?",
                       (nombre, descripcion or None, id_lugar))

    def eliminar(self, id_lugar):
        fila = self._query("SELECT COUNT(*) FROM JornadasRecoleccion WHERE IdLugar = ?",
                           (id_lugar,), fetch="one")
        if fila and fila[0] > 0:
            raise RuntimeError("No se puede eliminar: el lugar tiene recolecciones asociadas.")
        self._ejecutar("DELETE FROM Lugares WHERE IdLugar = ?", (id_lugar,))


class RepoModelos(RepositorioBase):
    def listar(self):
        return [(r[0], r[1]) for r in self._query(
            "SELECT IdModelo, Nombre FROM Modelos ORDER BY Nombre")]

    def listar_admin(self):
        return self._query(
            "SELECT IdModelo, Nombre, Categoria, TiempoEstimado, PesoEstimado "
            "FROM Modelos ORDER BY Nombre")

    def crear(self, nombre, categoria, tiempo_estimado, peso_estimado):
        return self._ejecutar(
            "INSERT INTO Modelos (Nombre, Categoria, TiempoEstimado, PesoEstimado) "
            "OUTPUT INSERTED.IdModelo VALUES (?, ?, ?, ?)",
            (nombre, categoria or None, tiempo_estimado, peso_estimado), return_id=True)

    def actualizar(self, id_modelo, nombre, categoria, tiempo_estimado, peso_estimado):
        self._ejecutar(
            "UPDATE Modelos SET Nombre=?, Categoria=?, TiempoEstimado=?, PesoEstimado=? WHERE IdModelo=?",
            (nombre, categoria or None, tiempo_estimado, peso_estimado, id_modelo))

    def eliminar(self, id_modelo):
        fila = self._query("SELECT COUNT(*) FROM FabricacionObjetos WHERE IdModelo = ?",
                           (id_modelo,), fetch="one")
        if fila and fila[0] > 0:
            raise RuntimeError("No se puede eliminar: el modelo tiene impresiones asociadas.")
        self._ejecutar("DELETE FROM Modelos WHERE IdModelo = ?", (id_modelo,))
