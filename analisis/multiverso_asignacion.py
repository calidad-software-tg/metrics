#!/usr/bin/env python3
"""
analisis/multiverso_asignacion.py

Sensibilidad a la asignación de las métricas compartidas (análisis de multiverso). Dieciséis métricas pertenecen
a dos dimensiones según el catálogo y, en los cruces y en el análisis de tres dimensiones, cada una tiene que ir
a un solo lado. Este script recorre muchas asignaciones posibles (cada métrica, con todos sus resúmenes, va a
una de sus dos dimensiones) y registra qué patrones aparecen en cada una, con la asignación principal o sin ella.

  1. Cruce de variables (sin volver a calcular: la correlación de un par no depende del lado). Se toman todos
     los pares que son patrón en algún nivel (hallazgos candidatos dentro de cada dimensión y patrones de los
     cruces) y, para cada uno, la proporción de las asignaciones posibles en la que relaciona dos dimensiones
     distintas. Así aparecen también los patrones que la asignación principal deja dentro de una dimensión.
  2. Cruces de a pares que dependen de la asignación (se vuelven a calcular en cada asignación): PCA y
     clustering de cada dimensión con sus variables, y en cada cruce el cruce de componentes, el conjunto
     reducido, la correlación canónica, el cruce de grupos, el PCA y el clustering conjunto y la triangulación.
     Los componentes y grupos se reconocen entre asignaciones por su tema (las variables que los definen).
  3. Tres dimensiones (se vuelve a calcular en cada asignación): correlación canónica generalizada, RV medio y
     factores del MFA sobre los componentes sin tamaño, y qué temas juntan las tres dimensiones.

Universos: la asignación principal, cada métrica cambiada de lado sola, la opuesta y N_MUESTRA al azar.

Qué variables entran en cada dimensión: Persona, todas las suyas; Proceso y Producto, las del proyecto y los
resúmenes por colaborador de las métricas que comparten con Persona cuando se asignan ahí (en la asignación
principal coincide con los conjuntos del análisis principal).

Versión liviana, por costo: el análisis paralelo con N_HORN permutaciones, nulas de N_NULA corrimientos, sin
bootstrap ni canary. Un par es patrón si su p corregido (Benjamini–Hochberg dentro del cruce) es menor que 0,05,
tiene el mismo signo en todos los períodos evaluables (al menos tres), resiste el control por tamaño y no es de
escala ni mecánico. Los resultados indican cuánto depende cada patrón de la asignación; la evaluación completa
de un patrón es la del análisis principal.

Uso:
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/multiverso_asignacion.py [--solo-variables]

--solo-variables corre solo el cruce de variables y la lista de hallazgos entre dimensiones (segundos).
Criterio de hallazgo entre dimensiones: un patrón de variables cuyas dos variables no comparten ninguna dimensión
del catálogo, o sea, que relaciona dimensiones distintas con cualquier asignación (hallazgos_entre_dimensiones.md).

Salidas en analisis/salidas/multiverso_asignacion/: resumen.md, hallazgos_entre_dimensiones.md y .csv,
patrones_variables.csv, patrones_cruces.csv, universos.csv.
"""
import csv
import sys
import warnings
from collections import Counter, defaultdict
from itertools import combinations, product
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

sys.path.insert(0, str(Path(__file__).resolve().parent))
import correlaciones as corr  # noqa: E402
import pca  # noqa: E402
import tres_dimensiones as td  # noqa: E402

SALIDA = corr.ROOT / "analisis" / "salidas" / "multiverso_asignacion"
DIMS = ("Persona", "Proceso", "Producto")
CRUCES = [("Persona", "Proceso"), ("Persona", "Producto"), ("Proceso", "Producto")]
N_MUESTRA = 500
N_NULA = 200
N_HORN = 100
CARGA = 0.4
CARGA_FACTOR = 0.5     # correlación mínima de una variable con un factor del MFA para contar su tema
# asignación principal (la de los cruces y de tres_dimensiones.py)
PRINCIPAL = {"exprev": "Persona", "rexprev": "Persona", "cdiv": "Persona", "nc": "Persona", "sc": "Persona",
             "dev_exp": "Persona", "le": "Persona", "cd": "Persona", "mttr": "Proceso", "noi": "Proceso",
             "cfdr": "Producto", "nub": "Producto", "rc": "Producto", "wp": "Producto", "nob_42": "Producto",
             "anmcc": "Producto"}
# temas para reconocer componentes, grupos y factores entre asignaciones (prefijo de la variable → tema)
TEMAS = [("Learning Ease", ("le_",)),
         ("concentración del núcleo", ("exprev_share", "nc_share", "sc_share", "sc_p90", "cdiv_p90", "cdiv_share")),
         ("cierre de lo viejo", ("mttr_", "nci_")),
         ("bugs de usuarios", ("cfdr", "nub")),
         ("resolución de lo nuevo", ("jarczyk", "process_performance")),
         ("renovación y experiencia", ("tasa_nuevos", "nuevos_commits", "le_mediana", "dev_exp", "cdiv_mediana", "rexp_", "prop_commitean")),
         ("volumen de actividad", ("activos_", "nuevos_interaccion", "tasa_nuevos_interaccion")),
         ("documentación", ("dloc", "commits_doc", "le_producto", "cd_")),
         ("README e issues abiertas", ("rc_", "noi")),
         ("Wiki y branches", ("wp_", "nob_")),
         ("revisores más activos", ("exprev_p90", "nc_p90", "rexprev")),
         ("tamaño de los cambios", ("anmcc",)),
         ("participación", ("prop_comentan", "prop_cierran", "disc_centrality", "ss_", "sc_mediana")),
         ("issues de documentación", ("dis_",))]
CANDIDATO = {"concentración del núcleo", "cierre de lo viejo", "bugs de usuarios"}


def tema(v):
    for t, claves in TEMAS:
        if any(v.startswith(c) for c in claves):
            return t
    return "otro"


def dims_de(r):
    return [d for d, f in zip(DIMS, (r["dim_persona"], r["dim_proceso"], r["dim_producto"])) if f == "1"]


def es_compartida(v, var_dict):
    r = var_dict[v]
    return len(dims_de(r)) == 2 and not (r["nivel"] == "producto" and corr.metrica_base(r["metrica_id"]) in ("le", "cd"))


def lado(v, var_dict, asig):
    r = var_dict[v]
    if not es_compartida(v, var_dict):
        ds = dims_de(r)
        return "Producto" if r["nivel"] == "producto" and corr.metrica_base(r["metrica_id"]) in ("le", "cd") else ds[0]
    return asig[corr.metrica_base(r["metrica_id"])]


def entra(v, d, var_dict):
    """Persona usa todas sus variables; Proceso y Producto, las del proyecto y los resúmenes por colaborador de las
    métricas que comparten con Persona."""
    r = var_dict[v]
    return d == "Persona" or r["nivel"] == "producto" or "Persona" in dims_de(r)


# ── 1. cruce de variables ────────────────────────────────────────────────────

def lecturas(x, y, var_dict):
    """Proporción de asignaciones (cada métrica compartida a cada dimensión con igual chance) por lectura."""
    def opciones(v):
        return dims_de(var_dict[v]) if es_compartida(v, var_dict) else [lado(v, var_dict, PRINCIPAL)]
    mx, my = corr.metrica_base(var_dict[x]["metrica_id"]), corr.metrica_base(var_dict[y]["metrica_id"])
    cuenta = Counter()
    if mx == my and es_compartida(x, var_dict):          # misma métrica: va junta
        for a in opciones(x):
            cuenta["dentro de " + a] += 1 / len(opciones(x))
    else:
        ox, oy = opciones(x), opciones(y)
        for a, b in product(ox, oy):
            cuenta["dentro de " + a if a == b else "–".join(sorted((a, b), key=DIMS.index))] += 1 / (len(ox) * len(oy))
    return cuenta


def patrones_variables(var_dict):
    pares = {}
    for r in csv.DictReader(open(corr.SALIDA / "pares_correlacion.csv", encoding="utf-8")):
        if r.get("hallazgo_candidato") == "True":
            pares.setdefault(frozenset((r["x_id"], r["y_id"])), dict(x=r["x_id"], y=r["y_id"], rho=float(r["rho_corregida"]), origen=r["cruce"]))
    for a, b in CRUCES:
        ruta = corr.SALIDA / "cruces" / f"{a.lower()}_{b.lower()}" / "pares_variables.csv"
        if ruta.exists():
            for r in csv.DictReader(open(ruta, encoding="utf-8")):
                if r["tipo"] == "patrón":
                    pares.setdefault(frozenset((r["x_id"], r["y_id"])), dict(x=r["x_id"], y=r["y_id"], rho=float(r["rho_corregida"]), origen=f"{a}–{b}"))
    filas = []
    for p in pares.values():
        x, y = p["x"], p["y"]
        if x not in var_dict or y not in var_dict:
            continue
        mx, my = var_dict[x]["metrica_id"], var_dict[y]["metrica_id"]
        if mx in pca.VARIANTES or my in pca.VARIANTES or corr.es_solapamiento_definicion(x, y, (mx, my)) \
                or corr.es_por_construccion(x, y, corr.metrica_base(mx) == corr.metrica_base(my)):
            continue
        c = lecturas(x, y, var_dict)
        lx, ly = lado(x, var_dict, PRINCIPAL), lado(y, var_dict, PRINCIPAL)
        principal = "dentro de " + lx if lx == ly else "–".join(sorted((lx, ly), key=DIMS.index))
        entre = sum(v for k, v in c.items() if not k.startswith("dentro"))
        filas.append(dict(x=x, y=y, rho=p["rho"], dims_x="+".join(dims_de(var_dict[x])), dims_y="+".join(dims_de(var_dict[y])),
                          principal=principal, entre_dimensiones=entre, mismo_tema=tema(x) == tema(y),
                          tipo=("entre dimensiones con cualquier asignación" if entre == 1 else
                                "nuevo: solo con otras asignaciones" if not principal.startswith("dentro") is False and entre > 0 else
                                "depende de la asignación" if entre > 0 else "siempre dentro de una dimensión"),
                          lecturas="; ".join(f"{k} {v:.0%}" for k, v in sorted(c.items(), key=lambda t: -t[1]))))
    for f in filas:
        if f["principal"].startswith("dentro") and f["entre_dimensiones"] > 0:
            f["tipo"] = "nuevo: solo con otras asignaciones"
        elif not f["principal"].startswith("dentro") and f["entre_dimensiones"] < 1:
            f["tipo"] = "depende de la asignación"
    return filas


# ── utilidades de cada universo ─────────────────────────────────────────────

def bloque(vs, datos, rng, enfoque):
    filas, _ = pca.tabla(vs, datos, "versiones")
    const = [v for j, v in enumerate(vs) if len({f["valores"][j] for f in filas.values()}) < 2]
    if const:
        vs = [v for v in vs if v not in const]
        filas, _ = pca.tabla(vs, datos, "versiones")
    if len(vs) < 2:
        return None
    Z, pn = pca.transformar(filas, enfoque)
    if Z.shape[0] < 30:
        return None
    val, _ = pca.autodescomponer(Z)
    h95, _ = pca.horn(Z, rng, n_perm=N_HORN)
    k = max(1, pca.contar_hasta(val > h95))
    sol = pca.solucion(Z, k)
    pn = list(pn)
    return dict(vs=vs, Z=Z, pn=pn, F=sol["Fr"], L=sol["Lr"], k=k,
                du={p: filas[p]["dur"] for p in pn}, anio={p: filas[p]["anio"] for p in pn})


def tema_de(vars_cargas):
    """Tema dominante de un componente o grupo: el que suma más carga al cuadrado."""
    s = Counter()
    for v, x in vars_cargas:
        s[tema(v)] += x * x
    return s.most_common(1)[0][0] if s else "otro"


def elementos_pca(B, d, var_dict):
    """Componentes de un bloque, con su tema, si son de escala y sus variables fuertes."""
    out = []
    for j in range(B["F"].shape[1]):
        fuertes = [(B["vs"][i], float(B["L"][i, j])) for i in range(len(B["vs"])) if abs(B["L"][i, j]) >= CARGA]
        escala = bool(fuertes) and sum(var_dict[v].get("familia") == "tamano" for v, _ in fuertes) / len(fuertes) >= 0.5
        out.append(dict(id=f"{d}:cp{j + 1}", clave=f"{d}:{tema_de(fuertes)}", serie=B["F"][:, j],
                        vars=[v for v, _ in fuertes], escala=escala))
    return out


def elementos_grupos(B, d, var_dict):
    """Grupos del clustering de un bloque (1 − |r|, enlace promedio, tantos grupos como componentes), con la serie
    promedio de sus rangos orientados según la variable central."""
    Z = B["Z"]
    p = Z.shape[1]
    if p < 3:
        return []
    R = np.nan_to_num(np.corrcoef(Z, rowvar=False))
    D = 1 - np.abs(R)
    np.fill_diagonal(D, 0)
    lab = fcluster(linkage(squareform(D, checks=False), "average"), max(2, min(B["k"], p - 1)), "maxclust")
    out = []
    for g in sorted(set(lab)):
        idx = [i for i in range(p) if lab[i] == g]
        if len(idx) < 2:
            continue
        c = idx[int(np.argmax([np.mean(np.abs(R[i, idx])) for i in idx]))]
        serie = np.mean([Z[:, i] * (1 if R[i, c] >= 0 else -1) for i in idx], axis=0)
        vs = [B["vs"][i] for i in idx]
        escala = sum(var_dict[v].get("familia") == "tamano" for v in vs) / len(vs) >= 0.5
        out.append(dict(id=f"{d}:g{g}", clave=f"{d}:{tema_de([(v, 1.0) for v in vs])}", serie=serie, vars=vs, escala=escala))
    return out


def evaluar(x, y, pn, du, anio, size):
    g = corr.partial_spearman(list(x), list(y), pn, du)
    rhos = []
    for _, y0, y1 in corr.CALENDARIO:
        ii = [i for i, a in enumerate(anio) if a is not None and y0 <= a <= y1]
        if len(ii) >= corr.MIN_VENTANAS_PERIODO:
            rhos.append(corr.partial_spearman([x[i] for i in ii], [y[i] for i in ii], [pn[i] for i in ii], [du[i] for i in ii])["rho_corr"])
    rhos = [r for r in rhos if isinstance(r, float) and not np.isnan(r)]
    ok = [i for i, s in enumerate(size) if s is not None]
    t = corr.partial_spearman([x[i] for i in ok], [y[i] for i in ok], [pn[i] for i in ok], [du[i] for i in ok],
                              extra_controls=[[corr.safe_log(size[i] + 1) for i in ok]])["rho_corr"]
    rho = g["rho_corr"]
    estable = len(rhos) >= 3 and isinstance(rho, float) and all((r >= 0) == (rho >= 0) for r in rhos)
    return dict(rho=rho, p=g["p_corr"], estable=estable, rho_tam=t)


def cruzar(els_a, els_b, filas_a, filas_b, B, size_e, var_dict):
    """Pares de elementos de dos lados, con BH dentro del cruce. Devuelve las claves de los pares patrón."""
    comunes = sorted(set(B[0]["pn"]) & set(B[1]["pn"]))
    ia = {p: i for i, p in enumerate(B[0]["pn"])}
    ib = {p: i for i, p in enumerate(B[1]["pn"])}
    du = [B[0]["du"][p] for p in comunes]
    anio = [B[0]["anio"][p] for p in comunes]
    size = [size_e.get(p, (None, None))[1] for p in comunes]
    pn = [float(p) for p in comunes]
    pares = {}
    for ea, eb in product(els_a, els_b):
        if set(ea["vars"]) & set(eb["vars"]):
            continue
        r = evaluar(ea["serie"][[ia[p] for p in comunes]], eb["serie"][[ib[p] for p in comunes]], pn, du, anio, size)
        mec = any(corr.es_solapamiento_definicion(u, w, (var_dict[u]["metrica_id"], var_dict[w]["metrica_id"]))
                  for u in ea["vars"] for w in eb["vars"])
        mismo = ea["clave"].split(":", 1)[1] == eb["clave"].split(":", 1)[1]
        pares[(ea["id"], eb["id"])] = dict(r, clave=f"{ea['clave']} ↔ {eb['clave']}" + (" (mismo tema)" if mismo else ""),
                                           escala=ea["escala"] or eb["escala"], mecanico=mec)
    q = corr.benjamini_hochberg([(k, v["p"]) for k, v in pares.items()])
    out = {}
    for k, v in pares.items():
        sig = q.get(k) not in ("", None) and q[k] < 0.05
        v["patron"] = bool(sig and v["estable"] and corr.resiste_tamano(v["rho"], v["rho_tam"]) is not False
                           and not v["escala"] and not v["mecanico"])
        out[k] = v
    return out


def cca_par(Fa, Fb, rng):
    def can(X, Y):
        Qx, _ = np.linalg.qr(X - X.mean(0))
        Qy, _ = np.linalg.qr(Y - Y.mean(0))
        return np.linalg.svd(Qx.T @ Qy, compute_uv=False)[0]
    obs = can(Fa, Fb)
    n = len(Fa)
    m = max(10, n // 10)
    nul = [can(Fa, np.roll(Fb, rng.integers(m, n - m), axis=0)) for _ in range(N_NULA)]
    return obs, (1 + sum(x >= obs for x in nul)) / (N_NULA + 1)


def conjunto(B, comunes, d_de, rng, var_dict):
    """PCA y clustering de las variables que definen componentes de los dos lados, juntas: temas de los
    componentes y grupos que mezclan las dos dimensiones (sin los de escala)."""
    cols, dims = [], []
    for k, b in enumerate(B):
        fuertes = [i for i in range(len(b["vs"])) if np.abs(b["L"][i]).max() >= CARGA]
        idx = [b["pn"].index(p) for p in comunes]
        for i in fuertes:
            cols.append((b["vs"][i], b["Z"][idx, i]))
            dims.append(d_de[k])
    if len(cols) < 4:
        return set(), set()
    Z = np.column_stack([c[1] for c in cols])
    vs = [c[0] for c in cols]
    val, _ = pca.autodescomponer(Z)
    h95, _ = pca.horn(Z, rng, n_perm=N_HORN)
    k = max(1, pca.contar_hasta(val > h95))
    L = pca.solucion(Z, k)["Lr"]
    comps = set()
    for j in range(k):
        fuertes = [(vs[i], float(L[i, j]), dims[i]) for i in range(len(vs)) if abs(L[i, j]) >= CARGA]
        if len({d for *_, d in fuertes}) > 1 and sum(var_dict[v].get("familia") == "tamano" for v, *_ in fuertes) / len(fuertes) < 0.5:
            comps.add(" + ".join(sorted({f"{d}:{tema(v)}" for v, _, d in fuertes})))
    R = np.nan_to_num(np.corrcoef(Z, rowvar=False))
    D = 1 - np.abs(R)
    np.fill_diagonal(D, 0)
    lab = fcluster(linkage(squareform(D, checks=False), "average"), max(2, k), "maxclust")
    grupos = set()
    for g in set(lab):
        idx = [i for i in range(len(vs)) if lab[i] == g]
        if len({dims[i] for i in idx}) > 1 and sum(var_dict[vs[i]].get("familia") == "tamano" for i in idx) / len(idx) < 0.5:
            grupos.add(" + ".join(sorted({f"{dims[i]}:{tema(vs[i])}" for i in idx})))
    return comps, grupos


def universo(asig, vs_ajustado, vs_tamano, var_dict, datos, rng, pares_var, size_e):
    res = {"patrones": set()}
    # ── bloques ──
    Bj, Bt = {}, {}
    for d in DIMS:
        Bj[d] = bloque([v for v in vs_ajustado if lado(v, var_dict, asig) == d and entra(v, d, var_dict)], datos, rng, "ajustado")
        Bt[d] = bloque([v for v in vs_tamano if lado(v, var_dict, asig) == d and entra(v, d, var_dict)], datos, rng, "tamano")
    if any(b is None for b in list(Bj.values()) + list(Bt.values())):
        return None
    res["k"] = "/".join(str(Bj[d]["k"]) for d in DIMS)
    comps = {d: elementos_pca(Bj[d], d, var_dict) for d in DIMS}
    grupos = {d: elementos_grupos(Bj[d], d, var_dict) for d in DIMS}
    # ── cruces de a pares ──
    for a, b in CRUCES:
        cruce = f"{a}–{b}"
        B = (Bj[a], Bj[b])
        pc = cruzar(comps[a], comps[b], None, None, B, size_e, var_dict)
        for v in pc.values():
            if v["patron"]:
                res["patrones"].add(f"componentes | {v['clave']}")
        # conjunto reducido: componentes + variables que no definen ningún componente
        indep = {}
        for d in (a, b):
            Bd = Bj[d]
            indep[d] = [dict(id=f"{d}:{Bd['vs'][i]}", clave=f"{d}:{Bd['vs'][i]}", serie=Bd["Z"][:, i], vars=[Bd["vs"][i]],
                             escala=var_dict[Bd["vs"][i]].get("familia") == "tamano")
                        for i in range(len(Bd["vs"])) if np.abs(Bd["L"][i]).max() < CARGA]
        pr = cruzar(comps[a] + indep[a], comps[b] + indep[b], None, None, B, size_e, var_dict)
        for v in pr.values():
            if v["patron"]:
                res["patrones"].add(f"conjunto reducido | {v['clave']}")
        pg = cruzar(grupos[a], grupos[b], None, None, B, size_e, var_dict)
        for v in pg.values():
            if v["patron"]:
                res["patrones"].add(f"grupos | {v['clave']}")
        comunes = sorted(set(Bj[a]["pn"]) & set(Bj[b]["pn"]))
        Fa = Bj[a]["F"][[Bj[a]["pn"].index(p) for p in comunes]]
        Fb = Bj[b]["F"][[Bj[b]["pn"].index(p) for p in comunes]]
        r1, p = cca_par(Fa, Fb, rng)
        res[f"cca {cruce}"] = r1
        res[f"cca {cruce} p"] = p
        cs, gs = conjunto(B, comunes, (a, b), rng, var_dict)
        for t in cs:
            res["patrones"].add(f"PCA conjunto {cruce} | {t}")
        for t in gs:
            res["patrones"].add(f"clustering conjunto {cruce} | {t}")
        # triangulación: patrones de variables de este cruce cuyas variables definen componentes que son patrón
        dominante = {}
        for d in (a, b):
            for i, v in enumerate(Bj[d]["vs"]):
                j = int(np.argmax(np.abs(Bj[d]["L"][i])))
                if abs(Bj[d]["L"][i, j]) >= CARGA:
                    dominante[(d, v)] = f"{d}:cp{j + 1}"
        for f in pares_var:
            lx, ly = lado(f["x"], var_dict, asig), lado(f["y"], var_dict, asig)
            if {lx, ly} != {a, b}:
                continue
            x, y = (f["x"], f["y"]) if lx == a else (f["y"], f["x"])
            ca, cb = dominante.get((a, x)), dominante.get((b, y))
            if ca and cb and pc.get((ca, cb), {}).get("patron"):
                res["patrones"].add(f"triangulación | {a}:{x} ↔ {b}:{y}")
    # ── tres dimensiones ──
    comunes = sorted(set.intersection(*(set(Bt[d]["pn"]) for d in DIMS)))
    idx = {d: [Bt[d]["pn"].index(p) for p in comunes] for d in DIMS}
    bloques = [Bt[d]["F"][idx[d]] for d in DIMS]
    obs = td.estadisticos(bloques)
    n = len(comunes)
    m = max(10, n // 10)
    nul = {k: [] for k in ("gcca", "rv_medio", "mfa1")}
    for _ in range(N_NULA):
        e = td.estadisticos([bloques[0]] + [np.roll(bb, rng.integers(m, n - m), axis=0) for bb in bloques[1:]])
        for k in nul:
            nul[k].append(e[k])
    for k in nul:
        res[k] = obs[k]
        res[k + "_p"] = (1 + sum(x >= obs[k] for x in nul[k])) / (N_NULA + 1)
    Zs = [td._estandar(bb) for bb in bloques]
    W = np.hstack([Z / np.linalg.svd(Z, compute_uv=False)[0] for Z in Zs])
    U, s, _ = np.linalg.svd(W, full_matrices=False)
    res["candidato_tres_dimensiones"] = False
    for f in range(min(3, len(s))):
        temas = defaultdict(set)
        for d in DIMS:
            Zd = Bt[d]["Z"][idx[d]]
            r = np.array([np.corrcoef(Zd[:, j], U[:, f])[0, 1] for j in range(Zd.shape[1])])
            for j in np.where(np.abs(r) >= CARGA_FACTOR)[0]:
                temas[tema(Bt[d]["vs"][j])].add(d)
        if len(set().union(*temas.values()) if temas else set()) == 3:
            res["patrones"].add("tres dimensiones | " + " + ".join(sorted(f"{'/'.join(sorted(ds, key=DIMS.index))}:{t}" for t, ds in temas.items())))
            if CANDIDATO <= set(temas) and len(set().union(*(temas[t] for t in CANDIDATO))) == 3:
                res["candidato_tres_dimensiones"] = True
    return res


# ── criterio de hallazgo entre dimensiones ──────────────────────────────────
# Un patrón de variables cuenta como hallazgo entre dimensiones solo si relaciona dimensiones distintas con
# cualquier asignación de las métricas compartidas (100 % de las asignaciones), es decir, si sus dos variables no
# comparten ninguna dimensión del catálogo. Los demás patrones entre dimensiones dependen de la asignación.
DESCARTADOS_AL_VALIDAR = {
    frozenset(("cdiv_mediana", "commits_doc_producto")): "sin los commits que solo tocan documentación cae a −0,15",
    frozenset(("le_mediana", "anmcc_mediana")): "sin los recién llegados cae a +0,08",
    frozenset(("dev_exp_mediana", "anmcc_mediana")): "sin los recién llegados cae a −0,01",
    frozenset(("sc_mediana", "jarczyk_success_rate_producto")): "sin las issues propias cerradas en el mismo release cae",
}


def hallazgos_entre_dimensiones(pares_var, var_dict):
    cruces_de = defaultdict(list)
    for a, b in CRUCES:
        ruta = corr.SALIDA / "cruces" / f"{a.lower()}_{b.lower()}" / "pares_variables.csv"
        if ruta.exists():
            for r in csv.DictReader(open(ruta, encoding="utf-8")):
                if r["tipo"] == "patrón":
                    cruces_de[frozenset((r["x_id"], r["y_id"]))].append(f"{a}–{b}")
    filas = []
    for f in pares_var:
        k = frozenset((f["x"], f["y"]))
        if f["principal"].startswith("dentro") and f["entre_dimensiones"] == 0:
            continue
        criterio = "hallazgo entre dimensiones" if f["entre_dimensiones"] == 1 else "depende de la asignación"
        filas.append(dict(criterio=criterio, x=f["x"], y=f["y"], rho=f["rho"],
                          catalogo=f"{f['dims_x']} / {f['dims_y']}", entre_dimensiones=f["entre_dimensiones"],
                          con_la_principal="entre dimensiones" if not f["principal"].startswith("dentro") else f["principal"],
                          cruces=", ".join(cruces_de.get(k, [])) or "—", mismo_tema=f["mismo_tema"],
                          validacion=DESCARTADOS_AL_VALIDAR.get(k, "")))
    filas.sort(key=lambda f: (f["criterio"] != "hallazgo entre dimensiones", f["mismo_tema"], -f["entre_dimensiones"], -abs(f["rho"])))
    with open(SALIDA / "hallazgos_entre_dimensiones.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    L = ["# Hallazgos entre dimensiones con cualquier asignación", "",
         "Criterio: un patrón de variables es hallazgo entre dimensiones si relaciona dimensiones distintas con cualquier "
         "asignación de las métricas compartidas, es decir, si sus dos variables no comparten ninguna dimensión del "
         "catálogo. Los demás dependen de la asignación: la relación es la misma, pero según cómo se repartan las "
         "métricas compartidas puede contar como relación dentro de una dimensión. La asignación principal se mantiene "
         "para calcular los componentes y presentar los resultados.", ""]
    for crit in ("hallazgo entre dimensiones", "depende de la asignación"):
        sub = [f for f in filas if f["criterio"] == crit]
        L += [f"## {crit.capitalize()} ({len(sub)})", "",
              "| Par | ρ | Catálogo | Asignaciones en que es entre dimensiones | Con la principal | Cruces | Validación |",
              "|---|---|---|---|---|---|---|"]
        for f in sub:
            L.append(f"| {f['x']} ↔ {f['y']}{' (mismo tema)' if f['mismo_tema'] else ''} | {f['rho']:+.2f} | {f['catalogo']} | "
                     f"{f['entre_dimensiones']:.0%} | {f['con_la_principal']} | {f['cruces']} | "
                     f"{('descartado: ' + f['validacion']) if f['validacion'] else '—'} |")
        L.append("")
    (SALIDA / "hallazgos_entre_dimensiones.md").write_text("\n".join(L), encoding="utf-8")
    return filas


def main(solo_variables=False):
    warnings.filterwarnings("ignore")
    SALIDA.mkdir(parents=True, exist_ok=True)
    print("=== multiverso_asignacion.py ===", flush=True)
    var_dict, datos = pca.cargar_datos()

    pares_var = patrones_variables(var_dict)
    with open(SALIDA / "patrones_variables.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(pares_var[0]))
        w.writeheader()
        w.writerows(pares_var)
    print(f"  cruce de variables: {len(pares_var)} pares patrón", flush=True)
    hallazgos_entre_dimensiones(pares_var, var_dict)
    if solo_variables:
        return

    base = [v for v, r in var_dict.items() if v in datos and r["metrica_id"] not in pca.VARIANTES]
    ventanas = set().union(*(set(datos[v]["versiones"]) for v in base))
    base = [v for v in base if sum(1 for t in datos[v]["versiones"].values() if t[1] is not None) / len(ventanas) >= pca.MIN_COBERTURA]
    vs_tamano = [v for v in base if var_dict[v].get("familia") != "tamano" and v != pca.VARIABLE_TAMANO]
    compartidas = sorted({corr.metrica_base(var_dict[v]["metrica_id"]) for v in base if es_compartida(v, var_dict)})
    opciones = {m: dims_de(next(var_dict[v] for v in base if es_compartida(v, var_dict) and corr.metrica_base(var_dict[v]["metrica_id"]) == m))
                for m in compartidas}
    principal = {m: PRINCIPAL[m] for m in compartidas}
    universos = [("principal", principal)]
    for m in compartidas:
        a = dict(principal)
        a[m] = next(d for d in opciones[m] if d != principal[m])
        universos.append((f"cambia {m}", a))
    universos.append(("opuesta", {m: next(d for d in opciones[m] if d != principal[m]) for m in compartidas}))
    rng = np.random.default_rng(pca.SEMILLA)
    for i in range(N_MUESTRA):
        universos.append((f"azar {i + 1}", {m: opciones[m][rng.integers(2)] for m in compartidas}))
    size_e = datos["activos_interaccion_conteo"]["versiones"]

    filas_u = []
    for i, (nombre, asig) in enumerate(universos):
        if i % 20 == 0:
            print(f"  universo {i + 1} de {len(universos)}…", flush=True)
        r = universo(asig, base, vs_tamano, var_dict, datos, np.random.default_rng(pca.SEMILLA + i), pares_var, size_e)
        if r is None:
            print(f"  {nombre}: sin datos suficientes")
            continue
        r.update(universo=nombre, asig=asig)
        filas_u.append(r)

    # ── resumen por patrón ──
    azar = [r for r in filas_u if r["universo"].startswith("azar")]
    prin = next(r for r in filas_u if r["universo"] == "principal")
    cuenta = Counter(p for r in azar for p in r["patrones"])
    todos = set(cuenta) | prin["patrones"]
    filas_p = []
    for p in todos:
        tipo, clave = p.split(" | ", 1)
        decide = []
        for m in compartidas:
            con = {d: [r for r in azar if r["asig"][m] == d] for d in opciones[m]}
            fr = {d: sum(p in r["patrones"] for r in rs) / max(1, len(rs)) for d, rs in con.items()}
            dif = max(fr.values()) - min(fr.values())
            if dif >= 0.3:
                decide.append(f"{m} en {max(fr, key=fr.get)} ({max(fr.values()):.0%} vs {min(fr.values()):.0%})")
        filas_p.append(dict(analisis=tipo, patron=clave, en_principal=p in prin["patrones"],
                            asignaciones=cuenta[p] / max(1, len(azar)), decide="; ".join(decide)))
    filas_p.sort(key=lambda f: (f["analisis"], -f["asignaciones"]))
    with open(SALIDA / "patrones_cruces.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["analisis", "patron", "en_principal", "asignaciones", "decide"])
        w.writeheader()
        for fila in filas_p:
            w.writerow(dict(fila, asignaciones=round(fila["asignaciones"], 3)))
    cols = ["universo", "k", "gcca", "gcca_p", "rv_medio", "rv_medio_p", "mfa1", "mfa1_p", "candidato_tres_dimensiones"] + \
           [f"cca {a}–{b}" for a, b in CRUCES] + [f"cca {a}–{b} p" for a, b in CRUCES] + [f"lado_{m}" for m in compartidas] + ["patrones"]
    with open(SALIDA / "universos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in filas_u:
            fila = {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k not in ("asig", "patrones")}
            fila.update({f"lado_{m}": r["asig"][m] for m in compartidas}, patrones=" ; ".join(sorted(r["patrones"])))
            w.writerow(fila)
    escribir_md(pares_var, filas_p, filas_u, azar, prin, compartidas)
    print(f"  listo: {SALIDA}")


def escribir_md(pares_var, filas_p, filas_u, azar, prin, compartidas):
    n = len(azar)
    L = ["# Multiverso de asignaciones de las métricas compartidas", "",
         f"{len(compartidas)} métricas compartidas ({', '.join(compartidas)}). Universos: la asignación principal, cada "
         f"métrica cambiada de lado sola, la opuesta y {n} al azar. Los porcentajes son sobre las asignaciones al azar.", "",
         "## 1. Cruce de variables", "",
         "Todos los pares que son patrón en algún nivel (dentro de cada dimensión o en los cruces). Proporción de las "
         "asignaciones posibles en la que relacionan dimensiones distintas; la correlación es la misma en todas.", ""]
    cuenta = Counter(f["tipo"] for f in pares_var)
    L.append(f"Pares de un mismo tema (por ejemplo, dos medidas de la concentración del núcleo) que quedan entre "
             f"dimensiones solo si ese tema se reparte entre dos dimensiones: "
             f"{sum(1 for f in pares_var if f['mismo_tema'] and f['tipo'] == 'nuevo: solo con otras asignaciones')} de los nuevos.")
    L.append("")
    for t in ("entre dimensiones con cualquier asignación", "depende de la asignación", "nuevo: solo con otras asignaciones", "siempre dentro de una dimensión"):
        L.append(f"- **{t}:** {cuenta.get(t, 0)}")
    for t in ("nuevo: solo con otras asignaciones", "depende de la asignación", "entre dimensiones con cualquier asignación"):
        L += ["", f"### {t.capitalize()}", "", "| Par | ρ | Catálogo | Principal | Entre dimensiones | Lecturas |", "|---|---|---|---|---|---|"]
        for f in sorted([f for f in pares_var if f["tipo"] == t], key=lambda f: (-f["entre_dimensiones"], -abs(f["rho"]))):
            L.append(f"| {f['x']} ↔ {f['y']}{' (mismo tema)' if f['mismo_tema'] else ''} | {f['rho']:+.2f} | {f['dims_x']} / {f['dims_y']} | {f['principal']} | "
                     f"{f['entre_dimensiones']:.0%} | {f['lecturas']} |")
    L += ["", "## 2. Cruces de a pares que dependen de la asignación", "",
          "Patrones de componentes, grupos y del conjunto reducido (reconocidos por su tema), componentes y grupos "
          "conjuntos que mezclan dos dimensiones, y triangulaciones: proporción de asignaciones en que aparecen y si "
          "aparecen con la asignación principal. «Decide»: métrica compartida cuyo lado cambia en 30 puntos o más esa proporción.", ""]
    for a, b in CRUCES:
        c = f"{a}–{b}"
        sig = sum(1 for r in azar if r[f"cca {c} p"] < 0.05) / max(1, n)
        L.append(f"- Correlación canónica {c}: mayor que el azar en el {sig:.0%} de las asignaciones; principal "
                 f"{prin[f'cca {c}']:.2f} (p {prin[f'cca {c} p']:.3f})")
    for analisis in ("componentes", "conjunto reducido", "grupos", "triangulación"):
        filas = [f for f in filas_p if f["analisis"] == analisis and (f["asignaciones"] >= 0.1 or f["en_principal"])]
        L += ["", f"### {analisis.capitalize()}", "", "| Patrón | Asignaciones | Con la principal | Decide |", "|---|---|---|---|"]
        for f in filas[:30]:
            L.append(f"| {f['patron']} | {f['asignaciones']:.0%} | {'sí' if f['en_principal'] else 'no'} | {f['decide'] or '—'} |")
    filas = [f for f in filas_p if f["analisis"].startswith(("PCA conjunto", "clustering conjunto")) and (f["asignaciones"] >= 0.2 or f["en_principal"])]
    L += ["", "### PCA y clustering conjunto (componentes y grupos que mezclan las dos dimensiones, sin escala)", "",
          "| Análisis | Temas | Asignaciones | Con la principal |", "|---|---|---|---|"]
    for f in sorted(filas, key=lambda f: (f["analisis"], -f["asignaciones"]))[:30]:
        L.append(f"| {f['analisis']} | {f['patron']} | {f['asignaciones']:.0%} | {'sí' if f['en_principal'] else 'no'} |")
    L += ["", "## 3. Tres dimensiones", "",
          "| Resultado | Asignaciones al azar | Principal |", "|---|---|---|"]
    for k, nombre in (("gcca", "Correlación canónica generalizada mayor que el azar"), ("rv_medio", "RV medio mayor que el azar"),
                      ("mfa1", "Primer factor del MFA mayor que el azar")):
        L.append(f"| {nombre} | {sum(1 for r in azar if r[k + '_p'] < 0.05) / max(1, n):.0%} | {'sí' if prin[k + '_p'] < 0.05 else 'no'} |")
    L.append(f"| Patrón candidato (concentración + cierre de lo viejo + bugs, en tres dimensiones) | "
             f"{sum(1 for r in azar if r['candidato_tres_dimensiones']) / max(1, n):.0%} | {'sí' if prin['candidato_tres_dimensiones'] else 'no'} |")
    filas = [f for f in filas_p if f["analisis"] == "tres dimensiones"]
    temas = Counter()
    for f in filas:
        for t in f["patron"].split(" + "):
            temas[t.split(":", 1)[1]] += 0
    L += ["", "Factores del MFA (de los tres primeros) que juntan las tres dimensiones, por frecuencia:", "",
          "| Temas (dimensiones:tema) | Asignaciones | Con la principal |", "|---|---|---|"]
    for f in sorted(filas, key=lambda f: -f["asignaciones"])[:12]:
        L.append(f"| {f['patron']} | {f['asignaciones']:.0%} | {'sí' if f['en_principal'] else 'no'} |")
    por_tema = Counter()
    for r in azar:
        presentes = set()
        for p in r["patrones"]:
            if p.startswith("tres dimensiones"):
                presentes |= {t.split(":", 1)[1] for t in p.split(" | ", 1)[1].split(" + ")}
        por_tema.update(presentes)
    L += ["", "Temas que forman parte de algún factor de tres dimensiones:", ""]
    for t, c in por_tema.most_common():
        L.append(f"- {t}: {c / max(1, n):.0%}")
    (SALIDA / "resumen.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(solo_variables="--solo-variables" in sys.argv)
