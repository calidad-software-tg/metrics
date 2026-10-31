#!/usr/bin/env python3
"""
analisis/tres_dimensiones.py

Análisis tridimensional: ¿hay patrones que asocien Persona, Proceso y Producto a la vez, o las conexiones
son solo de a pares? Trabaja sobre los componentes del PCA de cada dimensión (los mismos puntajes que usa
cruces.py) con una asignación única de las métricas compartidas, y con los mismos criterios que el resto del
análisis: Spearman parcial (tendencia y duración), muestra efectiva, Benjamini–Hochberg, estabilidad por
períodos (calendario; épocas como sensibilidad), réplica en canary, control por tamaño y nula por corrimiento
circular.

Uso (después de pca.py de las tres dimensiones):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/tres_dimensiones.py

Componentes (sin variables compartidas entre los tres lados):
    Persona   CP1 renovación del equipo, CP2 volumen de actividad (escala), CP3 concentración del núcleo
    Proceso   CP2 resolución de lo nuevo, CP5 cierre de lo viejo
              (CP1, bugs de usuarios, queda en Producto porque CFDR y NUB se asignan ahí; CP3 y CP4 los arma
              un escalón de README o de Wiki y no se interpretan, como en los cruces)
    Producto  CP1 bugs de usuarios, CP4 flujo de documentación

Pasos:
  1. Medida global. Correlación canónica generalizada (MAXVAR: el mayor autovalor de la suma de los
     proyectores de los tres bloques, entre 1 y 3) y, como confirmación, el coeficiente RV entre bloques y el
     análisis factorial múltiple (MFA, PCA de los tres bloques con cada uno pesado por su primer valor
     singular). Nula: cada dimensión desplazada en el tiempo por separado. Con todos los componentes, sin el de
     volumen y sin tamaño (puntajes residualizados por el logaritmo de los activos), y en canary.
  2. Estructura. Red de correlaciones parciales entre los componentes de dimensiones distintas: cada par
     marginal (= cruce de componentes), descontando el tercer vértice de cada triángulo y descontando los
     otros cinco componentes. Cada triángulo (un componente por dimensión) se clasifica:
       tridimensional  los tres lados son patrón y se mantienen al descontar el tercer vértice;
       cadena          dos lados son patrón (o los tres, pero uno desaparece al descontar el tercero);
       solo tamaño     no hay patrones y algún lado robusto es escala;
       pares sueltos   uno o ningún lado es patrón.
     Triangulación con variables: los mismos lados con las variables que definen cada componente
     (|carga| >= 0,4), en los triángulos con al menos dos lados patrón y en el de la concentración del núcleo.
  3. Contraste. PCA y clustering conjunto de las variables de los siete componentes (cruces.pca_conjunto y
     cruces.clustering_conjunto), con y sin tamaño: ¿algún componente o grupo junta las tres dimensiones?
  4. Interpretación. Perfiles de releases: tercio con el puntaje más alto y más bajo de cada componente de
     Persona, diferencia de los demás componentes (en desvíos) contra la nula por corrimiento y su signo en
     canary. Rezago de un release entre componentes de dimensiones distintas (descriptivo).

Salidas en analisis/salidas/tres_dimensiones/: resumen.md, resumen.json, red.csv, triangulos.csv,
triangulacion_variables.csv, perfiles.csv, rezago.csv.
"""
import csv
import json
import math
import sys
import warnings
from itertools import combinations, product
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import correlaciones as corr  # noqa: E402
import cruces  # noqa: E402
import pca  # noqa: E402

SALIDA = corr.ROOT / "analisis" / "salidas" / "tres_dimensiones"
DIMS = ("Persona", "Proceso", "Producto")
CFG = cruces.mezclar(cruces.DEFAULTS, {"componentes": {
    "conjunto": {"Persona": "todas", "Proceso": "producto", "Producto": "producto"},
    "elegir": {"Persona": [1, 2, 3], "Proceso": [2, 5], "Producto": [1, 4]}}})
NOMBRES = {"persona_cp1": "renovación del equipo", "persona_cp2": "volumen de actividad",
           "persona_cp3": "concentración del núcleo", "proceso_cp2": "resolución de lo nuevo",
           "proceso_cp5": "cierre de lo viejo", "producto_cp1": "bugs de usuarios",
           "producto_cp4": "flujo de documentación"}
ESCALA = {"persona_cp2"}                     # volumen de actividad: es tamaño, no calidad
TRIANGULO_ARTIFACT = ("persona_cp3", "proceso_cp5", "producto_cp1")
# asignación única de las métricas que el catálogo asocia a dos dimensiones (la de los cruces de a pares)
ASIGNACION = {
    "Persona": ["exprev", "rexprev", "cdiv", "nc", "sc", "dev_exp", "le (por colaborador)", "cd (por colaborador)"],
    "Proceso": ["mttr", "noi"],
    "Producto": ["cfdr", "nub", "rc", "wp", "nob_42", "anmcc", "le (proyecto)", "cd (proyecto)"],
}
# variantes de la medida global: sin el componente de volumen, sin tamaño (puntajes residualizados por el
# logaritmo de los activos) y, además, sin uno de los dos componentes del único par mecánico (LE por colaborador
# en renovación del equipo y LE del proyecto en flujo de documentación)
VARIANTES = {"todos": {}, "sin_volumen": dict(quitar=ESCALA), "sin_tamano": dict(quitar=ESCALA, tamano=True),
             "sin_tamano_ni_documentacion": dict(quitar=ESCALA | {"producto_cp4"}, tamano=True),
             "sin_tamano_ni_renovacion": dict(quitar=ESCALA | {"persona_cp1"}, tamano=True)}
N_PERM = 1000
N_PERM_CANARY = 300
CARGA_MIN = CFG["carga_minima"]


def num(v):
    return isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v))


def r3(v):
    return round(float(v), 3) if num(v) else ""


def f2(v):
    return f"{v:+.2f}".replace(".", ",") if num(v) else "—"


# ── datos alineados ──────────────────────────────────────────────────────────

class Serie:
    """Los siete componentes en las releases que tienen todos, con duración, año, época y tamaño."""

    def __init__(self, cps, clave, size, epoca=None):
        comunes = sorted(set.intersection(*(set(c[clave]) for c in cps)))
        comunes = [p for p in comunes if all(c[clave][p][1] is not None for c in cps)]
        self.pn = np.array(comunes, dtype=float)
        ref = cps[0][clave]
        self.du = np.array([ref[p][0] if ref[p][0] else 1.0 for p in comunes], dtype=float)
        self.anio = [ref[p][2] for p in comunes]
        self.epoca = [epoca.get(p) for p in comunes] if epoca else None
        self.X = np.array([[c[clave][p][1] for c in cps] for p in comunes], dtype=float)
        self.size = np.array([size[p][1] if p in size and size[p][1] is not None else np.nan for p in comunes])
        self.n = len(comunes)


def ps(x, y, s, idx=None, ctrl=(), tamano=False):
    """Spearman parcial de corr.partial_spearman sobre las filas idx, con los componentes ctrl (y el logaritmo
    del tamaño) como controles extra."""
    idx = np.arange(s.n) if idx is None else np.asarray(idx)
    if tamano:
        idx = idx[~np.isnan(s.size[idx])]
    extra = [list(s.X[idx, k]) for k in ctrl]
    if tamano:
        extra.append([corr.safe_log(v + 1) for v in s.size[idx]])
    return corr.partial_spearman(list(x[idx]), list(y[idx]), list(s.pn[idx]), list(s.du[idx]), extra_controls=extra or None)


def evaluar(i, j, ctrl, E, C):
    """Un par de componentes (columnas i, j) con los controles ctrl: global, por período (calendario y épocas),
    canary y con tamaño. Mismos criterios que cruces.evaluar_par."""
    g = ps(E.X[:, i], E.X[:, j], E, ctrl=ctrl)
    out = dict(n=E.n, n_efectiva=g["n_efectiva"], rho=g["rho_corr"], ic_inf=g["ic_inf"], ic_sup=g["ic_sup"],
               p=g["p_corr"])
    for nombre, etiquetas in (("cal", [(lab, lambda a, y0=y0, y1=y1: a is not None and y0 <= a <= y1)
                                       for lab, y0, y1 in corr.CALENDARIO]),
                              ("ep", [(f"E{k}", lambda e, k=k: e == k) for k in (1, 2, 3, 4)])):
        valores = E.anio if nombre == "cal" else E.epoca
        rhos = {}
        for lab, en in etiquetas:
            idx = [t for t, v in enumerate(valores) if en(v)]
            if len(idx) >= corr.MIN_VENTANAS_PERIODO:
                rhos[lab] = ps(E.X[:, i], E.X[:, j], E, idx, ctrl)["rho_corr"]
        ev = [r for r in rhos.values() if num(r)]
        out[f"per_{nombre}"] = rhos
        out[f"estable_{nombre}"] = (len(ev) >= 3 and num(g["rho_corr"])
                                     and all((r >= 0) == (g["rho_corr"] >= 0) for r in ev))
    out["rho_canary"] = ps(C.X[:, i], C.X[:, j], C, ctrl=ctrl)["rho_corr"] if C.n >= 30 else np.nan
    out["rho_tamano"] = ps(E.X[:, i], E.X[:, j], E, ctrl=ctrl, tamano=True)["rho_corr"]
    return out


def clasificar(pares, escala_de, mecanico_de):
    """BH sobre el conjunto, categoría, robustez (calendario y épocas), tamaño y tipo."""
    q = corr.benjamini_hochberg([(k, pr["p"]) for k, pr in pares.items()])
    for k, pr in pares.items():
        pr["q"] = q.get(k, np.nan)
        cat, fuerza = corr.categoria_y_fuerza(False, pr["n"], pr["q"], pr["rho"], pr["ic_inf"], pr["ic_sup"])
        pr["categoria"], pr["fuerza"] = cat, fuerza
        pr["robusta"] = corr.es_robusta(cat, pr["estable_cal"], pr["rho"], pr["rho_canary"])
        pr["robusta_epocas"] = corr.es_robusta(cat, pr["estable_ep"], pr["rho"], pr["rho_canary"])
        ok = corr.resiste_tamano(pr["rho"], pr["rho_tamano"])
        pr["resiste_tamano"] = ok
        pr["escala"], pr["mecanico"] = escala_de(k), mecanico_de(k)
        for suf, rob in (("", pr["robusta"]), ("_epocas", pr["robusta_epocas"])):
            pr["patron" + suf] = bool(rob and not pr["escala"] and not pr["mecanico"] and ok is not False)
        pr["tipo"] = ("patrón" if pr["patron"] else "escala" if pr["robusta"] and pr["escala"]
                      else "mecánico" if pr["robusta"] and pr["mecanico"]
                      else "no resiste tamaño" if pr["robusta"] else
                      "patrón solo con épocas" if pr["patron_epocas"] else "")


# ── 1. medida global ─────────────────────────────────────────────────────────

def _base(B):
    Q, _ = np.linalg.qr(B - B.mean(0))
    return Q


def _estandar(B):
    B = B - B.mean(0)
    sd = B.std(0)
    return B / np.where(sd > 0, sd, 1)


def estadisticos(bloques):
    """GCCA (MAXVAR), RV medio entre pares de bloques y primer autovalor relativo del MFA."""
    Qs = [_base(B) for B in bloques]
    M = np.hstack(Qs)
    U, s, _ = np.linalg.svd(M, full_matrices=False)
    lam = float(s[0] ** 2)
    g = U[:, 0]
    z = [Q @ (Q.T @ g) for Q in Qs]
    rz = {f"{a}-{b}": float(np.corrcoef(z[a], z[b])[0, 1]) for a, b in combinations(range(len(z)), 2)}
    Zs = [_estandar(B) for B in bloques]
    rv = {}
    for a, b in combinations(range(len(Zs)), 2):
        num_ = np.linalg.norm(Zs[a].T @ Zs[b]) ** 2
        rv[f"{a}-{b}"] = float(num_ / math.sqrt(np.linalg.norm(Zs[a].T @ Zs[a]) ** 2 * np.linalg.norm(Zs[b].T @ Zs[b]) ** 2))
    W = np.hstack([Z / np.linalg.svd(Z, compute_uv=False)[0] for Z in Zs])
    sv = np.linalg.svd(W, compute_uv=False) ** 2
    return dict(gcca=lam, gcca_r=rz, rv=rv, rv_medio=float(np.mean(list(rv.values()))),
                mfa1=float(sv[0] / sv.sum()))


def mfa_factores(bloques, cols, k=2):
    """Correlación de cada componente original con los dos primeros factores del MFA y parte de la inercia de
    cada bloque en cada factor."""
    Zs = [_estandar(B) for B in bloques]
    W = np.hstack([Z / np.linalg.svd(Z, compute_uv=False)[0] for Z in Zs])
    U, s, Vt = np.linalg.svd(W, full_matrices=False)
    out = []
    Zall = np.hstack(Zs)
    sizes = [Z.shape[1] for Z in Zs]
    for f in range(min(k, len(s))):
        F = U[:, f] * s[f]
        cor = {c: float(np.corrcoef(Zall[:, t], F)[0, 1]) for t, c in enumerate(cols)}
        v2 = Vt[f] ** 2
        parte, t0 = [], 0
        for n_ in sizes:
            parte.append(float(v2[t0:t0 + n_].sum()))
            t0 += n_
        out.append(dict(factor=f + 1, inercia=float(s[f] ** 2 / (s ** 2).sum()), correlaciones=cor,
                        parte_por_dimension=dict(zip(DIMS, parte))))
    return out


def global_(S, cols, idx_dim, rng, n_perm, quitar=(), tamano=False):
    keep = [t for t in range(len(cols)) if cols[t] not in quitar]
    X = S.X.copy()
    filas = np.arange(S.n)
    if tamano:
        filas = filas[~np.isnan(S.size)]
        X = X[filas]
        ls = np.array([corr.safe_log(v + 1) for v in S.size[filas]])
        D = np.column_stack([np.ones(len(filas)), ls])
        X = X - D @ np.linalg.lstsq(D, X, rcond=None)[0]
    bloques = [X[:, [t for t in idx_dim[d] if t in keep]] for d in DIMS]
    obs = estadisticos(bloques)
    n = len(filas)
    margen = max(10, n // 10)
    nul = {k: [] for k in ("gcca", "rv_medio", "mfa1")}
    for _ in range(n_perm):
        bl = [bloques[0]] + [np.roll(B, rng.integers(margen, n - margen), axis=0) for B in bloques[1:]]
        e = estadisticos(bl)
        for k in nul:
            nul[k].append(e[k])
    res = dict(n=n, componentes=[cols[t] for t in keep], **{k: obs[k] for k in ("gcca", "rv_medio", "mfa1")},
               gcca_r=obs["gcca_r"], rv=obs["rv"])
    for k, v in nul.items():
        v = np.array(v)
        res[f"{k}_nula_p95"] = float(np.percentile(v, 95))
        res[f"{k}_p"] = float((1 + (v >= obs[k]).sum()) / (n_perm + 1))
    res["factores_mfa"] = mfa_factores(bloques, [cols[t] for t in keep], k=3)
    return res


# ── 4. perfiles y rezago ─────────────────────────────────────────────────────

def diferencia_tercios(a, y):
    lo, hi = np.percentile(a, [100 / 3, 200 / 3])
    sd = y.std()
    return float((y[a >= hi].mean() - y[a <= lo].mean()) / sd) if sd > 0 else np.nan


def perfiles(E, C, cols, rng):
    filas = []
    n = E.n
    margen = max(10, n // 10)
    for i, ci in enumerate(cols):
        if not ci.startswith("persona"):
            continue
        for j, cj in enumerate(cols):
            if cj.startswith("persona"):
                continue
            obs = diferencia_tercios(E.X[:, i], E.X[:, j])
            nula = np.array([diferencia_tercios(np.roll(E.X[:, i], rng.integers(margen, n - margen)), E.X[:, j])
                             for _ in range(N_PERM)])
            can = diferencia_tercios(C.X[:, i], C.X[:, j]) if C.n >= 30 else np.nan
            lo, hi = np.percentile(E.X[:, i], [100 / 3, 200 / 3])
            filas.append(dict(persona=ci, otro=cj, diferencia_desvios=obs,
                              p=float((1 + (np.abs(nula) >= abs(obs)).sum()) / (N_PERM + 1)),
                              nula_p95_abs=float(np.percentile(np.abs(nula), 95)), canary=can,
                              replica=num(can) and (can >= 0) == (obs >= 0),
                              anio_medio_alto=float(np.mean([a for a, v in zip(E.anio, E.X[:, i]) if v >= hi and a])),
                              anio_medio_bajo=float(np.mean([a for a, v in zip(E.anio, E.X[:, i]) if v <= lo and a]))))
    q = corr.benjamini_hochberg([(k, f["p"]) for k, f in enumerate(filas)])
    for k, f in enumerate(filas):
        f["q"] = q[k]
    return filas


def rezago(E, C, cols, idx_pares):
    """x en el release t contra y en el t+1 (y al revés), con la duración del release de y."""
    filas = []
    for i, j in idx_pares:
        for a, b in ((i, j), (j, i)):
            for nombre, S in (("estable", E), ("canary", C)):
                if S.n < 30:
                    continue
                x, y = S.X[:-1, a], S.X[1:, b]
                r = corr.partial_spearman(list(x), list(y), list(S.pn[1:]), list(S.du[1:]))
                if nombre == "estable":
                    filas.append(dict(antes=cols[a], despues=cols[b], rho=r["rho_corr"], p=r["p_corr"]))
                else:
                    filas[-1]["rho_canary"] = r["rho_corr"]
    q = corr.benjamini_hochberg([(k, f["p"]) for k, f in enumerate(filas)])
    for k, f in enumerate(filas):
        f["q"] = q[k]
        f["replica"] = num(f.get("rho_canary")) and (f["rho_canary"] >= 0) == (f["rho"] >= 0)
    return filas


# ── triángulos ───────────────────────────────────────────────────────────────

def tipo_triangulo(lados, cond):
    """lados: {arista: par marginal}; cond: {arista: par descontando el tercer vértice}."""
    pat = [a for a, pr in lados.items() if pr["patron"]]
    if len(pat) == 3:
        caen = [a for a in pat if not cond[a]["patron"]]
        return ("tridimensional", "") if not caen else ("cadena", "desaparece al descontar el tercero: " + ", ".join(caen))
    if len(pat) == 2:
        comun = set(pat[0].split("__")) & set(pat[1].split("__"))
        return "cadena", "a través de " + ", ".join(comun)
    if not pat and any(pr["robusta"] and pr["escala"] for pr in lados.values()):
        return "solo tamaño", ""
    return "pares sueltos", ", ".join(pat)


def escribir_csv(ruta, filas, cols):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for fila in filas:
            w.writerow({k: (r3(v) if isinstance(v, float) else v) for k, v in fila.items()})


def main():
    rng = np.random.default_rng(pca.SEMILLA)
    warnings.filterwarnings("ignore", message="An input array is constant")
    SALIDA.mkdir(parents=True, exist_ok=True)
    print("=== tres_dimensiones.py ===", flush=True)
    var_dict, datos = pca.cargar_datos()
    duraciones = {s: {} for s in ("versiones", "versiones_canary")}
    for v in datos:
        if v.startswith("__"):
            continue
        for s in duraciones:
            for p, t in datos[v].get(s, {}).items():
                if t[0] is not None:
                    duraciones[s].setdefault(p, t[0])
    cps = [c for d in DIMS for c in cruces.componentes(d, CFG, duraciones)]
    cols = [c["id"] for c in cps]
    assert cols == list(NOMBRES), cols
    sin_canary = [c["id"] for c in cps if not c["canary_serie"]]
    assert not sin_canary, f"sin serie canary: {sin_canary}"
    vars_de = {c["id"]: cruces.vars_cp(c, CARGA_MIN, var_dict) for c in cps}
    dim_de = {}
    for c in cps:
        for v in vars_de[c["id"]]:
            assert dim_de.setdefault(v, c["dim"]) == c["dim"], f"{v} en dos dimensiones"
    idx_dim = {d: [t for t, c in enumerate(cps) if c["dim"] == d] for d in DIMS}
    cortes = corr.cortes_epocas(datos)
    epoca = {p: 1 + sum(p >= c for c in cortes) for p in cps[0]["estable"]}
    size = datos["activos_interaccion_conteo"]
    E = Serie(cps, "estable", size["versiones"], epoca)
    C = Serie(cps, "canary_serie", size["versiones_canary"])
    print(f"  componentes: {', '.join(cols)} · releases estables {E.n} · canary {C.n}", flush=True)

    def escala_de(k):
        return any(c in ESCALA for c in k.split("__"))

    def mecanico_de(k):
        a, b = k.split("__")
        return cruces.solapan(vars_de[a], vars_de[b], var_dict)

    # ── 1. global ──
    print("  medida global…", flush=True)
    glob = {}
    for nombre, kw in VARIANTES.items():
        glob[nombre] = global_(E, cols, idx_dim, rng, N_PERM, **kw)
        glob[nombre + "_canary"] = global_(C, cols, idx_dim, rng, N_PERM_CANARY, **kw)

    # ── 2. red y triángulos ──
    print("  red de correlaciones parciales…", flush=True)
    cruzados = [(i, j) for i, j in combinations(range(len(cols)), 2) if cps[i]["dim"] != cps[j]["dim"]]
    red = {"marginal": {}, "parcial": {}}
    for i, j in cruzados:
        k = f"{cols[i]}__{cols[j]}"
        red["marginal"][k] = evaluar(i, j, (), E, C)
        red["parcial"][k] = evaluar(i, j, tuple(t for t in range(len(cols)) if t not in (i, j)), E, C)
    for cond in red.values():
        clasificar(cond, escala_de, mecanico_de)
    triangulos, cond3 = [], {}
    for a, b, c in product(*(idx_dim[d] for d in DIMS)):
        for x, y, z in ((a, b, c), (a, c, b), (b, c, a)):
            cond3[(f"{cols[x]}__{cols[y]}", cols[z])] = evaluar(x, y, (z,), E, C)
    clasificar(cond3, lambda k: escala_de(k[0]), lambda k: mecanico_de(k[0]))
    for a, b, c in product(*(idx_dim[d] for d in DIMS)):
        aristas = {f"{cols[x]}__{cols[y]}": cols[z] for x, y, z in ((a, b, c), (a, c, b), (b, c, a))}
        lados = {k: red["marginal"][k] for k in aristas}
        cond = {k: cond3[(k, z)] for k, z in aristas.items()}
        tipo, detalle = tipo_triangulo(lados, cond)
        lados_ep = {k: dict(pr, patron=pr["patron_epocas"]) for k, pr in lados.items()}
        cond_ep = {k: dict(pr, patron=pr["patron_epocas"]) for k, pr in cond.items()}
        tipo_ep, detalle_ep = tipo_triangulo(lados_ep, cond_ep)
        n_par = sum(red["parcial"][k]["patron"] for k in aristas)
        fila = dict(triangulo=" · ".join(cols[t] for t in (a, b, c)), tipo=tipo, detalle=detalle,
                    tipo_epocas=tipo_ep, detalle_epocas=detalle_ep,
                    tipo_red_parcial={3: "tridimensional", 2: "cadena"}.get(n_par, "pares sueltos"))
        for t, k in enumerate(aristas):
            fila[f"lado{t + 1}"] = k
            fila[f"lado{t + 1}_marginal"] = red["marginal"][k]["rho"]
            fila[f"lado{t + 1}_tipo"] = red["marginal"][k]["tipo"]
            fila[f"lado{t + 1}_sin_tercero"] = cond[k]["rho"]
            fila[f"lado{t + 1}_sin_tercero_tipo"] = cond[k]["tipo"]
            fila[f"lado{t + 1}_parcial_todos"] = red["parcial"][k]["rho"]
        triangulos.append(fila)

    # ── 2b. triangulación con variables ──
    print("  triangulación con variables…", flush=True)
    candidatos = {tuple(f["triangulo"].split(" · ")) for f in triangulos
                  if "pares sueltos" not in (f["tipo"], f["tipo_epocas"], f["tipo_red_parcial"]) or
                  f["tipo"] == "cadena" or f["tipo_epocas"] == "cadena" or f["tipo_red_parcial"] != "pares sueltos"}
    candidatos.add(TRIANGULO_ARTIFACT)
    trios = {}
    for tri in sorted(candidatos):
        for va, vb, vc in product(*(vars_de[c] for c in tri)):
            trios[(va, vb, vc)] = tri
    filas_v, pares_v, cond_v = [], {}, {}
    for (va, vb, vc), tri in trios.items():
        ser = {v: datos[v] for v in (va, vb, vc)}
        falsos = [dict(id=v, estable={p: (t[0], t[1], t[2], t[3], t[4]) for p, t in ser[v]["versiones"].items()},
                       canary_serie=ser[v]["versiones_canary"]) for v in (va, vb, vc)]
        Ev = Serie(falsos, "estable", size["versiones"], {p: 1 + sum(p >= c for c in cortes) for p in ser[va]["versiones"]})
        Cv = Serie(falsos, "canary_serie", size["versiones_canary"])
        for x, y, z in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
            k = (f"{(va, vb, vc)[x]}__{(va, vb, vc)[y]}", (va, vb, vc)[z])
            if k[0] not in pares_v:
                pares_v[k[0]] = evaluar(x, y, (), Ev, Cv)
            cond_v[k] = evaluar(x, y, (z,), Ev, Cv)
    meta = lambda k: corr.es_solapamiento_definicion(*k.split("__"), tuple(var_dict[v]["metrica_id"] for v in k.split("__")))
    esc = lambda k: any(var_dict[v].get("familia") == "tamano" for v in k.split("__"))
    clasificar(pares_v, esc, meta)
    clasificar(cond_v, lambda k: esc(k[0]), lambda k: meta(k[0]))
    for (va, vb, vc), tri in trios.items():
        aristas = {f"{va}__{vb}": vc, f"{va}__{vc}": vb, f"{vb}__{vc}": va}
        lados = {k: pares_v[k] for k in aristas}
        cond = {k: cond_v[(k, z)] for k, z in aristas.items()}
        tipo, detalle = tipo_triangulo(lados, cond)
        tipo_ep, _ = tipo_triangulo({k: dict(p, patron=p["patron_epocas"]) for k, p in lados.items()},
                                    {k: dict(p, patron=p["patron_epocas"]) for k, p in cond.items()})
        fila = dict(triangulo_componentes=" · ".join(tri), variables=f"{va} · {vb} · {vc}", tipo=tipo,
                    detalle=detalle, tipo_epocas=tipo_ep, n=lados[f"{va}__{vb}"]["n"])
        for t, k in enumerate(aristas):
            fila[f"lado{t + 1}"] = k
            fila[f"lado{t + 1}_marginal"] = lados[k]["rho"]
            fila[f"lado{t + 1}_tipo"] = lados[k]["tipo"]
            fila[f"lado{t + 1}_sin_tercero"] = cond[k]["rho"]
        filas_v.append(fila)

    # ── 3. PCA y clustering conjunto ──
    print("  PCA y clustering conjunto…", flush=True)
    vars_pca = sorted(dim_de)
    conj = {}
    for enf in ("ajustado", "tamano"):
        rp = cruces.pca_conjunto(vars_pca, datos, var_dict, enf, np.random.default_rng(pca.SEMILLA), CARGA_MIN, dim_de)
        rc = cruces.clustering_conjunto(vars_pca, datos, var_dict, enf, dim_de, rp)
        conj[enf] = dict(pca=rp, clustering=rc)

    # ── 4. perfiles y rezago ──
    print("  perfiles y rezago…", flush=True)
    perf = perfiles(E, C, cols, rng)
    rez = rezago(E, C, cols, cruzados)

    # ── escribir ──
    cols_red = ["condicion", "par", "tipo", "categoria", "fuerza", "rho", "ic_inf", "ic_sup", "q", "n", "n_efectiva",
                "rho_2016_2019", "rho_2020_2022", "rho_2023_2024", "rho_2025_2026", "estable_cal", "rho_E1", "rho_E2",
                "rho_E3", "rho_E4", "estable_ep", "rho_canary", "rho_tamano", "resiste_tamano", "robusta",
                "robusta_epocas", "escala", "mecanico", "patron", "patron_epocas"]
    filas_red = []
    for cond, pares in red.items():
        for k, pr in pares.items():
            f = dict(pr, condicion=cond, par=k)
            for lab, r in {**pr["per_cal"], **pr["per_ep"]}.items():
                f["rho_" + lab.replace("-", "_")] = r
            filas_red.append(f)
    escribir_csv(SALIDA / "red.csv", filas_red, cols_red)
    escribir_csv(SALIDA / "triangulos.csv", triangulos, list(triangulos[0]))
    escribir_csv(SALIDA / "triangulacion_variables.csv", filas_v, list(filas_v[0]) if filas_v else ["triangulo"])
    escribir_csv(SALIDA / "perfiles.csv", perf, list(perf[0]))
    escribir_csv(SALIDA / "rezago.csv", rez, ["antes", "despues", "rho", "p", "q", "rho_canary", "replica"])
    resumen = dict(componentes={c["id"]: dict(nombre=NOMBRES[c["id"]], dimension=c["dim"], n=c["n"],
                                              variables=vars_de[c["id"]]) for c in cps},
                   asignacion=ASIGNACION, releases=dict(estable=E.n, canary=C.n), global_=glob,
                   conjunto=conj)
    (SALIDA / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    escribir_md(cps, E, C, glob, red, triangulos, filas_v, conj, perf, rez)
    print(f"  listo: {SALIDA}")


def escribir_md(cps, E, C, glob, red, triangulos, filas_v, conj, perf, rez):
    L = ["# Análisis tridimensional", "",
         f"{E.n} releases estables y {C.n} canary con los siete componentes. Nula: {N_PERM} corrimientos circulares "
         f"de cada dimensión por separado ({N_PERM_CANARY} en canary).", "",
         "## Componentes", "", "| Componente | Dimensión | Variables que lo definen |", "|---|---|---|"]
    for c in cps:
        L.append(f"| {c['id']} · {NOMBRES[c['id']]} | {c['dim']} | {', '.join(f'{v} ({x:+.2f})' for v, x in c['cargas'] if abs(x) >= CARGA_MIN)} |")
    L += ["", "## 1. Medida global", "",
          "| Variante | Serie | n | GCCA (1 a 3) | nula p95 | p | RV medio | nula p95 | p | MFA factor 1 | nula p95 | p |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for nombre in VARIANTES:
        for suf, serie in (("", "estable"), ("_canary", "canary")):
            g = glob[nombre + suf]
            L.append(f"| {nombre.replace('_', ' ')} | {serie} | {g['n']} | {g['gcca']:.3f} | {g['gcca_nula_p95']:.3f} | "
                     f"{g['gcca_p']:.3f} | {g['rv_medio']:.3f} | {g['rv_medio_nula_p95']:.3f} | {g['rv_medio_p']:.3f} | "
                     f"{g['mfa1']:.3f} | {g['mfa1_nula_p95']:.3f} | {g['mfa1_p']:.3f} |")
    L += ["", "Correlación entre las variables canónicas de cada par de dimensiones (0 Persona, 1 Proceso, 2 Producto) y RV por par:", ""]
    for nombre in VARIANTES:
        g = glob[nombre]
        L.append(f"- **{nombre.replace('_', ' ')}:** GCCA " + ", ".join(f"{k} {v:+.2f}" for k, v in g["gcca_r"].items())
                 + " · RV " + ", ".join(f"{k} {v:.2f}" for k, v in g["rv"].items()))
    L += ["", "Factores del MFA (correlación de cada componente con el factor; parte de la inercia de cada dimensión; "
          "congruencia de Tucker con el factor más parecido de canary):", ""]
    for nombre in VARIANTES:
        fc = glob[nombre + "_canary"]["factores_mfa"]
        for f in glob[nombre]["factores_mfa"]:
            fuertes = ", ".join(f"{k} {v:+.2f}" for k, v in sorted(f["correlaciones"].items(), key=lambda t: -abs(t[1])) if abs(v) >= 0.4)
            partes = ", ".join(f"{d} {p:.0%}" for d, p in f["parte_por_dimension"].items())
            dims = sorted({c.split("_")[0] for c, v in f["correlaciones"].items() if abs(v) >= 0.4})
            ve = np.array(list(f["correlaciones"].values()))
            tk = [(abs(pca.tucker(ve, np.array([g["correlaciones"][c] for c in f["correlaciones"]]))), g["factor"]) for g in fc]
            t, g = max(tk)
            L.append(f"- {nombre.replace('_', ' ')}, factor {f['factor']} ({f['inercia']:.0%}, {len(dims)} dimensiones): "
                     f"{fuertes or '—'} · {partes} · canary: factor {g}, congruencia {t:.2f}")
    L += ["", "## 2. Red de correlaciones parciales", "",
          "Marginal = el cruce de componentes de siempre; parcial = descontando los otros cinco componentes.", "",
          "| Par | Marginal | tipo | Parcial | tipo | canary (parcial) | tamaño (parcial) |", "|---|---|---|---|---|---|---|"]
    for k in red["marginal"]:
        m, p = red["marginal"][k], red["parcial"][k]
        L.append(f"| {k.replace('__', ' ↔ ')} | {f2(m['rho'])} | {m['tipo'] or m['categoria']} | {f2(p['rho'])} | "
                 f"{p['tipo'] or p['categoria']} | {f2(p['rho_canary'])} | {f2(p['rho_tamano'])} |")
    L += ["", "### Triángulos (un componente por dimensión)", "",
          "| Triángulo | Tipo (calendario) | Tipo (épocas) | Red parcial | Lados: marginal → sin el tercer vértice |", "|---|---|---|---|---|"]
    for f in triangulos:
        lados = "; ".join(f"{f[f'lado{t}'].replace('__', '↔')} {f2(f[f'lado{t}_marginal'])} → {f2(f[f'lado{t}_sin_tercero'])}"
                          + (f" ({f[f'lado{t}_tipo']})" if f[f"lado{t}_tipo"] else "") for t in (1, 2, 3))
        L.append(f"| {f['triangulo']} | {f['tipo']} {f['detalle']} | {f['tipo_epocas']} {f['detalle_epocas']} | {f['tipo_red_parcial']} | {lados} |")
    L += ["", "### Triangulación con variables", ""]
    cuenta = {}
    for f in filas_v:
        cuenta.setdefault(f["triangulo_componentes"], {}).setdefault(f["tipo"], 0)
        cuenta[f["triangulo_componentes"]][f["tipo"]] += 1
    for tri, c in cuenta.items():
        L.append(f"- **{tri}:** " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())))
    destacados = [f for f in filas_v if f["tipo"] in ("tridimensional", "cadena") or f["tipo_epocas"] in ("tridimensional", "cadena")]
    if destacados:
        L += ["", "| Variables | Tipo | Tipo (épocas) | Lados: marginal → sin el tercero |", "|---|---|---|---|"]
        for f in destacados:
            lados = "; ".join(f"{f[f'lado{t}'].replace('__', '↔')} {f2(f[f'lado{t}_marginal'])} → {f2(f[f'lado{t}_sin_tercero'])}"
                              + (f" ({f[f'lado{t}_tipo']})" if f[f"lado{t}_tipo"] else "") for t in (1, 2, 3))
            L.append(f"| {f['variables']} | {f['tipo']} {f['detalle']} | {f['tipo_epocas']} | {lados} |")
    L += ["", "## 3. PCA y clustering conjunto", ""]
    for enf, r in conj.items():
        rp = r["pca"]
        if "error" in rp:
            L.append(f"- {enf}: {rp['error']}")
            continue
        L.append(f"**{enf}** ({rp['variables']} variables, {rp['n']} releases, k = {rp['k']}):")
        for c in rp["componentes"]:
            marca = " **(tres dimensiones)**" if len(c["dimensiones"]) == 3 else " (dos dimensiones)" if c["mixto"] else ""
            L.append(f"- CP{c['n']} ({c['varianza']:.0%}, bootstrap {c['bootstrap']:.2f}){marca}: "
                     + ", ".join(f"{v} {x:+.2f}" for v, x in c["cargas"][:8]))
        rc = r["clustering"]
        for nombre, s in rc.get("soluciones", {}).items():
            mixtos = [g for g in s["grupos"] if g["mixto"]]
            L.append(f"- clustering ({nombre}, k = {s['k']}, silueta {s['silueta']} frente a {s['nula_p95']}): "
                     + ("; ".join(f"[{', '.join(g['dimensiones'])}] {', '.join(g['variables'])}" for g in mixtos) or "ningún grupo mixto"))
        L.append("")
    L += ["## 4. Perfiles de releases", "",
          "Diferencia entre el tercio de releases con el puntaje más alto y el más bajo del componente de Persona, en desvíos del otro componente.", "",
          "| Persona | Otro | Diferencia | nula p95 | q | canary | años (alto / bajo) |", "|---|---|---|---|---|---|---|"]
    for f in perf:
        L.append(f"| {f['persona']} | {f['otro']} | {f2(f['diferencia_desvios'])} | ±{f['nula_p95_abs']:.2f} | {f['q']:.3f} | "
                 f"{f2(f['canary'])} | {f['anio_medio_alto']:.0f} / {f['anio_medio_bajo']:.0f} |")
    L += ["", "## Rezago de un release (descriptivo)", "", "| Antes | Después | ρ | q | canary |", "|---|---|---|---|---|"]
    for f in sorted(rez, key=lambda f: f["q"])[:10]:
        L.append(f"| {f['antes']} | {f['despues']} | {f2(f['rho'])} | {f['q']:.3f} | {f2(f.get('rho_canary'))} |")
    (SALIDA / "resumen.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
