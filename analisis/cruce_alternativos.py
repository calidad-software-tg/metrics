#!/usr/bin/env python3
"""
analisis/cruce_alternativos.py

Corre sobre un cruce entre dimensiones los métodos que cruce_dimensiones.md deja como alternativas
descartadas, para comprobar con los datos si aportan algo que el análisis principal no ve:

  1. CCA sobre todas las variables (y, para comparar, sobre los componentes firmes).
  2. Reglas de asociación (support, confidence, lift) sobre terciles.
  3. Clustering de releases (k-means), con y sin el ajuste por tiempo y duración.
  4. Clustering de métricas (jerárquico) comparado con los componentes del PCA.
  5. Regresión multivariable (cada métrica de un lado con todas las del otro).
  6. Información mutua por par, para buscar dependencias no monótonas.
  7. Random forest, para buscar relaciones no lineales o combinadas.

Todos usan los mismos releases y la misma transformación que el PCA ajustado: rangos, descontada la
tendencia en el tiempo (spline) y la duración de la ventana, y estandarizados. Cada método tiene
un criterio fijado de antemano para decir si aporta:
  - se compara con una nula que respeta el orden en el tiempo: uno de los lados se corre en forma
    circular respecto del otro, así cada lado conserva su autocorrelación pero se rompe el vínculo;
  - lo que encuentra tiene que repetirse en canary, que es una muestra independiente de ventanas;
  - y tiene que ser algo que el cruce de variables y de componentes no haya encontrado ya.

Uso (después de cruce_dimensiones.py, porque compara con sus resultados):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruce_alternativos.py Persona Producto \\
        --config analisis/cruces/persona_producto.json

Salidas en analisis/salidas/cruces/<dima>_<dimb>/alternativos/:
    resumen.md (veredicto por método), resumen.json y un CSV por método.
"""
import argparse
import csv
import json
import os
import sys
import warnings
from pathlib import Path

import numpy as np
from scipy.stats import norm, rankdata, spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cruce_dimensiones as cd  # noqa: E402
import generar_correlaciones as gc  # noqa: E402
import generar_pca as gp  # noqa: E402

os.environ.setdefault("PYTHONWARNINGS", "ignore")  # también en los procesos de joblib
try:
    from sklearn.cluster import KMeans
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.feature_selection import mutual_info_regression
    from sklearn.inspection import permutation_importance
    from sklearn.metrics import adjusted_rand_score, silhouette_score
except ImportError:
    sys.exit("Falta scikit-learn: python3 -m pip install scikit-learn")

MIN_COBERTURA = 0.6      # parte de los releases estables en que una variable tiene que tener dato
PERIODOS = [(2016, 2019), (2020, 2022), (2023, 2024), (2025, 2026)]
SOPORTE_MIN, LIFT_MIN = 0.10, 1.5
MIN_DISTINTOS = 10       # menos valores distintos: la información mutua (k vecinos) se sesga con los empates
PLIEGUES = 5             # validación cruzada en bloques contiguos (sin mezclar el orden en el tiempo)


# ── datos ────────────────────────────────────────────────────────────────────

def matriz(variables, datos, serie_db):
    """Releases con dato en todas las variables, transformados como el PCA ajustado."""
    filas, _ = gp.tabla(variables, datos, serie_db)
    if len(filas) < 30:
        return None, [], {}
    Z, pnums = gp.transformar(filas, "ajustado")
    Zc, _ = gp.transformar(filas, "crudo")
    Zt, pt = gp.transformar(filas, "tamano")
    return Z, pnums, dict(crudo=Zc, anio=[filas[p]["anio"] for p in pnums], tamano=Zt if len(pt) == len(pnums) else None)


def elegir_variables(lado, datos, var_dict):
    """Saca las variables con poca cobertura o casi constantes (misma regla que el PCA)."""
    n_tot = max(len(datos[v]["versiones"]) for v in lado)
    out, fuera = [], []
    for v in lado:
        s = {p: t for p, t in datos[v]["versiones"].items() if t[1] is not None}
        vals = [t[1] for t in s.values()]
        if len(s) < MIN_COBERTURA * n_tot:
            fuera.append((v, f"cobertura {len(s)}/{n_tot}"))
        elif vals and max(vals.count(x) for x in set(vals)) / len(vals) > gp.MAX_PCT_MODA:
            fuera.append((v, "casi constante"))
        else:
            out.append(v)
    return out, fuera


def corrimientos(n, k, rng):
    """k corrimientos circulares, lejos de 0 para no dejar la serie casi alineada."""
    margen = max(5, n // 10)
    return rng.integers(margen, n - margen, size=k)


def p_normal(obs, nula):
    """p de cola superior con la nula aproximada por una normal: permite p más chicos que 1/(k+1),
    que hacen falta para sobrevivir a la corrección por comparaciones múltiples."""
    nula = np.asarray(nula, dtype=float)
    sd = nula.std(ddof=1)
    return float(norm.sf((obs - nula.mean()) / sd)) if sd > 0 else 1.0


def p_valor(obs, nula):
    nula = np.asarray(nula, dtype=float)
    return float((1 + np.sum(nula >= obs)) / (1 + len(nula)))


def bh(ps):
    ps = np.asarray(ps, dtype=float)
    orden = np.argsort(ps)
    q = np.empty_like(ps)
    acum = 1.0
    for i in range(len(ps) - 1, -1, -1):
        j = orden[i]
        acum = min(acum, ps[j] * len(ps) / (i + 1))
        q[j] = acum
    return q


def periodo_de(anio):
    for i, (a, b) in enumerate(PERIODOS):
        if a <= anio <= b:
            return i
    return len(PERIODOS) - 1


def pliegues(n):
    cortes = np.linspace(0, n, PLIEGUES + 1).astype(int)
    return [(np.r_[0:cortes[i], cortes[i + 1]:n], np.arange(cortes[i], cortes[i + 1])) for i in range(PLIEGUES)]


def r2(y, yhat):
    sst = float(np.sum((y - y.mean()) ** 2))
    return 1 - float(np.sum((y - yhat) ** 2)) / sst if sst > 0 else np.nan


def escribir(ruta, filas):
    if not filas:
        ruta.write_text("", encoding="utf-8")
        return
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        for fl in filas:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in fl.items()})


# ── 1. CCA ───────────────────────────────────────────────────────────────────

def corr_canonicas(X, Y, ridge=1e-6):
    X = X - X.mean(0)
    Y = Y - Y.mean(0)
    n = len(X)
    Sxx = X.T @ X / (n - 1) + ridge * np.eye(X.shape[1])
    Syy = Y.T @ Y / (n - 1) + ridge * np.eye(Y.shape[1])
    Sxy = X.T @ Y / (n - 1)
    Wx = np.linalg.inv(np.linalg.cholesky(Sxx)).T
    Wy = np.linalg.inv(np.linalg.cholesky(Syy)).T
    U, s, Vt = np.linalg.svd(Wx.T @ Sxy @ Wy)
    return np.clip(s, 0, 1), Wx @ U[:, 0], Wy @ Vt[0]


def cca_bloque(nombre, A, B, Ac, Bc, n_perm, rng):
    s, wa, wb = corr_canonicas(A, B)
    nula = [corr_canonicas(A, np.roll(B, k, axis=0))[0][0] for k in corrimientos(len(A), n_perm, rng)]
    rep = np.nan
    if Ac is not None and len(Ac) > 30:
        rep = float(np.corrcoef(Ac @ wa, Bc @ wb)[0, 1])
    return dict(conjunto=nombre, variables_a=A.shape[1], variables_b=B.shape[1], n=len(A),
                r1=float(s[0]), r2=float(s[1]) if len(s) > 1 else np.nan,
                nula_p50=float(np.median(nula)), nula_p95=float(np.percentile(nula, 95)),
                p=p_valor(s[0], nula), canary_r1=rep)


# ── 2. reglas de asociación ──────────────────────────────────────────────────

def terciles(Z):
    T = np.zeros_like(Z, dtype=int)
    for j in range(Z.shape[1]):
        q1, q2 = np.quantile(Z[:, j], [1 / 3, 2 / 3])
        T[:, j] = np.where(Z[:, j] <= q1, 0, np.where(Z[:, j] <= q2, 1, 2))
    return T


def reglas(TA, TB, va, vb, base_de, con_pares=True):
    """Reglas A → B con un ítem (o dos ítems de A) y uno de B, sobre los extremos bajo/alto."""
    n = len(TA)
    itA = {(va[j], niv): TA[:, j] == niv for j in range(len(va)) for niv in (0, 2)}
    itB = {(vb[j], niv): TB[:, j] == niv for j in range(len(vb)) for niv in (0, 2)}
    sup = {k: m.mean() for k, m in itB.items()}
    out = []
    claves = list(itA)
    antecedentes = [((k,), m) for k, m in itA.items()]
    if con_pares:
        for i in range(len(claves)):
            for j in range(i + 1, len(claves)):
                if claves[i][0] == claves[j][0]:
                    continue
                m = itA[claves[i]] & itA[claves[j]]
                if m.mean() >= SOPORTE_MIN:
                    antecedentes.append(((claves[i], claves[j]), m))
    for ant, m in antecedentes:
        s_ant = m.mean()
        if s_ant < SOPORTE_MIN:
            continue
        for kb, mb in itB.items():
            if any(base_de[a[0]] == base_de[kb[0]] for a in ant):
                continue
            s = (m & mb).mean()
            if s < SOPORTE_MIN:
                continue
            conf = s / s_ant
            lift = conf / sup[kb] if sup[kb] else np.nan
            out.append(dict(antecedente=ant, consecuente=kb, soporte=s, confianza=conf, lift=lift))
    return out


def nivel(n):
    return "alto" if n == 2 else "bajo"


# ── 5–7. modelos ─────────────────────────────────────────────────────────────

def ols_cv(X, y):
    pred = np.empty_like(y)
    for tr, te in pliegues(len(y)):
        Xt = np.column_stack([np.ones(len(tr)), X[tr]])
        coef, *_ = np.linalg.lstsq(Xt, y[tr], rcond=None)
        pred[te] = np.column_stack([np.ones(len(te)), X[te]]) @ coef
    return r2(y, pred)


def rf_modelo(semilla):
    return RandomForestRegressor(n_estimators=300, min_samples_leaf=5, max_features=0.33, random_state=semilla, n_jobs=-1)


def rf_cv(X, y, semilla):
    pred = np.empty_like(y)
    for tr, te in pliegues(len(y)):
        pred[te] = rf_modelo(semilla).fit(X[tr], y[tr]).predict(X[te])
    return r2(y, pred)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dim_a")
    ap.add_argument("dim_b")
    ap.add_argument("--config")
    ap.add_argument("--permutaciones", type=int, default=200, help="corrimientos de la nula (200)")
    args = ap.parse_args()
    dim_a, dim_b = (d.strip().capitalize() for d in (args.dim_a, args.dim_b))
    cfg = cd.mezclar(cd.DEFAULTS, json.loads(Path(args.config).read_text(encoding="utf-8")) if args.config else {})
    rng = np.random.default_rng(gp.SEMILLA)
    warnings.filterwarnings("ignore")
    base = cd.SALIDA / f"{dim_a.lower()}_{dim_b.lower()}"
    if not (base / "pares_variables.csv").exists():
        sys.exit(f"Falta {base / 'pares_variables.csv'}: corré antes cruce_dimensiones.py {dim_a} {dim_b}.")
    destino = base / "alternativos"
    destino.mkdir(parents=True, exist_ok=True)
    NP = args.permutaciones

    print(f"=== cruce_alternativos.py · {dim_a}–{dim_b} ===", flush=True)
    var_dict, datos = gp.cargar_datos()
    lados, _ = cd.armar_lados(dim_a, dim_b, var_dict, cfg)
    va, fuera_a = elegir_variables(lados[dim_a], datos, var_dict)
    vb, fuera_b = elegir_variables(lados[dim_b], datos, var_dict)
    todas = va + vb
    Z, pnums, extra = matriz(todas, datos, "versiones")
    Zc_can, pn_can, _ = matriz(todas, datos, "versiones_canary")
    if Z is None:
        sys.exit("No hay releases con dato en todas las variables.")
    A, B = Z[:, :len(va)], Z[:, len(va):]
    Acan, Bcan = (Zc_can[:, :len(va)], Zc_can[:, len(va):]) if Zc_can is not None else (None, None)
    nombre = {v: var_dict[v]["nombre_legible"] for v in todas}
    base_de = {v: gc.metrica_base(var_dict[v]["metrica_id"]) for v in todas}
    # una métrica que está en los dos lados (ANMCC por persona y del producto, etc.) es un par de control:
    # se saca de los predictores de su propia métrica y, en la CCA, del lado A
    bases_b = {base_de[v] for v in vb}
    ia_cca = [i for i, v in enumerate(va) if base_de[v] not in bases_b]
    # explicaciones triviales que el análisis principal ya descarta: tamaño y definiciones superpuestas
    escala = {v for v in todas if var_dict[v].get("familia") == "tamano"}
    solapa = lambda x, y: gc.es_solapamiento_definicion(x, y, (var_dict[x]["metrica_id"], var_dict[y]["metrica_id"]))
    ia_limpio = [i for i in ia_cca if va[i] not in escala and not any(solapa(va[i], y) for y in vb)]
    distintos = {v: len({t[1] for t in datos[v]["versiones"].values() if t[1] is not None}) for v in todas}
    pocos = {v for v in todas if distintos[v] < MIN_DISTINTOS}
    print(f"  {dim_a}: {len(va)} variables · {dim_b}: {len(vb)} · releases estables {len(pnums)} · canary {len(pn_can)}")
    for v, r in fuera_a + fuera_b:
        print(f"    fuera: {v} ({r})")

    # lo que ya encontró el análisis principal
    sig, patrones = set(), set()
    with open(base / "pares_variables.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["categoria"] in ("positiva", "negativa"):
                sig.add((r["x_id"], r["y_id"]))
            if r["tipo"] == "patrón":
                patrones.add((r["x_id"], r["y_id"]))
    res = {}

    # ── 1. CCA ──
    print("  1. CCA…", flush=True)
    filas_cca = [cca_bloque("todas las variables", A[:, ia_cca], B, Acan[:, ia_cca] if Acan is not None else None, Bcan, NP, rng),
                 cca_bloque("sin escala ni definiciones superpuestas", A[:, ia_limpio], B, Acan[:, ia_limpio] if Acan is not None else None, Bcan, NP, rng)]
    # qué variables arman la primera correlación canónica en la versión limpia
    s_, wa_, wb_ = corr_canonicas(A[:, ia_limpio], B)
    ua, ub = A[:, ia_limpio] @ wa_, B @ wb_
    arma_a = sorted(((abs(np.corrcoef(A[:, i], ua)[0, 1]), va[i]) for i in ia_limpio), reverse=True)[:5]
    arma_b = sorted(((abs(np.corrcoef(B[:, j], ub)[0, 1]), vb[j]) for j in range(len(vb))), reverse=True)[:4]
    filas_cca[1]["arman_a"] = ", ".join(f"{v} ({x:.2f})" for x, v in arma_a)
    filas_cca[1]["arman_b"] = ", ".join(f"{v} ({x:.2f})" for x, v in arma_b)
    filas_cca[0]["arman_a"] = filas_cca[0]["arman_b"] = ""
    duraciones = {s: {} for s in ("versiones", "versiones_canary")}
    for v in datos:
        if not v.startswith("__"):
            for s in duraciones:
                for p, t in datos[v].get(s, {}).items():
                    if t[0] is not None:
                        duraciones[s].setdefault(p, t[0])
    cps = {d: cd.componentes(d, cfg, duraciones) for d in (dim_a, dim_b)}

    def mat_cp(lista, serie):
        comunes = sorted(set.intersection(*(set(c[serie]) for c in lista)))
        return np.array([[c[serie][p][1] for c in lista] for p in comunes], dtype=float), comunes

    if cps[dim_a] and cps[dim_b]:
        Ma, pa = mat_cp(cps[dim_a], "estable")
        Mb, pb = mat_cp(cps[dim_b], "estable")
        com = sorted(set(pa) & set(pb))
        Ma2 = Ma[[pa.index(p) for p in com]]
        Mb2 = Mb[[pb.index(p) for p in com]]
        can_a = [c for c in cps[dim_a] if c["canary_serie"]]
        can_b = [c for c in cps[dim_b] if c["canary_serie"]]
        Mca = Mcb = None
        if len(can_a) == len(cps[dim_a]) and len(can_b) == len(cps[dim_b]):
            Ca, qa = mat_cp(can_a, "canary_serie")
            Cb, qb = mat_cp(can_b, "canary_serie")
            cc = sorted(set(qa) & set(qb))
            Mca, Mcb = Ca[[qa.index(p) for p in cc]], Cb[[qb.index(p) for p in cc]]
        filas_cca.append(cca_bloque("componentes firmes", Ma2, Mb2, Mca, Mcb, NP, rng))
    escribir(destino / "cca.csv", filas_cca)
    t = filas_cca[0]
    tl = filas_cca[1]
    # aporta si, sin las explicaciones triviales, queda una relación global que se repite en canary
    res["cca"] = dict(filas=filas_cca, aporta=bool(tl["p"] < 0.05 and tl["canary_r1"] > 0.3))

    # ── 2. reglas de asociación ──
    print("  2. reglas de asociación…", flush=True)
    TA, TB = terciles(A), terciles(B)
    obs = reglas(TA, TB, va, vb, base_de)
    fuertes = [r for r in obs if r["lift"] >= LIFT_MIN]
    nula_n = [sum(r["lift"] >= LIFT_MIN for r in reglas(TA, np.roll(TB, k, axis=0), va, vb, base_de))
              for k in corrimientos(len(TA), min(NP, 50), rng)]
    rep_can = {}
    if Acan is not None:
        TAc, TBc = terciles(Acan), terciles(Bcan)
        for r in reglas(TAc, TBc, va, vb, base_de):
            rep_can[(r["antecedente"], r["consecuente"])] = r["lift"]
    filas_r = []
    for r in sorted(fuertes, key=lambda r: -r["lift"]):
        pares = {(a[0], r["consecuente"][0]) for a in r["antecedente"]}
        filas_r.append(dict(
            regla=" y ".join(f"{nombre[a]} {nivel(n)}" for a, n in r["antecedente"]) + f" → {nombre[r['consecuente'][0]]} {nivel(r['consecuente'][1])}",
            items=len(r["antecedente"]), soporte=r["soporte"], confianza=r["confianza"], lift=r["lift"],
            lift_canary=rep_can.get((r["antecedente"], r["consecuente"]), np.nan),
            ya_significativo=all(p in sig for p in pares), ya_patron=any(p in patrones for p in pares),
            con_escala=any(a in escala for a, _ in r["antecedente"]),
            con_solapamiento=any(solapa(a, r["consecuente"][0]) for a, _ in r["antecedente"]),
            pocos_valores=any(v in pocos for v in [a for a, _ in r["antecedente"]] + [r["consecuente"][0]])))
    escribir(destino / "reglas.csv", filas_r)
    nuevas_rep = [f for f in filas_r if not f["ya_significativo"] and not f["con_escala"] and not f["con_solapamiento"]
                  and not f["pocos_valores"] and f["lift_canary"] >= 1.2]
    res["reglas"] = dict(reglas=len(obs), fuertes=len(fuertes), nula_p50=float(np.median(nula_n)),
                         nula_p95=float(np.percentile(nula_n, 95)), p=p_valor(len(fuertes), nula_n),
                         ya_significativas=sum(f["ya_significativo"] for f in filas_r),
                         nuevas_que_replican=len(nuevas_rep),
                         ejemplos_nuevas=[f["regla"] for f in sorted(nuevas_rep, key=lambda f: -f["lift_canary"])[:5]])
    res["reglas"]["aporta"] = bool(res["reglas"]["p"] < 0.05 and len(nuevas_rep) >= 3)

    # ── 3. clustering de releases ──
    print("  3. clustering de releases…", flush=True)
    per = np.array([periodo_de(a) for a in extra["anio"]])

    def cramer(a, b):
        tab = np.zeros((a.max() + 1, b.max() + 1))
        for i, j in zip(a, b):
            tab[i, j] += 1
        e = tab.sum(1, keepdims=True) @ tab.sum(0, keepdims=True) / tab.sum()
        chi = np.nansum((tab - e) ** 2 / np.where(e > 0, e, np.nan))
        return float(np.sqrt(chi / (tab.sum() * (min(tab.shape) - 1))))

    filas_k = []
    for enfoque, M in (("crudo", extra["crudo"]), ("ajustado", Z)):
        for k in range(2, 7):
            lab = KMeans(k, n_init=20, random_state=gp.SEMILLA).fit_predict(M)
            sil = float(silhouette_score(M, lab))
            nula = []
            for _ in range(min(NP, 50)):
                Mn = np.column_stack([np.roll(M[:, j], rng.integers(0, len(M))) for j in range(M.shape[1])])
                nula.append(silhouette_score(Mn, KMeans(k, n_init=5, random_state=gp.SEMILLA).fit_predict(Mn)))
            # estabilidad: mitades de releases (pares e impares) dan los mismos grupos
            l1 = KMeans(k, n_init=20, random_state=gp.SEMILLA).fit(M[0::2]).predict(M)
            l2 = KMeans(k, n_init=20, random_state=gp.SEMILLA).fit(M[1::2]).predict(M)
            filas_k.append(dict(enfoque=enfoque, k=k, silueta=sil, nula_p95=float(np.percentile(nula, 95)),
                                p=p_valor(sil, nula), estabilidad_ari=float(adjusted_rand_score(l1, l2)),
                                v_cramer_periodo=cramer(lab, per),
                                tamanos="/".join(str(int((lab == i).sum())) for i in range(k))))
    escribir(destino / "clustering_releases.csv", filas_k)
    aj = [f for f in filas_k if f["enfoque"] == "ajustado"]
    mejor = max(aj, key=lambda f: f["silueta"])
    mejor_c = max((f for f in filas_k if f["enfoque"] == "crudo"), key=lambda f: f["silueta"])
    res["clustering_releases"] = dict(mejor_ajustado=mejor, mejor_crudo=mejor_c,
                                      aporta=bool(mejor["p"] < 0.05 and mejor["silueta"] >= 0.25 and mejor["estabilidad_ari"] >= 0.7))

    # ── 4. clustering de métricas ──
    print("  4. clustering de métricas…", flush=True)
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import squareform
    R = np.corrcoef(Z, rowvar=False)
    D = 1 - np.abs(np.nan_to_num(R))
    np.fill_diagonal(D, 0)
    L = linkage(squareform(D, checks=False), "average")
    # referencia: componente firme donde más carga cada variable (o "sin componente")
    ref = {}
    for d in (dim_a, dim_b):
        for c in cps[d]:
            for v, x in c["cargas"]:
                if abs(x) >= cfg["carga_minima"] and (v not in ref or abs(x) > ref[v][1]):
                    ref[v] = (c["id"], abs(x))
    ref_lab = np.array([hash(ref[v][0]) % 10 ** 6 if v in ref else -1 - i for i, v in enumerate(todas)])
    n_ref = len({ref[v][0] for v in ref})
    filas_m = []
    for k in sorted({max(2, n_ref), n_ref + 2, n_ref + 4}):
        lab = fcluster(L, k, "maxclust")
        mezcla = sum(1 for g in set(lab) if {v in va for v, l in zip(todas, lab) if l == g} == {True, False})
        # estabilidad: el mismo corte con la mitad de los releases
        Rm = np.corrcoef(Z[0::2], rowvar=False)
        Dm = 1 - np.abs(np.nan_to_num(Rm))
        np.fill_diagonal(Dm, 0)
        lm = fcluster(linkage(squareform(Dm, checks=False), "average"), k, "maxclust")
        grupos = [", ".join(v for v, l in zip(todas, lab) if l == g) for g in sorted(set(lab))]
        filas_m.append(dict(k=k, ari_con_pca=float(adjusted_rand_score(ref_lab, lab)), estabilidad_ari=float(adjusted_rand_score(lab, lm)),
                            grupos_que_mezclan_dimensiones=mezcla,
                            grupos=" | ".join(g for g in grupos if "," in g)))
    escribir(destino / "clustering_metricas.csv", filas_m)
    fm = filas_m[0]
    res["clustering_metricas"] = dict(filas=filas_m, componentes_referencia=n_ref,
                                      aporta=bool(fm["ari_con_pca"] < 0.5 and fm["estabilidad_ari"] >= 0.7 and fm["grupos_que_mezclan_dimensiones"] > 0))

    # ── 5 y 7. regresión y random forest: cada variable de B con todas las de A ──
    print("  5/7. regresión multivariable y random forest…", flush=True)
    filas_mod = []
    A_todo, Acan_todo = A, Acan
    Zt = extra["tamano"]
    for j, y_id in enumerate(vb):
        cols = [i for i, v in enumerate(va) if base_de[v] != base_de[y_id] and not solapa(v, y_id)]
        y = B[:, j]
        A, Acan_j = A_todo[:, cols], (Acan_todo[:, cols] if Acan_todo is not None else None)
        r2_ols = ols_cv(A, y)
        r2_rf = rf_cv(A, y, gp.SEMILLA)
        ks = corrimientos(len(y), 20, rng)
        nula_ols = [ols_cv(A, np.roll(y, k)) for k in corrimientos(len(y), min(NP, 100), rng)]
        nula_rf = [rf_cv(A, np.roll(y, k), gp.SEMILLA) for k in ks]
        # réplica en canary: el modelo ajustado en estable predice canary
        r2c_ols = r2c_rf = np.nan
        if Acan_j is not None:
            Xt = np.column_stack([np.ones(len(A)), A])
            coef, *_ = np.linalg.lstsq(Xt, y, rcond=None)
            r2c_ols = r2(Bcan[:, j], np.column_stack([np.ones(len(Acan_j)), Acan_j]) @ coef)
            m = rf_modelo(gp.SEMILLA).fit(A, y)
            r2c_rf = r2(Bcan[:, j], m.predict(Acan_j))
            imp = permutation_importance(m, Acan_j, Bcan[:, j], n_repeats=5, random_state=gp.SEMILLA)
            top = [va[cols[i]] for i in np.argsort(-imp.importances_mean)[:3]]
        else:
            top = []
        # estabilidad de los signos de la regresión: remuestreo en bloques
        blq = max(5, int(np.sqrt(len(y))))
        signos = []
        for _ in range(100):
            ini = rng.integers(0, len(y), size=len(y) // blq + 1)
            idx = np.concatenate([np.arange(s, s + blq) % len(y) for s in ini])[:len(y)]
            coef, *_ = np.linalg.lstsq(np.column_stack([np.ones(len(idx)), A[idx]]), y[idx], rcond=None)
            signos.append(np.sign(coef[1:]))
        signos = np.array(signos)
        estables = int(np.sum(np.abs(signos.mean(0)) >= 0.8))
        # control por tamaño: lo mismo con todas las series descontando también la cantidad de activos
        # (los conteos de activos y nuevos se sacan de los predictores: son el tamaño)
        r2t_ols = r2t_rf = np.nan
        if Zt is not None:
            ct = [i for i in cols if va[i] not in escala]
            At, yt = Zt[:, :len(va)][:, ct], Zt[:, len(va) + j]
            r2t_ols, r2t_rf = ols_cv(At, yt), rf_cv(At, yt, gp.SEMILLA)
        filas_mod.append(dict(variable=y_id, r2_cv_regresion=r2_ols, r2_cv_regresion_tamano=r2t_ols, r2_cv_rf_tamano=r2t_rf, nula_p95_regresion=float(np.percentile(nula_ols, 95)),
                              r2_canary_regresion=r2c_ols, coeficientes_signo_estable=f"{estables}/{len(va)}",
                              r2_cv_rf=r2_rf, nula_p95_rf=float(np.percentile(nula_rf, 95)), r2_canary_rf=r2c_rf,
                              rf_top3_canary=", ".join(top),
                              top3_ya_significativos=sum((v, y_id) in sig for v in top)))
        print(f"     {y_id}: R² cv regresión {r2_ols:+.2f} (nula {np.percentile(nula_ols, 95):+.2f}) · RF {r2_rf:+.2f} "
              f"(nula {np.percentile(nula_rf, 95):+.2f}) · canary RF {r2c_rf:+.2f}", flush=True)
    A = A_todo
    escribir(destino / "modelos.csv", filas_mod)
    reg_ok = [f for f in filas_mod if f["r2_cv_regresion"] > max(0.1, f["nula_p95_regresion"]) and f["r2_canary_regresion"] > 0.05
              and f["r2_cv_regresion_tamano"] > 0.1]
    rf_ok = [f for f in filas_mod if f["r2_cv_rf"] > max(0.1, f["nula_p95_rf"]) and f["r2_canary_rf"] > 0.05
             and f["r2_cv_rf"] > f["r2_cv_regresion"] + 0.05 and f["r2_cv_rf_tamano"] > 0.1]
    res["regresion_sin_tamano"] = [f["variable"] for f in filas_mod if f["r2_cv_regresion"] > max(0.1, f["nula_p95_regresion"]) and f["r2_canary_regresion"] > 0.05]
    res["rf_sin_tamano"] = [f["variable"] for f in filas_mod if f["r2_cv_rf"] > max(0.1, f["nula_p95_rf"]) and f["r2_canary_rf"] > 0.05
                            and f["r2_cv_rf"] > f["r2_cv_regresion"] + 0.05]
    res["regresion"] = dict(predecibles=[f["variable"] for f in reg_ok], aporta=bool(reg_ok))
    res["random_forest"] = dict(mejor_que_lineal=[f["variable"] for f in rf_ok], aporta=bool(rf_ok))

    # ── 6. información mutua ──
    print("  6. información mutua…", flush=True)
    filas_mi = []
    nmi = min(NP, 100)
    for i, x_id in enumerate(va):
        for j, y_id in enumerate(vb):
            if base_de[x_id] == base_de[y_id]:
                continue
            x, y = A[:, i], B[:, j]
            mi = float(mutual_info_regression(x.reshape(-1, 1), y, n_neighbors=5, random_state=gp.SEMILLA)[0])
            nula = [mutual_info_regression(x.reshape(-1, 1), np.roll(y, k), n_neighbors=5, random_state=gp.SEMILLA)[0]
                    for k in corrimientos(len(y), nmi, rng)]
            mi_c = np.nan
            if Acan is not None:
                mi_c = float(mutual_info_regression(Acan[:, i].reshape(-1, 1), Bcan[:, j], n_neighbors=5, random_state=gp.SEMILLA)[0])
            # información mutua que implicaría una relación lineal con esa ρ (para separar lo no lineal)
            rho = float(spearmanr(x, y)[0])
            mi_lineal = -0.5 * np.log(1 - min(rho ** 2, 0.999))
            filas_mi.append(dict(x_id=x_id, y_id=y_id, mi=mi, nula_p95=float(np.percentile(nula, 95)), p=p_normal(mi, nula),
                                 rho=rho, mi_esperada_lineal=mi_lineal, exceso=mi - mi_lineal, mi_canary=mi_c,
                                 ya_significativo=(x_id, y_id) in sig))
    for f, q in zip(filas_mi, bh([f["p"] for f in filas_mi])):
        f["q"] = float(q)
    # umbral canary: percentil 95 de la información mutua en canary entre pares sin relación
    base_can = np.nanpercentile([f["mi_canary"] for f in filas_mi], 50) if Acan is not None else np.nan
    for f in filas_mi:
        f["pocos_valores"] = f["x_id"] in pocos or f["y_id"] in pocos
        f["nuevo"] = bool(f["q"] < 0.05 and not f["ya_significativo"] and f["exceso"] > 0.02 and not f["pocos_valores"])
        f["nuevo_con_pocos_valores"] = bool(f["q"] < 0.05 and not f["ya_significativo"] and f["exceso"] > 0.02 and f["pocos_valores"])
        f["replica_canary"] = bool(f["mi_canary"] > 2 * base_can) if Acan is not None else None
    filas_mi.sort(key=lambda f: f["p"])
    escribir(destino / "informacion_mutua.csv", filas_mi)
    nuevos = [f for f in filas_mi if f["nuevo"]]
    nuevos_rep = [f for f in nuevos if f["replica_canary"]]
    res["informacion_mutua"] = dict(pares=len(filas_mi), significativos=sum(f["q"] < 0.05 for f in filas_mi),
                                    tambien_spearman=sum(f["q"] < 0.05 and f["ya_significativo"] for f in filas_mi),
                                    nuevos=len(nuevos), nuevos_que_replican=len(nuevos_rep),
                                    descartados_por_pocos_valores=sum(f["nuevo_con_pocos_valores"] for f in filas_mi),
                                    ejemplos=[f"{nombre[f['x_id']]} ↔ {nombre[f['y_id']]} (MI {f['mi']:.3f}, ρ {f['rho']:+.2f})" for f in nuevos_rep[:5]],
                                    aporta=bool(len(nuevos_rep) >= 1))

    # ── resumen ──
    res["datos"] = dict(dim_a=dim_a, dim_b=dim_b, variables_a=va, variables_b=vb, fuera=fuera_a + fuera_b,
                        releases=len(pnums), releases_canary=len(pn_can), permutaciones=NP)
    (destino / "resumen.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    si = lambda b: "**Sí**" if b else "No"
    f2 = lambda v: f"{v:+.2f}".replace(".", ",") if v == v else "—"
    c0 = res["cca"]["filas"]
    md = [f"# Métodos alternativos · {dim_a}–{dim_b}", "",
          f"{len(va)} variables de {dim_a} y {len(vb)} de {dim_b}, {len(pnums)} releases estables y {len(pn_can)} canary con dato en todas. "
          f"Nula: {NP} corrimientos circulares de un lado respecto del otro.", "",
          "| Método | ¿Aporta? | Resultado |", "|---|---|---|",
          f"| CCA sobre todas las variables | {si(res['cca']['aporta'])} | Todas: r₁ = {f2(c0[0]['r1'])} frente a una nula de {f2(c0[0]['nula_p50'])} (p95 {f2(c0[0]['nula_p95'])}), canary {f2(c0[0]['canary_r1'])}. "
          f"Sin escala ni definiciones superpuestas: r₁ = {f2(c0[1]['r1'])} (nula p95 {f2(c0[1]['nula_p95'])}), canary {f2(c0[1]['canary_r1'])}; la arman {c0[1]['arman_a']} ↔ {c0[1]['arman_b']}"
          + (f". Sobre los componentes: r₁ = {f2(c0[2]['r1'])} (nula p95 {f2(c0[2]['nula_p95'])}), canary {f2(c0[2]['canary_r1'])}" if len(c0) > 2 else "") + " |",
          f"| Reglas de asociación | {si(res['reglas']['aporta'])} | {res['reglas']['fuertes']} reglas con lift ≥ {LIFT_MIN} frente a {res['reglas']['nula_p50']:.0f} con datos desalineados (p95 {res['reglas']['nula_p95']:.0f}); "
          f"{res['reglas']['ya_significativas']} repiten pares que la correlación ya encontró y {res['reglas']['nuevas_que_replican']} nuevas se repiten en canary |",
          f"| Clustering de releases | {si(res['clustering_releases']['aporta'])} | Ajustado: k = {mejor['k']}, silueta {mejor['silueta']:.2f} (nula p95 {mejor['nula_p95']:.2f}), estabilidad {mejor['estabilidad_ari']:.2f}. "
          f"Sin ajustar: k = {mejor_c['k']}, silueta {mejor_c['silueta']:.2f}, V de Cramér con el período {mejor_c['v_cramer_periodo']:.2f} |",
          f"| Clustering de métricas | {si(res['clustering_metricas']['aporta'])} | Con {fm['k']} grupos: ARI con los componentes del PCA {fm['ari_con_pca']:.2f}, estabilidad {fm['estabilidad_ari']:.2f}, "
          f"{fm['grupos_que_mezclan_dimensiones']} grupos mezclan dimensiones |",
          f"| Regresión multivariable | {si(res['regresion']['aporta'])} | Predice fuera de muestra, en canary y con control de tamaño: {', '.join(res['regresion']['predecibles']) or 'ninguna'} (sin exigir el control de tamaño: {', '.join(res['regresion_sin_tamano']) or 'ninguna'}) |",
          f"| Información mutua | {si(res['informacion_mutua']['aporta'])} | {res['informacion_mutua']['significativos']} pares significativos (q < 0,05), {res['informacion_mutua']['tambien_spearman']} ya los encontró Spearman; "
          f"{res['informacion_mutua']['nuevos']} nuevos con más información que la que daría una relación monótona, {res['informacion_mutua']['nuevos_que_replican']} se repiten en canary; "
          f"{res['informacion_mutua']['descartados_por_pocos_valores']} más se descartan porque una de las variables tiene menos de {MIN_DISTINTOS} valores distintos |",
          f"| Random forest | {si(res['random_forest']['aporta'])} | Mejor que la regresión lineal, fuera de muestra, en canary y con control de tamaño: {', '.join(res['random_forest']['mejor_que_lineal']) or 'ninguna'} (sin exigir el control de tamaño: {', '.join(res['rf_sin_tamano']) or 'ninguna'}) |",
          "", "## Modelos por variable", "",
          "| Variable | R² cv regresión (nula p95) | canary | con tamaño | signos estables | R² cv RF (nula p95) | canary | con tamaño | RF top 3 en canary |", "|---|---|---|---|---|---|---|---|---|"]
    md += [f"| {nombre[f['variable']]} | {f2(f['r2_cv_regresion'])} ({f2(f['nula_p95_regresion'])}) | {f2(f['r2_canary_regresion'])} | {f2(f['r2_cv_regresion_tamano'])} | {f['coeficientes_signo_estable']} | "
           f"{f2(f['r2_cv_rf'])} ({f2(f['nula_p95_rf'])}) | {f2(f['r2_canary_rf'])} | {f2(f['r2_cv_rf_tamano'])} | {f['rf_top3_canary']} |" for f in filas_mod]
    if res["reglas"]["ejemplos_nuevas"]:
        md += ["", "## Reglas nuevas que se repiten en canary", ""] + [f"- {e}" for e in res["reglas"]["ejemplos_nuevas"]]
    if res["informacion_mutua"]["ejemplos"]:
        md += ["", "## Pares nuevos por información mutua que se repiten en canary", ""] + [f"- {e}" for e in res["informacion_mutua"]["ejemplos"]]
    md += ["", "## Grupos de métricas", ""] + [f"- k = {f['k']}: {f['grupos']}" for f in filas_m]
    (destino / "resumen.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"  salida: {destino}")
    for k in ("cca", "reglas", "clustering_releases", "clustering_metricas", "regresion", "informacion_mutua", "random_forest"):
        print(f"    {k}: {'APORTA' if res[k]['aporta'] else 'no aporta'}")


if __name__ == "__main__":
    main()
