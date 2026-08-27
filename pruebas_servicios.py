"""
pruebas_servicios.py
Pruebas unitarias de la capa de servicios y validaciones. No tocan la base de
datos: verifican solo lógica pura (proyección de producción y validadores).

Uso:  python pruebas_servicios.py
"""

from servicio_proyeccion import ServicioProyeccion
import validaciones as v


def _check(nombre, condicion):
    print(f"  [{'OK' if condicion else 'FALLA'}]  {nombre}")
    return bool(condicion)


def main():
    ok = True
    p = ServicioProyeccion()

    # --- Proyección de impresión: (peso_total_g, tiempo_total_min) ---
    ok &= _check("proyeccion_impresion(2, 80, 3) == (240.0, 360)",
                 p.proyeccion_impresion(2, 80, 3) == (240.0, 360))
    ok &= _check("proyeccion_impresion con cantidad vacía usa 1",
                 p.proyeccion_impresion(1, 50, "") == (50.0, 60))
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

    print("\n=== TODO OK ===" if ok else "\n=== HAY FALLAS ===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
