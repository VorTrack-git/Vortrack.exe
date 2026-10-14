/* ============================================================
   VorTrack — réplica web para la demo.
   Cada pantalla, validación, mensaje y cálculo está portado de
   interfaz/*_ui.py, servicios/*.py y datos/repo_*.py. Los datos
   viven en el navegador (localStorage) en lugar de SQL Server.
   ============================================================ */
(() => {
'use strict';
const ROOT = document.getElementById('vtApp');
if (!ROOT) return;
const GUIDE = document.getElementById('vtGuide');
const KEY = 'vortrack-demo-v2';
const KEY_RECORDAR = 'vortrack-demo-recordar';
const MOVIL = matchMedia('(max-width:860px)');

const $ = (s, r = ROOT) => r.querySelector(s);
const $$ = (s, r = ROOT) => [...r.querySelectorAll(s)];
const esc = v => String(v ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const espera = ms => new Promise(r => setTimeout(r, ms));
const azar = (a, b) => a + Math.random() * (b - a);
const pad = n => String(n).padStart(2, '0');

/* ---------- Formatos de Python ---------- */
// f"{x:g}"
function g(x) {
  x = Number(x);
  if (!isFinite(x)) return String(x);
  if (x === 0) return '0';
  const e = Math.floor(Math.log10(Math.abs(x)));
  if (e < -4 || e >= 6) {
    const [m, ex] = x.toExponential(5).split('e');
    const n = parseInt(ex, 10);
    return m.replace(/\.?0+$/, '') + 'e' + (n < 0 ? '-' : '+') + String(Math.abs(n)).padStart(2, '0');
  }
  return String(parseFloat(x.toPrecision(6)));
}
const f2 = x => Number(x).toFixed(2);           // f"{x:.2f}"
const f0 = x => Number(x).toFixed(0);           // f"{x:.0f}"
// informe_html.num: 1.234,56
function num(x, dec = 2) {
  const neg = x < 0, [ent, frac] = Math.abs(Number(x)).toFixed(dec).split('.');
  return (neg ? '-' : '') + ent.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (frac ? ',' + frac : '');
}
const ent = x => num(x, 0);
const hoyISO = () => { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; };
const dmy = iso => { if (!iso) return ''; const [y, m, d] = iso.split('-'); return `${d}/${m}/${y}`; };

/* ---------- servicios/validaciones.py ---------- */
const RE_NUM = /^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$/;
const esVacio = t => !String(t ?? '').trim();
const numero = t => { const s = String(t ?? '').trim(); return RE_NUM.test(s) ? [true, parseFloat(s)] : [false, null]; };
const numeroPositivo = t => { const [ok, v] = numero(t); return [ok && v > 0, v]; };
const enteroPositivo = t => { const [ok, v] = numero(t); if (!ok) return [false, null]; const n = Math.trunc(v); return [n > 0, n]; };

/* ---------- Datos de ejemplo (catálogos de scripts/seed_datos.py) ---------- */
function semilla() {
  return {
    v: 2, user: null, page: 'login', hecho: {},
    responsables: [
      { id: 1, n: 'Arnaldo Pérez' }, { id: 2, n: 'Juan Gómez' }, { id: 3, n: 'María López' }, { id: 4, n: 'Miguel Ruiz' },
    ],
    lugares: [
      { id: 1, n: 'Patio principal' }, { id: 2, n: 'Cafetería' }, { id: 3, n: 'Laboratorio de electrónica' },
      { id: 4, n: 'Biblioteca' }, { id: 5, n: 'Aulas primaria' },
    ],
    // (id, nombre, categoría, tiempo estimado min, peso estimado g)
    modelos: [
      { id: 1, n: 'Engranaje didáctico', c: 'Mecánica', t: 45, g: 12 },
      { id: 2, n: 'Molécula de agua (H2O)', c: 'Química', t: 30, g: 5 },
      { id: 3, n: 'Regla graduada', c: 'Geometría', t: 25, g: 9 },
      { id: 4, n: 'Sólido geométrico', c: 'Geometría', t: 40, g: 10 },
      { id: 5, n: 'Pieza de robótica', c: 'Robótica', t: 60, g: 15 },
      { id: 6, n: 'Tiburón', c: 'Biología', t: 60, g: 52.4 },
      { id: 7, n: 'Abeja', c: 'Biología', t: 35, g: 18 },
    ],
    jornadas: [
      { id: 1, f: '2026-08-26', lug: 2, resp: 4, bot: 200, peso: 5, obs: 'Envases de gaseosa' },
      { id: 2, f: '2026-09-02', lug: 1, resp: 3, bot: 320, peso: 8.4, obs: '' },
      { id: 3, f: '2026-09-09', lug: 4, resp: 2, bot: 150, peso: 3.9, obs: '' },
      { id: 4, f: '2026-09-16', lug: 2, resp: 1, bot: 410, peso: 10.6, obs: 'Semana ambiental' },
      { id: 5, f: '2026-09-30', lug: 5, resp: 3, bot: 260, peso: 6.8, obs: '' },
      { id: 6, f: '2026-10-07', lug: 3, resp: 2, bot: 120, peso: 3.1, obs: '' },
    ],
    prods: [
      { id: 1, j: 1, f: '2026-08-27', color: 'Translúcido', diam: 1.75, peso: 3.6, m: 1080, obs: 'Buena calidad' },
      { id: 2, j: 2, f: '2026-09-04', color: 'Azul', diam: 1.75, peso: 6.1, m: 1830, obs: '' },
      { id: 3, j: 4, f: '2026-09-18', color: 'Verde', diam: 1.75, peso: 7.9, m: 2370, obs: '' },
    ],
    fabs: [
      { id: 1, mod: 6, prod: 1, f: '2026-08-29', cant: 5, peso: 262, t: 300, estado: 'Finalizado' },
      { id: 2, mod: 1, prod: 2, f: '2026-09-08', cant: 20, peso: 240, t: 900, estado: 'Finalizado' },
      { id: 3, mod: 3, prod: 2, f: '2026-09-10', cant: 10, peso: 90, t: 250, estado: 'Fallido' },
      { id: 4, mod: 2, prod: 3, f: '2026-09-22', cant: 30, peso: 150, t: 900, estado: 'Finalizado' },
      { id: 5, mod: 5, prod: 3, f: '2026-09-25', cant: 8, peso: 120, t: 480, estado: 'En proceso' },
    ],
  };
}
let S;
try { S = JSON.parse(localStorage.getItem(KEY)); } catch { S = null; }
if (!S || S.v !== 2) S = semilla();
function guardar() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch {} pintarGuia(); }
const sigId = arr => arr.reduce((m, x) => Math.max(m, x.id), 0) + 1;
const porFechaDesc = (a, b) => (b.f || '').localeCompare(a.f || '') || b.id - a.id;
const porNombre = (a, b) => a.n.localeCompare(b.n, 'es');

/* ---------- datos/repo_*.py ---------- */
const repo = {
  responsables: () => [...S.responsables].sort(porNombre),
  lugares: () => [...S.lugares].sort(porNombre),
  modelos: () => [...S.modelos].sort(porNombre),
  lugar: id => S.lugares.find(l => l.id === id),
  resp: id => S.responsables.find(r => r.id === id),
  jornada: id => S.jornadas.find(j => j.id === id),
  modelo: id => S.modelos.find(m => m.id === id),
  // RepoJornadas.listar_para_combo
  jornadasCombo: () => [...S.jornadas].sort(porFechaDesc).map(j =>
    ({ id: j.id, lab: `#${j.id} · ${dmy(j.f)} · ${repo.lugar(j.lug)?.n || 'Sin lugar'} (${g(j.peso)} kg PET)`, peso: j.peso })),
  // RepoProduccion.listar_para_combo
  prodsCombo: () => [...S.prods].sort(porFechaDesc).map(p =>
    ({ id: p.id, lab: `#${p.id} · ${p.f ? dmy(p.f) : 's/f'} · ${p.color || 'sin color'} (${g(p.peso)} kg)`, peso: p.peso })),
  // RepoIndicadores.resumen
  indicadores() {
    const pet = S.jornadas.reduce((a, j) => a + (j.peso || 0), 0);
    const filamento = S.prods.reduce((a, p) => a + (p.peso || 0), 0);
    const consumido = S.prods.reduce((a, p) => a + (repo.jornada(p.j)?.peso || 0), 0);
    return {
      pet_recolectado: pet, filamento_producido: filamento, desperdicio: Math.max(consumido - filamento, 0),
      objetos_impresos: S.fabs.reduce((a, f) => a + (f.cant || 0), 0),
      responsables: S.responsables.length,
      botellas: S.jornadas.reduce((a, j) => a + (j.bot || 0), 0),
    };
  },
  // RepoIndicadores.ranking
  ranking(limite = 10) {
    return S.responsables.map(r => {
      const js = S.jornadas.filter(j => j.resp === r.id);
      return { id: r.id, n: r.n, pet: js.reduce((a, j) => a + (j.peso || 0), 0), jornadas: js.length, bot: js.reduce((a, j) => a + (j.bot || 0), 0) };
    }).sort((a, b) => b.pet - a.pet || a.id - b.id).slice(0, limite);
  },
};

/* ---------- servicios/servicio_proyeccion.py ---------- */
const proyeccion = {
  impresion(tiempoMin, pesoG, cantidad) {
    const s = String(cantidad ?? '').trim();
    let c = /^[+-]?\d+$/.test(s) ? parseInt(s, 10) : 1;
    if (c <= 0) c = 1;
    return [pesoG != null ? pesoG * c : null, tiempoMin != null ? Math.round(tiempoMin * c) : null];
  },
  piezasPorFilamento(pesoKg, modelos) {
    const disp = pesoKg * 1000;
    const filas = []; let mejor = null;
    for (const m of modelos) {
      if (!m.g || m.g <= 0) { filas.push([m.n, null]); continue; }
      const piezas = Math.floor(disp / m.g), sobr = disp - piezas * m.g;
      const tt = m.t ? m.t * piezas : null;
      filas.push([m.n, piezas, m.g, sobr, tt]);
      if (!mejor || piezas > mejor[1]) mejor = [m.n, piezas, sobr];
    }
    return [filas, mejor, disp];
  },
};

/* ============================================================
   Ventana, páginas y transiciones (app.Navegador)
   ============================================================ */
const TITULOS = {
  login: 'VorTrack - Login', inicio: 'VorTrack - Quiénes somos', recoleccion: 'VorTrack - Recolecciones',
  transformacion: 'VorTrack - Transformación', impresion: 'VorTrack - Impresión', historico: 'VorTrack - Histórico e Informes',
};
ROOT.classList.add('vt');
ROOT.innerHTML = `<div class="vt-window">
  <div class="vt-titlebar"><img src="logo.png" alt=""><span class="t" id="vtTitle"></span>
    <span class="ctl"><span>&#x2014;</span><span>&#x25A2;</span><span>&#x2715;</span></span></div>
  <div class="vt-screen" id="vtScreen"></div></div>`;
const SCREEN = $('#vtScreen');
let navegando = false;

async function ir(destino) {
  if (navegando) return;
  if (destino !== 'login' && !S.user) destino = 'login';
  navegando = true;
  cerrarMenus();
  const vieja = $('.vt-page', SCREEN);
  const nueva = document.createElement('div');
  nueva.className = 'vt-page fade';
  SCREEN.appendChild(nueva);
  $('#vtTitle').textContent = TITULOS[destino];
  S.page = destino; guardar();
  const construir = PAGINAS[destino];
  if (MOVIL.matches) {
    vieja?.remove(); nueva.classList.remove('fade');
    const top = ROOT.getBoundingClientRect().top;
    if (top < 0) ROOT.scrollIntoView({ block: 'start' });
    construir(nueva);
  } else {
    construir(nueva);
    void nueva.offsetWidth; nueva.classList.remove('fade');
    await espera(160);
    vieja?.remove();
  }
  navegando = false;
}

function navbar(pagina) {
  const opciones = [['Recolección', 'recoleccion'], ['Transformación', 'transformacion'], ['Impresión', 'impresion']];
  return `<div class="vt-nav">
    <div class="vt-brand"><img src="icon.png" alt=""><b>VorTrack</b></div>
    <div class="vt-navitems">
      <button class="vt-navlink ${pagina === 'inicio' ? 'on' : ''}" data-go="inicio">QUIÉNES SOMOS</button>
      <div class="vt-reg"><button type="button" data-reg>REGISTRAR <svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 6.2 8 10.5l4.5-4.3" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
        <div class="panel">${opciones.map(([t, p]) => `<button type="button" class="${p === pagina ? 'act' : ''}" data-opcion="${p}">${t}</button>`).join('')}</div></div>
      <button class="vt-navlink btn" data-go="historico">HISTÓRICO INFORMES</button>
    </div>
    <button class="vt-logout" data-logout>Logout</button></div>`;
}
function footer() {
  return `<div class="vt-foot"><div class="l"><b>VorTrack</b><span>© 2026 desarrollado por Miguel Ruiz Ramirez</span></div>
    <div class="r">${['Privacidad', 'Términos de Uso', 'Contacto', 'Soporte Técnico'].map(l => `<button type="button" data-link="${l}">${l}</button>`).join('')}</div></div>`;
}
function marco(pagina, contenido) {
  return navbar(pagina) + `<div class="vt-main">${contenido}</div>` + footer();
}
function cerrarMenus() { $$('.vt-reg.open').forEach(m => m.classList.remove('open')); }

// Delegación de eventos comunes (navbar, footer)
ROOT.addEventListener('click', e => {
  const t = e.target.closest('[data-go],[data-reg],[data-opcion],[data-logout],[data-link]');
  if (!e.target.closest('.vt-reg')) cerrarMenus();
  if (!t) return;
  if (t.dataset.go) { if (t.dataset.go !== S.page) ir(t.dataset.go); return; }
  if ('reg' in t.dataset) { t.closest('.vt-reg').classList.toggle('open'); return; }
  if (t.dataset.opcion) {
    const destino = t.dataset.opcion;
    cerrarMenus();
    if (destino !== S.page) setTimeout(() => ir(destino), 200); // navega al terminar de cerrarse
    return;
  }
  if ('logout' in t.dataset) { logout(); return; }
  if (t.dataset.link) abrirEnlace(t.dataset.link);
});
document.addEventListener('keydown', e => { if (e.key === 'Escape') cerrarMenus(); });
document.addEventListener('click', e => { if (!ROOT.contains(e.target)) cerrarMenus(); });

async function logout() {
  if (await msg('q', 'Cerrar sesión', '¿Desea cerrar sesión en VorTrack?', ['Sí', 'No']) === 'Sí') {
    S.user = null; guardar(); ir('login');
  }
}

/* ---------- messagebox (tkinter → MessageBox de Windows) ---------- */
function msg(tipo, titulo, texto, botones = ['Aceptar']) {
  return new Promise(res => {
    const capa = document.createElement('div');
    capa.className = 'vt-modal';
    const ico = { info: 'i', q: '?', err: '✕', warn: '' }[tipo];
    capa.innerHTML = `<div class="vt-msg" role="alertdialog" aria-label="${esc(titulo)}">
      <div class="bar">${esc(titulo)}<span data-x>✕</span></div>
      <div class="body"><div class="ico ${tipo}">${ico}</div><div>${esc(texto)}</div></div>
      <div class="btns">${botones.map(b => `<button type="button" data-b="${b}">${b}</button>`).join('')}</div></div>`;
    (MOVIL.matches ? document.body : SCREEN).appendChild(capa);
    if (MOVIL.matches) capa.classList.add('vt');
    const fin = b => { capa.remove(); document.removeEventListener('keydown', tecla); res(b); };
    const tecla = e => { if (e.key === 'Enter') { e.preventDefault(); fin(botones[0]); } if (e.key === 'Escape') fin(botones[botones.length - 1]); };
    document.addEventListener('keydown', tecla);
    capa.addEventListener('click', e => {
      const b = e.target.closest('[data-b]'); if (b) fin(b.dataset.b);
      if (e.target.closest('[data-x]')) fin(botones[botones.length - 1]);
    });
    capa.querySelector('[data-b]').focus({ preventScroll: true });
  });
}
const aviso = (t, x) => msg('warn', t, x);
const info = (t, x) => msg('info', t, x);

/* ---------- Spinner con % (interfaz/ui_cargando.py) ---------- */
function spinner(contenedor, cargas, titulo = 'Obteniendo datos…') {
  // cargas: [mensaje, ...]; cada "consulta" termina en paralelo a su ritmo.
  return new Promise(res => {
    const total = cargas.length, R = 41, C = 2 * Math.PI * R;
    const capa = document.createElement('div');
    capa.className = 'vt-spin';
    capa.innerHTML = `<div class="box"><svg viewBox="0 0 96 96"><circle cx="48" cy="48" r="${R}" fill="none" stroke="#3b494b" stroke-width="7"/>
      <circle class="arc" cx="48" cy="48" r="${R}" fill="none" stroke="#7df4ff" stroke-width="7" stroke-dasharray="0 ${C}" transform="rotate(-90 48 48)"/>
      <text x="48" y="55" text-anchor="middle" fill="#fff" font-size="20" font-weight="700" font-family="Segoe UI,sans-serif">0%</text></svg>
      <div class="tx">${esc(titulo)}</div><div class="dt">0 de ${total} consultas listas</div></div>`;
    contenedor.appendChild(capa);
    const listas = cargas.map(() => false);
    cargas.forEach((_, i) => setTimeout(() => { listas[i] = true; }, azar(180, 820)));
    let mostrado = 0; const inicio = Date.now();
    const arco = $('.arc', capa), pct = $('text', capa), tx = $('.tx', capa), dt = $('.dt', capa);
    const timer = setInterval(() => {
      const hechas = listas.filter(Boolean).length, listo = hechas >= total;
      const objetivo = 100 * hechas / total, techo = listo ? 100 : objetivo + 0.85 * (100 / total);
      if (mostrado < objetivo) {
        const [av, min] = objetivo >= 100 ? [0.4, 4] : [0.22, 1];
        mostrado = Math.min(mostrado + Math.max((objetivo - mostrado) * av, min), objetivo);
      } else if (mostrado < techo) mostrado += (techo - mostrado) * 0.025;
      const p = Math.min(mostrado, 100);
      arco.setAttribute('stroke-dasharray', `${C * p / 100} ${C}`);
      pct.textContent = Math.floor(p) + '%';
      const pend = listas.findIndex(x => !x);
      tx.textContent = pend >= 0 ? cargas[pend] : '¡Listo!';
      dt.textContent = `${hechas} de ${total} consultas listas`;
      if (listo && mostrado >= 100 && Date.now() - inicio >= 350) {
        clearInterval(timer);
        setTimeout(() => { capa.remove(); res(); }, 120);
      }
    }, 30);
  });
}
// ejecutar_con_spinner con las etapas del informe
function spinnerEtapas(contenedor, etapas, titulo) {
  return new Promise(res => {
    const R = 41, C = 2 * Math.PI * R, total = etapas.length;
    const capa = document.createElement('div');
    capa.className = 'vt-spin';
    capa.innerHTML = `<div class="box"><svg viewBox="0 0 96 96"><circle cx="48" cy="48" r="${R}" fill="none" stroke="#3b494b" stroke-width="7"/>
      <circle class="arc" cx="48" cy="48" r="${R}" fill="none" stroke="#7df4ff" stroke-width="7" stroke-dasharray="0 ${C}" transform="rotate(-90 48 48)"/>
      <text x="48" y="55" text-anchor="middle" fill="#fff" font-size="20" font-weight="700" font-family="Segoe UI,sans-serif">0%</text></svg>
      <div class="tx">${esc(titulo)}</div><div class="dt"></div></div>`;
    contenedor.appendChild(capa);
    let hechos = 0, mostrado = 0, terminado = false;
    const arco = $('.arc', capa), pct = $('text', capa), tx = $('.tx', capa), dt = $('.dt', capa);
    (async () => { for (let i = 0; i < total; i++) { hechos = i; tx.textContent = etapas[i]; await espera(azar(380, 700)); } hechos = total; terminado = true; tx.textContent = '¡Informe listo!'; })();
    const timer = setInterval(() => {
      const h = terminado ? total : Math.min(hechos, total - 1);
      const objetivo = 100 * h / total, techo = terminado ? 100 : objetivo + 0.85 * (100 / total);
      if (mostrado < objetivo) mostrado = Math.min(mostrado + Math.max((objetivo - mostrado) * (terminado ? 0.4 : 0.22), terminado ? 4 : 1), objetivo);
      else if (mostrado < techo) mostrado += (techo - mostrado) * 0.025;
      const p = Math.min(mostrado, 100);
      arco.setAttribute('stroke-dasharray', `${C * p / 100} ${C}`);
      pct.textContent = Math.floor(p) + '%';
      dt.textContent = terminado ? '' : `Paso ${h + 1} de ${total}`;
      if (terminado && mostrado >= 100) { clearInterval(timer); setTimeout(() => { capa.remove(); res(); }, 120); }
    }, 30);
  });
}

/* ---------- Widgets de formulario (interfaz/widgets.py) ---------- */
const lbl = t => `<label class="vt-lbl">${t}</label>`;
const entrada = (id, ph = '', extra = '') => `<input class="vt-in" id="${id}" placeholder="${esc(ph)}" autocomplete="off" ${extra}>`;
const fecha = id => `<input class="vt-in date" type="date" id="${id}" value="${hoyISO()}">`;
const combo = (id, valores) => `<div class="vt-sel"><select id="${id}">${valores.map(([v, t]) => `<option value="${esc(v)}">${esc(t)}</option>`).join('')}</select></div>`;
const caja = id => `<textarea class="vt-ta" id="${id}">Opcional...</textarea>`;
function tabla(cols, filas, nuevoId) {
  return `<table class="vt-tbl"><thead><tr>${cols.map(c => `<th>${c[0]}</th>`).join('')}</tr></thead><tbody>${
    filas.map(f => `<tr class="${f.id != null && f.id === nuevoId ? 'nuevo' : ''} ${f.sel ? 'sel' : ''}">${f.v.map((v, i) => `<td class="${cols[i][1]}">${esc(v)}</td>`).join('')}</tr>`).join('')
  }</tbody></table>`;
}
function placeholderOpcional(ta) {
  ta.addEventListener('focus', () => { if (ta.value.trim() === 'Opcional...') ta.value = ''; });
}
const obsDe = ta => { const o = ta.value; return o.trim() === 'Opcional...' ? '' : o; };

/* ============================================================
   PÁGINAS
   ============================================================ */
const PAGINAS = {};

/* ---------- login_ui.py ---------- */
PAGINAS.login = page => {
  page.classList.add('vt-login');
  let recordado = ''; try { recordado = localStorage.getItem(KEY_RECORDAR) || ''; } catch {}
  page.innerHTML = `<div class="glow"></div><div class="vt-center"><div class="vt-card-login"><div class="accent"></div>
    <img class="logo" src="icon.png" alt="">
    <h1>VorTrack</h1><div class="sub">Gestión, Seguimiento y Transformación</div>
    <form id="lgForm" autocomplete="off" novalidate>
      <label class="cap" for="lgUser">IDENTIFICADOR</label>
      <input class="vt-in-login" id="lgUser" placeholder="vortrack.soporte@gmail.com" style="margin-bottom:16px" value="${esc(recordado)}">
      <label class="cap" for="lgPass">CREDENCIAL DE ACCESO</label>
      <div class="vt-passrow"><input class="vt-in-login" id="lgPass" type="password" placeholder="••••••••"><button type="button" class="vt-btn-ver" id="lgVer">Ver</button></div>
      <div class="vt-opts"><label class="vt-check"><input type="checkbox" id="lgRec" ${recordado ? 'checked' : ''}>Recordar sesión</label>
        <button type="button" class="vt-forgot" id="lgOlv">¿Olvidó su credencial?</button></div>
      <button class="vt-btn-login" type="submit">INICIAR SESIÓN</button>
    </form></div></div>
    <div class="vt-footer-login">© 2026 desarrollado por Miguel Ruiz Ramirez</div>`;
  const pass = $('#lgPass', page);
  $('#lgVer', page).onclick = e => { const v = pass.type === 'password'; pass.type = v ? 'text' : 'password'; e.target.textContent = v ? 'Ocultar' : 'Ver'; };
  $('#lgOlv', page).onclick = () => info('Recuperar Credencial', 'Para restablecer su contraseña, escriba al correo de soporte:\n\nvortrack.soporte@gmail.com');
  $('#lgForm', page).onsubmit = async e => {
    e.preventDefault();
    const user = $('#lgUser', page).value, pwd = pass.value;
    if (esVacio(user) || esVacio(pwd)) {
      await aviso('Campos Requeridos', 'Por favor ingrese su identificador y credencial de acceso.');
      return;
    }
    try { $('#lgRec', page).checked ? localStorage.setItem(KEY_RECORDAR, user) : localStorage.removeItem(KEY_RECORDAR); } catch {}
    entrarComo(user);
    ir('inicio');
  };
};
// Demo: el identificador se vuelve el estudiante con el que se registra todo.
function entrarComo(identificador) {
  let nombre = identificador.trim();
  if (nombre.includes('@')) nombre = nombre.split('@')[0].replace(/[._-]+/g, ' ');
  nombre = nombre.replace(/\s+/g, ' ').slice(0, 40).replace(/(^|\s)\p{Ll}/gu, c => c.toUpperCase());
  let r = S.responsables.find(x => x.n.toLowerCase() === nombre.toLowerCase());
  if (!r) { r = { id: sigId(S.responsables), n: nombre, visitante: true }; S.responsables.push(r); }
  S.user = { nombre: r.n, idResp: r.id };
  S.hecho.login = true;
  guardar();
}

/* ---------- inicio_ui.py ---------- */
PAGINAS.inicio = page => {
  page.innerHTML = marco('inicio', `<div class="vt-home">
    <div class="left"><div class="vt-glass"><img src="logo_hero.jpg" alt="Logo de VorTrack"></div></div>
    <div class="right">
      <span class="vt-badge">●&nbsp;&nbsp; GESTIÓN &nbsp;·&nbsp; SEGUIMIENTO &nbsp;·&nbsp; TRANSFORMACIÓN</span>
      <h2>VorTrack</h2>
      <div class="vt-desc"><p>Es un software de escritorio que apoya la gestión y realización del proyecto TRANSRE/SC, del Instituto San Carlos de la Salle.</p>
        <p>Permite el registro, organización, consulta y análisis de la información generada durante el proceso de aprovechamiento de residuos de tereftalato de polietileno (PET) para la fabricación de material didáctico.</p></div>
      <div class="vt-feats">
        <div class="vt-feat"><div class="i">🛣️</div><b>Trazabilidad</b><span>Fortalecer el control de procesos.</span></div>
        <div class="vt-feat"><div class="i">📊</div><b>Indicadores</b><span>Facilitar la generación de métricas.</span></div>
        <div class="vt-feat"><div class="i">💡</div><b>Decisiones</b><span>Apoyar la toma de decisiones.</span></div>
      </div>
      <button class="vt-explorar" data-go="recoleccion">EXPLORAR SISTEMA &nbsp; ➔</button>
    </div></div>`);
};

/* ---------- recolec_ui.py ---------- */
PAGINAS.recoleccion = async page => {
  page.innerHTML = marco('recoleccion', '');
  const main = $('.vt-main', page);
  await spinner(main, ['Cargando estudiantes…', 'Cargando lugares de recolección…', 'Obteniendo últimos registros…']);
  const resps = repo.responsables(), lugs = repo.lugares();
  main.innerHTML = `<div class="vt-split">
    <div class="vt-card"><div class="ttl">Nueva Recolección</div><div class="vt-form">
      ${lbl('Fecha del Registro')}${fecha('rFecha')}
      ${lbl('Estudiante / Responsable')}${combo('rResp', [['', 'Seleccione responsable...'], ...resps.map(r => [r.id, r.n])])}
      <div class="vt-hint">Se le asignarán los puntos automáticamente</div>
      ${lbl('Lugar de recolección')}${combo('rLug', [['', 'Seleccione lugar...'], ...lugs.map(l => [l.id, l.n])])}
      ${lbl('Cantidad de botellas')}${entrada('rBot', 'Ej. 20', 'inputmode="numeric"')}
      ${lbl('Peso PET (kg) aprovechado')}${entrada('rPeso', 'Ej. 2.5', 'inputmode="decimal"')}
      ${lbl('Observaciones')}${caja('rObs')}
      <button class="vt-btn-ok" id="rOk">Registrar PET</button>
    </div></div>
    <div class="vt-card"><div class="ttl left">Últimos Registros</div><div class="vt-tblwrap" id="rTabla"></div></div></div>`;
  placeholderOpcional($('#rObs', page));
  const recargar = nuevo => {
    const filas = [...S.jornadas].sort(porFechaDesc).slice(0, 50).map(j => ({
      id: j.id, v: [dmy(j.f), repo.resp(j.resp)?.n || '', repo.lugar(j.lug)?.n || '', j.bot != null ? String(j.bot) : '', j.peso != null ? g(j.peso) : '', j.obs || ''],
    }));
    $('#rTabla', page).innerHTML = tabla([['Fecha', 'c'], ['Responsable', 'w'], ['Lugar', 'w'], ['Botellas', 'c'], ['Peso PET (kg)', 'c'], ['Observaciones', 'w']], filas, nuevo);
  };
  recargar();
  $('#rOk', page).onclick = async () => {
    const idResp = parseInt($('#rResp', page).value, 10), idLug = parseInt($('#rLug', page).value, 10);
    const botellas = $('#rBot', page).value.trim(), peso = $('#rPeso', page).value.trim();
    if (!idResp) return aviso('Error', 'Debe seleccionar un responsable.');
    if (!idLug) return aviso('Error', 'Debe seleccionar un lugar de recolección.');
    if (esVacio(peso)) return aviso('Error', 'Debe ingresar el peso de PET aprovechado.');
    const [okP, pesoV] = numero(peso);
    if (!okP) return aviso('Error', 'El peso debe ser un número válido.');
    let botV = null;
    if (botellas) { const [okB, b] = enteroPositivo(botellas); if (!okB) return aviso('Error', 'La cantidad de botellas debe ser un número entero.'); botV = b; }
    const id = sigId(S.jornadas);
    S.jornadas.push({ id, f: $('#rFecha', page).value || hoyISO(), lug: idLug, resp: idResp, bot: botV, peso: pesoV, obs: obsDe($('#rObs', page)) });
    if (idResp === S.user?.idResp) S.hecho.rec = true;
    guardar();
    await info('Recolección Registrada', `Jornada #${id} registrada correctamente.`);
    $('#rBot', page).value = ''; $('#rPeso', page).value = ''; $('#rObs', page).value = 'Opcional...';
    $('#rResp', page).value = ''; $('#rLug', page).value = '';
    recargar(id);
  };
};

/* ---------- transformacion_ui.py ---------- */
PAGINAS.transformacion = async page => {
  page.innerHTML = marco('transformacion', '');
  const main = $('.vt-main', page);
  await spinner(main, ['Cargando jornadas de recolección…', 'Obteniendo historial de filamento…']);
  const jornadas = repo.jornadasCombo();
  main.innerHTML = `<div class="vt-split">
    <div class="vt-card"><div class="ttl">Nueva Transformación</div><div class="stl">Producción de filamento 3D (extrusión de PET)</div><div class="vt-form" style="padding-top:4px">
      ${lbl('Fecha del Registro')}${fecha('tFecha')}
      ${lbl('Jornada de recolección (origen del PET)')}${combo('tJor', [['', 'Seleccione jornada...'], ...jornadas.map(j => [j.id, j.lab])])}
      ${lbl('Peso ingresado (kg) — PET de la jornada')}${entrada('tIn', '', 'readonly value="—"')}
      ${lbl('Peso salido (kg) — filamento')}${entrada('tSal', 'Ej. 1.7', 'inputmode="decimal"')}
      ${lbl('Desperdicio (kg) — automático')}${entrada('tDesp', '', 'readonly value="—"')}
      ${lbl('Color del filamento')}${entrada('tColor', 'Ej. Translúcido, Azul...')}
      ${lbl('Diámetro (mm)')}${entrada('tDiam', 'Ej. 1.75', 'inputmode="decimal"')}
      ${lbl('Metros de filamento producidos')}${entrada('tM', 'Ej. 560', 'inputmode="decimal"')}
      ${lbl('Observaciones')}${caja('tObs')}
      <button class="vt-btn-ok" id="tOk">Registrar Filamento</button>
    </div></div>
    <div class="vt-card"><div class="ttl left">Historial de Filamento</div><div class="vt-tblwrap" id="tTabla"></div></div></div>`;
  placeholderOpcional($('#tObs', page));
  const porId = Object.fromEntries(jornadas.map(j => [j.id, j]));
  const desperdicio = () => {
    const [a, ing] = numero($('#tIn', page).value), [b, sal] = numero($('#tSal', page).value);
    $('#tDesp', page).value = a && b && ing - sal >= 0 ? f2(ing - sal) : '—';
  };
  $('#tJor', page).onchange = () => { const j = porId[$('#tJor', page).value]; $('#tIn', page).value = j ? f2(j.peso) : '—'; desperdicio(); };
  $('#tSal', page).addEventListener('input', desperdicio);
  const recargar = nuevo => {
    const filas = [...S.prods].sort(porFechaDesc).slice(0, 50).map(p => {
      const ing = repo.jornada(p.j)?.peso ?? 0, sal = p.peso ?? 0;
      return { id: p.id, v: [dmy(p.f), p.j != null ? `#${p.j}` : '', g(ing), g(sal), f2(Math.max(ing - sal, 0)), p.color || '', p.diam != null ? g(p.diam) : '', p.m != null ? g(p.m) : '', p.obs || ''] };
    });
    $('#tTabla', page).innerHTML = tabla([['Fecha', 'c'], ['Jornada', 'c'], ['Ingresado (kg)', 'c'], ['Salido (kg)', 'c'], ['Desperdicio (kg)', 'c'], ['Color', 'w'], ['Diám. (mm)', 'c'], ['Metros (m)', 'c'], ['Observaciones', 'w']], filas, nuevo);
  };
  recargar();
  $('#tOk', page).onclick = async () => {
    const j = porId[$('#tJor', page).value];
    const salido = $('#tSal', page).value.trim(), metros = $('#tM', page).value.trim();
    const color = $('#tColor', page).value.trim(), diam = $('#tDiam', page).value.trim();
    if (!j) return aviso('Error', 'Debe seleccionar la jornada de recolección de origen.');
    if (esVacio(salido)) return aviso('Error', 'Debe ingresar el peso salido (filamento).');
    const [okS, salV] = numeroPositivo(salido);
    if (!okS) return aviso('Error', 'El peso salido debe ser un número mayor que cero.');
    if (salV > j.peso) return aviso('Error', `El peso salido no puede superar el ingresado (${g(j.peso)} kg).`);
    if (esVacio(metros)) return aviso('Error', 'Debe ingresar los metros de filamento producidos.');
    const [okM, mV] = numeroPositivo(metros);
    if (!okM) return aviso('Error', 'Los metros deben ser un número mayor que cero.');
    let diamV = null;
    if (diam) { const [okD, d] = numero(diam); if (!okD) return aviso('Error', 'El diámetro debe ser un número válido.'); diamV = d; }
    const id = sigId(S.prods);
    S.prods.push({ id, j: j.id, f: $('#tFecha', page).value || hoyISO(), color: color || null, diam: diamV, peso: salV, m: mV, obs: obsDe($('#tObs', page)) });
    if (repo.jornada(j.id)?.resp === S.user?.idResp) S.hecho.trans = true;
    guardar();
    await info('Transformación Registrada', `Producción #${id} registrada.\nDesperdicio calculado: ${f2(j.peso - salV)} kg`);
    ['#tSal', '#tM', '#tColor', '#tDiam'].forEach(s => { $(s, page).value = ''; });
    $('#tIn', page).value = '—'; $('#tDesp', page).value = '—'; $('#tObs', page).value = 'Opcional...'; $('#tJor', page).value = '';
    recargar(id);
  };
};

/* ---------- impresion_ui.py ---------- */
const ESTADOS = ['Seleccione estado...', 'En proceso', 'Finalizado', 'Fallido'];
PAGINAS.impresion = async page => {
  page.innerHTML = marco('impresion', '');
  const main = $('.vt-main', page);
  await spinner(main, ['Cargando modelos…', 'Obteniendo filamentos producidos…', 'Obteniendo historial de impresiones…']);
  const modelos = repo.modelos(), prods = repo.prodsCombo();
  main.innerHTML = `<div class="vt-split">
    <div class="vt-card"><div class="ttl">Nueva Impresión</div><div class="stl">Fabricación de material didáctico (impresión 3D)</div><div class="vt-form" style="padding-top:4px">
      ${lbl('Fecha del Registro')}${fecha('iFecha')}
      ${lbl('Modelo (material didáctico)')}${combo('iMod', [['', 'Seleccione modelo...'], ...modelos.map(m => [m.id, m.n])])}
      ${lbl('Filamento utilizado (producción)')}${combo('iProd', [['', 'Seleccione producción...'], ...prods.map(p => [p.id, p.lab])])}
      ${lbl('Cantidad de piezas')}${entrada('iCant', 'Ej. 3', 'inputmode="numeric"')}
      ${lbl('Peso de filamento utilizado (g)')}${entrada('iPeso', 'Ej. 120', 'inputmode="decimal"')}
      ${lbl('Tiempo de impresión (min)')}${entrada('iTiempo', 'Ej. 150', 'inputmode="numeric"')}
      ${lbl('Estado')}${combo('iEst', ESTADOS.map((e, i) => [i ? e : '', e]))}
      <button class="vt-btn-ok" id="iOk">Registrar Impresión</button>
    </div></div>
    <div class="vt-card"><div class="ttl left">Historial de Impresiones</div><div class="vt-tblwrap" id="iTabla"></div></div></div>`;
  const proyectar = () => {
    const m = repo.modelo(parseInt($('#iMod', page).value, 10));
    if (!m) return;
    const [peso, tiempo] = proyeccion.impresion(m.t, m.g, $('#iCant', page).value.trim());
    if (peso != null) $('#iPeso', page).value = g(peso);
    if (tiempo != null) $('#iTiempo', page).value = String(tiempo);
  };
  $('#iMod', page).onchange = proyectar;
  $('#iCant', page).addEventListener('input', proyectar);
  const recargar = nuevo => {
    const filas = [...S.fabs].sort(porFechaDesc).slice(0, 50).map(f => ({
      id: f.id, v: [dmy(f.f), repo.modelo(f.mod)?.n || '', f.prod != null ? `#${f.prod}` : '', f.cant ?? '', f.peso != null ? g(f.peso) : '', f.t ?? '', f.estado || ''],
    }));
    $('#iTabla', page).innerHTML = tabla([['Fecha', 'c'], ['Modelo', 'w'], ['Filamento', 'c'], ['Piezas', 'c'], ['Peso (g)', 'c'], ['Tiempo (min)', 'c'], ['Estado', 'c']], filas, nuevo);
  };
  recargar();
  $('#iOk', page).onclick = async () => {
    const idMod = parseInt($('#iMod', page).value, 10), idProd = parseInt($('#iProd', page).value, 10), estado = $('#iEst', page).value;
    if (!idMod) return aviso('Error', 'Debe seleccionar un modelo.');
    if (!idProd) return aviso('Error', 'Debe seleccionar la producción de filamento utilizada.');
    const [okC, cant] = enteroPositivo($('#iCant', page).value);
    if (!okC) return aviso('Error', 'La cantidad de piezas debe ser un número entero mayor que cero.');
    const [okF, fil] = numeroPositivo($('#iPeso', page).value);
    if (!okF) return aviso('Error', 'El peso de filamento (g) debe ser un número mayor que cero.');
    const [okT, t] = numeroPositivo($('#iTiempo', page).value);
    if (!okT) return aviso('Error', 'El tiempo (min) debe ser un número mayor que cero.');
    if (!estado) return aviso('Error', 'Debe seleccionar el estado de la impresión.');
    const id = sigId(S.fabs);
    S.fabs.push({ id, mod: idMod, prod: idProd, f: $('#iFecha', page).value || hoyISO(), cant, peso: fil, t: Math.trunc(t), estado });
    const prod = S.prods.find(p => p.id === idProd);
    if (repo.jornada(prod?.j)?.resp === S.user?.idResp || S.hecho.trans) S.hecho.imp = true;
    guardar();
    await info('Impresión Registrada', `Fabricación #${id} registrada correctamente.`);
    ['#iCant', '#iPeso', '#iTiempo', '#iMod', '#iProd', '#iEst'].forEach(s => { $(s, page).value = ''; });
    recargar(id);
  };
};

/* ---------- historico_ui.py ---------- */
let generando = false;
PAGINAS.historico = async page => {
  page.innerHTML = marco('historico', `<div class="vt-hist">
    <div class="vt-hhead"><h2>Histórico e Informes</h2><button class="vt-btn-inf" id="hInf">GENERAR INFORME &nbsp; ⭳</button></div>
    <div class="vt-hbody" id="hBody"></div></div>`);
  const body = $('#hBody', page);
  $('#hInf', page).onclick = () => generarInforme(body);
  await spinner(body, ['Calculando indicadores…', 'Consultando ranking de participación…', 'Obteniendo filamentos producidos…', 'Cargando modelos…']);
  const k = repo.indicadores();
  const kpis = [
    [`${g(k.pet_recolectado)} kg`, 'PET recolectado', '🧴'], [`${g(k.filamento_producido)} kg`, 'Filamento producido', '🧵'],
    [`${f2(k.desperdicio)} kg`, 'Desperdicio', '♻︎'], [String(k.objetos_impresos), 'Objetos impresos', '🖨︎'],
    [String(k.responsables), 'Responsables', '👥'], [String(k.botellas), 'Botellas recolectadas', '🍾'],
  ];
  const ranking = repo.ranking().map((r, i) => ({
    sel: r.id === S.user?.idResp, v: [i + 1, r.n, g(r.pet), r.jornadas, r.bot, Math.round(r.pet * 100)],
  }));
  const prods = repo.prodsCombo();
  body.insertAdjacentHTML('beforeend', `<div class="vt-kpis">${kpis.map(([v, t, i]) => `<div class="vt-kpi"><div class="i">${i}</div><b>${v}</b><span>${t}</span></div>`).join('')}</div>
    <div class="vt-hgrid">
      <div class="vt-card"><div class="ttl left">Ranking de participación</div><div class="vt-tblwrap">${tabla([['Puesto', 'c'], ['Estudiante', 'w'], ['PET aportado (kg)', 'c'], ['Jornadas', 'c'], ['Botellas', 'c'], ['Puntos', 'c']], ranking)}</div></div>
      <div class="vt-card"><div class="ttl left" style="padding-bottom:6px">Proyecciones de producción</div>
        <div class="vt-proysel">${lbl('Filamento producido:')}${combo('hProd', [['', 'Seleccione filamento...'], ...prods.map(p => [p.id, p.lab])])}</div>
        <div class="vt-proymsg" id="hMsg">Elige un filamento para ver cuántas piezas alcanzan.</div>
        <div class="vt-tblwrap" id="hProy"></div></div>
    </div>`);
  const colsProy = [['Modelo', 'w'], ['Piezas posibles', 'c'], ['g/pieza', 'c'], ['Sobrante (g)', 'c'], ['Tiempo total (min)', 'c']];
  $('#hProy', page).innerHTML = tabla(colsProy, []);
  $('#hProd', page).onchange = e => {
    const p = prods.find(x => String(x.id) === e.target.value);
    if (!p) { $('#hMsg', page).textContent = 'Elige un filamento para ver cuántas piezas alcanzan.'; $('#hProy', page).innerHTML = tabla(colsProy, []); return; }
    const [filas, mejor, disp] = proyeccion.piezasPorFilamento(p.peso, repo.modelos());
    $('#hProy', page).innerHTML = tabla(colsProy, filas.map(([n, pz, gp, sob, tt]) =>
      ({ v: pz == null ? [n, '—', '—', '—', '—'] : [n, pz, g(gp), f0(sob), tt != null ? g(tt) : '—'] })));
    $('#hMsg', page).textContent = mejor && mejor[1] > 0
      ? `Con ${g(p.peso)} kg (${f0(disp)} g) de filamento alcanza para ${mejor[1]} ${mejor[0]}, sobrando ~${f0(mejor[2])} g. Mira la tabla para cada modelo.`
      : 'No alcanza para ningún modelo con ese filamento (o faltan pesos estimados en los modelos).';
  };
  S.hecho.hist = true; guardar();
};

async function generarInforme(body) {
  if (generando) return;
  generando = true;
  await spinnerEtapas(body, ['Consultando la base de datos…', 'Calculando estadísticas…', 'Armando el documento…', 'Exportando a PDF…'], 'Generando informe…');
  generando = false;
  const ahora = new Date();
  const nombre = `Informe_VorTrack_${ahora.getFullYear()}-${pad(ahora.getMonth() + 1)}-${pad(ahora.getDate())}_${pad(ahora.getHours())}${pad(ahora.getMinutes())}.pdf`;
  S.hecho.inf = true; guardar();
  if (await msg('q', 'Informe descargado', `El informe se guardó en tu carpeta de Descargas:\n\n${nombre}\n\n¿Deseas abrirlo ahora?`, ['Sí', 'No']) === 'Sí') {
    abrirInforme(nombre, ahora);
  }
}

/* ---------- Diálogos del footer ---------- */
const PRIVACIDAD = `VorTrack es una aplicación de escritorio desarrollada para el proyecto TRANSORE ISC del Instituto San Carlos de La Salle, orientada a la gestión y trazabilidad del aprovechamiento de residuos de PET para la fabricación de material didáctico.

1. Información que se registra
La aplicación almacena únicamente la información necesaria para la gestión del proyecto:
• Datos de responsables y estudiantes participantes (nombre y rol).
• Jornadas de recolección: fecha, aportante, cantidad y peso de PET.
• Producción de filamento: peso ingresado, peso salido, desperdicio y metros producidos.
• Impresiones y material didáctico fabricado.
• Observaciones asociadas a cada registro.

2. Almacenamiento local
Los datos se guardan de forma local en los equipos de cómputo de la institución destinados al proyecto. VorTrack no transmite información a servidores externos ni a terceros a través de Internet.

3. Finalidad del tratamiento
La información se utiliza exclusivamente para fortalecer la trazabilidad de los procesos, generar indicadores y reportes, y apoyar la toma de decisiones dentro del proyecto educativo.

4. Datos de menores de edad
Cuando se registren datos de estudiantes menores de edad, su tratamiento se realiza bajo la responsabilidad de la institución educativa y con el consentimiento de los acudientes, conforme a la normativa aplicable de protección de datos.

5. Acceso y seguridad
El acceso a la aplicación está protegido por credenciales personales. Cada usuario es responsable del uso de sus credenciales y de la información que registra.

6. Contacto
Para consultas o solicitudes relacionadas con el tratamiento de datos, escriba al correo de soporte: vortrack.soporte@gmail.com

Nota: Este documento es una versión preliminar (borrador) para el contexto del proyecto y podrá ajustarse a las políticas definitivas de la institución.`;
const TERMINOS = `Bienvenido a VorTrack, el sistema de gestión y seguimiento del proyecto TRANSORE ISC del Instituto San Carlos de La Salle. El uso de esta aplicación implica la aceptación de los siguientes términos.

1. Objeto y ámbito de uso
VorTrack es una herramienta de uso institucional y educativo, destinada a registrar y consultar la información del proceso de aprovechamiento de PET (recolección, transformación en filamento e impresión de material didáctico). Su uso está autorizado únicamente a los miembros del proyecto.

2. Cuentas y credenciales
El acceso se realiza mediante credenciales personales e intransferibles. El usuario es responsable de mantener la confidencialidad de su contraseña y de todas las actividades realizadas bajo su cuenta.

3. Uso adecuado
El usuario se compromete a:
• Registrar información veraz y completa.
• Utilizar la aplicación con fines relacionados con el proyecto.
• No alterar, dañar ni intentar acceder de forma no autorizada a los datos o al sistema.
• Cuidar los equipos institucionales en los que se ejecuta la aplicación.

4. Información registrada
Los datos ingresados forman parte del proyecto y podrán utilizarse para generar indicadores, reportes y estadísticas. El tratamiento de datos se rige por la Política de Privacidad de VorTrack.

5. Disponibilidad y garantía
La aplicación se ofrece "tal cual", con fines educativos. Se procura su correcto funcionamiento, pero no se garantiza que esté libre de errores. La institución y el desarrollador no serán responsables por pérdidas derivadas de un uso indebido.

6. Propiedad
VorTrack fue desarrollado por Miguel Ruiz Ramírez para el proyecto TRANSORE ISC del Instituto San Carlos de La Salle.

7. Soporte y contacto
Para dudas, reportes o sugerencias, escriba al correo de soporte: vortrack.soporte@gmail.com

Nota: Este documento es una versión preliminar (borrador) para el contexto del proyecto y podrá ajustarse a los términos definitivos de la institución.`;

function dialogo(clase, titulo, interior) {
  const capa = document.createElement('div');
  capa.className = 'vt-modal';
  capa.innerHTML = `<div class="vt-dlg ${clase}"><div class="bar">${esc(titulo)}<span data-x>✕</span></div><div class="accent"></div>${interior}</div>`;
  (MOVIL.matches ? document.body : SCREEN).appendChild(capa);
  if (MOVIL.matches) capa.classList.add('vt');
  const cerrar = () => { capa.remove(); document.removeEventListener('keydown', tecla); };
  const tecla = e => { if (e.key === 'Escape') cerrar(); };
  document.addEventListener('keydown', tecla);
  capa.addEventListener('click', e => { if (e.target.closest('[data-x],[data-cerrar]')) cerrar(); });
  return capa;
}
function abrirEnlace(link) {
  if (link === 'Soporte Técnico' || link === 'Contacto') {
    const capa = dialogo('vt-sop', 'Soporte Técnico — VorTrack', `<div class="in">
      <div class="big">🛠️</div><h4>¿Necesitás ayuda?</h4>
      <p>Nuestro equipo está listo para asistirte.<br>Reportá tu problema o sugerencia y<br>te responderemos a la brevedad. 😊</p>
      <hr><div class="mail"><small>✉&nbsp; Correo de soporte:</small><b data-copiar>vortrack.soporte@gmail.com</b><small>(clic para copiar al portapapeles)</small></div>
      <div class="ok"></div><button class="vt-btn-cerrar" data-cerrar>&nbsp; Cerrar &nbsp;</button></div>`);
    capa.querySelector('[data-copiar]').onclick = async () => {
      try { await navigator.clipboard.writeText('vortrack.soporte@gmail.com'); } catch {}
      const ok = capa.querySelector('.ok'); ok.textContent = '✔  ¡Correo copiado al portapapeles!';
      setTimeout(() => { ok.textContent = ''; }, 2500);
    };
  } else {
    const [t, h, x] = link === 'Privacidad' ? ['Privacidad — VorTrack', 'Política de Privacidad', PRIVACIDAD] : ['Términos de Uso — VorTrack', 'Términos de Uso', TERMINOS];
    dialogo('vt-txt', t, `<div class="in"><h4>${h}</h4><div class="doc">${esc(x)}</div><button class="vt-btn-cerrar" data-cerrar>&nbsp; Cerrar &nbsp;</button></div>`);
  }
}

/* ============================================================
   Informe PDF (servicios/servicio_informe.py + informe_html.py)
   ============================================================ */
const MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
const pctDe = (p, t) => t ? 100 * p / t : 0;
function calcularInforme() {
  const k = repo.indicadores();
  const recs = [...S.jornadas].sort(porFechaDesc).map(r => ({ id: r.id, fecha: r.f, responsable: repo.resp(r.resp)?.n || 'Sin responsable', lugar: repo.lugar(r.lug)?.n || 'Sin lugar', botellas: r.bot || 0, pet: r.peso || 0, obs: r.obs || '' }));
  const petJ = Object.fromEntries(recs.map(r => [r.id, r.pet]));
  const fabs = [...S.fabs].sort(porFechaDesc).map(f => ({ id: f.id, fecha: f.f, modelo: repo.modelo(f.mod)?.n || 'Sin modelo', id_prod: f.prod, piezas: f.cant || 0, peso_g: f.peso || 0, tiempo_min: f.t || 0, estado: f.estado || '—' }));
  const usado = {}; fabs.forEach(f => { usado[f.id_prod] = (usado[f.id_prod] || 0) + f.peso_g; });
  const prods = [...S.prods].sort(porFechaDesc).map(p => {
    const pet = petJ[p.j] || 0, obt = p.peso || 0, us = (usado[p.id] || 0) / 1000;
    return { id: p.id, fecha: p.f, jornada: p.j, color: p.color || '—', diametro: p.diam, pet, obtenido: obt, metros: p.m || 0, rendimiento: pctDe(obt, pet), usado: us, disponible: obt - us };
  });
  const petTotal = k.pet_recolectado, fil = k.filamento_producido;
  const petTransf = prods.reduce((a, p) => a + p.pet, 0), desp = Math.max(petTransf - fil, 0);
  const filUsado = fabs.reduce((a, f) => a + f.peso_g, 0) / 1000, piezas = fabs.reduce((a, f) => a + f.piezas, 0);
  const porEstado = { 'Finalizado': 0, 'En proceso': 0, 'Fallido': 0 };
  fabs.forEach(f => { porEstado[f.estado] = (porEstado[f.estado] || 0) + f.piezas; });
  const porMes = [];
  const fechas = recs.map(r => r.fecha).filter(Boolean).sort();
  if (fechas.length) {
    let [y, m] = fechas[0].split('-').map(Number); const [y2, m2] = fechas[fechas.length - 1].split('-').map(Number);
    while (y < y2 || (y === y2 && m <= m2)) {
      const v = recs.filter(r => r.fecha && +r.fecha.slice(0, 4) === y && +r.fecha.slice(5, 7) === m).reduce((a, r) => a + r.pet, 0);
      porMes.push([`${MESES[m - 1]} ${y}`, v]);
      [y, m] = m === 12 ? [y + 1, 1] : [y, m + 1];
    }
  }
  const agrupa = (arr, key, val) => { const o = {}; arr.forEach(x => { o[x[key]] = (o[x[key]] || 0) + x[val]; }); return Object.entries(o).sort((a, b) => b[1] - a[1]); };
  const ranking = repo.ranking(1000).map((r, i) => ({ puesto: i + 1, nombre: r.n, pet: r.pet, jornadas: r.jornadas, botellas: r.bot, puntos: Math.round(r.pet * 100), participacion: pctDe(r.pet, petTotal) }));
  const todas = [...recs, ...prods, ...fabs].map(x => x.fecha).filter(Boolean).sort();
  const jornadas = recs.length;
  const r = {
    pet_recolectado: petTotal, filamento_producido: fil, desperdicio: desp, objetos_impresos: k.objetos_impresos, responsables: k.responsables,
    botellas: k.botellas, jornadas, pet_transformado: petTransf, pet_pendiente: Math.max(petTotal - petTransf, 0),
    rendimiento: pctDe(fil, petTransf), tasa_desperdicio: pctDe(desp, petTransf), filamento_usado: filUsado,
    filamento_disponible: Math.max(fil - filUsado, 0), metros: prods.reduce((a, p) => a + p.metros, 0), piezas,
    tasa_exito: pctDe(porEstado['Finalizado'] || 0, piezas), horas_impresion: fabs.reduce((a, f) => a + f.tiempo_min, 0) / 60,
    pet_por_jornada: jornadas ? petTotal / jornadas : 0, botellas_por_kg: petTotal ? k.botellas / petTotal : 0,
  };
  const modelo = { resumen: r, periodo: todas.length ? [todas[0], todas[todas.length - 1]] : null, pet_por_mes: porMes,
    pet_por_lugar: agrupa(recs, 'lugar', 'pet'), piezas_por_estado: Object.entries(porEstado), piezas_por_modelo: agrupa(fabs, 'modelo', 'piezas'),
    ranking, recolecciones: recs, producciones: prods, fabricaciones: fabs };
  // ServicioInforme.hallazgos
  const h = [];
  if (r.pet_recolectado > 0) h.push(`Se han recolectado ${num(r.pet_recolectado)} kg de PET (${num(r.botellas, 0)} botellas) en ${r.jornadas} jornada(s), un promedio de ${num(r.pet_por_jornada)} kg por jornada.`);
  if (modelo.pet_por_lugar.length) { const [l, kg] = modelo.pet_por_lugar[0]; h.push(`${l} es el lugar con más PET aportado: ${num(kg)} kg (${num(pctDe(kg, r.pet_recolectado), 0)}% del total).`); }
  if (ranking.length && ranking[0].pet > 0) h.push(`${ranking[0].nombre} lidera el ranking de participación con ${num(ranking[0].pet)} kg y ${num(ranking[0].puntos, 0)} puntos.`);
  if (r.pet_transformado > 0) h.push(`La extrusión convirtió ${num(r.pet_transformado)} kg de PET en ${num(r.filamento_producido)} kg de filamento: rendimiento del ${num(r.rendimiento, 1)}% y desperdicio del ${num(r.tasa_desperdicio, 1)}%.`);
  if (r.pet_pendiente > 0) h.push(`Quedan ${num(r.pet_pendiente)} kg de PET recolectado pendientes de transformar.`);
  if (r.piezas > 0) h.push(`Se imprimieron ${r.piezas} pieza(s) usando ${num(r.filamento_usado)} kg de filamento (${num(r.horas_impresion, 1)} h de impresión); tasa de éxito del ${num(r.tasa_exito, 0)}%.`);
  prods.forEach(p => { if (p.disponible < -0.0005) h.push(`Atención: la producción #${p.id} registra ${num(p.usado)} kg de filamento usado en impresiones pero solo produjo ${num(p.obtenido)} kg. Conviene revisar esos registros.`); });
  if (r.filamento_producido > 0) h.push(`Hay ${num(r.filamento_disponible)} kg de filamento disponible para nuevas impresiones.`);
  modelo.hallazgos = h;
  return modelo;
}

const CI = { navy: '#071a2e', navy2: '#0d2a47', tinta: '#13263a', suave: '#5b6b7c', linea: '#dbe4ec', fondo: '#f4f8fb', cian: '#00a6b8', cian_claro: '#7df4ff', azul: '#0056fd', verde: '#1f9d55', ambar: '#d99a00', rojo: '#d64545' };
const COLOR_ESTADO = { 'Finalizado': CI.verde, 'En proceso': CI.ambar, 'Fallido': CI.rojo };
const vacio = (t = 'Sin datos registrados todavía.') => `<div class="vacio">${esc(t)}</div>`;
const fechaI = iso => iso ? dmy(iso) : '—';
const minutos = m => { const h = Math.floor(m / 60), mm = Math.floor(m % 60); return h ? `${h} h ${pad(mm)} min` : `${mm} min`; };
function svgBarrasH(items, unidad = 'kg', dec = 2, color = CI.cian) {
  items = items.filter(([, v]) => v > 0).slice(0, 8);
  if (!items.length) return vacio();
  const ancho = 380, eti = 112, val = 74, fila = 28, max = Math.max(...items.map(x => x[1])), util = ancho - eti - val, h = items.length * fila + 6;
  return `<svg viewBox="0 0 ${ancho} ${h}" class="grafico">` + items.map(([e, v], i) => {
    const y = i * fila + 4, w = Math.max(util * v / max, 3), t = e.length <= 18 ? e : e.slice(0, 17) + '…';
    return `<text x="${eti - 10}" y="${y + 16}" text-anchor="end" class="eje">${esc(t)}</text><rect x="${eti}" y="${y + 3}" width="${util}" height="18" rx="4" fill="${CI.fondo}"/><rect x="${eti}" y="${y + 3}" width="${w.toFixed(1)}" height="18" rx="4" fill="${color}"/><text x="${(eti + w + 8).toFixed(1)}" y="${y + 16}" class="valor">${num(v, dec)} ${esc(unidad)}</text>`;
  }).join('') + '</svg>';
}
function svgColumnas(items, unidad = 'kg', color = CI.azul) {
  if (!items.length || !items.some(([, v]) => v > 0)) return vacio();
  items = items.slice(-12);
  const ancho = 380, alto = 200, izq = 36, abajo = 28, arriba = 20, max = Math.max(...items.map(x => x[1])) || 1, uh = alto - abajo - arriba;
  const paso = (ancho - izq - 10) / items.length, bw = Math.min(paso * 0.58, 44);
  let s = `<svg viewBox="0 0 ${ancho} ${alto}" class="grafico">`;
  for (let gi = 0; gi < 5; gi++) { const y = arriba + uh * gi / 4; s += `<line x1="${izq}" y1="${y.toFixed(1)}" x2="${ancho - 6}" y2="${y.toFixed(1)}" class="guia"/><text x="${izq - 6}" y="${(y + 4).toFixed(1)}" text-anchor="end" class="eje">${num(max * (4 - gi) / 4, 1)}</text>`; }
  items.forEach(([e, v], i) => {
    const x = izq + paso * i + (paso - bw) / 2, hh = uh * v / max, y = arriba + uh - hh;
    s += `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(hh, 0.5).toFixed(1)}" rx="4" fill="${color}"/><text x="${(x + bw / 2).toFixed(1)}" y="${alto - abajo + 16}" text-anchor="middle" class="eje">${esc(e)}</text>`;
    if (v > 0) s += `<text x="${(x + bw / 2).toFixed(1)}" y="${(y - 6).toFixed(1)}" text-anchor="middle" class="valor">${num(v, 1)}</text>`;
  });
  return s + `<text x="4" y="12" class="eje">${esc(unidad)}</text></svg>`;
}
function svgDona(items, centroV, centroT) {
  const total = items.reduce((a, x) => a + x[1], 0);
  if (total <= 0) return vacio();
  const r = 70, gr = 26, cx = 90, cy = 90, circ = 2 * Math.PI * r; let ini = 0;
  let s = `<div class="dona"><svg viewBox="0 0 180 180" width="170" height="170"><circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${CI.fondo}" stroke-width="${gr}"/>`;
  items.forEach(([, v, c]) => { if (v <= 0) return; const l = circ * v / total; s += `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${c}" stroke-width="${gr}" stroke-dasharray="${l.toFixed(2)} ${(circ - l).toFixed(2)}" stroke-dashoffset="${(-ini).toFixed(2)}" transform="rotate(-90 ${cx} ${cy})"/>`; ini += l; });
  s += `<text x="${cx}" y="${cy + 2}" text-anchor="middle" class="dona-num">${esc(centroV)}</text><text x="${cx}" y="${cy + 20}" text-anchor="middle" class="eje">${esc(centroT)}</text></svg><ul class="leyenda">`;
  items.forEach(([e, v, c]) => { s += `<li><span class="punto" style="background:${c}"></span>${esc(e)}<b>${ent(v)}</b><small>${num(100 * v / total, 0)}%</small></li>`; });
  return s + '</ul></div>';
}
function embudo(etapas) {
  const base = etapas[0][1] > 0 ? etapas[0][1] : Math.max(0, ...etapas.map(x => x[1]));
  if (base <= 0) return vacio();
  return etapas.map(([e, v, c]) => { const a = v > 0 ? Math.max(100 * v / base, 1.5) : 0;
    return `<div class="embudo-fila"><div class="embudo-eti">${esc(e)}</div><div class="embudo-pista"><div class="embudo-barra" style="width:${Math.min(a, 100).toFixed(1)}%;background:${c}"></div></div><div class="embudo-val"><b>${num(v)} kg</b><small>${num(100 * v / base, 0)}%</small></div></div>`; }).join('');
}
const kpiI = (v, u, t, a) => `<div class="kpi" style="border-left-color:${a}"><div class="kpi-valor">${v}<span>${esc(u)}</span></div><div class="kpi-titulo">${esc(t)}</div></div>`;
const mini = (v, t) => `<div class="mini"><b>${v}</b><span>${esc(t)}</span></div>`;
const medalla = p => { const c = { 1: '#e3b341', 2: '#a9b4c0', 3: '#c98a4b' }[p]; return c ? `<span class="medalla" style="background:${c}">${p}</span>` : `<span class="medalla medalla-n">${p}</span>`; };
const estadoI = e => { const c = COLOR_ESTADO[e] || CI.suave; return `<span class="estado" style="color:${c};border-color:${c}">${esc(e)}</span>`; };
const disponible = kg => kg < -0.0005 ? `<b class="alerta">${num(kg)} ⚠</b>` : `<b>${num(kg)}</b>`;
function tablaI(cols, filas, pie, vac = 'Sin registros.') {
  if (!filas.length) return vacio(vac);
  return `<table><thead><tr>${cols.map(([t, c]) => `<th class="${c}">${esc(t)}</th>`).join('')}</tr></thead><tbody>${filas.map(f => '<tr>' + f.map((v, i) => `<td class="${cols[i][1]}">${v}</td>`).join('') + '</tr>').join('')}</tbody>${pie ? '<tfoot><tr>' + pie.map((v, i) => `<td class="${cols[i][1]}">${v}</td>`).join('') + '</tr></tfoot>' : ''}</table>`;
}
const CSS_INFORME = `@page{size:A4;margin:15mm 13mm 17mm}
*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}b{font-weight:700}
body{margin:0 auto;max-width:820px;padding:18px;font:10pt/1.45 'Segoe UI',Roboto,Arial,sans-serif;color:${CI.tinta};background:#fff}
@media print{body{padding:0;max-width:none}}
h2{font-size:14pt;color:${CI.navy};margin:22px 0 10px;display:flex;align-items:center;gap:8px}
h2::before{content:"";width:5px;height:18px;border-radius:3px;background:${CI.cian}}
h3{font-size:10.5pt;margin:0 0 10px;color:${CI.navy}}
.nota{margin:-4px 0 10px;color:${CI.suave};font-size:8.5pt}
.bloque,.panel,.kpi,.mini{break-inside:avoid}
.portada{background:linear-gradient(135deg,${CI.navy} 0%,${CI.navy2} 100%);color:#fff;border-radius:14px;padding:22px 26px;position:relative;overflow:hidden}
.portada::after{content:"";position:absolute;right:-60px;top:-60px;width:220px;height:220px;border-radius:50%;border:28px solid rgba(125,244,255,.10)}
.marca{display:flex;align-items:center;gap:12px}.marca img{width:46px;height:46px}
.marca-nombre{font-size:22pt;font-weight:700;color:${CI.cian_claro};line-height:1}.marca-sub{font-size:8.5pt;color:#b9cacb;margin-top:3px}
.portada-titulo{font-size:19pt;font-weight:700;margin:18px 0 14px}
.meta{display:grid;grid-template-columns:repeat(2,1fr);gap:8px 24px}
.meta span{display:block;font-size:7.5pt;text-transform:uppercase;letter-spacing:.06em;color:#8fb3c9}.meta b{font-size:9.5pt;font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.kpi{border:1px solid ${CI.linea};border-left:5px solid;border-radius:10px;padding:10px 14px;background:#fff}
.kpi-valor{font-size:19pt;font-weight:700;color:${CI.navy};line-height:1.15}.kpi-valor span{font-size:9pt;font-weight:600;color:${CI.suave};margin-left:4px}
.kpi-titulo{font-size:8.5pt;color:${CI.suave}}
.minis{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:10px}
.mini{background:${CI.fondo};border-radius:8px;padding:8px 10px}.mini b{display:block;font-size:12pt;color:${CI.navy}}.mini span{font-size:7.8pt;color:${CI.suave}}
.hallazgos{margin:0;padding:12px 16px 12px 32px;background:${CI.fondo};border-radius:10px;border:1px solid ${CI.linea}}
.hallazgos li{margin:3px 0}.hallazgos li::marker{color:${CI.cian}}
.panel{border:1px solid ${CI.linea};border-radius:10px;padding:12px 14px;background:#fff}
.dos-col{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.grafico{width:100%;height:auto;display:block}.grafico .eje{font-size:10px;fill:${CI.suave}}.grafico .valor{font-size:10px;font-weight:700;fill:${CI.tinta}}.grafico .guia{stroke:${CI.linea};stroke-width:1}
.vacio{padding:18px;text-align:center;color:${CI.suave};background:${CI.fondo};border-radius:8px;font-size:9pt}
.embudo-fila{display:grid;grid-template-columns:190px 1fr 110px;align-items:center;gap:10px;margin:7px 0}
.embudo-eti{font-weight:600;font-size:9pt}.embudo-pista{background:${CI.fondo};border-radius:6px;height:20px}.embudo-barra{height:100%;border-radius:6px}
.embudo-val b{font-size:9.5pt}.embudo-val small{color:${CI.suave};margin-left:6px}
.dona{display:flex;align-items:center;gap:14px}.dona-num{font-size:24px;font-weight:700;fill:${CI.navy}}
.leyenda{list-style:none;margin:0;padding:0;flex:1}.leyenda li{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid ${CI.linea};font-size:9pt}
.leyenda b{margin-left:auto}.leyenda small{color:${CI.suave};width:34px;text-align:right}.punto{width:10px;height:10px;border-radius:3px}
.tw{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:8.6pt}
thead th{background:${CI.navy};color:#fff;font-weight:600;padding:7px 8px;text-align:left}
thead th:first-child{border-top-left-radius:8px}thead th:last-child{border-top-right-radius:8px}
td{padding:6px 8px;border-bottom:1px solid ${CI.linea};vertical-align:middle}
tbody tr:nth-child(even) td{background:${CI.fondo}}tr{break-inside:avoid}
tfoot td{border-top:2px solid ${CI.navy};border-bottom:none;font-weight:600}
.n{text-align:right;white-space:nowrap}.c{text-align:center}td.obs{color:${CI.suave};max-width:200px}
.medalla{display:inline-block;width:22px;height:22px;line-height:22px;border-radius:50%;color:#fff;font-weight:700;text-align:center;font-size:8.5pt}
.medalla-n{background:${CI.fondo};color:${CI.suave}}
.pct{position:relative;background:${CI.fondo};border-radius:4px;height:16px;min-width:110px}.pct div{height:100%;background:${CI.cian};border-radius:4px;opacity:.55}
.pct span{position:absolute;left:6px;top:0;font-size:8pt;line-height:16px;font-weight:600}
.estado{display:inline-block;border:1px solid;border-radius:999px;padding:1px 9px;font-size:7.8pt;font-weight:600}
.alerta{color:${CI.rojo}}h2,.nota{break-after:avoid}
.cierre{margin-top:24px;padding-top:10px;border-top:1px solid ${CI.linea};font-size:8pt;color:${CI.suave}}
@media (max-width:640px){.kpis{grid-template-columns:1fr 1fr}.minis{grid-template-columns:1fr 1fr}.dos-col{grid-template-columns:1fr}.meta{grid-template-columns:1fr}.embudo-fila{grid-template-columns:1fr;gap:4px}.dona{flex-direction:column}}`;

function renderInforme(m, gen) {
  const r = m.resumen, fh = `${pad(gen.getDate())}/${pad(gen.getMonth() + 1)}/${gen.getFullYear()}`, hh = `${pad(gen.getHours())}:${pad(gen.getMinutes())}`;
  const periodo = m.periodo ? `${fechaI(m.periodo[0])} – ${fechaI(m.periodo[1])}` : 'Sin registros';
  const logo = new URL('icon.png', location.href).href;
  const prods = m.producciones, fabs = m.fabricaciones, recs = m.recolecciones;
  const ranking = tablaI([['Puesto', 'c'], ['Estudiante / responsable', ''], ['PET (kg)', 'n'], ['% del total', ''], ['Jornadas', 'n'], ['Botellas', 'n'], ['Puntos', 'n']],
    m.ranking.map(x => [medalla(x.puesto), esc(x.nombre), num(x.pet), `<div class="pct"><div style="width:${Math.min(x.participacion, 100).toFixed(1)}%"></div><span>${num(x.participacion, 1)}%</span></div>`, ent(x.jornadas), ent(x.botellas), `<b>${ent(x.puntos)}</b>`]), null, 'No hay responsables registrados.');
  const produccion = tablaI([['#', 'c'], ['Fecha', ''], ['Jornada', 'c'], ['Color', ''], ['Ø mm', 'n'], ['PET (kg)', 'n'], ['Filamento (kg)', 'n'], ['Rendim.', 'n'], ['Usado (kg)', 'n'], ['Disponible (kg)', 'n'], ['Metros', 'n']],
    prods.map(p => [`#${p.id}`, fechaI(p.fecha), p.jornada ? `#${p.jornada}` : '—', esc(p.color), p.diametro != null ? num(p.diametro) : '—', num(p.pet), num(p.obtenido), `${num(p.rendimiento, 1)}%`, num(p.usado), disponible(p.disponible), num(p.metros, 0)]),
    prods.length ? ['', '<b>Total</b>', '', '', '', num(prods.reduce((a, p) => a + p.pet, 0)), num(prods.reduce((a, p) => a + p.obtenido, 0)), `${num(r.rendimiento, 1)}%`, num(prods.reduce((a, p) => a + p.usado, 0)), `<b>${num(prods.reduce((a, p) => a + p.disponible, 0))}</b>`, num(r.metros, 0)] : null,
    'No hay producciones de filamento registradas.');
  const impresiones = tablaI([['#', 'c'], ['Fecha', ''], ['Modelo', ''], ['Filamento', 'c'], ['Piezas', 'n'], ['Peso (g)', 'n'], ['Tiempo', 'n'], ['Estado', 'c']],
    fabs.map(f => [`#${f.id}`, fechaI(f.fecha), esc(f.modelo), f.id_prod ? `#${f.id_prod}` : '—', ent(f.piezas), num(f.peso_g, 1), minutos(f.tiempo_min), estadoI(f.estado)]),
    fabs.length ? ['', '<b>Total</b>', '', '', ent(r.piezas), num(fabs.reduce((a, f) => a + f.peso_g, 0), 1), minutos(fabs.reduce((a, f) => a + f.tiempo_min, 0)), ''] : null,
    'No hay impresiones registradas.');
  const recol = tablaI([['#', 'c'], ['Fecha', ''], ['Responsable', ''], ['Lugar', ''], ['Botellas', 'n'], ['PET (kg)', 'n'], ['Observaciones', 'obs']],
    recs.map(x => [`#${x.id}`, fechaI(x.fecha), esc(x.responsable), esc(x.lugar), ent(x.botellas), num(x.pet), esc(x.obs) || '—']),
    recs.length ? ['', '<b>Total</b>', '', '', ent(recs.reduce((a, x) => a + x.botellas, 0)), num(r.pet_recolectado), ''] : null,
    'No hay jornadas de recolección registradas.');
  return `<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Informe VorTrack ${fh}</title><style>${CSS_INFORME}</style></head><body>
<header class="portada"><div class="marca"><img src="${logo}" alt=""><div><div class="marca-nombre">VorTrack</div>
<div class="marca-sub">Trazabilidad PET → filamento 3D → material didáctico</div></div></div>
<div class="portada-titulo">Informe de gestión y trazabilidad</div><div class="meta">
<div><span>Generado</span><b>${fh} · ${hh}</b></div><div><span>Periodo de datos</span><b>${periodo}</b></div>
${S.user ? `<div><span>Generado por</span><b>${esc(S.user.nombre)}</b></div>` : ''}
<div><span>Institución</span><b>Instituto San Carlos de La Salle · TRANSORE ISC</b></div></div></header>
<section><h2>Resumen ejecutivo</h2><div class="kpis">${[
    kpiI(num(r.pet_recolectado), 'kg', 'PET recolectado', CI.cian), kpiI(num(r.filamento_producido), 'kg', 'Filamento producido', CI.azul),
    kpiI(num(r.desperdicio), 'kg', 'Desperdicio de extrusión', CI.rojo), kpiI(ent(r.objetos_impresos), 'piezas', 'Objetos impresos', CI.verde),
    kpiI(ent(r.botellas), '', 'Botellas recolectadas', CI.navy2), kpiI(ent(r.responsables), '', 'Responsables', CI.ambar)].join('')}</div>
<div class="minis">${[mini(`${num(r.rendimiento, 1)}%`, 'Rendimiento de extrusión'), mini(`${num(r.tasa_exito, 0)}%`, 'Éxito en impresión'),
    mini(`${num(r.pet_por_jornada)} kg`, 'PET promedio por jornada'), mini(num(r.botellas_por_kg, 0), 'Botellas por kg de PET'),
    mini(`${num(r.filamento_disponible)} kg`, 'Filamento disponible'), mini(`${num(r.horas_impresion, 1)} h`, 'Horas de impresión'),
    mini(`${num(r.metros, 0)} m`, 'Metros de filamento'), mini(ent(r.jornadas), 'Jornadas de recolección')].join('')}</div></section>
<section class="bloque"><h2>Hallazgos clave</h2><ul class="hallazgos">${m.hallazgos.map(x => `<li>${esc(x)}</li>`).join('') || '<li>Aún no hay datos suficientes.</li>'}</ul></section>
<section class="bloque"><h2>Flujo del material</h2><p class="nota">Cuánto del PET recolectado avanza en cada etapa de la cadena (porcentaje respecto al PET recolectado).</p>
<div class="panel">${embudo([['PET recolectado', r.pet_recolectado, CI.cian], ['PET transformado', r.pet_transformado, '#33b9c8'], ['Filamento producido', r.filamento_producido, CI.azul], ['Filamento usado en impresión', r.filamento_usado, CI.navy2]])}</div></section>
<section class="dos-col bloque"><div class="panel"><h3>PET recolectado por mes</h3>${svgColumnas(m.pet_por_mes)}</div>
<div class="panel"><h3>PET por lugar de recolección</h3>${svgBarrasH(m.pet_por_lugar)}</div></section>
<section class="bloque"><h2>Participación de estudiantes</h2><p class="nota">Gamificación: 100 puntos por cada kg de PET aportado.</p><div class="tw">${ranking}</div></section>
<section class="dos-col bloque"><div class="panel"><h3>Piezas por estado</h3>${svgDona(m.piezas_por_estado.map(([e, v]) => [e, v, COLOR_ESTADO[e] || CI.suave]), ent(r.piezas), 'piezas')}</div>
<div class="panel"><h3>Piezas impresas por modelo</h3>${svgBarrasH(m.piezas_por_modelo, 'pzs', 0, CI.verde)}</div></section>
<section><h2>Producción de filamento</h2><p class="nota">Rendimiento = filamento obtenido ÷ PET de la jornada. Usado/Disponible según las impresiones registradas con cada producción.</p><div class="tw">${produccion}</div></section>
<section><h2>Impresiones 3D</h2><div class="tw">${impresiones}</div></section>
<section><h2>Detalle de jornadas de recolección</h2><div class="tw">${recol}</div></section>
<footer class="cierre">Documento generado automáticamente por VorTrack a partir de la base de datos <b>vortrack_db</b> el ${fh} a las ${hh}. Las cifras reflejan los registros existentes en ese momento.</footer>
</body></html>`;
}
function abrirInforme(nombre, gen) {
  const capa = document.createElement('div');
  capa.className = 'vt vt-inf';
  capa.innerHTML = `<div class="tb"><span>📄 ${esc(nombre)}</span><button class="pri" data-imp>Imprimir / Guardar PDF</button><button data-x>Cerrar</button></div><iframe title="Informe VorTrack"></iframe>`;
  document.body.appendChild(capa);
  document.documentElement.style.overflow = 'hidden';
  const fr = capa.querySelector('iframe');
  fr.srcdoc = renderInforme(calcularInforme(), gen);
  const cerrar = () => { capa.remove(); document.documentElement.style.overflow = ''; document.removeEventListener('keydown', tecla); };
  const tecla = e => { if (e.key === 'Escape') cerrar(); };
  document.addEventListener('keydown', tecla);
  capa.querySelector('[data-x]').onclick = cerrar;
  capa.querySelector('[data-imp]').onclick = () => fr.contentWindow?.print();
}

/* ============================================================
   Guía de la demo (fuera de la ventana de la app)
   ============================================================ */
const PASOS = [
  ['login', 'Inicia sesión', 'Escribe tu nombre en <b>IDENTIFICADOR</b> y cualquier texto en <b>CREDENCIAL DE ACCESO</b>. Ese nombre será tu estudiante.'],
  ['rec', 'Registra una recolección', 'Pulsa <b>EXPLORAR SISTEMA</b> o <b>REGISTRAR → Recolección</b>. Elige tu nombre como responsable, un lugar, y escribe las botellas y el peso PET (kg).'],
  ['trans', 'Transforma el PET', '<b>REGISTRAR → Transformación</b>: elige tu jornada, escribe el peso salido (no puede superar el ingresado), el color, el diámetro y los metros.'],
  ['imp', 'Registra una impresión', '<b>REGISTRAR → Impresión</b>: elige un modelo y tu filamento. Al escribir la cantidad, VorTrack proyecta el peso y el tiempo. Elige el estado.'],
  ['inf', 'Genera el informe', '<b>HISTÓRICO INFORMES</b>: busca tu nombre en el ranking, prueba las proyecciones y pulsa <b>GENERAR INFORME</b>.'],
];
function pintarGuia() {
  if (!GUIDE) return;
  const sig = PASOS.findIndex(([k]) => !S.hecho[k]);
  GUIDE.innerHTML = `<ol class="guia-pasos">${PASOS.map(([k, t], i) => `<li class="${S.hecho[k] ? 'ok' : i === sig ? 'cur' : ''}"><span>${S.hecho[k] ? '✓' : i + 1}</span>${t}</li>`).join('')}</ol>
    <div class="guia-tip"><span>${sig < 0 ? '🎉 <b>¡Recorriste todo el ciclo de VorTrack!</b> Así se ve la trazabilidad de punta a punta: tu recolección, tu filamento y tus piezas quedaron enlazados en el informe.' : '👉 ' + PASOS[sig][2]}</span>
    <button type="button" class="guia-reset" id="vtReset">↺ Reiniciar demo</button></div>`;
  document.getElementById('vtReset').onclick = async () => {
    if (await msg('q', 'Reiniciar demo', '¿Borrar los datos de esta demo y empezar de cero?', ['Sí', 'No']) !== 'Sí') return;
    S = semilla(); guardar(); navegando = false; ir('login');
  };
}

/* ---------- Arranque ---------- */
pintarGuia();
ir(S.user ? (PAGINAS[S.page] ? S.page : 'inicio') : 'login');
})();
