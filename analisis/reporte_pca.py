#!/usr/bin/env python3
"""
analisis/reporte_pca.py

Reporte HTML del análisis de componentes principales de una dimensión.

Uso:
    python3 analisis/reporte_pca.py Producto

Lee analisis/salidas/pca/pca_<dim>.json (lo genera generar_pca.py, que además llama a
este script al terminar) y escribe analisis/salidas/reportes/reporte_pca_<dim>.html.
El reporte no tiene texto de análisis fijo: todo sale de los datos. Arriba se eligen
el conjunto de variables, la serie (estables o canary) y el enfoque (crudo, ajustado o
ajustado y sin tamaño), y todas las secciones se actualizan.
"""
import argparse
import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reporte_cruce as rc  # noqa: E402

ENTRADA = rc.ROOT / "analisis" / "salidas" / "pca"
SALIDA = rc.ROOT / "analisis" / "salidas" / "reportes"

NOMBRE_CONJUNTO = {"producto": "Métricas a nivel producto", "todas": "Todas las variables de la dimensión"}

ESTILO_PIEZAS = """
.leyenda .lin { display:inline-block; width:18px; height:0; border-top:2px solid var(--serie); margin-right:5px; vertical-align:3px; }
.leyenda .lin.horn { border-top:2px dashed var(--serie2); }
.leyenda .lin.kaiser { border-top:1.5px dashed var(--texto2); }
.leyenda .cuadro { display:inline-block; width:12px; height:12px; border-radius:3px; margin-right:5px; vertical-align:-2px; }
td.celda { text-align: center; font-variant-numeric: tabular-nums; font-size: 12.5px; padding: 6px 4px; min-width: 52px; }
td.celda.fuerte { font-weight: 650; }
td.var { white-space: nowrap; }
svg .scree { stroke: var(--serie); stroke-width: 2; fill: none; }
svg .scree-pt { fill: var(--serie); }
svg .horn { stroke: var(--serie2); stroke-width: 2; stroke-dasharray: 6 4; fill: none; }
svg .kaiser { stroke: var(--texto2); stroke-width: 1.5; stroke-dasharray: 4 4; }
svg .barra-acum { fill: var(--serie); fill-opacity: .25; }
svg .barra-acum.elegido { fill-opacity: .7; }
svg .linea-cp { stroke: var(--serie); stroke-width: 1.4; fill: none; }
svg .ic { stroke: var(--texto2); stroke-width: 1.5; }
svg .pt { fill: var(--serie); }
svg .pt.debil { fill: var(--tenue); }
:root { --cp1:#2a78d6; --cp2:#eb6834; --cp3:#1f9d74; --cp4:#9b59b6; --cp5:#c9a227; --cp6:#d6457a; --cp7:#4aa3b5; --cp8:#7a6f5c; --cp9:#5c7a29; }
@media (prefers-color-scheme: dark) { :root:where(:not([data-theme="light"])) {
  --cp1:#3987e5; --cp2:#d95926; --cp3:#2fb88a; --cp4:#b27ad0; --cp5:#d9b63e; --cp6:#e0628f; --cp7:#5cb8ca; --cp8:#a3987f; --cp9:#82a548; } }
:root[data-theme="dark"] { --cp1:#3987e5; --cp2:#d95926; --cp3:#2fb88a; --cp4:#b27ad0; --cp5:#d9b63e; --cp6:#e0628f; --cp7:#5cb8ca; --cp8:#a3987f; --cp9:#82a548; }
svg .rama { stroke: var(--texto2); stroke-width: 1.3; fill: none; }
svg .corte { stroke: var(--serie2); stroke-width: 1.3; stroke-dasharray: 5 4; }
svg .corte.pca { stroke: var(--serie); }
svg .nula { stroke: var(--texto2); stroke-width: 1.5; stroke-dasharray: 4 4; fill: none; }
.chip { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:4px; vertical-align:-1px; }
.lista-vars { line-height: 1.7; }
.lista-vars span { white-space: nowrap; margin-right: 10px; }
"""

ESTILO_PCA = ESTILO_PIEZAS + """
h2 { scroll-margin-top: 64px; }
.barra-sel { position: sticky; top: 0; z-index: 5; background: var(--fondo); padding: 10px 0 6px;
  border-bottom: 1px solid var(--borde); display: flex; flex-wrap: wrap; gap: 6px 18px; align-items: center; }
.barra-sel .grupo { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--texto2); }
.barra-sel .modo { margin: 0; }
.indice { background: var(--superficie); border: 1px solid var(--borde); border-radius: 10px; padding: 12px 18px; margin: 16px 0 8px; }
.indice ol { margin: 6px 0 0; padding-left: 0; list-style: none; columns: 2; font-size: 14px; }
.indice a { color: var(--texto); }
.dos { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 16px; }
.panel h4 { margin: 0 0 6px; font-size: 14px; }
.mini { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; }
.mini table { font-size: 12px; } .mini td, .mini th { padding: 3px 4px; }
.etiqueta-cp { font-size: 13px; margin: 4px 0; }
.etiqueta-cp b { display: inline-block; min-width: 44px; }
"""

SCRIPT = r"""
const D = JSON.parse(document.getElementById('datosPca').textContent);
const estado = { conjunto: Object.keys(D.conjuntos)[0], serie: 'estable', enfoque: 'ajustado', rotacion: 'varimax', cp: 0 };
const fmt = (v, d = 2) => v === null || v === undefined || Number.isNaN(v) ? '—' : v.toFixed(d).replace('.', ',').replace('-', '−');
const pct = v => v === null || v === undefined ? '—' : Math.round(v * 100) + ' %';
const fechaTxt = f => f ? `${f.slice(6, 8)}/${f.slice(4, 6)}/${f.slice(0, 4)}` : '—';
const fechaMs = f => Date.UTC(+f.slice(0, 4), +f.slice(4, 6) - 1, +f.slice(6, 8));
const clave = (c = estado.conjunto, s = estado.serie, e = estado.enfoque) => `${c}|${s}|${e}`;
const actual = () => D.resultados[clave()];
const vars = () => (actual() && actual().variables) || D.conjuntos[estado.conjunto];
const nom = v => D.nombres[v].replace(/\s*\[producto\]$/, '');

// color divergente desde los tokens del tema
function tokens() {
  const cs = getComputedStyle(document.documentElement);
  const hex = n => { const h = cs.getPropertyValue(n).trim().replace('#', ''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); };
  return { neg: hex('--div-neg'), mid: hex('--div-mid'), pos: hex('--div-pos') };
}
let T = tokens();
function colorCarga(v) {
  if (v === null || v === undefined) return 'transparent';
  const t = Math.min(1, Math.abs(v)), a = T.mid, b = v < 0 ? T.neg : T.pos;
  const c = a.map((x, i) => Math.round(x + (b[i] - x) * t));
  return `rgb(${c.join(',')})`;
}
const textoSobre = v => Math.abs(v ?? 0) > 0.6 ? '#ffffff' : 'var(--texto)';

// ── selectores ──
function barraSel() {
  const grupo = (titulo, campo, opciones) => `<div class="grupo">${titulo}<div class="modo" data-campo="${campo}">`
    + opciones.map(([v, t]) => `<button type="button" data-v="${v}" class="${estado[campo] === v ? 'activo' : ''}">${t}</button>`).join('')
    + '</div></div>';
  const conj = Object.keys(D.conjuntos).map(c => [c, `${c === 'producto' ? 'Nivel producto' : 'Todas'} (${D.conjuntos[c].length})`]);
  document.getElementById('barraSel').innerHTML =
    grupo('Variables', 'conjunto', conj)
    + grupo('Serie', 'serie', Object.entries(D.series))
    + grupo('Enfoque', 'enfoque', Object.entries(D.enfoques));
  document.querySelectorAll('#barraSel .modo button').forEach(b => b.addEventListener('click', () => {
    const campo = b.parentElement.dataset.campo;
    estado[campo] = b.dataset.v; estado.cp = 0;
    todo();
  }));
}

// ── KPIs y datos ──
function kpis() {
  const R = actual(), el = document.getElementById('kpis');
  if (!R) { el.innerHTML = '<p class="vacio">No hay resultados para esta combinación.</p>'; return; }
  const acum = R.acumulada[R.k - 1];
  const k = (v, l, d = '') => `<div class="kpi"><div class="v">${v}</div><div class="l">${l}</div>${d ? `<div class="d">${d}</div>` : ''}</div>`;
  el.innerHTML = k(R.p, 'variables') + k(R.n, 'releases usados', `${fechaTxt(R.desde)} – ${fechaTxt(R.hasta)}`)
    + k(R.backports, 'backports excluidos') + k(R.k, 'componentes retenidos', D.parametros.k_forzado ? 'fijado a mano' : 'análisis paralelo de Horn')
    + k(pct(acum), 'varianza explicada', `por los ${R.k} componentes`);
}

function tablaVariables() {
  const el = document.getElementById('tablaVariables');
  const R = actual(), exc = (R && R.excluidas) || [];
  el.innerHTML = '<table><thead><tr><th>#</th><th>Variable</th><th>Nivel</th></tr></thead><tbody>'
    + vars().map((v, i) => `<tr><td class="n">${i + 1}</td><td>${nom(v)}</td><td>${D.niveles[v] === 'producto' ? 'producto' : 'agregada por colaborador'}</td></tr>`).join('')
    + '</tbody></table>'
    + (exc.length ? `<p class="nota">No entran en esta combinación (sin datos en al menos la mitad de las ventanas de la serie, o de la familia tamaño en el enfoque sin tamaño): ${exc.map(nom).join(', ')}.</p>` : '');
}

// ── cuántos componentes ──
function scree() {
  const R = actual(), el = document.getElementById('scree');
  if (!R) { el.innerHTML = ''; return; }
  const p = R.p, W = 520, H = 280, m = { l: 44, r: 14, t: 14, b: 36 };
  const ymax = Math.ceil(Math.max(...R.autovalores, ...R.horn95, 1.2));
  const sx = i => m.l + (i) / (p - 1) * (W - m.l - m.r), sy = v => m.t + (1 - v / ymax) * (H - m.t - m.b);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Gráfico de sedimentación">`;
  for (let v = 0; v <= ymax; v += ymax > 4 ? 1 : 0.5) s += `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(v)}" y2="${sy(v)}" class="grid"/><text x="${m.l - 6}" y="${sy(v)}" class="ticky">${fmt(v, ymax > 4 ? 0 : 1)}</text>`;
  for (let i = 0; i < p; i++) s += `<text x="${sx(i)}" y="${H - m.b + 6}" class="tick">${i + 1}</text>`;
  s += `<text x="${(m.l + W - m.r) / 2}" y="${H - 6}" class="eje">componente</text>`;
  s += `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(1)}" y2="${sy(1)}" class="kaiser"/>`;
  s += `<path d="${R.horn95.map((v, i) => (i ? 'L' : 'M') + sx(i) + ',' + sy(v)).join('')}" class="horn"/>`;
  s += `<path d="${R.autovalores.map((v, i) => (i ? 'L' : 'M') + sx(i) + ',' + sy(v)).join('')}" class="scree"/>`;
  R.autovalores.forEach((v, i) => {
    s += `<circle cx="${sx(i)}" cy="${sy(v)}" r="${i < R.k ? 5 : 3.5}" class="scree-pt" fill-opacity="${i < R.k ? 1 : .45}"><title>CP${i + 1}: autovalor ${fmt(v)} · Horn (p${D.parametros.percentil_horn}) ${fmt(R.horn95[i])} · ${pct(R.varianza[i])} de la varianza</title></circle>`;
  });
  el.innerHTML = s + '</svg>';
}

function acumulada() {
  const R = actual(), el = document.getElementById('acumulada');
  if (!R) { el.innerHTML = ''; return; }
  const p = R.p, W = 520, H = 280, m = { l: 44, r: 14, t: 14, b: 36 };
  const bw = (W - m.l - m.r) / p, sy = v => m.t + (1 - v) * (H - m.t - m.b);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Varianza acumulada">`;
  for (const v of [0, .25, .5, .75, 1]) s += `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(v)}" y2="${sy(v)}" class="grid"/><text x="${m.l - 6}" y="${sy(v)}" class="ticky">${v * 100}%</text>`;
  R.acumulada.forEach((v, i) => {
    const x = m.l + i * bw;
    s += `<rect x="${x + 3}" y="${sy(v)}" width="${bw - 6}" height="${sy(0) - sy(v)}" class="barra-acum${i < R.k ? ' elegido' : ''}"><title>${i + 1} componentes: ${pct(v)}</title></rect>`
      + `<text x="${x + bw / 2}" y="${H - m.b + 6}" class="tick">${i + 1}</text>`;
  });
  for (const u of [.7, .8]) s += `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(u)}" y2="${sy(u)}" class="ref"/><text x="${W - m.r - 2}" y="${sy(u) - 5}" class="ref-txt" text-anchor="end">${u * 100}%</text>`;
  s += `<text x="${(m.l + W - m.r) / 2}" y="${H - 6}" class="eje">cantidad de componentes</text>`;
  el.innerHTML = s + '</svg>';
}

const CRITERIOS = [['kaiser', 'Kaiser'], ['codo', 'Codo'], ['varianza_70', 'Varianza ≥ 70 %'],
  ['varianza_80', 'Varianza ≥ 80 %'], ['horn', 'Horn']];

function tablaCriterios() {
  const el = document.getElementById('criterios');
  const filas = [];
  for (const s of Object.keys(D.series)) for (const e of Object.keys(D.enfoques)) {
    const R = D.resultados[clave(estado.conjunto, s, e)];
    if (R) filas.push([s, e, R]);
  }
  el.innerHTML = '<table><thead><tr><th>Serie</th><th>Enfoque</th><th>n</th>' + CRITERIOS.map(([, t]) => `<th>${t}</th>`).join('')
    + '<th>Retenidos</th><th>Varianza explicada</th></tr></thead><tbody>'
    + filas.map(([s, e, R]) => `<tr${s === estado.serie && e === estado.enfoque ? ' style="background:var(--hover)"' : ''}>
      <td>${D.series[s]}</td><td>${D.enfoques[e]}</td><td class="n">${R.n}</td>`
      + CRITERIOS.map(([c]) => `<td class="n">${R.criterios[c]}</td>`).join('')
      + `<td class="n"><b>${R.k}</b></td><td class="n">${pct(R.acumulada[R.k - 1])}</td></tr>`).join('')
    + '</tbody></table>';
}

// ── cargas ──
function cargasActuales(R) { return estado.rotacion === 'varimax' ? R.varimax : R.cargas; }

function mapaCargas() {
  const R = actual(), el = document.getElementById('mapaCargas');
  if (!R) { el.innerHTML = ''; return; }
  const L = cargasActuales(R), vs = vars(), k = R.k;
  const varCp = Array.from({ length: k }, (_, j) => L.reduce((a, f) => a + f[j] ** 2, 0) / R.p);
  el.innerHTML = '<table><thead><tr><th>Variable</th>' + Array.from({ length: k }, (_, j) => `<th style="text-align:center">CP${j + 1}<br><span class="cuenta">${pct(varCp[j])}</span></th>`).join('')
    + '<th style="text-align:center">Comunalidad</th></tr></thead><tbody>'
    + vs.map((v, i) => {
      const com = L[i].reduce((a, x) => a + x * x, 0);
      return `<tr><td class="var">${nom(v)}</td>` + L[i].map((x, j) => {
        const ic = estado.rotacion === 'varimax' ? ` · IC bootstrap [${fmt(R.boot.p025[i][j])}; ${fmt(R.boot.p975[i][j])}]` : '';
        return `<td class="celda${Math.abs(x) >= .4 ? ' fuerte' : ''}" style="background:${colorCarga(x)};color:${textoSobre(x)}" title="${nom(v)} en CP${j + 1}: ${fmt(x)}${ic}">${fmt(x)}</td>`;
      }).join('') + `<td class="n" style="text-align:center">${fmt(com)}</td></tr>`;
    }).join('') + '</tbody></table>';
  // resumen de cada componente: variables con |carga| >= 0,4
  const res = Array.from({ length: k }, (_, j) => {
    const fuertes = vs.map((v, i) => [v, L[i][j]]).filter(([, x]) => Math.abs(x) >= .4).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
    return `<p class="etiqueta-cp"><b>CP${j + 1}</b> ${fuertes.length ? fuertes.map(([v, x]) => `${nom(v)} (${x > 0 ? '+' : ''}${fmt(x)})`).join(', ') : '<span class="cuenta">ninguna variable con |carga| ≥ 0,4</span>'}</p>`;
  });
  document.getElementById('resumenCp').innerHTML = res.join('');
}

// ── puntajes ──
function puntajes() {
  const R = actual(), el = document.getElementById('puntajes');
  if (!R) { el.innerHTML = ''; return; }
  const pts = R.puntajes.map(f => ({ t: fechaMs(f[2]), v: f[1], f: f[2], s: f.slice(3) }));
  const t0 = pts[0].t, t1 = pts[pts.length - 1].t, W = 1000, fila = 92, m = { l: 54, r: 12, t: 8, b: 28 };
  const H = m.t + R.k * fila + m.b;
  const sx = t => m.l + (t - t0) / ((t1 - t0) || 1) * (W - m.l - m.r);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Puntajes de los componentes en el tiempo">`;
  for (let a = new Date(t0).getUTCFullYear() + 1; a <= new Date(t1).getUTCFullYear(); a++) {
    const x = sx(Date.UTC(a, 0, 1));
    s += `<line x1="${x}" x2="${x}" y1="${m.t}" y2="${H - m.b}" class="grid"/><text x="${x}" y="${H - m.b + 6}" class="tick">${a}</text>`;
  }
  for (let j = 0; j < R.k; j++) {
    const vals = pts.map(o => o.s[j]), lim = Math.max(3, ...vals.map(Math.abs));
    const y0 = m.t + j * fila, sy = v => y0 + 10 + (1 - (v + lim) / (2 * lim)) * (fila - 20);
    s += `<text x="${m.l - 8}" y="${y0 + fila / 2}" class="ticky" style="font-weight:600;fill:var(--texto)">CP${j + 1}</text>`
      + `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(0)}" y2="${sy(0)}" class="cero"/>`
      + `<path d="${pts.map((o, i) => (i ? 'L' : 'M') + sx(o.t).toFixed(1) + ',' + sy(o.s[j]).toFixed(1)).join('')}" class="linea-cp"/>`;
  }
  s += `<line class="guia" y1="${m.t}" y2="${H - m.b}" x1="-10" x2="-10"/>`;
  el.innerHTML = s + '</svg><div class="tooltip"></div>';
  const svg = el.querySelector('svg'), tip = el.querySelector('.tooltip'), guia = svg.querySelector('.guia');
  svg.addEventListener('pointermove', ev => {
    const r = svg.getBoundingClientRect(), k = W / r.width, px = (ev.clientX - r.left) * k;
    let mejor = pts[0], d = Infinity;
    for (const o of pts) { const dd = Math.abs(sx(o.t) - px); if (dd < d) { d = dd; mejor = o; } }
    guia.setAttribute('x1', sx(mejor.t)); guia.setAttribute('x2', sx(mejor.t));
    tip.innerHTML = `<b>${mejor.v}</b> · ${fechaTxt(mejor.f)}<br>` + mejor.s.map((v, j) => `CP${j + 1}: ${fmt(v)}`).join(' · ');
    tip.style.display = 'block';
    const cx = sx(mejor.t) / k, ancho = tip.offsetWidth;
    tip.style.left = (cx + 12 + ancho > r.width ? cx - ancho - 12 : cx + 12) + 'px'; tip.style.top = '0px';
  });
  svg.addEventListener('pointerleave', () => { tip.style.display = 'none'; guia.setAttribute('x1', -10); guia.setAttribute('x2', -10); });
}

// ── solidez ──
function solidez() {
  const R = actual(), el = document.getElementById('solidezCp');
  if (!R) { el.innerHTML = ''; return; }
  const b = R.boot;
  el.innerHTML = '<table><thead><tr><th>Componente</th><th>Congruencia mediana</th><th>Congruencia p5</th><th>Autovalor</th><th>IC 95 % del autovalor</th><th>Lectura</th></tr></thead><tbody>'
    + Array.from({ length: R.k }, (_, j) => {
      const c = b.congruencia_mediana[j];
      const p5 = b.congruencia_p05[j];
      const lectura = c >= .95 && p5 >= .85 ? 'muy estable' : c >= .85 ? 'estable' + (p5 < .85 ? ' (en algunos remuestreos se mezcla con otro componente)' : '') : 'inestable';
      return `<tr><td>CP${j + 1}</td><td class="n">${fmt(c)}</td><td class="n">${fmt(b.congruencia_p05[j])}</td><td class="n">${fmt(R.autovalores[j])}</td>
        <td class="n">[${fmt(b.autoval_p025[j])}; ${fmt(b.autoval_p975[j])}]</td><td>${lectura}</td></tr>`;
    }).join('') + '</tbody></table>';
  document.getElementById('notaBoot').textContent = `${D.parametros.bootstrap} remuestreos de bloques de ${b.largo_bloque} releases consecutivos. `
    + 'Congruencia de Tucker entre las cargas varimax de cada remuestreo y las originales: ≥ 0,95 el componente es prácticamente el mismo; 0,85–0,95, parecido; < 0,85, distinto.';
  // selector de componente para el gráfico de cargas con IC
  const sel = document.getElementById('cpForest');
  sel.innerHTML = Array.from({ length: R.k }, (_, j) => `<button type="button" data-j="${j}" class="${j === estado.cp ? 'activo' : ''}">CP${j + 1}</button>`).join('');
  sel.querySelectorAll('button').forEach(bt => bt.addEventListener('click', () => { estado.cp = +bt.dataset.j; solidez(); }));
  forestCargas();
}

function forestCargas() {
  const R = actual(), el = document.getElementById('forestCargas'), j = Math.min(estado.cp, R.k - 1);
  const vs = vars(), b = R.boot, LW = 260, W = 760, fila = 24, top = 8, H = top + vs.length * fila + 28;
  const sx = v => LW + (v + 1) / 2 * (W - LW - 70);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Cargas con intervalo bootstrap">`;
  for (const v of [-1, -.5, 0, .5, 1]) s += `<line x1="${sx(v)}" x2="${sx(v)}" y1="${top}" y2="${top + vs.length * fila}" class="${v ? 'grid' : 'cero'}"/><text x="${sx(v)}" y="${top + vs.length * fila + 6}" class="tick">${fmt(v, 1)}</text>`;
  for (const v of [-.4, .4]) s += `<line x1="${sx(v)}" x2="${sx(v)}" y1="${top}" y2="${top + vs.length * fila}" class="umbral"/>`;
  vs.forEach((v, i) => {
    const y = top + i * fila + fila / 2, x = R.varimax[i][j], a = b.p025[i][j], z = b.p975[i][j];
    const debil = Math.abs(x) < .4;
    s += `<text x="${LW - 10}" y="${y}" class="cat">${nom(v)}</text>`
      + `<line x1="${sx(a)}" x2="${sx(z)}" y1="${y}" y2="${y}" class="ic"/>`
      + `<circle cx="${sx(x)}" cy="${y}" r="5" class="pt${debil ? ' debil' : ''}"><title>${nom(v)}: ${fmt(x)} [${fmt(a)}; ${fmt(z)}] · mismo componente dominante en el ${pct(b.dominante_estable[i])} de los remuestreos</title></circle>`
      + `<text x="${W - 4}" y="${y}" class="val" text-anchor="end">${pct(b.dominante_estable[i])}</text>`;
  });
  el.innerHTML = s + '</svg>';
}

// ── comparación ──
function comparacion() {
  const el = document.getElementById('comparacion'), mini = document.getElementById('miniCargas');
  const filas = D.comparacion.filter(c => c.conjunto === estado.conjunto);
  if (!filas.length) { el.innerHTML = '<p class="vacio">Sin comparación.</p>'; mini.innerHTML = ''; return; }
  const kRef = filas[0].k_comparado;
  const confs = [];
  for (const s of Object.keys(D.series)) for (const e of Object.keys(D.enfoques)) {
    const f = filas.filter(c => c.serie === s && c.enfoque === e).sort((a, b) => a.componente - b.componente);
    if (f.length) confs.push([s, e, f]);
  }
  const celda = v => {
    const col = v >= .95 ? 'var(--div-neg)' : v >= .85 ? 'color-mix(in srgb, var(--div-neg) 45%, var(--superficie))' : 'var(--div-mid)';
    return `<td class="celda" style="background:${col};color:${v >= .95 ? '#fff' : 'var(--texto)'}">${fmt(v)}</td>`;
  };
  el.innerHTML = `<table><thead><tr><th>Serie</th><th>Enfoque</th><th>Componentes propios</th>`
    + Array.from({ length: kRef }, (_, j) => `<th style="text-align:center">CP${j + 1}</th>`).join('') + '</tr></thead><tbody>'
    + confs.map(([s, e, f]) => `<tr><td>${D.series[s]}</td><td>${D.enfoques[e]}</td><td class="n">${f[0].k_propio}</td>${f.map(c => celda(c.congruencia)).join('')}</tr>`).join('')
    + '</tbody></table>';
  mini.innerHTML = confs.map(([s, e, f]) => `<div class="panel" style="margin-top:0"><h4>${D.series[s]} · ${D.enfoques[e]}</h4><table><tbody>`
    + (f[0].variables || vars()).map((v, i) => `<tr><td class="var" style="max-width:150px;overflow:hidden;text-overflow:ellipsis" title="${nom(v)}">${nom(v)}</td>`
      + f.map(c => { const x = c.cargas[i]; return `<td class="celda" style="background:${colorCarga(x)};color:${textoSobre(x)};min-width:34px">${fmt(x, 1)}</td>`; }).join('') + '</tr>').join('')
    + '</tbody></table></div>').join('');
}

function todo() {
  barraSel(); kpis(); tablaVariables(); scree(); acumulada(); tablaCriterios(); mapaCargas(); puntajes(); solidez(); comparacion();
  document.querySelectorAll('.cfg-actual').forEach(e => e.textContent = `${D.series[estado.serie]} · ${D.enfoques[estado.enfoque]} · ${estado.conjunto === 'producto' ? 'nivel producto' : 'todas las variables'}`);
}
document.querySelectorAll('#modoRot button').forEach(b => b.addEventListener('click', () => {
  estado.rotacion = b.dataset.v;
  document.querySelectorAll('#modoRot button').forEach(x => x.classList.toggle('activo', x === b));
  mapaCargas();
}));
const mq = window.matchMedia('(prefers-color-scheme: dark)');
mq.addEventListener('change', () => { T = tokens(); todo(); });
todo();
"""


def archivo(dim: str) -> Path:
    return SALIDA / f"reporte_pca_{dim.lower()}.html"


def escribir(dim: str) -> Path:
    entrada = ENTRADA / f"pca_{dim.lower()}.json"
    if not entrada.exists():
        sys.exit(f"No existe {entrada}. Corré primero: python3 analisis/generar_pca.py {dim}")
    d = json.loads(entrada.read_text(encoding="utf-8"))
    p = d["parametros"]
    titulo = f"Componentes principales · {d['dimension']}"
    secciones = [("s-datos", "1. Datos"), ("s-cuantos", "2. Cuántos componentes"), ("s-cargas", "3. Cargas"),
                 ("s-puntajes", "4. Puntajes en el tiempo"), ("s-solidez", "5. Solidez (bootstrap de bloques)"),
                 ("s-comparacion", "6. Comparación entre enfoques y series")]
    C = cargar_clustering(d["dimension"])
    seccion_clus = ""
    if C:
        secciones.append(("s-clustering", "7. Clustering de métricas"))
        bloques = "".join(f'<div class="clus" data-clave="{html.escape(cl)}" style="display:none">{_bloque_clustering(d, C, cl)}</div>'
                          for cl in C["resultados"])
        pc = C["parametros"]
        seccion_clus = f"""
<h2 id="s-clustering">7. Clustering de métricas</h2>
<p class="sub">Mostrando: <span class="cfg-actual"></span>. Agrupamiento jerárquico de las mismas variables y releases que el PCA,
calculado por separado: distancia {html.escape(pc['distancia'])} entre métricas y enlace {html.escape(pc['enlace'])}. La cantidad de grupos se
elige con la silueta frente a {pc['permutaciones']} conjuntos de datos permutados al azar; también se muestra el corte con tantos
grupos como componentes retiene el PCA, para compararlos.</p>
{bloques}
<p class="vacio" id="clusVacio" style="display:none">No hay clustering para esta combinación.</p>"""
    conjuntos = "".join(f"<li><b>{html.escape(NOMBRE_CONJUNTO.get(c, c))}</b> ({len(v)} variables)</li>"
                        for c, v in d["conjuntos"].items())
    doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo)}</title><style>{rc.ESTILO}{ESTILO_PCA}</style></head>
<body><main>
<h1>{html.escape(titulo)}</h1>
<p class="sub">Fuente: analisis/salidas/pca/pca_{d['dimension'].lower()}.json (generar_pca.py) · rangos estandarizados · sin backports</p>
<div class="barra-sel" id="barraSel"></div>
<nav class="indice"><b>Contenido</b><ol>{"".join(f'<li><a href="#{a}">{t}</a></li>' for a, t in secciones)}</ol></nav>
<div class="kpis" id="kpis"></div>

<h2 id="s-datos">1. Datos</h2>
<p class="sub">Cada fila es un release y cada columna una variable; se usan los releases con valor en todas las variables
del conjunto. Conjuntos:</p>
<ul>{conjuntos}</ul>
<p class="nota">Enfoques: <b>crudo</b> usa los rangos de los valores; <b>ajustado</b> quita a cada rango la tendencia de
largo plazo (spline de 4 grados de libertad sobre el orden de los releases) y la duración de la ventana, igual que la
correlación corregida; <b>ajustado y sin tamaño</b> además quita el log de los activos de interacción. Los backports
(parches de una versión mayor anterior) se excluyen en las dos series.</p>
<div class="panel tabla" id="tablaVariables"></div>

<h2 id="s-cuantos">2. Cuántos componentes</h2>
<p class="sub">Mostrando: <span class="cfg-actual"></span>. Los componentes retenidos son los que superan el análisis paralelo de Horn.</p>
<div class="dos">
  <div class="panel"><h4>Gráfico de sedimentación (scree)</h4><div class="grafico-disp" id="scree"></div>
    <div class="leyenda"><span><i class="lin"></i>autovalor</span><span><i class="lin horn"></i>Horn: p{p['percentil_horn']} de {p['permutaciones']} permutaciones</span><span><i class="lin kaiser"></i>Kaiser (1)</span></div>
    <p class="nota">Puntos grandes: componentes retenidos.</p></div>
  <div class="panel"><h4>Varianza acumulada</h4><div class="grafico-disp" id="acumulada"></div>
    <p class="nota">Barras oscuras: componentes retenidos. Líneas: 70 % y 80 %.</p></div>
</div>
<div class="panel tabla"><h4>Criterios por serie y enfoque</h4><div id="criterios"></div>
  <p class="nota">Cantidad de componentes que indica cada criterio. Kaiser: autovalor mayor a 1. Codo: punto donde el scree
  se aplana. Varianza: componentes necesarios para explicar el 70 % o el 80 %. Horn: autovalores mayores que el percentil
  {p['percentil_horn']} de los de datos permutados al azar. La fila resaltada es la combinación elegida arriba.</p></div>

<h2 id="s-cargas">3. Cargas</h2>
<p class="sub">Mostrando: <span class="cfg-actual"></span>. La carga es la correlación entre la variable y el componente.</p>
<div class="panel">
  <div class="modo" id="modoRot"><button type="button" data-v="varimax" class="activo">Varimax</button><button type="button" data-v="sin">Sin rotar</button></div>
  <div class="tabla" id="mapaCargas"></div>
  <div class="leyenda"><span><i class="cuadro" style="background:var(--div-neg)"></i>negativa</span><span><i class="cuadro" style="background:var(--div-pos)"></i>positiva</span><span>en negrita: |carga| ≥ 0,4</span></div>
  <p class="nota">Debajo de cada componente, el porcentaje de la varianza total que explica. Comunalidad: parte de la variable
  explicada por los componentes retenidos. El signo de cada componente es arbitrario: se orienta para que su carga de mayor
  valor absoluto sea positiva.</p>
  <h4 style="margin-top:14px">Variables que definen cada componente (|carga| ≥ 0,4)</h4>
  <div id="resumenCp"></div>
</div>

<h2 id="s-puntajes">4. Puntajes en el tiempo</h2>
<p class="sub">Mostrando: <span class="cfg-actual"></span>. Valor de cada componente (varimax, estandarizado) en cada release.</p>
<div class="panel grafico-disp" id="puntajes"></div>

<h2 id="s-solidez">5. Solidez (bootstrap de bloques)</h2>
<p class="sub">Mostrando: <span class="cfg-actual"></span>.</p>
<div class="panel tabla" id="solidezCp"></div>
<p class="nota" id="notaBoot"></p>
<div class="panel"><h4>Cargas varimax con intervalo bootstrap (95 %)</h4>
  <div class="modo" id="cpForest"></div>
  <div id="forestCargas"></div>
  <p class="nota">A la derecha: en qué porcentaje de los remuestreos la variable carga más en el mismo componente que en la
  solución original. Puntos grises: |carga| &lt; 0,4.</p></div>

<h2 id="s-comparacion">6. Comparación entre enfoques y series</h2>
<p class="sub">Cada solución se calcula con la cantidad de componentes de la referencia (estables, ajustado) y se compara con
ella por la congruencia de Tucker, después de emparejar los componentes.</p>
<div class="panel tabla" id="comparacion"></div>
<div class="leyenda"><span><i class="cuadro" style="background:var(--div-neg)"></i>≥ 0,95: el mismo componente</span><span><i class="cuadro" style="background:color-mix(in srgb, var(--div-neg) 45%, var(--superficie))"></i>0,85–0,95: parecido</span><span><i class="cuadro" style="background:var(--div-mid)"></i>&lt; 0,85: distinto</span></div>
<div class="mini" id="miniCargas" style="margin-top:12px"></div>
{seccion_clus}

<script type="application/json" id="datosPca">{json.dumps(d, ensure_ascii=False).replace("</", "<\\/")}</script>
<script>{SCRIPT}</script>
<script>{SCRIPT_CLUSTERING if C else ""}</script>
<p class="nota">Semilla {p['semilla']} · {p['permutaciones']} permutaciones (Horn) · {p['bootstrap']} remuestreos bootstrap.</p>
</main></body></html>
"""
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = archivo(d["dimension"])
    destino.write_text(doc, encoding="utf-8")
    return destino


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dimension", help="Persona, Proceso o Producto")
    args = ap.parse_args()
    destino = escribir(args.dimension.strip().capitalize())
    print(f"Reporte: {destino} ({destino.stat().st_size / 1e6:.1f} MB)")



# ── Piezas estáticas para el informe (generar_informe.py: marcas [[pca ...]]) ─────────────────

def cargar(dim: str) -> dict | None:
    entrada = ENTRADA / f"pca_{dim.lower()}.json"
    if not entrada.exists():
        return None
    d = json.loads(entrada.read_text(encoding="utf-8"))
    d["clustering"] = cargar_clustering(dim)
    return d


# ── Clustering de métricas (generar_clustering.py) ───────────────────────────

SCRIPT_CLUSTERING = r"""
function mostrarClustering() {
  let hay = false;
  document.querySelectorAll('.clus').forEach(e => { const ok = e.dataset.clave === clave(); e.style.display = ok ? '' : 'none'; hay = hay || ok; });
  const v = document.getElementById('clusVacio'); if (v) v.style.display = hay ? 'none' : '';
}
const _todoPca = todo;
todo = function () { _todoPca(); mostrarClustering(); };
mostrarClustering();
"""

NOMBRE_SOLUCION = {"propio": "Corte elegido por el clustering", "pca": "Corte con tantos grupos como componentes del PCA"}


def cargar_clustering(dim: str) -> dict | None:
    entrada = ENTRADA / f"clustering_{dim.lower()}.json"
    return json.loads(entrada.read_text(encoding="utf-8")) if entrada.exists() else None


def _cp_color(c):
    return f"var(--cp{(c - 1) % 9 + 1})" if c else "var(--tenue)"


def _corto(d, v):
    n = _nombre(d, v)
    base, _, resto = n.partition(" (")
    # sigla con su nombre largo entre paréntesis: alcanza la sigla; si no, el texto sin el paréntesis
    return base if len(base) <= 28 else base[:26] + "…"


def _chip_var(d, v, c):
    return (f'<span title="{html.escape(_nombre(d, v))}"><i class="chip" style="background:{_cp_color(c)}"></i>'
            f'{html.escape(_corto(d, v))}</span>')


def _leyenda_cp(Ck):
    cps = sorted({c for c in Ck["referencia_pca"] if c})
    items = "".join(f'<span><i class="cuadro" style="background:{_cp_color(c)}"></i>CP{c}</span>' for c in cps)
    return f'<div class="leyenda">{items}<span><i class="cuadro" style="background:var(--tenue)"></i>sin componente</span></div>'


def _altura_corte(dn, k, p):
    hs = sorted(dc[1] for dc in dn["dcoord"])
    i = p - k - 1
    if i < 0 or i + 1 >= len(hs) + 1:
        return None
    alto = hs[i + 1] if i + 1 < len(hs) else hs[-1] * 1.04
    return (hs[i] + alto) / 2


def _dendro_svg(d, Ck, W=720):
    p, dn, vs, ref = Ck["p"], Ck["dendrograma"], Ck["variables"], Ck["referencia_pca"]
    fila, m = 22, dict(l=190, r=24, t=10, b=40)
    H = m["t"] + p * fila + m["b"]
    dmax = max(max(x) for x in dn["dcoord"]) * 1.05 or 1
    sx = lambda dist: m["l"] + dist / dmax * (W - m["l"] - m["r"])
    sy = lambda ic: m["t"] + (ic - 5) / 10 * fila + fila / 2
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Dendrograma de las métricas">']
    paso = 0.25 if dmax > 0.6 else 0.1
    v = 0.0
    while v <= dmax + 1e-9:
        x = sx(v)
        s.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{m["t"]}" y2="{H - m["b"]}" class="grid"/>'
                 f'<text x="{x:.1f}" y="{H - m["b"] + 6}" class="tick">{_f(v, 2)}</text>')
        v += paso
    s.append(f'<text x="{(m["l"] + W - m["r"]) / 2}" y="{H - 6}" class="eje">distancia (1 − |correlación|) a la que se unen</text>')
    for ic, dc in zip(dn["icoord"], dn["dcoord"]):
        s.append('<path d="' + "".join(f'{"L" if i else "M"}{sx(dc[i]):.1f},{sy(ic[i]):.1f}' for i in range(4)) + '" class="rama"/>')
    for nombre, clase in (("pca", "corte pca"), ("propio", "corte")):
        sol = Ck["soluciones"].get(nombre)
        if not sol:
            continue
        h = _altura_corte(dn, sol["k"], p)
        if h is None:
            continue
        x = sx(h)
        s.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{m["t"]}" y2="{H - m["b"]}" class="{clase}"><title>Corte en {sol["k"]} grupos</title></line>')
    for pos, i in enumerate(dn["hojas"]):
        y = m["t"] + pos * fila + fila / 2
        s.append(f'<rect x="{m["l"] - 14}" y="{y - 5}" width="10" height="10" rx="2" style="fill:{_cp_color(ref[i])}"/>'
                 f'<text x="{m["l"] - 20}" y="{y}" class="ticky">{html.escape(_corto(d, vs[i]))}<title>{html.escape(_nombre(d, vs[i]))}</title></text>')
    s.append("</svg>")
    return "".join(s)


def _silueta_svg(Ck, W=420, H=230):
    ks = Ck["ks"]
    sil = [Ck["silueta"][str(k)] for k in ks]
    nul = [Ck["nula_p95"][str(k)] for k in ks]
    m = dict(l=44, r=14, t=12, b=36)
    ymax = max([x for x in sil + nul if x is not None] + [0.1]) * 1.15
    sx = lambda k: m["l"] + (k - ks[0]) / max(1, ks[-1] - ks[0]) * (W - m["l"] - m["r"])
    sy = lambda v: m["t"] + (1 - v / ymax) * (H - m["t"] - m["b"])
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Silueta según la cantidad de grupos">']
    paso = 0.1 if ymax > 0.3 else 0.05
    v = 0.0
    while v <= ymax + 1e-9:
        s.append(f'<line x1="{m["l"]}" x2="{W - m["r"]}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" class="grid"/>'
                 f'<text x="{m["l"] - 6}" y="{sy(v):.1f}" class="ticky">{_f(v, 2)}</text>')
        v += paso
    for k in ks:
        s.append(f'<text x="{sx(k):.1f}" y="{H - m["b"] + 6}" class="tick">{k}</text>')
    s.append(f'<text x="{(m["l"] + W - m["r"]) / 2}" y="{H - 6}" class="eje">cantidad de grupos</text>')
    s.append('<path d="' + "".join(f'{"L" if i else "M"}{sx(k):.1f},{sy(v):.1f}' for i, (k, v) in enumerate(zip(ks, nul))) + '" class="nula"/>')
    s.append('<path d="' + "".join(f'{"L" if i else "M"}{sx(k):.1f},{sy(v):.1f}' for i, (k, v) in enumerate(zip(ks, sil))) + '" class="scree"/>')
    for k, v in zip(ks, sil):
        grande = k in (Ck["k_propio"], Ck["k_pca"])
        s.append(f'<circle cx="{sx(k):.1f}" cy="{sy(v):.1f}" r="{5 if grande else 3}" class="scree-pt" '
                 f'style="fill:{"var(--serie2)" if k == Ck["k_propio"] else "var(--serie)"}"><title>{k} grupos: silueta {_f(v)} · azar p95 {_f(Ck["nula_p95"][str(k)])}</title></circle>')
    s.append("</svg>")
    return "".join(s)


def _tablas_solucion(d, Ck, R, nombre):
    sol = Ck["soluciones"][nombre]
    vs, ref = Ck["variables"], Ck["referencia_pca"]
    boot = R["boot"]["congruencia_mediana"]
    filas = []
    for g in sol["grupos"]:
        chips = "".join(_chip_var(d, v, ref[vs.index(v)]) for v in g["variables"])
        if g["componente"]:
            comp = (f'CP{g["componente"]} · comparte {len(g["compartidas"])} de {len(g["variables"])} variables '
                    f'(Jaccard {_f(g["jaccard"])})')
        else:
            comp = "ninguno: sus variables no cargan en ningún componente"
        filas.append(f'<tr><td class="lista-vars">{chips}</td><td>{comp}</td></tr>')
    t1 = (f'<table><thead><tr><th>Grupo del clustering</th><th>Componente del PCA más parecido</th></tr></thead>'
          f'<tbody>{"".join(filas)}</tbody></table>')
    filas = []
    for c in sol["por_componente"]:
        chips = "".join(_chip_var(d, v, c["componente"]) for v in c["variables"]) or "—"
        n = len(c["grupos"])
        destino = ("todas en el mismo grupo" if c["completo"] else
                   f'repartidas en {n} grupos' if n > 1 else "—")
        firme = boot[c["componente"] - 1]
        filas.append(f'<tr><td><b>CP{c["componente"]}</b><br><span class="cuenta">bootstrap {_f(firme)}</span></td>'
                     f'<td class="lista-vars">{chips}</td><td>{destino}</td></tr>')
    t2 = (f'<table><thead><tr><th>Componente</th><th>Variables con |carga| ≥ 0,4</th><th>En el clustering</th></tr></thead>'
          f'<tbody>{"".join(filas)}</tbody></table>')
    sin = [v for v, c in zip(vs, ref) if c is None]
    nota = (f'<p class="nota">Sin componente en el PCA (ninguna carga llega a 0,4): '
            f'{", ".join(html.escape(_nombre(d, v)) for v in sin)}. El clustering, en cambio, asigna cada variable a un grupo.</p>'
            if sin else "")
    est = sol["estabilidad"]
    kp = (f'<p class="etiqueta-cp">{sol["k"]} grupos · silueta {_f(sol["silueta"])} (azar p95 {_f(sol["nula_p95"])}) · '
          f'estabilidad en el bootstrap {_f(est["mediana"])} (p5 {_f(est["p05"])}) · '
          f'réplica en canary {_f(sol.get("ari_canary"))} · coincidencia con el PCA (ARI) {_f(sol["ari_pca"])}</p>')
    return (f'<div class="panel inserto tabla"><h4>{NOMBRE_SOLUCION[nombre]}</h4>{kp}{t1}'
            f'<h4 style="margin-top:12px">Dónde quedan los componentes del PCA</h4>{t2}{nota}</div>')


def _bloque_clustering(d, C, clave):
    Ck, R = C["resultados"][clave], d["resultados"].get(clave)
    if R is None:
        return ""
    kp = Ck["k_propio"]
    elegido = (f'El clustering elige <b>{kp} grupos</b>: es el corte cuya silueta más supera la de datos al azar.'
               if kp else 'Ningún corte supera la silueta de datos al azar: el clustering no encuentra grupos.')
    graf = (f'<div class="dos"><div class="panel"><h4>Silueta según la cantidad de grupos</h4>{_silueta_svg(Ck)}'
            '<div class="leyenda"><span><i class="lin"></i>silueta</span><span><i class="lin kaiser"></i>percentil 95 con datos al azar</span></div>'
            f'<p class="nota">{elegido} Punto naranja: corte elegido; azul: {Ck["k_pca"]} grupos, como el PCA. La silueta mide '
            'cuánto más se parece cada métrica a su grupo que al grupo más cercano (de −1 a 1).</p></div>'
            f'<div class="panel"><h4>Dendrograma</h4>{_dendro_svg(d, Ck, 560)}{_leyenda_cp(Ck)}'
            '<div class="leyenda"><span><i class="lin" style="border-top-color:var(--serie2);border-top-style:dashed"></i>corte elegido</span>'
            f'<span><i class="lin" style="border-top-style:dashed"></i>corte en {Ck["k_pca"]} grupos</span></div>'
            '<p class="nota">El color de cada métrica es el componente del PCA donde más carga (gris: ninguno). '
            'Cuanto más a la izquierda se unen dos ramas, más correlacionadas están.</p></div></div>')
    tablas = "".join(_tablas_solucion(d, Ck, R, n) for n in ("propio", "pca") if n in Ck["soluciones"])
    return graf + tablas


def pieza_clustering(d: dict, tipo: str, conjunto: str, serie: str = "estable", enfoque: str = "ajustado") -> str:
    C, clave = d.get("clustering"), f"{conjunto}|{serie}|{enfoque}"
    if not C or clave not in C["resultados"]:
        return f'<p class="error-marca">No hay clustering para {html.escape(clave)}: corré analisis/generar_clustering.py.</p>'
    Ck, R = C["resultados"][clave], d["resultados"][clave]
    cfg = f'{d["series"][serie]} · {d["enfoques"][enfoque]} · {Ck["p"]} variables'
    if tipo == "dendrograma":
        return (f'<div class="panel inserto"><h4>Dendrograma de las métricas · {cfg}</h4>{_dendro_svg(d, Ck)}{_leyenda_cp(Ck)}'
                '<div class="leyenda"><span><i class="lin" style="border-top-color:var(--serie2);border-top-style:dashed"></i>corte elegido por el clustering</span>'
                f'<span><i class="lin" style="border-top-style:dashed"></i>corte en {Ck["k_pca"]} grupos, como el PCA</span></div>'
                '<p class="nota">Color: componente del PCA donde más carga cada métrica (gris: ninguno). Cuanto más a la izquierda '
                'se unen dos ramas, más correlacionadas están las métricas.</p></div>')
    if tipo == "silueta":
        return f'<div class="panel inserto"><h4>Silueta según la cantidad de grupos · {cfg}</h4>{_silueta_svg(Ck, 560, 250)}</div>'
    if tipo in ("grupos", "grupos_pca"):
        return _tablas_solucion(d, Ck, R, "propio" if tipo == "grupos" else "pca")
    if tipo == "clustering":
        return _bloque_clustering(d, C, clave)
    return f'<p class="error-marca">Marca de clustering desconocida: {html.escape(tipo)}</p>'


def _f(v, d=2):
    return "—" if v is None else f"{v:.{d}f}".replace(".", ",").replace("-", "−")


def _color(v):
    if v is None:
        return "transparent"
    t = round(min(1.0, abs(v)) * 100)
    return f"color-mix(in srgb, var({'--div-pos' if v >= 0 else '--div-neg'}) {t}%, var(--div-mid))"


def _nombre(d, v):
    return d["nombres"][v].replace(" [producto]", "")


def _scree_svg(R, W=560, H=260):
    p, m = R["p"], dict(l=44, r=14, t=14, b=36)
    ymax = max(R["autovalores"] + R["horn95"] + [1.2])
    ymax = float(int(ymax) + 1)
    sx = lambda i: m["l"] + i / (p - 1) * (W - m["l"] - m["r"])
    sy = lambda v: m["t"] + (1 - v / ymax) * (H - m["t"] - m["b"])
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Gráfico de sedimentación">']
    paso = 1 if ymax > 4 else 0.5
    v = 0.0
    while v <= ymax + 1e-9:
        s.append(f'<line x1="{m["l"]}" x2="{W - m["r"]}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" class="grid"/>'
                 f'<text x="{m["l"] - 6}" y="{sy(v):.1f}" class="ticky">{_f(v, 1)}</text>')
        v += paso
    for i in range(p):
        s.append(f'<text x="{sx(i):.1f}" y="{H - m["b"] + 6}" class="tick">{i + 1}</text>')
    s.append(f'<text x="{(m["l"] + W - m["r"]) / 2}" y="{H - 6}" class="eje">componente</text>')
    s.append(f'<line x1="{m["l"]}" x2="{W - m["r"]}" y1="{sy(1):.1f}" y2="{sy(1):.1f}" class="kaiser"/>')
    s.append('<path d="' + "".join(f'{"L" if i else "M"}{sx(i):.1f},{sy(v):.1f}' for i, v in enumerate(R["horn95"])) + '" class="horn"/>')
    s.append('<path d="' + "".join(f'{"L" if i else "M"}{sx(i):.1f},{sy(v):.1f}' for i, v in enumerate(R["autovalores"])) + '" class="scree"/>')
    for i, v in enumerate(R["autovalores"]):
        s.append(f'<circle cx="{sx(i):.1f}" cy="{sy(v):.1f}" r="{5 if i < R["k"] else 3.5}" class="scree-pt" '
                 f'fill-opacity="{1 if i < R["k"] else .45}"><title>CP{i + 1}: {_f(v)} · Horn {_f(R["horn95"][i])}</title></circle>')
    s.append("</svg>")
    return "".join(s)


def pieza(d: dict, tipo: str, conjunto: str, serie: str = "estable", enfoque: str = "ajustado") -> str:
    clave = f"{conjunto}|{serie}|{enfoque}"
    R = d["resultados"].get(clave)
    if tipo not in ("comparacion", "criterios", "screes") and R is None:
        return f'<p class="error-marca">No hay resultados de PCA para {html.escape(clave)}.</p>'
    vs = R["variables"] if R and "variables" in R else d["conjuntos"].get(conjunto, [])
    cfg = f'{d["series"][serie]} · {d["enfoques"][enfoque]} · {len(vs)} variables'
    if tipo == "cargas":
        k, L = R["k"], R["varimax"]
        var = [sum(f[j] ** 2 for f in L) / R["p"] for j in range(k)]
        cab = "".join(f'<th style="text-align:center">CP{j + 1}<br><span class="cuenta">{round(var[j] * 100)} %</span></th>' for j in range(k))
        filas = []
        for v, f in zip(vs, L):
            celdas = "".join(f'<td class="celda" style="background:{_color(x)};color:{"#fff" if abs(x) > .6 else "var(--texto)"};'
                             f'font-weight:{650 if abs(x) >= .4 else 400}">{_f(x)}</td>' for x in f)
            filas.append(f'<tr><td>{html.escape(_nombre(d, v))}</td>{celdas}<td class="n" style="text-align:center">{_f(sum(x * x for x in f))}</td></tr>')
        return (f'<div class="panel inserto tabla"><h4>Cargas varimax · {cfg}</h4><table><thead><tr><th>Variable</th>{cab}'
                f'<th style="text-align:center">Comunalidad</th></tr></thead><tbody>{"".join(filas)}</tbody></table>'
                f'<p class="nota">Carga: correlación entre la variable y el componente (en negrita si |carga| ≥ 0,4; naranja positiva, '
                f'azul negativa). Debajo de cada componente, el porcentaje de la varianza total que explica después de la rotación. '
                f'Comunalidad: parte de la variable que explican los {k} componentes juntos.</p></div>')
    leyenda = (f'<div class="leyenda"><span><i class="lin"></i>autovalor</span><span><i class="lin horn"></i>Horn: percentil '
               f'{d["parametros"]["percentil_horn"]} con datos permutados</span><span><i class="lin kaiser"></i>Kaiser (1)</span></div>')
    if tipo == "screes":
        paneles = []
        for c in conjunto.split("+"):
            Rc = d["resultados"].get(f"{c}|{serie}|{enfoque}")
            if Rc is None:
                continue
            titulo = f'{len(Rc["variables"])} variables' + (" a nivel producto" if c == "producto" else "")
            paneles.append(f'<figure style="margin:0">{_scree_svg(Rc, 400, 250)}<figcaption class="nota" style="text-align:center;margin-top:2px">'
                           f'<b>{titulo}</b> · {Rc["k"]} componentes retenidos</figcaption></figure>')
        return (f'<div class="panel inserto"><h4>Gráfico de sedimentación · {d["series"][serie]} · {d["enfoques"][enfoque]}</h4>'
                f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px">{"".join(paneles)}</div>'
                f'{leyenda}<p class="nota">Puntos grandes: componentes retenidos (los que superan la línea de Horn).</p></div>')
    if tipo == "scree":
        return (f'<div class="panel inserto"><h4>Gráfico de sedimentación · {cfg}</h4>{_scree_svg(R)}{leyenda}'
                f'<p class="nota">Puntos grandes: componentes retenidos (los que superan la línea de Horn).</p></div>')
    if tipo == "criterios":
        filas = []
        for s_ in d["series"]:
            for e_ in d["enfoques"]:
                r_ = d["resultados"].get(f"{conjunto}|{s_}|{e_}")
                if not r_:
                    continue
                c = r_["criterios"]
                filas.append(f'<tr><td>{d["series"][s_]}</td><td>{d["enfoques"][e_]}</td><td class="n">{r_["n"]}</td>'
                             + "".join(f'<td class="n">{c[x]}</td>' for x in ("kaiser", "codo", "varianza_70", "varianza_80", "horn"))
                             + f'<td class="n"><b>{r_["k"]}</b></td><td class="n">{round(r_["acumulada"][r_["k"] - 1] * 100)} %</td></tr>')
        return (f'<div class="panel inserto tabla"><h4>Cantidad de componentes según cada criterio · {len(vs)} variables</h4><table><thead><tr>'
                '<th>Serie</th><th>Enfoque</th><th>Releases</th><th>Kaiser</th><th>Codo</th><th>Varianza ≥ 70 %</th>'
                '<th>Varianza ≥ 80 %</th><th>Horn</th><th>Retenidos</th><th>Varianza explicada</th></tr></thead>'
                f'<tbody>{"".join(filas)}</tbody></table></div>')
    if tipo == "solidez":
        b = R["boot"]
        filas = "".join(f'<tr><td>CP{j + 1}</td><td class="n">{_f(b["congruencia_mediana"][j])}</td><td class="n">{_f(b["congruencia_p05"][j])}</td>'
                        f'<td class="n">{_f(R["autovalores"][j])}</td><td class="n">[{_f(b["autoval_p025"][j])}; {_f(b["autoval_p975"][j])}]</td></tr>'
                        for j in range(R["k"]))
        return (f'<div class="panel inserto tabla"><h4>Solidez en el bootstrap · {cfg}</h4><table><thead><tr><th>Componente</th>'
                '<th>Congruencia mediana</th><th>Congruencia p5</th><th>Autovalor</th><th>IC 95 % del autovalor</th></tr></thead>'
                f'<tbody>{filas}</tbody></table><p class="nota">{d["parametros"]["bootstrap"]} remuestreos de bloques de '
                f'{b["largo_bloque"]} releases consecutivos. Congruencia p5: el valor que supera el 95 % de los remuestreos.</p></div>')
    if tipo == "comparacion":
        cs = [c for c in d["comparacion"] if c["conjunto"] == conjunto]
        if not cs:
            return '<p class="error-marca">No hay comparación para ese conjunto.</p>'
        k = cs[0]["k_comparado"]
        filas = []
        for s_ in d["series"]:
            for e_ in d["enfoques"]:
                f = sorted((c for c in cs if c["serie"] == s_ and c["enfoque"] == e_), key=lambda c: c["componente"])
                if not f:
                    continue
                celdas = "".join(
                    f'<td class="celda" style="background:{"var(--div-neg)" if c["congruencia"] >= .95 else "color-mix(in srgb, var(--div-neg) 45%, var(--superficie))" if c["congruencia"] >= .85 else "var(--div-mid)"};'
                    f'color:{"#fff" if c["congruencia"] >= .95 else "var(--texto)"}">{_f(c["congruencia"])}</td>' for c in f)
                filas.append(f'<tr><td>{d["series"][s_]}</td><td>{d["enfoques"][e_]}</td><td class="n">{f[0]["k_propio"]}</td>{celdas}</tr>')
        cab = "".join(f'<th style="text-align:center">CP{j + 1}</th>' for j in range(k))
        return (f'<div class="panel inserto tabla"><h4>Congruencia con la solución de referencia (estables, ajustado) · {len(vs)} variables</h4>'
                f'<table><thead><tr><th>Serie</th><th>Enfoque</th><th>Componentes propios</th>{cab}</tr></thead><tbody>{"".join(filas)}</tbody></table>'
                '<div class="leyenda"><span><i class="cuadro" style="background:var(--div-neg)"></i>≥ 0,95: el mismo componente</span>'
                '<span><i class="cuadro" style="background:color-mix(in srgb, var(--div-neg) 45%, var(--superficie))"></i>0,85–0,95: parecido</span>'
                '<span><i class="cuadro" style="background:var(--div-mid)"></i>&lt; 0,85: distinto</span></div>'
                f'<p class="nota">Cada solución se recalcula con {k} componentes y se empareja con la de referencia.</p></div>')
    if tipo == "puntajes":
        pts = R["puntajes"]
        import datetime as _dt
        t = [_dt.date(int(x[2][:4]), int(x[2][4:6]), int(x[2][6:8])).toordinal() for x in pts]
        t0, t1 = min(t), max(t)
        W, fila, m = 1000, 80, dict(l=54, r=12, t=8, b=28)
        H = m["t"] + R["k"] * fila + m["b"]
        sx = lambda x: m["l"] + (x - t0) / ((t1 - t0) or 1) * (W - m["l"] - m["r"])
        s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Puntajes de los componentes">']
        for a in range(_dt.date.fromordinal(t0).year + 1, _dt.date.fromordinal(t1).year + 1):
            x = sx(_dt.date(a, 1, 1).toordinal())
            s.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{m["t"]}" y2="{H - m["b"]}" class="grid"/><text x="{x:.1f}" y="{H - m["b"] + 6}" class="tick">{a}</text>')
        for j in range(R["k"]):
            vals = [x[3 + j] for x in pts]
            lim = max([3.0] + [abs(v) for v in vals])
            y0 = m["t"] + j * fila
            sy = lambda v: y0 + 8 + (1 - (v + lim) / (2 * lim)) * (fila - 16)
            s.append(f'<text x="{m["l"] - 8}" y="{y0 + fila / 2}" class="ticky" style="font-weight:600;fill:var(--texto)">CP{j + 1}</text>'
                     f'<line x1="{m["l"]}" x2="{W - m["r"]}" y1="{sy(0):.1f}" y2="{sy(0):.1f}" class="cero"/>'
                     '<path d="' + "".join(f'{"L" if i else "M"}{sx(tt):.1f},{sy(v):.1f}' for i, (tt, v) in enumerate(zip(t, vals))) + '" class="linea-cp"/>')
        s.append("</svg>")
        return (f'<div class="panel inserto"><h4>Puntajes por release · {cfg}</h4>{"".join(s)}'
                '<p class="nota">Valor de cada componente (varimax, estandarizado: media 0 y desvío 1) en cada release.</p></div>')
    return f'<p class="error-marca">Marca de PCA desconocida: {html.escape(tipo)}</p>'


if __name__ == "__main__":
    main()
