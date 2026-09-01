"""
repo_indicadores.py
Repositorio de indicadores agregados para el Histórico (KPIs y ranking).
"""

from datos.repositorio_base import RepositorioBase


class RepoIndicadores(RepositorioBase):
    def resumen(self):
        """KPIs del tablero calculados en vivo desde la base."""
        pet = self._valor("SELECT ISNULL(SUM(PesoPET),0) FROM JornadasRecoleccion")
        filamento = self._valor("SELECT ISNULL(SUM(PesoObtenido),0) FROM ProduccionFilamento")
        consumido = self._valor(
            "SELECT ISNULL(SUM(j.PesoPET),0) FROM ProduccionFilamento p "
            "JOIN JornadasRecoleccion j ON p.IdJornada = j.IdJornada")
        desperdicio = max(consumido - filamento, 0.0)
        objetos = int(self._valor("SELECT ISNULL(SUM(Cantidad),0) FROM FabricacionObjetos"))
        responsables = int(self._valor("SELECT COUNT(*) FROM Responsables"))
        botellas = int(self._valor("SELECT ISNULL(SUM(CantidadBotellas),0) FROM JornadasRecoleccion"))
        return {
            "pet_recolectado": pet,
            "filamento_producido": filamento,
            "desperdicio": desperdicio,
            "objetos_impresos": objetos,
            "responsables": responsables,
            "botellas": botellas,
        }

    def ranking(self, limite=10):
        """Ranking de responsables por PET aportado (gamificación)."""
        return self._query(
            f"SELECT TOP {int(limite)} r.NombreResponsable, "
            "ISNULL(SUM(j.PesoPET),0) AS Pet, "
            "COUNT(j.IdJornada) AS Jornadas, "
            "ISNULL(SUM(j.CantidadBotellas),0) AS Botellas "
            "FROM Responsables r "
            "LEFT JOIN JornadasRecoleccion j ON j.IdResponsable = r.IdResponsable "
            "GROUP BY r.NombreResponsable "
            "ORDER BY Pet DESC")
