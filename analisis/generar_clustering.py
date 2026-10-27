#!/usr/bin/env python3
"""
analisis/generar_clustering.py

Clustering jerárquico de las métricas de una dimensión, comparado con el PCA.

Uso:
    python3 analisis/generar_clustering.py Producto

Corre después de generar_pca.py, porque toma del pca_<dim>.json qué variables y qué releases
usó cada combinación (conjunto, serie y enfoque) y reconstruye la misma matriz con las mismas
funciones (tabla y transformar). El clustering se calcula por separado: no usa los componentes
ni las cargas, solo los datos de entrada. Para cada combinación:

  - distancia entre métricas: 1 − |correlación| sobre los rangos ya transformados;
  - árbol con enlace promedio (agrupamiento jerárquico);
  - cantidad de grupos con un criterio propio: el índice de silueta de cada corte (2 a 10 grupos)
    comparado con el percentil 95 de la silueta de datos permutados al azar (cada variable se
    desordena por separado, como en el análisis paralelo de Horn); se elige el corte que más
    supera al azar. Si ninguno lo supera, no hay estructura de grupos;
  - estabilidad: el mismo bootstrap de bloques de releases consecutivos que el PCA (mismo largo de
    bloque y semilla), medida con el índice de Rand ajustado (ARI) frente a la solución original;
  - réplica: el mismo corte en la serie canary, con las variables comunes;
  - comparación con el PCA, en el corte propio y en la misma cantidad de grupos que componentes
    retiene Horn: ARI frente al componente dominante de cada variable (|carga| ≥ 0,4) y, para cada
    grupo, el componente con el que comparte más variables.

Salidas (analisis/salidas/pca/):
  clustering_<dim>.json  (lo lee reporte_pca.py y generar_informe.py)
  clustering_<dim>_grupos.csv
"""
import argparse
import csv
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import dendrogram, fcluster, linkage
from scipy.spatial.distance import squareform

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar_pca as gp  # noqa: E402

SALIDA = gp.SALIDA
K_MAX = 10
N_PERM = 200          # datos permutados para la nula de la silueta
N_BOOT = 200          # remuestreos de bloques para la estabilidad
CARGA_MINIMA = 0.4
SERIE_DB = dict(gp.SERIES)


def ari(a, b):
    from sklearn.metrics import adjusted_rand_score
    return float(adjusted_rand_score(a, b))


def silueta(D, lab):
    from sklearn.metrics import silhouette_score
    return float(silhouette_score(D, lab, metric="precomputed")) if 1 < len(set(lab)) < len(lab) else float("nan")


def distancias(Z):
    R = np.nan_to_num(np.corrcoef(Z, rowvar=False))
    D = 1 - np.abs(R)
    np.fill_diagonal(D, 0)
    return np.clip(D, 0, None)


def arbol(D):
    return linkage(squareform(D, checks=False), "average")


def cortes(L, ks):
    return {k: fcluster(L, k, "maxclust") for k in ks}


def nula_silueta(Z, ks, rng):
    sil = {k: [] for k in ks}
    for _ in range(N_PERM):
        Zp = np.column_stack([rng.permutation(Z[:, j]) for j in range(Z.shape[1])])
        Dp = distancias(Zp)
        for k, lab in cortes(arbol(Dp), ks).items():
            sil[k].append(silueta(Dp, lab))
    return {k: float(np.nanpercentile(v, 95)) for k, v in sil.items()}


def estabilidad(Z, k, lab_ref, rng):
    """ARI entre el corte original y el de cada remuestreo de bloques (igual que el bootstrap del PCA)."""
    n = Z.shape[0]
    largo = max(5, int(round(math.sqrt(n))))
    inicios = np.arange(0, n - largo + 1)
    out = []
    for _ in range(N_BOOT):
        idx = np.concatenate([np.arange(s, s + largo) for s in rng.choice(inicios, int(math.ceil(n / largo)))])[:n]
        lab = fcluster(arbol(distancias(Z[idx])), k, "maxclust")
        out.append(ari(lab_ref, lab))
    return dict(mediana=float(np.median(out)), p05=float(np.percentile(out, 5)), largo_bloque=largo)


def referencia_pca(R):
    """Componente dominante de cada variable en el PCA (varimax); None si ninguna carga llega a 0,4."""
    ref = []
    for fila in R["varimax"]:
        j = int(np.argmax(np.abs(fila)))
        ref.append(j + 1 if abs(fila[j]) >= CARGA_MINIMA else None)
    return ref


def etiquetas_ref(ref):
    # las variables sin componente cuentan como grupos de una sola variable
    return [c if c is not None else -1 - i for i, c in enumerate(ref)]


def correspondencia(variables, lab, ref, R):
    """Para cada grupo, el componente con el que comparte más variables, y al revés."""
    grupos = {}
    for v, g in zip(variables, lab):
        grupos.setdefault(int(g), []).append(v)
    comp = {}
    for v, c in zip(variables, ref):
        if c is not None:
            comp.setdefault(c, []).append(v)
    filas = []
    for g, vs in sorted(grupos.items(), key=lambda x: -len(x[1])):
        cuenta = {}
        for v in vs:
            c = ref[variables.index(v)]
            cuenta[c] = cuenta.get(c, 0) + 1
        mejor = max((c for c in cuenta if c is not None), key=lambda c: cuenta[c], default=None)
        union = set(vs) | set(comp.get(mejor, []))
        filas.append(dict(grupo=g, variables=vs, componente=mejor,
                          compartidas=sorted(set(vs) & set(comp.get(mejor, []))),
                          jaccard=round(len(set(vs) & set(comp.get(mejor, []))) / len(union), 3) if mejor else 0.0,
                          sin_componente=[v for v in vs if ref[variables.index(v)] is None]))
    por_cp = []
    for c in range(1, R["k"] + 1):
        vs = comp.get(c, [])
        destino = {}
        for v in vs:
            g = int(lab[variables.index(v)])
            destino[g] = destino.get(g, 0) + 1
        por_cp.append(dict(componente=c, variables=vs, grupos=destino,
                           completo=len(destino) == 1 and bool(vs)))
    return filas, por_cp


def analizar(clave, R, datos, rng):
    conj, serie, enf = clave.split("|")
    variables = R["variables"]
    filas, _ = gp.tabla(variables, datos, SERIE_DB[serie])
    Z, pnums = gp.transformar(filas, enf)
    if Z.shape[0] != R["n"]:
        print(f"  {clave}: la matriz no coincide con la del PCA ({Z.shape[0]} releases frente a {R['n']})")
        return None, None
    p = Z.shape[1]
    ks = list(range(2, min(K_MAX, p - 1) + 1))
    D = distancias(Z)
    L = arbol(D)
    cut = cortes(L, ks)
    sil = {k: silueta(D, cut[k]) for k in ks}
    nula = nula_silueta(Z, ks, rng)
    exceso = {k: sil[k] - nula[k] for k in ks}
    supera = [k for k in ks if sil[k] > nula[k]]
    k_propio = max(supera, key=lambda k: exceso[k]) if supera else None
    k_pca = R["k"]
    ref = referencia_pca(R)
    soluciones = {}
    for nombre, k in (("propio", k_propio), ("pca", k_pca)):
        if k is None or k < 2 or k > p - 1:
            continue
        lab = cut[k] if k in cut else fcluster(L, k, "maxclust")
        grupos, por_cp = correspondencia(variables, lab, ref, R)
        soluciones[nombre] = dict(k=k, etiquetas=[int(x) for x in lab], silueta=sil.get(k), nula_p95=nula.get(k),
                                  ari_pca=ari(etiquetas_ref(ref), lab), estabilidad=estabilidad(Z, k, lab, rng),
                                  grupos=grupos, por_componente=por_cp)
    dn = dendrogram(L, no_plot=True, labels=list(range(p)))
    return dict(n=int(Z.shape[0]), p=p, variables=variables, ks=ks,
                silueta={str(k): sil[k] for k in ks}, nula_p95={str(k): nula[k] for k in ks},
                k_propio=k_propio, k_pca=k_pca, referencia_pca=ref, soluciones=soluciones,
                dendrograma=dict(icoord=dn["icoord"], dcoord=dn["dcoord"], hojas=[int(i) for i in dn["leaves"]]),
                Z=Z), L


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dimension", help="Persona, Proceso o Producto")
    ap.add_argument("--sin-reporte", action="store_true", help="no regenera reporte_pca_<dim>.html")
    args = ap.parse_args()
    dim = args.dimension.strip().capitalize()
    entrada = SALIDA / f"pca_{dim.lower()}.json"
    if not entrada.exists():
        sys.exit(f"No existe {entrada}. Corré primero: python3 analisis/generar_pca.py {dim}")
    pca = json.loads(entrada.read_text(encoding="utf-8"))
    warnings.filterwarnings("ignore")
    rng = np.random.default_rng(gp.SEMILLA)
    print(f"=== generar_clustering.py · {dim} ===", flush=True)
    _, datos = gp.cargar_datos()

    res = {}
    for clave, R in pca["resultados"].items():
        out, _ = analizar(clave, R, datos, rng)
        if out is None:
            continue
        res[clave] = out
        ps, pp = out["soluciones"].get("propio"), out["soluciones"].get("pca")
        linea = f"  {clave:28s} k propio {out['k_propio'] or '—'}"
        linea += (f" (silueta {ps['silueta']:.2f}, azar p95 {ps['nula_p95']:.2f}, estabilidad {ps['estabilidad']['mediana']:.2f}, "
                  f"ARI con PCA {ps['ari_pca']:.2f})" if ps else " (ningún corte supera al azar)")
        if pp:
            linea += f" · con {pp['k']} grupos, como el PCA: ARI con PCA {pp['ari_pca']:.2f}"
        print(linea, flush=True)

    # réplica en canary: el mismo corte de la serie estable, sobre las variables comunes
    for clave, out in res.items():
        conj, serie, enf = clave.split("|")
        otro = res.get(f"{conj}|canary|{enf}")
        if serie != "estable" or otro is None:
            continue
        comunes = [v for v in out["variables"] if v in otro["variables"]]
        ie = [out["variables"].index(v) for v in comunes]
        ic = [otro["variables"].index(v) for v in comunes]
        Lc = arbol(distancias(otro["Z"][:, ic]))
        for nombre, sol in out["soluciones"].items():
            lab_c = fcluster(Lc, sol["k"], "maxclust")
            sol["ari_canary"] = ari([sol["etiquetas"][i] for i in ie], lab_c)

    for out in res.values():
        out.pop("Z")
    js = {"dimension": dim, "parametros": dict(k_max=K_MAX, permutaciones=N_PERM, bootstrap=N_BOOT,
                                                carga_minima=CARGA_MINIMA, semilla=gp.SEMILLA,
                                                distancia="1 − |correlación|", enlace="promedio"),
          "resultados": res}
    base = f"clustering_{dim.lower()}"
    (SALIDA / f"{base}.json").write_text(json.dumps(js, ensure_ascii=False), encoding="utf-8")
    with open(SALIDA / f"{base}_grupos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["conjunto", "serie", "enfoque", "solucion", "k", "grupo", "variable_id", "componente_pca_dominante"])
        for clave, out in res.items():
            conj, serie, enf = clave.split("|")
            for nombre, sol in out["soluciones"].items():
                for v, g, c in zip(out["variables"], sol["etiquetas"], out["referencia_pca"]):
                    w.writerow([conj, serie, enf, nombre, sol["k"], g, v, c if c is not None else ""])
    print(f"Salidas en {SALIDA}/{base}.json y {base}_grupos.csv")
    if args.sin_reporte:
        return
    import reporte_pca
    destino = reporte_pca.escribir(dim)
    print(f"Reporte: {destino} ({destino.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
