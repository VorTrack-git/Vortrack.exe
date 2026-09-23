"""
repo_indicadores.py
Repositorio de indicadores agregados para el Histórico (KPIs y ranking).
"""

from concurrent.futures import ThreadPoolExecutor

from datos.repositorio_base import RepositorioBase

# Consultas escalares de los KPIs. Son independientes entre sí, así que se
# lanzan todas a la vez (cada una en su propia conexión) en vez de una por una.
_SQL_KPIS = {
    "pet": "SELECT ISNULL(SUM(PesoPET),0) FROM JornadasRecoleccion",
    "filamento": "SELECT ISNULL(SUM(PesoObtenido),0) FROM ProduccionFilamento",
    "consumido": ("SELECT ISNULL(SUM(j.PesoPET),0) FROM ProduccionFilamento p "
                  "JOIN JornadasRecoleccion j ON p.IdJornada = j.IdJornada"),
    "objetos": "SELECT ISNULL(SUM(Cantidad),0) FROM FabricacionObjetos",
    "responsables": "SELECT COUNT(*) FROM Responsables",
    "botellas": "SELECT ISNULL(SUM(CantidadBotellas),0) FROM JornadasRecoleccion",
}


class RepoIndicadores(RepositorioBase):
    def resumen(self):
        """KPIs del tablero calculados en vivo desde la base (consultas en paralelo)."""
        with ThreadPoolExecutor(max_workers=len(_SQL_KPIS)) as pool:
            futuros = {clave: pool.submit(self._valor, sql) for clave, sql in _SQL_KPIS.items()}
            v = {clave: f.result() for clave, f in futuros.items()}
        pet, filamento = v["pet"], v["filamento"]
        desperdicio = max(v["consumido"] - filamento, 0.0)
        objetos = int(v["objetos"])
        responsables = int(v["responsables"])
        botellas = int(v["botellas"])
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
