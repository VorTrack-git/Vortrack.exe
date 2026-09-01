# VorTrack

Aplicación de escritorio (Python + Tkinter / customtkinter) para el seguimiento
del reciclaje de PET → producción de filamento 3D → impresión de material
didáctico, respaldada por Microsoft SQL Server.

## Cómo ejecutar

Desde la raíz del proyecto:

```bash
python app.py
```

## Configuración de la base de datos

1. Copia la plantilla y complétala con tus datos de conexión:
   ```bash
   cp db_config.example.ini db_config.ini
   ```
2. Edita `db_config.ini` (server, database, username, password). Este archivo
   **no se versiona** (está en `.gitignore`).

Para sembrar los catálogos base y el usuario administrador:

```bash
python scripts/seed_datos.py
python scripts/seed_usuario.py
```

## Estructura del proyecto

| Carpeta | Contenido |
|---|---|
| `app.py`, `contenedor.py` | Punto de entrada y raíz de composición |
| `datos/` | Repositorios y conexión a SQL Server (capa de datos) |
| `servicios/` | Lógica de negocio (auth, proyecciones, validaciones) |
| `interfaz/` | Pantallas y utilidades de interfaz |
| `pruebas/` | `pruebas_humo.py` (contra la BD) y `pruebas_servicios.py` (lógica pura) |
| `scripts/` | Semillas de datos (`seed_*.py`) |
| `recursos/logos/` | Imágenes (íconos y logo) |
| `docs/` | Documentación (`ARQUITECTURA.md`) |
| `DB/` | Respaldo de la base (`.bacpac`) |
| `maquetas_html/` | Mockups HTML de cada pantalla |

Ver [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) para el detalle de las capas y
la inyección de dependencias.

## Pruebas

```bash
python pruebas/pruebas_servicios.py   # lógica pura, sin BD
python pruebas/pruebas_humo.py        # CRUD contra la BD real (datos temporales)
```
