"""
seed_datos.py
Siembra los catálogos base de VorTrack (Lugares, Responsables, Modelos).

Estas tablas son llaves foráneas obligatorias de las jornadas/producciones/
fabricaciones, así que sin al menos un registro los formularios no pueden
guardar. El script es idempotente: no duplica lo que ya exista.

Uso:  python seed_datos.py
"""

import db

LUGARES = [
    ("Patio principal", "Punto de acopio central"),
    ("Cafetería", "Recolección de envases de bebidas"),
    ("Laboratorio de electrónica", "Área del proyecto TRANSORE ISC"),
    ("Biblioteca", "Punto de acopio secundario"),
    ("Aulas primaria", "Recolección por cursos"),
]

RESPONSABLES = [
    ("Arnaldo Pérez", "arnaldo@sancarlos.edu", "3000000001"),
    ("Miguel Ruiz", "miguel@sancarlos.edu", "3000000002"),
    ("Juan Gómez", "juan@sancarlos.edu", "3000000003"),
    ("María López", "maria@sancarlos.edu", "3000000004"),
]

MODELOS = [
    ("Engranaje didáctico", "Mecánica", 45, 0.12),
    ("Molécula de agua (H2O)", "Química", 30, 0.05),
    ("Regla graduada", "Geometría", 25, 0.09),
    ("Sólido geométrico", "Geometría", 40, 0.10),
    ("Pieza de robótica", "Robótica", 60, 0.15),
]


def _seed(cur, tabla, col_clave, filas, sql_insert):
    creados = 0
    for fila in filas:
        clave = fila[0]
        cur.execute(f"SELECT COUNT(*) FROM {tabla} WHERE {col_clave} = ?", clave)
        if cur.fetchone()[0] == 0:
            cur.execute(sql_insert, *fila)
            creados += 1
    print(f"{tabla}: {creados} nuevo(s), {len(filas)-creados} ya existía(n).")


def main():
    try:
        conn = db.get_connection()
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] No se pudo conectar: {exc}")
        return

    cur = conn.cursor()
    _seed(cur, "Lugares", "NombreLugar", LUGARES,
          "INSERT INTO Lugares (NombreLugar, Descripcion) VALUES (?, ?)")
    _seed(cur, "Responsables", "NombreResponsable", RESPONSABLES,
          "INSERT INTO Responsables (NombreResponsable, Email, Telefono) VALUES (?, ?, ?)")
    _seed(cur, "Modelos", "Nombre", MODELOS,
          "INSERT INTO Modelos (Nombre, Categoria, TiempoEstimado, PesoEstimado) VALUES (?, ?, ?, ?)")
    conn.commit()
    conn.close()
    print("Catálogos listos.")


if __name__ == "__main__":
    main()
