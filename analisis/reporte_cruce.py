#!/usr/bin/env python3
"""
analisis/reporte_cruce.py

Genera un reporte HTML de un cruce de dimensiones a partir de las salidas de
generar_correlaciones.py:
  analisis/salidas/pares_correlacion.csv
  analisis/salidas/pares_valores.csv   (valores por release, para los gráficos de dispersión)

Uso:
    python3 analisis/reporte_cruce.py Producto-Producto
    python3 analisis/reporte_cruce.py "persona-proceso"
    python3 analisis/reporte_cruce.py producto          # = Producto-Producto

El reporte (analisis/salidas/reportes/reporte_<cruce>.html) tiene:
  - cantidad de pares, pares evaluados (sin los de control), con relación,
    robustos, robustos que pasan el control por tamaño, sin solapamiento de
    definición y hallazgos candidatos;
  - un mapa de calor con la correlación (corregida o cruda) de todos los pares;
  - un gráfico con la cantidad de pares por categoría;
  - un explorador de pares: dos selectores con todas las combinaciones de
    variables del cruce y, para el par elegido, sus resultados y dos gráficos
    de dispersión (valores ajustados por tiempo y duración, y valores originales);
  - una tabla con todos los pares evaluados, de mayor a menor |ρ corregida|, con
    filtros por dirección (positivas / negativas), significativas, robustas y que
    pasan el control por tamaño (al hacer clic en una fila se abre ese par en el explorador).
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PARES = ROOT / "analisis" / "salidas" / "pares_correlacion.csv"
VALORES = ROOT / "analisis" / "salidas" / "pares_valores.csv"


def archivos_valores(carpeta: Path = VALORES.parent) -> list:
    """pares_valores.csv, o sus dos mitades (_persona / _resto) si generar_correlaciones lo partió."""
    entero = carpeta / "pares_valores.csv"
    if entero.exists():
        return [entero]
    return [a for a in (carpeta / "pares_valores_persona.csv", carpeta / "pares_valores_resto.csv") if a.exists()]


def leer_valores(columnas: list, carpeta: Path = VALORES.parent) -> pd.DataFrame:
    archivos = archivos_valores(carpeta)
    if not archivos:
        return pd.DataFrame(columns=columnas)
    return pd.concat([pd.read_csv(a, usecols=columnas) for a in archivos], ignore_index=True)
DICCIONARIO = ROOT / "analisis" / "salidas" / "diccionario_variables.csv"
SALIDA = ROOT / "analisis" / "salidas" / "reportes"

DIMENSIONES = ["Persona", "Proceso", "Producto"]
UMBRAL_FUERZA = 0.1

NOMBRES_CORTOS = {
    "anmcc": "ANMCC", "mttr": "MTTR", "le": "Learning Easy", "cd": "CD", "dloc": "DLOC",
    "rc": "README Completeness", "cfdr": "CFDR", "nub": "NUB", "noi": "NOI", "nci": "NCI",
    "dis": "DIS", "jarczyk_success_rate": "Jarczyk", "process_performance": "Process Performance",
    "schedule_compliance": "Schedule Compliance", "cdiv": "Contribution Diversity",
    "exprev": "EXPRev", "rexprev": "REXPRev", "rexp": "REXP", "fexp": "FEXP",
    "ss": "Skill Similarity", "nc": "NC", "sc": "Social Contributions",
    "dev_exp": "Development Experience", "disc_centrality": "Discussion Centrality",
    # agregadas en la branch de fixes
    "dloc_flujo": "DLOC 2.0", "commits_doc": "Commits que tocan doc",
    "mttr_p50": "MTTR (mediana de issues)", "mttr_bugs": "MTTR de bugs", "mttr_con_bots": "MTTR con bots",
    "nci_con_bots": "NCI con bots", "wp": "Wiki Presence", "nob_42": "NOB",
}
SUFIJOS = {"valor": "", "mediana": " (mediana)", "p90": " (p90)", "share_top10pct": " (share top 10%)"}

CATEGORIAS = [  # (valor en el csv, etiqueta)
    ("positiva", "Positiva"),
    ("negativa", "Negativa"),
    ("sin_relacion", "Sin relación"),
    ("no_concluyente", "No concluyente"),
    ("insuficiente", "Insuficiente"),
]
ETIQUETA_CATEGORIA = dict(CATEGORIAS) | {"control": "Control"}
PERIODOS = ["2016_2019", "2020_2022", "2023_2024", "2025_2026"]


def normalizar_cruce(texto: str) -> str:
    partes = [p.strip().capitalize() for p in texto.replace("–", "-").split("-") if p.strip()]
    if len(partes) == 1:
        partes = partes * 2
    if len(partes) != 2 or any(p not in DIMENSIONES for p in partes):
        sys.exit(f"Cruce inválido: {texto!r}. Ejemplos: Producto-Producto, Persona-Proceso")
    partes.sort(key=DIMENSIONES.index)
    return "–".join(partes)


def nombres_variables() -> dict:
    d = pd.read_csv(DICCIONARIO)
    out = {}
    for _, r in d.iterrows():
        base = NOMBRES_CORTOS.get(r.metrica_id)
        if base is None or r.estadistico not in SUFIJOS:
            out[r.variable_id] = r.nombre_legible.split(" [")[0]
        else:
            out[r.variable_id] = base + SUFIJOS[r.estadistico]
    return out


def es_verdadero(v) -> bool:
    return str(v).strip().lower() == "true"


def control_tamano(r) -> str:
    if not es_verdadero(r.tamano_aplica) or pd.isna(r.rho_corregida_tamano):
        return "no aplica"
    ok = abs(r.rho_corregida_tamano) >= UMBRAL_FUERZA and (r.rho_corregida_tamano >= 0) == (r.rho_corregida >= 0)
    return "pasa" if ok else "no pasa"


# ── Datos para el explorador de pares ────────────────────────────────────────
def _num(v, d=4):
    return None if pd.isna(v) else round(float(v), d)


def _ic_texto(t):
    """'[-0.08; 0.14]' -> [-0.08, 0.14]; None si está vacío."""
    if not isinstance(t, str):
        return None
    m = re.findall(r"-?\d+(?:\.\d+)?", t.replace("−", "-"))
    return [float(m[0]), float(m[1])] if len(m) == 2 else None


def datos_reporte(p: pd.DataFrame, nombres: dict) -> dict:
    """Variables del cruce, resultados de cada par y, si existe pares_valores.csv, sus
    valores por release (los originales una vez por variable; por par, solo los ajustados)."""
    columnas = ["par_id", "periodo_num", "version", "fecha_hora", "anio", "etapa", "duracion_dias",
                "x_valor", "y_valor", "x_ajustado", "y_ajustado"]
    con_valores = bool(archivos_valores())
    v = leer_valores(columnas)
    v = v[v.par_id.isin(set(p.par_id))]
    releases = (v.drop_duplicates("periodo_num").set_index("periodo_num")[["version", "anio", "etapa", "duracion_dias", "fecha_hora"]]
                .sort_index())
    mayor = releases.version.str.extract(r"^v?(\d+)\.")[0].astype(float)
    releases["backport"] = mayor < mayor.cummax()   # parche de una versión mayor anterior

    serie = {}  # variable -> {periodo_num: valor}
    pares = {}
    for _, r in p.iterrows():
        x, y = r.x_id, r.y_id
        g = v[v.par_id == r.par_id].sort_values("periodo_num")
        serie.setdefault(x, {}).update(dict(zip(g.periodo_num, g.x_valor)))
        serie.setdefault(y, {}).update(dict(zip(g.periodo_num, g.y_valor)))
        pares[r.par_id] = {
            "x": x, "y": y,
            "p": [int(n) for n in g.periodo_num],
            "xa": [_num(a, 1) for a in g.x_ajustado], "ya": [_num(a, 1) for a in g.y_ajustado],
            "n": int(r.n), "cruda": _num(r.rho_cruda, 3), "corr": _num(r.rho_corregida, 3),
            "ic": [_num(r.ic_inf, 2), _num(r.ic_sup, 2)],
            "cat": ETIQUETA_CATEGORIA.get(r.categoria, r.categoria),
            "fuerza": r.fuerza if isinstance(r.fuerza, str) else "",
            "robusta": es_verdadero(r.robusta), "tamano": control_tamano(r),
            "solap": es_verdadero(r.solapamiento_definicion), "control": es_verdadero(r.por_construccion),
            "per": [_num(r[f"rho_{k}"], 2) for k in PERIODOS],
            "icp": [_ic_texto(r.get(f"ic_{k}")) for k in PERIODOS],
            "est": [r.get(f"estado_{k}") if isinstance(r.get(f"estado_{k}"), str) else "" for k in PERIODOS],
            "canary": _num(r.rho_canary, 2), "sincortas": _num(r.rho_corregida_sin_cortas, 2),
            "alcance": r.alcance_temporal if isinstance(r.alcance_temporal, str) else "",
            "escala": r.escala_relacion if isinstance(r.escala_relacion, str) else "",
            "hallazgo": es_verdadero(r.hallazgo_candidato),
            "estable": es_verdadero(r.estable), "cortas": es_verdadero(r.depende_ventanas_cortas),
            "fam": es_verdadero(r.misma_familia),
            "lineal": _num(r.rho_corregida_lineal, 2), "local": _num(r.rho_corregida_local, 2),
            "rtam": _num(r.rho_corregida_tamano, 2),
            "motivo": r.motivo_descarte if isinstance(r.motivo_descarte, str) else "",
        }
    variables = sorted(set(p.x_id) | set(p.y_id), key=lambda k: nombres.get(k, k).lower())
    return {
        "con_valores": con_valores,
        "variables": [{"id": k, "nombre": nombres.get(k, k)} for k in variables],
        "releases": {int(n): [r.version, int(r.anio), r.etapa, _num(r.duracion_dias, 2),
                              f"{str(r.fecha_hora)[:4]}-{str(r.fecha_hora)[4:6]}-{str(r.fecha_hora)[6:8]}",
                              bool(r.backport)]
                     for n, r in releases.iterrows()},
        "serie": {k: {int(n): _num(val, 6) for n, val in s.items() if not pd.isna(val)} for k, s in serie.items()},
        "pares": pares,
    }


# ── HTML ─────────────────────────────────────────────────────────────────────
def esc(v) -> str:
    return html.escape(str(v))


def num(v, d=2) -> str:
    return "—" if pd.isna(v) else f"{v:.{d}f}".replace(".", ",").replace("-", "−")


def grafico(conteos: list[tuple[str, int]], total: int) -> str:
    """Barras horizontales en SVG, una por categoría."""
    alto_barra, sep, ancho_label, ancho_plot = 26, 14, 130, 420
    maximo = max([c for _, c in conteos] + [1])
    escala = max(10, -(-maximo // 10) * 10)  # redondea hacia arriba a decena
    alto = len(conteos) * (alto_barra + sep) + 30
    filas = []
    for i, (etiqueta, c) in enumerate(conteos):
        y = i * (alto_barra + sep)
        w = ancho_plot * c / escala
        pct = f"{c / total:.0%}" if total else "0%"
        r = min(4, w / 2)
        camino = (f"M{ancho_label},{y} h{max(w - r, 0):.1f} q{r:.1f},0 {r:.1f},{r:.1f} "
                  f"v{alto_barra - 2 * r:.1f} q0,{r:.1f} -{r:.1f},{r:.1f} h-{max(w - r, 0):.1f} z") if c else ""
        filas.append(
            f'<g class="barra"><title>{esc(etiqueta)}: {c} pares ({pct})</title>'
            f'<rect x="0" y="{y - sep / 2}" width="{ancho_label + ancho_plot + 90}" height="{alto_barra + sep}" class="hit"/>'
            f'<text x="{ancho_label - 10}" y="{y + alto_barra / 2}" class="cat">{esc(etiqueta)}</text>'
            + (f'<path d="{camino}" class="marca"/>' if c else "")
            + f'<text x="{ancho_label + w + 8}" y="{y + alto_barra / 2}" class="val">{c} ({pct})</text></g>')
    ticks = []
    y_eje = len(conteos) * (alto_barra + sep)
    for k in range(0, escala + 1, max(1, escala // 5)):
        x = ancho_label + ancho_plot * k / escala
        ticks.append(f'<line x1="{x}" x2="{x}" y1="-6" y2="{y_eje - sep}" class="grid"/>'
                     f'<text x="{x}" y="{y_eje + 4}" class="tick">{k}</text>')
    return (f'<svg viewBox="0 -8 {ancho_label + ancho_plot + 90} {alto + 26}" role="img" '
            f'aria-label="Cantidad de pares por categoría">'
            + "".join(ticks) + "".join(filas)
            + f'<text x="{ancho_label + ancho_plot / 2}" y="{y_eje + 30}" class="eje">Cantidad de pares</text></svg>')


ESTILO = """
:root { color-scheme: light;
  --fondo:#fcfcfb; --superficie:#ffffff; --texto:#0b0b0b; --texto2:#52514e; --tenue:#8a8984;
  --borde:#e6e5e0; --div-neg:#2a78d6; --div-mid:#f1f0ec; --div-pos:#eb6834; --serie:#2a78d6; --serie2:#eb6834; --tendencia:#52514e; --banda:rgba(0,0,0,.035); --hover:rgba(42,120,214,.08); }
@media (prefers-color-scheme: dark) { :root:where(:not([data-theme="light"])) { color-scheme: dark;
  --fondo:#141413; --superficie:#1a1a19; --texto:#ffffff; --texto2:#c3c2b7; --tenue:#8f8e86;
  --borde:#33322f; --div-neg:#3987e5; --div-mid:#2c2b29; --div-pos:#d95926; --serie:#3987e5; --serie2:#d95926; --tendencia:#c3c2b7; --banda:rgba(255,255,255,.045); --hover:rgba(57,135,229,.14); } }
:root[data-theme="dark"] { color-scheme: dark;
  --fondo:#141413; --superficie:#1a1a19; --texto:#ffffff; --texto2:#c3c2b7; --tenue:#8f8e86;
  --borde:#33322f; --div-neg:#3987e5; --div-mid:#2c2b29; --div-pos:#d95926; --serie:#3987e5; --serie2:#d95926; --tendencia:#c3c2b7; --banda:rgba(255,255,255,.045); --hover:rgba(57,135,229,.14); }
* { box-sizing: border-box; }
body { margin:0; background:var(--fondo); color:var(--texto);
  font: 15px/1.5 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
main { max-width: 1100px; margin: 0 auto; padding: 32px 16px 64px; }
h1 { font-size: 24px; margin: 0 0 4px; } h2 { font-size: 18px; margin: 40px 0 4px; }
h3 { font-size: 15px; margin: 0 0 6px; }
.sub { color: var(--texto2); margin: 0 0 24px; }
.kpis { display:grid; grid-template-columns: repeat(auto-fit, minmax(150px,1fr)); gap:12px; }
.kpi { background:var(--superficie); border:1px solid var(--borde); border-radius:10px; padding:14px 16px; }
.kpi .v { font-size: 28px; font-weight: 650; font-variant-numeric: tabular-nums; }
.kpi .l { color: var(--texto2); font-size: 13px; }
.kpi .d { color: var(--tenue); font-size: 12px; margin-top: 2px; }
.panel { background:var(--superficie); border:1px solid var(--borde); border-radius:10px; padding:16px; margin-top:12px; }
svg { width:100%; height:auto; display:block; font-size:13px; }
svg .cat { fill:var(--texto); text-anchor:end; dominant-baseline:middle; }
svg .val { fill:var(--texto); dominant-baseline:middle; font-variant-numeric: tabular-nums; }
svg .tick { fill:var(--tenue); text-anchor:middle; dominant-baseline:hanging; font-size:12px; }
svg .ticky { fill:var(--tenue); text-anchor:end; dominant-baseline:middle; font-size:12px; }
svg .eje { fill:var(--texto2); text-anchor:middle; font-size:12px; }
svg .grid { stroke:var(--borde); stroke-width:1; }
svg .cero { stroke:var(--tenue); stroke-width:1; }
svg .marca { fill:var(--serie); }
svg .punto { fill:var(--serie); fill-opacity:.55; }
svg .punto.activo { fill-opacity:1; stroke:var(--superficie); stroke-width:2; }
svg .tendencia { stroke:var(--tendencia); stroke-width:2; fill:none; }
svg .hit { fill:transparent; }
svg .barra:hover .hit { fill:var(--hover); }
.tabla { overflow-x:auto; }
table { border-collapse: collapse; width:100%; font-size:13.5px; }
th, td { text-align:left; padding:7px 10px; border-bottom:1px solid var(--borde); vertical-align:top; }
th { color:var(--texto2); font-weight:600; white-space:nowrap; }
td.n { text-align:right; font-variant-numeric: tabular-nums; white-space:nowrap; }
tbody tr:hover { background: var(--hover); }
table.clic tbody tr { cursor: pointer; }
#tablaPares td:nth-child(2) { min-width: 230px; }
#tablaPares td:nth-child(10) { min-width: 120px; }
.vacio { color: var(--texto2); }
.nota { color: var(--texto2); font-size: 13px; margin-top: 8px; }
.selectores { display:flex; flex-wrap:wrap; gap:12px; align-items:flex-end; }
.selectores label { display:flex; flex-direction:column; gap:4px; font-size:13px; color:var(--texto2); flex:1 1 260px; }
select { font: inherit; color: var(--texto); background: var(--superficie); border:1px solid var(--borde);
  border-radius:8px; padding:8px 10px; min-width:0; width:100%; }
.cuenta { color:var(--tenue); font-size:13px; }
.ficha { display:grid; grid-template-columns: repeat(auto-fit, minmax(170px,1fr)); gap:10px 16px; margin-top:14px; }
.ficha div { font-size:13px; } .ficha b { display:block; color:var(--texto2); font-weight:500; font-size:12px; }
.ficha span { font-variant-numeric: tabular-nums; }
.etiqueta { display:inline-block; padding:1px 8px; border-radius:99px; border:1px solid var(--borde); font-size:12px; }
.motivo { margin-top:10px; font-size:13px; color:var(--texto2); }
.graficos { display:grid; grid-template-columns: repeat(auto-fit, minmax(320px,1fr)); gap:16px; margin-top:12px; }
.grafico-disp { position:relative; }
.tooltip { position:absolute; pointer-events:none; background:var(--superficie); color:var(--texto);
  border:1px solid var(--borde); border-radius:8px; padding:6px 9px; font-size:12px; line-height:1.4;
  box-shadow:0 2px 8px rgba(0,0,0,.12); white-space:nowrap; display:none; z-index:2; }
.leyenda { display:flex; gap:16px; font-size:12px; color:var(--texto2); margin-top:4px; }
.leyenda i { display:inline-block; width:10px; height:10px; border-radius:50%; background:var(--serie); opacity:.7; margin-right:5px; vertical-align:-1px; }
svg .linea-x { stroke:var(--serie); stroke-width:2; fill:none; stroke-linejoin:round; }
svg .linea-y { stroke:var(--serie2); stroke-width:2; fill:none; stroke-linejoin:round; }
svg .marca-x { fill:var(--serie); stroke:var(--superficie); stroke-width:2; }
svg .marca-y { fill:var(--serie2); stroke:var(--superficie); stroke-width:2; }
svg .banda { fill:var(--banda); }
svg .etapa { fill:var(--tenue); font-size:11px; text-anchor:middle; }
svg .titulo-panel { fill:var(--texto); font-size:12.5px; font-weight:600; }
svg .barra-per { fill:var(--serie); }
svg .barra-per.debil { fill-opacity:.35; }
svg .barra-can { fill:var(--serie2); }
svg .bigote { stroke:var(--texto2); stroke-width:1.5; }
svg .ref { stroke:var(--texto2); stroke-width:1.5; stroke-dasharray:5 4; }
svg .ref-txt { fill:var(--texto2); font-size:11.5px; }
svg .val-barra { fill:var(--texto); font-size:12px; text-anchor:middle; font-variant-numeric: tabular-nums; }
svg .per-grupo { cursor:pointer; outline:none; }
svg .per-grupo .hit:hover, svg .per-grupo:focus-visible .hit { fill:var(--hover); }
svg .per-grupo.atenuado { opacity:.3; }
svg .per-grupo.activo .hit { fill:var(--hover); }
svg .banda-clic { fill:transparent; cursor:pointer; }
svg .banda-sel { fill:var(--hover); }
svg .pt-sig { fill:var(--serie); fill-opacity:.85; cursor:pointer; }
svg .pt-ns { fill:var(--tenue); fill-opacity:.45; cursor:pointer; }
svg .pt-rob { stroke:var(--texto); stroke-width:1.5; }
svg .pt-at { opacity:.12; }
svg .arista { cursor:pointer; stroke-linecap:round; stroke-opacity:.85; }
svg .arista:hover { stroke-opacity:1; }
svg .nodo { fill:var(--serie); } svg .nodo.solo { fill:var(--tenue); }
svg .lbl-nodo { fill:var(--texto); font-size:11px; dominant-baseline:middle; } svg .lbl-nodo.solo { fill:var(--tenue); }
svg .fila-hit { fill:transparent; cursor:pointer; } svg g:hover > .fila-hit { fill:var(--hover); }
svg .ic-linea { stroke:var(--serie); stroke-width:2; }
svg .pt-forest { fill:var(--serie); } svg .pt-forest.hueca { fill:var(--superficie); stroke:var(--serie); stroke-width:2; }
svg .pt-sens { fill:var(--texto2); }
svg .txt-celda { fill:var(--texto); font-size:11.5px; text-anchor:middle; dominant-baseline:middle; font-variant-numeric:tabular-nums; }
svg .umbral { stroke:var(--tenue); stroke-width:1; stroke-dasharray:3 3; }
svg .punto.bp { fill:var(--serie2); fill-opacity:.85; }
svg .rug { stroke:var(--serie2); stroke-width:1.5; }
svg .guia { stroke:var(--tenue); stroke-width:1; stroke-dasharray:3 3; }
.filtro-banner { display:none; align-items:center; flex-wrap:wrap; gap:8px 12px; margin-top:12px; padding:10px 14px;
  border:1px solid var(--borde); border-radius:10px; background:var(--hover); font-size:13.5px; }
.filtro-banner.visible { display:flex; }
.filtro-banner button { font:inherit; font-size:13px; border:1px solid var(--borde); border-radius:8px; padding:4px 10px;
  background:var(--superficie); color:var(--texto); cursor:pointer; }
.filtro-banner .aclaracion { color:var(--texto2); font-size:12.5px; flex-basis:100%; }
svg .celda { stroke:var(--superficie); stroke-width:1; }
svg .celda.par { cursor:pointer; }
svg .celda.par:hover { stroke:var(--texto); stroke-width:1.5; }
svg .celda.atenuada { opacity:.18; }
svg .celda.vacia { fill:transparent; }
svg .lbl-fila { fill:var(--texto2); font-size:11px; text-anchor:end; dominant-baseline:middle; }
svg .lbl-col { fill:var(--texto2); font-size:11px; text-anchor:start; dominant-baseline:middle; }
.mapa-cont { overflow-x:auto; }
.filtros { display:flex; flex-wrap:wrap; gap:10px 16px; align-items:center; margin-bottom:10px; }
.chip { font:inherit; font-size:13px; border:1px solid var(--borde); border-radius:99px; padding:5px 12px;
  background:var(--superficie); color:var(--texto2); cursor:pointer; }
.chip[aria-pressed="true"] { background:var(--hover); color:var(--texto); border-color:var(--serie); font-weight:600; }
.chip.limpiar { border-style:dashed; }
.conteo { color:var(--texto2); font-size:13px; margin-left:auto; }
.modo { display:inline-flex; border:1px solid var(--borde); border-radius:8px; overflow:hidden; margin:4px 0 8px; }
.modo button { font:inherit; font-size:13px; border:0; padding:6px 12px; background:var(--superficie); color:var(--texto2); cursor:pointer; }
.modo button.activo { background:var(--hover); color:var(--texto); font-weight:600; }
.leyenda i.y { background:var(--serie2); }
.leyenda i.gris { background:var(--tenue); opacity:.5; }
.leyenda i.anillo { background:var(--serie); box-shadow:0 0 0 1.5px var(--texto); }
.leyenda i.hueco { background:var(--superficie); box-shadow:inset 0 0 0 2px var(--serie); opacity:1; }
.leyenda i.rug { width:2px; height:10px; border-radius:0; background:var(--serie2); opacity:1; }
.leyenda i.linea-neg, .leyenda i.linea-pos { width:16px; height:3px; border-radius:2px; opacity:1; vertical-align:3px; }
.leyenda i.linea-neg { background:var(--div-neg); } .leyenda i.linea-pos { background:var(--div-pos); }
.leyenda i.cuad { border-radius:2px; opacity:1; } .leyenda i.cuad.debil { opacity:.35; }
.leyenda i.punteada { width:16px; height:0; border-top:2px dashed var(--texto2); background:none; border-radius:0; vertical-align:3px; }
.leyenda i.linea { width:14px; height:2px; border-radius:0; background:var(--tendencia); opacity:1; vertical-align:3px; }
"""

SCRIPT_TABLA = r"""
const D = JSON.parse(document.getElementById('datos').textContent);
const nombre = Object.fromEntries(D.variables.map(v => [v.id, v.nombre]));
const fmt = (v, d = 2) => v === null || v === undefined || Number.isNaN(v) ? '—'
  : v.toLocaleString('es-AR', { minimumFractionDigits: d, maximumFractionDigits: d });
let abrirPar = null;              // lo define el explorador, si el reporte tiene valores por release
let actualizarSelectores = null;  // ídem: limita los selectores a los pares que cumplen los filtros
let paresVisibles = new Set(Object.keys(D.pares)), ordenVisibles = [];

const filtros = { dir: 'todas', sig: false, rob: false, tam: false };
const evaluados = Object.entries(D.pares).filter(([, p]) => !p.control);
const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`;
const hayFiltros = () => filtros.dir !== 'todas' || filtros.sig || filtros.rob || filtros.tam;
function renderTabla() {
  const filas = evaluados
    .filter(([, p]) => filtros.dir === 'todas' || (p.corr !== null && (filtros.dir === 'pos' ? p.corr > 0 : p.corr < 0)))
    .filter(([, p]) => !filtros.sig || p.cat === 'Positiva' || p.cat === 'Negativa')
    .filter(([, p]) => !filtros.rob || p.robusta)
    .filter(([, p]) => !filtros.tam || p.tamano === 'pasa')
    .sort((a, b) => Math.abs(b[1].corr ?? 0) - Math.abs(a[1].corr ?? 0));
  // pares disponibles en el explorador: los filtrados; sin filtros, también los de control
  ordenVisibles = filas.map(([id]) => id);
  paresVisibles = new Set(ordenVisibles);
  if (!hayFiltros()) Object.entries(D.pares).forEach(([id, p]) => { if (p.control) paresVisibles.add(id); });
  if (actualizarSelectores) actualizarSelectores();
  const si = b => b ? 'sí' : 'no';
  document.getElementById('conteoTabla').textContent = `${filas.length} de ${evaluados.length} pares evaluados`;
  const cuerpo = filas.map(([id, p], i) => `<tr data-par="${id}" tabindex="0" title="Ver este par en el explorador">
      <td class="n">${i + 1}</td><td>${nombre[p.x]} ↔ ${nombre[p.y]}</td>
      <td class="n">${fmt(p.corr)}</td><td class="n">[${fmt(p.ic[0])}; ${fmt(p.ic[1])}]</td>
      <td>${p.cat}</td><td>${p.fuerza}</td><td>${si(p.robusta)}</td><td>${p.tamano}</td>
      <td>${si(p.solap)}</td><td>${p.alcance}</td><td>${si(p.hallazgo)}</td></tr>`).join('');
  document.getElementById('tablaPares').innerHTML = filas.length
    ? `<table class="clic"><thead><tr><th>#</th><th>Par</th><th>ρ corregida</th><th>IC 95%</th><th>Categoría</th>
        <th>Fuerza</th><th>Robusta</th><th>Control por tamaño</th><th>Solapamiento</th><th>Alcance temporal</th>
        <th>Hallazgo</th></tr></thead><tbody>${cuerpo}</tbody></table>`
    : '<p class="vacio">Ningún par cumple los filtros elegidos.</p>';
  document.querySelectorAll('#tablaPares tbody tr').forEach(tr => {
    const abrir = () => abrirPar && abrirPar(tr.dataset.par);
    tr.addEventListener('click', abrir);
    tr.addEventListener('keydown', ev => { if (ev.key === 'Enter') abrir(); });
  });
}
document.querySelectorAll('#filtroDir button').forEach(b => b.addEventListener('click', () => {
  filtros.dir = b.dataset.dir;
  document.querySelectorAll('#filtroDir button').forEach(o => o.classList.toggle('activo', o === b));
  renderTabla();
}));
document.querySelectorAll('.chip[data-filtro]').forEach(b => b.addEventListener('click', () => {
  filtros[b.dataset.filtro] = !filtros[b.dataset.filtro];
  b.setAttribute('aria-pressed', filtros[b.dataset.filtro]);
  renderTabla();
}));
document.getElementById('limpiarFiltros').addEventListener('click', () => {
  Object.assign(filtros, { dir: 'todas', sig: false, rob: false, tam: false });
  document.querySelectorAll('#filtroDir button').forEach(o => o.classList.toggle('activo', o.dataset.dir === 'todas'));
  document.querySelectorAll('.chip[data-filtro]').forEach(o => o.setAttribute('aria-pressed', 'false'));
  renderTabla();
});

// ── Mapa de calor ──
let modoMapa = 'corr';
const idsMapa = D.variables.map(v => v.id);
const parMapa = {};
for (const [id, p] of Object.entries(D.pares)) { parMapa[p.x + '|' + p.y] = id; parMapa[p.y + '|' + p.x] = id; }
const hexRgb = h => { h = h.trim().replace('#', ''); return [0, 2, 4].map(i => parseInt(h.slice(i, i + 2), 16)); };
function colorDiv(v) {
  const css = getComputedStyle(document.documentElement);
  const [neg, mid, pos] = ['--div-neg', '--div-mid', '--div-pos'].map(k => hexRgb(css.getPropertyValue(k)));
  const t = Math.max(-1, Math.min(1, v)), fin = t < 0 ? neg : pos, a = Math.abs(t);
  return `rgb(${mid.map((c, i) => Math.round(c + (fin[i] - c) * a)).join(',')})`;
}
function renderMapa(cont = document.getElementById('mapaCalor'), leyenda = document.getElementById('leyendaMapa')) {
  const n = idsMapa.length;
  const maxCar = Math.max(...idsMapa.map(id => nombre[id].length));
  const LW = Math.min(240, maxCar * 6.2 + 12);
  const celda = Math.max(13, Math.min(34, (940 - LW) / n));
  const LH = Math.min(200, maxCar * 5.2 + 12);
  const extra = Math.min(170, maxCar * 6.2 * 0.6);   // las etiquetas inclinadas se extienden a la derecha
  const W = LW + celda * n + extra, H = LH + celda * n + 8;
  let svg = `<svg viewBox="0 0 ${W} ${H}" style="min-width:${Math.min(W, 520)}px" role="img" aria-label="Mapa de calor de correlaciones">`;
  idsMapa.forEach((id, i) => {
    svg += `<text x="${LW - 6}" y="${LH + celda * (i + 0.5)}" class="lbl-fila">${nombre[id]}</text>`;
    const cx = LW + celda * (i + 0.5);
    svg += `<text transform="translate(${cx} ${LH - 6}) rotate(-55)" class="lbl-col">${nombre[id]}</text>`;
  });
  idsMapa.forEach((a, i) => idsMapa.forEach((b, j) => {
    const x = LW + celda * j, y = LH + celda * i, id = i !== j ? parMapa[a + '|' + b] : null;
    if (!id) { svg += `<rect x="${x}" y="${y}" width="${celda}" height="${celda}" class="celda vacia"/>`; return; }
    const p = D.pares[id], v = modoMapa === 'corr' ? p.corr : p.cruda;
    const fill = v === null ? 'transparent' : colorDiv(v);
    const at = hayFiltros() && !paresVisibles.has(id) ? ' atenuada' : '';
    svg += `<rect x="${x}" y="${y}" width="${celda}" height="${celda}" class="celda par${at}" data-id="${id}" data-a="${a}" data-b="${b}" style="fill:${fill}"/>`;
  }));
  cont.innerHTML = svg + '</svg><div class="tooltip"></div>';
  const el = cont.querySelector('svg'), tip = cont.querySelector('.tooltip');
  el.addEventListener('pointermove', ev => {
    const r = ev.target.closest('.celda.par');
    if (!r) { tip.style.display = 'none'; return; }
    const p = D.pares[r.dataset.id];
    tip.innerHTML = `<b>${nombre[r.dataset.a]} ↔ ${nombre[r.dataset.b]}</b><br>ρ corregida ${fmt(p.corr)} · ρ cruda ${fmt(p.cruda)}<br>`
      + `${p.control ? 'Control (misma métrica)' : p.cat + (p.fuerza ? ' · ' + p.fuerza : '')}${p.robusta ? ' · robusta' : ''}`;
    tip.style.display = 'block';
    const caja = cont.getBoundingClientRect(), rr = r.getBoundingClientRect();
    let left = rr.left - caja.left + cont.scrollLeft + rr.width + 8;
    if (left + tip.offsetWidth > cont.scrollLeft + caja.width) left = rr.left - caja.left + cont.scrollLeft - tip.offsetWidth - 8;
    tip.style.left = Math.max(0, left) + 'px';
    tip.style.top = (rr.top - caja.top) + 'px';
  });
  el.addEventListener('pointerleave', () => { tip.style.display = 'none'; });
  el.addEventListener('click', ev => {
    const r = ev.target.closest('.celda.par');
    if (r && abrirPar) abrirPar(r.dataset.id);
  });
  // leyenda: gradiente de −1 a 1
  const ley = [-1, -0.5, 0, 0.5, 1];
  if (leyenda) leyenda.innerHTML = `<svg viewBox="0 0 320 34" style="max-width:320px">
    <defs><linearGradient id="gradMapa">${ley.map(v => `<stop offset="${(v + 1) / 2}" stop-color="${colorDiv(v)}"/>`).join('')}</linearGradient></defs>
    <rect x="10" y="4" width="300" height="10" rx="2" fill="url(#gradMapa)"/>
    ${ley.map(v => `<text x="${10 + (v + 1) / 2 * 300}" y="18" class="tick">${fmt(v, 1)}</text>`).join('')}</svg>`;
}
document.querySelectorAll('#modoMapa button').forEach(b => b.addEventListener('click', () => {
  modoMapa = b.dataset.modo;
  document.querySelectorAll('#modoMapa button').forEach(o => o.classList.toggle('activo', o === b));
  renderMapa();
}));
const _renderTablaBase = renderTabla;
renderTabla = function () { _renderTablaBase(); renderMapa(); };
renderMapa();
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => renderMapa());

// ── Vista general del cruce ──
const signif = p => p.cat === 'Positiva' || p.cat === 'Negativa';
const nPar = p => `${nombre[p.x]} ↔ ${nombre[p.y]}`;
const replica = p => p.canary === null || p.corr === null || (p.canary >= 0) === (p.corr >= 0);
const visible = id => !hayFiltros() || paresVisibles.has(id);
const tipPar = p => `<b>${nPar(p)}</b><br>ρ corregida ${fmt(p.corr)} [${fmt(p.ic[0])}; ${fmt(p.ic[1])}] · ρ cruda ${fmt(p.cruda)}<br>`
  + `${p.cat}${p.fuerza ? ' · ' + p.fuerza : ''}${p.robusta ? ' · robusta' : ''}${p.hallazgo ? ' · hallazgo' : ''}`;

function interactivo(cont) {   // tooltip con data-tip y clic con data-par, una sola vez por contenedor
  const tip = () => {
    let t = cont.querySelector(':scope > .tooltip');
    if (!t) { t = document.createElement('div'); t.className = 'tooltip'; cont.appendChild(t); }
    return t;
  };
  cont.addEventListener('pointermove', ev => {
    const el = ev.target.closest('[data-tip]'), t = tip();
    if (!el) { t.style.display = 'none'; return; }
    t.innerHTML = el.dataset.tip; t.style.display = 'block';
    const caja = cont.getBoundingClientRect();
    let left = ev.clientX - caja.left + 14;
    if (left + t.offsetWidth > caja.width) left = ev.clientX - caja.left - t.offsetWidth - 14;
    t.style.left = Math.max(0, left) + 'px';
    t.style.top = (ev.clientY - caja.top + 14) + 'px';
  });
  cont.addEventListener('pointerleave', () => { tip().style.display = 'none'; });
  cont.addEventListener('click', ev => {
    const el = ev.target.closest('[data-par]');
    if (el && abrirPar) abrirPar(el.dataset.par);
  });
}

function renderEmbudo(cont = document.getElementById('vEmbudo')) {
  const ev = evaluados.map(([, p]) => p), total = ev.length;
  const pasos = [
    ['Pares evaluados', p => true],
    ['Significativos', p => signif(p)],
    ['+ mismo signo en todos los períodos', p => signif(p) && p.estable],
    ['+ se repiten en canary', p => signif(p) && p.estable && replica(p)],
    ['+ no dependen de ventanas cortas (robustos)', p => p.robusta],
    ['+ resisten el control por tamaño (o no aplica)', p => p.robusta && p.tamano !== 'no pasa'],
    ['+ sin solapamiento de definición', p => p.robusta && p.tamano !== 'no pasa' && !p.solap],
  ];
  const LW = 300, W = 980, fila = 30, H = pasos.length * fila + 6;
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Embudo de filtrado de pares">`;
  pasos.forEach(([txt, f], i) => {
    const n = ev.filter(f).length, w = total ? (W - LW - 120) * n / total : 0, y = i * fila;
    s += `<text x="${LW - 10}" y="${y + fila / 2}" class="cat">${txt}</text>`
      + (n ? `<rect x="${LW}" y="${y + 5}" width="${Math.max(w, 2)}" height="${fila - 10}" rx="3" class="marca"/>` : '')
      + `<text x="${LW + w + 8}" y="${y + fila / 2}" class="val">${n} (${total ? Math.round(100 * n / total) : 0}%)</text>`;
  });
  cont.innerHTML = s + '</svg>';
}

function renderCrudaCorr(cont = document.getElementById('vCrudaCorr')) {
  const W = 520, H = 440, m = { l: 50, r: 14, t: 12, b: 44 };
  const sx = v => m.l + (v + 1) / 2 * (W - m.l - m.r), sy = v => m.t + (1 - v) / 2 * (H - m.t - m.b);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Correlación cruda contra corregida">`
    + `<rect x="${sx(-1)}" y="${sy(0.2)}" width="${sx(1) - sx(-1)}" height="${sy(-0.2) - sy(0.2)}" class="banda"/>`;
  for (const v of [-1, -0.5, 0, 0.5, 1]) {
    s += `<line x1="${sx(v)}" x2="${sx(v)}" y1="${sy(1)}" y2="${sy(-1)}" class="${v ? 'grid' : 'cero'}"/>`
      + `<line x1="${sx(-1)}" x2="${sx(1)}" y1="${sy(v)}" y2="${sy(v)}" class="${v ? 'grid' : 'cero'}"/>`
      + `<text x="${sx(v)}" y="${sy(-1) + 6}" class="tick">${fmt(v, 1)}</text>`
      + `<text x="${m.l - 6}" y="${sy(v)}" class="ticky">${fmt(v, 1)}</text>`;
  }
  s += `<line x1="${sx(-1)}" y1="${sy(-1)}" x2="${sx(1)}" y2="${sy(1)}" class="ref"/>`;
  const orden = [...evaluados].sort((a, b) => signif(a[1]) - signif(b[1]));   // significativos arriba
  for (const [id, p] of orden) {
    if (p.corr === null || p.cruda === null) continue;
    const cls = (signif(p) ? 'pt-sig' : 'pt-ns') + (p.robusta ? ' pt-rob' : '') + (visible(id) ? '' : ' pt-at');
    s += `<circle cx="${sx(p.cruda)}" cy="${sy(p.corr)}" r="${signif(p) ? 4.5 : 3.5}" class="${cls}" data-par="${id}" data-tip="${tipPar(p)}"/>`;
  }
  s += `<text x="${m.l + (W - m.l - m.r) / 2}" y="${H - 8}" class="eje">ρ cruda</text>`
    + `<text transform="translate(14 ${m.t + (H - m.t - m.b) / 2}) rotate(-90)" class="eje">ρ corregida</text></svg>`;
  cont.innerHTML = s;
}

function renderRed(cont = document.getElementById('vRed')) {
  const W = 520, H = 460, cx = W / 2, cy = H / 2, n = idsMapa.length;
  const R = Math.min(150, 60 + n * 3);
  const pos = Object.fromEntries(idsMapa.map((id, i) => {
    const a = -Math.PI / 2 + 2 * Math.PI * i / n;
    return [id, [cx + R * Math.cos(a), cy + R * Math.sin(a), a]];
  }));
  const aristas = evaluados.filter(([id, p]) => signif(p) && visible(id)).sort((a, b) => Math.abs(a[1].corr) - Math.abs(b[1].corr));
  const grado = {};
  aristas.forEach(([, p]) => { grado[p.x] = (grado[p.x] || 0) + 1; grado[p.y] = (grado[p.y] || 0) + 1; });
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Red de relaciones significativas">`;
  for (const [id, p] of aristas) {
    const [x1, y1] = pos[p.x], [x2, y2] = pos[p.y];
    s += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="arista" style="stroke:${colorDiv(p.corr)};stroke-width:${1.5 + 5 * Math.abs(p.corr)}" data-par="${id}" data-tip="${tipPar(p)}"/>`;
  }
  for (const id of idsMapa) {
    const [x, y, a] = pos[id], der = Math.cos(a) >= 0;
    const lx = x + 9 * Math.cos(a), ly = y + 9 * Math.sin(a);
    s += `<circle cx="${x}" cy="${y}" r="${grado[id] ? 5 : 3.5}" class="nodo${grado[id] ? '' : ' solo'}"><title>${nombre[id]}: ${grado[id] || 0} relaciones</title></circle>`
      + `<text x="${lx}" y="${ly}" class="lbl-nodo${grado[id] ? '' : ' solo'}" style="text-anchor:${der ? 'start' : 'end'}">${nombre[id]}</text>`;
  }
  s += aristas.length ? '' : `<text x="${cx}" y="${cy}" class="eje">Ningún par significativo con estos filtros</text>`;
  cont.innerHTML = s + '</svg>';
}

const anchoEtiquetas = filas => Math.min(420, Math.max(200, ...filas.map(([, p]) => nPar(p).length * 6.6 + 24)));
function filasSignif() {
  return evaluados.filter(([id, p]) => signif(p) && visible(id));
}

function renderForest(cont = document.getElementById('vForest')) {
  const filas = filasSignif().sort((a, b) => b[1].corr - a[1].corr);
  if (!filas.length) { cont.innerHTML = '<p class="vacio">Ningún par significativo con estos filtros.</p>'; return; }
  const LW = anchoEtiquetas(filas), W = 980, fila = 24, top = 26, H = top + filas.length * fila + 30;
  const sx = v => LW + (v + 1) / 2 * (W - LW - 60);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Intervalos de confianza de las relaciones significativas">`
    + `<rect x="${sx(-0.2)}" y="${top - 6}" width="${sx(0.2) - sx(-0.2)}" height="${filas.length * fila + 6}" class="banda"/>`;
  for (const v of [-1, -0.5, 0, 0.5, 1]) s += `<line x1="${sx(v)}" x2="${sx(v)}" y1="${top - 6}" y2="${top + filas.length * fila}" class="${v ? 'grid' : 'cero'}"/>`
    + `<text x="${sx(v)}" y="${top + filas.length * fila + 6}" class="tick">${fmt(v, 1)}</text>`;
  s += `<text x="${sx(0)}" y="${top - 12}" class="ref-txt" style="text-anchor:middle">zona despreciable (−0,2 a 0,2)</text>`;
  filas.forEach(([id, p], i) => {
    const y = top + i * fila + fila / 2;
    s += `<g data-par="${id}" data-tip="${tipPar(p)}"><rect x="0" y="${y - fila / 2}" width="${W}" height="${fila}" class="fila-hit"/>`
      + `<text x="${LW - 10}" y="${y}" class="cat">${nPar(p)}</text>`
      + `<line x1="${sx(p.ic[0])}" x2="${sx(p.ic[1])}" y1="${y}" y2="${y}" class="ic-linea"/>`
      + `<circle cx="${sx(p.corr)}" cy="${y}" r="5" class="pt-forest${p.robusta ? '' : ' hueca'}"/>`
      + `<text x="${sx(p.ic[1]) + 8}" y="${y}" class="val">${fmt(p.corr)}</text></g>`;
  });
  cont.innerHTML = s + '</svg>';
}

function renderEstab(cont = document.getElementById('vEstab')) {
  const filas = filasSignif().sort((a, b) => Math.abs(b[1].corr) - Math.abs(a[1].corr));
  if (!filas.length) { cont.innerHTML = '<p class="vacio">Ningún par significativo con estos filtros.</p>'; return; }
  const cols = ['Toda la historia', '2016–19', '2020–22', '2023–24', '2025–26'];
  const LW = anchoEtiquetas(filas), cw = 120, fila = 26, top = 30, W = LW + cw * cols.length + 10, H = top + filas.length * fila + 4;
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Estabilidad por período de las relaciones significativas">`;
  cols.forEach((c, j) => { s += `<text x="${LW + cw * j + cw / 2}" y="${top - 12}" class="tick" style="font-weight:600">${c}</text>`; });
  filas.forEach(([id, p], i) => {
    const y = top + i * fila;
    s += `<g data-par="${id}" data-tip="${tipPar(p)}"><rect x="0" y="${y}" width="${W}" height="${fila}" class="fila-hit"/>`
      + `<text x="${LW - 10}" y="${y + fila / 2}" class="cat">${nPar(p)}</text>`;
    const celdas = [[p.corr, p.corr >= 0 ? '+' : '-'], ...p.per.map((v, k) => [v, p.est[k]])];
    celdas.forEach(([v, e], j) => {
      const fill = e === '+' ? colorDiv(0.75) : e === '-' ? colorDiv(-0.75) : e === '0' ? colorDiv(0) : 'transparent';
      s += `<rect x="${LW + cw * j + 2}" y="${y + 2}" width="${cw - 4}" height="${fila - 4}" rx="3" style="fill:${fill}" class="celda-est"/>`
        + `<text x="${LW + cw * j + cw / 2}" y="${y + fila / 2}" class="txt-celda">${v === null ? '—' : fmt(v)}</text>`;
    });
    s += '</g>';
  });
  cont.innerHTML = s + '</svg>';
}

function renderVista() {
  renderEmbudo(); renderCrudaCorr(); renderRed(); renderForest(); renderEstab();
}
['vCrudaCorr', 'vRed', 'vForest', 'vEstab'].forEach(id => interactivo(document.getElementById(id)));
const _renderTablaMapa = renderTabla;
renderTabla = function () { _renderTablaMapa(); renderVista(); };
renderTabla();   // dibuja la tabla, el mapa de calor y la vista general
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => renderVista());
"""

SCRIPT = r"""
const parDe = {};   // "x|y" -> par_id, en los dos órdenes
for (const [id, p] of Object.entries(D.pares)) { parDe[p.x + '|' + p.y] = id; parDe[p.y + '|' + p.x] = id; }
const selX = document.getElementById('selX'), selY = document.getElementById('selY');
const fmtVal = v => v === null || v === undefined ? '—'
  : (Math.abs(v) >= 1000 ? v.toLocaleString('es-AR', { maximumFractionDigits: 0 })
     : v.toLocaleString('es-AR', { maximumSignificantDigits: 4 }));

function opciones(sel, ids, actual) {
  sel.innerHTML = ids.map(id => `<option value="${id}">${nombre[id]}</option>`).join('');
  if (actual && ids.includes(actual)) sel.value = actual;
}
function compañeras(x) {
  return D.variables.map(v => v.id).filter(y => y !== x && parDe[x + '|' + y] && paresVisibles.has(parDe[x + '|' + y]));
}

function niceTicks(min, max, n = 5) {
  if (min === max) { min -= 1; max += 1; }
  const paso0 = (max - min) / n, mag = Math.pow(10, Math.floor(Math.log10(paso0)));
  const paso = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => s >= paso0);
  const ini = Math.floor(min / paso) * paso, fin = Math.ceil(max / paso) * paso;
  const t = []; for (let v = ini; v <= fin + paso / 2; v += paso) t.push(+v.toFixed(10));
  return t;
}

function dispersion(contenedor, pts, etiqX, etiqY, centrado) {
  if (pts.length < 2) { contenedor.innerHTML = '<p class="vacio">No hay suficientes releases con dato en el período elegido.</p>'; return; }
  const W = 480, H = 340, m = { l: 58, r: 14, t: 12, b: 46 };
  const xs = pts.map(p => p.x), ys = pts.map(p => p.y);
  const tx = niceTicks(Math.min(...xs), Math.max(...xs)), ty = niceTicks(Math.min(...ys), Math.max(...ys));
  const x0 = tx[0], x1 = tx[tx.length - 1], y0 = ty[0], y1 = ty[ty.length - 1];
  const sx = v => m.l + (v - x0) / (x1 - x0) * (W - m.l - m.r);
  const sy = v => H - m.b - (v - y0) / (y1 - y0) * (H - m.t - m.b);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Dispersión ${etiqY} contra ${etiqX}">`;
  for (const v of tx) s += `<line x1="${sx(v)}" x2="${sx(v)}" y1="${m.t}" y2="${H - m.b}" class="grid"/>`
    + `<text x="${sx(v)}" y="${H - m.b + 6}" class="tick">${fmtVal(v)}</text>`;
  for (const v of ty) s += `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(v)}" y2="${sy(v)}" class="grid"/>`
    + `<text x="${m.l - 6}" y="${sy(v)}" class="ticky">${fmtVal(v)}</text>`;
  if (centrado) {
    if (x0 < 0 && x1 > 0) s += `<line x1="${sx(0)}" x2="${sx(0)}" y1="${m.t}" y2="${H - m.b}" class="cero"/>`;
    if (y0 < 0 && y1 > 0) s += `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(0)}" y2="${sy(0)}" class="cero"/>`;
  }
  pts.forEach((p, i) => { s += `<circle cx="${sx(p.x)}" cy="${sy(p.y)}" r="3.5" class="punto${p.rel && p.rel[5] ? ' bp' : ''}" data-i="${i}"/>`; });
  // línea de tendencia (mínimos cuadrados sobre lo que se grafica)
  const n = pts.length, mx = xs.reduce((a, b) => a + b, 0) / n, my = ys.reduce((a, b) => a + b, 0) / n;
  let sxy = 0, sxx = 0; for (let i = 0; i < n; i++) { sxy += (xs[i] - mx) * (ys[i] - my); sxx += (xs[i] - mx) ** 2; }
  if (sxx > 0) {
    const b = sxy / sxx, a = my - b * mx, xa = Math.min(...xs), xb = Math.max(...xs);
    const clip = v => Math.max(y0, Math.min(y1, v));
    s += `<line x1="${sx(xa)}" y1="${sy(clip(a + b * xa))}" x2="${sx(xb)}" y2="${sy(clip(a + b * xb))}" class="tendencia"/>`;
  }
  s += `<text x="${m.l + (W - m.l - m.r) / 2}" y="${H - 8}" class="eje">${etiqX}</text>`
    + `<text transform="translate(14 ${m.t + (H - m.t - m.b) / 2}) rotate(-90)" class="eje">${etiqY}</text></svg>`;
  contenedor.innerHTML = s + '<div class="tooltip"></div>';
  const svg = contenedor.querySelector('svg'), tip = contenedor.querySelector('.tooltip');
  const circulos = [...svg.querySelectorAll('.punto')];
  let activo = null;
  svg.addEventListener('pointermove', ev => {
    const r = svg.getBoundingClientRect(), k = W / r.width;
    const px = (ev.clientX - r.left) * k, py = (ev.clientY - r.top) * k;
    let mejor = null, dmin = 14 * k;
    pts.forEach((p, i) => { const d = Math.hypot(sx(p.x) - px, sy(p.y) - py); if (d < dmin) { dmin = d; mejor = i; } });
    if (activo !== null) circulos[activo].classList.remove('activo');
    activo = mejor;
    if (mejor === null) { tip.style.display = 'none'; return; }
    circulos[mejor].classList.add('activo');
    const p = pts[mejor];
    const dur = p.rel[3] === null ? '—' : p.rel[3] < 1 ? `${Math.max(1, Math.round(p.rel[3] * 24))} h` : `${fmt(p.rel[3], 1)} días`;
    tip.innerHTML = `<b>${p.rel[0]}</b> · ${p.rel[1]} · ventana de ${dur}<br>${etiqX}: ${fmtVal(p.x)}<br>${etiqY}: ${fmtVal(p.y)}`;
    tip.style.display = 'block';
    const cx = sx(p.x) / k, cy = sy(p.y) / k, ancho = tip.offsetWidth;
    tip.style.left = Math.min(Math.max(cx - ancho / 2, 0), r.width - ancho) + 'px';
    tip.style.top = (cy - tip.offsetHeight - 10 < 0 ? cy + 12 : cy - tip.offsetHeight - 10) + 'px';
  });
  svg.addEventListener('pointerleave', () => {
    if (activo !== null) circulos[activo].classList.remove('activo');
    activo = null; tip.style.display = 'none';
  });
}

function barrasPeriodo(cont, p) {
  const W = 980, H = 300, m = { l: 56, r: 16, t: 20, b: 40 };
  const items = [
    ...['2016–19', '2020–22', '2023–24', '2025–26'].map((et, i) => ({ et, v: p.per[i], ic: p.icp[i], est: p.est[i], tipo: 'per' })),
    { et: 'Canary', v: p.canary, ic: null, est: '', tipo: 'can' },
  ];
  const vals = [0, p.corr, ...items.flatMap(o => [o.v, ...(o.ic || [])])].filter(v => v !== null && v !== undefined);
  const lo = Math.min(-0.2, ...vals), hi = Math.max(0.2, ...vals);
  const ty = niceTicks(lo, hi, 5), y0 = ty[0], y1 = ty[ty.length - 1];
  const sy = v => m.t + (y1 - v) / (y1 - y0) * (H - m.t - m.b);
  const banda = (W - m.l - m.r) / items.length, ancho = Math.min(64, banda * 0.5);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Correlación corregida por período y en canary">`;
  for (const v of ty) s += `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(v)}" y2="${sy(v)}" class="${v === 0 ? 'cero' : 'grid'}"/>`
    + `<text x="${m.l - 6}" y="${sy(v)}" class="ticky">${fmt(v, 1)}</text>`;
  items.forEach((o, i) => {
    const cx = m.l + banda * (i + 0.5), x = cx - ancho / 2;
    const clic = o.tipo === 'per';
    if (clic) {
      const cls = 'per-grupo' + (periodoSel === i ? ' activo' : periodoSel !== null ? ' atenuado' : '');
      s += `<g class="${cls}" data-i="${i}" tabindex="0" role="button" aria-pressed="${periodoSel === i}" `
        + `aria-label="Ver solo ${o.et}"><rect x="${m.l + banda * i}" y="${m.t}" width="${banda}" height="${H - m.t - m.b + 22}" rx="6" class="hit"/>`;
    }
    s += `<text x="${cx}" y="${H - m.b + 10}" class="tick">${o.et}</text>`;
    if (o.v === null || o.v === undefined) {
      s += `<text x="${cx}" y="${sy(0) - 8}" class="val-barra">sin dato</text>` + (clic ? '</g>' : ''); return;
    }
    const ya = sy(Math.max(o.v, 0)), yb = sy(Math.min(o.v, 0)), h = Math.max(yb - ya, 1), r = Math.min(4, h / 2);
    // barra con el extremo de dato redondeado y la base recta sobre el 0
    const d = o.v >= 0
      ? `M${x},${yb} V${ya + r} Q${x},${ya} ${x + r},${ya} H${x + ancho - r} Q${x + ancho},${ya} ${x + ancho},${ya + r} V${yb} Z`
      : `M${x},${ya} V${yb - r} Q${x},${yb} ${x + r},${yb} H${x + ancho - r} Q${x + ancho},${yb} ${x + ancho},${yb - r} V${ya} Z`;
    const clase = o.tipo === 'can' ? 'barra-can' : 'barra-per' + (o.est === '0' ? ' debil' : '');
    const icTxt = o.ic ? ` · IC [${fmt(o.ic[0])}; ${fmt(o.ic[1])}]` : '';
    s += `<path d="${d}" class="${clase}"><title>${o.et}: ρ = ${fmt(o.v)}${icTxt}</title></path>`;
    if (o.ic) {
      const t1 = sy(o.ic[1]), t0 = sy(o.ic[0]);
      s += `<line x1="${cx}" x2="${cx}" y1="${t1}" y2="${t0}" class="bigote"/>`
        + `<line x1="${cx - 7}" x2="${cx + 7}" y1="${t1}" y2="${t1}" class="bigote"/>`
        + `<line x1="${cx - 7}" x2="${cx + 7}" y1="${t0}" y2="${t0}" class="bigote"/>`;
    }
    s += `<text x="${cx + ancho / 2 + 6}" y="${o.v >= 0 ? ya + 4 : yb - 4}" class="val-barra" style="text-anchor:start">${fmt(o.v)}</text>`;
    if (clic) s += '</g>';
  });
  if (p.corr !== null) s += `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(p.corr)}" y2="${sy(p.corr)}" class="ref"/>`
    + `<text x="${W - m.r}" y="${sy(p.corr) - 5}" class="ref-txt" style="text-anchor:end">toda la historia: ${fmt(p.corr)}</text>`;
  cont.innerHTML = s + '</svg>';
  cont.querySelectorAll('.per-grupo').forEach(g => {
    const elegir = periodoPara(cont);
    if (!elegir) return;
    g.addEventListener('click', () => elegir(+g.dataset.i));
    g.addEventListener('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); elegir(+g.dataset.i); } });
  });
}

let modoTiempo = 'original';
let periodoSel = null;   // índice de ETAPAS_T o null = toda la historia
const ETAPA_ID = ['2016-2019', '2020-2022', '2023-2024', '2025-2026'];
function elegirPeriodo(i) { periodoSel = (i === null || periodoSel === i) ? null : i; mostrar(); }
// a quién le toca elegir el período al hacer clic en una franja: el explorador del reporte, el análisis
// particular de un informe (elegirPeriodoLocal, si existe) o nadie (gráficos insertados en el texto)
function periodoPara(cont) {
  const det = cont.closest('.detalle-local');
  if (det && cont.closest('.graficos-par') && window.elegirPeriodoLocal) return i => window.elegirPeriodoLocal(det, i);
  return cont.closest('.inserto') ? null : elegirPeriodo;
}
const ETAPAS_T = [[2016, 2020, '2016–19'], [2020, 2023, '2020–22'], [2023, 2025, '2023–24'], [2025, 2027, '2025–26']];
const fechaMs = n => Date.parse(D.releases[n][4] + 'T00:00:00Z');

function temporal(cont, x, y, p, inv, leyenda = document.getElementById('leyendaTiempo')) {
  const W = 980, PH = 140, GAP = 40, m = { l: 66, r: 16, t: 30, b: 34 };
  const H = m.t + PH * 2 + GAP + m.b;
  let sX, sY;
  if (modoTiempo === 'original') {
    const desde = obj => Object.entries(obj).map(([n, v]) => ({ n: +n, v })).filter(o => o.v !== null && D.releases[o.n]);
    sX = desde(D.serie[x]); sY = desde(D.serie[y]);
  } else {
    const xa = inv ? p.ya : p.xa, ya = inv ? p.xa : p.ya;
    sX = p.p.map((n, i) => ({ n, v: xa[i] })).filter(o => o.v !== null);
    sY = p.p.map((n, i) => ({ n, v: ya[i] })).filter(o => o.v !== null);
  }
  for (const s of [sX, sY]) { s.forEach(o => o.t = fechaMs(o.n)); s.sort((a, b) => a.t - b.t); }
  let todos = [...sX, ...sY].map(o => o.t);
  let t0 = Math.min(...todos), t1 = Math.max(...todos);
  if (periodoSel !== null) {
    const [a, b] = ETAPAS_T[periodoSel], ini = Date.UTC(a, 0, 1), fin = Date.UTC(b, 0, 1);
    sX = sX.filter(o => o.t >= ini && o.t < fin); sY = sY.filter(o => o.t >= ini && o.t < fin);
    t0 = Math.max(ini, t0); t1 = Math.min(fin, t1);
    if (!sX.length && !sY.length) {
      cont.innerHTML = '<p class="vacio">Este par no tiene datos en el período elegido.</p>';
      if (leyenda) leyenda.innerHTML = ''; return;
    }
  }
  const sx = t => m.l + (t - t0) / ((t1 - t0) || 1) * (W - m.l - m.r);
  const sufijo = modoTiempo === 'ajustado' ? ' (ajustado)' : '';
  const paneles = [[sX, nombre[x] + sufijo, 'x'], [sY, nombre[y] + sufijo, 'y']];
  let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Evolución de ${nombre[x]} y ${nombre[y]} en el tiempo">`;
  // franjas de períodos
  ETAPAS_T.forEach(([a, b, et], i) => {
    const xa = Math.max(m.l, sx(Date.UTC(a, 0, 1))), xb = Math.min(W - m.r, sx(Date.UTC(b, 0, 1)));
    if (xb <= xa) return;
    const clase = periodoSel === i ? 'banda-sel' : (i % 2 === 0 ? 'banda' : '');
    if (clase) svg += `<rect x="${xa}" y="${m.t - 14}" width="${xb - xa}" height="${PH * 2 + GAP + 14}" class="${clase}"/>`;
    svg += `<text x="${(xa + xb) / 2}" y="${m.t - 18}" class="etapa">${et}${periodoSel === i ? ' · clic para volver' : ''}</text>`;
  });
  const escalas = [];
  paneles.forEach(([serie, titulo, cual], k) => {
    const top = m.t + k * (PH + GAP), vals = serie.map(o => o.v);
    const ty = niceTicks(Math.min(...vals), Math.max(...vals), 4), y0 = ty[0], y1 = ty[ty.length - 1];
    const sy = v => top + PH - (v - y0) / ((y1 - y0) || 1) * PH;
    escalas.push(sy);
    for (const v of ty) svg += `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(v)}" y2="${sy(v)}" class="grid"/>`
      + `<text x="${m.l - 6}" y="${sy(v)}" class="ticky">${fmtVal(v)}</text>`;
    if (modoTiempo === 'ajustado' && y0 < 0 && y1 > 0) svg += `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(0)}" y2="${sy(0)}" class="cero"/>`;
    svg += `<text x="${m.l}" y="${top - 4}" class="titulo-panel">${titulo}</text>`;
    svg += `<path d="${serie.map((o, i) => (i ? 'L' : 'M') + sx(o.t).toFixed(1) + ',' + sy(o.v).toFixed(1)).join('')}" class="linea-${cual}"/>`;
    for (const o of serie) if (D.releases[o.n][5]) svg += `<line x1="${sx(o.t)}" x2="${sx(o.t)}" y1="${top + PH + 2}" y2="${top + PH + 9}" class="rug"/>`;
  });
  const yb = m.t + PH * 2 + GAP;
  const trimestral = (t1 - t0) < 3.5 * 365.25 * 864e5, MESES = ['ene', 'abr', 'jul', 'oct'];
  for (let a = new Date(t0).getUTCFullYear(); a <= new Date(t1).getUTCFullYear() + 1; a++) {
    for (const q of trimestral ? [0, 1, 2, 3] : [0]) {
      const t = Date.UTC(a, q * 3, 1); if (t < t0 || t > t1) continue;
      svg += `<text x="${sx(t)}" y="${yb + 8}" class="tick">${q === 0 ? a : MESES[q]}</text>`;
      if (trimestral) svg += `<line x1="${sx(t)}" x2="${sx(t)}" y1="${m.t}" y2="${yb}" class="grid"/>`;
    }
  }
  svg += `<line class="guia" y1="${m.t}" y2="${yb}" x1="-10" x2="-10"/>`
    + `<circle class="marca-x" r="4.5" cx="-10" cy="-10"/><circle class="marca-y" r="4.5" cx="-10" cy="-10"/></svg>`;
  cont.innerHTML = svg + '<div class="tooltip"></div>';
  if (leyenda) leyenda.innerHTML =
    `<span><i></i>${nombre[x]}</span><span><i class="y"></i>${nombre[y]}</span><span><i class="rug"></i>backport (parche de una versión mayor anterior)</span>`;

  const el = cont.querySelector('svg'), tip = cont.querySelector('.tooltip');
  const guia = el.querySelector('.guia'), mx = el.querySelector('.marca-x'), my = el.querySelector('.marca-y');
  const porN = [new Map(sX.map(o => [o.n, o])), new Map(sY.map(o => [o.n, o]))];
  const ts = [...new Map([...sX, ...sY].map(o => [o.n, o.t])).entries()].sort((a, b) => a[1] - b[1]);
  el.addEventListener('pointermove', ev => {
    const r = el.getBoundingClientRect(), k = W / r.width, px = (ev.clientX - r.left) * k;
    if (px < m.l || px > W - m.r) { tip.style.display = 'none'; guia.setAttribute('x1', -10); guia.setAttribute('x2', -10); return; }
    let mejor = ts[0], dmin = Infinity;
    for (const e of ts) { const d = Math.abs(sx(e[1]) - px); if (d < dmin) { dmin = d; mejor = e; } }
    const [n, t] = mejor, xpos = sx(t);
    guia.setAttribute('x1', xpos); guia.setAttribute('x2', xpos);
    [mx, my].forEach((c, i) => {
      const o = porN[i].get(n);
      if (o) { c.setAttribute('cx', xpos); c.setAttribute('cy', escalas[i](o.v)); } else { c.setAttribute('cx', -10); }
    });
    const rel = D.releases[n], vx = porN[0].get(n), vy = porN[1].get(n);
    const dur = rel[3] === null ? '—' : rel[3] < 1 ? `${Math.max(1, Math.round(rel[3] * 24))} h` : `${fmt(rel[3], 1)} días`;
    tip.innerHTML = `<b>${rel[0]}</b> · ${rel[4]} · ventana de ${dur}<br>`
      + `${nombre[x]}${sufijo}: ${vx ? fmtVal(vx.v) : '—'}<br>${nombre[y]}${sufijo}: ${vy ? fmtVal(vy.v) : '—'}`;
    tip.style.display = 'block';
    const cx = xpos / k, ancho = tip.offsetWidth;
    tip.style.left = Math.min(Math.max(cx + 12, 0), r.width - ancho) + 'px';
    if (cx + 12 + ancho > r.width) tip.style.left = Math.max(cx - ancho - 12, 0) + 'px';
    tip.style.top = (m.t / k) + 'px';
  });
  el.addEventListener('pointerleave', () => {
    tip.style.display = 'none'; guia.setAttribute('x1', -10); guia.setAttribute('x2', -10);
    mx.setAttribute('cx', -10); my.setAttribute('cx', -10);
  });
  // clic en una franja: ver solo ese período (o volver a toda la historia)
  el.style.cursor = 'pointer';
  el.addEventListener('click', ev => {
    const elegir = periodoPara(cont);
    if (!elegir) return;
    const r = el.getBoundingClientRect(), px = (ev.clientX - r.left) * W / r.width;
    if (px < m.l || px > W - m.r) return;
    const t = t0 + (px - m.l) / (W - m.l - m.r) * (t1 - t0), anio = new Date(t).getUTCFullYear();
    const i = ETAPAS_T.findIndex(([a, b]) => anio >= a && anio < b);
    if (i >= 0) elegir(i);
  });
}

document.querySelectorAll('#modoTiempo button').forEach(b => b.addEventListener('click', () => {
  modoTiempo = b.dataset.modo;
  document.querySelectorAll('#modoTiempo button').forEach(o => o.classList.toggle('activo', o === b));
  mostrar();
}));


// ── Sensibilidad del par: la ρ con cada control ──
function sensibilidad(cont, p) {
  const items = [
    ['ρ cruda', p.cruda, null, ''],
    ['Corregida (tiempo lineal)', p.lineal, null, ''],
    ['ρ corregida', p.corr, p.ic, 'principal'],
    ['Sin ventanas de < 1 día', p.sincortas, null, ''],
    ['Con tendencia local', p.local, null, ''],
    ['Con control por tamaño', p.rtam, null, ''],
    ['Canary', p.canary, null, ''],
  ];
  const W = 480, LW = 170, fila = 30, top = 10, H = top + items.length * fila + 30;
  const sx = v => LW + (v + 1) / 2 * (W - LW - 44);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Correlación del par según cada control">`;
  for (const v of [-1, -0.5, 0, 0.5, 1]) s += `<line x1="${sx(v)}" x2="${sx(v)}" y1="${top}" y2="${top + items.length * fila}" class="${v ? 'grid' : 'cero'}"/>`
    + `<text x="${sx(v)}" y="${top + items.length * fila + 6}" class="tick">${fmt(v, 1)}</text>`;
  for (const v of [-0.1, 0.1]) s += `<line x1="${sx(v)}" x2="${sx(v)}" y1="${top}" y2="${top + items.length * fila}" class="umbral"/>`;
  items.forEach(([txt, v, ic, cls], i) => {
    const y = top + i * fila + fila / 2;
    s += `<text x="${LW - 10}" y="${y}" class="cat"${cls ? ' style="font-weight:600"' : ''}>${txt}</text>`;
    if (v === null || v === undefined) { s += `<text x="${sx(0) + 8}" y="${y}" class="val" style="fill:var(--tenue)">no aplica</text>`; return; }
    if (ic) s += `<line x1="${sx(ic[0])}" x2="${sx(ic[1])}" y1="${y}" y2="${y}" class="ic-linea"/>`;
    s += `<circle cx="${sx(v)}" cy="${y}" r="${cls ? 6 : 4.5}" class="${cls ? 'pt-forest' : 'pt-sens'}"/>`
      + `<text x="${sx(v) + (v >= 0 ? 10 : -10)}" y="${y}" class="val" style="text-anchor:${v >= 0 ? 'start' : 'end'}">${fmt(v)}</text>`;
  });
  cont.innerHTML = s + '</svg>';
}

// ── Correlación móvil de los valores ajustados ──
const VENTANA_MOVIL = 41;
function movil(cont, p, inv) {
  const xa = inv ? p.ya : p.xa, ya = inv ? p.xa : p.ya;
  const pts = p.p.map((n, i) => ({ n, t: fechaMs(n), x: xa[i], y: ya[i] }))
    .filter(o => o.x !== null && o.y !== null).sort((a, b) => a.t - b.t);
  const mitad = Math.floor(VENTANA_MOVIL / 2), serie = [];
  for (let i = 0; i < pts.length; i++) {
    const v = pts.slice(Math.max(0, i - mitad), i + mitad + 1);
    if (v.length < 21) continue;
    const mx = v.reduce((a, o) => a + o.x, 0) / v.length, my = v.reduce((a, o) => a + o.y, 0) / v.length;
    let sxy = 0, sxx = 0, syy = 0;
    for (const o of v) { sxy += (o.x - mx) * (o.y - my); sxx += (o.x - mx) ** 2; syy += (o.y - my) ** 2; }
    if (sxx > 0 && syy > 0) serie.push({ t: pts[i].t, n: pts[i].n, r: sxy / Math.sqrt(sxx * syy) });
  }
  if (serie.length < 2) { cont.innerHTML = '<p class="vacio">No hay releases suficientes para la correlación móvil.</p>'; return; }
  const W = 480, H = 270, m = { l: 44, r: 12, t: 22, b: 30 };
  const t0 = serie[0].t, t1 = serie[serie.length - 1].t;
  const sx = t => m.l + (t - t0) / ((t1 - t0) || 1) * (W - m.l - m.r), sy = v => m.t + (1 - v) / 2 * (H - m.t - m.b);
  let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Correlación móvil del par">`;
  ETAPAS_T.forEach(([a, b, et], i) => {
    const xa2 = Math.max(m.l, sx(Date.UTC(a, 0, 1))), xb = Math.min(W - m.r, sx(Date.UTC(b, 0, 1)));
    if (xb <= xa2) return;
    const clase = periodoSel === i ? 'banda-sel' : (i % 2 === 0 ? 'banda' : '');
    if (clase) s += `<rect x="${xa2}" y="${m.t}" width="${xb - xa2}" height="${H - m.t - m.b}" class="${clase}"/>`;
    s += `<text x="${(xa2 + xb) / 2}" y="${m.t - 8}" class="etapa">${et}</text>`;
  });
  for (const v of [-1, -0.5, 0, 0.5, 1]) s += `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(v)}" y2="${sy(v)}" class="${v ? 'grid' : 'cero'}"/>`
    + `<text x="${m.l - 6}" y="${sy(v)}" class="ticky">${fmt(v, 1)}</text>`;
  if (p.corr !== null) s += `<line x1="${m.l}" x2="${W - m.r}" y1="${sy(p.corr)}" y2="${sy(p.corr)}" class="ref"/>`;
  for (let a = new Date(t0).getUTCFullYear() + 1; a <= new Date(t1).getUTCFullYear(); a++) {
    const t = Date.UTC(a, 0, 1); if (t > t1) break;
    s += `<text x="${sx(t)}" y="${H - m.b + 6}" class="tick">${String(a).slice(2)}</text>`;
  }
  s += `<path d="${serie.map((o, i) => (i ? 'L' : 'M') + sx(o.t).toFixed(1) + ',' + sy(o.r).toFixed(1)).join('')}" class="linea-x"/>`;
  s += `<line class="guia" y1="${m.t}" y2="${H - m.b}" x1="-10" x2="-10"/><circle class="marca-x" r="4" cx="-10" cy="-10"/>`;
  cont.innerHTML = s + '</svg><div class="tooltip"></div>';
  const el = cont.querySelector('svg'), tip = cont.querySelector('.tooltip'), guia = el.querySelector('.guia'), mk = el.querySelector('.marca-x');
  el.addEventListener('pointermove', ev => {
    const r = el.getBoundingClientRect(), k = W / r.width, px = (ev.clientX - r.left) * k;
    let mejor = serie[0], d = Infinity;
    for (const o of serie) { const dd = Math.abs(sx(o.t) - px); if (dd < d) { d = dd; mejor = o; } }
    guia.setAttribute('x1', sx(mejor.t)); guia.setAttribute('x2', sx(mejor.t));
    mk.setAttribute('cx', sx(mejor.t)); mk.setAttribute('cy', sy(mejor.r));
    const rel = D.releases[mejor.n];
    tip.innerHTML = `<b>${rel[0]}</b> · ${rel[4]}<br>ρ en ${VENTANA_MOVIL} releases alrededor: ${fmt(mejor.r)}`;
    tip.style.display = 'block';
    const cx = sx(mejor.t) / k, ancho = tip.offsetWidth;
    tip.style.left = (cx + 12 + ancho > r.width ? cx - ancho - 12 : cx + 12) + 'px';
    tip.style.top = '0px';
  });
  el.addEventListener('pointerleave', () => { tip.style.display = 'none'; guia.setAttribute('x1', -10); guia.setAttribute('x2', -10); mk.setAttribute('cx', -10); });
}

function mostrar() {
  const x = selX.value, y = selY.value, id = parDe[x + '|' + y];
  if (!id) return;
  const p = D.pares[id], inv = p.x !== x;   // el usuario eligió el orden inverso
  const nx = nombre[x], ny = nombre[y];
  const xa = inv ? p.ya : p.xa, ya = inv ? p.xa : p.ya;
  const ajust = p.p.map((n, i) => ({ x: xa[i], y: ya[i], rel: D.releases[n] }));
  const orig = p.p.map(n => ({ x: D.serie[x][n], y: D.serie[y][n], rel: D.releases[n] }))
    .filter(q => q.x !== undefined && q.y !== undefined && q.x !== null && q.y !== null);
  const enPeriodo = q => periodoSel === null || q.rel[2] === ETAPA_ID[periodoSel];
  const ajustF = ajust.filter(enPeriodo), origF = orig.filter(enPeriodo);
  const banner = document.getElementById('filtroPeriodo');
  if (periodoSel === null) { banner.classList.remove('visible'); banner.innerHTML = ''; }
  else {
    const et = ETAPAS_T[periodoSel][2];
    banner.innerHTML = `<span>Mostrando solo <b>${et}</b>: ${ajustF.length} releases con dato en las dos variables ·
      ρ corregida del período: <b>${fmt(p.per[periodoSel])}</b></span>
      <button type="button" id="verTodo">Ver toda la historia</button>
      <span class="aclaracion">En las dispersiones, los valores ajustados son los de toda la historia; la ρ del período se calcula
      corrigiendo dentro del período, así que puede no coincidir exactamente con la nube.</span>`;
    banner.classList.add('visible');
    document.getElementById('verTodo').addEventListener('click', () => elegirPeriodo(null));
  }
  const si = b => b ? 'sí' : 'no';
  document.getElementById('ficha').innerHTML = `
    <h3>${nx} ↔ ${ny}</h3>
    <span class="etiqueta">${p.cat}${p.fuerza ? ' · ' + p.fuerza : ''}</span>
    ${p.hallazgo ? ' <span class="etiqueta">hallazgo candidato</span>' : ''}
    <div class="ficha">
      <div><b>ρ corregida</b><span>${fmt(p.corr)} [${fmt(p.ic[0])}; ${fmt(p.ic[1])}]</span></div>
      <div><b>ρ cruda</b><span>${fmt(p.cruda)}</span></div>
      <div><b>Releases</b><span>${p.n}</span></div>
      <div><b>Robusta</b><span>${si(p.robusta)}</span></div>
      <div><b>Control por tamaño</b><span>${p.tamano}</span></div>
      <div><b>Solapamiento de definición</b><span>${si(p.solap)}</span></div>
      <div><b>Por período (16–19 · 20–22 · 23–24 · 25–26)</b><span>${p.per.map(v => fmt(v)).join(' · ')}</span></div>
      <div><b>Canary · sin ventanas cortas</b><span>${fmt(p.canary)} · ${fmt(p.sincortas)}</span></div>
      <div><b>Alcance temporal</b><span>${p.alcance || '—'}</span></div>
      <div><b>Escala</b><span>${p.escala || '—'}</span></div>
    </div>
    ${p.motivo ? `<div class="motivo">Por qué no es hallazgo: ${p.motivo}</div>` : ''}`;
  sensibilidad(document.getElementById('dispSens'), p);
  movil(document.getElementById('dispMovil'), p, inv);
  barrasPeriodo(document.getElementById('dispPeriodos'), p);
  dispersion(document.getElementById('dispAjustada'), ajustF, nx + ' (ajustado)', ny + ' (ajustado)', true);
  dispersion(document.getElementById('dispOriginal'), origF, nx, ny, false);
  temporal(document.getElementById('dispTiempo'), x, y, p, inv);
}

function elegirX(actualY) {
  const ys = compañeras(selX.value);
  opciones(selY, ys, actualY);
  document.getElementById('cuentaY').textContent = `${plural(ys.length, 'variable forma', 'variables forman')} par con esta`
    + (hayFiltros() ? ' (con los filtros)' : ' en el cruce');
  mostrar();
}
actualizarSelectores = function () {
  const xs = D.variables.map(v => v.id).filter(x => compañeras(x).length);
  const cuenta = document.getElementById('cuentaX');
  selX.disabled = selY.disabled = !xs.length;
  if (!xs.length) {
    selX.innerHTML = selY.innerHTML = '';
    cuenta.textContent = 'Ningún par cumple los filtros de la tabla';
    document.getElementById('cuentaY').textContent = '';
    return;
  }
  cuenta.textContent = `${plural(xs.length, 'variable', 'variables')} · ${plural(paresVisibles.size, 'par', 'pares')}`
    + (hayFiltros() ? (paresVisibles.size === 1 ? ' que cumple' : ' que cumplen') + ' los filtros de la tabla' : ' en el cruce');
  const actualX = selX.value, actualY = selY.value;
  if (xs.includes(actualX)) { opciones(selX, xs, actualX); elegirX(actualY); return; }
  const primero = D.pares[ordenVisibles[0]] || D.pares[[...paresVisibles][0]];
  opciones(selX, xs, primero.x); elegirX(primero.y);
};
actualizarSelectores();
selX.addEventListener('change', () => elegirX(selY.value));
selY.addEventListener('change', mostrar);
abrirPar = function (id) {
  const p = D.pares[id]; if (!p) return;
  selX.value = p.x; elegirX(p.y);
  document.getElementById('explorador').scrollIntoView({ behavior: 'smooth', block: 'start' });
}
// #par=<id> en la dirección abre ese par (lo usa el enlace del informe)
const parUrl = location.hash.startsWith('#par=') ? decodeURIComponent(location.hash.slice(5)) : null;
abrirPar(parUrl && D.pares[parUrl] ? parUrl : D.inicial);
"""


def construir(cruce: str) -> dict:
    """Arma las piezas del reporte de un cruce (ya normalizado). Las usa main() para
    escribir el reporte y generar_informe.py para insertarlas en un informe."""
    pares = pd.read_csv(PARES)
    p = pares[pares.cruce == cruce].copy()
    if p.empty:
        a, b = cruce.split("–")
        if a != b:
            sys.exit(f"{PARES} tiene solo los pares dentro de cada dimensión. El cruce {cruce} se analiza con "
                     f"cruces.py {a} {b} y su reporte es reporte_cruce_dimensiones.py {a} {b}.")
        sys.exit(f"No hay pares del cruce {cruce} en {PARES}")
    nombres = nombres_variables()

    control = p.por_construccion.map(es_verdadero)
    ev = p[~control]
    robustas = ev[ev.robusta.map(es_verdadero)]
    tam = robustas.apply(control_tamano, axis=1)
    sin_solap = ev[~ev.solapamiento_definicion.map(es_verdadero)]
    hallazgos = ev[ev.hallazgo_candidato.map(es_verdadero)]
    rel_tamano = ev[ev.relacion_tamano.map(es_verdadero)] if "relacion_tamano" in ev else ev.iloc[0:0]
    pos = ev[ev.categoria == "positiva"].sort_values("rho_corregida", ascending=False)
    neg = ev[ev.categoria == "negativa"].sort_values("rho_corregida", ascending=True)

    kpis = [
        (len(p), "Pares", f"{int(control.sum())} de control"),
        (len(ev), "Pares evaluados", "sin los de control"),
        (len(pos) + len(neg), "Con relación", f"{len(pos)} positivas · {len(neg)} negativas"),
        (len(robustas), "Robustos", "significativos, estables y replicados en canary"),
        (int((tam == "pasa").sum()), "Robustos que pasan el control por tamaño",
         f"{int((tam == 'no pasa').sum())} no pasan · {int((tam == 'no aplica').sum())} no aplica"),
        (len(sin_solap), "Sin solapamiento de definición", "entre los evaluados"),
        (len(hallazgos), "Hallazgos candidatos", "robustos, sin solapamiento, misma familia ni variable de tamaño"),
        (len(rel_tamano), "Relaciones con el tamaño", "pasarían como hallazgo, pero incluyen una variable de tamaño (escala)"),
    ]
    kpi_html = "".join(f'<div class="kpi"><div class="v">{v}</div><div class="l">{esc(l)}</div>'
                       f'<div class="d">{esc(d)}</div></div>' for v, l, d in kpis)

    conteos = [(etq, int((ev.categoria == cat).sum())) for cat, etq in CATEGORIAS]
    conteos = [c for c in conteos if c[1] > 0 or c[0] != "Insuficiente"]

    datos = datos_reporte(p, nombres)
    if datos["con_valores"]:
        orden = (hallazgos if len(hallazgos) else ev).assign(a=lambda d: d.rho_corregida.abs())
        datos["inicial"] = orden.sort_values("a", ascending=False).par_id.iloc[0]
        explorador = f"""
<h2 id="explorador">Explorador de pares</h2>
<p class="sub">Elegí dos variables del cruce: se muestran los resultados del par y sus valores en cada release.
Los selectores ofrecen solo los pares que cumplen los filtros de la tabla.
También podés hacer clic en una fila de la tabla de pares.</p>
<div class="panel">
  <div class="selectores">
    <label>Variable X<select id="selX"></select><span class="cuenta" id="cuentaX"></span></label>
    <label>Variable Y<select id="selY"></select><span class="cuenta" id="cuentaY"></span></label>
  </div>
  <div id="ficha"></div>
</div>
<div class="graficos">
  <div class="panel"><h3>Sensibilidad: la ρ del par con cada control</h3>
    <div class="grafico-disp" id="dispSens"></div>
    <p class="nota">Si los puntos quedan del mismo lado del 0 y fuera de las líneas punteadas (±0,1), la relación no depende de
    esa decisión del método. Línea: intervalo de confianza de la ρ corregida.</p></div>
  <div class="panel"><h3>Correlación móvil</h3>
    <div class="grafico-disp" id="dispMovil"></div>
    <p class="nota">Correlación de los valores ajustados en una ventana de 41 releases alrededor de cada punto. Muestra cuándo
    aparece o desaparece la relación sin depender de los cortes de período. Punteada: ρ corregida de toda la historia.</p></div>
</div>
<div class="panel" style="margin-top:16px"><h3>Correlación corregida por período y en canary</h3>
  <div class="grafico-disp" id="dispPeriodos"></div>
  <div class="leyenda"><span><i class="cuad"></i>período con relación (|ρ| ≥ 0,1 e IC sin el 0)</span>
    <span><i class="cuad debil"></i>período sin relación</span><span><i class="cuad y"></i>canary</span>
    <span><i class="punteada"></i>ρ corregida de toda la historia</span></div>
  <p class="nota">Los bigotes son el intervalo de confianza del 95% de cada período. Un período sin barra no tiene ventanas suficientes (menos de 15).
  <b>Hacé clic en un período</b> (acá o en una franja del gráfico temporal) para ver solo ese período en los demás gráficos.</p></div>
<div class="filtro-banner" id="filtroPeriodo" role="status"></div>
<div class="graficos">
  <div class="panel"><h3>Relación ajustada (sin tiempo ni duración)</h3>
    <div class="grafico-disp" id="dispAjustada"></div>
    <div class="leyenda"><span><i></i>release</span><span><i class="y"></i>backport</span><span><i class="linea"></i>tendencia</span></div>
    <p class="nota">Cada eje: posición del release menos la esperable para su momento y su duración. La correlación de esta nube es la ρ corregida.</p></div>
  <div class="panel"><h3>Valores originales</h3>
    <div class="grafico-disp" id="dispOriginal"></div>
    <div class="leyenda"><span><i></i>release</span><span><i class="y"></i>backport</span><span><i class="linea"></i>tendencia</span></div>
    <p class="nota">Valores de cada métrica tal como se calcularon, con la tendencia del proyecto incluida.</p></div>
</div>
<div class="panel" style="margin-top:16px"><h3>Evolución en el tiempo</h3>
  <div class="modo" id="modoTiempo" role="group" aria-label="Valores del gráfico temporal">
    <button type="button" data-modo="original" class="activo">Valores originales</button>
    <button type="button" data-modo="ajustado">Ajustados (sin tiempo ni duración)</button>
  </div>
  <div class="grafico-disp" id="dispTiempo"></div>
  <div class="leyenda" id="leyendaTiempo"></div>
  <p class="nota">Un panel por variable, con el mismo eje de tiempo (cada punto es el inicio de la ventana del release).
  Las franjas marcan los períodos del análisis. En "ajustados", cada línea muestra cuánto se aparta la variable de lo
  esperable para su momento y su duración: si suben y bajan juntas, la relación existe release a release.</p></div>
"""
        script_explorador = f"<script>{SCRIPT}</script>"
    else:
        script_explorador = ""
        explorador = (f'<p class="nota">No se encontró {VALORES.name} (ni sus mitades _persona / _resto): corré generar_correlaciones.py '
                      f'para generar los valores por release y ver el explorador de pares.</p>')

    tabla_pares = f"""
<h2>Pares del cruce</h2>
<p class="sub">Ordenados de mayor a menor |ρ corregida| · los filtros se combinan · clic en una fila para verla en el explorador</p>
<div class="panel">
  <div class="filtros">
    <div class="modo" id="filtroDir" role="group" aria-label="Dirección de la relación" style="margin:0">
      <button type="button" data-dir="todas" class="activo">Todas</button>
      <button type="button" data-dir="pos">Positivas</button>
      <button type="button" data-dir="neg">Negativas</button>
    </div>
    <button type="button" class="chip" data-filtro="sig" aria-pressed="false"
      title="Categoría positiva o negativa: p ajustado por pruebas múltiples menor a 0,05">Significativas</button>
    <button type="button" class="chip" data-filtro="rob" aria-pressed="false"
      title="Significativa, mismo signo en todos los períodos y en canary, sin depender de ventanas cortas">Robustas</button>
    <button type="button" class="chip" data-filtro="tam" aria-pressed="false"
      title="Con el control por tamaño mantiene el signo y |ρ| ≥ 0,1">Pasan el control por tamaño</button>
    <button type="button" class="chip limpiar" id="limpiarFiltros">Limpiar filtros</button>
    <span class="conteo" id="conteoTabla"></span>
  </div>
  <div class="tabla" id="tablaPares"></div>
</div>

<h2>Mapa de calor</h2>
<p class="sub">Correlación de cada par del cruce · usa los filtros de la tabla · clic en una celda para verla en el explorador</p>
<div class="panel">
  <div class="modo" id="modoMapa" role="group" aria-label="Correlación del mapa" style="margin-top:0">
    <button type="button" data-modo="corr" class="activo">ρ corregida</button>
    <button type="button" data-modo="cruda">ρ cruda</button>
  </div>
  <div class="grafico-disp mapa-cont" id="mapaCalor"></div>
  <div id="leyendaMapa"></div>
  <p class="nota">Azul: correlación negativa; naranja: positiva; gris: cerca de 0. Las celdas vacías son la diagonal o pares
  que no pertenecen al cruce. Con filtros activos, los pares que no los cumplen se muestran atenuados.
  Comparar "corregida" y "cruda" muestra cuánto de cada relación venía del crecimiento del proyecto.</p>
</div>

<h2>Vista general del cruce</h2>
<p class="sub">Salvo el embudo, usan los filtros de la tabla · clic en un par para verlo en el explorador</p>
<div class="panel"><h3>Embudo: de los pares evaluados a los hallazgos</h3>
  <div id="vEmbudo"></div>
  <p class="nota">Cada paso agrega una condición a la anterior; muestra en qué paso se descarta la mayoría de las relaciones.
  No usa los filtros de la tabla.</p></div>
<div class="graficos">
  <div class="panel"><h3>ρ cruda vs. ρ corregida</h3>
    <div class="grafico-disp" id="vCrudaCorr"></div>
    <div class="leyenda"><span><i></i>significativo</span><span><i class="gris"></i>no significativo</span><span><i class="anillo"></i>robusto</span></div>
    <p class="nota">Cada punto es un par. Sobre la diagonal, la relación no cambia al corregir; los que caen a la franja
    (−0,2 a 0,2) eran crecimiento del proyecto o efecto de la duración de las ventanas.</p></div>
  <div class="panel"><h3>Red de relaciones significativas</h3>
    <div class="grafico-disp" id="vRed"></div>
    <div class="leyenda"><span><i class="linea-neg"></i>negativa</span><span><i class="linea-pos"></i>positiva</span></div>
    <p class="nota">Cada línea une dos variables con una relación significativa; el grosor es la fuerza.
    Las variables sin relaciones quedan en gris.</p></div>
</div>
<div class="panel" style="margin-top:16px"><h3>Intervalos de las relaciones significativas</h3>
  <div class="grafico-disp" id="vForest"></div>
  <div class="leyenda"><span><i></i>robusta</span><span><i class="hueco"></i>no robusta</span></div>
  <p class="nota">Punto: ρ corregida; línea: intervalo de confianza del 95%. La franja marca la zona despreciable.</p></div>
<div class="panel" style="margin-top:16px"><h3>Estabilidad por período de las relaciones significativas</h3>
  <div class="grafico-disp" id="vEstab"></div>
  <p class="nota">Naranja / azul: relación positiva / negativa en ese período (|ρ| ≥ 0,1 e intervalo sin el 0);
  gris: sin relación en ese período; vacío: menos de 15 ventanas.</p></div>"""

    scripts = (f'<script type="application/json" id="datos">{json.dumps(datos, ensure_ascii=False, separators=(",", ":"))}</script>\n'
               f"<script>{SCRIPT_TABLA}</script>\n{script_explorador}")
    resumen = (f"{cruce}: {len(p)} pares, {len(ev)} evaluados, {len(pos)} positivas, {len(neg)} negativas, "
               f"{len(robustas)} robustos, {int((tam == 'pasa').sum())} pasan tamaño, "
               f"{len(sin_solap)} sin solapamiento, {len(hallazgos)} hallazgos")
    return {
        "cruce": cruce, "kpis": f'<div class="kpis">{kpi_html}</div>', "tabla_pares": tabla_pares,
        "categorias": (f'<h2>Pares por categoría</h2>\n<p class="sub">{len(ev)} pares evaluados '
                       f'(sin los {int(control.sum())} de control)</p>\n<div class="panel">{grafico(conteos, len(ev))}</div>'),
        "grafico_categorias": grafico(conteos, len(ev)),
        "explorador": explorador, "scripts": scripts, "resumen": resumen,
    }


NOTA_FINAL = """<p class="nota">Control por tamaño: "pasa" si con el control la correlación mantiene el signo y |ρ| ≥ 0,1;
"no aplica" en pares de control o con variables de la familia tamaño. Robusta: significativa, con el mismo
signo en todos los períodos y en canary, y sin depender de las ventanas de menos de 1 día.</p>"""


def archivo_reporte(cruce: str) -> Path:
    return SALIDA / f"reporte_{cruce.replace('–', '_').lower()}.html"


def escribir_reporte(cruce: str, r: dict | None = None) -> Path:
    """Escribe el reporte del cruce (ya normalizado) y devuelve su ruta."""
    r = r or construir(cruce)
    titulo = f"Correlaciones {cruce}"
    doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(titulo)}</title><style>{ESTILO}</style></head>
<body><main>
<h1>{esc(titulo)}</h1>
<p class="sub">Fuente: analisis/salidas/pares_correlacion.csv y pares_valores.csv · correlación corregida por tiempo y duración · serie estable de next.js</p>
{r["kpis"]}
{r["tabla_pares"]}

{r["categorias"]}

{r["explorador"]}
{r["scripts"]}

{NOTA_FINAL}
</main></body></html>
"""
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = archivo_reporte(cruce)
    destino.write_text(doc, encoding="utf-8")
    return destino


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cruce", help="por ejemplo Producto-Producto o Persona-Proceso")
    args = ap.parse_args()
    cruce = normalizar_cruce(args.cruce)
    r = construir(cruce)
    destino = escribir_reporte(cruce, r)
    print(r["resumen"])
    print(f"Reporte: {destino} ({destino.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
