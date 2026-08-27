"""
repo_jornadas.py
Repositorio de recolecciones (tabla JornadasRecoleccion).
"""

from repositorio_base import RepositorioBase, parse_fecha


class RepoJornadas(RepositorioBase):
    def listar_para_combo(self):
        """(IdJornada, etiqueta, PesoPET) para el desplegable de Transformación."""
        filas = self._query(
            "SELECT j.IdJornada, j.Fecha, l.NombreLugar, j.PesoPET "
            "FROM JornadasRecoleccion j LEFT JOIN Lugares l ON j.IdLugar = l.IdLugar "
            "ORDER BY j.Fecha DESC, j.IdJornada DESC")
        out = []
        for idj, fecha, lugar, peso in filas:
            peso = float(peso) if peso is not None else 0.0
            etiqueta = f"#{idj} · {fecha:%d/%m/%Y} · {lugar or 'Sin lugar'} ({peso:g} kg PET)"
            out.append((idj, etiqueta, peso))
        return out

    def peso_pet(self, id_jornada):
        row = self._query("SELECT PesoPET FROM JornadasRecoleccion WHERE IdJornada = ?",
                          (id_jornada,), fetch="one")
        return float(row[0]) if row and row[0] is not None else 0.0

    def crear(self, fecha, id_lugar, id_responsable, cantidad_botellas, peso_pet, observaciones):
        return self._ejecutar(
            "INSERT INTO JornadasRecoleccion "
            "(Fecha, IdLugar, IdResponsable, CantidadBotellas, PesoPET, Observaciones) "
            "OUTPUT INSERTED.IdJornada VALUES (?, ?, ?, ?, ?, ?)",
            (parse_fecha(fecha), id_lugar, id_responsable,
             cantidad_botellas, peso_pet, observaciones or None),
            return_id=True)

    def recientes(self, limite=50):
        return self._query(
            f"SELECT TOP {int(limite)} j.Fecha, r.NombreResponsable, l.NombreLugar, "
            "j.CantidadBotellas, j.PesoPET, j.Observaciones "
            "FROM JornadasRecoleccion j "
            "LEFT JOIN Responsables r ON j.IdResponsable = r.IdResponsable "
            "LEFT JOIN Lugares l ON j.IdLugar = l.IdLugar "
            "ORDER BY j.Fecha DESC, j.IdJornada DESC")

    def listar_admin(self, limite=300):
        return self._query(
            f"SELECT TOP {int(limite)} j.IdJornada, j.Fecha, r.NombreResponsable, l.NombreLugar, "
            "j.CantidadBotellas, j.PesoPET, j.Observaciones "
            "FROM JornadasRecoleccion j "
            "LEFT JOIN Responsables r ON j.IdResponsable = r.IdResponsable "
            "LEFT JOIN Lugares l ON j.IdLugar = l.IdLugar "
            "ORDER BY j.Fecha DESC, j.IdJornada DESC")

    def obtener(self, id_jornada):
        return self._query(
            "SELECT IdJornada, Fecha, IdLugar, IdResponsable, CantidadBotellas, PesoPET, Observaciones "
            "FROM JornadasRecoleccion WHERE IdJornada = ?", (id_jornada,), fetch="one")

    def actualizar(self, id_jornada, fecha, id_lugar, id_responsable, botellas, peso, obs):
        self._ejecutar(
            "UPDATE JornadasRecoleccion SET Fecha=?, IdLugar=?, IdResponsable=?, "
            "CantidadBotellas=?, PesoPET=?, Observaciones=? WHERE IdJornada=?",
            (parse_fecha(fecha), id_lugar, id_responsable, botellas, peso, obs or None, id_jornada))

    def eliminar(self, id_jornada):
        fila = self._query("SELECT COUNT(*) FROM ProduccionFilamento WHERE IdJornada = ?",
                           (id_jornada,), fetch="one")
        if fila and fila[0] > 0:
            raise RuntimeError(
                "No se puede eliminar: la jornada tiene producciones de filamento asociadas. "
                "Elimine primero esas producciones.")
        self._ejecutar("DELETE FROM JornadasRecoleccion WHERE IdJornada = ?", (id_jornada,))
