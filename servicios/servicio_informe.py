"""
servicio_informe.py
Genera el informe PDF de VorTrack (Histórico e Informes).

Flujo:  recopilar (consultas en paralelo) -> calcular (estadísticas, lógica pura)
        -> render HTML (maqueta con gráficos SVG) -> exportar a PDF -> Descargas.

`calcular()` no toca la base ni la UI: recibe filas crudas y devuelve un
diccionario con todo lo que el informe muestra, así se puede probar aislado.
"""

from collections import OrderedDict, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime

import servicios.exportador_pdf as exportador_pdf
from servicios import informe_html

LIMITE_FILAS = 100000  # "todas" las filas: el informe resume el histórico completo

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
ESTADOS = ["Finalizado", "En proceso", "Fallido"]


def _f(v):
    return float(v) if v is not None else 0.0


def _i(v):
    return int(v) if v is not None else 0


def _fecha(v):
    if isinstance(v, datetime):
        return v.date()
    return v if isinstance(v, date) else None


def _pct(parte, total):
    return 100.0 * parte / total if total else 0.0


class ServicioInforme:
    # Pasos del informe (para el indicador de progreso de la UI).
    ETAPAS = ["Consultando la base de datos…", "Calculando estadísticas…",
              "Armando el documento…", "Exportando a PDF…"]

    def __init__(self, datos, exportador=exportador_pdf):
        self.datos = datos
        self.exportador = exportador

    # --- 1. Datos -------------------------------------------------------
    def recopilar(self):
        """Lanza todas las consultas a la vez (cada una en su hilo/conexión)."""
        d = self.datos
        consultas = {
            "indicadores": d.indicadores_resumen,
            "ranking": lambda: d.ranking_participacion(limite=1000),
            "recolecciones": lambda: d.recolecciones_admin(limite=LIMITE_FILAS),
            "producciones": lambda: d.producciones_admin(limite=LIMITE_FILAS),
            "fabricaciones": lambda: d.fabricaciones_admin(limite=LIMITE_FILAS),
        }
        with ThreadPoolExecutor(max_workers=len(consultas)) as pool:
            futuros = {k: pool.submit(f) for k, f in consultas.items()}
            return {k: f.result() for k, f in futuros.items()}

    # --- 2. Estadísticas (lógica pura) ------------------------------------
    @staticmethod
    def calcular(crudos):
        k = crudos["indicadores"]

        # Recolecciones: (IdJornada, Fecha, Responsable, Lugar, Botellas, PesoPET, Obs)
        recolecciones = [
            {"id": r[0], "fecha": _fecha(r[1]), "responsable": r[2] or "Sin responsable",
             "lugar": r[3] or "Sin lugar", "botellas": _i(r[4]), "pet": _f(r[5]), "obs": r[6] or ""}
            for r in crudos["recolecciones"]]
        pet_por_jornada = {r["id"]: r["pet"] for r in recolecciones}

        # Fabricaciones: (Id, Fecha, IdModelo, Modelo, IdProduccion, Cantidad, Peso g, Tiempo min, Estado)
        fabricaciones = [
            {"id": r[0], "fecha": _fecha(r[1]), "modelo": r[3] or "Sin modelo", "id_prod": r[4],
             "piezas": _i(r[5]), "peso_g": _f(r[6]), "tiempo_min": _i(r[7]), "estado": r[8] or "—"}
            for r in crudos["fabricaciones"]]
        usado_g_por_prod = defaultdict(float)
        for f in fabricaciones:
            usado_g_por_prod[f["id_prod"]] += f["peso_g"]

        # Producciones: (Id, Fecha, IdJornada, Color, Diámetro, PesoObtenido kg, Metros, Obs)
        producciones = []
        for r in crudos["producciones"]:
            pet = pet_por_jornada.get(r[2], 0.0)
            obtenido = _f(r[5])
            usado_kg = usado_g_por_prod.get(r[0], 0.0) / 1000.0
            producciones.append({
                "id": r[0], "fecha": _fecha(r[1]), "jornada": r[2], "color": r[3] or "—",
                "diametro": _f(r[4]) if r[4] is not None else None, "pet": pet, "obtenido": obtenido,
                "metros": _f(r[6]), "rendimiento": _pct(obtenido, pet),
                "usado": usado_kg, "disponible": obtenido - usado_kg})  # negativo = se usó más de lo producido

        # Totales y derivados
        pet_total = _f(k["pet_recolectado"])
        filamento = _f(k["filamento_producido"])
        pet_transformado = sum(p["pet"] for p in producciones)
        desperdicio = max(pet_transformado - filamento, 0.0)
        filamento_usado = sum(f["peso_g"] for f in fabricaciones) / 1000.0
        piezas_total = sum(f["piezas"] for f in fabricaciones)
        piezas_por_estado = OrderedDict((e, 0) for e in ESTADOS)
        for f in fabricaciones:
            piezas_por_estado[f["estado"]] = piezas_por_estado.get(f["estado"], 0) + f["piezas"]
        jornadas = len(recolecciones)

        # PET por mes (todos los meses entre el primero y el último, aunque estén vacíos)
        por_mes = OrderedDict()
        fechas = sorted(r["fecha"] for r in recolecciones if r["fecha"])
        if fechas:
            y, m = fechas[0].year, fechas[0].month
            while (y, m) <= (fechas[-1].year, fechas[-1].month):
                por_mes[(y, m)] = 0.0
                y, m = (y + 1, 1) if m == 12 else (y, m + 1)
            for r in recolecciones:
                if r["fecha"]:
                    por_mes[(r["fecha"].year, r["fecha"].month)] += r["pet"]
        pet_por_mes = [(f"{MESES[m - 1]} {y}", v) for (y, m), v in por_mes.items()]

        pet_por_lugar = defaultdict(float)
        for r in recolecciones:
            pet_por_lugar[r["lugar"]] += r["pet"]
        pet_por_lugar = sorted(pet_por_lugar.items(), key=lambda x: -x[1])

        piezas_por_modelo = defaultdict(int)
        for f in fabricaciones:
            piezas_por_modelo[f["modelo"]] += f["piezas"]
        piezas_por_modelo = sorted(piezas_por_modelo.items(), key=lambda x: -x[1])

        ranking = []
        for puesto, (nombre, pet, jorn, bot) in enumerate(crudos["ranking"], start=1):
            ranking.append({"puesto": puesto, "nombre": nombre, "pet": _f(pet), "jornadas": _i(jorn),
                            "botellas": _i(bot), "puntos": int(round(_f(pet) * 100)),
                            "participacion": _pct(_f(pet), pet_total)})

        todas_fechas = [x["fecha"] for x in recolecciones + producciones + fabricaciones if x["fecha"]]
        resumen = {
            "pet_recolectado": pet_total,
            "filamento_producido": filamento,
            "desperdicio": desperdicio,
            "objetos_impresos": _i(k["objetos_impresos"]),
            "responsables": _i(k["responsables"]),
            "botellas": _i(k["botellas"]),
            "jornadas": jornadas,
            "pet_transformado": pet_transformado,
            "pet_pendiente": max(pet_total - pet_transformado, 0.0),
            "rendimiento": _pct(filamento, pet_transformado),
            "tasa_desperdicio": _pct(desperdicio, pet_transformado),
            "filamento_usado": filamento_usado,
            "filamento_disponible": max(filamento - filamento_usado, 0.0),
            "metros": sum(p["metros"] for p in producciones),
            "piezas": piezas_total,
            "tasa_exito": _pct(piezas_por_estado.get("Finalizado", 0), piezas_total),
            "horas_impresion": sum(f["tiempo_min"] for f in fabricaciones) / 60.0,
            "pet_por_jornada": pet_total / jornadas if jornadas else 0.0,
            "botellas_por_kg": _i(k["botellas"]) / pet_total if pet_total else 0.0,
        }

        modelo = {
            "resumen": resumen,
            "periodo": (min(todas_fechas), max(todas_fechas)) if todas_fechas else None,
            "pet_por_mes": pet_por_mes,
            "pet_por_lugar": pet_por_lugar,
            "piezas_por_estado": list(piezas_por_estado.items()),
            "piezas_por_modelo": piezas_por_modelo,
            "ranking": ranking,
            "recolecciones": recolecciones,
            "producciones": producciones,
            "fabricaciones": fabricaciones,
        }
        modelo["hallazgos"] = ServicioInforme.hallazgos(modelo)
        return modelo

    @staticmethod
    def hallazgos(modelo):
        """Frases de lectura rápida a partir de las estadísticas."""
        from servicios.informe_html import num as n
        r = modelo["resumen"]
        out = []
        if r["pet_recolectado"] > 0:
            out.append(f"Se han recolectado {n(r['pet_recolectado'])} kg de PET ({n(r['botellas'], 0)} botellas) "
                       f"en {r['jornadas']} jornada(s), un promedio de {n(r['pet_por_jornada'])} kg por jornada.")
        if modelo["pet_por_lugar"]:
            lugar, kg = modelo["pet_por_lugar"][0]
            out.append(f"{lugar} es el lugar con más PET aportado: {n(kg)} kg "
                       f"({n(_pct(kg, r['pet_recolectado']), 0)}% del total).")
        if modelo["ranking"] and modelo["ranking"][0]["pet"] > 0:
            top = modelo["ranking"][0]
            out.append(f"{top['nombre']} lidera el ranking de participación con {n(top['pet'])} kg "
                       f"y {n(top['puntos'], 0)} puntos.")
        if r["pet_transformado"] > 0:
            out.append(f"La extrusión convirtió {n(r['pet_transformado'])} kg de PET en {n(r['filamento_producido'])} kg "
                       f"de filamento: rendimiento del {n(r['rendimiento'], 1)}% y desperdicio del {n(r['tasa_desperdicio'], 1)}%.")
        if r["pet_pendiente"] > 0:
            out.append(f"Quedan {n(r['pet_pendiente'])} kg de PET recolectado pendientes de transformar.")
        if r["piezas"] > 0:
            out.append(f"Se imprimieron {r['piezas']} pieza(s) usando {n(r['filamento_usado'])} kg de filamento "
                       f"({n(r['horas_impresion'], 1)} h de impresión); tasa de éxito del {n(r['tasa_exito'], 0)}%.")
        for p in modelo["producciones"]:
            if p["disponible"] < -0.0005:
                out.append(f"Atención: la producción #{p['id']} registra {n(p['usado'])} kg de filamento usado en "
                           f"impresiones pero solo produjo {n(p['obtenido'])} kg. Conviene revisar esos registros.")
        if r["filamento_producido"] > 0:
            out.append(f"Hay {n(r['filamento_disponible'])} kg de filamento disponible para nuevas impresiones.")
        return out

    # --- 3. Orquestación -----------------------------------------------------
    def generar(self, usuario=None, progreso=None, carpeta=None):
        """Genera el PDF y lo guarda en Descargas (o `carpeta`). Devuelve la ruta.

        `progreso(paso, total, texto)` se llama al empezar cada etapa (desde el
        hilo de trabajo; la UI solo debe leerlo, no tocar widgets ahí).
        """
        def etapa(i):
            if progreso:
                progreso(i, len(self.ETAPAS), self.ETAPAS[i])

        etapa(0)
        crudos = self.recopilar()
        etapa(1)
        modelo = self.calcular(crudos)
        etapa(2)
        generado = datetime.now()
        html = informe_html.render(modelo, generado=generado, usuario=usuario,
                                   logo_uri=informe_html.logo_data_uri())
        etapa(3)
        destino = self.exportador.ruta_disponible(
            carpeta or self.exportador.carpeta_descargas(),
            f"Informe_VorTrack_{generado:%Y-%m-%d_%H%M}.pdf")
        self.exportador.html_a_pdf(html, destino)
        if progreso:
            progreso(len(self.ETAPAS), len(self.ETAPAS), "¡Informe listo!")
        return destino
