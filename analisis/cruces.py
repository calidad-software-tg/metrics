#!/usr/bin/env python3
"""
analisis/cruces.py

Análisis entre dos dimensiones (por ejemplo Persona–Producto o Proceso–Producto), con el mismo
método que el análisis dentro de cada dimensión:

  1. Cruce de variables: correlación parcial de Spearman entre cada variable de un lado y cada
     variable del otro, con muestra efectiva, Benjamini–Hochberg, estabilidad por período, réplica
     en canary y control por tamaño. Cada par se marca como control, escala (involucra conteos de
     participantes), mecánico (misma familia o definición superpuesta) o patrón.
  2. Cruce de componentes: la misma correlación entre los puntajes por release de los componentes
     firmes de cada dimensión (PCA ya calculado por pca.py).
  3. Conjunto reducido: de cada lado, un puntaje por cada componente firme (o su variable de carga
     más alta) más las variables que no cargan en ningún componente firme. Cruza aspectos completos
     y métricas independientes sin repetir la misma información varias veces.
  4. Correlación canónica (CCA) entre los dos conjuntos de componentes, con una prueba de
     permutación que respeta el orden en el tiempo (corrimiento circular).
  5. Triangulación: un patrón de variables se confirma si sus variables cargan en componentes
     que también se relacionan.
  6. PCA conjunto con las variables de los dos lados: componentes que mezclan dimensiones. Con las mismas
     variables, clustering conjunto: grupos de métricas que mezclan dimensiones, comparados con el PCA conjunto.
  7. Red de métricas: nodos y aristas de las relaciones robustas, para ver qué variables hacen de puente.

  8. Cruce con los grupos del clustering de métricas (--grupos): repite 2–5 con los grupos de
     clustering.py en lugar de los componentes del PCA (ver más abajo).

Usa las funciones de correlaciones.py para evaluar y clasificar cada par, y los resultados ya guardados
de pca.py y clustering.py de cada dimensión (los análisis de cada dimensión no se repiten).

Uso (todo con la base corregida):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruces.py Persona Producto
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruces.py Proceso Producto \\
        --config analisis/cruces/proceso_producto_asignado.json [--periodos calendario|epocas|ambos]
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruces.py Proceso Producto \\
        --config analisis/cruces/proceso_producto_asignado.json --grupos propio [--asignado]

--periodos   períodos de la regla de estabilidad, como en correlaciones.py: calendario (por defecto), épocas
             (en <dima>_<dimb>/epocas/) o ambos, con la comparación en <dima>_<dimb>/comparacion_periodos.csv
             (firme si el patrón pasa con los dos cortes, depende del corte si pasa con uno).
--grupos     cruce con los grupos del clustering, con el corte propio o el del PCA (después del cruce
             de variables, porque usa sus patrones). --asignado saca de cada grupo las métricas que la
             config asigna al otro lado (salida en clustering_<corte>_asignado/).

Requisitos: analisis/salidas/diccionario_variables.csv (generar_diccionario.py) y
analisis/salidas/pca/pca_<dim>.json de las dos dimensiones (pca.py <Dim>); para --grupos, también
clustering_<dim>.json (clustering.py <Dim>).

Configuración (JSON, todo opcional; ver analisis/cruces/*.json):
    lados.<Dim>.niveles      niveles de variable que aporta cada lado ("producto", "persona_agregada").
                             Por defecto, Persona aporta todas las suyas y las otras dimensiones solo las
                             del proyecto (los resúmenes por colaborador son de Persona).
    lados.<Dim>.excluir      variables que no entran.
    lados.<Dim>.variantes    true para incluir las variantes de una métrica (MTTR con bots, etc.).
    compartidas              qué hacer con una variable que queda en los dos lados:
                             "excluir" (por defecto), o el nombre de la dimensión que se la queda.
    asignar                  {variable: dimensión} para resolver compartidas una por una.
    escala.familias          familias que cuentan como escala (por defecto ["tamano"]).
    escala.variables         variables sueltas que cuentan como escala.
    componentes.conjunto     {Dim: "producto" | "todas"} conjunto del PCA a usar.
    componentes.enfoque      "ajustado" (por defecto), "crudo" o "tamano".
    componentes.elegir       {Dim: [1, 4]} componentes a usar; si no, se eligen los firmes.
    componentes.umbral_bootstrap / umbral_canary   umbrales de congruencia para "firme".
    carga_minima             |carga| desde la que una variable define un componente (0,4).
    permutaciones            permutaciones de la prueba de la CCA (1000).
    reducido.modo            "puntajes" (por defecto: el puntaje de cada componente firme) o "marcadoras"
                             (la variable de carga más alta de cada componente).
    reducido.escala_si       proporción de variables de escala entre las que definen un componente a partir
                             de la cual el componente cuenta como escala (0,5).
    pca_conjunto             false para no correr el PCA conjunto.
    clustering_conjunto      false para no correr el clustering conjunto (las mismas variables que el PCA conjunto).
    pca_conjunto_variables   "componentes" (por defecto: las variables con |carga| >= carga_minima en los
                             componentes elegidos de cada lado) o "todas" (necesita 3 releases por variable).

Salidas en analisis/salidas/cruces/<dima>_<dimb>/:
    pares_variables.csv, pares_componentes.csv, pares_reducido.csv, triangulacion.csv, red_nodos.csv, red_aristas.csv,

Cruce con los grupos del clustering (--grupos)
-----------------------------------------------
Cruce entre dos dimensiones usando los grupos del clustering de métricas en lugar de los
componentes del PCA. Repite, con el mismo procedimiento que el cruce de variables y componentes, los análisis que
usan componentes:

  2. Cruce de grupos: la correlación parcial entre la serie por release de cada grupo de una
     dimensión y la de cada grupo de la otra.
  3. Conjunto reducido: de cada lado, la serie de cada grupo de dos o más métricas más las variables
     que quedan solas o fuera del clustering.
  4. Correlación canónica entre los grupos de las dos dimensiones.
  5. Triangulación: un patrón del cruce de variables se confirma si los grupos de sus dos variables
     también forman un patrón.

Cada grupo se convierte en una serie por release de tres formas, y el cruce se hace con cada una:

  promedio        promedio de los rangos ajustados de sus métricas, con el signo orientado (las que
                  correlacionan en negativo con la métrica central del grupo se invierten);
  componente      el primer componente principal de las métricas del grupo (pesos del autovector,
                  orientado como la métrica central);
  representativa  la métrica más parecida al resto del grupo (mayor |correlación| promedio), con la
                  misma transformación que el PCA, como las variables marcadoras del conjunto reducido.

Los grupos, las variables y los releases salen de clustering_<dim>.json (clustering.py), que
a su vez usa las mismas variables y la misma transformación que el PCA de la dimensión. La serie
canary de cada grupo se arma con las mismas métricas y los mismos signos o pesos que la estable.

Uso (después de pca.py y clustering.py de las dos dimensiones y del cruce de variables):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruces.py Persona Producto \\
        --config analisis/cruces/persona_producto.json --grupos propio|pca [--asignado]

--grupos propio usa la cantidad de grupos que elige el clustering; --grupos pca, la misma
cantidad que componentes del PCA.

Salidas en analisis/salidas/cruces/<dima>_<dimb>/clustering_<corte>/:
    <metodo>/pares_grupos.csv, <metodo>/pares_reducido.csv, <metodo>/triangulacion.csv,
    resumen.json y comparacion.md (los tres métodos entre sí y frente al cruce con el PCA).
"""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

import warnings

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import correlaciones as corr  # noqa: E402
import pca  # noqa: E402

ROOT = corr.ROOT
SALIDA = ROOT / "analisis" / "salidas" / "cruces"
PCA_DIR = ROOT / "analisis" / "salidas" / "pca"

DEFAULTS = {
    "lados": {},
    "compartidas": "excluir",
    "asignar": {},
    "escala": {"familias": ["tamano"], "variables": []},
    "componentes": {"conjunto": {}, "enfoque": "ajustado", "elegir": {},
                    "umbral_bootstrap": 0.85, "umbral_canary": 0.70},
    "carga_minima": 0.4,
    "reducido": {"modo": "puntajes", "escala_si": 0.5},
    "permutaciones": 1000,
    "pca_conjunto": True,
    "clustering_conjunto": True,
    "pca_conjunto_variables": "componentes",
}


# ── utilidades ───────────────────────────────────────────────────────────────

def mezclar(base, extra):
    out = json.loads(json.dumps(base))
    for k, v in (extra or {}).items():
        out[k] = mezclar(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def num(v):
    return isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v))


def r4(v):
    return round(float(v), 4) if num(v) else ""


def dims_de(row):
    t = row.get("dims_texto", "")
    return set() if t in ("", "Sin dimensión") else set(t.split("+"))


# ── 1. lados ─────────────────────────────────────────────────────────────────

def armar_lados(dim_a, dim_b, var_dict, cfg):
    def niveles_por_defecto(dim):
        return None if dim == "Persona" else ["producto"]

    lados = {}
    for dim in (dim_a, dim_b):
        c = cfg["lados"].get(dim, {})
        niveles = c.get("niveles", niveles_por_defecto(dim))
        excluir = set(c.get("excluir", []))
        variantes = c.get("variantes", False)
        lados[dim] = sorted(
            v for v, row in var_dict.items()
            if dim in dims_de(row)
            and (niveles is None or row["nivel"] in niveles)
            and v not in excluir
            and (variantes or row["metrica_id"] not in pca.VARIANTES))

    compartidas = sorted(set(lados[dim_a]) & set(lados[dim_b]))
    resueltas = {}
    for v in compartidas:
        destino = cfg["asignar"].get(v, cfg["compartidas"])
        resueltas[v] = destino
        for dim in (dim_a, dim_b):
            if destino != dim and v in lados[dim]:
                lados[dim].remove(v)
    return lados, resueltas


def es_escala(v, var_dict, cfg):
    return var_dict[v].get("familia", "") in cfg["escala"]["familias"] or v in cfg["escala"]["variables"]


# ── 2. un par: el mismo cálculo que correlaciones.py ──────────────────────────────

def evaluar_par(x_e, y_e, x_c, y_c, size_e, tamano_aplica):
    (n, rho_c, p_c, rho_lin, rho_corr, ic_inf, ic_sup, p_corr,
     r1x, r1y, n_ef, rho_per, rxr, ryr, rows_e, rho_canary) = corr.compute_pair(x_e, y_e, x_c, y_c)

    rho_global = rho_corr if num(rho_corr) else 0.0
    n_eval = len(rho_per)
    n_mismo = sum(1 for r in rho_per.values() if num(r) and (r >= 0) == (rho_global >= 0))
    estable = n_eval >= 3 and n_mismo == n_eval

    rho_tamano = np.nan
    if tamano_aplica and n >= 5:
        filas = [(vx, vy, p, d if d else 1.0, size_e[p][1]) for p, d, vx, vy, *_ in rows_e
                 if p in size_e and size_e[p][1] is not None]
        if len(filas) >= 5:
            rho_tamano = corr.partial_spearman([f[0] for f in filas], [f[1] for f in filas],
                                             [f[2] for f in filas], [f[3] for f in filas],
                                             extra_controls=[[corr.safe_log(f[4] + 1) for f in filas]])["rho_corr"]
    out = dict(corr.chequeos_par(rows_e), n=n, n_efectiva=n_ef, rho_cruda=rho_c, rho_corregida=rho_corr,
               ic_inf=ic_inf, ic_sup=ic_sup, p_corregida=p_corr, rho_canary=rho_canary,
               rho_corregida_tamano=rho_tamano, estable=estable,
               _pn=[r[0] for r in rows_e], _xr=list(rxr) if rxr is not None else [], _yr=list(ryr) if ryr is not None else [])
    for label, *_ in corr.ETAPAS:
        out["rho_" + label.replace("-", "_")] = rho_per.get(label, np.nan)
    return out


def clasificar(pares, claves_control):
    """BH sobre los pares que no son de control, categoría, robustez y control por tamaño."""
    p_fdr = corr.benjamini_hochberg([(k, pr["p_corregida"]) for k, pr in pares.items() if k not in claves_control])
    for k, pr in pares.items():
        pr["p_fdr"] = p_fdr.get(k, "")
        cat, fuerza = corr.categoria_y_fuerza(k in claves_control, pr["n"], pr["p_fdr"] if pr["p_fdr"] != "" else np.nan,
                                            pr["rho_corregida"], pr["ic_inf"], pr["ic_sup"])
        pr["categoria"], pr["fuerza"] = cat, fuerza
        cortas = corr.depende_de_ventanas_cortas(pr["rho_corregida"], pr.get("rho_corregida_sin_cortas", np.nan))
        pr["robusta"] = corr.es_robusta(cat, pr["estable"], pr["rho_corregida"], pr["rho_canary"], cortas)
        ok = corr.resiste_tamano(pr["rho_corregida"], pr["rho_corregida_tamano"])
        pr["resiste_tamano"] = "" if ok is None else ok


# ── 3. componentes ───────────────────────────────────────────────────────────

def cargar_pca(dim, cfg):
    archivo = PCA_DIR / f"pca_{dim.lower()}.json"
    if not archivo.exists():
        sys.exit(f"Falta {archivo}: corré pca.py {dim} sobre la misma base.")
    d = json.loads(archivo.read_text(encoding="utf-8"))
    conj = cfg["componentes"]["conjunto"].get(dim) or ("todas" if dim == "Persona" else "producto")
    if f"{conj}|estable|{cfg['componentes']['enfoque']}" not in d["resultados"]:
        conj = next(iter(d["conjuntos"]))
    return d, conj


def congruencia_canary(d, conj, enfoque, j):
    for c in d.get("comparacion", []):
        if (c["conjunto"], c["serie"], c["enfoque"], c["componente"]) == (conj, "canary", enfoque, j + 1):
            return c["congruencia"]
    return np.nan


def alinear_canary(r_e, r_c, j, umbral):
    """Componente de la solución canary que corresponde al j estable (congruencia de Tucker sobre
    las variables comunes) y su signo. None si ninguno llega al umbral."""
    if not r_c:
        return None
    ve, vc = r_e["variables"], r_c["variables"]
    comunes = [v for v in ve if v in vc]
    if len(comunes) < 3:
        return None
    Le = np.array(r_e["varimax"], dtype=float)[[ve.index(v) for v in comunes], j]
    Lc = np.array(r_c["varimax"], dtype=float)[[vc.index(v) for v in comunes]]
    t = [pca.tucker(Le, Lc[:, i]) for i in range(Lc.shape[1])]
    i = int(np.argmax(np.abs(t)))
    return (i, 1.0 if t[i] >= 0 else -1.0) if abs(t[i]) >= umbral else None


def componentes(dim, cfg, duraciones):
    d, conj = cargar_pca(dim, cfg)
    enf = cfg["componentes"]["enfoque"]
    r_e = d["resultados"][f"{conj}|estable|{enf}"]
    r_c = d["resultados"].get(f"{conj}|canary|{enf}")
    k = r_e["k"]
    elegidos = cfg["componentes"]["elegir"].get(dim)
    out = []
    for j in range(k):
        boot = r_e["boot"]["congruencia_mediana"][j]
        can = congruencia_canary(d, conj, enf, j)
        firme = boot >= cfg["componentes"]["umbral_bootstrap"] and num(can) and can >= cfg["componentes"]["umbral_canary"]
        if elegidos is not None and (j + 1) not in elegidos:
            continue
        if elegidos is None and not firme:
            continue
        L = np.array(r_e["varimax"], dtype=float)[:, j]
        cargas = sorted(((v, float(x)) for v, x in zip(r_e["variables"], L)), key=lambda t: -abs(t[1]))

        def serie(res, col, signo, serie_db):
            s = {}
            for fila in res["puntajes"]:
                pnum, ver, fecha = fila[0], fila[1], str(fila[2])
                s[pnum] = (duraciones[serie_db].get(pnum), signo * float(fila[3 + col]),
                           int(fecha[:4]) if fecha[:4].isdigit() else None, ver, fecha)
            return s

        al = alinear_canary(r_e, r_c, j, cfg["componentes"]["umbral_canary"])
        out.append(dict(
            id=f"{dim.lower()}_cp{j + 1}", dim=dim, n=j + 1, conjunto=conj, enfoque=enf,
            varianza=r_e["varianza"][j], bootstrap=boot, canary=can, firme=firme,
            cargas=cargas, variables=r_e["variables"],
            estable=serie(r_e, j, 1.0, "versiones"),
            canary_serie=serie(r_c, al[0], al[1], "versiones_canary") if al else {}))
    return out


def metricas_cp(c, carga_min, var_dict):
    """Métricas base de las variables que definen un componente (|carga| >= carga_min)."""
    return {corr.metrica_base(var_dict[v]["metrica_id"]) for v, x in c["cargas"] if abs(x) >= carga_min and v in var_dict}


def vars_cp(c, carga_min, var_dict):
    """Variables que definen un componente (|carga| >= carga_min)."""
    return [v for v, x in c["cargas"] if abs(x) >= carga_min and v in var_dict]


def solapan(vars_a, vars_b, var_dict):
    """True si alguna variable de un lado tiene una definición superpuesta con alguna del otro
    (la misma regla que entre variables: ANMCC y Contribution Diversity, LE y Development Experience, etc.)."""
    return any(corr.es_solapamiento_definicion(x, y, (var_dict[x]["metrica_id"], var_dict[y]["metrica_id"]))
               for x in vars_a for y in vars_b)


def es_escala_cp(c, carga_min, var_dict, cfg):
    """Un componente cuenta como escala si al menos reducido.escala_si de sus variables fuertes son de escala."""
    fuertes = [v for v, x in c["cargas"] if abs(x) >= carga_min and v in var_dict]
    return bool(fuertes) and sum(es_escala(v, var_dict, cfg) for v in fuertes) / len(fuertes) >= cfg["reducido"]["escala_si"]


def nombre_cp(c, carga_min):
    fuertes = [f"{v} ({x:+.2f})" for v, x in c["cargas"] if abs(x) >= carga_min][:4]
    return f"CP{c['n']} {c['dim']}: " + (", ".join(fuertes) or "sin cargas ≥ umbral")


# ── 4. CCA con permutaciones por corrimiento circular ────────────────────────

def cca(cps_a, cps_b, n_perm, rng):
    comunes = sorted(set.intersection(*(set(c["estable"]) for c in cps_a + cps_b)))
    if len(comunes) < 30 or not cps_a or not cps_b:
        return None
    X = np.array([[c["estable"][p][1] for c in cps_a] for p in comunes])
    Y = np.array([[c["estable"][p][1] for c in cps_b] for p in comunes])

    def corr_canonicas(X, Y):
        Qx, _ = np.linalg.qr(X - X.mean(0))
        Qy, _ = np.linalg.qr(Y - Y.mean(0))
        return np.linalg.svd(Qx.T @ Qy, compute_uv=False)

    obs = corr_canonicas(X, Y)
    n = len(comunes)
    margen = max(10, n // 10)
    nulas = np.array([corr_canonicas(X, np.roll(Y, rng.integers(margen, n - margen), axis=0))[0]
                      for _ in range(n_perm)])
    return dict(n=n, correlaciones=[round(float(v), 4) for v in obs],
                p_primera=round(float((1 + (nulas >= obs[0]).sum()) / (n_perm + 1)), 4),
                nula_p95=round(float(np.percentile(nulas, 95)), 4))


# ── 5. PCA conjunto ──────────────────────────────────────────────────────────

def matriz_conjunta(variables, datos, var_dict, enfoque):
    """Variables de los dos lados con cobertura suficiente y no constantes, y sus releases con todos los datos:
    la misma entrada para el PCA conjunto y el clustering conjunto."""
    ventanas = set().union(*(set(datos[v]["versiones"]) for v in variables))
    cob = {v: sum(1 for t in datos[v]["versiones"].values() if t[1] is not None) / max(1, len(ventanas)) for v in variables}
    vs = [v for v in variables if cob[v] >= pca.MIN_COBERTURA]
    if enfoque == "tamano":
        vs = [v for v in vs if var_dict[v].get("familia") != "tamano" and v != pca.VARIABLE_TAMANO]
    filas, _ = pca.tabla(vs, datos, "versiones")
    constantes = [v for j, v in enumerate(vs) if len({f["valores"][j] for f in filas.values()}) < 2]
    if constantes:
        vs = [v for v in vs if v not in constantes]
        filas, _ = pca.tabla(vs, datos, "versiones")
    return vs, filas


def pca_conjunto(variables, datos, var_dict, enfoque, rng, carga_min, dim_de):
    vs, filas = matriz_conjunta(variables, datos, var_dict, enfoque)
    res = pca.analizar(vs, filas, enfoque, None, rng) if len(filas) >= 30 else None
    if res is None:
        return dict(error=f"pocas ventanas con todos los datos ({len(filas)}) para {len(vs)} variables")
    L = res["sol"]["Lr"]
    comps = []
    for j in range(res["k"]):
        fuertes = [(vs[i], float(L[i, j])) for i in np.argsort(-np.abs(L[:, j])) if abs(L[i, j]) >= carga_min]
        dims = sorted({dim_de[v] for v, _ in fuertes})
        comps.append(dict(n=j + 1, varianza=round(float(res["var"][j]), 4),
                          bootstrap=round(float(res["boot"]["congruencia_mediana"][j]), 4),
                          mixto=len(dims) > 1, dimensiones=dims,
                          cargas=[(v, round(x, 3)) for v, x in fuertes]))
    return dict(n=res["n"], variables=len(vs), excluidas=sorted(set(variables) - set(vs)), k=res["k"],
                criterios=res["criterios"], componentes=comps)


def clustering_conjunto(variables, datos, var_dict, enfoque, dim_de, res_pca):
    """Clustering jerárquico de las métricas de los dos lados juntas, con las mismas variables y releases que el
    PCA conjunto y el mismo método que clustering.py (1 − |correlación|, enlace promedio, corte por silueta frente
    a datos permutados, estabilidad por bootstrap de bloques). Usa su propio generador de números aleatorios, así
    no cambia el resto del cruce. Compara los grupos con los componentes del PCA conjunto."""
    import clustering as cl
    rng = np.random.default_rng(pca.SEMILLA)
    vs, filas = matriz_conjunta(variables, datos, var_dict, enfoque)
    if len(filas) < 30 or len(vs) < 4:
        return dict(error=f"pocas ventanas o variables ({len(filas)} releases, {len(vs)} variables)")
    Z, _ = pca.transformar(filas, enfoque)
    p = Z.shape[1]
    ks = list(range(2, min(cl.K_MAX, p - 1) + 1))
    D = cl.distancias(Z)
    L = cl.arbol(D)
    cut = cl.cortes(L, ks)
    sil = {k: cl.silueta(D, cut[k]) for k in ks}
    nula = cl.nula_silueta(Z, ks, rng)
    supera = [k for k in ks if sil[k] > nula[k]]
    k_propio = max(supera, key=lambda k: sil[k] - nula[k]) if supera else None
    # componente dominante de cada variable en el PCA conjunto (|carga| >= carga mínima), como referencia_pca
    dominante = {}
    if res_pca and "componentes" in res_pca:
        for c in res_pca["componentes"]:
            for v, x in c["cargas"]:
                if abs(x) > abs(dominante.get(v, (None, 0))[1]):
                    dominante[v] = (c["n"], x)
    ref = [dominante[v][0] if v in dominante else -1 - i for i, v in enumerate(vs)]
    soluciones = {}
    k_pca = res_pca.get("k") if res_pca else None
    for nombre, k in (("propio", k_propio), ("pca", k_pca)):
        if k is None or k < 2 or k > p - 1:
            continue
        lab = cut[k] if k in cut else cl.fcluster(L, k, "maxclust")
        grupos = {}
        for v, g in zip(vs, lab):
            grupos.setdefault(int(g), []).append(v)
        filas_g = []
        for g, mv in sorted(grupos.items(), key=lambda x: -len(x[1])):
            dims = sorted({dim_de[v] for v in mv})
            comps = sorted({dominante[v][0] for v in mv if v in dominante})
            filas_g.append(dict(grupo=g, variables=mv, dimensiones=dims, mixto=len(dims) > 1, componentes_pca=comps))
        soluciones[nombre] = dict(k=k, silueta=round(sil.get(k, float("nan")), 4), nula_p95=r4(nula.get(k)),
                                  ari_pca=round(cl.ari(ref, lab), 4), estabilidad=cl.estabilidad(Z, k, lab, rng),
                                  grupos=filas_g)
    return dict(n=int(Z.shape[0]), variables=p, k_propio=k_propio, k_pca=k_pca,
                silueta={str(k): round(sil[k], 4) for k in ks}, nula_p95={str(k): r4(nula[k]) for k in ks},
                soluciones=soluciones)


# ── salida ───────────────────────────────────────────────────────────────────

def escribir_csv(ruta, filas, columnas):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
        w.writeheader()
        for fila in filas:
            w.writerow({c: (r4(fila[c]) if isinstance(fila.get(c), float) else fila.get(c, "")) for c in columnas})



# ── cruce de variables y componentes ─────────────────────────────────────────

def cruzar(dim_a, dim_b, cfg, destino, periodos="calendario"):
    """Cruce de variables, componentes, conjunto reducido, CCA, triangulación y PCA conjunto, en destino."""
    try:
        _cruzar(dim_a, dim_b, cfg, destino, periodos)
    finally:
        if periodos == "epocas":
            corr.usar_periodos("calendario")


def _cruzar(dim_a, dim_b, cfg, destino, periodos):
    rng = np.random.default_rng(pca.SEMILLA)
    warnings.filterwarnings("ignore", message="An input array is constant")
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)

    print(f"=== cruces.py · {dim_a}–{dim_b} · períodos: {periodos} ===", flush=True)
    var_dict, datos = pca.cargar_datos()
    if periodos == "epocas":
        corr.usar_periodos("epocas", datos)
    lados, compartidas = armar_lados(dim_a, dim_b, var_dict, cfg)
    for dim in (dim_a, dim_b):
        print(f"  {dim}: {len(lados[dim])} variables")
    if compartidas:
        print(f"  variables en los dos lados: {', '.join(f'{v} → {d}' for v, d in compartidas.items())}")
    dim_de = {v: dim for dim in (dim_a, dim_b) for v in lados[dim]}
    size_e = datos.get("activos_interaccion_conteo", {}).get("versiones", {})

    # ── 1. variables ──
    pares, control = {}, set()
    for x in lados[dim_a]:
        for y in lados[dim_b]:
            rx, ry = var_dict[x], var_dict[y]
            misma = corr.metrica_base(rx["metrica_id"]) == corr.metrica_base(ry["metrica_id"])
            constr = corr.es_por_construccion(x, y, misma)
            fx, fy = rx.get("familia", ""), ry.get("familia", "")
            pr = evaluar_par(datos[x]["versiones"], datos[y]["versiones"], datos[x]["versiones_canary"],
                             datos[y]["versiones_canary"], size_e, not constr and "tamano" not in (fx, fy))
            k = f"{x}__{y}"
            pr.update(par_id=k, x_id=x, y_id=y, x_dim=dim_a, y_dim=dim_b,
                      x_nombre=rx["nombre_legible"], y_nombre=ry["nombre_legible"],
                      escala=es_escala(x, var_dict, cfg) or es_escala(y, var_dict, cfg),
                      misma_familia=fx not in ("", "otra") and fx == fy,
                      solapamiento=corr.es_solapamiento_definicion(x, y, (rx["metrica_id"], ry["metrica_id"])))
            pares[k] = pr
            if constr:
                control.add(k)
    clasificar(pares, control)
    for k, pr in pares.items():
        pr["control"] = k in control
        pr["mecanico"] = pr["misma_familia"] or pr["solapamiento"]
        pr["patron"] = bool(pr["robusta"] and not pr["control"] and not pr["escala"] and not pr["mecanico"]
                            and pr["resiste_tamano"] is not False)
        pr["tipo"] = ("control" if pr["control"] else "patrón" if pr["patron"] else "escala" if pr["robusta"] and pr["escala"]
                      else "mecánico" if pr["robusta"] and pr["mecanico"] else "no resiste tamaño" if pr["robusta"] else "")
    print(f"  pares de variables: {len(pares)} · robustos {sum(p['robusta'] for p in pares.values())} · "
          f"patrones {sum(p['patron'] for p in pares.values())}")

    # ── 2. componentes ──
    duraciones = {s: {} for s in ("versiones", "versiones_canary")}
    for v in datos:
        if v.startswith("__"):
            continue
        for s in duraciones:
            for p, t in datos[v].get(s, {}).items():
                if t[0] is not None:
                    duraciones[s].setdefault(p, t[0])
    cps = {dim: componentes(dim, cfg, duraciones) for dim in (dim_a, dim_b)}
    pares_cp, control_cp = {}, set()
    for ca in cps[dim_a]:
        for cb in cps[dim_b]:
            pr = evaluar_par(ca["estable"], cb["estable"], ca["canary_serie"], cb["canary_serie"], size_e, True)
            k = f"{ca['id']}__{cb['id']}"
            comunes = metricas_cp(ca, cfg["carga_minima"], var_dict) & metricas_cp(cb, cfg["carga_minima"], var_dict)
            pr.update(par_id=k, x_id=ca["id"], y_id=cb["id"], x_nombre=nombre_cp(ca, cfg["carga_minima"]),
                      y_nombre=nombre_cp(cb, cfg["carga_minima"]), comparten=", ".join(sorted(comunes)),
                      solapamiento=solapan(vars_cp(ca, cfg["carga_minima"], var_dict), vars_cp(cb, cfg["carga_minima"], var_dict), var_dict),
                      escala=es_escala_cp(ca, cfg["carga_minima"], var_dict, cfg) or es_escala_cp(cb, cfg["carga_minima"], var_dict, cfg))
            pares_cp[k] = pr
    clasificar(pares_cp, control_cp)
    for pr in pares_cp.values():
        pr["tipo"] = ("escala" if pr["robusta"] and pr["escala"]
                      else "mecánico" if pr["robusta"] and (pr["comparten"] or pr["solapamiento"])
                      else "no resiste tamaño" if pr["robusta"] and pr["resiste_tamano"] is False
                      else "patrón" if pr["robusta"] else "")
    print(f"  componentes: {dim_a} {[c['n'] for c in cps[dim_a]]} · {dim_b} {[c['n'] for c in cps[dim_b]]} · "
          f"pares robustos {sum(p['robusta'] for p in pares_cp.values())} de {len(pares_cp)}")

    # ── 3. conjunto reducido ──
    def elementos(dim):
        """Puntaje (o variable marcadora) de cada componente firme + variables que no cargan en ninguno."""
        els, cubiertas = [], set()
        for c in cps[dim]:
            fuertes = [v for v, x in c["cargas"] if abs(x) >= cfg["carga_minima"]]
            cubiertas |= set(fuertes)
            escala_cp = es_escala_cp(c, cfg["carga_minima"], var_dict, cfg)
            if cfg["reducido"]["modo"] == "marcadoras" and fuertes:
                v = fuertes[0]
                if v in datos:
                    els.append(dict(id=v, tipo="marcadora", componente=c["id"], nombre=f"{var_dict[v]['nombre_legible']} (marca CP{c['n']})",
                                    e=datos[v]["versiones"], c=datos[v]["versiones_canary"], escala=es_escala(v, var_dict, cfg), familia=var_dict[v].get("familia", ""),
                                    metricas={corr.metrica_base(var_dict[v]["metrica_id"])}, vars=[v]))
            else:
                els.append(dict(id=c["id"], tipo="componente", componente=c["id"], nombre=nombre_cp(c, cfg["carga_minima"]),
                                e=c["estable"], c=c["canary_serie"], escala=escala_cp, familia="",
                                metricas=metricas_cp(c, cfg["carga_minima"], var_dict), vars=fuertes))
        for v in lados[dim]:
            if v not in cubiertas:
                els.append(dict(id=v, tipo="variable", componente="", nombre=var_dict[v]["nombre_legible"],
                                e=datos[v]["versiones"], c=datos[v]["versiones_canary"], escala=es_escala(v, var_dict, cfg), familia=var_dict[v].get("familia", ""),
                                metricas={corr.metrica_base(var_dict[v]["metrica_id"])}, vars=[v]))
        return els
    red_a, red_b = elementos(dim_a), elementos(dim_b)
    pares_red, control_red = {}, set()
    for ea in red_a:
        for eb in red_b:
            k = f"{ea['id']}__{eb['id']}"
            dos_vars = ea["tipo"] != "componente" and eb["tipo"] != "componente"
            if dos_vars and k in pares:
                base = pares[k]
                constr, misma_fam, solap = base["control"], base["misma_familia"], base["solapamiento"]
            else:
                constr = False
                # el componente contiene la misma métrica que el otro lado, o una con definición superpuesta
                solap = bool(ea["metricas"] & eb["metricas"]) or solapan(ea["vars"], eb["vars"], var_dict)
                misma_fam = dos_vars and ea["familia"] not in ("", "otra") and ea["familia"] == eb["familia"]
            tam_aplica = not constr and not (dos_vars and "tamano" in (ea["familia"], eb["familia"]))
            pr = evaluar_par(ea["e"], eb["e"], ea["c"], eb["c"], size_e, tam_aplica)
            pr.update(par_id=k, x_id=ea["id"], y_id=eb["id"], x_nombre=ea["nombre"], y_nombre=eb["nombre"],
                      x_tipo=ea["tipo"], y_tipo=eb["tipo"], escala=ea["escala"] or eb["escala"],
                      misma_familia=misma_fam, solapamiento=solap)
            pares_red[k] = pr
            if constr:
                control_red.add(k)
    clasificar(pares_red, control_red)
    for k, pr in pares_red.items():
        pr["control"] = k in control_red
        pr["mecanico"] = pr["misma_familia"] or pr["solapamiento"]
        pr["patron"] = bool(pr["robusta"] and not pr["control"] and not pr["escala"] and not pr["mecanico"]
                            and pr["resiste_tamano"] is not False)
        pr["tipo"] = ("control" if pr["control"] else "patrón" if pr["patron"] else "escala" if pr["robusta"] and pr["escala"]
                      else "mecánico" if pr["robusta"] and pr["mecanico"] else "no resiste tamaño" if pr["robusta"] else "")
    print(f"  conjunto reducido: {dim_a} {len(red_a)} · {dim_b} {len(red_b)} · pares {len(pares_red)} · "
          f"patrones {sum(p['patron'] for p in pares_red.values())}")

    # ── 4. CCA ──
    res_cca = cca(cps[dim_a], cps[dim_b], cfg["permutaciones"], rng)

    # ── 5. triangulación ──
    def comps_de(v, dim):
        return [c for c in cps[dim] if any(var == v and abs(x) >= cfg["carga_minima"] for var, x in c["cargas"])]
    triang = []
    for pr in pares.values():
        if not pr["patron"]:
            continue
        en_a, en_b = comps_de(pr["x_id"], dim_a), comps_de(pr["y_id"], dim_b)
        apoyos = [pares_cp[f"{ca['id']}__{cb['id']}"] for ca in en_a for cb in en_b]
        robustos = [a for a in apoyos if a["tipo"] == "patrón"]
        triang.append(dict(par_id=pr["par_id"], x_nombre=pr["x_nombre"], y_nombre=pr["y_nombre"],
                           rho_corregida=pr["rho_corregida"],
                           componentes_x=", ".join(f"CP{c['n']}" for c in en_a),
                           componentes_y=", ".join(f"CP{c['n']}" for c in en_b),
                           par_componentes_robusto=", ".join(a["par_id"] for a in robustos),
                           triangulado=bool(robustos)))

    # ── 6. PCA conjunto ──
    res_pca = None
    if cfg["pca_conjunto"]:
        print("  PCA conjunto…", flush=True)
        if cfg["pca_conjunto_variables"] == "todas":
            vars_pca = lados[dim_a] + lados[dim_b]
        else:
            vars_pca = sorted({v for d in (dim_a, dim_b) for c in cps[d] for v, x in c["cargas"]
                               if abs(x) >= cfg["carga_minima"] and v in dim_de})
        res_pca = pca_conjunto(vars_pca, datos, var_dict, cfg["componentes"]["enfoque"],
                               rng, cfg["carga_minima"], dim_de)

    # ── 6b. clustering conjunto (mismas variables y releases que el PCA conjunto) ──
    res_clus = None
    if cfg["pca_conjunto"] and cfg["clustering_conjunto"]:
        print("  clustering conjunto…", flush=True)
        res_clus = clustering_conjunto(vars_pca, datos, var_dict, cfg["componentes"]["enfoque"], dim_de, res_pca)

    # ── 7. red ──
    aristas = [dict(origen=p["x_id"], destino=p["y_id"], rho=p["rho_corregida"], tipo=p["tipo"])
               for p in pares.values() if p["robusta"] and not p["control"]]
    grado = {}
    for a in aristas:
        if a["tipo"] == "patrón":
            for v in (a["origen"], a["destino"]):
                grado[v] = grado.get(v, 0) + 1
    nodos = [dict(variable=v, dimension=dim_de[v], nombre=var_dict[v]["nombre_legible"], grado_patrones=grado.get(v, 0))
             for v in sorted({a["origen"] for a in aristas} | {a["destino"] for a in aristas})]

    # ── escribir ──
    cols = ["par_id", "x_id", "y_id", "x_nombre", "y_nombre", "tipo", "categoria", "fuerza", "n", "n_efectiva",
            "rho_cruda", "rho_corregida", "ic_inf", "ic_sup", "p_corregida", "p_fdr", "rho_2016_2019", "rho_2020_2022",
            "rho_2023_2024", "rho_2025_2026", "estable", "rho_canary", "rho_corregida_tamano", "resiste_tamano",
            "rho_corregida_sin_cortas", "rho_corregida_local", "alcance_temporal", "robusta", "escala", "misma_familia",
            "solapamiento", "control", "patron"]
    escribir_csv(destino / "pares_variables.csv", sorted(pares.values(), key=lambda p: -abs(p["rho_corregida"]) if num(p["rho_corregida"]) else 0), cols)
    escribir_csv(destino / "pares_componentes.csv", list(pares_cp.values()), [c for c in cols if c not in ("escala", "misma_familia", "solapamiento", "control", "patron")] + ["comparten", "solapamiento", "escala"])
    escribir_csv(destino / "pares_reducido.csv", sorted(pares_red.values(), key=lambda p: -abs(p["rho_corregida"]) if num(p["rho_corregida"]) else 0),
                 ["x_tipo", "y_tipo"] + cols)
    escribir_csv(destino / "triangulacion.csv", triang, list(triang[0]) if triang else ["par_id"])
    escribir_csv(destino / "red_aristas.csv", aristas, ["origen", "destino", "rho", "tipo"])
    escribir_csv(destino / "red_nodos.csv", nodos, ["variable", "dimension", "nombre", "grado_patrones"])
    resumen = dict(
        dimensiones=[dim_a, dim_b], configuracion=cfg, variables={d: lados[d] for d in (dim_a, dim_b)},
        compartidas=compartidas,
        conteo_variables={t: sum(1 for p in pares.values() if p["tipo"] == t) for t in ("patrón", "escala", "mecánico", "no resiste tamaño", "control")},
        componentes={d: [dict(n=c["n"], conjunto=c["conjunto"], varianza=c["varianza"], bootstrap=c["bootstrap"],
                              canary=r4(c["canary"]), cargas=[(v, round(x, 3)) for v, x in c["cargas"] if abs(x) >= cfg["carga_minima"]])
                         for c in cps[d]] for d in (dim_a, dim_b)},
        reducido=dict(modo=cfg["reducido"]["modo"],
                      elementos={d: [dict(id=e["id"], tipo=e["tipo"], componente=e["componente"], nombre=e["nombre"], escala=e["escala"])
                                     for e in els] for d, els in ((dim_a, red_a), (dim_b, red_b))},
                      conteo={t: sum(1 for p in pares_red.values() if p["tipo"] == t) for t in ("patrón", "escala", "mecánico", "no resiste tamaño", "control")}),
        cca=res_cca, pca_conjunto=res_pca, clustering_conjunto=res_clus)
    # valores por release para el reporte (reporte_cruce_dimensiones.py)
    releases = {}
    for v in dim_de:
        for pnum, t in datos[v]["versiones"].items():
            if pnum not in releases and t[3]:
                fh = str(t[4] or "")
                releases[pnum] = [t[3], f"{fh[:4]}-{fh[4:6]}-{fh[6:8]}" if len(fh) >= 8 else "", t[2]]
    def residuos(pr):
        return dict(p=pr["_pn"], xr=[r4(v) for v in pr["_xr"]], yr=[r4(v) for v in pr["_yr"]])
    valores = dict(
        releases=releases,
        serie={v: {p: r4(t[1]) for p, t in datos[v]["versiones"].items() if t[1] is not None} for v in dim_de},
        residuos={k: residuos(pr) for k, pr in pares.items() if pr["robusta"] and not pr["control"]},
        componentes={c["id"]: {p: r4(t[1]) for p, t in c["estable"].items()} for d in (dim_a, dim_b) for c in cps[d]},
        residuos_cp={k: residuos(pr) for k, pr in pares_cp.items()},
        residuos_red={k: residuos(pr) for k, pr in pares_red.items() if pr["robusta"] and not pr["control"]},
    )
    (destino / "valores.json").write_text(json.dumps(valores, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (destino / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    f = lambda v, d=2: f"{v:+.{d}f}".replace(".", ",") if num(v) else "—"
    md = [f"# Cruce {dim_a}–{dim_b}", "",
          f"Variables: {dim_a} {len(lados[dim_a])}, {dim_b} {len(lados[dim_b])}" +
          (f". En los dos lados: {', '.join(f'{v} → {d}' for v, d in compartidas.items())}." if compartidas else "."), "",
          "## Variables", "", "| Tipo | Pares |", "|---|---|"]
    md += [f"| {t} | {n} |" for t, n in resumen["conteo_variables"].items()] + ["", "### Patrones (robustos, sin escala ni construcción)", "",
           "| Par | ρ corregida | con tamaño | canary | alcance |", "|---|---|---|---|---|"]
    md += [f"| {p['x_nombre']} ↔ {p['y_nombre']} | {f(p['rho_corregida'])} | {f(p['rho_corregida_tamano'])} | {f(p['rho_canary'])} | {p.get('alcance_temporal', '')} |"
           for p in sorted(pares.values(), key=lambda p: -abs(p["rho_corregida"]) if num(p["rho_corregida"]) else 0) if p["patron"]]
    md += ["", "## Componentes", ""]
    for d in (dim_a, dim_b):
        md += [f"- {nombre_cp(c, cfg['carga_minima'])} · bootstrap {f(c['bootstrap'])} · canary {f(c['canary'])}" for c in cps[d]]
    md += ["", "| Par de componentes | ρ corregida | con tamaño | canary | resultado |", "|---|---|---|---|---|"]
    md += [f"| {p['x_nombre']} ↔ {p['y_nombre']} | {f(p['rho_corregida'])} | {f(p['rho_corregida_tamano'])} | {f(p['rho_canary'])} | {p['tipo'] or 'no robusto'} |"
           for p in pares_cp.values()]
    md += ["", "## Conjunto reducido", "",
           f"De cada lado: {'el puntaje de cada componente firme' if cfg['reducido']['modo'] == 'puntajes' else 'la variable de carga más alta de cada componente firme'} "
           f"más las variables que no cargan en ningún componente. {dim_a}: {len(red_a)} elementos · {dim_b}: {len(red_b)} · {len(pares_red)} pares.", "",
           "| Tipo | Pares |", "|---|---|"] + [f"| {t} | {n} |" for t, n in resumen["reducido"]["conteo"].items()]
    md += ["", "| Par | ρ corregida | con tamaño | canary | tipo |", "|---|---|---|---|---|"]
    md += [f"| {p['x_nombre']} ↔ {p['y_nombre']} | {f(p['rho_corregida'])} | {f(p['rho_corregida_tamano'])} | {f(p['rho_canary'])} | {p['tipo']} |"
           for p in sorted(pares_red.values(), key=lambda p: -abs(p["rho_corregida"]) if num(p["rho_corregida"]) else 0) if p["robusta"] and not p["control"]]
    if res_cca:
        md += ["", "## Correlación canónica entre componentes", "",
               f"Correlaciones canónicas: {', '.join(f(v) for v in res_cca['correlaciones'])} (n = {res_cca['n']}). "
               f"Primera frente a la nula por corrimiento circular: p = {res_cca['p_primera']:.3f} (percentil 95 nulo {f(res_cca['nula_p95'])})."]
    if triang:
        md += ["", "## Triangulación", "", "| Par | componentes | par de componentes robusto |", "|---|---|---|"]
        md += [f"| {t['x_nombre']} ↔ {t['y_nombre']} | {t['componentes_x'] or '—'} / {t['componentes_y'] or '—'} | {t['par_componentes_robusto'] or 'no'} |" for t in triang]
    if res_pca and "componentes" in res_pca:
        md += ["", "## PCA conjunto", "", f"{res_pca['variables']} variables, {res_pca['n']} releases, Horn retiene {res_pca['k']}.", ""]
        md += [f"- CP{c['n']} ({c['varianza']:.0%}){' · **mezcla dimensiones**' if c['mixto'] else ''}: " +
               ", ".join(f"{v} ({x:+.2f})" for v, x in c["cargas"][:6]) for c in res_pca["componentes"]]
    elif res_pca:
        md += ["", "## PCA conjunto", "", res_pca["error"]]
    if res_clus and "soluciones" in res_clus:
        md += ["", "## Clustering conjunto", "",
               f"{res_clus['variables']} variables, {res_clus['n']} releases; corte propio: "
               f"{res_clus['k_propio'] or 'ninguno supera la nula'}."]
        for nombre, sol in res_clus["soluciones"].items():
            md += ["", f"**Corte {nombre}** ({sol['k']} grupos): silueta {f(sol['silueta'])} (nula p95 {f(sol['nula_p95'])}), "
                       f"ARI con el PCA conjunto {f(sol['ari_pca'])}, estabilidad {f(sol['estabilidad']['mediana'])}.", ""]
            md += [f"- {'**mezcla dimensiones** · ' if g['mixto'] else ''}" + ", ".join(g["variables"])
                   + (f" (CP {', '.join(map(str, g['componentes_pca']))} del PCA conjunto)" if g["componentes_pca"] else "")
                   for g in sol["grupos"] if len(g["variables"]) > 1]
    elif res_clus:
        md += ["", "## Clustering conjunto", "", res_clus["error"]]
    (destino / "resumen.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"  salida: {destino}")


def comparar_periodos(dir_calendario, dir_epocas, destino):
    """Patrones con el calendario y con las épocas, en los pares de variables, de componentes y del conjunto
    reducido: firme si pasa con los dos cortes, depende del corte si pasa con uno."""
    filas, conteo = [], {}
    for archivo in ("pares_variables.csv", "pares_componentes.csv", "pares_reducido.csv"):
        leer = lambda d: {r["par_id"]: r for r in csv.DictReader(open(Path(d) / archivo, newline="", encoding="utf-8"))}
        cal, epo = leer(dir_calendario), leer(dir_epocas)
        c = conteo.setdefault(archivo, dict(firme=0, solo_calendario=0, solo_epocas=0))
        for pid in sorted(set(cal) | set(epo)):
            a, b = cal.get(pid, {}), epo.get(pid, {})
            pa, pb = a.get("tipo") == "patrón", b.get("tipo") == "patrón"
            if not (pa or pb):
                continue
            estado = "firme" if pa and pb else "solo_calendario" if pa else "solo_epocas"
            c[estado] += 1
            r = a or b
            filas.append(dict(archivo=archivo, par_id=pid, x=r.get("x_nombre", ""), y=r.get("y_nombre", ""),
                              estado=estado, tipo_calendario=a.get("tipo", ""), tipo_epocas=b.get("tipo", ""),
                              rho_corregida=r.get("rho_corregida", ""),
                              **{f"cal_{p}": a.get(f"rho_{p}", "") for p in ("2016_2019", "2020_2022", "2023_2024", "2025_2026")},
                              **{f"ep_E{i + 1}": b.get(f"rho_{p}", "") for i, p in enumerate(("2016_2019", "2020_2022", "2023_2024", "2025_2026"))}))
    escribir_csv(Path(destino) / "comparacion_periodos.csv", filas, list(filas[0]) if filas else ["archivo", "par_id"])
    for archivo, c in conteo.items():
        print(f"  {archivo}: firmes {c['firme']} · solo calendario {c['solo_calendario']} · solo épocas {c['solo_epocas']}")
    return conteo


# ── cruce con los grupos del clustering ──────────────────────────────────────

METODOS = ("promedio", "componente", "representativa")
SERIE_DB = dict(pca.SERIES)


def cargar_clustering(dim):
    archivo = PCA_DIR / f"clustering_{dim.lower()}.json"
    if not archivo.exists():
        sys.exit(f"Falta {archivo}: corré antes clustering.py {dim}.")
    return json.loads(archivo.read_text(encoding="utf-8"))


def matriz(variables, datos, serie, enfoque):
    """Misma matriz que el PCA y el clustering: rangos sin tendencia ni duración, estandarizados."""
    filas, _ = pca.tabla(variables, datos, SERIE_DB[serie])
    if len(filas) < 30:
        return None, [], {}
    Z, pnums = pca.transformar(filas, enfoque)
    return Z, pnums, filas


def a_serie(valores, pnums, filas, duraciones, serie_db):
    """dict pnum -> (duración, valor, año, versión, fecha), el formato de evaluar_par."""
    return {p: (duraciones[serie_db].get(p, filas[p]["dur"]), float(v), filas[p]["anio"], filas[p]["version"], filas[p]["fecha"])
            for p, v in zip(pnums, valores)}


def grupos_de(dim, cfg, datos, duraciones, corte, var_dict, permitidas=None):
    C = cargar_clustering(dim)
    _, conj = cargar_pca(dim, cfg)
    enf = cfg["componentes"]["enfoque"]
    ke, kc = f"{conj}|estable|{enf}", f"{conj}|canary|{enf}"
    if ke not in C["resultados"] or corte not in C["resultados"][ke]["soluciones"]:
        sys.exit(f"{dim}: no hay corte '{corte}' para {ke} en clustering_{dim.lower()}.json.")
    Ce = C["resultados"][ke]
    sol = Ce["soluciones"][corte]
    vs = Ce["variables"]
    Ze, pe, fe = matriz(vs, datos, "estable", enf)
    Cc = C["resultados"].get(kc)
    vc = Cc["variables"] if Cc else []
    Zc, pc, fc = matriz(vc, datos, "canary", enf) if Cc else (None, [], {})
    miembros = {}
    for v, g in zip(vs, sol["etiquetas"]):
        miembros.setdefault(g, []).append(v)
    if permitidas is not None:
        # cada grupo conserva solo las métricas de su lado (las compartidas se reparten como en el cruce de variables)
        miembros = {g: [v for v in mv if v in permitidas] for g, mv in miembros.items()}
        miembros = {g: mv for g, mv in miembros.items() if mv}
    grupos, sueltas = [], []
    for g, mv in sorted(miembros.items(), key=lambda x: -len(x[1])):
        if len(mv) < 2:
            sueltas += mv
            continue
        idx = [vs.index(v) for v in mv]
        R = np.corrcoef(Ze[:, idx], rowvar=False)
        central = int(np.argmax(np.abs(R).mean(axis=0)))          # la más parecida al resto
        signo = np.sign(R[central])
        signo[signo == 0] = 1.0
        val, vec = np.linalg.eigh(R)
        w = vec[:, -1] * (1.0 if vec[central, -1] >= 0 else -1.0)
        series = {}
        for metodo in METODOS:
            for serie, Z, pn, fil, vlist in (("estable", Ze, pe, fe, vs), ("canary", Zc, pc, fc, vc)):
                if Z is None or any(v not in vlist for v in mv):
                    series[(metodo, serie)] = {}
                    continue
                cols = [vlist.index(v) for v in mv]
                if metodo == "promedio":
                    x = (Z[:, cols] * signo).mean(axis=1)
                    series[(metodo, serie)] = a_serie(x, pn, fil, duraciones, SERIE_DB[serie])
                elif metodo == "componente":
                    x = Z[:, cols] @ w / np.sqrt(max(val[-1], 1e-12))
                    series[(metodo, serie)] = a_serie(x, pn, fil, duraciones, SERIE_DB[serie])
                else:
                    # la columna ya transformada de la métrica central: con los valores originales, la
                    # correlación canónica (que no descuenta la tendencia) mezclaría el crecimiento del proyecto
                    x = Z[:, cols[central]] * signo[central]
                    series[(metodo, serie)] = a_serie(x, pn, fil, duraciones, SERIE_DB[serie])
        grupos.append(dict(
            id=f"{dim.lower()}_g{len(grupos) + 1}", dim=dim, n=len(grupos) + 1, variables=mv,
            central=mv[central], signos=[int(s) for s in signo], pesos=[round(float(x), 3) for x in w],
            varianza_grupo=round(float(val[-1] / len(mv)), 3),
            # para las reglas de escala y de métricas compartidas, todas las métricas del grupo cuentan como "fuertes"
            cargas=[(v, float(s)) for v, s in zip(mv, signo)],
            series=series))
    return dict(conjunto=conj, enfoque=enf, corte=corte, k=sol["k"], estabilidad=sol["estabilidad"]["mediana"],
                ari_canary=sol.get("ari_canary"), ari_pca=sol["ari_pca"], grupos=grupos, sueltas=sueltas,
                cubiertas=set(vs))


def nombre_g(g, var_dict, metodo):
    vs = [var_dict[v]["nombre_legible"].split(" (")[0].replace(" [producto]", "") for v in g["variables"]]
    extra = f" · representa {var_dict[g['central']]['nombre_legible'].split(' (')[0]}" if metodo == "representativa" else ""
    return f"G{g['n']} {g['dim']}: " + ", ".join(vs[:5]) + ("…" if len(vs) > 5 else "") + extra


def tipo_par(pr):
    pr["control"] = pr.get("control", False)
    pr["mecanico"] = pr.get("misma_familia", False) or pr.get("solapamiento", False)
    pr["patron"] = bool(pr["robusta"] and not pr["control"] and not pr["escala"] and not pr["mecanico"]
                        and pr["resiste_tamano"] is not False)
    pr["tipo"] = ("control" if pr["control"] else "patrón" if pr["patron"] else "escala" if pr["robusta"] and pr["escala"]
                  else "mecánico" if pr["robusta"] and pr["mecanico"] else "no resiste tamaño" if pr["robusta"] else "")


def correr(metodo, G, dim_a, dim_b, lados, datos, var_dict, cfg, size_e, pares_var, rng):
    cm = cfg["carga_minima"]
    serie = lambda g, s: g["series"][(metodo, s)]
    # ── cruce de grupos ──
    pares_g = {}
    for ga in G[dim_a]["grupos"]:
        for gb in G[dim_b]["grupos"]:
            pr = evaluar_par(serie(ga, "estable"), serie(gb, "estable"), serie(ga, "canary"), serie(gb, "canary"), size_e, True)
            comunes = metricas_cp(ga, cm, var_dict) & metricas_cp(gb, cm, var_dict)
            pr.update(par_id=f"{ga['id']}__{gb['id']}", x_id=ga["id"], y_id=gb["id"],
                      x_nombre=nombre_g(ga, var_dict, metodo), y_nombre=nombre_g(gb, var_dict, metodo),
                      comparten=", ".join(sorted(comunes)),
                      escala=es_escala_cp(ga, cm, var_dict, cfg) or es_escala_cp(gb, cm, var_dict, cfg),
                      solapamiento=bool(comunes) or solapan(ga["variables"], gb["variables"], var_dict))
            pares_g[pr["par_id"]] = pr
    clasificar(pares_g, set())
    for pr in pares_g.values():
        tipo_par(pr)

    # ── conjunto reducido: grupos de dos o más métricas + variables solas o fuera del clustering ──
    def elementos(dim):
        els = []
        for g in G[dim]["grupos"]:
            els.append(dict(id=g["id"], tipo="grupo", nombre=nombre_g(g, var_dict, metodo), e=serie(g, "estable"), c=serie(g, "canary"),
                            escala=es_escala_cp(g, cm, var_dict, cfg), familia="", metricas=metricas_cp(g, cm, var_dict),
                            vars=g["variables"]))
        en_grupo = {v for g in G[dim]["grupos"] for v in g["variables"]}
        for v in lados[dim]:
            if v not in en_grupo:
                els.append(dict(id=v, tipo="variable", nombre=var_dict[v]["nombre_legible"], e=datos[v]["versiones"], c=datos[v]["versiones_canary"],
                                escala=es_escala(v, var_dict, cfg), familia=var_dict[v].get("familia", ""),
                                metricas={corr.metrica_base(var_dict[v]["metrica_id"])}, vars=[v]))
        return els
    red_a, red_b = elementos(dim_a), elementos(dim_b)
    pares_r, control_r = {}, set()
    for ea in red_a:
        for eb in red_b:
            k = f"{ea['id']}__{eb['id']}"
            dos_vars = ea["tipo"] == "variable" and eb["tipo"] == "variable"
            if dos_vars and k in pares_var:
                base = pares_var[k]
                constr, misma_fam, solap = base["control"], base["misma_familia"], base["solapamiento"]
            else:
                constr = False
                solap = bool(ea["metricas"] & eb["metricas"]) or solapan(ea["vars"], eb["vars"], var_dict)
                misma_fam = dos_vars and ea["familia"] not in ("", "otra") and ea["familia"] == eb["familia"]
            tam = not constr and not (dos_vars and "tamano" in (ea["familia"], eb["familia"]))
            pr = evaluar_par(ea["e"], eb["e"], ea["c"], eb["c"], size_e, tam)
            pr.update(par_id=k, x_id=ea["id"], y_id=eb["id"], x_nombre=ea["nombre"], y_nombre=eb["nombre"],
                      x_tipo=ea["tipo"], y_tipo=eb["tipo"], escala=ea["escala"] or eb["escala"],
                      misma_familia=misma_fam, solapamiento=solap)
            pares_r[k] = pr
            if constr:
                control_r.add(k)
    clasificar(pares_r, control_r)
    for k, pr in pares_r.items():
        pr["control"] = k in control_r
        tipo_par(pr)

    # ── correlación canónica ──
    cps = {d: [dict(estable=serie(g, "estable")) for g in G[d]["grupos"]] for d in (dim_a, dim_b)}
    res_cca = cca(cps[dim_a], cps[dim_b], cfg["permutaciones"], rng)

    # ── triangulación ──
    def grupo_de(v, dim):
        return next((g for g in G[dim]["grupos"] if v in g["variables"]), None)
    triang = []
    for pr in pares_var.values():
        if not pr["patron"]:
            continue
        ga, gb = grupo_de(pr["x_id"], dim_a), grupo_de(pr["y_id"], dim_b)
        apoyo = pares_g.get(f"{ga['id']}__{gb['id']}") if ga and gb else None
        triang.append(dict(par_id=pr["par_id"], x_nombre=pr["x_nombre"], y_nombre=pr["y_nombre"], rho_corregida=pr["rho_corregida"],
                           grupo_x=f"G{ga['n']}" if ga else "solo", grupo_y=f"G{gb['n']}" if gb else "solo",
                           par_grupos=apoyo["par_id"] if apoyo else "", rho_grupos=apoyo["rho_corregida"] if apoyo else "",
                           tipo_par_grupos=(apoyo["tipo"] or "no robusto") if apoyo else "",
                           triangulado=bool(apoyo and apoyo["tipo"] == "patrón")))
    return pares_g, pares_r, red_a, red_b, res_cca, triang


def leer_csv(ruta):
    if not ruta.exists():
        return []
    with open(ruta, encoding="utf-8") as f:
        return list(csv.DictReader(f))



def cruzar_grupos(dim_a, dim_b, cfg, corte="propio", asignado=False):
    warnings.filterwarnings("ignore")
    base = SALIDA / f"{dim_a.lower()}_{dim_b.lower()}"
    if not (base / "pares_variables.csv").exists():
        sys.exit(f"Falta {base / 'pares_variables.csv'}: corré antes cruces.py {dim_a} {dim_b}.")
    destino = base / (f"clustering_{corte}" + ("_asignado" if asignado else ""))
    destino.mkdir(parents=True, exist_ok=True)

    print(f"=== cruces.py · {dim_a}–{dim_b} · grupos, corte {corte}{' (asignado)' if asignado else ''} ===", flush=True)
    var_dict, datos = pca.cargar_datos()
    lados, _ = armar_lados(dim_a, dim_b, var_dict, cfg)
    size_e = datos.get("activos_interaccion_conteo", {}).get("versiones", {})
    duraciones = {s: {} for s in ("versiones", "versiones_canary")}
    for v in datos:
        if not v.startswith("__"):
            for s in duraciones:
                for p, t in datos[v].get(s, {}).items():
                    if t[0] is not None:
                        duraciones[s].setdefault(p, t[0])
    G = {d: grupos_de(d, cfg, datos, duraciones, corte, var_dict, set(lados[d]) if asignado else None)
         for d in (dim_a, dim_b)}
    for d in (dim_a, dim_b):
        g = G[d]
        print(f"  {d}: {g['k']} grupos ({len(g['grupos'])} de dos o más métricas, {len(g['sueltas'])} métricas solas) · "
              f"estabilidad {g['estabilidad']:.2f} · canary {g['ari_canary'] if g['ari_canary'] is None else round(g['ari_canary'], 2)}")

    # patrones del cruce de variables, para el conjunto reducido y la triangulación
    pares_var = {}
    for r in leer_csv(base / "pares_variables.csv"):
        b = lambda c: r.get(c) == "True"
        pares_var[r["par_id"]] = dict(par_id=r["par_id"], x_id=r["x_id"], y_id=r["y_id"], x_nombre=r["x_nombre"], y_nombre=r["y_nombre"],
                                      rho_corregida=float(r["rho_corregida"]) if r["rho_corregida"] else np.nan,
                                      patron=b("patron"), control=b("control"), misma_familia=b("misma_familia"), solapamiento=b("solapamiento"))
    pca_cp = leer_csv(base / "pares_componentes.csv")
    pca_red = leer_csv(base / "pares_reducido.csv")

    cols = ["par_id", "x_nombre", "y_nombre", "tipo", "categoria", "n", "rho_corregida", "ic_inf", "ic_sup", "p_fdr",
            "rho_2016_2019", "rho_2020_2022", "rho_2023_2024", "rho_2025_2026", "estable", "rho_canary",
            "rho_corregida_tamano", "resiste_tamano", "robusta", "escala", "comparten"]
    res = {}
    for metodo in METODOS:
        rng = np.random.default_rng(pca.SEMILLA)
        pares_g, pares_r, red_a, red_b, res_cca, triang = correr(metodo, G, dim_a, dim_b, lados, datos, var_dict, cfg, size_e, pares_var, rng)
        (destino / metodo).mkdir(exist_ok=True)
        orden = lambda d: sorted(d.values(), key=lambda p: -abs(p["rho_corregida"]) if num(p["rho_corregida"]) else 0)
        escribir_csv(destino / metodo / "pares_grupos.csv", orden(pares_g), cols)
        escribir_csv(destino / metodo / "pares_reducido.csv", orden(pares_r), ["x_tipo", "y_tipo"] + cols)
        escribir_csv(destino / metodo / "triangulacion.csv", triang, list(triang[0]) if triang else ["par_id"])
        cuenta = lambda d: {t: sum(1 for p in d.values() if p["tipo"] == t) for t in ("patrón", "escala", "mecánico", "no resiste tamaño", "control")}
        res[metodo] = dict(
            grupos={"pares": len(pares_g), "tipos": cuenta(pares_g),
                    "robustos": [dict(par=p["par_id"], x=p["x_nombre"], y=p["y_nombre"], rho=r4(p["rho_corregida"]),
                                      tamano=r4(p["rho_corregida_tamano"]), canary=r4(p["rho_canary"]), tipo=p["tipo"])
                                 for p in orden(pares_g) if p["robusta"]]},
            reducido={"elementos": {dim_a: len(red_a), dim_b: len(red_b)}, "pares": len(pares_r), "tipos": cuenta(pares_r),
                      "patrones": [dict(par=p["par_id"], x=p["x_nombre"], y=p["y_nombre"], rho=r4(p["rho_corregida"]),
                                        tamano=r4(p["rho_corregida_tamano"]), canary=r4(p["rho_canary"]))
                                   for p in orden(pares_r) if p["patron"]]},
            cca=res_cca,
            triangulacion=dict(patrones=len(triang), triangulados=sum(t["triangulado"] for t in triang),
                               detalle=[{k: (r4(v) if isinstance(v, float) else v) for k, v in t.items()} for t in triang]))
        r_ = res[metodo]
        print(f"  {metodo:15s} grupos: {r_['grupos']['tipos']} · reducido: {r_['reducido']['tipos']} · "
              f"CCA {res_cca['correlaciones'][0] if res_cca else '—'} (p {res_cca['p_primera'] if res_cca else '—'}) · "
              f"triangulados {r_['triangulacion']['triangulados']} de {r_['triangulacion']['patrones']}", flush=True)

    resumen = dict(dimensiones=[dim_a, dim_b], corte=corte,
                   grupos={d: dict(k=G[d]["k"], conjunto=G[d]["conjunto"], estabilidad=G[d]["estabilidad"], ari_canary=G[d]["ari_canary"],
                                   ari_pca=G[d]["ari_pca"], sueltas=G[d]["sueltas"],
                                   grupos=[dict(id=g["id"], variables=g["variables"], central=g["central"], signos=g["signos"],
                                                pesos=g["pesos"], varianza_grupo=g["varianza_grupo"]) for g in G[d]["grupos"]])
                           for d in (dim_a, dim_b)},
                   metodos=res)
    (destino / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    # ── comparación entre métodos y con el cruce que usa el PCA ──
    f = lambda v: f"{float(v):+.2f}".replace(".", ",") if v not in ("", None) and num(float(v)) else "—"
    md = [f"# Cruce {dim_a}–{dim_b} con los grupos del clustering (corte {corte})", ""]
    for d in (dim_a, dim_b):
        g = G[d]
        md += [f"## Grupos de {d}", "",
               f"{g['k']} grupos en total, {len(g['grupos'])} de dos o más métricas · estabilidad {g['estabilidad']:.2f} · "
               f"canary {'—' if g['ari_canary'] is None else round(g['ari_canary'], 2)} · coincidencia con el PCA {g['ari_pca']:.2f}", ""]
        md += [f"- G{x['n']}: {', '.join(x['variables'])} (central: {x['central']}; varianza del primer componente {x['varianza_grupo']:.0%})"
               for x in g["grupos"]]
        md += [f"- Solas: {', '.join(g['sueltas'])}" if g["sueltas"] else "", ""]
    md += ["## Resumen por método", "",
           "| | Promedio | Primer componente | Más representativa |", "|---|---|---|---|"]
    fila = lambda t, fn: f"| {t} | " + " | ".join(fn(res[m]) for m in METODOS) + " |"
    md += [fila("Pares de grupos robustos", lambda r: str(len(r["grupos"]["robustos"]))),
           fila("Patrones entre grupos", lambda r: str(r["grupos"]["tipos"]["patrón"])),
           fila("Patrones en el conjunto reducido", lambda r: str(r["reducido"]["tipos"]["patrón"])),
           fila("Primera correlación canónica", lambda r: (f"{r['cca']['correlaciones'][0]:.2f} (p {r['cca']['p_primera']:.3f})".replace(".", ",") if r["cca"] else "—")),
           fila("Patrones triangulados", lambda r: f"{r['triangulacion']['triangulados']} de {r['triangulacion']['patrones']}"), ""]
    md += ["## Pares de grupos robustos", "", "| Método | Par | ρ corregida | con tamaño | canary | tipo |", "|---|---|---|---|---|---|"]
    for m in METODOS:
        md += [f"| {m} | {p['x']} ↔ {p['y']} | {f(p['rho'])} | {f(p['tamano'])} | {f(p['canary'])} | {p['tipo']} |" for p in res[m]["grupos"]["robustos"]]
    md += ["", "## Patrones del conjunto reducido", "", "| Método | Par | ρ corregida | con tamaño | canary |", "|---|---|---|---|---|"]
    for m in METODOS:
        md += [f"| {m} | {p['x']} ↔ {p['y']} | {f(p['rho'])} | {f(p['tamano'])} | {f(p['canary'])} |" for p in res[m]["reducido"]["patrones"]]
    md += ["", "## Triangulación de los patrones de variables", "", "| Patrón de variables | Promedio | Primer componente | Más representativa |", "|---|---|---|---|"]
    det = {m: {t["par_id"]: t for t in res[m]["triangulacion"]["detalle"]} for m in METODOS}
    for pid, t in det[METODOS[0]].items():
        celda = lambda m: (lambda x: f"{x['grupo_x']}–{x['grupo_y']}: {x['tipo_par_grupos'] or 'métrica sola'} ({f(x['rho_grupos'])})")(det[m][pid])
        md += [f"| {t['x_nombre']} ↔ {t['y_nombre']} | " + " | ".join(celda(m) for m in METODOS) + " |"]
    md += ["", "## Frente al cruce con el PCA (cruce_dimensiones.py)", ""]
    rob = [r for r in pca_cp if r.get("robusta") == "True"]
    md += [f"- Pares de componentes del PCA: {len(pca_cp)}, robustos {len(rob)}: " +
           ("; ".join(f"{r['x_nombre']} ↔ {r['y_nombre']} ({f(r['rho_corregida'])}, {r['tipo'] or 'no robusto'})" for r in rob) or "ninguno"),
           f"- Patrones del conjunto reducido con el PCA: {sum(1 for r in pca_red if r.get('patron') == 'True')}"]
    (destino / "comparacion.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"  salida: {destino}")



def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dim_a")
    ap.add_argument("dim_b")
    ap.add_argument("--config", help="archivo JSON con la configuración del cruce")
    ap.add_argument("--periodos", choices=("calendario", "epocas", "ambos"), default="calendario",
                    help="períodos de la regla de estabilidad (por defecto, el calendario)")
    ap.add_argument("--grupos", choices=("propio", "pca"), help="cruce con los grupos del clustering, con ese corte")
    ap.add_argument("--asignado", action="store_true", help="con --grupos: saca de cada grupo las métricas del otro lado")
    args = ap.parse_args(argv)
    dim_a, dim_b = (d.strip().capitalize() for d in (args.dim_a, args.dim_b))
    for d in (dim_a, dim_b):
        if d not in corr.DIM_ORDER:
            sys.exit(f"Dimensión desconocida: {d}. Opciones: {', '.join(corr.DIM_ORDER)}")
    if dim_a == dim_b:
        sys.exit("Las dos dimensiones tienen que ser distintas.")
    cfg = mezclar(DEFAULTS, json.loads(Path(args.config).read_text(encoding="utf-8")) if args.config else {})
    if args.grupos:
        if args.periodos != "calendario":
            sys.exit("--grupos se corre con el calendario.")
        cruzar_grupos(dim_a, dim_b, cfg, args.grupos, args.asignado)
        return
    if args.asignado:
        sys.exit("--asignado va con --grupos.")
    base = SALIDA / f"{dim_a.lower()}_{dim_b.lower()}"
    if args.periodos in ("calendario", "ambos"):
        cruzar(dim_a, dim_b, cfg, base, "calendario")
    if args.periodos in ("epocas", "ambos"):
        cruzar(dim_a, dim_b, cfg, base / "epocas", "epocas")
    if args.periodos == "ambos":
        comparar_periodos(base, base / "epocas", base)


if __name__ == "__main__":
    main()
