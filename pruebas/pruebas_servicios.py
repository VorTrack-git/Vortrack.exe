"""
pruebas_servicios.py
Pruebas unitarias de la capa de servicios y validaciones. No tocan la base de
datos: verifican solo lógica pura (proyección de producción y validadores).

Uso:  python pruebas_servicios.py
"""

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))

from datetime import date, datetime

from servicios import informe_html
from servicios.servicio_informe import ServicioInforme
from servicios.servicio_proyeccion import ServicioProyeccion
import servicios.validaciones as v


def _check(nombre, condicion):
    print(f"  [{'OK' if condicion else 'FALLA'}]  {nombre}")
    return bool(condicion)


def main():
    ok = True
    p = ServicioProyeccion()

    # --- Proyección de impresión: (peso_total_g, tiempo_total_min) ---
    ok &= _check("proyeccion_impresion(58, 80, 3) == (240.0, 174)  [tiempo en minutos]",
                 p.proyeccion_impresion(58, 80, 3) == (240.0, 174))
    ok &= _check("proyeccion_impresion con cantidad vacía usa 1",
                 p.proyeccion_impresion(30, 50, "") == (50.0, 30))
    ok &= _check("proyeccion_impresion sin estimados -> (None, None)",
                 p.proyeccion_impresion(None, None, 5) == (None, None))

    # --- Piezas por filamento ---
    modelos = [(1, "Tiburón", "Animales", 0.5, 80), (2, "Abeja", "Animales", 0.2, 25)]
    filas, mejor, disp = p.piezas_por_filamento(1.0, modelos)  # 1 kg = 1000 g
    ok &= _check("disponible 1.0 kg -> 1000 g", disp == 1000.0)
    ok &= _check("Tiburón: 1000//80 = 12 piezas", filas[0][1] == 12)
    ok &= _check("Abeja: 1000//25 = 40 piezas", filas[1][1] == 40)
    ok &= _check("mejor modelo es Abeja (40)", mejor[0] == "Abeja" and mejor[1] == 40)
    ok &= _check("modelo sin peso estimado -> piezas None",
                 p.piezas_por_filamento(1.0, [(9, "X", "c", 1, None)])[0][0][1] is None)

    # --- Validaciones ---
    ok &= _check("es_vacio('  ') True", v.es_vacio("  ") is True)
    ok &= _check("es_vacio('x') False", v.es_vacio("x") is False)
    ok &= _check("numero('2.5') -> (True, 2.5)", v.numero("2.5") == (True, 2.5))
    ok &= _check("numero('abc') -> (False, None)", v.numero("abc") == (False, None))
    ok &= _check("numero_positivo('0') -> ok False", v.numero_positivo("0")[0] is False)
    ok &= _check("entero_positivo('3') -> (True, 3)", v.entero_positivo("3") == (True, 3))
    ok &= _check("entero_positivo('-1') -> ok False", v.entero_positivo("-1")[0] is False)
    ok &= _check("fecha_valida('26/08/2026') True", v.fecha_valida("26/08/2026") is True)
    ok &= _check("fecha_valida('2026-08-26') True", v.fecha_valida("2026-08-26") is True)
    ok &= _check("fecha_valida('nope') False", v.fecha_valida("nope") is False)
    ok &= _check("correo_valido('a@b.com') True", v.correo_valido("a@b.com") is True)
    ok &= _check("correo_valido('a@b') False", v.correo_valido("a@b") is False)

    # --- Estadísticas del informe PDF (sin base de datos) ---
    crudos = {
        "indicadores": {"pet_recolectado": 12.0, "filamento_producido": 6.0, "desperdicio": 2.0,
                        "objetos_impresos": 7, "responsables": 2, "botellas": 300},
        "ranking": [("Ana", 10.0, 2, 250), ("Luis", 2.0, 1, 50)],
        # (IdJornada, Fecha, Responsable, Lugar, Botellas, PesoPET, Obs)
        "recolecciones": [(1, date(2026, 7, 5), "Ana", "Patio", 200, 8.0, ""),
                          (2, date(2026, 9, 1), "Luis", "Cafetería", 50, 2.0, None),
                          (3, date(2026, 9, 2), "Ana", "Patio", 50, 2.0, "x")],
        # (Id, Fecha, IdJornada, Color, Diámetro, PesoObtenido kg, Metros, Obs)
        "producciones": [(10, date(2026, 9, 3), 1, "azul", 1.75, 6.0, 100, "")],
        # (Id, Fecha, IdModelo, Modelo, IdProduccion, Cantidad, Peso g, Tiempo min, Estado)
        "fabricaciones": [(20, date(2026, 9, 4), 1, "Abeja", 10, 5, 500.0, 90, "Finalizado"),
                          (21, date(2026, 9, 5), 1, "Abeja", 10, 2, 200.0, 30, "Fallido")],
    }
    m = ServicioInforme.calcular(crudos)
    r = m["resumen"]
    ok &= _check("informe: PET transformado = PET de la jornada 1 (8 kg)", r["pet_transformado"] == 8.0)
    ok &= _check("informe: desperdicio = 8 - 6 = 2 kg", r["desperdicio"] == 2.0)
    ok &= _check("informe: rendimiento 6/8 = 75%", r["rendimiento"] == 75.0)
    ok &= _check("informe: PET pendiente de transformar 12 - 8 = 4 kg", r["pet_pendiente"] == 4.0)
    ok &= _check("informe: filamento usado 0.7 kg y disponible 5.3 kg",
                 abs(r["filamento_usado"] - 0.7) < 1e-9 and abs(r["filamento_disponible"] - 5.3) < 1e-9)
    ok &= _check("informe: tasa de éxito 5/7 piezas", abs(r["tasa_exito"] - 500 / 7) < 1e-9)
    ok &= _check("informe: horas de impresión 120 min = 2 h", r["horas_impresion"] == 2.0)
    ok &= _check("informe: PET por mes incluye meses vacíos (Jul, Ago, Sep)",
                 m["pet_por_mes"] == [("Jul 2026", 8.0), ("Ago 2026", 0.0), ("Sep 2026", 4.0)])
    ok &= _check("informe: lugar con más PET es Patio (10 kg)", m["pet_por_lugar"][0] == ("Patio", 10.0))
    ok &= _check("informe: ranking con puntos (100 por kg)", m["ranking"][0]["puntos"] == 1000)
    ok &= _check("informe: periodo 05/07/2026 – 05/09/2026",
                 m["periodo"] == (date(2026, 7, 5), date(2026, 9, 5)))
    crudos["fabricaciones"].append((22, date(2026, 9, 6), 1, "Abeja", 10, 60, 6000.0, 10, "Finalizado"))
    m2 = ServicioInforme.calcular(crudos)
    ok &= _check("informe: avisa si una producción usó más filamento del producido",
                 m2["producciones"][0]["disponible"] < 0
                 and any("#10" in h and "revisar" in h for h in m2["hallazgos"]))
    ok &= _check("informe: formato español de números", informe_html.num(1234.5) == "1.234,50")
    ok &= _check("informe: HTML se genera con los datos",
                 "Informe de gestión y trazabilidad" in informe_html.render(m, generado=datetime(2026, 9, 23, 10, 0)))

    print("\n=== TODO OK ===" if ok else "\n=== HAY FALLAS ===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
