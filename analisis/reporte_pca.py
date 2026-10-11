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

<script type="application/json" id="datosPca">{json.dumps(d, ensure_ascii=False).replace("</", "<\\/")}</script>
<script>{SCRIPT}</script>
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


if __name__ == "__main__":
    main()


# ── Piezas estáticas para el informe (generar_informe.py: marcas [[pca ...]]) ─────────────────

def cargar(dim: str) -> dict | None:
    entrada = ENTRADA / f"pca_{dim.lower()}.json"
    return json.loads(entrada.read_text(encoding="utf-8")) if entrada.exists() else None


def _f(v, d=2):
    return "—" if v is None else f"{v:.{d}f}".replace(".", ",").replace("-", "−")


def _color(v):
    if v is None:
        return "transparent"
    t = round(min(1.0, abs(v)) * 100)
    return f"color-mix(in srgb, var({'--div-pos' if v >= 0 else '--div-neg'}) {t}%, var(--div-mid))"


def _nombre(d, v):
    return d["nombres"][v].replace(" [producto]", "")


def pieza(d: dict, tipo: str, conjunto: str, serie: str = "estable", enfoque: str = "ajustado") -> str:
    clave = f"{conjunto}|{serie}|{enfoque}"
    R = d["resultados"].get(clave)
    if tipo != "comparacion" and tipo != "criterios" and R is None:
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
    if tipo == "scree":
        p, W, H, m = R["p"], 560, 260, dict(l=44, r=14, t=14, b=36)
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
        return (f'<div class="panel inserto"><h4>Gráfico de sedimentación · {cfg}</h4>{"".join(s)}'
                f'<div class="leyenda"><span><i class="lin"></i>autovalor</span><span><i class="lin horn"></i>Horn: percentil '
                f'{d["parametros"]["percentil_horn"]} con datos permutados</span><span><i class="lin kaiser"></i>Kaiser (1)</span></div>'
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
