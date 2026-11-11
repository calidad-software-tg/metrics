#!/usr/bin/env python3
"""
analisis/reporte_tres_dimensiones.py

Reporte HTML autocontenido del análisis de las tres dimensiones a la vez.

Uso:
    python3 analisis/reporte_tres_dimensiones.py

Lee salidas/4_tres_dimensiones/ (resumen.json, red.csv, triangulos.csv, triangulacion_variables.csv,
perfiles.csv, rezago.csv) y salidas/5_patrones/cadenas.csv, y escribe
salidas/reportes/_partes/tridimensional/tres_dimensiones.html (reportes.py la pasa a tridimensional.html).

Secciones:
  1. Resumen.
  2. Los componentes que entran, por dimensión, con las variables que los definen.
  3. Medida global: correlación canónica generalizada, RV y MFA frente a la nula, en cada variante, y
     la conexión de cada par de dimensiones.
  4. Red de componentes: marginal (el cruce de a dos) y parcial (descontando los demás componentes).
  5. Triángulos de componentes: cada lado antes y después de descontar el tercer vértice.
  6. Cadenas entre variables (relaciones.py): tríos de tres aspectos distintos y qué lado desaparece.
  7. Perfiles de releases y rezago.
"""
import html
import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reporte_cruce as rc  # noqa: E402  (estilo y nombres cortos)
import rutas  # noqa: E402

ENTRADA = rutas.TRES_DIMENSIONES
SALIDA = rutas.REPORTES_TRES
DIMS = ("Persona", "Proceso", "Producto")
SIGLA = {"Persona": "Pe", "Proceso": "Pr", "Producto": "Pd"}

ESTILO_EXTRA = """
:root { --persona:#2a78d6; --proceso:#eb6834; --producto:#1f9e74; }
@media (prefers-color-scheme: dark) { :root:where(:not([data-theme="light"])) { --persona:#3987e5; --proceso:#e0743f; --producto:#2fb487; } }
:root[data-theme="dark"] { --persona:#3987e5; --proceso:#e0743f; --producto:#2fb487; }
nav.indice { background:var(--superficie); border:1px solid var(--borde); border-radius:10px; padding:12px 16px; margin:16px 0 0; font-size:14px; }
nav.indice ol { margin:6px 0 0; padding-left:20px; columns:2; }
nav.indice a { color:var(--texto); }
.dims { display:grid; grid-template-columns:repeat(auto-fit, minmax(260px, 1fr)); gap:12px; }
.dim h3 { display:flex; align-items:center; gap:8px; }
.dim h3 i { width:12px; height:12px; border-radius:50%; display:inline-block; }
.comp { border-top:1px solid var(--borde); padding:10px 0 4px; }
.comp:first-of-type { border-top:0; }
.comp b { font-weight:600; }
.comp .id { color:var(--tenue); font-size:12px; margin-left:4px; }
.carga { display:grid; grid-template-columns:minmax(0,1fr) 80px 44px; gap:6px; align-items:center; font-size:13px; margin-top:3px; }
.carga span:first-child { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.carga .bar { height:8px; background:var(--div-mid); border-radius:4px; position:relative; }
.carga .bar i { position:absolute; top:0; bottom:0; border-radius:4px; }
.carga .x { text-align:right; font-variant-numeric:tabular-nums; color:var(--texto2); }
.botones { display:flex; gap:8px; flex-wrap:wrap; margin:4px 0 8px; }
.botones button { font:inherit; font-size:13px; padding:6px 12px; border-radius:8px; border:1px solid var(--borde);
  background:var(--superficie); color:var(--texto); cursor:pointer; }
.botones button[aria-pressed="true"] { background:var(--texto); color:var(--fondo); border-color:var(--texto); }
.leyenda { display:flex; flex-wrap:wrap; gap:14px; font-size:13px; color:var(--texto2); margin-top:8px; }
.leyenda span { display:flex; align-items:center; gap:6px; }
.leyenda svg { width:28px; height:10px; display:inline; }
.etq { display:inline-block; font-size:12px; padding:1px 8px; border-radius:999px; border:1px solid var(--borde); white-space:nowrap; }
.etq.fuerte { background:var(--texto); color:var(--fondo); border-color:var(--texto); }
.cadenas { display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:12px; }
.cadena svg { max-width:380px; margin:0 auto; }
.cadena p { margin:6px 0 0; font-size:13px; color:var(--texto2); }
svg .nodo-t { fill:var(--texto); font-size:12.5px; text-anchor:middle; dominant-baseline:middle;
  paint-order:stroke; stroke:var(--superficie); stroke-width:4px; stroke-linejoin:round; }
.chico svg { max-width:460px; margin:0 auto; }
svg .nodo-s { fill:var(--tenue); font-size:11px; text-anchor:middle; dominant-baseline:middle; }
svg .lado-t { font-size:12px; text-anchor:middle; dominant-baseline:middle; font-variant-numeric:tabular-nums; }
svg .fondo-t { fill:var(--superficie); }
td .tachado { text-decoration:line-through; color:var(--tenue); }
"""


def esc(v):
    return html.escape(str(v), quote=True)


def num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else f


def fmt(v, d=2, signo=True):
    f = num(v)
    if f is None:
        return "—"
    s = f"{f:+.{d}f}" if signo else f"{f:.{d}f}"
    return s.replace(".", ",")


def verdadero(v):
    return str(v).strip().lower() in ("true", "1", "sí", "si")


def leer(nombre, base=ENTRADA):
    ruta = base / nombre
    return pd.read_csv(ruta) if ruta.exists() else pd.DataFrame()


def nombre_variante(v):
    s = v.replace("_", " ")
    for a, b in (("tamano", "tamaño"), ("documentacion", "documentación"), ("renovacion", "renovación")):
        s = s.replace(a, b)
    return "Todos los componentes" if s == "todos" else s[0].upper() + s[1:]


def ticks_redondos(vmax, n=5):
    paso = vmax / n
    mag = 10 ** math.floor(math.log10(paso))
    paso = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= paso)
    return [paso * i for i in range(int(vmax / paso) + 2)], paso


def color_dim(dim):
    return f"var(--{dim.lower()})"


# ── piezas ────────────────────────────────────────────────────────────────────

def kpis(res, red, tris, cadenas):
    g = res["global_"].get("todos", {})
    parcial = red[red.condicion == "parcial"] if not red.empty else red
    pat_parcial = int(parcial.patron.map(verdadero).sum()) if not parcial.empty else 0
    tri3 = int((tris.tipo == "tridimensional").sum()) if not tris.empty else 0
    n_cad = int((cadenas.tipo == "cadena").sum()) if not cadenas.empty else 0
    n_tri_v = int((cadenas.tipo == "tridimensional").sum()) if not cadenas.empty else 0
    sig = g.get("gcca_p") is not None and g["gcca_p"] < 0.05
    items = [
        (f"{res['releases']['estable']}", "releases estables", f"{res['releases']['canary']} en la réplica (canary)"),
        (f"{len(res['componentes'])}", "componentes", " · ".join(f"{sum(1 for c in res['componentes'].values() if c['dimension'] == d)} {d}" for d in DIMS)),
        (fmt(g.get("gcca"), 2, False), "asociación global (GCCA)",
         f"nula p95 {fmt(g.get('gcca_nula_p95'), 2, False)} · " + ("distinta del azar" if sig else "no se distingue del azar")),
        (f"{pat_parcial}", "pares de componentes patrón", "en la red parcial (sin los demás componentes)"),
        (f"{tri3}", "triángulos de componentes", "tridimensionales (los tres lados se mantienen)"),
        (f"{n_tri_v} / {n_cad}", "tríos de variables", "tridimensionales / cadenas"),
    ]
    return '<div class="kpis">' + "".join(
        f'<div class="kpi"><div class="v">{esc(v)}</div><div class="l">{esc(l)}</div><div class="d">{esc(d)}</div></div>'
        for v, l, d in items) + "</div>"


def componentes(res, nombres):
    cols = []
    for d in DIMS:
        cs = [(k, c) for k, c in res["componentes"].items() if c["dimension"] == d]
        filas = []
        for k, c in cs:
            cargas = c.get("cargas") or [[v, None] for v in c["variables"]]
            lineas = []
            for v, x in cargas:
                if x is None:
                    lineas.append(f'<div class="carga"><span title="{esc(v)}">{esc(nombres.get(v, v))}</span><span></span><span></span></div>')
                    continue
                ancho = min(abs(x), 1) * 50
                izq = 50 if x >= 0 else 50 - ancho
                col = "var(--div-pos)" if x >= 0 else "var(--div-neg)"
                lineas.append(f'<div class="carga"><span title="{esc(v)}">{esc(nombres.get(v, v))}</span>'
                              f'<span class="bar"><i style="left:{izq:.1f}%;width:{ancho:.1f}%;background:{col}"></i></span>'
                              f'<span class="x">{fmt(x)}</span></div>')
            filas.append(f'<div class="comp"><b>{esc(c["nombre"])}</b><span class="id">{esc(k)}</span>{"".join(lineas)}</div>')
        cols.append(f'<div class="panel dim"><h3><i style="background:{color_dim(d)}"></i>{d}</h3>'
                    + ("".join(filas) or '<p class="vacio">Sin componentes.</p>') + "</div>")
    return '<div class="dims">' + "".join(cols) + "</div>"


def grafico_global(res, medida, titulo):
    """Puntos: valor observado (estable y canary) frente al percentil 95 de la nula, por variante."""
    g = res["global_"]
    variantes = [k for k in g if not k.endswith("_canary")]
    W, fila, izq, der, top = 760, 34, 230, 30, 26
    H = top + fila * len(variantes) + 34
    vals = []
    for v in variantes:
        for s in (v, v + "_canary"):
            if s in g:
                vals += [g[s].get(medida), g[s].get(f"{medida}_nula_p95")]
    vals = [x for x in vals if x is not None]
    ticks, paso = ticks_redondos(max(vals) * 1.05 if vals else 1)
    vmax = ticks[-1]
    X = lambda x: izq + (W - izq - der) * x / vmax  # noqa: E731
    dec = max(0, -math.floor(math.log10(paso)) + (1 if paso / 10 ** math.floor(math.log10(paso)) == 2.5 else 0))
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(titulo)}">']
    for x in ticks:
        s.append(f'<line class="grid" x1="{X(x):.1f}" x2="{X(x):.1f}" y1="{top - 8}" y2="{H - 30}"/>'
                 f'<text class="tick" x="{X(x):.1f}" y="{H - 24}">{f"{x:.{dec}f}".replace(".", ",")}</text>')
    for i, v in enumerate(variantes):
        y = top + fila * i + fila / 2
        etiqueta = nombre_variante(v)
        s.append(f'<text class="cat" x="{izq - 10}" y="{y:.1f}">{esc(etiqueta)}</text>')
        for s_k, dy, clase in ((v, -6, "var(--serie)"), (v + "_canary", 6, "var(--serie2)")):
            if s_k not in g:
                continue
            o, nula, p = g[s_k].get(medida), g[s_k].get(f"{medida}_nula_p95"), g[s_k].get(f"{medida}_p")
            if o is None:
                continue
            yy = y + dy
            if nula is not None:
                s.append(f'<line x1="{X(0):.1f}" x2="{X(nula):.1f}" y1="{yy:.1f}" y2="{yy:.1f}" stroke="var(--borde)" stroke-width="5" stroke-linecap="round"/>'
                         f'<line x1="{X(nula):.1f}" x2="{X(nula):.1f}" y1="{yy - 5:.1f}" y2="{yy + 5:.1f}" stroke="var(--tenue)" stroke-width="2"/>')
            serie = "canary" if s_k.endswith("_canary") else "estable"
            s.append(f'<circle cx="{X(o):.1f}" cy="{yy:.1f}" r="5" fill="{clase}"><title>{esc(etiqueta)} · {serie}: {o:.3f} '
                     f'(nula p95 {nula:.3f}, p = {p:.3f})</title></circle>')
    s.append("</svg>")
    leyenda = ('<div class="leyenda"><span><svg viewBox="0 0 28 10"><circle cx="14" cy="5" r="4.5" fill="var(--serie)"/></svg>estable</span>'
               '<span><svg viewBox="0 0 28 10"><circle cx="14" cy="5" r="4.5" fill="var(--serie2)"/></svg>canary (réplica)</span>'
               '<span><svg viewBox="0 0 28 10"><line x1="2" x2="22" y1="5" y2="5" stroke="var(--borde)" stroke-width="5" stroke-linecap="round"/>'
               '<line x1="22" x2="22" y1="0" y2="10" stroke="var(--tenue)" stroke-width="2"/></svg>hasta el percentil 95 de la nula</span></div>')
    return f'<div class="panel"><h3>{esc(titulo)}</h3>{"".join(s)}{leyenda}</div>'


def triangulo_dimensiones(res):
    """Las tres dimensiones como vértices; cada lado, la correlación canónica del par (variante todos)."""
    g = res["global_"].get("todos", {})
    r, rv = g.get("gcca_r", {}), g.get("rv", {})
    W, H = 420, 300
    pos = {0: (210, 48), 1: (70, 250), 2: (350, 250)}
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Conexión de cada par de dimensiones">']
    for clave, (a, b) in (("0-1", (0, 1)), ("0-2", (0, 2)), ("1-2", (1, 2))):
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        val = r.get(clave)
        ancho = 1.5 + 9 * abs(val or 0)
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="var(--tenue)" stroke-opacity=".55" stroke-width="{ancho:.1f}" stroke-linecap="round">'
                 f'<title>{DIMS[a]}–{DIMS[b]}: correlación canónica {fmt(val)}, RV {fmt(rv.get(clave), 2, False)}</title></line>')
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        s.append(f'<rect class="fondo-t" x="{mx - 40}" y="{my - 18}" width="80" height="36" rx="6"/>'
                 f'<text class="lado-t" x="{mx}" y="{my - 6}" fill="var(--texto)">{fmt(val)}</text>'
                 f'<text class="nodo-s" x="{mx}" y="{my + 9}">RV {fmt(rv.get(clave), 2, False)}</text>')
    for i, d in enumerate(DIMS):
        x, y = pos[i]
        s.append(f'<circle cx="{x}" cy="{y}" r="34" fill="{color_dim(d)}"/>'
                 f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" style="fill:#fff;font-weight:600;font-size:13px">{d}</text>')
    s.append("</svg>")
    return ('<div class="panel chico"><h3>Conexión de cada par (todos los componentes, serie estable)</h3>' + "".join(s)
            + '<p class="nota">Cada lado: correlación entre las variables canónicas de las dos dimensiones y coeficiente RV. '
              'El grosor es proporcional a la correlación.</p></div>')


ESTILO_LADO = {
    "patrón": dict(color="var(--texto)", dash="", w=3.2),
    "escala": dict(color="var(--tenue)", dash="6 4", w=2.4),
    "mecánico": dict(color="var(--tenue)", dash="2 4", w=2.4),
}


def red_componentes(res, red, condicion):
    """Siete componentes en tres columnas; líneas para los pares con q < 0,05, con estilo según el tipo."""
    sub = red[red.condicion == condicion] if not red.empty else red
    comps = res["componentes"]
    W, H = 760, 360
    xs = {"Persona": 130, "Proceso": 380, "Producto": 630}
    pos = {}
    for d in DIMS:
        ids = [k for k, c in comps.items() if c["dimension"] == d]
        for i, k in enumerate(ids):
            pos[k] = (xs[d], 90 + (H - 140) * (i + 0.5) / max(len(ids), 1))
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Red de componentes ({condicion})">']
    etiquetas = []
    for d in DIMS:
        s.append(f'<text class="eje" x="{xs[d]}" y="22" style="font-weight:600;fill:{color_dim(d)}">{d}</text>')
    for _, f in sub.iterrows():
        a, b = f.par.split("__")
        if a not in pos or b not in pos:
            continue
        q, rho = num(f.q), num(f.rho)
        if q is None or q >= 0.05 or rho is None:
            continue
        tipo = f.tipo if isinstance(f.tipo, str) else ""
        est = ESTILO_LADO.get(tipo, dict(color="var(--tenue)", dash="", w=1.2))
        op = 1 if tipo in ESTILO_LADO else .45
        (x1, y1), (x2, y2) = pos[a], pos[b]
        # Persona–Producto pasa por arriba de Proceso
        if {comps[a]["dimension"], comps[b]["dimension"]} == {"Persona", "Producto"}:
            cy = min(y1, y2) - 90
            camino = f"M{x1},{y1} Q{(x1 + x2) / 2},{cy} {x2},{y2}"
        else:
            camino = f"M{x1},{y1} L{x2},{y2}"
        sentido = "positiva" if rho > 0 else "negativa"
        s.append(f'<path d="{camino}" fill="none" stroke="{est["color"]}" stroke-width="{est["w"]}" stroke-dasharray="{est["dash"]}" '
                 f'stroke-opacity="{op}" stroke-linecap="round"><title>{esc(comps[a]["nombre"])} ↔ {esc(comps[b]["nombre"])}: '
                 f'{fmt(rho)} ({tipo or sentido}), canary {fmt(f.rho_canary)}, con tamaño {fmt(f.rho_tamano)}</title></path>')
    for k, (x, y) in pos.items():
        c = comps[k]
        s.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{color_dim(c["dimension"])}"><title>{esc(k)}</title></circle>')
        etiquetas.append(f'<text class="nodo-t" x="{x}" y="{y + 22}">{esc(c["nombre"])}</text>')
    s += etiquetas + ["</svg>"]
    return "".join(s)


def leyenda_red():
    def linea(color, dash, w, op=1):
        return (f'<svg viewBox="0 0 28 10"><line x1="2" x2="26" y1="5" y2="5" stroke="{color}" stroke-width="{w}" '
                f'stroke-dasharray="{dash}" stroke-opacity="{op}" stroke-linecap="round"/></svg>')
    return ('<div class="leyenda">'
            f'<span>{linea("var(--texto)", "", 3.2)}patrón</span>'
            f'<span>{linea("var(--tenue)", "6 4", 2.4)}escala (efecto del tamaño)</span>'
            f'<span>{linea("var(--tenue)", "2 4", 2.4)}mecánico</span>'
            f'<span>{linea("var(--tenue)", "", 1.2, .45)}significativa, no robusta</span>'
            "</div>")


def tabla_triangulos(tris, comps):
    if tris.empty:
        return '<p class="vacio">No hay triángulos de componentes.</p>'
    filas = []
    orden = {"tridimensional": 0, "cadena": 1, "solo tamaño": 2, "pares sueltos": 3}
    for _, t in sorted(tris.iterrows(), key=lambda it: orden.get(it[1].tipo, 9)):
        ids = [x.strip() for x in t.triangulo.split("·")]
        lados = []
        for i in (1, 2, 3):
            a, b = t[f"lado{i}"].split("__")
            tipo = t[f"lado{i}_tipo"] if isinstance(t[f"lado{i}_tipo"], str) else ""
            lados.append(f"{esc(comps.get(a, {}).get('nombre', a))} ↔ {esc(comps.get(b, {}).get('nombre', b))}: "
                         f"{fmt(t[f'lado{i}_marginal'])} → {fmt(t[f'lado{i}_sin_tercero'])}" + (f" <span class='etq'>{esc(tipo)}</span>" if tipo else ""))
        nombre = " · ".join(esc(comps.get(i, {}).get("nombre", i)) for i in ids)
        clase = "etq fuerte" if t.tipo in ("tridimensional", "cadena") else "etq"
        red_p = t.get("tipo_red_parcial", "")
        filas.append(f"<tr><td>{nombre}</td><td><span class='{clase}'>{esc(t.tipo)}</span></td>"
                     f"<td>{esc(t.tipo_epocas if isinstance(t.tipo_epocas, str) else '')}</td>"
                     f"<td>{esc(red_p if isinstance(red_p, str) else '')}</td><td>{'<br>'.join(lados)}</td></tr>")
    return ('<div class="panel tabla"><table><thead><tr><th>Triángulo</th><th>Tipo</th><th>Con épocas</th><th>Red parcial</th>'
            '<th>Lados: marginal → sin el tercer vértice</th></tr></thead><tbody>' + "".join(filas) + "</tbody></table></div>")


def dimension_de(var, asignaciones):
    for parte in str(asignaciones).split("|")[0].split(","):
        if "→" in parte:
            v, d = parte.strip().split("→")
            if v.strip() == var:
                return d.strip()
    return None


def diagrama_cadena(fila, nombres):
    variables = [v.strip() for v in fila.variables.split("·")]
    dims = {v: dimension_de(v, fila.asignaciones) for v in variables}
    orden = sorted(variables, key=lambda v: DIMS.index(dims[v]) if dims[v] in DIMS else 9)
    W, H = 330, 225
    pos = dict(zip(orden, [(165, 38), (92, 170), (238, 170)]))
    caen = {frozenset(x.strip() for x in p.split("↔")) for p in str(fila.desaparece_al_descontar).split(";") if "↔" in p}
    s = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Trío {esc(fila.variables)}">']
    for i in (1, 2, 3):
        a, b = (x.strip() for x in fila[f"lado{i}"].split("↔"))
        if a not in pos or b not in pos:
            continue
        (x1, y1), (x2, y2) = pos[a], pos[b]
        cae = frozenset((a, b)) in caen
        rho, sin = num(fila[f"lado{i}_rho"]), num(fila[f"lado{i}_sin_tercero"])
        color = "var(--tenue)" if cae else "var(--texto2)"
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{1.5 + 7 * abs(rho or 0):.1f}" '
                 f'stroke-linecap="round" stroke-opacity="{.5 if cae else .8}" stroke-dasharray="{"5 5" if cae else ""}"/>')
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        # la etiqueta se corre hacia afuera del triángulo para que no se pisen
        cx, cy = sum(px for px, _ in pos.values()) / 3, sum(py for _, py in pos.values()) / 3
        dx, dy = mx - cx, my - cy
        largo = math.hypot(dx, dy) or 1
        if dy > 0:   # el lado de abajo: arriba de la línea, adentro del triángulo
            my -= 16
        else:
            mx, my = mx + 34 * dx / largo, my + 16 * dy / largo
        s.append(f'<rect class="fondo-t" x="{mx - 44}" y="{my - 10}" width="88" height="20" rx="5"/>'
                 f'<text class="lado-t" x="{mx}" y="{my}" fill="{"var(--tenue)" if cae else "var(--texto)"}">{fmt(rho)} → {fmt(sin)}</text>')
    for v, (x, y) in pos.items():
        d = dims[v] or ""
        s.append(f'<circle cx="{x}" cy="{y}" r="11" fill="{color_dim(d) if d else "var(--tenue)"}"/>'
                 f'<text class="nodo-t" x="{x}" y="{y + (25 if y > 100 else -23)}">{esc(nombres.get(v, v))}</text>')
    s.append("</svg>")
    tipo = fila.tipo
    if tipo == "cadena":
        texto = "Cadena: al descontar el tercer vértice desaparece " + "; ".join(
            " ↔ ".join(esc(nombres.get(x.strip(), x.strip())) for x in p.split("↔")) for p in str(fila.desaparece_al_descontar).split(";"))
    elif tipo == "tridimensional":
        texto = "Tridimensional: los tres lados se mantienen al descontar el tercer vértice."
    else:
        texto = f"{esc(tipo.capitalize())}: los tres vértices no miden aspectos distintos ({esc(fila.temas)})."
    return (f'<div class="panel cadena"><h3><span class="etq{" fuerte" if tipo in ("cadena", "tridimensional") else ""}">{esc(tipo)}</span></h3>'
            f'{"".join(s)}<p>{texto}</p></div>')


def tabla_perfiles(perf, rez, comps):
    partes = []
    nom = lambda k: esc(comps.get(k, {}).get("nombre", k))  # noqa: E731
    if not perf.empty:
        sig = perf[(perf.q < 0.05) & perf.replica.map(verdadero)].sort_values("q")
        filas = "".join(f"<tr><td>{nom(r.desde)}</td><td>{nom(r.otro)}</td><td class='n'>{fmt(r.diferencia_desvios)}</td>"
                        f"<td class='n'>±{fmt(r.nula_p95_abs, 2, False)}</td><td class='n'>{fmt(r.canary)}</td><td class='n'>{fmt(r.q, 3, False)}</td></tr>"
                        for r in sig.itertuples())
        partes.append('<div class="panel tabla"><h3>Perfiles de releases</h3><p class="nota">Diferencia, en desvíos, del componente '
                      'de otra dimensión entre el tercio de releases con el puntaje más alto y el más bajo del primero. Solo las '
                      'significativas (q &lt; 0,05) que se replican en canary.</p>'
                      '<table><thead><tr><th>Desde</th><th>Otro</th><th>Diferencia</th><th>Nula p95</th><th>Canary</th><th>q</th></tr></thead>'
                      f'<tbody>{filas or "<tr><td colspan=6 class=vacio>Ninguno.</td></tr>"}</tbody></table></div>')
    if not rez.empty:
        sig = rez[(rez.q < 0.05)].sort_values("q")
        filas = "".join(f"<tr><td>{nom(r.antes)}</td><td>{nom(r.despues)}</td><td class='n'>{fmt(r.rho)}</td>"
                        f"<td class='n'>{fmt(r.rho_canary)}</td><td>{'sí' if verdadero(r.replica) else 'no'}</td><td class='n'>{fmt(r.q, 3, False)}</td></tr>"
                        for r in sig.itertuples())
        partes.append('<div class="panel tabla"><h3>Rezago</h3><p class="nota">Un componente en la ventana t con otro en la ventana '
                      't + 1. Solo los significativos (q &lt; 0,05).</p>'
                      '<table><thead><tr><th>Antes</th><th>Después</th><th>ρ</th><th>Canary</th><th>Mismo signo</th><th>q</th></tr></thead>'
                      f'<tbody>{filas or "<tr><td colspan=6 class=vacio>Ninguno.</td></tr>"}</tbody></table></div>')
    return "".join(partes)


SCRIPT = """
document.querySelectorAll('[data-vista]').forEach(b => b.addEventListener('click', () => {
  const v = b.dataset.vista;
  document.querySelectorAll('[data-vista]').forEach(x => x.setAttribute('aria-pressed', x.dataset.vista === v));
  document.querySelectorAll('[data-red]').forEach(x => x.hidden = x.dataset.red !== v);
}));
"""


def escribir():
    ruta = ENTRADA / "resumen.json"
    if not ruta.exists():
        sys.exit(f"No existe {ruta}. Corré primero: python3 analisis/tres_dimensiones.py")
    res = json.loads(ruta.read_text(encoding="utf-8"))
    red, tris = leer("red.csv"), leer("triangulos.csv")
    perf, rez = leer("perfiles.csv"), leer("rezago.csv")
    cadenas = leer("cadenas.csv", rutas.PATRONES)
    nombres = rc.nombres_variables()
    comps = res["componentes"]
    repo = rutas.proyecto.REPO or "el repositorio"

    secciones = [("resumen", "Resumen"), ("componentes", "Componentes"), ("global", "Medida global"),
                 ("red", "Red de componentes"), ("triangulos", "Triángulos de componentes"),
                 ("cadenas", "Tríos de variables"), ("perfiles", "Perfiles y rezago")]
    if cadenas.empty:
        bloque_cadenas = '<p class="vacio">No hay tríos de variables de tres dimensiones (salidas/5_patrones/cadenas.csv).</p>'
    else:
        orden = {"tridimensional": 0, "cadena": 1}
        cad = sorted((f for _, f in cadenas.iterrows()), key=lambda f: orden.get(f.tipo, 2))
        bloque_cadenas = '<div class="cadenas">' + "".join(diagrama_cadena(f, nombres) for f in cad) + "</div>"

    cuerpo = f"""<main>
<h1>Análisis de las tres dimensiones</h1>
<p class="sub">{esc(repo)} · Persona, Proceso y Producto a la vez · fuente: salidas/4_tres_dimensiones y salidas/5_patrones/cadenas.csv</p>
<nav class="indice"><b>Contenido</b><ol>{"".join(f'<li><a href="#{a}">{t}</a></li>' for a, t in secciones)}</ol></nav>

<h2 id="resumen">1. Resumen</h2>
<p class="sub">Los cruces de a dos muestran qué dimensiones se relacionan, pero no si tres relaciones de a pares forman un mismo patrón.
Acá se mide la conexión de las tres en conjunto y se buscan tríos, uno por dimensión, que sigan relacionados al descontar el tercero.</p>
{kpis(res, red, tris, cadenas)}

<h2 id="componentes">2. Componentes</h2>
<p class="sub">Los componentes firmes de cada dimensión que entran en el análisis (PCA de cada dimensión), con las variables que los
definen y su carga.</p>
{componentes(res, nombres)}

<h2 id="global">3. Medida global</h2>
<p class="sub">Cuánto se conectan las tres dimensiones en conjunto, frente a 1.000 desalineaciones en el tiempo de cada dimensión
(300 en canary). Un punto a la derecha de la marca de la nula indica una conexión mayor que la del azar. Las variantes sacan
componentes de tamaño, documentación o renovación para ver si la conexión depende de ellos.</p>
{grafico_global(res, "gcca", "Correlación canónica generalizada (suma de las tres correlaciones, de 1 a 3)")}
{grafico_global(res, "rv_medio", "Coeficiente RV medio entre pares de dimensiones")}
{grafico_global(res, "mfa1", "Primer factor del análisis factorial múltiple (parte de la inercia)")}
{triangulo_dimensiones(res)}

<h2 id="red">4. Red de componentes</h2>
<p class="sub">Pares de componentes de dimensiones distintas con q &lt; 0,05. <b>Marginal</b> es el cruce de a dos;
<b>parcial</b> descuenta los demás componentes, así queda la relación directa. Pasá el cursor por una línea para ver sus valores.</p>
<div class="panel">
<div class="botones" role="group" aria-label="Vista de la red">
<button type="button" data-vista="parcial" aria-pressed="true">Parcial</button>
<button type="button" data-vista="marginal" aria-pressed="false">Marginal</button></div>
<div data-red="parcial">{red_componentes(res, red, "parcial")}</div>
<div data-red="marginal" hidden>{red_componentes(res, red, "marginal")}</div>
{leyenda_red()}</div>

<h2 id="triangulos">5. Triángulos de componentes</h2>
<p class="sub">Un componente por dimensión. Cada lado se recalcula descontando el tercer vértice: si los tres lados se mantienen
como patrón es <b>tridimensional</b>; si alguno desaparece, una <b>cadena</b>; si no, son <b>pares sueltos</b> (o relaciones
que solo explica el tamaño del equipo).</p>
{tabla_triangulos(tris, comps)}

<h2 id="cadenas">6. Tríos de variables</h2>
<p class="sub">Tríos de variables, de tres dimensiones y tres aspectos distintos, relacionados de a pares como patrón
(relaciones.py). Cada lado muestra la correlación y, después de la flecha, la correlación descontando el tercer vértice; las
líneas punteadas son las que desaparecen.</p>
{bloque_cadenas}

<h2 id="perfiles">7. Perfiles y rezago</h2>
{tabla_perfiles(perf, rez, comps)}

<p class="nota">Método: analisis/metodologia.md, sección 8. Detalle completo: salidas/4_tres_dimensiones/resumen.md.</p>
</main>"""
    pagina = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
              f'<title>Tres dimensiones</title><style>{rc.ESTILO}{ESTILO_EXTRA}</style></head><body>{cuerpo}'
              f"<script>{SCRIPT}</script></body></html>")
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / "tres_dimensiones.html"
    destino.write_text(pagina, encoding="utf-8")
    return destino


def main():
    destino = escribir()
    print(f"Reporte: {destino} ({destino.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
