"""
servicio_proyeccion.py
Servicio de proyecciones/predicciones de producción.

Centraliza la lógica de cálculo que hoy está embebida en la UI:
  - Impresión: a partir de los estimados de un modelo y una cantidad, proyecta
    el peso de filamento (g) y el tiempo (min).
  - Histórico: dado un filamento producido (kg), cuántas piezas de cada modelo
    alcanzan a hacerse, el sobrante y el tiempo total.

Unidades: modelos en horas y gramos; filamento producido en kg.
"""


class ServicioProyeccion:
    @staticmethod
    def proyeccion_impresion(tiempo_estimado_h, peso_estimado_g, cantidad):
        """Devuelve (peso_total_g, tiempo_total_min). Cada uno es None si falta
        el estimado correspondiente en el modelo."""
        try:
            cantidad = int(cantidad)
        except (TypeError, ValueError):
            cantidad = 1
        if cantidad <= 0:
            cantidad = 1
        peso_total = float(peso_estimado_g) * cantidad if peso_estimado_g is not None else None
        tiempo_min = (int(round(float(tiempo_estimado_h) * 60 * cantidad))
                      if tiempo_estimado_h is not None else None)
        return peso_total, tiempo_min

    @staticmethod
    def piezas_por_filamento(peso_kg, modelos):
        """`modelos`: iterable de (id, nombre, categoria, tiempo_h, peso_g).

        Devuelve (filas, mejor, disponible_g) donde:
          - filas: [(nombre, piezas|None, g_pieza|None, sobrante_g|None, tiempo_total_h|None), ...]
          - mejor: (nombre, piezas, sobrante_g) del modelo con más piezas, o None.
          - disponible_g: gramos disponibles de filamento.
        """
        disponible_g = float(peso_kg) * 1000.0
        filas = []
        mejor = None
        for _id, nombre, _cat, tiempo_h, peso_g in modelos:
            if not peso_g or float(peso_g) <= 0:
                filas.append((nombre, None, None, None, None))
                continue
            pg = float(peso_g)
            piezas = int(disponible_g // pg)
            sobrante = disponible_g - piezas * pg
            tiempo_total = float(tiempo_h) * piezas if tiempo_h else None
            filas.append((nombre, piezas, pg, sobrante, tiempo_total))
            if mejor is None or piezas > mejor[1]:
                mejor = (nombre, piezas, sobrante)
        return filas, mejor, disponible_g
