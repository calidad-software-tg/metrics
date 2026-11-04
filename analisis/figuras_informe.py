"""Figuras de los capítulos 4 y 5 del informe, generadas solo desde analisis/salidas/.

Uso:
    python3 analisis/figuras_informe.py            # todas las que tienen datos
    python3 analisis/figuras_informe.py --solo 3,6,19

Cada figura lee las salidas del análisis (rama analisis) y no recalcula nada. Cuando un número de los datos no
coincide con el que afirma el texto de los capítulos, la figura se genera igual con el dato real y la diferencia
queda anotada en analisis/salidas/figuras/diferencias_automaticas.md (la explicación está en diferencias.md).
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figuras import estilo as E  # noqa: E402

S = E.SALIDAS
DIFERENCIAS = []      # (figura, mensaje)
ESTADO = {}           # figura -> (archivo, sección, fuente, estado)


def dif(fig, etiqueta, obtenido, esperado, tol=0.0):
    m = E.chequear(etiqueta, obtenido, esperado, tol)
    if m:
        DIFERENCIAS.append((fig, m))


def clave(par):
    return "|".join(sorted(par))


# ── datos ────────────────────────────────────────────────────────────────────
def patrones():
    p = pd.read_csv(S / "relaciones" / "patrones.csv")
    p["clave"] = [clave((a, b)) for a, b in zip(p.x, p.y)]
    return p


def base():
    b = pd.read_csv(S / "relaciones" / "base" / "pares_correlacion.csv", low_memory=False)
    b = b.drop_duplicates("par_id")
    b["clave"] = [clave((a, c)) for a, c in zip(b.x_id, b.y_id)]
    return b.set_index("clave")


def familias(p):
    f = pd.read_csv(Path(__file__).resolve().parent / "figuras" / "familias.csv")
    f["clave"] = [clave((a, b)) for a, b in zip(f.var_a, f.var_b)]
    idx = p.set_index("clave")
    f["es_patron"] = [bool(idx.loc[k, "patron"]) if k in idx.index else False for k in f.clave]
    f["motivo"] = [idx.loc[k, "motivo"] if k in idx.index else "no existe" for k in f.clave]
    return f


def evaluados(p):
    return p[p.categoria != "control"]


# ── Fig. 3 · embudo ──────────────────────────────────────────────────────────
def embudo(ax, escalones, perdidas, color_final):
    n0 = escalones[0][1]
    for i, (lab, n) in enumerate(escalones):
        w = max(n / n0, 0.012)
        c = color_final if i == len(escalones) - 1 else E.OSCURO
        ax.barh(-i, w, left=(1 - w) / 2, height=0.62, color=c, edgecolor="white", linewidth=0)
        ax.text(-0.02, -i, lab, ha="right", va="center", fontsize=9)
        dentro = w > 0.12
        ax.text(0.5 if dentro else (1 + w) / 2 + 0.012, -i, E.entero(n), ha="center" if dentro else "left", va="center",
                fontsize=9, color="white" if dentro else "#111111", fontweight="bold")
        if i < len(perdidas) and perdidas[i]:
            ax.text(1.03, -i - 0.5, perdidas[i], ha="left", va="center", fontsize=8, color=E.TEXTO2)
    ax.set_xlim(0, 1)
    ax.set_ylim(-len(escalones) + 0.4, 0.6)
    ax.axis("off")


def fig03():
    p = patrones()
    ev = evaluados(p)
    sig = ev[ev.categoria.isin(["positiva", "negativa"])]
    rob = sig[sig.robusta]
    m = rob.motivo.fillna("")
    escala, no_tam = (m == "escala").sum(), (m == "no resiste tamaño").sum()
    res_tam = rob[~m.isin(["escala", "no resiste tamaño"])]
    mec = (res_tam.motivo.fillna("") == "mecánico").sum()
    sin_mec = res_tam[res_tam.motivo.fillna("") != "mecánico"]
    valid = sin_mec.motivo.fillna("").str.startswith("descartado al validar").sum()
    pat = int(p.patron.sum())
    esc = [("Pares evaluados", len(ev)), ("Significativos", len(sig)), ("Robustos", len(rob)),
           ("Resisten el tamaño", len(res_tam)), ("Sin explicación mecánica", len(sin_mec)), ("Patrones", pat)]
    for (lab, n), t in zip(esc, [1368, 268, 159, 86, 72, 57]):
        dif("Fig. 3", lab, n, t)
    perd = [f"−{E.entero(len(ev) - len(sig))} no significativos", f"−{len(sig) - len(rob)} no robustos",
            f"−{escala} de escala y −{no_tam} que no resisten el tamaño", f"−{mec} mecánicos (definiciones superpuestas)",
            f"−{valid} descartados al validar"]
    perd = [s.replace("−", E.MENOS) for s in perd]
    fig, ax = plt.subplots(figsize=(E.ANCHO, 6.2 * E.CM))
    embudo(ax, esc, perd, E.ROJO)
    E.guardar(fig, "fig03_embudo")
    return "hecha"


# ── Fig. 14 · patrones por par ───────────────────────────────────────────────
PARES = ["Persona–Proceso", "Persona–Producto", "Proceso–Producto"]


def conteo_pares(p):
    pat = p[p.patron]
    out = {}
    for par in PARES:
        con = pat[pat.entre.fillna("").str.contains(par)]
        solo = con[con.tipo == "entre dimensiones"]
        out[par] = (len(con), len(solo), len(con) - len(solo))
    return out, pat


def fig14():
    p = patrones()
    c, pat = conteo_pares(p)
    texto = {"Persona–Proceso": (27, 5, 22), "Persona–Producto": (20, 13, 7), "Proceso–Producto": (17, 8, 9)}
    for par in PARES:
        for lab, a, b in zip(("total", "solo entre", "también dentro"), c[par], texto[par]):
            dif("Fig. 14", f"{par} {lab}", a, b)
    entre = pat[pat.entre.notna()]
    dif("Fig. 14", "patrones entre dimensiones", len(entre), 42)
    dif("Fig. 14", "solo entre dimensiones", (entre.tipo == "entre dimensiones").sum(), 16)
    fig, ax = plt.subplots(figsize=(E.ANCHO, 4.6 * E.CM))
    for i, par in enumerate(PARES):
        tot, solo, tamb = c[par]
        col = E.OSCURO
        ax.barh(-i, solo, color=col, height=0.55, edgecolor="white", linewidth=1.5)
        ax.barh(-i, tamb, left=solo, color=col, height=0.55, edgecolor="white", linewidth=1.5, hatch="///", alpha=0.3)
        ax.text(solo / 2, -i, str(solo), ha="center", va="center", color="white", fontweight="bold")
        ax.text(solo + tamb / 2, -i, str(tamb), ha="center", va="center", color="#111111")
        ax.text(tot + 0.4, -i, f"{tot} patrones", va="center", fontsize=8, color=E.TEXTO2)
    ax.set_yticks(-np.arange(3), PARES)
    ax.set_xlabel("Patrones que pueden conectar el par")
    ax.set_xlim(0, max(v[0] for v in c.values()) * 1.18)
    ax.legend(handles=[Patch(facecolor=E.OSCURO, label="Solo entre dimensiones"),
                       Patch(facecolor=E.OSCURO, alpha=0.3, hatch="///", label="También dentro de una dimensión")],
              loc="lower right", ncol=1)
    E.guardar(fig, "fig14_patrones_por_par")
    return "hecha"


# ── gráfico de bosque estándar ───────────────────────────────────────────────
def bosque(filas, archivo, ancho=E.ANCHO, color_fila=None, extra=None):
    """filas: lista de (grupo, etiqueta, clave). extra: dict clave -> (rho, etiqueta) para filas recalculadas."""
    b = base()
    p = patrones().set_index("clave")
    alto = (0.52 * len(filas) + 0.45 * len({g for g, _, _ in filas}) + 1.4) * E.CM
    fig, ax = plt.subplots(figsize=(ancho, alto))
    y, ticks, labs, grupo_prev = 0, [], [], None
    for g, lab, k in filas:
        if g != grupo_prev:
            y -= 0.35
            ax.text(-1.0, y, g, ha="left", va="center", fontsize=8.5, fontweight="bold", transform=ax.get_yaxis_transform())
            y -= 0.75
            grupo_prev = g
        if isinstance(k, tuple) and k[0] == "extra":
            r, _ = extra[k[1]]
            ax.plot(r, y, "s", color="black", ms=4.5, mfc="white", mew=1)
        else:
            r, lo, hi = p.loc[k, "rho"], b.loc[k, "ic_inf"], b.loc[k, "ic_sup"]
            c = color_fila(k) if color_fila else "black"
            ax.plot([lo, hi], [y, y], color=c, lw=1.1, solid_capstyle="butt")
            ax.plot(r, y, "o", color=c, ms=4.5)
            ax.plot(p.loc[k, "rho_canary"], y, "D", ms=4.2, mfc="white", mec=c, mew=0.9)
            ax.plot(p.loc[k, "rho_tamano"], y, "^", ms=4.8, mfc="white", mec=c, mew=0.9)
        ax.text(1.005, y, E.rho(r), transform=ax.get_yaxis_transform(), va="center", fontsize=8, color=E.TEXTO2)
        ticks.append(y)
        labs.append(lab)
        y -= 1
    ax.axvline(0, color=E.DESCARTE, lw=0.8, zorder=0)
    ax.set_yticks(ticks, labs, fontsize=8.5)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_ylim(y + 0.4, 0.2)
    ax.set_xlim(-0.8, 0.8)
    for v in (-0.5, 0.5):
        ax.axvline(v, color=E.GUIA, lw=0.5, zorder=0)
    E.eje_rho(ax)
    ax.set_xlabel("ρ parcial de Spearman")
    h = [Line2D([], [], marker="o", color="black", lw=1.1, ms=4.5, label="Serie estable (IC 95 %)"),
         Line2D([], [], marker="D", ls="", mfc="white", mec="black", ms=4.2, label="Canary"),
         Line2D([], [], marker="^", ls="", mfc="white", mec="black", ms=4.8, label="Con control por tamaño")]
    if extra:
        h.append(Line2D([], [], marker="s", ls="", mfc="white", mec="black", ms=4.5, label="Sin recién llegados"))
    alto_ejes = alto * (fig.subplotpars.top - fig.subplotpars.bottom)
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -1.05 * E.CM / alto_ejes), ncol=len(h), handletextpad=0.3)
    E.guardar(fig, archivo)


def filas_familias(fams, titulo):
    p = patrones()
    f = familias(p)
    out, faltan = [], []
    for fam in fams:
        sub = f[f.familia == fam]
        for _, r in sub.iterrows():
            if not r.es_patron:
                faltan.append(f"familia {fam}: {E.par(r.var_a, r.var_b)} no es patrón en los datos ({r.motivo})")
                continue
            out.append((f"Familia {fam}. {titulo.get(fam, r.nombre)}", E.par(r.var_a, r.var_b), r.clave))
    return out, faltan


def fig06():
    filas, faltan = filas_familias("ABC", {"A": "Participación en el código y concentración del núcleo",
                                          "B": "Participación en el cierre de issues y revisores más activos",
                                          "C": "Participación en el código y experiencia"})
    for m in faltan:
        DIFERENCIAS.append(("Fig. 6", m))
    extra = {}
    v = validacion_experiencia()
    if v is not None:
        for var in ("le_mediana", "dev_exp_mediana"):
            k = clave(("prop_commitean_ratio", var))
            if k in v:
                extra[var] = (v[k], "")
                filas.append(("Familia C. Participación en el código y experiencia",
                              E.par("prop_commitean_ratio", var) + " (sin recién llegados)", ("extra", var)))
    if not extra:
        DIFERENCIAS.append(("Fig. 6", "no hay salida de validación con las medianas de experiencia sin recién llegados "
                                      "frente a la proporción que commitea: la figura va sin esas dos filas"))
    bosque(filas, "fig06_bosque_ABC", extra=extra or None)
    return "hecha" if extra else "hecha (sin las filas recalculadas sin recién llegados: falta la validación)"


def fig12():
    filas, faltan = filas_familias("GH", {"G": "Resolver lo nuevo y cerrar lo viejo",
                                         "H": "Issues de documentación y ritmo de las issues"})
    for m in faltan:
        DIFERENCIAS.append(("Fig. 12", m))
    bosque(filas, "fig12_bosque_proceso")
    return "hecha"


def fig15():
    p = patrones().set_index("clave")
    filas, faltan = filas_familias("OP", {"O": "Concentración del núcleo y documentación",
                                         "P": "Participación en el cierre de issues y resolución de lo nuevo"})
    for m in faltan:
        DIFERENCIAS.append(("Fig. 15", m))

    filas = [(g, f"{lab} [{' o '.join(str(p.loc[k, 'entre']).split('; '))}]", k) for g, lab, k in filas]
    bosque(filas, "fig15_bosque_entre_dimensiones")
    return "hecha (familias O y P: confirmar que son «las dos desarrolladas»)"


# ── Fig. 19 y 19b · la cadena de tres dimensiones ────────────────────────────
CONC = ["exprev_share_top10pct", "nc_share_top10pct", "sc_p90"]


def cadenas():
    t = pd.read_csv(S / "relaciones" / "triangulos.csv")
    t = t[(t.tipo == "cadena") & t.variables.str.contains("prop_commitean_ratio") & t.variables.str.contains("dloc_flujo_producto")]
    out = []
    for _, r in t.iterrows():
        c = next(v for v in CONC if v in r.variables)
        lados = {}
        for i in (1, 2, 3):
            a, b = r[f"lado{i}"].split(" ↔ ")
            lados[clave((a, b))] = (r[f"lado{i}_rho"], r[f"lado{i}_sin_tercero"])
        out.append((c, lados, r.desaparece_al_descontar))
    return sorted(out, key=lambda z: CONC.index(z[0]))


def fig19():
    cs = cadenas()
    dif("Fig. 19", "versiones de la cadena (EXPRev, NC, SC p90)", len(cs), 3)
    pc = [l[clave(("prop_commitean_ratio", c))][0] for c, l, _ in cs]
    cd = [l[clave(("dloc_flujo_producto", c))][0] for c, l, _ in cs]
    dd = [l[clave(("dloc_flujo_producto", "prop_commitean_ratio"))] for c, l, _ in cs]
    dif("Fig. 19", "lado Persona–Proceso mín", round(min(pc), 2), 0.43)
    dif("Fig. 19", "lado Persona–Proceso máx", round(max(pc), 2), 0.47)
    dif("Fig. 19", "lado Proceso–Producto mín", round(min(cd), 2), 0.20)
    dif("Fig. 19", "lado Proceso–Producto máx", round(max(cd), 2), 0.29)
    dif("Fig. 19", "lado directo", round(dd[0][0], 2), 0.21)
    dif("Fig. 19", "lado directo sin el tercero mín", round(min(d[1] for d in dd), 2), 0.08)
    dif("Fig. 19", "lado directo sin el tercero máx", round(max(d[1] for d in dd), 2), 0.13)
    for c, l, quita in cs:
        otros = [s for s in quita.split("; ") if "prop_commitean_ratio" not in s or "dloc" not in s]
        if otros:
            DIFERENCIAS.append(("Fig. 19", f"con {E.nombre(c)} también desaparece al descontar el tercero: {', '.join(otros)} "
                                           "(el texto dice que los otros dos lados casi no cambian)"))
    fig, ax = plt.subplots(figsize=(E.ANCHO, 6.8 * E.CM))
    nodos = {"Persona": (0.0, 0.0, "Proporción\nque commitea"),
             "Proceso": (1.5, 0.0, "Concentración del núcleo\n(EXPRev y NC del 10 %\nmás activo; SC p90)"),
             "Producto": (3.0, 0.0, "DLOC 2.0 (líneas de\ndocumentación cambiadas)")}
    for d, (x, y, lab) in nodos.items():
        ax.add_patch(plt.Circle((x, y), 0.24, color=E.DIM[d], zorder=3))
        ax.text(x, y, d, ha="center", va="center", color="white", fontsize=8.5, fontweight="bold", zorder=4)
        ax.text(x, y + 0.3, lab, ha="center", va="bottom", fontsize=8.5)
    rng = lambda v: f"{E.rho(min(v))} a {E.rho(max(v))}"
    for (a, b, txt) in [(0, 1.5, rng(pc)), (1.5, 3, rng(cd))]:
        ax.plot([a + 0.24, b - 0.24], [0, 0], color="#222222", lw=2.2, zorder=2, solid_capstyle="butt")
        ax.text((a + b) / 2, 0.05, "ρ " + txt, ha="center", va="bottom", fontsize=8.5)
    arco = FancyArrowPatch((0.12, -0.17), (2.88, -0.17), connectionstyle="arc3,rad=0.25", arrowstyle="-",
                           ls=(0, (3, 2.5)), lw=1.4, color=E.TEXTO2, zorder=1)
    ax.add_patch(arco)
    sin = [d[1] for d in dd]
    ax.text(1.5, -0.66, f"Relación directa: ρ {E.rho(dd[0][0])} → {E.rho(min(sin))} a {E.rho(max(sin))} "
                        "al descontar la concentración del núcleo", ha="center", va="top", fontsize=8.5, color=E.TEXTO2)
    ax.set_xlim(-0.5, 3.5)
    ax.set_ylim(-0.85, 0.85)
    ax.set_aspect("equal")
    ax.axis("off")
    E.guardar(fig, "fig19_cadena")
    return "hecha"


def fig19b():
    cs = cadenas()
    tipo = {clave(("prop_commitean_ratio", "C")): ("Persona", "Proceso")}
    fig, ax = plt.subplots(figsize=(E.ANCHO, 8.4 * E.CM))
    y, ticks, labs = 0, [], []
    for c, l, _ in cs:
        y -= 0.3
        ax.text(-0.02, y, f"Versión con {E.nombre(c)}", transform=ax.get_yaxis_transform(), ha="right", va="center",
                fontsize=8.5, fontweight="bold")
        y -= 0.8
        for (a, b), dims, lab in [(("prop_commitean_ratio", c), ("Persona", "Proceso"), f"Proporción que commitea ↔ {E.nombre(c)}"),
                                  (("dloc_flujo_producto", c), ("Proceso", "Producto"), f"{E.nombre(c)} ↔ DLOC 2.0"),
                                  (("dloc_flujo_producto", "prop_commitean_ratio"), ("Persona", "Producto"), "Proporción que commitea ↔ DLOC 2.0 (directa)")]:
            r0, r1 = l[clave((a, b))]
            col = E.DESCARTE if abs(r1) <= 0.15 else "#222222"
            lab = f"{lab} [{dims[0]}–{dims[1]}]"
            ax.plot([r0, r1], [y, y], color=col, lw=1.6, zorder=2)
            ax.plot(r0, y, "o", color=col, ms=5.5, zorder=3)
            ax.plot(r1, y, "o", mfc="white", mec=col, mew=1.3, ms=5.5, zorder=3)
            ax.text(max(r0, r1) + 0.015, y, f"{E.rho(r0)} → {E.rho(r1)}", va="center", fontsize=8, color=E.TEXTO2)
            ticks.append(y)
            labs.append(lab)
            y -= 1
    ax.axvspan(-0.15, 0.15, color="#f3f3f3", zorder=0)
    ax.axvline(0, color=E.DESCARTE, lw=0.8, zorder=1)
    ax.set_yticks(ticks, labs, fontsize=8.5)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(-0.2, 0.62)
    ax.set_ylim(y + 0.4, 0.2)
    E.eje_rho(ax)
    ax.set_xlabel("ρ parcial de Spearman")
    h = [Line2D([], [], marker="o", ls="", color="#222222", ms=5.5, label="Original"),
         Line2D([], [], marker="o", ls="", mfc="white", mec="#222222", ms=5.5, label="Descontando el tercer elemento"),
         Line2D([], [], color=E.DESCARTE, lw=2, label="Cae a ±0,15 o menos"),
         Patch(color="#f3f3f3", label="Banda ±0,15")]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.3, -0.13), ncol=2, fontsize=8)
    E.guardar(fig, "fig19b_cadena_mancuernas")
    return "hecha"


# ── Fig. 2 · variables por dimensión ─────────────────────────────────────────
DIMS = ["Persona", "Proceso", "Producto"]


def fig02():
    p = patrones()
    d = pd.read_csv(S / "diccionario_variables.csv").set_index("variable_id")
    ids = sorted(set(p.x) | set(p.y))
    dif("Fig. 2", "variables en la búsqueda", len(ids), 54)
    dims = {v: [D for D in DIMS if d.loc[v, f"dim_{D.lower()}"] == 1] for v in ids}
    fig, ax = plt.subplots(figsize=(E.ANCHO, 4.8 * E.CM))
    for i, D in enumerate(DIMS):
        solo = sum(1 for v in ids if dims[v] == [D])
        left = 0
        ax.barh(-i, solo, color=E.DIM[D], height=0.55, edgecolor="white", linewidth=1.5)
        ax.text(solo / 2, -i, str(solo), ha="center", va="center", color="white", fontweight="bold")
        left = solo
        for O in DIMS:
            if O == D:
                continue
            n = sum(1 for v in ids if set(dims[v]) == {D, O})
            if not n:
                continue
            ax.barh(-i, n, left=left, color="white", height=0.55, edgecolor=E.DIM[O], hatch="////", linewidth=0)
            ax.barh(-i, n, left=left, color="none", height=0.55, edgecolor="white", linewidth=1.5)
            ax.text(left + n / 2, -i, str(n), ha="center", va="center", fontsize=8.5,
                    bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none"))
            left += n
        ax.text(left + 0.4, -i, f"{left} variables", va="center", fontsize=8, color=E.TEXTO2)
    ax.set_yticks(-np.arange(3), DIMS)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Variables que entran en la búsqueda de relaciones")
    ax.set_xlim(0, ax.get_xlim()[1] * 1.12)
    h = [Patch(facecolor="#888888", label="Solo esa dimensión (color de la barra)")] + [
        Patch(facecolor="white", edgecolor=E.DIM[O], hatch="////", label=f"Compartida con {O}") for O in DIMS]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=4)
    E.guardar(fig, "fig02_variables_por_dimension")
    return "hecha"


# ── Fig. 7 · estabilidad de A, B y C ─────────────────────────────────────────
def fig07():
    p = patrones().set_index("clave")
    ep = pd.read_csv(S / "relaciones" / "base_epocas" / "pares_correlacion.csv", low_memory=False).drop_duplicates("par_id")
    ep["clave"] = [clave((a, b)) for a, b in zip(ep.x_id, ep.y_id)]
    ep = ep.set_index("clave")
    # en la corrida por épocas, las columnas de período guardan las épocas 1 a 4 (correlaciones.py, NOMBRES["epocas"])
    cols_ep = ["rho_2016_2019", "rho_2020_2022", "rho_2023_2024", "rho_2025_2026"]
    filas, _ = filas_familias("ABC", {})
    M, labs, fam = [], [], []
    for g, lab, k in filas:
        cal = [p.loc[k, c] for c in ("rho_2016_2019", "rho_2020_2022", "rho_2023_2024", "rho_2025_2026")]
        epo = [ep.loc[k, c] if k in ep.index else np.nan for c in cols_ep]
        M.append(cal + epo)
        labs.append(lab)
        fam.append(g.split(".")[0])
    M = np.array(M, float)
    # familia B: cuántas cambian de signo en la época 2
    sig = [np.sign(M[i, 5]) != np.sign(p.loc[k, "rho"]) for i, (g, _, k) in enumerate(filas) if g.startswith("Familia B")]
    dif("Fig. 7", "relaciones de la familia B que cambian de signo en la época 2", int(sum(sig)), 3)
    fig, ax = plt.subplots(figsize=(E.ANCHO, (0.62 * len(labs) + 2.2) * E.CM))
    x = [0, 1, 2, 3, 4.4, 5.4, 6.4, 7.4]
    for i in range(M.shape[0]):
        for j in range(8):
            v = M[i, j]
            if np.isnan(v):
                ax.add_patch(plt.Rectangle((x[j] - 0.48, -i - 0.45), 0.96, 0.9, fc="white", ec=E.GUIA, lw=0.5))
                ax.text(x[j], -i, "—", ha="center", va="center", fontsize=8, color=E.TEXTO2)
                continue
            c = E.CMAP_RHO((np.clip(v, -0.8, 0.8) + 0.8) / 1.6)
            ax.add_patch(plt.Rectangle((x[j] - 0.48, -i - 0.45), 0.96, 0.9, fc=c, ec="white", lw=1))
            ax.text(x[j], -i, E.rho(v), ha="center", va="center", fontsize=7.5, color="white" if abs(v) > 0.55 else "#111111")
    ax.axvline(3.7, color="#333333", lw=0.8)
    for i in range(1, len(fam)):
        if fam[i] != fam[i - 1]:
            ax.axhline(-i + 0.5, color="#333333", lw=0.6)
    ax.set_xticks(x, ["2016–19", "2020–22", "2023–24", "2025–26", "Época 1", "Época 2", "Época 3", "Época 4"], fontsize=8)
    ax.xaxis.tick_top()
    ax.set_yticks(-np.arange(len(labs)), [f"{f[-1]} · {l}" for f, l in zip(fam, labs)], fontsize=8)
    ax.tick_params(length=0)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xlim(-0.55, 7.95)
    ax.set_ylim(-len(labs) + 0.45, 0.55)
    ax.text(1.5, 1.55, "Períodos de calendario", ha="center", fontsize=8.5, transform=ax.transData)
    ax.text(5.9, 1.55, "Épocas (cortes v9.1.7, v12.0.5 y v14.1.1)", ha="center", fontsize=8.5, transform=ax.transData)
    E.guardar(fig, "fig07_estabilidad_ABC")
    return "hecha"


# ── Fig. 15b · embudos de componentes y grupos ───────────────────────────────
def bloques():
    return pd.read_csv(S / "bloques_etiquetas" / "pares.csv")


def fig15b():
    b = bloques()
    fig, axs = plt.subplots(2, 1, figsize=(E.ANCHO, 9.5 * E.CM), gridspec_kw={"hspace": 0.35})
    texto = {"componente": [33, 10, 9, 7, 5, 4], "grupo": [125, 36, 26, None, 17, 15]}
    for ax, tipo, tit in zip(axs, ("componente", "grupo"), ("Componentes del PCA", "Grupos del clustering")):
        g = b[b.tipo_elemento == tipo]
        ev = g[g.evaluado == True]
        m = ev.motivo.fillna("")
        sig = ev[~m.isin(["no_concluyente", "sin_relacion"])]
        rob = sig[sig.robusta == True]
        ms = rob.motivo.fillna("")
        limpio = rob[~ms.isin(["escala", "mecánico", "no resiste tamaño"])]
        pat = g[g.patron == True]
        distinto = pat[pat.x_tema != pat.y_tema]
        n = [len(ev), len(sig), len(rob), len(limpio), len(pat), len(distinto)]
        for lab, a, t in zip(("evaluados", "significativos", "robustos", "sin escala ni mecánicos", "patrones",
                              "entre aspectos distintos"), n, texto[tipo]):
            if t is not None:
                dif("Fig. 15b", f"{tit}: {lab}", a, t)
        motivos = [f"{E.MENOS}{(ms == m_).sum()} {t_}" for m_, t_ in (("escala", "de escala"), ("mecánico", "mecánicos"),
                                                                      ("no resiste tamaño", "no resisten el tamaño")) if (ms == m_).sum()]
        if n[3] != n[4]:
            motivos.append(f"{E.MENOS}{n[3] - n[4]} otros")
        esc = [("Evaluados", n[0]), ("Significativos", n[1]), ("Robustos", n[2]), ("Patrones", n[4]),
               ("Entre aspectos distintos", n[5])]
        perd = [f"{E.MENOS}{n[0] - n[1]} no significativos", f"{E.MENOS}{n[1] - n[2]} no robustos", ", ".join(motivos),
                f"{E.MENOS}{n[4] - n[5]} del mismo aspecto"]
        if tipo == "grupo":
            esc[0] = (f"Evaluados (+{(g.evaluado == False).sum()} no evaluables)", n[0])
        embudo(ax, esc, perd, E.ROJO)
        ax.set_title(tit, loc="left", fontsize=9, fontweight="bold", x=-0.3)
    E.guardar(fig, "fig15b_embudo_componentes_grupos")
    return "hecha"


# ── Fig. 16 · componentes de las tres dimensiones ────────────────────────────
def fig16():
    b = bloques()
    c = b[b.tipo_elemento == "componente"].copy()
    c[["a", "b_"]] = c.par_id.str.split("__", expand=True)
    tema = {}
    for _, r in c.iterrows():
        tema[r.a], tema[r.b_] = r.x_tema, r.y_tema
    orden = sorted(tema, key=lambda e: (DIMS.index(e.split("_")[0].capitalize()), int(e.split("cp")[1])))
    n = len(orden)
    M = np.full((n, n), np.nan)
    pat = np.zeros((n, n), bool)
    for _, r in c.iterrows():
        i, j = orden.index(r.a), orden.index(r.b_)
        M[i, j] = M[j, i] = r.rho_corregida
        pat[i, j] = pat[j, i] = bool(r.patron) and r.x_tema != r.y_tema
    dif("Fig. 16", "patrones entre componentes de aspectos distintos", int(pat.sum() / 2), 4)
    fig, ax = plt.subplots(figsize=(E.ANCHO, 13 * E.CM))
    for i in range(n):
        for j in range(n):
            if i == j or np.isnan(M[i, j]):
                continue
            v = M[i, j]
            ax.add_patch(plt.Rectangle((j, -i), 1, 1, fc=E.CMAP_RHO((np.clip(v, -0.8, 0.8) + 0.8) / 1.6), ec="white", lw=1))
            ax.text(j + 0.5, -i + 0.5, E.rho(v), ha="center", va="center", fontsize=7, color="white" if abs(v) > 0.55 else "#111111")
            if pat[i, j]:
                ax.add_patch(plt.Rectangle((j + 0.04, -i + 0.04), 0.92, 0.92, fc="none", ec="black", lw=1.8))
    labs = [f"{tema[e]}" for e in orden]
    for k, e in enumerate(orden):
        col = E.DIM[e.split("_")[0].capitalize()]
        ax.add_patch(plt.Rectangle((-0.35, -k), 0.25, 1, fc=col, ec="white", clip_on=False))
        ax.add_patch(plt.Rectangle((k, 1.1), 1, 0.25, fc=col, ec="white", clip_on=False))
        ax.text(-0.45, -k + 0.5, labs[k], ha="right", va="center", fontsize=8)
        ax.text(k + 0.5, 1.45, labs[k], ha="left", va="bottom", fontsize=8, rotation=45, rotation_mode="anchor")
    ax.set_xlim(-0.4, n)
    ax.set_ylim(-n + 1, 1.4)
    ax.set_aspect("equal")
    ax.axis("off")
    h = [Patch(color=E.DIM[d], label=d) for d in DIMS] + [Patch(fc="white", ec="black", lw=1.8, label="Patrón")]
    ax.legend(handles=h, loc="upper left", bbox_to_anchor=(0.0, -0.01), ncol=4)
    E.guardar(fig, "fig16_componentes_tres_dimensiones")
    return "hecha"


# ── Fig. 17 · correlación canónica según la asignación ───────────────────────
def fig17():
    u = pd.read_csv(S / "multiverso_asignacion" / "universos.csv")
    dif("Fig. 17", "asignaciones", len(u), 518)
    azar = u[u.universo.str.startswith("azar")]
    texto = {"Persona–Proceso": (0.45, 0.54, 0.84, 100), "Persona–Producto": (0.61, 0.50, 0.73, 99),
             "Proceso–Producto": (0.33, 0.32, 0.71, 81)}
    fig, ax = plt.subplots(figsize=(E.ANCHO, 5 * E.CM))
    for i, par in enumerate(PARES):
        v = u[f"cca {par}"]
        p5, p95, med = np.percentile(v, 5), np.percentile(v, 95), v.median()
        prin = u.loc[u.universo == "principal", f"cca {par}"].iloc[0]
        pct_az = (azar[f"cca {par} p"] < 0.05).mean() * 100
        for lab, a, t in zip(("principal", "P5", "P95"), (prin, p5, p95), texto[par][:3]):
            dif("Fig. 17", f"{par} {lab}", round(a, 2), t)
        dif("Fig. 17", f"{par} % que supera al azar", round(pct_az), texto[par][3])
        ax.plot([p5, p95], [-i, -i], color="#c9c9c9", lw=9, solid_capstyle="butt", zorder=1)
        ax.plot([med, med], [-i - 0.17, -i + 0.17], color="#444444", lw=1.5, zorder=2)
        ax.plot(prin, -i, "o", color="black", ms=7, mec="white", mew=1.2, zorder=3)
        ax.text(prin, -i + 0.24, E.rho(prin, signo=False), ha="center", fontsize=8)
        ax.text(1.02, -i, E.pct(pct_az), transform=ax.get_yaxis_transform(), va="center", fontsize=9)
    ax.text(1.02, 0.5, "Supera\nal azar", transform=ax.get_yaxis_transform(), va="bottom", fontsize=8, color=E.TEXTO2)
    ax.set_yticks(-np.arange(3), PARES)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0.2, 1.0)
    ax.set_ylim(-2.5, 0.6)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: E.rho(v, 1, signo=False)))
    ax.set_xlabel("Primera correlación canónica")
    h = [Line2D([], [], color="#c9c9c9", lw=8, label=f"P5–P95 de las {len(u)} asignaciones"),
         Line2D([], [], color="#444444", lw=1.5, label="Mediana"),
         Line2D([], [], marker="o", ls="", color="black", ms=6, label="Asignación principal")]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=3)
    E.guardar(fig, "fig17_multiverso_asignacion")
    return "hecha"


# ── Fig. 18 · las tres dimensiones frente al azar ────────────────────────────
VARIANTES = [("todos", "Todas las variables"), ("sin_volumen", "Sin el componente de volumen"),
             ("sin_tamano", "Sin tamaño"), ("sin_tamano_ni_documentacion", "Sin tamaño ni documentación"),
             ("sin_tamano_ni_renovacion", "Sin tamaño ni renovación")]


def fig18():
    g = json.load(open(S / "tres_dimensiones" / "resumen.json"))["global_"]
    dif("Fig. 18", "GCCA", round(g["todos"]["gcca"], 2), 1.71)
    dif("Fig. 18", "GCCA P95 nula", round(g["todos"]["gcca_nula_p95"], 2), 1.44)
    dif("Fig. 18", "GCCA canary", round(g["todos_canary"]["gcca"], 2), 1.63)
    dif("Fig. 18", "GCCA canary P95", round(g["todos_canary"]["gcca_nula_p95"], 2), 1.12)
    dif("Fig. 18", "sin tamaño", round(g["sin_tamano"]["gcca"], 2), 1.58)
    dif("Fig. 18", "sin tamaño P95", round(g["sin_tamano"]["gcca_nula_p95"], 2), 1.38)
    dif("Fig. 18", "RV medio", round(g["todos"]["rv_medio"], 3), 0.098)
    dif("Fig. 18", "RV P95", round(g["todos"]["rv_medio_nula_p95"], 3), 0.031)
    dif("Fig. 18", "MFA 1.er factor %", round(g["todos"]["mfa1"] * 100), 24)
    dif("Fig. 18", "MFA P95 %", round(g["todos"]["mfa1_nula_p95"] * 100), 21)
    fig, axs = plt.subplots(1, 2, figsize=(E.ANCHO, 5.6 * E.CM), sharey=True, gridspec_kw={"wspace": 0.08})
    for ax, suf, tit in zip(axs, ("", "_canary"), ("Serie estable", "Serie canary")):
        for i, (k, lab) in enumerate(VARIANTES):
            d = g[k + suf]
            ax.barh(-i, d["gcca_nula_p95"] - 1, left=1, height=0.5, color="#e4e4e4", zorder=1)
            ax.plot(d["gcca"], -i, "o", color="black", ms=6, zorder=3)
            ax.text(d["gcca"] + 0.035, -i, f"{E.rho(d['gcca'], signo=False)} vs. {E.rho(d['gcca_nula_p95'], signo=False)}",
                    va="center", fontsize=7.5)
        ax.set_title(tit, fontsize=9)
        ax.set_xlim(1, 2.05)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: E.rho(v, 1, signo=False)))
        ax.set_xlabel("Correlación canónica generalizada")
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
    axs[0].set_yticks(-np.arange(len(VARIANTES)), [l for _, l in VARIANTES])
    h = [Line2D([], [], marker="o", ls="", color="black", ms=6, label="Valor observado"),
         Patch(color="#e4e4e4", label="Azar (corrimiento temporal) hasta el percentil 95")]
    fig.legend(handles=h, loc="lower center", bbox_to_anchor=(0.55, -0.2), ncol=2)
    E.guardar(fig, "fig18_tres_dimensiones_vs_azar")
    return "hecha"


# ── PCA y clustering (Figs. 9, 10 y 20) ──────────────────────────────────────
CONJ = {"Persona": "todas", "Proceso": "producto", "Producto": "producto"}   # los del análisis intradimensional (4.2)


def pca_dim(dim):
    """Resultado del PCA de la dimensión (serie estable, enfoque ajustado) con varianza rotada, tema y firmeza
    de cada componente, usando las mismas funciones del análisis (cruces.componentes, multiverso_asignacion.tema_de)."""
    import warnings
    warnings.filterwarnings("ignore")
    import cruces
    import multiverso_asignacion as mv
    d = json.load(open(S / "pca" / f"pca_{dim.lower()}.json"))
    r = d["resultados"][f"{CONJ[dim]}|estable|ajustado"]
    cfg = cruces.mezclar(cruces.DEFAULTS, {"componentes": {"conjunto": {dim: CONJ[dim]},
                                                           "elegir": {dim: list(range(1, r["k"] + 1))}}})
    cps = cruces.componentes(dim, cfg, {"versiones": {}, "versiones_canary": {}})
    L = np.array(r["varimax"], float)
    comps = []
    for c in cps:
        j = c["n"] - 1
        comps.append(dict(n=c["n"], firme=bool(c["firme"]), var_rot=float((L[:, j] ** 2).sum() / L.shape[0] * 100),
                          tema=mv.tema_de([(v, x) for v, x in c["cargas"] if abs(x) >= 0.4])))
    return r, L, comps


def fig09():
    r, L, comps = pca_dim("Persona")
    dif("Fig. 9", "componentes retenidos", len(comps), 5)
    dif("Fig. 9", "variación explicada %", round(sum(c["var_rot"] for c in comps)), 59)
    dif("Fig. 9", "componentes firmes", sum(c["firme"] for c in comps), 3)
    for c, t in zip(sorted(comps, key=lambda c: -c["var_rot"]), (16.5, 14.5, 12.1, 10.3, 5.9)):
        dif("Fig. 9", f"varianza rotada CP{c['n']} ({c['tema']})", round(c["var_rot"], 1), t)
    orden_c = sorted(range(len(comps)), key=lambda j: -comps[j]["var_rot"])
    L = L[:, orden_c]
    comps = [comps[j] for j in orden_c]
    dom = np.abs(L).argmax(axis=1)
    filas = sorted(range(L.shape[0]), key=lambda i: (dom[i], -abs(L[i, dom[i]])))
    fig, ax = plt.subplots(figsize=(E.ANCHO, 17 * E.CM))
    for a, i in enumerate(filas):
        for j in range(L.shape[1]):
            v = L[i, j]
            ax.add_patch(plt.Rectangle((j, -a), 1, 1, fc=E.CMAP_RHO((np.clip(v, -1, 1) + 1) / 2), ec="white", lw=0.8))
            if abs(v) >= 0.4:
                ax.text(j + 0.5, -a + 0.5, E.rho(v), ha="center", va="center", fontsize=7, color="white" if abs(v) > 0.7 else "#111111")
        ax.text(-0.1, -a + 0.5, E.nombre(r["variables"][i]), ha="right", va="center", fontsize=7.5)
    for j, c in enumerate(comps):
        ax.text(j + 0.5, 1.15, f"{c['tema']}{' *' if c['firme'] else ''}\n{E.pct(c['var_rot'], 1)}", ha="left", va="bottom",
                fontsize=7.5, rotation=35, rotation_mode="anchor", fontweight="bold" if c["firme"] else "normal")
    for a in range(1, len(filas)):
        if dom[filas[a]] != dom[filas[a - 1]]:
            ax.plot([0, L.shape[1]], [-a + 1, -a + 1], color="#333333", lw=0.8)
    ax.set_xlim(-0.05, L.shape[1])
    ax.set_ylim(-len(filas) + 1, 1.1)
    ax.axis("off")
    ax.text(0, -len(filas) + 0.5, "* componente firme (bootstrap y canary). Se escriben las cargas con |carga| ≥ 0,4.",
            fontsize=7.5, color=E.TEXTO2, va="top")
    E.guardar(fig, "fig09_cargas_persona")
    return "hecha"


def fig10():
    from scipy.cluster.hierarchy import dendrogram  # noqa: F401  (solo para el formato de coordenadas)
    c = json.load(open(S / "pca" / "clustering_persona.json"))["resultados"]["todas|estable|ajustado"]
    r, L, comps = pca_dim("Persona")
    sol = c["soluciones"]["propio"]
    dif("Fig. 10", "grupos", sol["k"], 10)
    dif("Fig. 10", "ARI estabilidad", round(sol["estabilidad"]["mediana"], 2), 0.71)
    dif("Fig. 10", "ARI con el PCA", round(sol["ari_pca"], 2), 0.66)
    den = c["dendrograma"]
    pal = ["#2a78d6", "#eda100", "#6250d6", "#e87ba4", "#008300"]   # validada (dataviz), distinta de los colores de dimensión
    dom = np.abs(L).argmax(axis=1)
    fig, ax = plt.subplots(figsize=(E.ANCHO, 9.5 * E.CM))
    for xs, ys in zip(den["icoord"], den["dcoord"]):
        ax.plot(xs, ys, color="#555555", lw=0.8)
    alturas = sorted({round(y, 6) for ys in den["dcoord"] for y in ys if y > 0}, reverse=True)
    corte = (alturas[sol["k"] - 2] + alturas[sol["k"] - 1]) / 2 if len(alturas) >= sol["k"] else None
    if corte:
        ax.axhline(corte, color=E.ROJO, lw=0.9, ls="--")
        ax.text(10 * len(den["hojas"]) - 2, corte + 0.01, f"corte: {sol['k']} grupos", ha="right", color=E.ROJO, fontsize=8, va="bottom")
    for pos, hoja in enumerate(den["hojas"]):
        v = c["variables"][hoja]
        i = r["variables"].index(v)
        col = pal[dom[i]] if abs(L[i, dom[i]]) >= 0.4 else "white"
        ax.add_patch(plt.Rectangle((5 + 10 * pos - 3.2, -0.045), 6.4, 0.03, fc=col, ec="#888888", lw=0.4, clip_on=False))
        ax.text(5 + 10 * pos, -0.06, E.nombre(v), rotation=90, ha="center", va="top", fontsize=7)
    ax.set_xlim(0, 10 * len(den["hojas"]))
    ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    ax.set_ylabel("Distancia (1 − |correlación|)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: E.rho(v, 1, signo=False)))
    h = [Patch(color=pal[j], label=f"{c_['tema']}") for j, c_ in enumerate(comps)] + [Patch(fc="white", ec="#888888", label="sin carga ≥ 0,4")]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, -0.52), ncol=3, fontsize=7.5,
              title="Componente del PCA en el que más carga", title_fontsize=7.5)
    E.guardar(fig, "fig10_dendrograma_persona")
    return "hecha"


def fig20():
    import datetime as dt
    fig, axs = plt.subplots(3, 1, figsize=(E.ANCHO, 15 * E.CM), sharex=True, gridspec_kw={"hspace": 0.25})
    cortes = {}
    for dim, ax in zip(DIMS, axs):
        r, L, comps = pca_dim(dim)
        pts = pd.DataFrame(r["puntajes"])
        fechas = [dt.datetime.strptime(str(f)[:8], "%Y%m%d") for f in pts[2]]
        vers = list(pts[1])
        for v in ("v9.1.7", "v12.0.5", "v14.1.1"):
            if v in vers:
                cortes[v] = fechas[vers.index(v)]
        estilos = ["-", "--", ":", "-.", (0, (5, 1, 1, 1))]
        k = 0
        for c in comps:
            if not c["firme"]:
                continue
            y = pts[3 + c["n"] - 1].astype(float)
            suave = y.rolling(9, center=True, min_periods=3).mean()
            ax.plot(fechas, y, ".", color="#d0d0d0", ms=2)
            ax.plot(fechas, suave, ls=estilos[k % 5], color=E.DIM[dim], lw=1.3, label=c["tema"])
            k += 1
        ax.set_ylabel(dim, fontsize=9, color=E.DIM[dim], fontweight="bold")
        lo, hi = ax.get_ylim()
        ax.set_ylim(lo, hi + (hi - lo) * 0.45)
        ax.legend(loc="upper left", fontsize=7.5, ncol=3)
        ax.axhline(0, color=E.GUIA, lw=0.5)
    for ax in axs:
        for v, fch in cortes.items():
            ax.axvline(fch, color="#333333", lw=0.8)
        for an in (2020, 2023, 2025):
            ax.axvline(dt.datetime(an, 1, 1), color="#888888", lw=0.7, ls=":")
    for v, fch in cortes.items():
        axs[0].text(fch, axs[0].get_ylim()[1], v, ha="center", va="bottom", fontsize=7.5)
    dif("Fig. 20", "cortes de época encontrados en los releases", len(cortes), 3)
    axs[-1].set_xlabel("Fecha del release estable")
    E.guardar(fig, "fig20_componentes_en_el_tiempo")
    return "hecha (Proceso y Producto desde 2019: CFDR y NUB solo tienen datos desde v9.0.0)"


# ── Fig. 4 · qué pasó con los pares que resisten el tamaño ───────────────────
TABLA7 = {"Persona": (339, 112, 72, 32, 6, 7, 19), "Proceso": (394, 65, 43, 36, 6, 5, 25), "Producto": (199, 21, 7, 5, 1, 2, 2)}
DESARROLLADAS = set("ABCGHN")


def tabla7(p):
    ev = evaluados(p)
    out = {}
    for D in DIMS:
        d = ev[ev.dentro.fillna("").str.contains(D)]
        sig = d[d.categoria.isin(["positiva", "negativa"])]
        rob = sig[sig.robusta]
        rt = rob[~rob.motivo.fillna("").isin(["escala", "no resiste tamaño"])]
        out[D] = dict(n=(len(d), len(sig), len(rob), len(rt), int((rt.motivo == "mecánico").sum()),
                         int(rt.motivo.fillna("").str.startswith("descartado").sum()), int(d.patron.sum())), rt=rt)
    return out


def fig04():
    p = patrones()
    t7 = tabla7(p)
    fam = familias(p).set_index("clave")
    cats = [("Mecánicos", "#9a9a9a", None), ("Descartados al validar", "#d9d9d9", "///"),
            ("Patrones: medidas de un mismo aspecto", "#5b5b5b", None), ("Patrones: evidencia baja", "white", None),
            ("Patrones desarrollados en el texto (A–C, G–H, N)", E.ROJO, None), ("Otros patrones con familia en el texto", "#f2a3a2", None),
            ("Patrones sin familia en el texto", "white", "...")]
    fig, ax = plt.subplots(figsize=(E.ANCHO, 6.2 * E.CM))
    for i, D in enumerate(DIMS):
        n, rt = t7[D]["n"], t7[D]["rt"]
        for lab, a, b in zip(("pares evaluados", "significativos", "robustos", "resisten el tamaño", "mecánicos",
                              "descartados al validar", "patrones"), n, TABLA7[D]):
            dif("Fig. 4 / Tabla 7", f"{D} {lab}", a, b)
        cnt = [0] * len(cats)
        for _, r in rt.iterrows():
            m = str(r.motivo) if pd.notna(r.motivo) else ""
            if m == "mecánico":
                cnt[0] += 1
            elif m.startswith("descartado"):
                cnt[1] += 1
            elif r.mismo_tema:
                cnt[2] += 1
            elif r.nivel == "baja":
                cnt[3] += 1
            elif r.clave in fam.index and fam.loc[r.clave, "familia"] in DESARROLLADAS:
                cnt[4] += 1
            elif r.clave in fam.index:
                cnt[5] += 1
            else:
                cnt[6] += 1
        left = 0
        for (lab, col, hatch), c in zip(cats, cnt):
            if not c:
                continue
            ax.barh(-i, c, left=left, color=col, hatch=hatch, height=0.55, edgecolor="#777777" if col == "white" else "white", linewidth=0.8)
            ax.text(left + c / 2, -i, str(c), ha="center", va="center", fontsize=8,
                    color="white" if col in ("#5b5b5b", E.ROJO, "#9a9a9a") else "#111111",
                    bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none") if hatch else None)
            left += c
        ax.text(left + 0.4, -i, f"{left} resisten el tamaño", va="center", fontsize=8, color=E.TEXTO2)
    ax.set_yticks(-np.arange(3), DIMS)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("Pares dentro de la dimensión que resisten el control por tamaño")
    ax.set_xlim(0, 44)
    h = [Patch(fc=c, hatch=hh, ec="#777777", label=l) for l, c, hh in cats]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.45, -0.3), ncol=2, fontsize=7.5)
    E.guardar(fig, "fig04_destino_resisten_tamano")
    return "hecha"


# ── Fig. 5 · red de patrones de Persona ──────────────────────────────────────
POS5 = {  # coordenadas a mano por zona
    "prop_commitean_ratio": (0.0, 0.0), "prop_cierran_ratio": (0.0, -2.6),
    "exprev_share_top10pct": (2.6, 1.9), "nc_share_top10pct": (2.9, 0.6), "sc_share_top10pct": (4.4, 1.3),
    "sc_p90": (2.7, -0.7), "cdiv_p90": (4.4, -0.5), "sc_mediana": (1.5, 2.6),
    "exprev_p90": (1.7, -3.6), "rexprev_mediana": (2.6, -2.4),
    "le_mediana": (-2.6, 1.0), "dev_exp_mediana": (-2.8, -0.4), "cdiv_mediana": (-4.2, 0.4), "rexp_mediana": (-3.6, -1.7),
    "tasa_nuevos_commits_ratio": (-1.6, -2.9)}
ZONAS5 = [("Participación", -0.6, -3.2, 1.2, 3.8), ("Concentración del núcleo", 1.0, -1.25, 4.1, 4.3),
          ("Revisores más activos", 1.0, -4.2, 2.3, 2.3), ("Experiencia", -4.9, -2.3, 3.0, 3.8),
          ("Ingreso de nuevos", -2.45, -3.5, 1.7, 1.2)]
COL_FAM = {"A": E.ROJO, "B": "#2a78d6", "C": "#eda100"}


def fig05():
    p = patrones()
    fam = familias(p).set_index("clave")
    per = p[p.dentro.fillna("").str.contains("Persona") & (p.patron | p.motivo.fillna("").str.startswith("descartado"))]
    vs = sorted(set(per[per.patron].x) | set(per[per.patron].y))
    dif("Fig. 5", "variables en los patrones de Persona", len(vs), 15)
    dif("Fig. 5", "patrones de Persona", int(per.patron.sum()), 19)
    faltan = [v for v in vs if v not in POS5]
    if faltan:
        DIFERENCIAS.append(("Fig. 5", f"variables sin ubicación en la red: {faltan}"))
    fig, ax = plt.subplots(figsize=(E.ANCHO, 11.5 * E.CM))
    for lab, x, y, w, h in ZONAS5:
        ax.add_patch(plt.Rectangle((x, y), w, h, fc="#f6f6f4", ec="#d0d0d0", lw=0.6, zorder=0))
        ax.text(x + 0.08, y + h - 0.08, lab, fontsize=7.5, color=E.TEXTO2, va="top", style="italic")
    sin_fam = 0
    for _, r in per.iterrows():
        if r.x not in POS5 or r.y not in POS5:
            continue
        (x0, y0), (x1, y1) = POS5[r.x], POS5[r.y]
        w = 0.6 + 5 * abs(r.rho) ** 1.5
        f_ = fam.loc[r.clave, "familia"] if r.clave in fam.index else None
        if not r.patron:
            kw = dict(color="#cfcfcf", ls=(0, (1.5, 1.5)), lw=1.0)
        elif f_ is None:
            kw = dict(color="#a8a8a8", ls=(0, (4, 2)), lw=min(w, 1.6))
            sin_fam += 1
        elif f_ in COL_FAM:
            kw = dict(color=COL_FAM[f_], ls="-", lw=w)
        elif r.nivel == "baja":
            kw = dict(color="#8a8a8a", ls=(0, (1.5, 1.5)), lw=w)
        else:
            kw = dict(color="#8a8a8a", ls="-", lw=w)
        ax.plot([x0, x1], [y0, y1], zorder=1, solid_capstyle="round", **kw)
    for v in vs:
        x, y = POS5[v]
        ax.plot(x, y, "o", ms=7, mfc="white", mec="#222222", mew=1.2, zorder=3)
        ax.text(x, y - 0.3, E.nombre(v).replace(" (", "\n("), ha="center", va="top", fontsize=7, zorder=4,
                bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.85))
    ax.set_xlim(-5.1, 5.3)
    ax.set_ylim(-4.4, 3.3)
    ax.set_aspect("equal")
    ax.axis("off")
    h = [Line2D([], [], color=COL_FAM[k], lw=2.5, label=f"Familia {k}") for k in "ABC"] + [
        Line2D([], [], color="#8a8a8a", lw=2, label="Familias D, E y F"),
        Line2D([], [], color="#8a8a8a", lw=2, ls=(0, (1.5, 1.5)), label="Evidencia baja"),
        Line2D([], [], color="#9e9e9e", lw=2, ls=(0, (4, 2)), label="Patrón en los datos que el texto da por descartado")]
    if (~per.patron).any():
        h.append(Line2D([], [], color="#cfcfcf", lw=1, ls=(0, (1.5, 1.5)), label="Descartado al validar"))
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, fontsize=7.5)
    ax.text(5.2, -4.35, "Grosor de la línea proporcional a |ρ|", ha="right", fontsize=7, color=E.TEXTO2)
    if sin_fam:
        DIFERENCIAS.append(("Fig. 5", f"{sin_fam} patrones de Persona en los datos no están en ninguna familia del texto "
                                      "(son las relaciones de medianas de experiencia que el texto da por descartadas)"))
    E.guardar(fig, "fig05_red_persona")
    return "hecha"


# ── Fig. 25 · aspectos de cada dimensión ─────────────────────────────────────
def fig25():
    p = patrones()
    pat = p[p.patron]
    tem = {D: sorted(set(pat[pat.dentro.fillna("").str.contains(D)].tema_x) | set(pat[pat.dentro.fillna("").str.contains(D)].tema_y))
           for D in DIMS}
    fig, axs = plt.subplots(3, 1, figsize=(E.ANCHO, 22 * E.CM), gridspec_kw={"height_ratios": [len(tem[D]) + 2.5 for D in DIMS], "hspace": 0.32})
    for ax, D in zip(axs, DIMS):
        d = pat[pat.dentro.fillna("").str.contains(D)]
        temas = tem[D]
        n = len(temas)
        for i, a in enumerate(temas):
            for j, b in enumerate(temas):
                if j < i:
                    continue
                sel = d[((d.tema_x == a) & (d.tema_y == b)) | ((d.tema_x == b) & (d.tema_y == a))]
                if sel.empty:
                    ax.add_patch(plt.Rectangle((j, -i), 1, 1, fc="white", ec="#e5e5e5", lw=0.6))
                    continue
                m = sel.rho.mean()
                ax.add_patch(plt.Rectangle((j, -i), 1, 1, fc=E.CMAP_RHO((np.clip(m, -0.8, 0.8) + 0.8) / 1.6),
                                           ec="#111111" if i == j else "white", lw=1.4 if i == j else 0.8))
                ax.text(j + 0.5, -i + 0.5, str(len(sel)), ha="center", va="center", fontsize=8.5, fontweight="bold")
        for k, t in enumerate(temas):
            ax.text(-0.08, -k + 0.5, t, ha="right", va="center", fontsize=8)
            ax.text(k + 0.5, 1.08, t, ha="left", va="bottom", fontsize=8, rotation=40, rotation_mode="anchor")
        ax.set_xlim(0, max(n, 1))
        ax.set_ylim(-max(n, 1) + 1, 1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.text(-3.4, 0.6, D, fontsize=9.5, color=E.DIM[D], fontweight="bold", ha="left", va="bottom")
        ax.set_xlim(-3.5, 8.5)
    sm = plt.cm.ScalarMappable(cmap=E.CMAP_RHO, norm=plt.Normalize(-0.8, 0.8))
    cb = fig.colorbar(sm, ax=axs, orientation="horizontal", fraction=0.025, pad=0.03, aspect=40)
    cb.set_label("ρ media de los patrones de la celda (el número es la cantidad; borde negro = mismo aspecto)", fontsize=7.5)
    cb.ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: E.rho(v, 1)))
    E.guardar(fig, "fig25_aspectos_por_dimension")
    return "hecha (aspectos = temas de multiverso_asignacion.tema, los de la columna tema_x/tema_y)"


# ── Fig. 26 · mapa de conexiones ─────────────────────────────────────────────
def fig26():
    p = patrones()
    c, _ = conteo_pares(p)
    u = pd.read_csv(S / "multiverso_asignacion" / "universos.csv")
    azar = u[u.universo.str.startswith("azar")]
    b = bloques()
    vb = b[(b.tipo_elemento == "componente") & (b.x_tema == "volumen de actividad") & (b.y_tema == "bugs de usuarios")].iloc[0]
    dif("Fig. 26", "volumen ↔ bugs (componentes)", round(vb.rho_corregida, 2), 0.50)
    dif("Fig. 26", "volumen ↔ bugs con control por tamaño", round(vb.rho_corregida_tamano, 2), -0.15)
    pos = {"Persona": (0.0, 1.0), "Proceso": (-1.15, -0.75), "Producto": (1.15, -0.75)}
    fig, ax = plt.subplots(figsize=(E.ANCHO, 9 * E.CM))
    k = 0.0085   # ancho de banda por patrón (unidades del gráfico)
    for par in PARES:
        a_, bb = par.split("–")
        p0, p1 = np.array(pos[a_]), np.array(pos[bb])
        dvec = (p1 - p0) / np.linalg.norm(p1 - p0)
        o = np.array([-dvec[1], dvec[0]])
        tot, solo, tamb = c[par]
        for w0, w1, col in ((0, solo, "#333333"), (solo, solo + tamb, "#c4c4c4")):
            off0, off1 = (w0 - tot / 2) * k, (w1 - tot / 2) * k
            poly = [p0 + o * off0, p1 + o * off0, p1 + o * off1, p0 + o * off1]
            ax.add_patch(plt.Polygon(poly, closed=True, fc=col, ec="white", lw=0.6, zorder=1))
        pct_az = (azar[f"cca {par} p"] < 0.05).mean() * 100
        mid = (p0 + p1) / 2
        lp = {"Persona–Proceso": mid + np.array([-0.98, 0.15]), "Persona–Producto": mid + np.array([0.98, 0.15]),
              "Proceso–Producto": mid + np.array([0, -0.33])}[par]
        ax.text(*lp, f"{tot} patrones\n{solo} solo entre · {tamb} también dentro\nCCA sobre el azar: {E.pct(pct_az)}",
                ha="center", va="center", fontsize=7.5, linespacing=1.3)
    for d, (x, y) in pos.items():
        ax.add_patch(plt.Circle((x, y), 0.27, color=E.DIM[d], zorder=3))
        ax.text(x, y, d, ha="center", va="center", color="white", fontsize=7.5, fontweight="bold", zorder=4)
    ax.text(1.95, 1.2, f"Tamaño del equipo (componentes):\nvolumen de actividad ↔ bugs de usuarios\n{E.rho(vb.rho_corregida)} → "
                        f"{E.rho(vb.rho_corregida_tamano)} con control por tamaño",
            fontsize=7.5, va="top", ha="left", bbox=dict(boxstyle="round,pad=0.4", fc="#f6f6f4", ec="#cccccc"))
    ax.set_xlim(-2.4, 3.6)
    ax.set_ylim(-1.3, 1.4)
    ax.set_aspect("equal")
    ax.axis("off")
    h = [Patch(fc="#333333", label="Solo entre dimensiones"), Patch(fc="#c4c4c4", label="También dentro de una dimensión"),
         Line2D([], [], color="none", label="Ancho proporcional a la cantidad de patrones")]
    ax.legend(handles=h, loc="lower left", bbox_to_anchor=(0.66, 0.02), fontsize=7.5)
    E.guardar(fig, "fig26_mapa_conexiones")
    return "hecha"


# ── validaciones disponibles en el repo ──────────────────────────────────────
VAL = S / "validaciones"
# Tabla 14 del texto: (x, y, explicación, ρ original, ρ validado, resultado)
TABLA14 = [
    ("le_mediana", "anmcc_mediana", "recién llegados", 0.48, 0.08, "Descartada"),
    ("dev_exp_mediana", "anmcc_mediana", "recién llegados", 0.38, -0.01, "Descartada"),
    ("le_mediana", "tasa_nuevos_commits_ratio", "recién llegados", -0.73, 0.01, "Descartada"),
    ("dev_exp_mediana", "tasa_nuevos_commits_ratio", "recién llegados", -0.71, -0.02, "Descartada"),
    ("cdiv_mediana", "tasa_nuevos_commits_ratio", "recién llegados", -0.44, 0.01, "Descartada"),
    ("rexp_mediana", "tasa_nuevos_commits_ratio", "recién llegados", -0.29, -0.02, "Descartada"),
    ("cdiv_mediana", "le_mediana", "recién llegados", 0.49, 0.04, "Descartada"),
    ("cdiv_mediana", "dev_exp_mediana", "recién llegados", 0.41, 0.06, "Descartada"),
    ("le_mediana", "rexp_mediana", "recién llegados", 0.29, 0.07, "Descartada"),
    ("le_mediana", "prop_commitean_ratio", "recién llegados", -0.33, -0.38, "Se mantiene"),
    ("dev_exp_mediana", "prop_commitean_ratio", "recién llegados", -0.30, -0.29, "Se mantiene"),
    ("cdiv_mediana", "commits_doc_producto", "commits solo de documentación", -0.42, -0.15, "Descartada"),
    ("anmcc_mediana", "commits_doc_producto", "commits solo de documentación", -0.45, -0.07, "Descartada"),
    ("sc_mediana", "jarczyk_success_rate_producto", "issues del mismo release", 0.33, 0.00, "Descartada"),
    ("nci_producto", "jarczyk_success_rate_producto", "issues del mismo release", 0.39, 0.15, "Descartada"),
    ("nci_producto", "process_performance_producto", "issues del mismo release", 0.28, 0.08, "Descartada"),
    ("tasa_nuevos_commits_ratio", "le_producto", "recién llegados", -0.26, 0.08, "Descartada"),
    ("prop_commitean_ratio", "le_producto", "recién llegados", -0.29, -0.20, "Se mantiene"),
]


def _json(nombre):
    f = VAL / nombre / "resumen.json"
    return json.load(open(f)) if f.exists() else None


def validados():
    """ρ recalculado sin los datos sospechosos, por par, solo de las validaciones que existen en el repo."""
    out = {}
    j = _json("experiencia_sin_recien_llegados")
    if j:
        for k, v in j["resultados"].items():
            if k.startswith("2. sin recién llegados ·"):
                x = k.split("· ")[1].split(" ↔ ")[0]
                out[clave((x, "anmcc_mediana"))] = (v["rho_corregida"], "experiencia_sin_recien_llegados")
    j = _json("cdiv_sin_commits_doc")
    if j:
        out[clave(("cdiv_mediana", "commits_doc_producto"))] = (
            j["resultados"]["cdiv_mediana sin commits solo de documentación"]["rho_corregida"], "cdiv_sin_commits_doc")
    j = _json("anmcc_sin_commits_doc")
    if j:
        out[clave(("anmcc_mediana", "commits_doc_producto"))] = (
            j["2. ANMCC sin commits solo de documentación"]["rho_corregida"], "anmcc_sin_commits_doc")
    f = VAL / "verificar_sc_jarczyk" / "resumen.json"
    if f.exists():
        out[clave(("sc_mediana", "jarczyk_success_rate_producto"))] = (json.load(open(f))["rho_sin_issues_propias"], "verificar_sc_jarczyk.py")
    return out


def validacion_experiencia():
    return None   # la validación de las medianas frente a la proporción que commitea no está en el repo


def tabla14_datos():
    p = patrones().set_index("clave")
    v = validados()
    filas = []
    for x, y, expl, r0t, r1t, rest in TABLA14:
        k = clave((x, y))
        r0 = p.loc[k, "rho"] if k in p.index else np.nan
        r1, fuente = v.get(k, (np.nan, ""))
        mot = str(p.loc[k, "motivo"]) if k in p.index and pd.notna(p.loc[k, "motivo"]) else ("patrón" if k in p.index and p.loc[k, "patron"] else "")
        res_datos = ("Descartada" if mot.startswith("descartado") else "Se mantiene (patrón)" if mot == "patrón" else mot)
        filas.append(dict(x=x, y=y, relacion=E.par(x, y), explicacion=expl, rho_original=r0, rho_validado=r1, fuente=fuente,
                          estado_en_datos=res_datos, texto_original=r0t, texto_validado=r1t, texto_resultado=rest))
    return pd.DataFrame(filas)


def fig21():
    t = tabla14_datos()
    for _, r in t.iterrows():
        dif("Fig. 21 / Tabla 14", f"{r.relacion} ρ original", round(r.rho_original, 2), r.texto_original)
        if np.isnan(r.rho_validado):
            DIFERENCIAS.append(("Fig. 21 / Tabla 14", f"{r.relacion}: el texto informa {E.rho(r.texto_validado)} sin esos datos, "
                                                      f"pero no hay validación en el repo que lo calcule (estado en los datos: {r.estado_en_datos})"))
        else:
            dif("Fig. 21 / Tabla 14", f"{r.relacion} ρ validado", round(r.rho_validado, 2), r.texto_validado)
    grupos = ["recién llegados", "commits solo de documentación", "issues del mismo release"]
    fig, ax = plt.subplots(figsize=(E.ANCHO, 13.5 * E.CM))
    y, ticks, labs = 0, [], []
    for g in grupos:
        sub = t[t.explicacion == g]
        y -= 0.3
        ax.text(-0.02, y, {"recién llegados": "Sin los recién llegados", "commits solo de documentación":
                           "Sin los commits que solo tocan documentación", "issues del mismo release":
                           "Sin las issues abiertas y cerradas en el mismo release"}[g],
                transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=8.5, fontweight="bold")
        y -= 0.8
        for _, r in sub.iterrows():
            r0, r1 = r.rho_original, r.rho_validado
            if np.isnan(r1):
                ax.plot(r0, y, "o", color="#bbbbbb", ms=5, zorder=3)
                ax.text(r0 + (0.03 if r0 > 0 else -0.03), y, "sin validación en el repo", va="center",
                        ha="left" if r0 > 0 else "right", fontsize=7, color=E.TEXTO2, style="italic")
            else:
                mantiene = abs(r1) > 0.15 and np.sign(r1) == np.sign(r0)
                col = E.DIM["Persona"] if mantiene else "#8a8a8a"
                ax.plot([r0, r1], [y, y], color=col, lw=1.6, zorder=2)
                ax.plot(r0, y, "o", color=col, ms=5.5, zorder=3)
                ax.plot(r1, y, "o", mfc="white", mec=col, mew=1.3, ms=5.5, zorder=3)
                ax.text(max(r0, r1) + 0.03, y, f"{E.rho(r0)} → {E.rho(r1)}", va="center", fontsize=7.5, color=E.TEXTO2)
            ticks.append(y)
            labs.append(r.relacion)
            y -= 1
    ax.axvspan(-0.15, 0.15, color="#f3f3f3", zorder=0)
    ax.axvline(0, color=E.DESCARTE, lw=0.8, zorder=1)
    ax.set_yticks(ticks, labs, fontsize=8)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(-0.85, 0.85)
    ax.set_ylim(y + 0.4, 0.2)
    E.eje_rho(ax)
    ax.set_xlabel("ρ parcial de Spearman")
    h = [Line2D([], [], marker="o", ls="", color="#555555", ms=5.5, label="Original"),
         Line2D([], [], marker="o", ls="", mfc="white", mec="#555555", ms=5.5, label="Sin los datos que podían producirla"),
         Line2D([], [], color="#8a8a8a", lw=2, label="Descartada"), Line2D([], [], color=E.DIM["Persona"], lw=2, label="Se mantiene"),
         Line2D([], [], marker="o", ls="", color="#bbbbbb", ms=5, label="Sin validación en el repo"), Patch(color="#f3f3f3", label="±0,15")]
    ax.legend(handles=h, loc="upper center", bbox_to_anchor=(0.3, -0.07), ncol=3, fontsize=7.5)
    E.guardar(fig, "fig21_validacion")
    n_ok = int(t.rho_validado.notna().sum())
    return f"parcial: {n_ok} de 18 relaciones tienen validación en el repo"


# ── Fig. 11 · las dos actividades de Proceso ─────────────────────────────────
def fig11():
    p = patrones().set_index("clave")
    b = base()
    k_nm, k_jm, k_nj = clave(("nci_producto", "mttr_producto")), clave(("jarczyk_success_rate_producto", "mttr_producto")), clave(("nci_producto", "jarczyk_success_rate_producto"))
    r_nm, r_jm, r_nj = p.loc[k_nm, "rho"], p.loc[k_jm, "rho"], p.loc[k_nj, "rho"]
    dif("Fig. 11", "NCI ↔ MTTR", round(r_nm, 2), 0.29)
    dif("Fig. 11", "Jarczyk ↔ MTTR", round(r_jm, 2), -0.12)
    dif("Fig. 11", "NCI ↔ Jarczyk", round(r_nj, 2), 0.39)
    est_nj = "patrón" if p.loc[k_nj, "patron"] else str(p.loc[k_nj, "motivo"])
    DIFERENCIAS.append(("Fig. 11", f"NCI ↔ Jarczyk en los datos: {est_nj} (el texto la da por descartada, +0,39 → +0,15); "
                                   "no hay validación nci_sin_issues_del_release en el repo, así que faltan +0,51 y +0,15"))
    fig, ax = plt.subplots(figsize=(E.ANCHO, 7.5 * E.CM))
    pos = {"NCI": (0, 0), "MTTR": (2.2, 0), "Jarczyk Success Rate": (1.1, 1.45)}
    nombres = {"NCI": "NCI\n(issues cerradas)", "MTTR": "MTTR\n(tiempo de resolución)", "Jarczyk Success Rate": "Jarczyk Success Rate\n(resolución de lo nuevo)"}
    for n_, (x, y) in pos.items():
        ax.add_patch(plt.Circle((x, y), 0.17, color=E.DIM["Proceso"], zorder=3))
        ax.text(x, y - 0.25 if y == 0 else y + 0.24, nombres[n_], ha="center", va="top" if y == 0 else "bottom", fontsize=8.5)

    def lado(a, b_, estilo, col, lw, txt, off):
        (x0, y0), (x1, y1) = pos[a], pos[b_]
        ax.plot([x0, x1], [y0, y1], ls=estilo, color=col, lw=lw, zorder=1)
        ax.text((x0 + x1) / 2 + off[0], (y0 + y1) / 2 + off[1], txt, ha="center", va="center", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))
    lado("NCI", "MTTR", "-", "#222222", 2.4, f"ρ {E.rho(r_nm)} ({p.loc[k_nm, 'nivel']})", (0, -0.12))
    lado("Jarczyk Success Rate", "MTTR", (0, (3, 2)), "#666666", 1.3, f"ρ {E.rho(r_jm)}\n{b.loc[k_jm, 'categoria'].replace('_', ' ')}", (0.42, 0.05))
    lado("NCI", "Jarczyk Success Rate", "-", "#b5b5b5", 1.6, f"ρ {E.rho(r_nj)}\n{est_nj} en los datos", (-0.45, 0.05))
    ax.set_xlim(-0.8, 3.0)
    ax.set_ylim(-0.75, 2.0)
    ax.set_aspect("equal")
    ax.axis("off")
    E.guardar(fig, "fig11_dos_actividades_proceso")
    return "parcial: sin los valores de la validación nci_sin_issues_del_release (no está en el repo)"


# ── Fig. 24 · qué quedó de cada relación ─────────────────────────────────────
def fig24():
    p = patrones()
    f = familias(p)
    pi = p.set_index("clave")
    filas = []

    def rango(claves):
        r = [pi.loc[k, "rho"] for k in claves if k in pi.index and pi.loc[k, "patron"]]
        return (min(r), max(r)) if r else (np.nan, np.nan)
    perm = [("Familia A: participación en el código y concentración del núcleo", list(f[f.familia == "A"].clave)),
            ("Familia C: participación en el código y experiencia", list(f[f.familia == "C"].clave)),
            ("NCI ↔ MTTR: cierre de lo acumulado y tiempo de resolución", [clave(("nci_producto", "mttr_producto"))]),
            ("Concentración del núcleo ↔ DLOC 2.0", [clave(("dloc_flujo_producto", c)) for c in CONC]),
            ("Familia P: participación en el cierre de issues y resolución de lo nuevo", list(f[f.familia == "P"].clave)),
            ("Familia K: concentración del núcleo y cierre de lo viejo", list(f[f.familia == "K"].clave))]
    for lab, ks in perm:
        filas.append(("Permanece", lab, *rango(ks)))
    deb = [("Familia B: cierre de issues y revisores (cambia de signo en la época 2)", list(f[f.familia == "B"].clave)),
           ("Familia M: revisores más activos y bugs de usuarios", list(f[f.familia == "M"].clave)),
           ("Familia Q: ingreso de nuevos y bugs reportados", list(f[f.familia == "Q"].clave)),
           ("Familia R: LE del proyecto y concentración del núcleo", list(f[f.familia == "R"].clave)),
           ("Familia H: issues de documentación (sin datos para las épocas)", list(f[f.familia == "H"].clave))]
    for lab, ks in deb:
        filas.append(("Débil o depende", lab, *rango(ks)))
    t = tabla14_datos()
    for _, r in t[t.rho_validado.notna()].iterrows():
        filas.append(("Descartada al validar", r.relacion, r.rho_original, r.rho_validado))
    fig, ax = plt.subplots(figsize=(E.ANCHO, (0.55 * len(filas) + 3) * E.CM))
    y, ticks, labs, prev = 0, [], [], None
    for sit, lab, a, b_ in filas:
        if sit != prev:
            y -= 0.3
            ax.text(-0.02, y, sit, transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=8.5, fontweight="bold")
            y -= 0.8
            prev = sit
        if sit == "Permanece":
            ax.plot([a, b_], [y, y], color=E.ROJO, lw=3, solid_capstyle="round", alpha=0.5)
            ax.plot([a, b_], [y, y], "o", color=E.ROJO, ms=5.5)
            txt = E.rho(a) if abs(a - b_) < 0.005 else f"{E.rho(a)} a {E.rho(b_)}"
        elif sit == "Débil o depende":
            ax.plot([a, b_], [y, y], color="#999999", lw=3, solid_capstyle="round", alpha=0.4)
            ax.plot([a, b_], [y, y], "o", mfc="white", mec="#555555", ms=5.5)
            txt = E.rho(a) if abs(a - b_) < 0.005 else f"{E.rho(a)} a {E.rho(b_)}"
        else:
            ax.annotate("", xy=(b_, y), xytext=(a, y), arrowprops=dict(arrowstyle="-|>", color="#8a8a8a", lw=1.3))
            ax.plot(a, y, "o", color="#8a8a8a", ms=4.5)
            txt = f"{E.rho(a)} → {E.rho(b_)}"
        ax.text(1.005, y, txt, transform=ax.get_yaxis_transform(), va="center", fontsize=7.5, color=E.TEXTO2)
        ticks.append(y)
        labs.append(lab)
        y -= 1
    ax.axvline(0, color=E.DESCARTE, lw=0.8)
    ax.set_yticks(ticks, labs, fontsize=8)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(-0.8, 0.8)
    ax.set_ylim(y + 0.4, 0.2)
    E.eje_rho(ax)
    ax.set_xlabel("ρ parcial de Spearman")
    E.guardar(fig, "fig24_que_quedo")
    return f"parcial: las descartadas son solo las {int(t.rho_validado.notna().sum())} con validación en el repo"


FIGS = {11: fig11, 21: fig21, 24: fig24, 4: fig04, 5: fig05, 25: fig25, 26: fig26, 9: fig09, 10: fig10, 20: fig20, 2: fig02, 7: fig07, 151: fig15b, 16: fig16, 17: fig17, 18: fig18, 3: fig03, 6: fig06, 12: fig12, 14: fig14, 15: fig15, 19: fig19, 191: fig19b}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", help="números de figura separados por coma")
    a = ap.parse_args()
    E.aplicar()
    que = [int(x) for x in a.solo.split(",")] if a.solo else sorted(FIGS)
    for n in que:
        print(f"Figura {n}")
        ESTADO[n] = FIGS[n]()
    escribir_diferencias()
    if not a.solo:
        escribir_readme()


INFO = {  # n.º -> (archivo, sección, fuente)
    2: ("fig02_variables_por_dimension", "4.1", "diccionario_variables.csv, relaciones/patrones.csv"),
    3: ("fig03_embudo", "4.1", "relaciones/patrones.csv"),
    4: ("fig04_destino_resisten_tamano", "4.2", "relaciones/patrones.csv, figuras/familias.csv"),
    5: ("fig05_red_persona", "4.2.1", "relaciones/patrones.csv, figuras/familias.csv"),
    6: ("fig06_bosque_ABC", "4.2.1", "relaciones/patrones.csv, relaciones/base/pares_correlacion.csv"),
    7: ("fig07_estabilidad_ABC", "4.2.1", "relaciones/patrones.csv, relaciones/base_epocas/pares_correlacion.csv"),
    8: ("fig08_experiencia_sin_recien_llegados", "4.2.1", "validaciones/experiencia_ingreso_sin_recien_llegados (no existe)"),
    9: ("fig09_cargas_persona", "4.2.1", "pca/pca_persona.json"),
    10: ("fig10_dendrograma_persona", "4.2.1", "pca/clustering_persona.json, pca/pca_persona.json"),
    11: ("fig11_dos_actividades_proceso", "4.2.2", "relaciones/patrones.csv"),
    12: ("fig12_bosque_proceso", "4.2.2", "relaciones/patrones.csv, relaciones/base/pares_correlacion.csv"),
    13: ("fig13_nci_sin_issues_del_release", "4.2.2", "validaciones/nci_sin_issues_del_release (no existe)"),
    14: ("fig14_patrones_por_par", "4.3.1", "relaciones/patrones.csv"),
    15: ("fig15_bosque_entre_dimensiones", "4.3.1", "relaciones/patrones.csv, relaciones/base/pares_correlacion.csv"),
    151: ("fig15b_embudo_componentes_grupos", "4.3.2", "bloques_etiquetas/pares.csv"),
    16: ("fig16_componentes_tres_dimensiones", "4.3.2", "bloques_etiquetas/pares.csv"),
    17: ("fig17_multiverso_asignacion", "4.3.3", "multiverso_asignacion/universos.csv"),
    18: ("fig18_tres_dimensiones_vs_azar", "4.4.1", "tres_dimensiones/resumen.json"),
    19: ("fig19_cadena", "4.4.2", "relaciones/triangulos.csv"),
    191: ("fig19b_cadena_mancuernas", "4.4.2", "relaciones/triangulos.csv"),
    20: ("fig20_componentes_en_el_tiempo", "4.5.1", "pca/pca_*.json"),
    21: ("fig21_validacion", "4.5.2", "validaciones/*/resumen.json, relaciones/patrones.csv"),
    22: ("fig22_relaciones_nuevas_alternativos", "4.5.3", "salidas de cruce_alternativos.py"),
    23: ("fig23_random_forest", "4.5.3", "salidas de cruce_alternativos.py"),
    24: ("fig24_que_quedo", "4.6", "relaciones/patrones.csv, figuras/familias.csv, validaciones/*"),
    25: ("fig25_aspectos_por_dimension", "5.1", "relaciones/patrones.csv"),
    26: ("fig26_mapa_conexiones", "5.2", "relaciones/patrones.csv, multiverso_asignacion/universos.csv, bloques_etiquetas/pares.csv"),
    27: ("fig27_antes_despues_correcciones", "5.4", "falta calcular (salidas_originales vs. salidas)"),
}
PENDIENTES = {
    8: "falta dato: la validación de las medianas de experiencia sin recién llegados frente a la tasa de ingreso y la proporción que commitea no está en el código de analisis",
    13: "falta dato: no existe la validación nci_sin_issues_del_release en el código de analisis",
    27: "no se hace sin confirmación: falta calcular la comparación con el dataset original",
}


def escribir_readme():
    L = ["# Figuras de los capítulos 4 y 5", "",
         "Generadas con `python3 analisis/figuras_informe.py` (matplotlib, PNG a 300 dpi + SVG) solo desde `analisis/salidas/`. "
         "Qué difiere del texto y por qué: [diferencias.md](diferencias.md) (listado automático en [diferencias_automaticas.md](diferencias_automaticas.md)).", "",
         "| Figura | Archivo | Sección | Fuente | Estado |", "|---|---|---|---|---|"]
    for n, (arch, sec, fuente) in sorted(INFO.items(), key=lambda t: t[0] if t[0] < 100 else t[0] / 10 + 0.05):
        num = {151: "15b", 191: "19b"}.get(n, str(n))
        estado = ESTADO.get(n) or PENDIENTES.get(n) or ("hecha" if (E.FIGURAS / f"{arch}.png").exists() else "sin generar")
        L.append(f"| {num} | `{arch}` | {sec} | {fuente} | {estado} |")
    (E.FIGURAS / "README.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def escribir_diferencias():
    E.FIGURAS.mkdir(parents=True, exist_ok=True)
    L = ["# Diferencias entre los datos y el texto de los capítulos 4 y 5", "",
         "Las figuras usan siempre el dato de `analisis/salidas/`. Esta lista marca dónde el texto afirma otra cosa.", ""]
    for f, m in DIFERENCIAS:
        L.append(f"- **{f}** · {m}")
    if not DIFERENCIAS:
        L.append("Sin diferencias en las figuras generadas.")
    (E.FIGURAS / "diferencias_automaticas.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
