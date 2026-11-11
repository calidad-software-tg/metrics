#!/usr/bin/env python3
"""
analisis/reporte_complementarios.py

La vista «Complementarios» de cada reporte: los análisis que no son técnica principal pero acompañan
a cada nivel (analisis/README.md, secciones 10 y 12).

    intradimensional  sensibilidad a los períodos (calendario frente a épocas), épocas de la dimensión,
                      agrupamiento temporal de releases y cambios de la estructura en el tiempo
    bidimensional     técnicas alternativas (CCA de todas las variables, reglas de asociación, regresión,
                      información mutua, random forest…), pertenencia ponderada según el catálogo,
                      sensibilidad a los períodos, coincidencia de etapas entre las dos dimensiones y
                      rezago (Proceso–Producto)
    tridimensional    composición de los componentes conjuntos según el catálogo, épocas con todas las
                      métricas y agrupamiento temporal conjunto

Lee salidas/complementarios/ (lo que dejan correlaciones.py --periodos ambos y los scripts de
analisis/complementarios/) y escribe en salidas/reportes/_partes/.

Uso: python3 analisis/reporte_complementarios.py
"""
import html
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reporte_resultados as rr  # noqa: E402  (estilo, formato y tablas)
import rutas  # noqa: E402

C = rutas.COMPLEMENTARIOS
DIMS, PARES = rr.DIMS, rr.PARES
esc, fmt, rho_html, tabla, kpis, pagina, guardar = rr.esc, rr.fmt, rr.rho_html, rr.tabla, rr.kpis, rr.pagina, rr.guardar


def leer(ruta):
    return pd.read_csv(ruta) if Path(ruta).exists() else pd.DataFrame()


def falta(texto):
    return f"<p class='vacio'>{texto}</p>"


# ── markdown mínimo, para los resumen.md de los scripts ──────────────────────

def _inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", s)


def markdown(texto, nivel_base=3):
    out, tabla_md, lista = [], [], []

    def cerrar():
        if tabla_md:
            filas = [f for f in tabla_md if not re.fullmatch(r"\|[\s:|-]+\|", f)]
            cab = [c.strip() for c in filas[0].strip("|").split("|")]
            cuerpo = ["<tr>" + "".join(f"<td>{_inline(c.strip())}</td>" for c in f.strip("|").split("|")) + "</tr>" for f in filas[1:]]
            out.append(tabla([_inline(c) for c in cab], cuerpo))
            tabla_md.clear()
        if lista:
            out.append("<ul>" + "".join(f"<li>{_inline(x)}</li>" for x in lista) + "</ul>")
            lista.clear()
    for linea in texto.splitlines():
        if linea.startswith("|"):
            if lista:
                cerrar()
            tabla_md.append(linea)
            continue
        if linea.startswith("- "):
            if tabla_md:
                cerrar()
            lista.append(linea[2:])
            continue
        cerrar()
        m = re.match(r"(#+)\s+(.*)", linea)
        if m:
            n = min(6, nivel_base + len(m.group(1)) - 1)
            out.append(f"<h{n} style='margin-top:18px'>{_inline(m.group(2))}</h{n}>")
        elif linea.strip():
            out.append(f"<p class='nota'>{_inline(linea)}</p>")
    cerrar()
    return "".join(out)


# ── piezas compartidas ────────────────────────────────────────────────────────

def sensibilidad_periodos(cruce):
    comp = leer(C / "periodos" / "comparacion.csv")
    if comp.empty:
        return falta("No se corrió la comparación de períodos (correlaciones.py --periodos ambos).")
    s = comp[comp.cruce == cruce]
    if s.empty:
        return falta("No hay pares de este cruce en la comparación.")
    cuenta = s.patron.value_counts()
    dos = int(cuenta.get("los dos", 0))
    solo_cal = int(sum(v for k, v in cuenta.items() if "calendario" in str(k)))
    solo_ep = int(sum(v for k, v in cuenta.items() if "época" in str(k) or "epoca" in str(k)))
    cal = [c for c in s.columns if c.startswith("cal_")]
    ep = [c for c in s.columns if c.startswith("ep_")]
    dif = s[s.patron.fillna("").str.contains("solo")]
    filas = [f"<tr><td>{esc(r['x'])} ↔ {esc(r['y'])}</td><td>{esc(r['patron'])}</td><td class='n'>{rho_html(r['rho_corregida'])}</td>"
             f"<td class='n tenue'>{' '.join(fmt(r[c]) for c in cal)}</td><td class='n tenue'>{' '.join(fmt(r[c]) for c in ep)}</td>"
             f"<td class='tenue'>{esc(r.get('motivo_cal') if isinstance(r.get('motivo_cal'), str) else (r.get('motivo_ep') if isinstance(r.get('motivo_ep'), str) else ''))}</td></tr>"
             for _, r in dif.iterrows()]
    return (kpis([(dos, "patrones con los dos cortes", "estables con el calendario y con las épocas"),
                  (solo_cal, "solo con el calendario", "dependen de cómo se corta la historia"),
                  (solo_ep, "solo con las épocas", "")])
            + "<p class='sub' style='margin-top:12px'>La regla de estabilidad pide el mismo signo en todos los períodos. Se repite con "
              "las épocas (tramos que salen de los datos) en lugar de los períodos de calendario (fijados antes de mirarlos).</p>"
            + tabla(["Par", "Con qué corte es patrón", "ρ", "Calendario", "Épocas", "Motivo"], filas, "Todos los patrones se sostienen con los dos cortes."))


def sensibilidad_cruce(a, b):
    comp = leer(C / "periodos" / f"{a.lower()}_{b.lower()}" / "comparacion_periodos.csv")
    if comp.empty:
        return falta("No se corrió el cruce con las épocas (cruces.py --periodos epocas).")
    nombres = {"pares_variables.csv": "Variables", "pares_componentes.csv": "Componentes", "pares_reducido.csv": "Conjunto reducido"}
    resumen = []
    for arch, t in nombres.items():
        s = comp[comp.archivo == arch]
        c = s.estado.value_counts()
        resumen.append(f"<tr><td>{t}</td><td class='n'>{int(c.get('firme', 0))}</td><td class='n'>{int(c.get('solo_calendario', 0))}</td>"
                       f"<td class='n'>{int(c.get('solo_epocas', 0))}</td></tr>")
    dif = comp[comp.estado != "firme"]
    cal = [c for c in comp.columns if c.startswith("cal_")]
    ep = [c for c in comp.columns if c.startswith("ep_")]
    filas = [f"<tr><td>{esc(nombres.get(r['archivo'], r['archivo']))}</td><td>{esc(r['x'])} ↔ {esc(r['y'])}</td>"
             f"<td>{esc(str(r['estado']).replace('_', ' ').replace('epocas', 'épocas'))}</td><td class='n'>{rho_html(r['rho_corregida'])}</td>"
             f"<td class='n tenue'>{' '.join(fmt(r[c]) for c in cal)}</td><td class='n tenue'>{' '.join(fmt(r[c]) for c in ep)}</td></tr>"
             for _, r in dif.iterrows()]
    return ("<p class='sub'>Los patrones del cruce (criterio de cruces.py) con la regla de estabilidad sobre los períodos de "
            "calendario y sobre las épocas. Firme: patrón con los dos cortes.</p>"
            + tabla(["Pares de", "Firmes", "Solo calendario", "Solo épocas"], resumen)
            + "<h3 style='margin-top:16px'>Los que dependen del corte</h3>"
            + tabla(["Pares de", "Par", "Con qué corte", "ρ", "Calendario", "Épocas"], filas, "Todos son firmes."))


# ── intradimensional ──────────────────────────────────────────────────────────

def vista_intra(dim):
    partes = [f"<h2>Sensibilidad a los períodos</h2>{sensibilidad_periodos(f'{dim}–{dim}')}"]

    ep = leer(C / "epocas_todas" / "epocas_por_dimension.csv")
    if not ep.empty:
        s = ep[ep.dimension == dim]
        filas = [f"<tr><td class='n'>{r.k}</td><td>{'toda la historia' if rr.verdadero(r.historia) else 'desde que hay datos de todas'}</td>"
                 f"<td>{esc(str(r.cortes).replace(' | ', ' · '))}</td></tr>" for r in s.itertuples()]
        partes.append("<h2>Épocas de la dimensión</h2><p class='sub'>Dónde cambian los niveles de las métricas de la dimensión: "
                      "segmentación contigua de los releases (Ward con restricción de contigüidad) sobre los valores sin ajustar.</p>"
                      + tabla(["Épocas", "Historia", "Cortes"], filas))
    else:
        partes.append("<h2>Épocas de la dimensión</h2>" + falta("No se corrió temporal.py epocas."))

    ck = leer(C / "clustering_temporal" / "clustering_k.csv")
    if not ck.empty:
        s = ck[ck.conjunto.str.startswith(f"{dim}/")]
        filas = [f"<tr><td>{esc(r.conjunto.split('/')[1])}</td><td>{esc(r.enfoque)}</td><td class='n'>{r.k}</td>"
                 f"<td class='n'>{fmt(r.silueta, 2, False)} <span class='tenue'>({fmt(r.nula_p95, 2, False)})</span></td>"
                 f"<td class='n'>{fmt(r.estabilidad_ari, 2, False)}</td><td class='n'>{fmt(r.persistencia, 2, False)} "
                 f"<span class='tenue'>({fmt(r.persistencia_nula_p95, 2, False)})</span></td><td class='tenue'>{esc(r.tamanos)}</td></tr>"
                 for r in s.itertuples()]
        partes.append("<h2>Agrupamiento temporal de releases</h2><p class='sub'>¿Hubo momentos en los que el proyecto se comportó igual? "
                      "k-means de releases (no de métricas), comparado con una nula por corrimiento circular. Entre paréntesis, el "
                      "percentil 95 de la nula. Persistencia: cuánto dura un release en el mismo grupo que el anterior.</p>"
                      + tabla(["Conjunto", "Enfoque", "k", "Silueta (nula)", "Estabilidad", "Persistencia (nula)", "Tamaños"], filas))
    est = leer(C / "clustering_temporal" / "estructura_periodos.csv")
    cam = leer(C / "clustering_temporal" / "estructura_cambios.csv")
    if not est.empty:
        s = est[est.conjunto.str.startswith(f"{dim}/") & (est.serie == "estable")]
        filas = [f"<tr><td>{esc(r.conjunto.split('/')[1])}</td><td>{esc(r.periodo_a)}</td><td>{esc(r.periodo_b)}</td><td class='n'>{fmt(r.similitud, 2, False)}</td></tr>"
                 for r in s.itertuples()]
        cambios = cam[cam.conjunto.str.startswith(f"{dim}/") & cam.cambia.map(rr.verdadero)] if not cam.empty else cam
        filas_c = [f"<tr><td>{esc(r.par)}</td><td>{esc(r.desde)} → {esc(r.hasta)}</td><td class='n'>{rho_html(r.rho_desde)} → {rho_html(r.rho_hasta)}</td>"
                   f"<td class='n'>{fmt(r.q, 3, False)}</td></tr>" for r in cambios.itertuples()]
        partes.append("<h2>Estructura en el tiempo</h2><p class='sub'>Similitud entre la matriz de correlaciones de cada período (1 = "
                      "la misma estructura), y los pares cuya correlación cambia de forma significativa entre el primer y el último período.</p>"
                      + tabla(["Conjunto", "Período", "Período", "Similitud"], filas)
                      + "<h3 style='margin-top:16px'>Pares que cambian</h3>" + tabla(["Par", "Períodos", "ρ", "q"], filas_c, "Ninguno cambia."))
    return pagina(f"Complementarios · {dim}", f"{esc(rutas.proyecto.REPO)} · correlaciones.py --periodos ambos y complementarios/temporal.py · no son técnica principal",
                  "".join(partes))


# ── bidimensional ─────────────────────────────────────────────────────────────

def vista_bi(a, b):
    base = f"{a.lower()}_{b.lower()}"
    partes = []
    md = C / "alternativos" / base / "resumen.md"
    if md.exists():
        texto = md.read_text(encoding="utf-8")
        secciones = re.split(r"\n(?=## )", texto, maxsplit=1)
        partes.append("<h2>Técnicas alternativas</h2><p class='sub'>Otras técnicas habituales para buscar patrones, con un criterio "
                      "fijado de antemano para decir si aportan: distinguirse de una nula que respeta el tiempo, repetirse en canary y "
                      "encontrar algo que el análisis principal no haya encontrado.</p>" + markdown(secciones[0], 3)
                      + (f"<details><summary>Detalle por método</summary>{markdown(secciones[1], 3)}</details>" if len(secciones) > 1 else ""))
    else:
        partes.append("<h2>Técnicas alternativas</h2>" + falta("No se corrió complementarios/cruce_alternativos.py."))

    pc = leer(C / "pesos_catalogo" / "patrones_cruces.csv")
    if not pc.empty:
        s = pc[pc.cruce == base]
        dep = int(s.depende_de_asignacion.map(rr.verdadero).sum())
        filas = [f"<tr><td>{esc(rr.nombre(r.x))} ↔ {esc(rr.nombre(r.y))}</td><td class='n'>{rho_html(r.rho)}</td>"
                 f"<td class='tenue'>{esc(r.dims_x)} / {esc(r.dims_y)}</td><td>{esc(r.dimension_comun if isinstance(r.dimension_comun, str) else '—')}</td>"
                 f"<td>{esc(r.composicion)}</td></tr>" for r in s.itertuples()]
        partes.append(f"<h2>Pertenencia ponderada</h2><p class='sub'>Cada variable cuenta para las dimensiones del catálogo en partes "
                      f"iguales. De {len(s)} patrones del cruce, {dep} dependen de la asignación: sus dos variables comparten una "
                      "dimensión y, con otra asignación, serían una relación dentro de ella.</p>"
                      + tabla(["Patrón", "ρ", "Catálogo", "Dimensión común", "Composición"], filas))
    else:
        partes.append("<h2>Pertenencia ponderada</h2>" + falta("No se corrió complementarios/pesos_catalogo.py."))

    partes.append(f"<h2>Sensibilidad a los períodos</h2>{sensibilidad_cruce(a, b)}")

    cd = leer(C / "clustering_temporal" / "cruce_dimensiones.csv")
    if not cd.empty:
        s = cd[cd.a.str.startswith(f"{a}/") & cd.b.str.startswith(f"{b}/")]
        filas = [f"<tr><td>{esc(r.a)}</td><td>{esc(r.b)}</td><td class='n'>{r.releases}</td><td class='n'>{fmt(r.v_cramer, 2, False)}</td>"
                 f"<td class='n'>{fmt(r.nula_p95, 2, False)}</td><td class='n'>{fmt(r.p, 3, False)}</td></tr>" for r in s.itertuples()]
        partes.append("<h2>Etapas en común</h2><p class='sub'>¿Los releases que se agrupan juntos en una dimensión también se agrupan "
                      "juntos en la otra? V de Cramér entre los dos agrupamientos temporales, frente a una nula por corrimiento circular.</p>"
                      + tabla(["Dimensión", "Dimensión", "Releases", "V de Cramér", "Nula p95", "p"], filas))

    if (a, b) == ("Proceso", "Producto"):
        rz = leer(C / "rezago" / "pares_rezago.csv")
        if not rz.empty:
            s = rz[(rz.k >= 1)]
            rob = s[s.robusta.map(rr.verdadero)].copy()
            rob = rob.reindex(rob.rho.abs().sort_values(ascending=False).index)
            filas = [f"<tr><td>{esc(rr.nombre(r.x))}</td><td>{esc(rr.nombre(r.y))}</td><td class='n'>{r.k}</td><td class='n'>{rho_html(r.rho)}</td>"
                     f"<td class='n'>{rho_html(r.canary)}</td><td class='n'>{rho_html(r.tamano)}</td>"
                     f"<td>{'sí' if rr.verdadero(r.resiste_tamano) else 'no'}</td></tr>" for r in rob.itertuples()]
            partes.append(f"<h2>Rezago</h2><p class='sub'>Una métrica en la ventana t contra otra en la ventana t + k (k = 1 a 3), en las dos "
                          f"direcciones. {len(s)} pares con rezago, {int(s.sig.map(rr.verdadero).sum())} significativos, {len(rob)} robustos.</p>"
                          + tabla(["Antes", "Después", "k", "ρ", "Canary", "Con tamaño", "Resiste tamaño"], filas, "Ningún par con rezago es robusto."))
        else:
            partes.append("<h2>Rezago</h2>" + falta("No se corrió complementarios/cruce_rezago.py."))
    return pagina(f"Complementarios · {a} – {b}", f"{esc(rutas.proyecto.REPO)} · analisis/complementarios · no son técnica principal", "".join(partes))


# ── tridimensional ────────────────────────────────────────────────────────────

def vista_tri():
    partes = []
    cc = leer(C / "pesos_catalogo" / "componentes_conjuntos.csv")
    md = C / "pesos_catalogo" / "resumen.md"
    if not cc.empty:
        filas = [f"<tr><td>{esc(r.enfoque)}</td><td class='n'>CP{r.componente}</td><td class='n'>{rr.pct(r.varianza)}</td>"
                 f"<td>{esc(r.ponderada)}<div class='tenue' style='font-size:12px'>{esc(r.tipo_ponderada)}</div></td>"
                 f"<td>{esc(r.asignada)}<div class='tenue' style='font-size:12px'>{esc(r.tipo_asignada)}</div></td>"
                 f"<td>{'sí' if rr.verdadero(r.escala) else 'no'}</td><td style='font-size:12.5px' class='tenue'>{esc(r.variables)}</td></tr>"
                 for r in cc.itertuples()]
        factor = ""
        if md.exists():
            sec = re.split(r"\n(?=## )", md.read_text(encoding="utf-8"))
            tres = [x for x in sec if x.startswith("## 3")]
            factor = markdown(tres[0], 3) if tres else ""
        partes.append("<h2>Composición según el catálogo</h2><p class='sub'>PCA de todas las variables de las tres dimensiones sin "
                      "decir de qué lado es cada una; después, cuánto aporta cada dimensión a cada componente, repartiendo cada "
                      "variable en partes iguales entre sus dimensiones (ponderada) o según la asignación de los cruces (asignada).</p>"
                      + tabla(["Enfoque", "", "Varianza", "Ponderada", "Asignada", "Escala", "Variables"], filas) + factor)
    else:
        partes.append("<h2>Composición según el catálogo</h2>" + falta("No se corrió complementarios/pesos_catalogo.py."))

    seg = leer(C / "epocas_todas" / "segmentacion_k.csv")
    if not seg.empty:
        filas = [f"<tr><td>{esc(r.conjunto)}</td><td class='n'>{r.k}</td><td class='n'>{fmt(r.r2, 2, False)} <span class='tenue'>({fmt(r.r2_nula_p95, 2, False)})</span></td>"
                 f"<td class='n'>{fmt(r.ari_calendario, 2, False)}</td><td class='n'>{fmt(r.ari_canary, 2, False)}</td>"
                 f"<td class='n'>{fmt(r.ari_persona, 2, False)} · {fmt(r.ari_proceso, 2, False)} · {fmt(r.ari_producto, 2, False)}</td>"
                 f"<td style='font-size:12.5px'>{esc(str(r.cortes).replace(' | ', ' · '))}</td></tr>" for r in seg.itertuples()]
        partes.append("<h2>Épocas con todas las métricas</h2><p class='sub'>Segmentación contigua de la historia con las métricas de las "
                      "tres dimensiones. R² frente a la nula (entre paréntesis), coincidencia con los períodos de calendario, con la "
                      "segmentación de canary y con la de cada dimensión (Persona · Proceso · Producto).</p>"
                      + tabla(["Conjunto", "k", "R² (nula)", "Con el calendario", "Con canary", "Con cada dimensión", "Cortes"], filas))
    else:
        partes.append("<h2>Épocas con todas las métricas</h2>" + falta("No se corrió complementarios/temporal.py epocas."))

    ck = leer(C / "clustering_temporal" / "clustering_k.csv")
    rc_ = leer(C / "clustering_temporal" / "replica_canary.csv")
    if not ck.empty:
        s = ck[ck.conjunto.str.lower().str.startswith("conjunto")]
        filas = [f"<tr><td>{esc(r.conjunto)}</td><td>{esc(r.enfoque)}</td><td class='n'>{r.k}</td>"
                 f"<td class='n'>{fmt(r.silueta, 2, False)} <span class='tenue'>({fmt(r.nula_p95, 2, False)})</span></td>"
                 f"<td class='n'>{fmt(r.estabilidad_ari, 2, False)}</td><td class='n'>{fmt(r.persistencia, 2, False)}</td></tr>" for r in s.itertuples()]
        rep = rc_[rc_.conjunto.str.lower().str.startswith("conjunto")] if not rc_.empty else rc_
        filas_r = [f"<tr><td>{esc(r.conjunto)}</td><td>{esc(r.enfoque)}</td><td class='n'>{r.k}</td><td class='n'>{fmt(r.ari, 3, False)}</td>"
                   f"<td class='n'>{fmt(r.nula_p95, 3, False)}</td><td class='n'>{fmt(r.p, 3, False)}</td></tr>" for r in rep.itertuples()]
        partes.append("<h2>Agrupamiento temporal conjunto</h2><p class='sub'>Releases agrupados con las métricas de las tres dimensiones.</p>"
                      + tabla(["Conjunto", "Enfoque", "k", "Silueta (nula)", "Estabilidad", "Persistencia"], filas)
                      + "<h3 style='margin-top:16px'>Réplica en canary</h3>"
                      + tabla(["Conjunto", "Enfoque", "k", "ARI", "Nula p95", "p"], filas_r))
    return pagina("Complementarios · tres dimensiones", f"{esc(rutas.proyecto.REPO)} · analisis/complementarios · no son técnica principal", "".join(partes))


def main():
    rr.NOMBRES = rr.rc.nombres_variables()
    for d in DIMS:
        guardar(rutas.REPORTES_DIMENSIONES, f"{d.lower()}_complementarios.html", vista_intra(d))
    for a, b in PARES:
        guardar(rutas.REPORTES_CRUCES, f"{a.lower()}_{b.lower()}_complementarios.html", vista_bi(a, b))
    guardar(rutas.REPORTES_TRES, "complementarios.html", vista_tri())


if __name__ == "__main__":
    main()
