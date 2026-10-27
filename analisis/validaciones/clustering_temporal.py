"""
Clustering temporal: ¿hubo momentos de la historia de next.js en los que los datos se comportaron igual?

Complementa el clustering de releases de cruce_alternativos.py agregando el eje del tiempo. Usa los
mismos datos y la misma transformación que el PCA (generar_pca.tabla / transformar) y los mismos
criterios que el resto del análisis: nula por corrimientos circulares, réplica en canary y control
por tamaño.

A. Perfiles (¿hubo momentos con el mismo perfil?)
   A1. Épocas: segmentación contigua de la historia con los datos crudos (contexto: dónde cambia el proyecto).
   A2. Clustering de releases por dimensión (k = 2..6) con los datos crudos, ajustados por tendencia y
       duración, y además sin tamaño. Silueta frente a la nula, estabilidad entre mitades y acuerdo con Ward.
   A3. Secuencia en el tiempo de los grupos: asociación con el período, persistencia frente a la nula y
       episodios que reaparecen con más de un año de distancia.
   A4. Semestres parecidos: perfil medio de cada semestre (qué variables están por encima o por debajo de
       lo esperable) y correlación entre semestres separados por al menos un año, frente a la nula, con
       Benjamini–Hochberg y réplica en canary.
   A5. Réplica en canary de los grupos: cada ventana canary se asigna al centroide más cercano y se compara
       con el grupo del release estable que la contiene.
   A6. Tabla cruzada entre dimensiones (plan de análisis, punto 6.2) y clustering conjunto (punto 6.1).
B. Estructura (¿las métricas se relacionaban igual en distintos momentos?)
   B1. Matriz de correlaciones por período (los cuatro del análisis) en estables y en canary; similitud
       entre períodos frente al techo de confiabilidad (mitades dentro del período).
   B2. Pares de variables cuya correlación cambia entre períodos, en estables y en canary a la vez.

Uso (desde la raíz del repo):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/clustering_temporal.py [carpeta_salida]

Por defecto escribe en analisis/salidas/validaciones/clustering_temporal/. Solo lee la base. Tarda unos 15 minutos
(las nulas del clustering). Resultados e interpretación: analisis/informes/clustering.md.
"""
import sys, json, math, warnings, csv
from pathlib import Path
from datetime import datetime
import numpy as np

ROOT = Path.cwd()
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "analisis" / "salidas" / "validaciones" / "clustering_temporal"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "analisis"))
import generar_correlaciones as gc
import generar_pca as gp
from scipy.stats import spearmanr, rankdata
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score
warnings.filterwarnings("ignore")

SEMILLA = gp.SEMILLA
rng = np.random.default_rng(SEMILLA)
KS = range(2, 7)
N_NULA = 100          # nulas del clustering (silueta y persistencia)
N_NULA_SEM = 300      # nula de los semestres
N_NULA_ACUERDO = 500
ENFOQUES = ["crudo", "ajustado", "tamano"]
ETAPAS = [(e[0], e[1], e[2]) for e in gc.ETAPAS]
DIMS = {"Persona": "todas", "Proceso": "producto", "Producto": "producto"}
SOLO_DESDE_2019 = {"cfdr_producto", "nub_producto"}
# métricas que la planilla asigna a Proceso y a Producto: se reparten como en los cruces
# (cruces/proceso_producto_asignado.json) para que los grupos de una dimensión no repitan los de la otra
FUERA_ASIGNADO = {"Proceso": {"cfdr_producto", "nub_producto", "rc_producto", "wp_producto", "nob_42_producto", "anmcc_producto"},
                  "Producto": {"mttr_producto", "noi_producto"}}
SERIES = {"estable": "versiones", "canary": "versiones_canary"}


# ── utilidades ───────────────────────────────────────────────────────────────

def fecha(s):
    return datetime.strptime(str(s)[:8], "%Y%m%d")

def semestre(d):
    return d.year * 2 + (0 if d.month <= 6 else 1)

def nombre_sem(s):
    return f"{s // 2}-{'S1' if s % 2 == 0 else 'S2'}"

def etapa(anio):
    for i, (_, a, b) in enumerate(ETAPAS):
        if a <= anio <= b:
            return i
    return len(ETAPAS) - 1

def cramer(a, b):
    a = np.asarray(a); b = np.asarray(b)
    ua, ia = np.unique(a, return_inverse=True); ub, ib = np.unique(b, return_inverse=True)
    tab = np.zeros((len(ua), len(ub)))
    np.add.at(tab, (ia, ib), 1)
    e = tab.sum(1, keepdims=True) @ tab.sum(0, keepdims=True) / tab.sum()
    chi = np.nansum((tab - e) ** 2 / np.where(e > 0, e, np.nan))
    m = min(tab.shape) - 1
    return float(np.sqrt(chi / (tab.sum() * m))) if m > 0 else 0.0

def p_sup(obs, nula):
    nula = np.asarray(nula, dtype=float)
    return float((1 + np.sum(nula >= obs)) / (1 + len(nula)))

def bh(ps):
    ps = np.asarray(ps, dtype=float); n = len(ps)
    if n == 0:
        return ps
    orden = np.argsort(ps); q = np.empty(n); acum = 1.0
    for i in range(n - 1, -1, -1):
        j = orden[i]; acum = min(acum, ps[j] * n / (i + 1)); q[j] = acum
    return q

def corrida_circular(M):
    """Cada variable corrida en el tiempo por separado: conserva la forma de cada serie, rompe el perfil conjunto."""
    n = len(M)
    return np.column_stack([np.roll(M[:, j], rng.integers(max(5, n // 10), n - max(5, n // 10))) for j in range(M.shape[1])])

def escribir(nombre, filas):
    if not filas:
        return
    claves = list(dict.fromkeys(k for f in filas for k in f))
    with open(OUT / nombre, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=claves); w.writeheader()
        for f in filas:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in f.items()})

def r2(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 3)


# ── datos ────────────────────────────────────────────────────────────────────

var_dict, datos = gp.cargar_datos()
EXTREMOS = []

def variables_de(dim, conj, serie_db, historia, asignado=False):
    de = sorted(v for v, r in var_dict.items() if dim in r["dims_texto"].split("+") and r["metrica_id"] not in gp.VARIANTES
                and (conj == "todas" or r["nivel"] == "producto"))
    if asignado:
        de = [v for v in de if v not in FUERA_ASIGNADO.get(dim, set())]
    if historia:
        de = [v for v in de if v not in SOLO_DESDE_2019]
    vent = set().union(*(set(datos[v][serie_db]) for v in de))
    cob = {v: sum(1 for t in datos[v][serie_db].values() if t[1] is not None) / max(1, len(vent)) for v in de}
    return [v for v in de if cob[v] >= gp.MIN_COBERTURA]

def matriz(variables, serie_db, enfoque):
    vs = [v for v in variables if not (enfoque == "tamano" and (var_dict[v].get("familia") == "tamano" or v == gp.VARIABLE_TAMANO))]
    filas, _ = gp.tabla(vs, datos, serie_db)
    const = [v for j, v in enumerate(vs) if len({f["valores"][j] for f in filas.values()}) < 2]
    if const:
        vs = [v for v in vs if v not in const]
        filas, _ = gp.tabla(vs, datos, serie_db)
    Z, pnums = gp.transformar(filas, enfoque)
    meta = [dict(pnum=p, fecha=fecha(filas[p]["fecha"]), anio=filas[p]["anio"], version=filas[p]["version"]) for p in pnums]
    # releases con un valor extremo (> 6 desvíos, ej. v9.0.0 en Wiki Presence, que vale 0 en casi todo el resto):
    # se informan aparte y no entran al clustering, porque si no forman un grupo de uno
    ext = np.abs(Z).max(axis=1) > 6
    if ext.any():
        EXTREMOS.extend((enfoque, m["version"], vs[int(np.argmax(np.abs(z)))], round(float(np.abs(z).max()), 1))
                        for m, z, e in zip(meta, Z, ext) if e)
        Z = Z[~ext]; meta = [m for m, e in zip(meta, ext) if not e]
    return Z, vs, meta


# ── A2. clustering con nula ──────────────────────────────────────────────────

def persistencia(lab):
    return float(np.mean(lab[1:] == lab[:-1]))

def evaluar_clustering(Z):
    filas, etiquetas = [], {}
    for k in KS:
        km = KMeans(k, n_init=20, random_state=SEMILLA).fit(Z)
        lab = km.labels_
        sil = float(silhouette_score(Z, lab))
        nula_s, nula_p = [], []
        for _ in range(N_NULA):
            Zn = corrida_circular(Z)
            ln = KMeans(k, n_init=4, random_state=SEMILLA).fit_predict(Zn)
            nula_s.append(silhouette_score(Zn, ln)); nula_p.append(persistencia(ln))
        l1 = KMeans(k, n_init=20, random_state=SEMILLA).fit(Z[0::2]).predict(Z)
        l2 = KMeans(k, n_init=20, random_state=SEMILLA).fit(Z[1::2]).predict(Z)
        ward = AgglomerativeClustering(k, linkage="ward").fit_predict(Z)
        pe = persistencia(lab)
        filas.append(dict(k=k, silueta=sil, nula_p95=float(np.percentile(nula_s, 95)), p_silueta=p_sup(sil, nula_s),
                          estabilidad_ari=float(adjusted_rand_score(l1, l2)), acuerdo_ward_ari=float(adjusted_rand_score(lab, ward)),
                          persistencia=pe, persistencia_nula_p95=float(np.percentile(nula_p, 95)), p_persistencia=p_sup(pe, nula_p),
                          tamanos="/".join(str(int((lab == i).sum())) for i in range(k))))
        etiquetas[k] = (lab, km.cluster_centers_)
    # un grupo con menos del 5 % de los releases es un outlier (ej. v9.0.0, el salto de Wiki Presence), no un régimen
    minimo = max(10, int(0.05 * len(Z)))
    for f in filas:
        f["grupo_chico"] = min(int(x) for x in f["tamanos"].split("/")) < minimo
    validos = [f for f in filas if f["p_silueta"] < 0.05 and not f["grupo_chico"]] or [f for f in filas if not f["grupo_chico"]]
    mejor = max(validos or filas, key=lambda f: f["silueta"])
    mejor["aporta"] = bool(mejor["p_silueta"] < 0.05 and mejor["silueta"] >= 0.25 and mejor["estabilidad_ari"] >= 0.7)
    return filas, mejor, etiquetas


# ── A3. secuencia en el tiempo ───────────────────────────────────────────────

def suavizar(lab):
    """Moda móvil de 3 releases: un release suelto no corta un episodio."""
    s = lab.copy()
    for i in range(1, len(lab) - 1):
        a, b, c = lab[i - 1], lab[i], lab[i + 1]
        if a == c and b != a:
            s[i] = a
    return s

def episodios(lab, meta, minimo=3):
    s = suavizar(lab); out = []; i = 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        if j - i + 1 >= minimo:
            out.append(dict(grupo=int(s[i]), desde=meta[i]["fecha"], hasta=meta[j]["fecha"], releases=j - i + 1,
                            desde_v=meta[i]["version"], hasta_v=meta[j]["version"]))
        i = j + 1
    return out

def recurrentes(eps):
    """Grupos con dos episodios separados por más de un año."""
    out = {}
    for g in {e["grupo"] for e in eps}:
        es = sorted((e for e in eps if e["grupo"] == g), key=lambda e: e["desde"])
        pares = [(a, b) for i, a in enumerate(es) for b in es[i + 1:] if (b["desde"] - a["hasta"]).days > 365]
        if pares:
            out[g] = pares
    return out

def describir(Z, vs, lab, g, n=4):
    m = Z[lab == g].mean(axis=0); o = np.argsort(m)
    alto = [f"{vs[j]} {m[j]:+.1f}" for j in o[::-1][:n] if m[j] > 0.3]
    bajo = [f"{vs[j]} {m[j]:+.1f}" for j in o[:n] if m[j] < -0.3]
    return alto, bajo


# ── A4. semestres parecidos ──────────────────────────────────────────────────

def perfiles_semestre(Z, meta, minimo):
    sem = np.array([semestre(m["fecha"]) for m in meta])
    us = [s for s in sorted(set(sem)) if (sem == s).sum() >= minimo]
    P = np.array([Z[sem == s].mean(axis=0) for s in us])
    return us, P, sem

def sim_perfiles(P):
    Pc = P - P.mean(axis=1, keepdims=True)
    n = np.linalg.norm(Pc, axis=1); n[n == 0] = 1
    Pc = Pc / n[:, None]
    return Pc @ Pc.T

def semestres_parecidos(Z, meta, Zc, metac):
    us, P, sem = perfiles_semestre(Z, meta, 5)
    S = sim_perfiles(P)
    nula = []
    for _ in range(N_NULA_SEM):
        Zn = corrida_circular(Z)
        nula.append(sim_perfiles(np.array([Zn[sem == s].mean(axis=0) for s in us])))
    nula = np.array(nula)
    # canary: mismos semestres, su propia transformación
    usc, Pcn, semc = perfiles_semestre(Zc, metac, 20) if Zc is not None else ([], None, None)
    Sc = sim_perfiles(Pcn) if Pcn is not None else None
    ic = {s: i for i, s in enumerate(usc)}
    nula_c = []
    if Sc is not None:
        for _ in range(100):
            Zn = corrida_circular(Zc)
            nula_c.append(sim_perfiles(np.array([Zn[semc == s].mean(axis=0) for s in usc])))
        nula_c = np.array(nula_c)
    pares = []
    for a in range(len(us)):
        for b in range(a + 1, len(us)):
            if us[b] - us[a] < 2:      # al menos un año entre los dos semestres
                continue
            f = dict(sem_a=nombre_sem(us[a]), sem_b=nombre_sem(us[b]), similitud=float(S[a, b]),
                     nula_p95=float(np.percentile(nula[:, a, b], 95)), p=p_sup(S[a, b], nula[:, a, b]))
            if Sc is not None and us[a] in ic and us[b] in ic:
                i, j = ic[us[a]], ic[us[b]]
                f.update(canary=float(Sc[i, j]), p_canary=p_sup(Sc[i, j], nula_c[:, i, j]))
            pares.append(f)
    # evidencia combinada estable + canary (Fisher): más potencia para pares concretos
    from scipy.stats import chi2
    for f in pares:
        f["p_combinado"] = float(chi2.sf(-2 * (math.log(f["p"]) + math.log(f.get("p_canary", 1.0))), 4)) if "p_canary" in f else f["p"]
    qc = bh([f["p_combinado"] for f in pares])
    for f, qq in zip(pares, qc):
        f["q_combinado"] = float(qq)
        f["parecidos_combinado"] = bool(qq < 0.05 and f["similitud"] > 0 and f.get("canary", 0) > 0)
    q = bh([f["p"] for f in pares])
    for f, qq in zip(pares, q):
        f["q"] = float(qq)
        f["parecidos"] = bool(qq < 0.05 and f["similitud"] > 0)
        f["replica_canary"] = bool(f["parecidos"] and f.get("p_canary", 1) < 0.05 and f.get("canary", 0) > 0)
    # acuerdo global entre la matriz estable y la canary (semestres a más de un año)
    acuerdo = None
    if Sc is not None:
        comunes = [s for s in us if s in ic]
        ii = [us.index(s) for s in comunes]; jj = [ic[s] for s in comunes]
        A = S[np.ix_(ii, ii)]; B = Sc[np.ix_(jj, jj)]
        m = np.array([[abs(comunes[x] - comunes[y]) >= 2 and x < y for y in range(len(comunes))] for x in range(len(comunes))])
        obs = spearmanr(A[m], B[m])[0]
        nul = []
        for _ in range(500):
            sh = rng.integers(2, len(comunes) - 2)
            pr = np.roll(np.arange(len(comunes)), sh)
            nul.append(spearmanr(A[m], B[np.ix_(pr, pr)][m])[0])
        # ¿el acuerdo es solo que los semestres cercanos se parecen más? se descuenta la distancia en el tiempo
        gap = np.abs(np.subtract.outer(comunes, comunes))[m].astype(float)
        G = np.column_stack([np.ones_like(gap), gap, gap ** 2])
        res_ = lambda v: v - G @ np.linalg.lstsq(G, v, rcond=None)[0]
        obs2 = spearmanr(res_(A[m]), res_(B[m]))[0]
        nul2 = []
        for _ in range(500):
            pr = np.roll(np.arange(len(comunes)), rng.integers(2, len(comunes) - 2))
            nul2.append(spearmanr(res_(A[m]), res_(B[np.ix_(pr, pr)][m]))[0])
        acuerdo = dict(rho=float(obs), p=p_sup(obs, nul), semestres=len(comunes),
                       rho_sin_distancia=float(obs2), p_sin_distancia=p_sup(obs2, nul2),
                       sim_vs_distancia=float(spearmanr(gap, A[m])[0]))
    return pares, acuerdo, (us, S)


# ── A5. réplica de los grupos en canary ──────────────────────────────────────

def replica_canary(lab, centros, meta, Zc, metac):
    fe = np.array([m["fecha"].timestamp() for m in meta])
    fc = np.array([m["fecha"].timestamp() for m in metac])
    idx = np.searchsorted(fe, fc, side="left")
    ok = idx < len(fe)
    asignado = np.argmin(((Zc[ok][:, None, :] - centros[None]) ** 2).sum(-1), axis=1)
    estable = lab[idx[ok]]
    obs = adjusted_rand_score(estable, asignado)
    nula = [adjusted_rand_score(estable, np.roll(asignado, rng.integers(len(asignado) // 10, len(asignado) - len(asignado) // 10)))
            for _ in range(N_NULA_ACUERDO)]
    return dict(ari=float(obs), nula_p95=float(np.percentile(nula, 95)), p=p_sup(obs, nula), ventanas=int(ok.sum()),
                coincidencia=float(np.mean(estable == asignado)))


# ── A1. épocas (crudo, contiguas) ────────────────────────────────────────────

def epocas(Z, meta, k):
    from scipy.sparse import diags
    n = len(Z)
    con = diags([np.ones(n - 1), np.ones(n - 1)], [-1, 1])
    lab = AgglomerativeClustering(k, linkage="ward", connectivity=con).fit_predict(Z)
    out, i = [], 0
    while i < n:
        j = i
        while j + 1 < n and lab[j + 1] == lab[i]:
            j += 1
        out.append(dict(desde=meta[i]["fecha"].strftime("%Y-%m"), hasta=meta[j]["fecha"].strftime("%Y-%m"),
                        desde_v=meta[i]["version"], hasta_v=meta[j]["version"], releases=j - i + 1))
        i = j + 1
    return out


# ── B. estructura de correlaciones por período ──────────────────────────────

def corr_periodo(Z, meta, filtro=None):
    et = np.array([etapa(m["anio"]) for m in meta])
    out = {}
    for e in range(len(ETAPAS)):
        idx = np.where(et == e)[0]
        if filtro is not None:
            idx = idx[filtro(idx)]
        if len(idx) >= 25:
            C = spearmanr(Z[idx])[0]
            out[e] = (C, len(idx))
    return out

def techo(Z, meta):
    """Similitud esperable si la estructura no cambiara: mitades (pares e impares) del mismo período."""
    et = np.array([etapa(m["anio"]) for m in meta]); res = {}
    for e in range(len(ETAPAS)):
        idx = np.where(et == e)[0]
        if len(idx) >= 50:
            a, b = spearmanr(Z[idx[0::2]])[0], spearmanr(Z[idx[1::2]])[0]
            iu = np.triu_indices_from(a, 1)
            res[e] = float(np.corrcoef(np.arctanh(np.clip(a[iu], -.99, .99)), np.arctanh(np.clip(b[iu], -.99, .99)))[0, 1])
    return res

def estructura(Z, vs, meta, Zc, vsc, metac):
    ce, cc = corr_periodo(Z, meta), corr_periodo(Zc, metac) if Zc is not None else {}
    iu = np.triu_indices(len(vs), 1)
    fz = lambda C: np.arctanh(np.clip(C[iu], -.99, .99))
    sims = []
    for serie, cs in (("estable", ce), ("canary", cc)):
        es = sorted(cs)
        for i, a in enumerate(es):
            for b in es[i + 1:]:
                sims.append(dict(serie=serie, periodo_a=ETAPAS[a][0], periodo_b=ETAPAS[b][0],
                                 similitud=float(np.corrcoef(fz(cs[a][0]), fz(cs[b][0]))[0, 1])))
    tec = dict(estable=techo(Z, meta), canary=techo(Zc, metac) if Zc is not None else {})
    # pares que cambian entre el primer y el último período con dato, en las dos series
    cambios = []
    comunes = sorted(set(ce) & set(cc))
    if len(comunes) >= 2 and vs == vsc:
        a, b = comunes[0], comunes[-1]
        for i, j in zip(*iu):
            ra, rb = ce[a][0][i, j], ce[b][0][i, j]; ca, cb = cc[a][0][i, j], cc[b][0][i, j]
            # diferencia de correlaciones independientes (z de Fisher)
            se_e = math.sqrt(1 / (ce[a][1] - 3) + 1 / (ce[b][1] - 3))
            z_e = (np.arctanh(np.clip(rb, -.99, .99)) - np.arctanh(np.clip(ra, -.99, .99))) / se_e
            p_e = float(2 * (1 - __import__("scipy.stats", fromlist=["norm"]).norm.cdf(abs(z_e))))
            cambios.append(dict(par=f"{vs[i]} ↔ {vs[j]}", desde=ETAPAS[a][0], hasta=ETAPAS[b][0],
                                rho_desde=float(ra), rho_hasta=float(rb), delta=float(rb - ra), p=p_e,
                                canary_desde=float(ca), canary_hasta=float(cb), delta_canary=float(cb - ca)))
        q = bh([c["p"] for c in cambios])
        for c, qq in zip(cambios, q):
            c["q"] = float(qq)
            c["cambia"] = bool(qq < 0.05 and abs(c["delta"]) >= 0.3 and abs(c["delta_canary"]) >= 0.15
                               and np.sign(c["delta"]) == np.sign(c["delta_canary"]))
    return sims, tec, cambios


# ── ejecución ───────────────────────────────────────────────────────────────

def conjuntos():
    for dim, conj in DIMS.items():
        yield dim, "principal", conj, False, False
        if dim != "Persona":
            yield dim, "historia", conj, True, False
            yield dim, "asignado", conj, False, True
            yield dim, "asignado_historia", conj, True, True

res = dict(conjuntos={}, cruce={}, conjunto3d={})
filas_k, filas_ep, filas_sem, filas_rep, filas_estr, filas_camb, filas_epocas, filas_lab = [], [], [], [], [], [], [], []
etiquetas_ajustado = {}

for dim, version, conj, historia, asignado in conjuntos():
    nombre = f"{dim}/{version}"
    vs0 = variables_de(dim, conj, "versiones", historia, asignado)
    vsc0 = variables_de(dim, conj, "versiones_canary", historia, asignado)
    print(f"=== {nombre}: {len(vs0)} variables", flush=True)
    R = res["conjuntos"][nombre] = {}
    for enf in ENFOQUES:
        Z, vs, meta = matriz(vs0, "versiones", enf)
        try:
            Zc, vsc, metac = matriz(vsc0, "versiones_canary", enf)
            if vsc != vs:
                comunes = [v for v in vs if v in vsc]
                Z = Z[:, [vs.index(v) for v in comunes]]; Zc = Zc[:, [vsc.index(v) for v in comunes]]
                vs = vsc = comunes
        except Exception as ex:
            Zc, vsc, metac = None, [], []
        filas, mejor, etq = evaluar_clustering(Z)
        for f in filas:
            filas_k.append(dict(conjunto=nombre, enfoque=enf, n=len(Z), variables=len(vs), **f))
        k = mejor["k"]; lab, centros = etq[k]
        et = [etapa(m["anio"]) for m in meta]
        eps = episodios(lab, meta)
        rec = recurrentes(eps)
        grupos = []
        for g in range(k):
            alto, bajo = describir(Z, vs, lab, g)
            grupos.append(dict(grupo=g, releases=int((lab == g).sum()), alto=alto, bajo=bajo,
                               por_periodo=[int(((lab == g) & (np.array(et) == e)).sum()) for e in range(len(ETAPAS))],
                               recurrente=g in rec))
        for e in eps:
            filas_ep.append(dict(conjunto=nombre, enfoque=enf, k=k, grupo=e["grupo"], desde=e["desde"].strftime("%Y-%m-%d"),
                                 hasta=e["hasta"].strftime("%Y-%m-%d"), desde_v=e["desde_v"], hasta_v=e["hasta_v"], releases=e["releases"]))
        for m, l in zip(meta, lab):
            filas_lab.append(dict(conjunto=nombre, enfoque=enf, k=k, pnum=m["pnum"], version=m["version"], fecha=m["fecha"].strftime("%Y-%m-%d"), grupo=int(l)))
        rep = replica_canary(lab, centros, meta, Zc, metac) if Zc is not None and enf != "crudo" else None
        if rep:
            filas_rep.append(dict(conjunto=nombre, enfoque=enf, k=k, **rep))
        R[enf] = dict(n=len(Z), variables=vs, mejor=mejor, v_cramer_periodo=cramer(lab, et), grupos=grupos,
                      episodios_recurrentes={int(g): [(a["desde"].strftime("%Y-%m"), a["hasta"].strftime("%Y-%m"),
                                                       b["desde"].strftime("%Y-%m"), b["hasta"].strftime("%Y-%m")) for a, b in p]
                                             for g, p in rec.items()},
                      replica_canary=rep)
        print(f"  {enf:8s} n={len(Z)} k={k} silueta {mejor['silueta']:.2f} (nula p95 {mejor['nula_p95']:.2f}, p {mejor['p_silueta']:.3f}) "
              f"estab {mejor['estabilidad_ari']:.2f} ward {mejor['acuerdo_ward_ari']:.2f} persist {mejor['persistencia']:.2f} "
              f"(nula p95 {mejor['persistencia_nula_p95']:.2f}) V período {cramer(lab, et):.2f} recurrentes {len(rec)} "
              f"canary {('ARI %.2f p %.3f' % (rep['ari'], rep['p'])) if rep else '—'}", flush=True)
        if enf == "crudo":
            for kk in (3, 4, 5):
                for e in epocas(Z, meta, kk):
                    filas_epocas.append(dict(conjunto=nombre, k=kk, **e))
        if enf in ("ajustado", "tamano"):
            pares, acuerdo, _ = semestres_parecidos(Z, meta, Zc, metac)
            for f in pares:
                filas_sem.append(dict(conjunto=nombre, enfoque=enf, **f))
            par = [f for f in pares if f["parecidos"]]
            comb = [f for f in pares if f["parecidos_combinado"]]
            R[enf]["semestres"] = dict(evaluados=len(pares), parecidos=len(par), replican=sum(f["replica_canary"] for f in par),
                                       parecidos_combinado=[(f["sem_a"], f["sem_b"], round(f["similitud"], 2), r2(f.get("canary"))) for f in comb],
                                       esperados_por_azar=round(0.05 * len(pares), 1), acuerdo_canary=acuerdo,
                                       lista=[(f["sem_a"], f["sem_b"], round(f["similitud"], 2), r2(f.get("canary"))) for f in par])
            print(f"           combinando estable y canary: {len(comb)} pares parecidos: {R[enf]['semestres']['parecidos_combinado']}", flush=True)
            print(f"           semestres a más de un año: {len(pares)} pares, parecidos {len(par)} (replican en canary "
                  f"{R[enf]['semestres']['replican']}); acuerdo estable–canary {acuerdo}", flush=True)
        if enf == "ajustado":
            etiquetas_ajustado[nombre] = (lab, meta, Z, vs, k)
            sims, tec, cambios = estructura(Z, vs, meta, Zc, vsc, metac)
            for s in sims:
                filas_estr.append(dict(conjunto=nombre, **s))
            for c in cambios:
                filas_camb.append(dict(conjunto=nombre, **c))
            R["estructura"] = dict(similitudes=sims, techo=tec, pares=len(cambios), cambian=[c["par"] for c in cambios if c["cambia"]])
            print(f"           estructura: techo {tec}; pares que cambian (estable y canary): {sum(c['cambia'] for c in cambios)} de {len(cambios)}", flush=True)

# ── A6. tabla cruzada entre dimensiones y clustering conjunto ───────────────
print("=== cruce entre dimensiones", flush=True)
filas_cruce = []
for a, b in (("Persona/principal", "Proceso/asignado"), ("Persona/principal", "Producto/asignado"), ("Proceso/asignado", "Producto/asignado"),
             ("Persona/principal", "Proceso/asignado_historia"), ("Persona/principal", "Producto/asignado_historia"),
             ("Proceso/asignado_historia", "Producto/asignado_historia"),
             ("Proceso/principal", "Producto/principal")):      # el último, con las compartidas en los dos lados: referencia de lo mecánico
    la, ma, *_ = etiquetas_ajustado[a]; lb, mb, *_ = etiquetas_ajustado[b]
    pa = {m["pnum"]: l for m, l in zip(ma, la)}; pb = {m["pnum"]: l for m, l in zip(mb, lb)}
    com = sorted(set(pa) & set(pb))
    x = np.array([pa[p] for p in com]); y = np.array([pb[p] for p in com])
    obs = cramer(x, y)
    nula = [cramer(x, np.roll(y, rng.integers(len(y) // 10, len(y) - len(y) // 10))) for _ in range(1000)]
    tab = np.zeros((x.max() + 1, y.max() + 1), dtype=int); np.add.at(tab, (x, y), 1)
    filas_cruce.append(dict(a=a, b=b, releases=len(com), v_cramer=obs, nula_p95=float(np.percentile(nula, 95)), p=p_sup(obs, nula),
                            tabla=json.dumps(tab.tolist())))
    print(f"  {a} × {b}: V {obs:.2f} (nula p95 {np.percentile(nula, 95):.2f}, p {p_sup(obs, nula):.3f}) n={len(com)}", flush=True)
res["cruce"] = filas_cruce

for version in ("asignado", "asignado_historia"):
    noms = ["Persona/principal", f"Proceso/{version}", f"Producto/{version}"]
    metas = [{m["pnum"]: i for i, m in enumerate(etiquetas_ajustado[n][1])} for n in noms]
    com = sorted(set.intersection(*(set(m) for m in metas)))
    bloques, crudos, nombres_v = [], [], []
    for n, mp in zip(noms, metas):
        Zb = etiquetas_ajustado[n][2][[mp[p] for p in com]]
        vsb = etiquetas_ajustado[n][3]
        usar = [j for j, v in enumerate(vsb) if v not in nombres_v]       # una variable compartida entra una sola vez
        bloques.append(Zb[:, usar] / math.sqrt(len(usar))); crudos.append(Zb[:, usar]); nombres_v += [vsb[j] for j in usar]
    Zt = np.column_stack(bloques); Zsin = np.column_stack(crudos)   # cada dimensión pesa lo mismo; Zsin solo para describir
    filas, mejor, etq = evaluar_clustering(Zt)
    for f in filas:
        filas_k.append(dict(conjunto=f"Conjunto/{version}", enfoque="ajustado", n=len(Zt), variables=Zt.shape[1], **f))
    meta = etiquetas_ajustado[noms[0]][1]; mp0 = metas[0]
    meta_c = [meta[mp0[p]] for p in com]
    lab = etq[mejor["k"]][0]
    res["conjunto3d"][version] = dict(n=len(Zt), mejor=mejor, v_cramer_periodo=cramer(lab, [etapa(m["anio"]) for m in meta_c]),
                                      grupos=[dict(grupo=g, releases=int((lab == g).sum()),
                                                   **dict(zip(("alto", "bajo"), describir(Zsin, nombres_v, lab, g))))
                                              for g in range(mejor["k"])])
    print(f"  conjunto {version}: n={len(Zt)} k={mejor['k']} silueta {mejor['silueta']:.2f} (nula p95 {mejor['nula_p95']:.2f}, p {mejor['p_silueta']:.3f}) "
          f"estab {mejor['estabilidad_ari']:.2f} persist {mejor['persistencia']:.2f} (nula {mejor['persistencia_nula_p95']:.2f})", flush=True)

print("releases extremos fuera del clustering:", sorted(set(EXTREMOS)), flush=True)
res["extremos"] = sorted(set(EXTREMOS))
escribir("clustering_k.csv", filas_k); escribir("episodios.csv", filas_ep); escribir("semestres.csv", filas_sem)
escribir("replica_canary.csv", filas_rep); escribir("estructura_periodos.csv", filas_estr); escribir("estructura_cambios.csv", filas_camb)
escribir("epocas.csv", filas_epocas); escribir("cruce_dimensiones.csv", filas_cruce); escribir("etiquetas.csv", filas_lab)
with open(OUT / "resultados.json", "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1, default=str)
print("salida:", OUT)
