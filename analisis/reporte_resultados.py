#!/usr/bin/env python3
"""
analisis/reporte_resultados.py

Las vistas de los reportes que no tienen generador propio: los patrones finales, el cruce entre grupos,
los cruces sin las métricas compartidas, el multiverso de asignaciones y el PCA y agrupamiento conjunto
de las tres dimensiones. reportes.py las suma como pestañas a los tres reportes.

Uso: python3 analisis/reporte_resultados.py   (después de relaciones.py, bloques_etiquetas.py,
     multiverso_asignacion.py, tres_dimensiones.py y cruces.py --grupos)

Lee:
    salidas/5_patrones/patrones.csv                     patrones finales y descartados al validar
    salidas/3_cruces/<a>_<b>/clustering_propio/          cruce entre grupos (cruces.py --grupos propio)
    salidas/6_robustez/metricas_compartidas/             componentes y grupos sin métricas compartidas
    salidas/6_robustez/multiverso_asignacion/            multiverso de asignaciones
    salidas/4_tres_dimensiones/resumen.json              PCA y agrupamiento conjunto
Escribe en salidas/reportes/_partes/:
    intradimensional/<dim>_patrones.html
    bidimensional/<a>_<b>_{patrones,grupos,compartidas,multiverso}.html
    tridimensional/{conjunto,multiverso}.html
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

DIMS = ("Persona", "Proceso", "Producto")
PARES = (("Persona", "Proceso"), ("Persona", "Producto"), ("Proceso", "Producto"))
PERIODOS = None  # se leen de las columnas rho_AAAA_AAAA

ESTILO_EXTRA = """
.etq { display:inline-block; font-size:12px; padding:1px 8px; border-radius:999px; border:1px solid var(--borde); white-space:nowrap; }
.etq.si { background:var(--texto); color:var(--fondo); border-color:var(--texto); }
.etq.alta { background:var(--texto); color:var(--fondo); border-color:var(--texto); }
.etq.media { border-color:var(--texto2); }
td .pos { color:var(--div-pos); } td .neg { color:var(--div-neg); }
td .tenue, .tenue { color:var(--tenue); }
.barrita { display:inline-block; height:8px; border-radius:4px; background:var(--serie); vertical-align:middle; margin-right:6px; }
.grupos { display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:12px; }
.grupos ul { margin:6px 0 0; padding-left:18px; font-size:13.5px; }
.grupos li { margin:3px 0; }
details { margin-top:12px; } summary { cursor:pointer; color:var(--texto2); font-size:14px; }
"""


# ── utilidades ────────────────────────────────────────────────────────────────

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
    return (f"{f:+.{d}f}" if signo else f"{f:.{d}f}").replace(".", ",")


def rho_html(v):
    f = num(v)
    if f is None:
        return "<span class='tenue'>—</span>"
    return f"<span class='{'pos' if f > 0 else 'neg'}'>{fmt(f)}</span>"


def pct(v):
    f = num(v)
    if f is None:
        return "—"
    return "< 1 %" if 0 < f < 0.005 else f"{f * 100:.0f} %"


def barra_pct(v):
    f = num(v) or 0
    return f"<span class='barrita' style='width:{max(2, f * 60):.0f}px'></span>{pct(f)}"


def verdadero(v):
    return str(v).strip().lower() in ("true", "1", "sí", "si")


def leer(ruta):
    return pd.read_csv(ruta) if Path(ruta).exists() else pd.DataFrame()


NOMBRES = None


def nombre(v):
    return NOMBRES.get(v, v) if NOMBRES else v


def tabla(cabeza, filas, vacio="Ninguno.", clase=""):
    if not filas:
        return f'<p class="vacio">{vacio}</p>'
    th = "".join(f"<th>{c}</th>" for c in cabeza)
    return f'<div class="tabla"><table class="{clase}"><thead><tr>{th}</tr></thead><tbody>{"".join(filas)}</tbody></table></div>'


def kpis(items):
    return '<div class="kpis">' + "".join(
        f'<div class="kpi"><div class="v">{esc(v)}</div><div class="l">{esc(l)}</div><div class="d">{esc(d)}</div></div>'
        for v, l, d in items) + "</div>"


def pagina(titulo, sub, cuerpo):
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{esc(titulo)}</title><style>{rc.ESTILO}{ESTILO_EXTRA}</style></head><body><main>'
            f'<h1>{esc(titulo)}</h1><p class="sub">{sub}</p>{cuerpo}</main></body></html>')


def guardar(carpeta, nombre_archivo, contenido):
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / nombre_archivo).write_text(contenido, encoding="utf-8")
    print(f"  {carpeta.name}/{nombre_archivo}")


# ── patrones finales (relaciones.py) ──────────────────────────────────────────

def columnas_periodo(df):
    return [c for c in df.columns if c.startswith("rho_") and c[4:8].isdigit()]


def filas_patrones(sub, per, otras):
    filas = []
    for r in sub.itertuples():
        nivel = r.nivel if isinstance(r.nivel, str) else ""
        periodos = " ".join(fmt(getattr(r, c), 2) for c in per)
        filas.append(
            f"<tr><td>{esc(nombre(r.x))} ↔ {esc(nombre(r.y))}<div class='tenue' style='font-size:12px'>{esc(r.x)} · {esc(r.y)}</div></td>"
            f"<td class='n'>{rho_html(r.rho)}</td><td><span class='etq {esc(nivel)}'>{esc(nivel)}</span></td>"
            f"<td class='n'>{rho_html(r.rho_canary)}</td><td class='n'>{rho_html(r.rho_tamano)}</td>"
            f"<td class='n tenue'>{periodos}</td><td>{esc(otras(r))}</td></tr>")
    return filas


def filas_descartados(sub):
    return [f"<tr><td>{esc(nombre(r.x))} ↔ {esc(nombre(r.y))}</td><td class='n'>{rho_html(r.rho)}</td>"
            f"<td>{esc(str(r.motivo).replace('descartado al validar: ', ''))}</td></tr>" for r in sub.itertuples()]


def contiene(celda, valor):
    return isinstance(celda, str) and valor in [x.strip() for x in celda.split(";")]


def vista_patrones_dimension(pat, dim):
    per = columnas_periodo(pat)
    es = pat[pat.patron.map(verdadero) & pat.dentro.map(lambda c: contiene(c, dim))]
    es = es.reindex(es.rho.abs().sort_values(ascending=False).index)
    desc = pat[pat.motivo.fillna("").str.startswith("descartado al validar") & pat.dentro.map(lambda c: contiene(c, dim))]
    solo = int((es.tipo == "dentro").sum())

    def otras(r):
        return "también " + r.entre.replace(";", ",") if isinstance(r.entre, str) and r.entre else "solo dentro de la dimensión"
    cab = ["Par", "ρ", "Evidencia", "Canary", "Con tamaño", "Por período (" + ", ".join(c[4:].replace("_", "–") for c in per) + ")", "Otras lecturas"]
    cuerpo = (kpis([(len(es), "patrones que se leen dentro de " + dim, f"{solo} solo dentro; el resto también conecta dimensiones"),
                    (len(desc), "descartados al validar", "relaciones que producía el cálculo, no el proyecto")])
              + f"<h2>Patrones</h2><p class='sub'>Pares de variables de {dim} que pasaron todos los controles: significativos "
              "con Benjamini–Hochberg sobre todos los pares, estables en los períodos, replicados en canary, que resisten el "
              "control por tamaño y sin explicación mecánica. Cuando el catálogo asigna una variable a dos dimensiones, el patrón "
              "también se lee entre dimensiones («otras lecturas»).</p>"
              + tabla(cab, filas_patrones(es, per, otras), "No hay patrones dentro de esta dimensión.")
              + "<h2>Descartados al validar</h2><p class='sub'>Pasaban todos los controles, pero desaparecían al recalcular las "
              "variables sin los datos que podían producirlos.</p>"
              + tabla(["Par", "ρ", "Sin qué datos desaparece"], filas_descartados(desc), "Ninguno."))
    return pagina(f"Patrones finales · {dim}", f"{esc(rutas.proyecto.REPO)} · criterio final (relaciones.py) · fuente: salidas/5_patrones/patrones.csv", cuerpo)


def vista_patrones_par(pat, a, b):
    par = f"{a}–{b}"
    per = columnas_periodo(pat)
    es = pat[pat.patron.map(verdadero) & pat.entre.map(lambda c: contiene(c, par))]
    es = es.reindex(es.rho.abs().sort_values(ascending=False).index)
    desc = pat[pat.motivo.fillna("").str.startswith("descartado al validar") & pat.entre.map(lambda c: contiene(c, par))]
    solo = es[es.tipo == "entre dimensiones"]

    def otras(r):
        lect = [x.strip() for x in str(r.entre).split(";") if x.strip() != par]
        if isinstance(r.dentro, str) and r.dentro:
            lect += [f"dentro de {d.strip()}" for d in r.dentro.split(";")]
        return ", ".join(lect) if lect else "solo esta"
    cab = ["Par", "ρ", "Evidencia", "Canary", "Con tamaño", "Por período (" + ", ".join(c[4:].replace("_", "–") for c in per) + ")", "Otras lecturas"]
    cuerpo = (kpis([(len(es), f"patrones que conectan {a} y {b}", "con alguna de las lecturas del catálogo"),
                    (len(solo), "solo se leen entre dimensiones", "no se leen dentro de ninguna dimensión"),
                    (len(desc), "descartados al validar", "relaciones que producía el cálculo")])
              + f"<h2>Patrones</h2><p class='sub'>Es el criterio final del trabajo (relaciones.py): todos los pares se evalúan una sola vez y "
              "cada patrón cuenta para todos los pares de dimensiones que el catálogo permite. Puede diferir de la pestaña "
              "«Variables y componentes», que asigna cada métrica compartida a un solo lado.</p>"
              + tabla(cab, filas_patrones(es, per, otras), "No hay patrones entre estas dimensiones.")
              + "<h2>Descartados al validar</h2>"
              + tabla(["Par", "ρ", "Sin qué datos desaparece"], filas_descartados(desc), "Ninguno."))
    return pagina(f"Patrones finales · {a} – {b}", f"{esc(rutas.proyecto.REPO)} · criterio final (relaciones.py) · fuente: salidas/5_patrones/patrones.csv", cuerpo)


# ── cruce entre grupos (cruces.py --grupos) ───────────────────────────────────

METODOS = {"promedio": "Promedio de las métricas", "componente": "Primer componente del grupo",
           "representativa": "Métrica más representativa"}


def vista_grupos(a, b):
    base = rutas.cruce(a, b) / "clustering_propio"
    if not (base / "resumen.json").exists():
        return pagina(f"Grupos · {a} – {b}", "", "<p class='vacio'>No se corrió el cruce entre grupos (cruces.py --grupos propio).</p>")
    res = json.loads((base / "resumen.json").read_text(encoding="utf-8"))
    tarjetas = []
    for d in (a, b):
        g = res["grupos"].get(d, {})
        items = "".join(f"<li><b>{esc(x['id'].split('_')[-1].upper())}</b>: {esc(', '.join(nombre(v) for v in x['variables']))}</li>"
                        for x in g.get("grupos", []))
        sueltas = ", ".join(nombre(v) for v in g.get("sueltas", []))
        tarjetas.append(f"<div class='panel'><h3>{d}</h3><p class='nota'>{g.get('k', '—')} grupos · estabilidad {fmt(g.get('estabilidad'), 2, False)} · "
                        f"canary {fmt(g.get('ari_canary'), 2, False)} · coincidencia con el PCA {fmt(g.get('ari_pca'), 2, False)}</p>"
                        f"<ul>{items}</ul>" + (f"<p class='nota'>Solas: {esc(sueltas)}</p>" if sueltas else "") + "</div>")
    resumen = []
    for m, t in METODOS.items():
        r = res.get("metodos", {}).get(m, {}).get("grupos", {})
        tipos = r.get("tipos", {})
        resumen.append(f"<tr><td>{t}</td><td class='n'>{r.get('pares', '—')}</td><td class='n'>{len(r.get('robustos', []))}</td>"
                       f"<td class='n'>{tipos.get('patrón', 0)}</td><td class='n'>{tipos.get('escala', 0)}</td><td class='n'>{tipos.get('mecánico', 0)}</td></tr>")
    pares = leer(base / "promedio" / "pares_grupos.csv")
    filas = []
    if not pares.empty:
        rob = pares[pares.robusta.map(verdadero)].copy()
        rob = rob.reindex(rob.rho_corregida.abs().sort_values(ascending=False).index)
        for r in rob.itertuples():
            tipo = r.tipo if isinstance(r.tipo, str) else ""
            filas.append(f"<tr><td>{esc(r.x_nombre)}</td><td>{esc(r.y_nombre)}</td><td class='n'>{rho_html(r.rho_corregida)}</td>"
                         f"<td class='n'>{rho_html(r.rho_canary)}</td><td class='n'>{rho_html(r.rho_corregida_tamano)}</td>"
                         f"<td><span class='etq{' si' if tipo == 'patrón' else ''}'>{esc(tipo or '—')}</span></td></tr>")
    cuerpo = (f"<h2>Grupos de cada dimensión</h2><p class='sub'>Agrupamiento jerárquico de las métricas de cada dimensión "
              f"(clustering.py), con la cantidad de grupos que elige la silueta. Cada grupo se resume en una serie por release.</p>"
              f"<div class='grupos'>{''.join(tarjetas)}</div>"
              "<h2>Resumen por forma de resumir el grupo</h2>"
              + tabla(["Serie del grupo", "Pares", "Robustos", "Patrones", "Escala", "Mecánicos"], resumen)
              + "<h2>Pares de grupos robustos</h2><p class='sub'>Con la serie de cada grupo como el promedio de sus métricas "
              "(orientadas según la métrica central). Patrón: robusto, resiste el control por tamaño y no es mecánico.</p>"
              + tabla([f"Grupo de {a}", f"Grupo de {b}", "ρ", "Canary", "Con tamaño", "Tipo"], filas, "No hay pares robustos."))
    return pagina(f"Grupos · {a} – {b}", f"{esc(rutas.proyecto.REPO)} · cruce entre los grupos del agrupamiento (cruces.py --grupos propio)", cuerpo)


# ── componentes y grupos sin las métricas compartidas (bloques_etiquetas.py) ──

def vista_compartidas(bl, a, b):
    par = f"{a}–{b}"
    if bl.empty:
        return pagina(f"Sin métricas compartidas · {a} – {b}", "", "<p class='vacio'>No se corrió bloques_etiquetas.py.</p>")
    sub = bl[bl.entre.map(lambda c: contiene(c, par))].copy()
    sub["abs"] = sub.rho_corregida.abs()
    secciones = []
    for tipo, titulo in (("componente", "Componentes"), ("grupo", "Grupos")):
        s = sub[sub.tipo_elemento == tipo].sort_values(["patron", "abs"], ascending=[False, False])
        filas = []
        for r in s.itertuples():
            if not verdadero(r.evaluado):
                estado = "<span class='tenue'>no se evalúa: no le queda ninguna métrica propia</span>"
            elif verdadero(r.patron):
                estado = "<span class='etq si'>patrón</span>"
            else:
                estado = f"<span class='tenue'>{esc(str(r.motivo).replace('_', ' ') if isinstance(r.motivo, str) else '')}</span>"
            x, y = r.par_id.split("__")
            comp = f"<div class='tenue' style='font-size:12px'>comparten {esc(r.comparten)}</div>" if isinstance(r.comparten, str) and r.comparten else ""
            filas.append(f"<tr><td>{esc(r.x_tema)}<div class='tenue' style='font-size:12px'>{esc(x)}</div></td>"
                         f"<td>{esc(r.y_tema)}<div class='tenue' style='font-size:12px'>{esc(y)}</div>{comp}</td>"
                         f"<td class='n'>{rho_html(r.rho_corregida)}</td><td class='n'>{rho_html(r.rho_canary)}</td>"
                         f"<td class='n'>{rho_html(r.rho_corregida_tamano)}</td><td>{estado}</td></tr>")
        n_pat = int(s.patron.map(verdadero).sum())
        secciones.append(f"<h2>{titulo}</h2><p class='sub'>{len(s)} cruces, {n_pat} patrones.</p>"
                         + (tabla(["Elemento", "Elemento", "ρ", "Canary", "Con tamaño", "Resultado"], filas[:12])
                            + (f"<details><summary>Ver los {len(filas) - 12} restantes</summary>"
                               + tabla(["Elemento", "Elemento", "ρ", "Canary", "Con tamaño", "Resultado"], filas[12:]) + "</details>"
                               if len(filas) > 12 else "")))
    cuerpo = ("<p class='sub'>Componentes y grupos de cada dimensión armados con <b>todas</b> sus variables, también las que el "
              "catálogo asigna a dos dimensiones. Si dos elementos comparten métricas, se cruza la parte propia de cada uno, para no "
              "comparar una métrica consigo misma; si a alguno no le queda nada, el cruce no se evalúa.</p>" + "".join(secciones))
    return pagina(f"Sin métricas compartidas · {a} – {b}", f"{esc(rutas.proyecto.REPO)} · bloques_etiquetas.py · fuente: salidas/6_robustez/metricas_compartidas", cuerpo)


# ── multiverso de asignaciones ────────────────────────────────────────────────

ANALISIS_PAR = ["componentes", "grupos", "conjunto reducido", "triangulación", "PCA conjunto", "clustering conjunto"]


def filas_multiverso(sub):
    filas = []
    for r in sub.itertuples():
        decide = r.decide if isinstance(r.decide, str) else ""
        filas.append(f"<tr><td>{esc(r.patron)}</td><td>{'<span class=\"etq si\">sí</span>' if verdadero(r.en_principal) else 'no'}</td>"
                     f"<td>{barra_pct(r.asignaciones)}</td><td class='tenue'>{esc(decide)}</td></tr>")
    return filas


def vista_multiverso_par(uni, mpc, mpv, a, b):
    par = f"{a}–{b}"
    if uni.empty:
        return pagina(f"Multiverso · {a} – {b}", "", "<p class='vacio'>No se corrió multiverso_asignacion.py.</p>")
    col, colp = f"cca {par}", f"cca {par} p"
    prin = uni[uni.universo == "principal"]
    sig = (uni[colp] < 0.05).mean() if colp in uni else None
    cuerpo = kpis([(pct(sig), "asignaciones con correlación canónica significativa", f"de {len(uni)} asignaciones de las métricas compartidas"),
                   (fmt(prin[col].iloc[0], 2, False) if not prin.empty else "—", "correlación canónica en la principal",
                    f"rango {fmt(uni[col].min(), 2, False)} a {fmt(uni[col].max(), 2, False)} en todas")])
    bloques = []
    for an in ANALISIS_PAR:
        if an in ("PCA conjunto", "clustering conjunto"):
            s = mpc[mpc.analisis == f"{an} {par}"]
        else:
            s = mpc[(mpc.analisis == an) & mpc.patron.map(lambda p: f"{a}:" in str(p) and f"{b}:" in str(p))]
        s = s.sort_values("asignaciones", ascending=False)
        if s.empty:
            continue
        filas = filas_multiverso(s)
        cab = ["Patrón", "En la principal", "Asignaciones en que aparece", "Qué lo decide"]
        bloques.append(f"<h3 style='margin-top:20px'>{esc(an[0].upper() + an[1:])}</h3>" + tabla(cab, filas[:8])
                       + (f"<details><summary>Ver los {len(filas) - 8} restantes</summary>" + tabla(cab, filas[8:]) + "</details>" if len(filas) > 8 else ""))
    var = mpv[mpv.lecturas.fillna("").str.contains(par)] if not mpv.empty else mpv
    filas_v = [f"<tr><td>{esc(nombre(r.x))} ↔ {esc(nombre(r.y))}</td><td class='n'>{rho_html(r.rho)}</td><td>{esc(r.principal)}</td>"
               f"<td>{barra_pct(r.entre_dimensiones)}</td><td class='tenue'>{esc(r.lecturas)}</td></tr>"
               for r in var.sort_values("entre_dimensiones", ascending=False).itertuples()]
    cuerpo += ("<h2>Pares de variables</h2><p class='sub'>Pares que son patrón en algún nivel y que, con alguna asignación, conectan "
               f"{a} y {b}. La correlación es la misma en todas; cambia de qué dimensiones se lee.</p>"
               + tabla(["Par", "ρ", "En la principal", "Entre dimensiones", "Lecturas"], filas_v[:12])
               + (f"<details><summary>Ver los {len(filas_v) - 12} restantes</summary>"
                  + tabla(["Par", "ρ", "En la principal", "Entre dimensiones", "Lecturas"], filas_v[12:]) + "</details>" if len(filas_v) > 12 else "")
               + "<h2>Componentes, grupos y medidas conjuntas</h2><p class='sub'>Versión liviana de cada cruce, recalculada en cada "
               "asignación: en qué proporción aparece cada patrón y qué métrica lo decide.</p>" + "".join(bloques))
    return pagina(f"Multiverso · {a} – {b}", f"{esc(rutas.proyecto.REPO)} · multiverso_asignacion.py · fuente: salidas/6_robustez/multiverso_asignacion", cuerpo)


def vista_multiverso_tres(uni, mpc, tris_bl):
    if uni.empty:
        return pagina("Multiverso y métricas compartidas", "", "<p class='vacio'>No se corrió multiverso_asignacion.py.</p>")
    prin = uni[uni.universo == "principal"]
    medidas = []
    for m, t in (("gcca", "Correlación canónica generalizada"), ("rv_medio", "RV medio"), ("mfa1", "Primer factor del MFA")):
        medidas.append(f"<tr><td>{t}</td><td class='n'>{fmt(prin[m].iloc[0] if not prin.empty else None, 3, False)}</td>"
                       f"<td class='n'>{fmt(uni[m].min(), 3, False)} a {fmt(uni[m].max(), 3, False)}</td>"
                       f"<td>{barra_pct((uni[m + '_p'] < 0.05).mean())}</td></tr>")
    s = mpc[mpc.analisis == "tres dimensiones"].sort_values("asignaciones", ascending=False)
    filas = filas_multiverso(s)
    cab = ["Patrón", "En la principal", "Asignaciones en que aparece", "Qué lo decide"]
    tri = []
    for r in tris_bl.itertuples() if not tris_bl.empty else []:
        tri.append(f"<tr><td>{esc(r.elementos)}</td><td>{esc(r.componentes)}</td><td><span class='etq si'>{esc(r.tipo)}</span></td>"
                   f"<td>{esc(r.desaparece)}</td><td class='tenue'>{esc(r.lados)}</td></tr>")
    cuerpo = (kpis([(pct(uni.candidato_tres_dimensiones.mean()), "asignaciones con un patrón de tres dimensiones",
                     f"de {len(uni)} asignaciones de las métricas compartidas"),
                    (pct((uni.gcca_p < 0.05).mean()), "asignaciones con asociación global significativa", "correlación canónica generalizada")])
              + "<h2>Medida global en todas las asignaciones</h2><p class='sub'>Como comparan dimensiones completas, una métrica "
              "compartida tendría que estar en los dos lados. Se recalculan con la asignación principal, cada métrica cambiada de "
              "lado, la opuesta y 500 al azar.</p>"
              + tabla(["Medida", "Principal", "Rango", "Significativa (p < 0,05)"], medidas)
              + "<h2>Patrones de tres dimensiones según la asignación</h2>" + tabla(cab, filas[:10], "Ninguno.")
              + (f"<details><summary>Ver los {len(filas) - 10} restantes</summary>" + tabla(cab, filas[10:]) + "</details>" if len(filas) > 10 else "")
              + "<h2>Triángulos sin métricas compartidas</h2><p class='sub'>Componentes y grupos con todas sus variables, cruzando la "
              "parte propia de cada uno (bloques_etiquetas.py).</p>"
              + tabla(["Elementos", "Vértices", "Tipo", "Desaparece", "Lados: marginal → sin el tercero"], tri, "Ninguno."))
    return pagina("Multiverso y métricas compartidas", f"{esc(rutas.proyecto.REPO)} · multiverso_asignacion.py y bloques_etiquetas.py", cuerpo)


# ── PCA y agrupamiento conjunto de las tres dimensiones ───────────────────────

ENFOQUES = {"ajustado": "Ajustado (sin tendencia ni duración)", "tamano": "Ajustado y sin tamaño del equipo"}


def vista_conjunto(res):
    conj = res.get("conjunto", {}) if res else {}
    if not conj:
        return pagina("PCA y agrupamiento conjunto", "", "<p class='vacio'>No hay PCA conjunto (tres_dimensiones.py).</p>")
    secciones = []
    for enf, titulo in ENFOQUES.items():
        c = conj.get(enf)
        if not c:
            continue
        p, k = c["pca"], c["clustering"]
        filas = []
        for cp in p["componentes"]:
            dims = ", ".join(cp["dimensiones"])
            marca = "<span class='etq si'>tres dimensiones</span>" if len(cp["dimensiones"]) == 3 else (
                "<span class='etq'>dos dimensiones</span>" if len(cp["dimensiones"]) == 2 else "")
            cargas = ", ".join(f"{nombre(v)} {fmt(x)}" for v, x in cp["cargas"])
            filas.append(f"<tr><td class='n'>CP{cp['n']}</td><td class='n'>{pct(cp['varianza'])}</td><td class='n'>{fmt(cp['bootstrap'], 2, False)}</td>"
                         f"<td>{esc(dims)} {marca}</td><td style='font-size:13px'>{esc(cargas)}</td></tr>")
        grupos = []
        for sol, t in (("propio", "corte propio"), ("pca", "tantos grupos como componentes")):
            s = k.get("soluciones", {}).get(sol)
            if not s:
                continue
            items = "".join(f"<li>[{esc(', '.join(g['dimensiones']))}] {esc(', '.join(nombre(v) for v in g['variables']))}</li>"
                            for g in s["grupos"] if len(g["variables"]) > 1)
            grupos.append(f"<div class='panel'><h3>{t} (k = {s['k']})</h3><p class='nota'>silueta {fmt(s['silueta'], 3, False)} frente a "
                          f"{fmt(s['nula_p95'], 3, False)} de la nula · estabilidad {fmt(s['estabilidad']['mediana'], 2, False)} · "
                          f"coincidencia con el PCA {fmt(s.get('ari_pca'), 2, False)}</p><ul>{items}</ul></div>")
        secciones.append(f"<h2>{titulo}</h2><p class='sub'>{p['variables']} variables de las tres dimensiones, {p['n']} releases, "
                         f"{p['k']} componentes (Horn).</p>"
                         + tabla(["", "Varianza", "Bootstrap", "Dimensiones", "Cargas"], filas)
                         + f"<div class='grupos' style='margin-top:12px'>{''.join(grupos)}</div>")
    cuerpo = ("<p class='sub'>Un PCA y un agrupamiento con las variables que definen los componentes de las tres dimensiones, sin "
              "decir de qué dimensión es cada una. Un componente o un grupo que mezcla variables de las tres es otra señal de "
              "conexión entre ellas.</p>" + "".join(secciones))
    return pagina("PCA y agrupamiento conjunto", f"{esc(rutas.proyecto.REPO)} · tres_dimensiones.py · fuente: salidas/4_tres_dimensiones/resumen.json", cuerpo)


def main():
    global NOMBRES
    NOMBRES = rc.nombres_variables()
    pat = leer(rutas.PATRONES / "patrones.csv")
    bl = leer(rutas.METRICAS_COMPARTIDAS / "pares.csv")
    tris_bl = leer(rutas.METRICAS_COMPARTIDAS / "triangulos.csv")
    uni = leer(rutas.MULTIVERSO / "universos.csv")
    mpc = leer(rutas.MULTIVERSO / "patrones_cruces.csv")
    mpv = leer(rutas.MULTIVERSO / "patrones_variables.csv")
    ruta3 = rutas.TRES_DIMENSIONES / "resumen.json"
    res3 = json.loads(ruta3.read_text(encoding="utf-8")) if ruta3.exists() else None

    if not pat.empty:
        for d in DIMS:
            guardar(rutas.REPORTES_DIMENSIONES, f"{d.lower()}_patrones.html", vista_patrones_dimension(pat, d))
    for a, b in PARES:
        base = f"{a.lower()}_{b.lower()}"
        if not pat.empty:
            guardar(rutas.REPORTES_CRUCES, f"{base}_patrones.html", vista_patrones_par(pat, a, b))
        guardar(rutas.REPORTES_CRUCES, f"{base}_grupos.html", vista_grupos(a, b))
        guardar(rutas.REPORTES_CRUCES, f"{base}_compartidas.html", vista_compartidas(bl, a, b))
        guardar(rutas.REPORTES_CRUCES, f"{base}_multiverso.html", vista_multiverso_par(uni, mpc, mpv, a, b))
    guardar(rutas.REPORTES_TRES, "conjunto.html", vista_conjunto(res3))
    guardar(rutas.REPORTES_TRES, "multiverso.html", vista_multiverso_tres(uni, mpc, tris_bl))


if __name__ == "__main__":
    main()
