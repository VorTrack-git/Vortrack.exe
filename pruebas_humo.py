"""
pruebas_humo.py
Prueba de humo de la capa de datos de VorTrack contra la base real.

Ejercita el CRUD de cada área (catálogos, estudiantes, recolección,
transformación, impresión, indicadores y login) usando SOLO registros
temporales que borra al final. Sirve para verificar que el comportamiento no
cambia tras cada fase del refactor a SOLID.

Uso:  python pruebas_humo.py
"""

import repositorio as R
import auth

CORREO = "smoke.test@vortrack.local"
errores = []


def check(cond, msg):
    print(("  [OK]  " if cond else "  [X]  ") + msg)
    if not cond:
        errores.append(msg)


def _pre_limpiar():
    """Borra restos de una corrida anterior fallida (best-effort)."""
    try:
        for e in R.listar_estudiantes():
            if e[3] == CORREO:
                R.eliminar_estudiante(e[0])
    except Exception:
        pass


def main():
    _pre_limpiar()

    # --- Catálogos ---
    id_lugar = R.crear_lugar("SMOKE Lugar", "temporal")
    id_modelo = R.crear_modelo("SMOKE Modelo", "temp", 2, 80)  # 2 h, 80 g/pieza
    check(any(x[0] == id_lugar for x in R.listar_lugares_admin()), "Lugares: crear + listar")
    check(any(x[0] == id_modelo for x in R.listar_modelos_admin()), "Modelos: crear + listar")

    # --- Estudiante (Usuario login + Responsable) + login ---
    id_usuario = R.crear_estudiante("Smoke", "Test", CORREO, "3000000000", "clave123")
    est = [e for e in R.listar_estudiantes() if e[3] == CORREO]
    check(len(est) == 1 and est[0][5] == "clave123", "Estudiantes: crear + contraseña visible")
    check(auth.authenticate(CORREO, "clave123") and not auth.is_admin(), "Auth: login estudiante + rol")
    auth.logout()
    resp = [r for r in R.listar_responsables() if r[1] == "Smoke Test"]
    check(len(resp) == 1, "Estudiante crea Responsable (aportante)")
    id_resp = resp[0][0]

    # --- Recolección ---
    id_jornada = R.crear_jornada("01/01/2026", id_lugar, id_resp, 10, 2.0, "temp")
    check(any(x[0] == id_jornada for x in R.recolecciones_admin()), "Recolección: crear + listar")
    R.actualizar_jornada(id_jornada, "02/01/2026", id_lugar, id_resp, 12, 2.5, "editada")
    check(float(R.obtener_jornada(id_jornada)[5]) == 2.5, "Recolección: actualizar")

    # --- Transformación ---
    id_prod = R.crear_produccion(id_jornada, "03/01/2026", "Azul", 1.75, 1.5, 400, "temp")
    check(any(x[0] == id_prod for x in R.producciones_admin()), "Transformación: crear + listar")
    R.actualizar_produccion(id_prod, id_jornada, "03/01/2026", "Rojo", 1.75, 1.4, 380, "editada")
    check(R.obtener_produccion(id_prod)[3] == "Rojo", "Transformación: actualizar")

    # --- Impresión ---
    id_fab = R.crear_fabricacion(id_modelo, id_prod, "04/01/2026", 3, 90, 120, "Finalizado")
    check(any(x[0] == id_fab for x in R.fabricaciones_admin()), "Impresión: crear + listar")
    R.actualizar_fabricacion(id_fab, id_modelo, id_prod, "04/01/2026", 5, 95, 130, "En proceso")
    check(R.obtener_fabricacion(id_fab)[4] == 5, "Impresión: actualizar")

    # --- Indicadores / ranking ---
    ind = R.indicadores_resumen()
    check(isinstance(ind, dict) and ind.get("pet_recolectado", 0) >= 2.5, "Indicadores: resumen")
    check(isinstance(R.ranking_participacion(), list), "Indicadores: ranking")

    # --- Protección de FK al eliminar ---
    try:
        R.eliminar_jornada(id_jornada)  # tiene producción -> debe bloquear
        check(False, "FK: eliminar jornada con producción NO se bloqueó")
    except Exception:
        check(True, "FK: eliminar jornada con producción se bloquea")

    # --- Limpieza (orden inverso por FKs) ---
    R.eliminar_fabricacion(id_fab)
    R.eliminar_produccion(id_prod)
    R.eliminar_jornada(id_jornada)
    R.eliminar_estudiante(id_usuario)  # borra Usuario + Responsable (sin jornadas)
    R.eliminar_lugar(id_lugar)
    R.eliminar_modelo(id_modelo)
    check(not any(e[3] == CORREO for e in R.listar_estudiantes()), "Limpieza: estudiante")
    check(not any(x[0] == id_lugar for x in R.listar_lugares_admin()), "Limpieza: lugar")

    print("\n=== TODO OK ===" if not errores else f"\n=== {len(errores)} FALLO(S) ===")
    return 0 if not errores else 1


if __name__ == "__main__":
    raise SystemExit(main())
