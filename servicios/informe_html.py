"""
informe_html.py
Maqueta HTML del informe PDF de VorTrack (A4, lista para imprimir).

`render(modelo)` recibe el diccionario de `ServicioInforme.calcular()` y
devuelve un documento HTML autocontenido: estilos en línea, logo en base64 y
gráficos dibujados en SVG (no depende de internet ni de librerías externas).
"""

import base64
import html
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LOGO = RAIZ / "recursos" / "logos" / "VorTrack icon.png"

# Paleta para papel (fondo blanco): tonos de la marca VorTrack con contraste de impresión.
C = {
    "navy": "#071a2e", "navy2": "#0d2a47", "tinta": "#13263a", "suave": "#5b6b7c",
    "linea": "#dbe4ec", "fondo": "#f4f8fb", "cian": "#00a6b8", "cian_claro": "#7df4ff",
    "azul": "#0056fd", "verde": "#1f9d55", "ambar": "#d99a00", "rojo": "#d64545",
}
COLOR_ESTADO = {"Finalizado": C["verde"], "En proceso": C["ambar"], "Fallido": C["rojo"]}
SERIE = [C["cian"], C["azul"], C["navy2"], "#4fb3c8", "#7a9cc6", "#9aa9b8"]


# --- Formato -----------------------------------------------------------------
def esc(v):
    return html.escape(str(v)) if v is not None else ""


def num(x, dec=2):
    """Número con formato español: 1.234,56"""
    s = f"{x:,.{dec}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def ent(x):
    return num(x, 0)


def fecha(d):
    return f"{d:%d/%m/%Y}" if d else "—"


def minutos(m):
    h, mm = divmod(int(m), 60)
    return f"{h} h {mm:02d} min" if h else f"{mm} min"


def logo_data_uri():
    try:
        return "data:image/png;base64," + base64.b64encode(LOGO.read_bytes()).decode("ascii")
    except OSError:
        return None


# --- Gráficos SVG --------------------------------------------------------------
def _vacio(texto="Sin datos registrados todavía."):
    return f'<div class="vacio">{esc(texto)}</div>'


def svg_barras_h(items, unidad="kg", dec=2, color=C["cian"], max_items=8):
    """Barras horizontales: etiqueta · barra · valor."""
    items = [(e, v) for e, v in items if v > 0][:max_items]
    if not items:
        return _vacio()
    ancho, eti, val, alto_fila = 380, 112, 74, 28
    maximo = max(v for _, v in items)
    util = ancho - eti - val
    h = len(items) * alto_fila + 6
    partes = [f'<svg viewBox="0 0 {ancho} {h}" class="grafico" role="img">']
    for i, (e, v) in enumerate(items):
        y = i * alto_fila + 4
        w = max(util * v / maximo, 3)
        texto = e if len(e) <= 18 else e[:17] + "…"
        partes.append(
            f'<text x="{eti - 10}" y="{y + 16}" text-anchor="end" class="eje">{esc(texto)}</text>'
            f'<rect x="{eti}" y="{y + 3}" width="{util:.1f}" height="18" rx="4" fill="{C["fondo"]}"/>'
            f'<rect x="{eti}" y="{y + 3}" width="{w:.1f}" height="18" rx="4" fill="{color}"/>'
            f'<text x="{eti + w + 8:.1f}" y="{y + 16}" class="valor">{num(v, dec)} {esc(unidad)}</text>')
    partes.append("</svg>")
    return "".join(partes)


def svg_columnas(items, unidad="kg", color=C["azul"]):
    """Columnas verticales con líneas guía (p. ej. PET por mes)."""
    if not items or not any(v > 0 for _, v in items):
        return _vacio()
    items = items[-12:]
    ancho, alto, izq, abajo, arriba = 380, 200, 36, 28, 20
    maximo = max(v for _, v in items) or 1
    util_h = alto - abajo - arriba
    paso = (ancho - izq - 10) / len(items)
    bw = min(paso * 0.58, 44)
    partes = [f'<svg viewBox="0 0 {ancho} {alto}" class="grafico" role="img">']
    for g in range(5):
        y = arriba + util_h * g / 4
        partes.append(f'<line x1="{izq}" y1="{y:.1f}" x2="{ancho - 6}" y2="{y:.1f}" class="guia"/>'
                      f'<text x="{izq - 6}" y="{y + 4:.1f}" text-anchor="end" class="eje">{num(maximo * (4 - g) / 4, 1)}</text>')
    for i, (e, v) in enumerate(items):
        x = izq + paso * i + (paso - bw) / 2
        h = util_h * v / maximo
        y = arriba + util_h - h
        partes.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{max(h, 0.5):.1f}" rx="4" fill="{color}"/>'
            f'<text x="{x + bw / 2:.1f}" y="{alto - abajo + 16}" text-anchor="middle" class="eje">{esc(e)}</text>')
        if v > 0:
            partes.append(f'<text x="{x + bw / 2:.1f}" y="{y - 6:.1f}" text-anchor="middle" class="valor">{num(v, 1)}</text>')
    partes.append(f'<text x="4" y="12" class="eje">{esc(unidad)}</text></svg>')
    return "".join(partes)


def svg_dona(items, centro_valor, centro_texto):
    """Dona con leyenda. `items`: [(etiqueta, valor, color)]."""
    total = sum(v for _, v, _ in items)
    if total <= 0:
        return _vacio()
    import math
    r, grosor, cx, cy = 70, 26, 90, 90
    partes = [f'<div class="dona"><svg viewBox="0 0 180 180" width="170" height="170" role="img">',
              f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{C["fondo"]}" stroke-width="{grosor}"/>']
    circ = 2 * math.pi * r
    inicio = 0.0
    for _, v, color in items:
        if v <= 0:
            continue
        largo = circ * v / total
        partes.append(
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="{grosor}" '
            f'stroke-dasharray="{largo:.2f} {circ - largo:.2f}" stroke-dashoffset="{-inicio:.2f}" '
            f'transform="rotate(-90 {cx} {cy})"/>')
        inicio += largo
    partes.append(f'<text x="{cx}" y="{cy + 2}" text-anchor="middle" class="dona-num">{esc(centro_valor)}</text>'
                  f'<text x="{cx}" y="{cy + 20}" text-anchor="middle" class="eje">{esc(centro_texto)}</text></svg><ul class="leyenda">')
    for e, v, color in items:
        partes.append(f'<li><span class="punto" style="background:{color}"></span>{esc(e)}'
                      f'<b>{ent(v)}</b><small>{num(100 * v / total, 0)}%</small></li>')
    partes.append("</ul></div>")
    return "".join(partes)


def html_embudo(etapas):
    """Flujo del material: barras proporcionales a la primera etapa."""
    base = etapas[0][1] if etapas and etapas[0][1] > 0 else max((v for _, v, _ in etapas), default=0)
    if base <= 0:
        return _vacio()
    filas = []
    for etiqueta, v, color in etapas:
        ancho = max(100 * v / base, 1.5) if v > 0 else 0
        filas.append(
            f'<div class="embudo-fila"><div class="embudo-eti">{esc(etiqueta)}</div>'
            f'<div class="embudo-pista"><div class="embudo-barra" style="width:{min(ancho, 100):.1f}%;background:{color}"></div></div>'
            f'<div class="embudo-val"><b>{num(v)} kg</b><small>{num(100 * v / base, 0)}%</small></div></div>')
    return "".join(filas)


# --- Bloques de contenido --------------------------------------------------------
def _kpi(valor, unidad, titulo, acento):
    return (f'<div class="kpi" style="border-left-color:{acento}"><div class="kpi-valor">{valor}'
            f'<span>{esc(unidad)}</span></div><div class="kpi-titulo">{esc(titulo)}</div></div>')


def _mini(valor, titulo):
    return f'<div class="mini"><b>{valor}</b><span>{esc(titulo)}</span></div>'


def _medalla(puesto):
    colores = {1: "#e3b341", 2: "#a9b4c0", 3: "#c98a4b"}
    color = colores.get(puesto)
    if color:
        return f'<span class="medalla" style="background:{color}">{puesto}</span>'
    return f'<span class="medalla medalla-n">{puesto}</span>'


def _estado(e):
    color = COLOR_ESTADO.get(e, C["suave"])
    return f'<span class="estado" style="color:{color};border-color:{color}">{esc(e)}</span>'


def _disponible(kg):
    if kg < -0.0005:
        return f'<b class="alerta" title="Se usó más filamento del producido">{num(kg)} ⚠</b>'
    return f"<b>{num(kg)}</b>"


def _tabla(columnas, filas, pie=None, vacio="Sin registros."):
    """`columnas`: [(título, clase)] — clase 'n' alinea a la derecha (números)."""
    if not filas:
        return _vacio(vacio)
    cab = "".join(f'<th class="{cl}">{esc(t)}</th>' for t, cl in columnas)
    cuerpo = "".join("<tr>" + "".join(f'<td class="{cl}">{v}</td>' for (_, cl), v in zip(columnas, f)) + "</tr>"
                     for f in filas)
    tpie = ("<tfoot><tr>" + "".join(f'<td class="{cl}">{v}</td>' for (_, cl), v in zip(columnas, pie)) + "</tr></tfoot>") if pie else ""
    return f'<table><thead><tr>{cab}</tr></thead><tbody>{cuerpo}</tbody>{tpie}</table>'


# --- Documento ---------------------------------------------------------------------
def render(modelo, generado, usuario=None, logo_uri=None):
    r = modelo["resumen"]
    nombre_usuario = ""
    if usuario:
        nombre_usuario = f"{usuario.get('nombres', '')} {usuario.get('apellidos', '')}".strip() or usuario.get("username", "")
    periodo = modelo["periodo"]
    periodo_txt = f"{fecha(periodo[0])} – {fecha(periodo[1])}" if periodo else "Sin registros"

    kpis = "".join([
        _kpi(num(r["pet_recolectado"]), "kg", "PET recolectado", C["cian"]),
        _kpi(num(r["filamento_producido"]), "kg", "Filamento producido", C["azul"]),
        _kpi(num(r["desperdicio"]), "kg", "Desperdicio de extrusión", C["rojo"]),
        _kpi(ent(r["objetos_impresos"]), "piezas", "Objetos impresos", C["verde"]),
        _kpi(ent(r["botellas"]), "", "Botellas recolectadas", C["navy2"]),
        _kpi(ent(r["responsables"]), "", "Responsables", C["ambar"]),
    ])
    minis = "".join([
        _mini(f"{num(r['rendimiento'], 1)}%", "Rendimiento de extrusión"),
        _mini(f"{num(r['tasa_exito'], 0)}%", "Éxito en impresión"),
        _mini(f"{num(r['pet_por_jornada'])} kg", "PET promedio por jornada"),
        _mini(f"{num(r['botellas_por_kg'], 0)}", "Botellas por kg de PET"),
        _mini(f"{num(r['filamento_disponible'])} kg", "Filamento disponible"),
        _mini(f"{num(r['horas_impresion'], 1)} h", "Horas de impresión"),
        _mini(f"{num(r['metros'], 0)} m", "Metros de filamento"),
        _mini(ent(r["jornadas"]), "Jornadas de recolección"),
    ])
    hallazgos = "".join(f"<li>{esc(h)}</li>" for h in modelo["hallazgos"]) or "<li>Aún no hay datos suficientes.</li>"

    embudo = html_embudo([
        ("PET recolectado", r["pet_recolectado"], C["cian"]),
        ("PET transformado", r["pet_transformado"], "#33b9c8"),
        ("Filamento producido", r["filamento_producido"], C["azul"]),
        ("Filamento usado en impresión", r["filamento_usado"], C["navy2"]),
    ])

    ranking = _tabla(
        [("Puesto", "c"), ("Estudiante / responsable", ""), ("PET (kg)", "n"), ("% del total", ""),
         ("Jornadas", "n"), ("Botellas", "n"), ("Puntos", "n")],
        [(_medalla(x["puesto"]), esc(x["nombre"]), num(x["pet"]),
          f'<div class="pct"><div style="width:{min(x["participacion"], 100):.1f}%"></div><span>{num(x["participacion"], 1)}%</span></div>',
          ent(x["jornadas"]), ent(x["botellas"]), f'<b>{ent(x["puntos"])}</b>') for x in modelo["ranking"]],
        vacio="No hay responsables registrados.")

    prods = modelo["producciones"]
    produccion = _tabla(
        [("#", "c"), ("Fecha", ""), ("Jornada", "c"), ("Color", ""), ("Ø mm", "n"), ("PET (kg)", "n"),
         ("Filamento (kg)", "n"), ("Rendim.", "n"), ("Usado (kg)", "n"), ("Disponible (kg)", "n"), ("Metros", "n")],
        [(f"#{p['id']}", fecha(p["fecha"]), f"#{p['jornada']}" if p["jornada"] else "—", esc(p["color"]),
          num(p["diametro"]) if p["diametro"] is not None else "—", num(p["pet"]), num(p["obtenido"]),
          f"{num(p['rendimiento'], 1)}%", num(p["usado"]), _disponible(p["disponible"]), num(p["metros"], 0))
         for p in prods],
        pie=["", "<b>Total</b>", "", "", "", num(sum(p["pet"] for p in prods)), num(sum(p["obtenido"] for p in prods)),
             f"{num(r['rendimiento'], 1)}%", num(sum(p["usado"] for p in prods)),
             f"<b>{num(sum(p['disponible'] for p in prods))}</b>", num(r["metros"], 0)] if prods else None,
        vacio="No hay producciones de filamento registradas.")

    fabs = modelo["fabricaciones"]
    impresiones = _tabla(
        [("#", "c"), ("Fecha", ""), ("Modelo", ""), ("Filamento", "c"), ("Piezas", "n"),
         ("Peso (g)", "n"), ("Tiempo", "n"), ("Estado", "c")],
        [(f"#{f['id']}", fecha(f["fecha"]), esc(f["modelo"]), f"#{f['id_prod']}" if f["id_prod"] else "—",
          ent(f["piezas"]), num(f["peso_g"], 1), minutos(f["tiempo_min"]), _estado(f["estado"])) for f in fabs],
        pie=["", "<b>Total</b>", "", "", ent(r["piezas"]), num(sum(f["peso_g"] for f in fabs), 1),
             minutos(sum(f["tiempo_min"] for f in fabs)), ""] if fabs else None,
        vacio="No hay impresiones registradas.")

    recs = modelo["recolecciones"]
    recolecciones = _tabla(
        [("#", "c"), ("Fecha", ""), ("Responsable", ""), ("Lugar", ""), ("Botellas", "n"), ("PET (kg)", "n"), ("Observaciones", "obs")],
        [(f"#{x['id']}", fecha(x["fecha"]), esc(x["responsable"]), esc(x["lugar"]), ent(x["botellas"]),
          num(x["pet"]), esc(x["obs"]) or "—") for x in recs],
        pie=["", "<b>Total</b>", "", "", ent(sum(x["botellas"] for x in recs)), num(r["pet_recolectado"]), ""] if recs else None,
        vacio="No hay jornadas de recolección registradas.")

    dona = svg_dona([(e, v, COLOR_ESTADO.get(e, C["suave"])) for e, v in modelo["piezas_por_estado"]],
                    ent(r["piezas"]), "piezas")
    logo = f'<img src="{logo_uri}" alt="">' if logo_uri else ""

    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Informe VorTrack {generado:%d/%m/%Y}</title>
<style>{_CSS}</style></head>
<body>
<header class="portada">
  <div class="marca">{logo}<div><div class="marca-nombre">VorTrack</div>
    <div class="marca-sub">Trazabilidad PET → filamento 3D → material didáctico</div></div></div>
  <div class="portada-titulo">Informe de gestión y trazabilidad</div>
  <div class="meta">
    <div><span>Generado</span><b>{generado:%d/%m/%Y · %H:%M}</b></div>
    <div><span>Periodo de datos</span><b>{periodo_txt}</b></div>
    {f'<div><span>Generado por</span><b>{esc(nombre_usuario)}</b></div>' if nombre_usuario else ''}
    <div><span>Institución</span><b>Instituto San Carlos de La Salle · TRANSORE ISC</b></div>
  </div>
</header>

<section>
  <h2>Resumen ejecutivo</h2>
  <div class="kpis">{kpis}</div>
  <div class="minis">{minis}</div>
</section>

<section class="bloque">
  <h2>Hallazgos clave</h2>
  <ul class="hallazgos">{hallazgos}</ul>
</section>

<section class="bloque">
  <h2>Flujo del material</h2>
  <p class="nota">Cuánto del PET recolectado avanza en cada etapa de la cadena (porcentaje respecto al PET recolectado).</p>
  <div class="panel">{embudo}</div>
</section>

<section class="dos-col bloque">
  <div class="panel"><h3>PET recolectado por mes</h3>{svg_columnas(modelo["pet_por_mes"])}</div>
  <div class="panel"><h3>PET por lugar de recolección</h3>{svg_barras_h(modelo["pet_por_lugar"])}</div>
</section>

<section class="bloque">
  <h2>Participación de estudiantes</h2>
  <p class="nota">Gamificación: 100 puntos por cada kg de PET aportado.</p>
  {ranking}
</section>

<section class="dos-col bloque">
  <div class="panel"><h3>Piezas por estado</h3>{dona}</div>
  <div class="panel"><h3>Piezas impresas por modelo</h3>{svg_barras_h(modelo["piezas_por_modelo"], unidad="pzs", dec=0, color=C["verde"])}</div>
</section>

<section>
  <h2>Producción de filamento</h2>
  <p class="nota">Rendimiento = filamento obtenido ÷ PET de la jornada. Usado/Disponible según las impresiones registradas con cada producción.</p>
  {produccion}
</section>

<section>
  <h2>Impresiones 3D</h2>
  {impresiones}
</section>

<section>
  <h2>Detalle de jornadas de recolección</h2>
  {recolecciones}
</section>

<footer class="cierre">Documento generado automáticamente por VorTrack a partir de la base de datos
  <b>vortrack_db</b> el {generado:%d/%m/%Y a las %H:%M}. Las cifras reflejan los registros existentes en ese momento.</footer>
</body></html>"""


_CSS = f"""
@page {{
  size: A4; margin: 15mm 13mm 17mm;
  @bottom-left {{ content: "VorTrack · Informe de gestión y trazabilidad"; font: 8pt 'Segoe UI', sans-serif; color: {C['suave']}; }}
  @bottom-right {{ content: "Página " counter(page) " de " counter(pages); font: 8pt 'Segoe UI', sans-serif; color: {C['suave']}; }}
}}
* {{ box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
b {{ font-weight: 700; }}
body {{ margin: 0; font: 10pt/1.45 'Segoe UI', Roboto, Arial, sans-serif; color: {C['tinta']}; background: #fff; }}
h2 {{ font-size: 14pt; color: {C['navy']}; margin: 22px 0 10px; display: flex; align-items: center; gap: 8px; }}
h2::before {{ content: ""; width: 5px; height: 18px; border-radius: 3px; background: {C['cian']}; }}
h3 {{ font-size: 10.5pt; margin: 0 0 10px; color: {C['navy']}; }}
.nota {{ margin: -4px 0 10px; color: {C['suave']}; font-size: 8.5pt; }}
.bloque, .panel, .kpi, .mini {{ break-inside: avoid; }}
.salto {{ break-before: page; }}
.salto h2 {{ margin-top: 0; }}

.portada {{ background: linear-gradient(135deg, {C['navy']} 0%, {C['navy2']} 100%); color: #fff;
  border-radius: 14px; padding: 22px 26px; position: relative; overflow: hidden; }}
.portada::after {{ content: ""; position: absolute; right: -60px; top: -60px; width: 220px; height: 220px;
  border-radius: 50%; border: 28px solid rgba(125,244,255,.10); }}
.marca {{ display: flex; align-items: center; gap: 12px; }}
.marca img {{ width: 46px; height: 46px; }}
.marca-nombre {{ font-size: 22pt; font-weight: 700; color: {C['cian_claro']}; line-height: 1; }}
.marca-sub {{ font-size: 8.5pt; color: #b9cacb; margin-top: 3px; }}
.portada-titulo {{ font-size: 19pt; font-weight: 700; margin: 18px 0 14px; }}
.meta {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px 24px; }}
.meta span {{ display: block; font-size: 7.5pt; text-transform: uppercase; letter-spacing: .06em; color: #8fb3c9; }}
.meta b {{ font-size: 9.5pt; font-weight: 600; }}

.kpis {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }}
.kpi {{ border: 1px solid {C['linea']}; border-left: 5px solid; border-radius: 10px; padding: 10px 14px; background: #fff; }}
.kpi-valor {{ font-size: 19pt; font-weight: 700; color: {C['navy']}; line-height: 1.15; }}
.kpi-valor span {{ font-size: 9pt; font-weight: 600; color: {C['suave']}; margin-left: 4px; }}
.kpi-titulo {{ font-size: 8.5pt; color: {C['suave']}; }}
.minis {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 10px; }}
.mini {{ background: {C['fondo']}; border-radius: 8px; padding: 8px 10px; }}
.mini b {{ display: block; font-size: 12pt; color: {C['navy']}; }}
.mini span {{ font-size: 7.8pt; color: {C['suave']}; }}

.hallazgos {{ margin: 0; padding: 12px 16px 12px 32px; background: {C['fondo']}; border-radius: 10px; border: 1px solid {C['linea']}; }}
.hallazgos li {{ margin: 3px 0; }}
.hallazgos li::marker {{ color: {C['cian']}; }}

.panel {{ border: 1px solid {C['linea']}; border-radius: 10px; padding: 12px 14px; background: #fff; }}
.dos-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }}
.grafico {{ width: 100%; height: auto; display: block; }}
.grafico .eje {{ font-size: 10px; fill: {C['suave']}; }}
.grafico .valor {{ font-size: 10px; font-weight: 700; fill: {C['tinta']}; }}
.grafico .guia {{ stroke: {C['linea']}; stroke-width: 1; }}
.vacio {{ padding: 18px; text-align: center; color: {C['suave']}; background: {C['fondo']}; border-radius: 8px; font-size: 9pt; }}

.embudo-fila {{ display: grid; grid-template-columns: 190px 1fr 110px; align-items: center; gap: 10px; margin: 7px 0; }}
.embudo-eti {{ font-weight: 600; font-size: 9pt; }}
.embudo-pista {{ background: {C['fondo']}; border-radius: 6px; height: 20px; }}
.embudo-barra {{ height: 100%; border-radius: 6px; }}
.embudo-val b {{ font-size: 9.5pt; }}
.embudo-val small {{ color: {C['suave']}; margin-left: 6px; }}

.dona {{ display: flex; align-items: center; gap: 14px; }}
.dona-num {{ font-size: 24px; font-weight: 700; fill: {C['navy']}; }}
.leyenda {{ list-style: none; margin: 0; padding: 0; flex: 1; }}
.leyenda li {{ display: flex; align-items: center; gap: 8px; padding: 5px 0; border-bottom: 1px solid {C['linea']}; font-size: 9pt; }}
.leyenda b {{ margin-left: auto; }}
.leyenda small {{ color: {C['suave']}; width: 34px; text-align: right; }}
.punto {{ width: 10px; height: 10px; border-radius: 3px; }}

table {{ width: 100%; border-collapse: collapse; font-size: 8.6pt; }}
thead th {{ background: {C['navy']}; color: #fff; font-weight: 600; padding: 7px 8px; text-align: left; }}
thead th:first-child {{ border-top-left-radius: 8px; }}
thead th:last-child {{ border-top-right-radius: 8px; }}
td {{ padding: 6px 8px; border-bottom: 1px solid {C['linea']}; vertical-align: middle; }}
tbody tr:nth-child(even) td {{ background: {C['fondo']}; }}
tr {{ break-inside: avoid; }}
tfoot td {{ border-top: 2px solid {C['navy']}; border-bottom: none; font-weight: 600; }}
.n {{ text-align: right; white-space: nowrap; }}
.c {{ text-align: center; }}
td.obs {{ color: {C['suave']}; max-width: 200px; }}
.medalla {{ display: inline-block; width: 22px; height: 22px; line-height: 22px; border-radius: 50%; color: #fff; font-weight: 700; text-align: center; font-size: 8.5pt; }}
.medalla-n {{ background: {C['fondo']}; color: {C['suave']}; }}
.pct {{ position: relative; background: {C['fondo']}; border-radius: 4px; height: 16px; min-width: 110px; }}
.pct div {{ height: 100%; background: {C['cian']}; border-radius: 4px; opacity: .55; }}
.pct span {{ position: absolute; left: 6px; top: 0; font-size: 8pt; line-height: 16px; font-weight: 600; }}
.estado {{ display: inline-block; border: 1px solid; border-radius: 999px; padding: 1px 9px; font-size: 7.8pt; font-weight: 600; }}
.alerta {{ color: {C['rojo']}; }}
h2, .nota {{ break-after: avoid; }}  /* el título no queda solo al pie de una página */
.cierre {{ margin-top: 24px; padding-top: 10px; border-top: 1px solid {C['linea']}; font-size: 8pt; color: {C['suave']}; }}
"""
