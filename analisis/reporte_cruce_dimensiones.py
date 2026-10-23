#!/usr/bin/env python3
"""
analisis/reporte_cruce_dimensiones.py

Reporte interactivo (HTML autocontenido) del análisis entre dos dimensiones que calcula
cruce_dimensiones.py. Reutiliza el estilo y los nombres cortos de reporte_cruce.py.

Uso:
    python3 analisis/reporte_cruce_dimensiones.py Persona Producto

Lee analisis/salidas/cruces/<dima>_<dimb>/ (pares_variables.csv, pares_componentes.csv,
triangulacion.csv, resumen.json y valores.json) y escribe
analisis/salidas/reportes/reporte_cruce_<dima>_<dimb>.html.

Secciones:
  1. Resumen: variables por lado, pares por tipo, componentes cruzados.
  2. Mapa de calor cruzado (filas: una dimensión; columnas: la otra) con los pares robustos marcados por tipo.
  3. Red bipartita de las relaciones robustas: qué variables hacen de puente.
  4. Tabla de pares robustos y explorador de un par (series en el tiempo, dispersión corregida,
     correlación por período y canary, sensibilidad a cada control).
  5. Componentes: cargas, matriz de cruces y explorador de un par de componentes.
  6. Conjunto reducido: componentes firmes y variables independientes de cada lado, con su matriz,
     tabla y explorador.
  7. Correlación canónica, triangulación y PCA conjunto.
"""
import html
import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reporte_cruce as rc  # noqa: E402  (estilo, nombres cortos)

ROOT = Path(__file__).resolve().parent.parent
CRUCES = ROOT / "analisis" / "salidas" / "cruces"
SALIDA = ROOT / "analisis" / "salidas" / "reportes"
PERIODOS = ["2016_2019", "2020_2022", "2023_2024", "2025_2026"]
TIPOS = [("patrón", "Patrón"), ("escala", "Escala"), ("mecánico", "Mecánico"), ("no resiste tamaño", "No resiste tamaño")]


def esc(v):
    return html.escape(str(v), quote=True)


def n(v, d=3):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else round(f, d)


def si(v):
    return str(v).strip().lower() in ("true", "sí", "si", "1")


def par_json(r):
    return dict(x=r.x_id, y=r.y_id, tipo=r.get("tipo", "") if isinstance(r.get("tipo", ""), str) else "",
                cat=r.categoria, rho=n(r.rho_corregida), cruda=n(r.rho_cruda), ic=[n(r.ic_inf, 2), n(r.ic_sup, 2)],
                tam=n(r.rho_corregida_tamano), can=n(r.rho_canary), per=[n(r[f"rho_{p}"], 2) for p in PERIODOS],
                local=n(r.get("rho_corregida_local")), cortas=n(r.get("rho_corregida_sin_cortas")),
                nn=int(r.n) if n(r.n) is not None else None, nef=n(r.n_efectiva, 0), pfdr=n(r.p_fdr, 4),
                alc=r.alcance_temporal if isinstance(r.get("alcance_temporal"), str) else "", rob=si(r.robusta))


def construir(dim_a, dim_b):
    carpeta = CRUCES / f"{dim_a.lower()}_{dim_b.lower()}"
    if not (carpeta / "resumen.json").exists():
        sys.exit(f"Falta {carpeta}/resumen.json: corré cruce_dimensiones.py {dim_a} {dim_b}.")
    resumen = json.loads((carpeta / "resumen.json").read_text(encoding="utf-8"))
    valores = json.loads((carpeta / "valores.json").read_text(encoding="utf-8")) if (carpeta / "valores.json").exists() else {}
    pv = pd.read_csv(carpeta / "pares_variables.csv")
    pcp = pd.read_csv(carpeta / "pares_componentes.csv")
    pred = pd.read_csv(carpeta / "pares_reducido.csv") if (carpeta / "pares_reducido.csv").exists() else pd.DataFrame()
    tri = pd.read_csv(carpeta / "triangulacion.csv") if (carpeta / "triangulacion.csv").exists() else pd.DataFrame()
    nombres = rc.nombres_variables()
    va, vb = resumen["variables"][dim_a], resumen["variables"][dim_b]
    nom = {v: nombres.get(v, v) for v in va + vb}

    comps = {}
    for d in (dim_a, dim_b):
        comps[d] = [dict(id=f"{d.lower()}_cp{c['n']}", n=c["n"], var=n(c["varianza"]), boot=n(c["bootstrap"]),
                         can=n(c["canary"]) if c["canary"] != "" else None,
                         cargas=[[v, x] for v, x in c["cargas"]]) for c in resumen["componentes"][d]]
    for d in (dim_a, dim_b):
        for c in comps[d]:
            fuertes = [nom.get(v, nombres.get(v, v)) for v, x in c["cargas"][:3]]
            nom[c["id"]] = f"CP{c['n']} {d}" + (f" · {', '.join(fuertes)}" if fuertes else "")
            for v, _ in c["cargas"]:
                nom.setdefault(v, nombres.get(v, v))
    pca = resumen.get("pca_conjunto") or {}
    for c in pca.get("componentes", []):
        for v, _ in c["cargas"]:
            nom.setdefault(v, nombres.get(v, v))

    datos = dict(
        dims=[dim_a, dim_b], varsA=sorted(va, key=lambda v: nom[v].lower()), varsB=sorted(vb, key=lambda v: nom[v].lower()),
        nombres=nom, dimDe={**{v: dim_a for v in va}, **{v: dim_b for v in vb}},
        pares={r.par_id: par_json(r) for _, r in pv.iterrows()},
        paresCp={r.par_id: dict(par_json(r), comparten=r.comparten if isinstance(r.get("comparten"), str) else "") for _, r in pcp.iterrows()},
        paresRed={r.par_id: par_json(r) for _, r in pred.iterrows()} if len(pred) else {},
        red={d: (resumen.get("reducido") or {}).get("elementos", {}).get(d, []) for d in (dim_a, dim_b)},
        modoRed=(resumen.get("reducido") or {}).get("modo", "puntajes"),
        residuosRed=valores.get("residuos_red", {}),
        comps=comps, releases=valores.get("releases", {}), serie=valores.get("serie", {}),
        residuos=valores.get("residuos", {}), compSerie=valores.get("componentes", {}), residuosCp=valores.get("residuos_cp", {}),
        cca=resumen.get("cca"), pca=pca, compartidas=resumen.get("compartidas", {}),
        triang=[dict(id=r.par_id, x=r.x_nombre, y=r.y_nombre, rho=n(r.rho_corregida), cx=r.componentes_x if isinstance(r.componentes_x, str) else "",
                     cy=r.componentes_y if isinstance(r.componentes_y, str) else "", ok=si(r.triangulado),
                     apoyo=r.par_componentes_robusto if isinstance(r.par_componentes_robusto, str) else "")
                for _, r in tri.iterrows()] if len(tri) else [],
    )
    for d in (dim_a, dim_b):
        for e in datos["red"][d]:
            if e["tipo"] == "variable":
                nom.setdefault(e["id"], nombres.get(e["id"], e["id"]))
            elif e["tipo"] == "marcadora":
                nom[e["id"]] = nombres.get(e["id"], e["id"]) + f" (marca {e['componente'].split('_')[-1].upper()})"
    cuenta = resumen.get("conteo_variables", {})
    return datos, cuenta, len(pv)


ESTILO_EXTRA = """
.dosc { display:grid; grid-template-columns: repeat(auto-fit, minmax(300px,1fr)); gap:16px; margin-top:12px; }
.cp-card { background:var(--superficie); border:1px solid var(--borde); border-radius:10px; padding:14px 16px; }
.cp-card h3 { display:flex; justify-content:space-between; gap:8px; }
.cp-card .met { color:var(--texto2); font-size:12.5px; margin:-2px 0 8px; }
.carga { display:grid; grid-template-columns: minmax(0,1fr) 120px 46px; gap:8px; align-items:center; font-size:12.5px; margin:3px 0; }
.carga .nm { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.carga .bx { position:relative; height:9px; background:var(--div-mid); border-radius:5px; }
.carga .bx i { position:absolute; top:0; bottom:0; border-radius:5px; }
.carga .vl { text-align:right; font-variant-numeric:tabular-nums; }
.tag-dim { display:inline-block; font-size:11px; padding:0 6px; border-radius:99px; margin-right:4px; color:#fff; }
.tag-a { background:var(--serie); } .tag-b { background:var(--serie2); }
.estado { font-size:12px; padding:1px 8px; border-radius:99px; border:1px solid var(--borde); white-space:nowrap; }
.estado.patron { background:var(--hover); border-color:var(--serie); font-weight:600; }
.estado.escala, .estado.no-resiste { opacity:.85; }
svg .mk-patron { fill:var(--texto); }
svg .mk-escala { fill:none; stroke:var(--texto); stroke-width:1.6; }
svg .mk-mecanico { fill:none; stroke:var(--texto); stroke-width:1.3; }
svg .mk-noresiste { fill:var(--texto); fill-opacity:.35; }
svg .nodo-a { fill:var(--serie); } svg .nodo-b { fill:var(--serie2); }
svg .arista.no-patron { stroke-dasharray:4 4; }
svg .arista.atenuada, svg .mk.atenuada { opacity:.1; }
svg .lbl-a { fill:var(--texto); font-size:11px; text-anchor:end; dominant-baseline:middle; }
svg .lbl-b { fill:var(--texto); font-size:11px; text-anchor:start; dominant-baseline:middle; }
.leyenda i.mk-p { background:var(--texto); opacity:1; } .leyenda i.mk-e { background:none; box-shadow:inset 0 0 0 1.6px var(--texto); opacity:1; }
.leyenda i.mk-m { background:none; border-radius:1px; box-shadow:inset 0 0 0 1.3px var(--texto); opacity:1; }
.leyenda i.mk-n { background:var(--texto); opacity:.35; }
.leyenda i.dim-a { background:var(--serie); opacity:1; } .leyenda i.dim-b { background:var(--serie2); opacity:1; }
"""

SCRIPT = r"""
const D = JSON.parse(document.getElementById('datos').textContent);
const [A, B] = D.dims;
const nom = v => D.nombres[v] || v;
const fmt = (v, d = 2) => (v === null || v === undefined || Number.isNaN(v)) ? '—' : (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(d).replace('.', ',');
const col = v => { if (v === null || v === undefined) return 'transparent';
  const t = Math.round(Math.min(1, Math.abs(v)) * 100);
  return `color-mix(in srgb, var(${v >= 0 ? '--div-pos' : '--div-neg'}) ${t}%, var(--div-mid))`; };
const SVG = (w, h, inner, label) => `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${label}">${inner}</svg>`;
const escH = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const claseTipo = t => ({'patrón':'patron','escala':'escala','mecánico':'mecanico','no resiste tamaño':'noresiste'}[t] || '');
let filtroTipo = null;

/* ── mapa de calor cruzado ── */
function mapa() {
  const ra = D.varsA, cb = D.varsB, c = 18, lw = 230, top = 170;
  const w = lw + cb.length * c + 150, h = top + ra.length * c + 10;
  let s = '';
  ra.forEach((v, i) => s += `<text x="${lw - 6}" y="${top + c * (i + .5)}" class="lbl-fila">${escH(nom(v))}</text>`);
  cb.forEach((v, j) => s += `<text transform="translate(${lw + c * (j + .5) + 3} ${top - 6}) rotate(-55)" class="lbl-col">${escH(nom(v))}</text>`);
  ra.forEach((x, i) => cb.forEach((y, j) => {
    const id = `${x}__${y}`, p = D.pares[id], X = lw + c * j, Y = top + c * i;
    if (!p) { s += `<rect x="${X}" y="${Y}" width="${c}" height="${c}" class="celda vacia"/>`; return; }
    const fill = p.cat === 'control' ? 'var(--borde)' : col(p.rho);
    const at = filtroTipo && p.tipo !== filtroTipo ? ' atenuada' : '';
    s += `<rect x="${X}" y="${Y}" width="${c}" height="${c}" class="celda par${at}" style="fill:${fill}" data-par="${id}"><title>${escH(nom(x))} ↔ ${escH(nom(y))}: ${fmt(p.rho)}${p.tipo ? ' · ' + p.tipo : ''}</title></rect>`;
    const k = claseTipo(p.tipo), cx = X + c / 2, cy = Y + c / 2;
    if (k === 'patron') s += `<circle cx="${cx}" cy="${cy}" r="3.6" class="mk mk-patron${at}" pointer-events="none"/>`;
    else if (k === 'escala') s += `<circle cx="${cx}" cy="${cy}" r="3.6" class="mk mk-escala${at}" pointer-events="none"/>`;
    else if (k === 'mecanico') s += `<rect x="${cx - 3.5}" y="${cy - 3.5}" width="7" height="7" class="mk mk-mecanico${at}" pointer-events="none"/>`;
    else if (k === 'noresiste') s += `<circle cx="${cx}" cy="${cy}" r="3.6" class="mk mk-noresiste${at}" pointer-events="none"/>`;
  }));
  document.getElementById('mapa').innerHTML = SVG(w, h, s, `Mapa de calor ${A}–${B}`);
}

/* ── red bipartita ── */
function red() {
  const rob = Object.entries(D.pares).filter(([, p]) => p.rob && p.cat !== 'control');
  const na = [...new Set(rob.map(([, p]) => p.x))].sort((a, b) => nom(a).localeCompare(nom(b)));
  const nb = [...new Set(rob.map(([, p]) => p.y))].sort((a, b) => nom(a).localeCompare(nom(b)));
  if (!rob.length) { document.getElementById('red').innerHTML = '<p class="vacio">No hay relaciones robustas.</p>'; return; }
  const rows = Math.max(na.length, nb.length), h = 30 + rows * 22, w = 900, xa = 300, xb = 600;
  const ya = v => 20 + (na.indexOf(v) + .5) * (h - 30) / na.length, yb = v => 20 + (nb.indexOf(v) + .5) * (h - 30) / nb.length;
  const grado = {}; rob.forEach(([, p]) => { if (p.tipo === 'patrón') { grado[p.x] = (grado[p.x] || 0) + 1; grado[p.y] = (grado[p.y] || 0) + 1; } });
  let s = '';
  rob.forEach(([id, p]) => {
    const at = filtroTipo && p.tipo !== filtroTipo ? ' atenuada' : '';
    s += `<line x1="${xa}" y1="${ya(p.x)}" x2="${xb}" y2="${yb(p.y)}" class="arista${p.tipo === 'patrón' ? '' : ' no-patron'}${at}" style="stroke:var(${p.rho >= 0 ? '--div-pos' : '--div-neg'});stroke-width:${1 + Math.abs(p.rho) * 6}" data-par="${id}"><title>${escH(nom(p.x))} ↔ ${escH(nom(p.y))}: ${fmt(p.rho)} · ${p.tipo}</title></line>`;
  });
  na.forEach(v => s += `<circle cx="${xa}" cy="${ya(v)}" r="${4 + (grado[v] || 0) * 1.5}" class="nodo-a"/><text x="${xa - 10}" y="${ya(v)}" class="lbl-a">${escH(nom(v))}${grado[v] ? ' · ' + grado[v] : ''}</text>`);
  nb.forEach(v => s += `<circle cx="${xb}" cy="${yb(v)}" r="${4 + (grado[v] || 0) * 1.5}" class="nodo-b"/><text x="${xb + 10}" y="${yb(v)}" class="lbl-b">${escH(nom(v))}${grado[v] ? ' · ' + grado[v] : ''}</text>`);
  s += `<text x="${xa}" y="12" class="titulo-panel" text-anchor="middle">${A}</text><text x="${xb}" y="12" class="titulo-panel" text-anchor="middle">${B}</text>`;
  document.getElementById('red').innerHTML = SVG(w, h, s, `Red de relaciones robustas ${A}–${B}`);
}

/* ── tabla de pares robustos ── */
function tabla() {
  const filas = Object.entries(D.pares).filter(([, p]) => p.rob && p.cat !== 'control' && (!filtroTipo || p.tipo === filtroTipo))
    .sort((a, b) => Math.abs(b[1].rho) - Math.abs(a[1].rho));
  document.getElementById('conteo').textContent = `${filas.length} pares`;
  document.getElementById('cuerpoTabla').innerHTML = filas.map(([id, p]) =>
    `<tr data-par="${id}"><td>${escH(nom(p.x))}</td><td>${escH(nom(p.y))}</td><td><span class="estado ${claseTipo(p.tipo)}">${p.tipo}</span></td>` +
    `<td class="n">${fmt(p.rho)}</td><td class="n">${fmt(p.cruda)}</td><td class="n">${fmt(p.tam)}</td><td class="n">${fmt(p.can)}</td><td>${escH(p.alc)}</td></tr>`).join('') ||
    '<tr><td colspan="8" class="vacio">Ninguno.</td></tr>';
}

/* ── gráficos del explorador ── */
function fechaDe(pn) { const r = D.releases[pn]; return r && r[1] ? new Date(r[1]) : null; }
function rangos(serie) {
  const ks = Object.keys(serie).filter(k => serie[k] !== null && serie[k] !== '');
  const ord = ks.slice().sort((a, b) => serie[a] - serie[b]);
  const out = {}; ord.forEach((k, i) => out[k] = ord.length > 1 ? 100 * i / (ord.length - 1) : 50); return out;
}
function graficoSeries(sx, sy, nx, ny) {
  const rx = rangos(sx), ry = rangos(sy);
  const pts = s => Object.keys(s).map(k => [fechaDe(k), s[k]]).filter(p => p[0]).sort((a, b) => a[0] - b[0]);
  const suav = p => p.map((q, i) => { const v = p.slice(Math.max(0, i - 4), i + 5).map(z => z[1]); return [q[0], v.reduce((a, b) => a + b, 0) / v.length]; });
  const px = suav(pts(rx)), py = suav(pts(ry)), todas = px.concat(py);
  if (!todas.length) return '<p class="vacio">Sin valores por release.</p>';
  const t0 = Math.min(...todas.map(p => +p[0])), t1 = Math.max(...todas.map(p => +p[0]));
  const W = 520, H = 220, ml = 34, mr = 8, mt = 22, mb = 24;
  const X = t => ml + (t - t0) / ((t1 - t0) || 1) * (W - ml - mr), Y = v => mt + (1 - v / 100) * (H - mt - mb);
  let s = `<text x="${ml}" y="13" class="titulo-panel">Las dos series en el tiempo (percentil, media móvil de 9 releases)</text>`;
  [0, 50, 100].forEach(v => s += `<line x1="${ml}" x2="${W - mr}" y1="${Y(v)}" y2="${Y(v)}" class="grid"/><text x="${ml - 5}" y="${Y(v)}" class="ticky">${v}</text>`);
  for (let a = new Date(t0).getFullYear() + 1; a <= new Date(t1).getFullYear(); a++) { const x = X(+new Date(`${a}-01-01`)); s += `<text x="${x}" y="${H - mb + 6}" class="tick">${a}</text>`; }
  const path = (p, c) => `<path d="${p.map((q, i) => (i ? 'L' : 'M') + X(+q[0]).toFixed(1) + ',' + Y(q[1]).toFixed(1)).join('')}" class="${c}"/>`;
  s += path(px, 'linea-x') + path(py, 'linea-y');
  return SVG(W, H, s, 'Series en el tiempo') + `<div class="leyenda"><span><i></i>${escH(nx)}</span><span><i class="y"></i>${escH(ny)}</span></div>`;
}
function graficoDispersion(res, nx, ny) {
  if (!res || !res.p || !res.p.length) return '<p class="vacio">Sin residuos guardados para este par (solo se guardan los pares robustos).</p>';
  const xs = res.xr, ys = res.yr, W = 520, H = 220, ml = 40, mr = 8, mt = 22, mb = 30;
  const mx = Math.max(...xs.map(Math.abs)) || 1, my = Math.max(...ys.map(Math.abs)) || 1;
  const X = v => ml + (v / mx + 1) / 2 * (W - ml - mr), Y = v => mt + (1 - (v / my + 1) / 2) * (H - mt - mb);
  let s = `<text x="${ml}" y="13" class="titulo-panel">Relación corregida (rangos sin tiempo ni duración)</text>`;
  s += `<line x1="${X(0)}" x2="${X(0)}" y1="${mt}" y2="${H - mb}" class="cero"/><line x1="${ml}" x2="${W - mr}" y1="${Y(0)}" y2="${Y(0)}" class="cero"/>`;
  xs.forEach((x, i) => { const r = D.releases[res.p[i]]; s += `<circle cx="${X(x).toFixed(1)}" cy="${Y(ys[i]).toFixed(1)}" r="3" class="punto"><title>${r ? escH(r[0]) : ''}</title></circle>`; });
  s += `<text x="${(ml + W - mr) / 2}" y="${H - 6}" class="eje">${escH(nx)} →</text>`;
  return SVG(W, H, s, 'Dispersión corregida') + `<p class="nota">Cada punto es un release; el eje vertical es ${escH(ny)}.</p>`;
}
function graficoPeriodos(p) {
  const et = ['2016–19', '2020–22', '2023–24', '2025–26', 'Canary'], vals = p.per.concat([p.can]);
  const W = 520, H = 200, ml = 34, mr = 8, mt = 22, mb = 26, bw = (W - ml - mr) / 5;
  const Y = v => mt + (1 - (v + 1) / 2) * (H - mt - mb);
  let s = `<text x="${ml}" y="13" class="titulo-panel">ρ corregida por período y en canary</text>`;
  [-1, -.5, 0, .5, 1].forEach(v => s += `<line x1="${ml}" x2="${W - mr}" y1="${Y(v)}" y2="${Y(v)}" class="${v === 0 ? 'cero' : 'grid'}"/><text x="${ml - 5}" y="${Y(v)}" class="ticky">${fmt(v, 1)}</text>`);
  vals.forEach((v, i) => {
    const x = ml + bw * i + bw * .2;
    if (v !== null && v !== undefined) s += `<rect x="${x}" y="${Math.min(Y(v), Y(0))}" width="${bw * .6}" height="${Math.abs(Y(v) - Y(0))}" class="${i === 4 ? 'barra-can' : 'barra-per' + (Math.abs(v) < .1 ? ' debil' : '')}"/><text x="${x + bw * .3}" y="${v >= 0 ? Y(v) - 6 : Y(v) + 12}" class="val-barra">${fmt(v)}</text>`;
    else s += `<text x="${x + bw * .3}" y="${Y(0) - 6}" class="val-barra">—</text>`;
    s += `<text x="${x + bw * .3}" y="${H - mb + 8}" class="tick">${et[i]}</text>`;
  });
  if (p.rho !== null) s += `<line x1="${ml}" x2="${W - mr}" y1="${Y(p.rho)}" y2="${Y(p.rho)}" class="ref"/><text x="${ml + bw * 4 - 4}" y="${Y(p.rho) + (p.rho >= 0 ? -5 : 13)}" class="ref-txt" text-anchor="end">toda la historia ${fmt(p.rho)}</text>`;
  return SVG(W, H, s, 'Correlación por período');
}
function graficoSensibilidad(p) {
  const filas = [['ρ cruda', p.cruda], ['Corregida', p.rho], ['Tendencia local', p.local], ['Sin ventanas cortas', p.cortas], ['Con control por tamaño', p.tam], ['Canary', p.can]];
  const W = 520, H = 30 + filas.length * 26, ml = 160, mr = 46;
  const X = v => ml + (v + 1) / 2 * (W - ml - mr);
  let s = `<text x="8" y="13" class="titulo-panel">Sensibilidad a cada control</text>`;
  [-1, 0, 1].forEach(v => s += `<line x1="${X(v)}" x2="${X(v)}" y1="22" y2="${H - 4}" class="${v === 0 ? 'cero' : 'grid'}"/>`);
  [-.1, .1].forEach(v => s += `<line x1="${X(v)}" x2="${X(v)}" y1="22" y2="${H - 4}" class="umbral"/>`);
  filas.forEach(([l, v], i) => { const y = 34 + i * 26; s += `<text x="${ml - 8}" y="${y}" class="cat">${l}</text>`;
    if (v !== null && v !== undefined) s += `<circle cx="${X(v)}" cy="${y}" r="5" class="pt-sens"/><text x="${W - 4}" y="${y}" class="val" text-anchor="end">${fmt(v)}</text>`; });
  return SVG(W, H, s, 'Sensibilidad');
}
function ficha(p, nx, ny) {
  const it = [['ρ corregida', `${fmt(p.rho)} [${fmt(p.ic[0])}; ${fmt(p.ic[1])}]`], ['Categoría', p.cat], ['Tipo', p.tipo || '—'],
    ['Ventanas (efectivas)', `${p.nn ?? '—'} (${p.nef ?? '—'})`], ['p corregido (BH)', p.pfdr === null || p.pfdr === undefined ? '—' : p.pfdr < 0.0001 ? '< 0,0001' : String(p.pfdr).replace('.', ',')], ['Alcance', p.alc || '—']];
  return `<h3>${escH(nx)} ↔ ${escH(ny)}</h3><div class="ficha">${it.map(([b, v]) => `<div><b>${b}</b><span>${escH(v)}</span></div>`).join('')}</div>`;
}
const FUENTES = {var: ['pares', 'residuos', 'explor'], cp: ['paresCp', 'residuosCp', 'explorCp'], red: ['paresRed', 'residuosRed', 'explorRed']};
function explorar(id, fuente) {
  const esCp = fuente === true || fuente === 'cp', f = FUENTES[fuente === true ? 'cp' : fuente === false || !fuente ? 'var' : fuente];
  const p = D[f[0]][id]; if (!p) return;
  const nx = nom(p.x), ny = nom(p.y);
  const serieDe = v => D.compSerie[v] || D.serie[v] || {};
  const sx = serieDe(p.x), sy = serieDe(p.y);
  const res = D[f[1]][id];
  const destino = document.getElementById(f[2]);
  destino.innerHTML = ficha(p, nx, ny) + `<div class="graficos"><div>${graficoSeries(sx, sy, nx, ny)}</div><div>${graficoDispersion(res, nx, ny)}</div>` +
    `<div>${graficoPeriodos(p)}</div><div>${graficoSensibilidad(p)}</div></div>`;
  if (f[2] === 'explor') { const sel = document.getElementById('selPar'); if ([...sel.options].some(o => o.value === id)) sel.value = id; }
}

/* ── componentes ── */
function cargasHTML(c, dimClase) {
  return c.cargas.slice(0, 8).map(([v, x]) => { const w = Math.min(1, Math.abs(x)) * 50;
    return `<div class="carga"><span class="nm" title="${escH(nom(v))}">${escH(nom(v))}</span><span class="bx"><i style="${x >= 0 ? 'left:50%' : 'right:50%'};width:${w}%;background:var(${x >= 0 ? '--div-pos' : '--div-neg'})"></i></span><span class="vl">${fmt(x)}</span></div>`; }).join('');
}
function componentes() {
  const card = (d, c, k) => `<div class="cp-card"><h3><span><span class="tag-dim ${k}">${d}</span>CP${c.n}</span><span class="cuenta">${c.var !== null ? Math.round(c.var * 100) + ' %' : ''}</span></h3>` +
    `<div class="met">bootstrap ${fmt(c.boot)} · canary ${fmt(c.can)}</div>${cargasHTML(c, k)}</div>`;
  document.getElementById('cpA').innerHTML = D.comps[A].map(c => card(A, c, 'tag-a')).join('') || '<p class="vacio">Sin componentes firmes.</p>';
  document.getElementById('cpB').innerHTML = D.comps[B].map(c => card(B, c, 'tag-b')).join('') || '<p class="vacio">Sin componentes firmes.</p>';
  const ca = D.comps[A], cb = D.comps[B];
  if (!ca.length || !cb.length) { document.getElementById('matrizCp').innerHTML = '<p class="vacio">No hay pares de componentes.</p>'; return; }
  const c = 120, lw = 120, top = 40, w = lw + cb.length * c + 10, h = top + ca.length * 58 + 10;
  let s = '';
  cb.forEach((y, j) => s += `<text x="${lw + c * (j + .5)}" y="${top - 12}" class="eje">${B} CP${y.n}</text>`);
  ca.forEach((x, i) => { s += `<text x="${lw - 8}" y="${top + 58 * (i + .5)}" class="cat">${A} CP${x.n}</text>`;
    cb.forEach((y, j) => { const id = `${x.id}__${y.id}`, p = D.paresCp[id]; if (!p) return;
      const X = lw + c * j, Y = top + 58 * i;
      s += `<rect x="${X + 2}" y="${Y + 2}" width="${c - 4}" height="54" rx="6" class="celda par" style="fill:${col(p.rho)}" data-cp="${id}"><title>${escH(nom(x.id))} ↔ ${escH(nom(y.id))}</title></rect>` +
        `<text x="${X + c / 2}" y="${Y + 22}" class="txt-celda" pointer-events="none">${fmt(p.rho)}</text>` +
        `<text x="${X + c / 2}" y="${Y + 40}" class="txt-celda" pointer-events="none" style="font-size:10.5px">${p.tipo || (p.rob ? 'robusta' : 'no robusta')}${p.comparten ? ' · comparten ' + escH(p.comparten) : ''}</text>`; }); });
  document.getElementById('matrizCp').innerHTML = SVG(w, h, s, 'Pares de componentes');
  const primero = Object.keys(D.paresCp).sort((a, b) => Math.abs(D.paresCp[b].rho) - Math.abs(D.paresCp[a].rho))[0];
  if (primero) explorar(primero, true);
}

/* ── conjunto reducido ── */
function reducido() {
  const ra = D.red[A] || [], rb = D.red[B] || [];
  if (!ra.length || !rb.length) { document.getElementById('mapaRed').innerHTML = '<p class="vacio">No se calculó el conjunto reducido.</p>'; return; }
  const c = 22, lw = 240, top = 170, w = lw + rb.length * c + 150, h = top + ra.length * c + 10;
  const etq = e => e.tipo === 'componente' ? '◆ ' + e.id.replace(/_cp(\d+)$/, ' CP$1').replace(/^./, ch => ch.toUpperCase()) : nom(e.id);
  let s = '';
  ra.forEach((e, i) => s += `<text x="${lw - 6}" y="${top + c * (i + .5)}" class="lbl-fila" style="${e.tipo === 'componente' ? 'font-weight:700' : ''}">${escH(etq(e))}<title>${escH(nom(e.id))}</title></text>`);
  rb.forEach((e, j) => s += `<text transform="translate(${lw + c * (j + .5) + 3} ${top - 6}) rotate(-55)" class="lbl-col" style="${e.tipo === 'componente' ? 'font-weight:700' : ''}">${escH(etq(e))}<title>${escH(nom(e.id))}</title></text>`);
  ra.forEach((x, i) => rb.forEach((y, j) => {
    const id = `${x.id}__${y.id}`, p = D.paresRed[id], X = lw + c * j, Y = top + c * i;
    if (!p) return;
    const fill = p.cat === 'control' ? 'var(--borde)' : col(p.rho), cx = X + c / 2, cy = Y + c / 2, k = claseTipo(p.tipo);
    s += `<rect x="${X}" y="${Y}" width="${c}" height="${c}" class="celda par" style="fill:${fill}" data-red="${id}"><title>${escH(nom(x.id))} ↔ ${escH(nom(y.id))}: ${fmt(p.rho)}${p.tipo ? ' · ' + p.tipo : ''}</title></rect>`;
    if (k === 'patron') s += `<circle cx="${cx}" cy="${cy}" r="4" class="mk mk-patron" pointer-events="none"/>`;
    else if (k === 'escala') s += `<circle cx="${cx}" cy="${cy}" r="4" class="mk mk-escala" pointer-events="none"/>`;
    else if (k === 'mecanico') s += `<rect x="${cx - 4}" y="${cy - 4}" width="8" height="8" class="mk mk-mecanico" pointer-events="none"/>`;
    else if (k === 'noresiste') s += `<circle cx="${cx}" cy="${cy}" r="4" class="mk mk-noresiste" pointer-events="none"/>`;
  }));
  document.getElementById('mapaRed').innerHTML = SVG(w, h, s, 'Conjunto reducido');
  const filas = Object.entries(D.paresRed).filter(([, p]) => p.rob && p.cat !== 'control').sort((a, b) => Math.abs(b[1].rho) - Math.abs(a[1].rho));
  document.getElementById('tablaRed').innerHTML = `<table class="clic"><thead><tr><th>${A}</th><th>${B}</th><th>Tipo</th><th class="n">ρ corregida</th><th class="n">con tamaño</th><th class="n">canary</th><th>Alcance</th></tr></thead><tbody>` +
    (filas.map(([id, p]) => `<tr data-red="${id}"><td>${escH(nom(p.x))}</td><td>${escH(nom(p.y))}</td><td><span class="estado ${claseTipo(p.tipo)}">${p.tipo}</span></td><td class="n">${fmt(p.rho)}</td><td class="n">${fmt(p.tam)}</td><td class="n">${fmt(p.can)}</td><td>${escH(p.alc)}</td></tr>`).join('') ||
     '<tr><td colspan="7" class="vacio">Ningún par robusto.</td></tr>') + '</tbody></table>';
  const ini = filas.find(([, p]) => p.tipo === 'patrón') || filas[0];
  if (ini) explorar(ini[0], 'red');
}

/* ── CCA, triangulación, PCA conjunto ── */
function extras() {
  const k = D.cca;
  document.getElementById('cca').innerHTML = k ? `<p>Correlaciones canónicas entre los componentes de ${A} y de ${B}: <b>${k.correlaciones.map(v => fmt(v)).join(' · ')}</b> (n = ${k.n} releases).</p>` +
    `<p>La primera, frente a lo que da al desplazar en el tiempo una de las series (1000 corrimientos): p = ${String(k.p_primera).replace('.', ',')}; percentil 95 de la nula ${fmt(k.nula_p95)}.</p>` +
    `<p class="nota">Si la primera supera claramente a la nula, los componentes de las dos dimensiones están conectados en conjunto, aunque ningún par suelto se destaque.</p>` : '<p class="vacio">No se pudo calcular (pocos componentes o releases en común).</p>';
  document.getElementById('triang').innerHTML = D.triang.length ? `<div class="tabla"><table><thead><tr><th>Patrón</th><th class="n">ρ</th><th>Componentes</th><th>Par de componentes robusto</th></tr></thead><tbody>` +
    D.triang.sort((a, b) => (b.ok - a.ok) || Math.abs(b.rho) - Math.abs(a.rho)).map(t => `<tr><td>${escH(t.x)} ↔ ${escH(t.y)}</td><td class="n">${fmt(t.rho)}</td><td>${escH(t.cx || '—')} / ${escH(t.cy || '—')}</td><td>${t.ok ? '<span class="estado patron">triangulado</span>' : 'no'}</td></tr>`).join('') + '</tbody></table></div>'
    : '<p class="vacio">No hay patrones para triangular.</p>';
  const P = D.pca;
  if (!P || !P.componentes) { document.getElementById('pcaConj').innerHTML = `<p class="vacio">${escH(P && P.error ? P.error : 'No se corrió el PCA conjunto.')}</p>`; return; }
  document.getElementById('pcaConj').innerHTML = `<p>${P.variables} variables y ${P.n} releases; Horn retiene ${P.k} componentes.</p><div class="dosc">` +
    P.componentes.map(c => `<div class="cp-card"><h3><span>CP${c.n}</span><span class="cuenta">${Math.round(c.varianza * 100)} %</span></h3><div class="met">bootstrap ${fmt(c.bootstrap)}${c.mixto ? ' · <b>mezcla dimensiones</b>' : ''}</div>` +
      c.cargas.slice(0, 8).map(([v, x]) => { const w = Math.min(1, Math.abs(x)) * 50, d = D.dimDe[v];
        return `<div class="carga"><span class="nm" title="${escH(nom(v))}"><span class="tag-dim ${d === A ? 'tag-a' : 'tag-b'}">${d ? d[0] : '?'}</span>${escH(nom(v))}</span><span class="bx"><i style="${x >= 0 ? 'left:50%' : 'right:50%'};width:${w}%;background:var(${d === A ? '--serie' : '--serie2'})"></i></span><span class="vl">${fmt(x)}</span></div>`; }).join('') + '</div>').join('') + '</div>';
}

/* ── filtros y eventos ── */
function aplicarFiltro(t) {
  filtroTipo = filtroTipo === t ? null : t;
  document.querySelectorAll('[data-tipo]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.tipo === filtroTipo)));
  mapa(); red(); tabla();
}
document.addEventListener('click', e => {
  const t = e.target.closest('[data-tipo]'); if (t) { aplicarFiltro(t.dataset.tipo); return; }
  const p = e.target.closest('[data-par]'); if (p) { explorar(p.dataset.par, false); document.getElementById('explor').scrollIntoView({behavior: 'smooth', block: 'start'}); return; }
  const c = e.target.closest('[data-cp]'); if (c) { explorar(c.dataset.cp, 'cp'); return; }
  const r = e.target.closest('[data-red]'); if (r) { explorar(r.dataset.red, 'red'); document.getElementById('explorRed').scrollIntoView({behavior: 'smooth', block: 'start'}); }
});
const sel = document.getElementById('selPar');
const robustos = Object.entries(D.pares).filter(([, p]) => p.rob && p.cat !== 'control').sort((a, b) => Math.abs(b[1].rho) - Math.abs(a[1].rho));
sel.innerHTML = robustos.map(([id, p]) => `<option value="${id}">${escH(nom(p.x))} ↔ ${escH(nom(p.y))} · ${fmt(p.rho)} · ${p.tipo}</option>`).join('');
sel.addEventListener('change', () => explorar(sel.value, false));
mapa(); red(); tabla(); componentes(); reducido(); extras();
const inicial = robustos.find(([, p]) => p.tipo === 'patrón') || robustos[0];
if (inicial) explorar(inicial[0], false);
"""


def escribir(dim_a, dim_b):
    datos, cuenta, total = construir(dim_a, dim_b)
    chips = "".join(f'<button class="chip" type="button" data-tipo="{esc(t)}" aria-pressed="false">{esc(l)} · {cuenta.get(t, 0)}</button>' for t, l in TIPOS)
    compart = datos["compartidas"]
    nota_compart = (f'<p class="nota">Variables asignadas a las dos dimensiones: '
                    + ", ".join(f"{esc(datos['nombres'].get(v, v))} → {esc(d)}" for v, d in compart.items()) + ".</p>") if compart else ""
    kpis = "".join(f'<div class="kpi"><div class="v">{v}</div><div class="l">{esc(l)}</div><div class="d">{esc(d)}</div></div>' for v, l, d in [
        (len(datos["varsA"]), f"variables de {dim_a}", "un lado del cruce"),
        (len(datos["varsB"]), f"variables de {dim_b}", "el otro lado"),
        (total, "pares evaluados", "variables de un lado × del otro"),
        (cuenta.get("patrón", 0), "patrones", "robustos, sin escala ni construcción"),
        (cuenta.get("escala", 0) + cuenta.get("no resiste tamaño", 0), "de escala", "los explica la cantidad de personas"),
        (f'{len(datos["comps"][dim_a])} × {len(datos["comps"][dim_b])}', "componentes cruzados", "los firmes de cada PCA"),
    ])
    titulo = f"Cruce {dim_a}–{dim_b}"
    cuerpo = f"""<main>
<h1>{esc(titulo)}</h1>
<p class="sub">Correlaciones entre las variables y entre los componentes principales de {esc(dim_a)} y de {esc(dim_b)} · serie estable de next.js, con la réplica en canary · mismo método que el análisis dentro de cada dimensión</p>
<div class="kpis">{kpis}</div>{nota_compart}

<h2>1. Mapa de las correlaciones cruzadas</h2>
<p class="sub">Filas: {esc(dim_a)}; columnas: {esc(dim_b)}. Color: ρ corregida (naranja positiva, azul negativa). Marcas: los pares robustos según su tipo. Tocá una celda para ver el par.</p>
<div class="filtros">{chips}</div>
<div class="leyenda"><span><i class="mk-p"></i>patrón</span><span><i class="mk-e"></i>escala</span><span><i class="mk-m"></i>mecánico</span><span><i class="mk-n"></i>no resiste tamaño</span></div>
<div class="panel mapa-cont" id="mapa"></div>

<h2>2. Red de relaciones robustas</h2>
<p class="sub">Las variables de {esc(dim_a)} a la izquierda y las de {esc(dim_b)} a la derecha. Cada línea es una relación robusta: color según el signo, grosor según la fuerza, punteada si no es un patrón. El número junto a cada variable es la cantidad de patrones en los que participa: las que tienen más hacen de puente entre las dimensiones.</p>
<div class="leyenda"><span><i class="linea-pos"></i>positiva</span><span><i class="linea-neg"></i>negativa</span><span><i class="punteada"></i>escala, mecánica o sin control por tamaño</span><span><i class="dim-a"></i>{esc(dim_a)}</span><span><i class="dim-b"></i>{esc(dim_b)}</span></div>
<div class="panel" id="red"></div>

<h2>3. Pares robustos</h2>
<p class="sub">Los filtros del mapa también se aplican acá. Tocá una fila para ver el par.</p>
<div class="filtros">{chips}<span class="conteo" id="conteo"></span></div>
<div class="panel tabla"><table class="clic"><thead><tr><th>{esc(dim_a)}</th><th>{esc(dim_b)}</th><th>Tipo</th><th class="n">ρ corregida</th><th class="n">cruda</th><th class="n">con tamaño</th><th class="n">canary</th><th>Alcance</th></tr></thead><tbody id="cuerpoTabla"></tbody></table></div>

<h2>4. Explorador de un par</h2>
<div class="selectores"><label>Par robusto<select id="selPar"></select></label></div>
<div class="panel" id="explor"></div>

<h2>5. Componentes principales</h2>
<p class="sub">Los componentes firmes de cada dimensión (estables en el bootstrap y replicados en canary) y la correlación entre sus puntajes por release, con el mismo método que para las variables.</p>
<div class="dosc"><div id="cpA"></div><div id="cpB"></div></div>
<div class="panel" id="matrizCp"></div>
<div class="panel" id="explorCp"></div>

<h2>6. Conjunto reducido</h2>
<p class="sub">De cada lado: {'el puntaje de cada componente firme (◆)' if datos['modoRed'] == 'puntajes' else 'la variable de carga más alta de cada componente firme'} más las variables que no cargan en ningún componente (las cargas de cada componente están en la sección 5). Cruza aspectos completos y métricas independientes sin repetir la misma información, con menos comparaciones que el cruce de todas las variables. Tocá una celda o una fila para ver el par.</p>
<div class="leyenda"><span><i class="mk-p"></i>patrón</span><span><i class="mk-e"></i>escala</span><span><i class="mk-m"></i>mecánico o comparte una métrica</span><span><i class="mk-n"></i>no resiste tamaño</span></div>
<div class="panel mapa-cont" id="mapaRed"></div>
<div class="panel tabla" id="tablaRed"></div>
<div class="panel" id="explorRed"></div>

<h2>7. Correlación canónica entre componentes</h2>
<div class="panel" id="cca"></div>

<h2>8. Triangulación</h2>
<p class="sub">Un patrón de variables queda triangulado si sus dos variables cargan en componentes que también se relacionan de forma robusta, sin ser un efecto del tamaño.</p>
<div class="panel" id="triang"></div>

<h2>9. PCA conjunto</h2>
<p class="sub">Un PCA con las variables que definen los componentes de las dos dimensiones. Un componente que mezcla variables de las dos es otra señal de conexión.</p>
<div id="pcaConj"></div>
<p class="nota">Método: ver analisis/cruce_dimensiones.md.</p>
</main>"""
    pagina = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
              f'<title>{esc(titulo)}</title><style>{rc.ESTILO}{ESTILO_EXTRA}</style></head><body>{cuerpo}'
              f'<script type="application/json" id="datos">{json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")}</script>'
              f"<script>{SCRIPT}</script></body></html>")
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / f"reporte_cruce_{dim_a.lower()}_{dim_b.lower()}.html"
    destino.write_text(pagina, encoding="utf-8")
    return destino


def main():
    if len(sys.argv) != 3:
        sys.exit("Uso: python3 analisis/reporte_cruce_dimensiones.py <DimA> <DimB>")
    dim_a, dim_b = (d.strip().capitalize() for d in sys.argv[1:3])
    destino = escribir(dim_a, dim_b)
    print(f"Reporte: {destino} ({destino.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
