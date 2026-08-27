# Arquitectura de VorTrack

VorTrack es una aplicación de escritorio (Tkinter / customtkinter) para el
seguimiento del reciclaje de PET → producción de filamento 3D → impresión de
material didáctico, respaldada por **Microsoft SQL Server**.

Tras el refactor SOLID, el código está organizado en **capas** con una única
dirección de dependencia (de arriba hacia abajo) y una **raíz de composición**
que arma las dependencias concretas y las inyecta en la interfaz.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  RAÍZ DE COMPOSICIÓN                                                       │
│  app.py  ─────────────  contenedor.py (Contenedor: datos + proyeccion)     │
│     │  crea Contenedor + FabricaWidgets y los inyecta en cada página       │
└─────┼──────────────────────────────────────────────────────────────────────┘
      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  PRESENTACIÓN (UI)                                                         │
│  login_ui · inicio_ui · recolec_ui · transformacion_ui · impresion_ui ·    │
│  historico_ui · admin_ui                                                   │
│  soporte de UI:  widgets (FabricaWidgets) · ui_tema · ui_imagenes ·        │
│                  ui_ventana · ui_dialogos · ui_navbar · ui_utils (fachada) │
│  depende de ▼ servicios y repos que recibe POR CONSTRUCTOR (no importa db) │
└─────┬───────────────────────────────────────┬──────────────────────────────┘
      ▼                                        ▼
┌───────────────────────────────┐   ┌──────────────────────────────────────┐
│  SERVICIOS (negocio)          │   │  DATOS (repositorios)                 │
│  servicio_auth (fachada auth) │   │  repositorio  (fachada agregada)      │
│  servicio_proyeccion          │   │     ├─ repo_usuarios                   │
│  validaciones                 │   │     ├─ repo_jornadas                   │
│  almacenamiento_sesion        │   │     ├─ repo_produccion                 │
│                               │   │     ├─ repo_fabricacion                │
│                               │   │     ├─ repo_catalogos                  │
│                               │   │     └─ repo_indicadores                │
│                               │   │  contratos: interfaces (Protocol)      │
│                               │   │  base común: repositorio_base          │
└───────────────────────────────┘   └─────────────────┬────────────────────┘
                                                       ▼
                                     ┌──────────────────────────────────────┐
                                     │  INFRAESTRUCTURA                      │
                                     │  db.py  (conexión pyodbc a SQL Server)│
                                     └──────────────────────────────────────┘
```

## Capas

### 1. Infraestructura — `db.py`
Abre la conexión a SQL Server (pyodbc, ODBC Driver 18) leyendo `db_config.ini`
(fuera del control de versiones). Es lo único que conoce el detalle de la BD.

### 2. Datos (repositorios)
Convierten operaciones de dominio en SQL. Cada repositorio tiene **una sola
responsabilidad** (SRP) y hereda de `repositorio_base.RepositorioBase`, que
aporta los helpers `_query` / `_ejecutar` / `_valor` y recibe una
`conexion_factory` **inyectable** (por defecto `db.get_connection`).

- `repo_usuarios` — login + CRUD de estudiantes.
- `repo_jornadas` — recolecciones (JornadasRecoleccion).
- `repo_produccion` — transformaciones (ProduccionFilamento).
- `repo_fabricacion` — impresiones (FabricacionObjetos).
- `repo_catalogos` — Lugares, Modelos, Responsables.
- `repo_indicadores` — resumen de KPIs y ranking.

`interfaces.py` define `Protocol`s ligeros (p. ej. `RepoJornadasProto`) para que
las capas altas dependan de **abstracciones**, no de clases concretas (DIP/ISP).

`repositorio.py` es una **fachada agregada**: expone las funciones que la UI ya
usaba y delega en las instancias de `repo_*`. Es la implementación concreta que
la raíz de composición inyecta como `datos`.

### 3. Servicios (negocio)
Lógica de aplicación, sin tocar la UI ni el SQL directamente:

- `servicio_auth.ServicioAuth` — login, sesión, roles y política de contraseñas
  (admin con hash SHA-256; estudiantes en claro para que el admin pueda verlas).
  Recibe `RepoUsuarios` inyectado. `auth.py` es su fachada.
- `almacenamiento_sesion.AlmacenamientoSesion` — "recordar usuario" en archivo
  local (separado de la lógica de login, SRP).
- `servicio_proyeccion.ServicioProyeccion` — proyecciones de producción
  (peso/tiempo de impresión; piezas posibles por filamento).
- `validaciones` — validadores reutilizables (número, entero, positivo, fecha,
  correo, requerido) que antes estaban repetidos en cada formulario.

### 4. Presentación (UI)
Cada pantalla arma su interfaz y delega:

- **Creación de widgets** → `widgets.FabricaWidgets`: centraliza en un solo lugar
  la doble rama customtkinter (`ctk`) / tkinter puro (`tk`) para label, entry,
  combo, hint, textbox, botón, tarjeta y tabla (OCP/DRY). Antes cada `*_ui.py`
  copiaba estos helpers (~120 ramas `if ctk`).
- **Persistencia** → el objeto `datos` que reciben por constructor.
- **Cálculos y validación** → `ServicioProyeccion` y `validaciones`.

El antiguo `ui_utils.py` se dividió por responsabilidad (SRP) en `ui_tema`
(paleta/tipografía), `ui_imagenes` (carga de imágenes), `ui_ventana`
(maximizar + ícono), `ui_dialogos` (diálogos, scroll, enlaces del footer) y
`ui_navbar` (navbar/footer compartidos). `ui_utils.py` quedó como **fachada**
que reexporta todo, de modo que los imports previos siguen funcionando.

### 5. Raíz de composición — `app.py` + `contenedor.py`
`Contenedor` construye una sola vez las dependencias concretas
(`datos = repositorio`, `proyeccion = ServicioProyeccion()`). `app.py` crea el
`Contenedor` y una `FabricaWidgets` compartida y los **inyecta** en cada página:

```python
_cont = Contenedor()
_fabrica = FabricaWidgets()
...
impresion_ui.ImpresionApp(root, on_navigate=..., on_logout=...,
                          datos=_cont.datos, proyeccion=_cont.proyeccion,
                          fabrica=_fabrica)
```

Es el **único** lugar que conoce las implementaciones concretas. Cada pantalla
declara esas dependencias como parámetros con un valor por defecto sensato, así
que siguen ejecutándose de forma aislada (p. ej. `python recolec_ui.py`) sin la
raíz de composición.

## Cómo fluye una dependencia (ejemplo)

`app.py` → `RecoleccionesApp(datos=_cont.datos)` → `RecoleccionesForm(datos=...)`
→ el formulario llama `self.datos.crear_jornada(...)` → la fachada `repositorio`
delega en `repo_jornadas.crear(...)` → `RepositorioBase._ejecutar` → `db`.

## Por qué se conservan las fachadas `repositorio` y `auth`

El plan inicial contemplaba eliminarlas al final. Se decidió **mantenerlas**
porque cumplen un rol legítimo de **fachada/agregado**: agrupan bajo una sola
interfaz las operaciones que la UI consume y que internamente pertenecen a
distintos `repo_*` / servicios. Son, además, la implementación concreta por
defecto que inyecta el `Contenedor`. Esto conserva el DIP (la UI depende de la
interfaz inyectada, no de módulos globales) y permite sustituir la
implementación desde un único punto sin tocar las pantallas.

## Verificación

- `python pruebas_servicios.py` — pruebas unitarias de servicios y validaciones
  (lógica pura, sin BD).
- `python pruebas_humo.py` — CRUD de cada área contra la BD real, con datos
  temporales que el propio script limpia (paridad de comportamiento).

## Principios SOLID aplicados

- **SRP** — `repositorio` dividido en `repo_*`; `ui_utils` dividido en módulos
  cohesivos; `auth` separado en login (`servicio_auth`) + "recordar usuario"
  (`almacenamiento_sesion`).
- **OCP / DRY** — `FabricaWidgets` centraliza la creación de widgets; agregar un
  estilo o una entidad ya no obliga a tocar cada `*_ui.py`.
- **DIP** — la UI recibe `datos` / `proyeccion` / `servicio_auth` por
  constructor y depende de `interfaces` (Protocol); la raíz de composición cablea
  lo concreto.
- **ISP** — los `Protocol` de `interfaces.py` son pequeños y por rol.
