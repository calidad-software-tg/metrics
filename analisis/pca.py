#!/usr/bin/env python3
"""
analisis/pca.py

Análisis de componentes principales (PCA) de las variables de una dimensión.

Uso:
    python3 analisis/pca.py Producto
    python3 analisis/pca.py Persona --k 3      # fuerza 3 componentes

Usa los datos y la transformación de preprocesamiento.py (los mismos que las correlaciones:
diccionario, lectura de la base y del CSV de persona agregada, releases excluidos, spline de
tendencia y duración). Las funciones de PCA (analizar, solucion, tucker, ...) las usa también
cruces.py para el PCA conjunto de dos dimensiones. Calcula el PCA para cada combinación de:

  conjunto : variables a nivel producto, y todas las variables de la dimensión
  serie    : releases estables y canary (sin backports)
  enfoque  : crudo     (rangos de los valores)
             ajustado  (rangos sin tendencia de tiempo ni duración, como la ρ corregida)
             tamano    (ajustado y además sin el tamaño: log de activos de interacción)

Para cada una: autovalores, criterios para elegir cuántos componentes (Kaiser,
codo del scree, varianza acumulada y análisis paralelo de Horn), cargas sin rotar y
con rotación varimax, comunalidades, puntajes por release y solidez por bootstrap
de bloques. Compara las soluciones entre enfoques y series con la congruencia de Tucker.

Salidas (analisis/salidas/pca/):
  pca_<dim>_autovalores.csv, pca_<dim>_cargas.csv, pca_<dim>_puntajes.csv,
  pca_<dim>_comparacion.csv y pca_<dim>.json, y el reporte
  analisis/salidas/reportes/reporte_pca_<dim>.html (reporte_pca.py).
"""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import rankdata

sys.path.insert(0, str(Path(__file__).resolve().parent))
from preprocesamiento import (  # noqa: E402,F401  (se reexportan para los scripts que importan este módulo)
    ROOT, DIM_ORDER, SERIES, VARIABLE_TAMANO, VARIANTES, MIN_COBERTURA, SEMILLA,
    cargar_datos, es_backport, tabla, transformar)

SALIDA = ROOT / "analisis" / "salidas" / "pca"

ENFOQUES = ["crudo", "ajustado", "tamano"]
NOMBRE_ENFOQUE = {"crudo": "Crudo", "ajustado": "Ajustado", "tamano": "Ajustado y sin tamaño"}
NOMBRE_SERIE = {"estable": "Estables", "canary": "Canary"}

N_PERMUTACIONES = 500     # análisis paralelo de Horn
N_BOOTSTRAP = 500         # bootstrap de bloques
PERCENTIL_HORN = 95
UMBRALES_VARIANZA = (0.70, 0.80)


# ── PCA ──────────────────────────────────────────────────────────────────────

def autodescomponer(Z):
    C = np.corrcoef(Z, rowvar=False)
    C = np.nan_to_num(C, nan=0.0)
    np.fill_diagonal(C, 1.0)
    val, vec = np.linalg.eigh(C)
    orden = np.argsort(val)[::-1]
    val, vec = np.clip(val[orden], 0, None), vec[:, orden]
    return val, vec


def fijar_signos(L):
    """Cada componente con su carga de mayor valor absoluto positiva (el signo es arbitrario)."""
    s = np.sign(L[np.abs(L).argmax(axis=0), np.arange(L.shape[1])])
    s[s == 0] = 1
    return L * s, s


def varimax(L, normalizar=True, iteraciones=500, tol=1e-8):
    """Rotación varimax (con normalización de Kaiser). Devuelve cargas rotadas y matriz T."""
    p, k = L.shape
    if k < 2:
        return L.copy(), np.eye(k)
    h = np.sqrt((L ** 2).sum(axis=1)) if normalizar else np.ones(p)
    h[h == 0] = 1
    A = L / h[:, None]
    T = np.eye(k)
    d = 0
    for _ in range(iteraciones):
        B = A @ T
        u, s, vt = np.linalg.svd(A.T @ (B ** 3 - B @ np.diag((B ** 2).sum(axis=0)) / p))
        T = u @ vt
        d_nuevo = s.sum()
        if d_nuevo < d * (1 + tol):
            break
        d = d_nuevo
    return (A @ T) * h[:, None], T


def horn(Z, rng, n_perm=N_PERMUTACIONES, percentil=PERCENTIL_HORN):
    """Análisis paralelo: autovalores de datos con cada columna permutada al azar."""
    n, p = Z.shape
    sim = np.empty((n_perm, p))
    for b in range(n_perm):
        P = np.column_stack([rng.permutation(Z[:, j]) for j in range(p)])
        sim[b] = np.sort(np.linalg.eigvalsh(np.corrcoef(P, rowvar=False)))[::-1]
    return np.percentile(sim, percentil, axis=0), sim.mean(axis=0)


def contar_hasta(condicion):
    k = 0
    for c in condicion:
        if not c:
            break
        k += 1
    return k


def codo(val):
    """Codo del scree: punto más alejado de la recta entre el primer y el último autovalor."""
    p = len(val)
    if p < 3:
        return 1
    x = np.arange(1, p + 1, dtype=float)
    x0, y0, x1, y1 = x[0], val[0], x[-1], val[-1]
    dist = np.abs((y1 - y0) * x - (x1 - x0) * val + x1 * y0 - y1 * x0) / math.hypot(y1 - y0, x1 - x0)
    return int(dist.argmax()) + 1


def tucker(a, b):
    den = math.sqrt(float((a ** 2).sum() * (b ** 2).sum()))
    return float((a * b).sum() / den) if den else float("nan")


def alinear(L, ref):
    """Reordena y cambia el signo de los componentes de L para que coincidan con ref."""
    k = min(L.shape[1], ref.shape[1])
    M = np.array([[abs(tucker(L[:, i], ref[:, j])) for j in range(ref.shape[1])] for i in range(L.shape[1])])
    fi, co = linear_sum_assignment(-M)
    out = np.full((L.shape[0], ref.shape[1]), np.nan)
    for i, j in zip(fi, co):
        col = L[:, i]
        out[:, j] = col if tucker(col, ref[:, j]) >= 0 else -col
    return out, k


def solucion(Z, k):
    """Cargas sin rotar y varimax, y puntajes varimax estandarizados, con k componentes."""
    val, vec = autodescomponer(Z)
    k = max(1, min(k, Z.shape[1]))
    L = vec[:, :k] * np.sqrt(np.maximum(val[:k], 1e-12))
    L, s = fijar_signos(L)
    vec_k = vec[:, :k] * s
    Lr, T = varimax(L)
    Lr, s2 = fijar_signos(Lr)
    T = T * s2
    F = Z @ vec_k / np.sqrt(np.maximum(val[:k], 1e-12))      # puntajes sin rotar (varianza 1)
    Fr = F @ T
    # ordenar los rotados por varianza explicada
    orden = np.argsort((Lr ** 2).sum(axis=0))[::-1]
    return dict(val=val, L=L, Lr=Lr[:, orden], Fr=Fr[:, orden])


def bootstrap_bloques(Z, k, ref_Lr, rng, n_boot=N_BOOTSTRAP):
    """Bootstrap de bloques móviles sobre los releases ordenados en el tiempo."""
    n, p = Z.shape
    largo = max(5, int(round(math.sqrt(n))))
    inicios = np.arange(0, n - largo + 1)
    cargas, congr, autoval, dominante = [], [], [], []
    for _ in range(n_boot):
        idx = np.concatenate([np.arange(s, s + largo) for s in rng.choice(inicios, int(math.ceil(n / largo)))])[:n]
        sol = solucion(Z[idx], k)
        Lb, _ = alinear(sol["Lr"], ref_Lr)
        cargas.append(Lb)
        congr.append([tucker(Lb[:, j], ref_Lr[:, j]) for j in range(ref_Lr.shape[1])])
        autoval.append(sol["val"])
        dominante.append(np.nanargmax(np.abs(Lb), axis=1))
    cargas, congr, autoval, dominante = map(np.array, (cargas, congr, autoval, dominante))
    dom_ref = np.abs(ref_Lr).argmax(axis=1)
    return dict(
        largo_bloque=largo,
        cargas_p025=np.nanpercentile(cargas, 2.5, axis=0), cargas_p975=np.nanpercentile(cargas, 97.5, axis=0),
        congruencia_mediana=np.nanmedian(congr, axis=0), congruencia_p05=np.nanpercentile(congr, 5, axis=0),
        autoval_p025=np.percentile(autoval, 2.5, axis=0), autoval_p975=np.percentile(autoval, 97.5, axis=0),
        dominante_estable=(dominante == dom_ref).mean(axis=0),
    )


def analizar(variables, filas, enfoque, k_forzado, rng):
    Z, pnums = transformar(filas, enfoque)
    n, p = Z.shape
    if n < 3 * p or n < 30:
        return None
    val, _ = autodescomponer(Z)
    h95, hmed = horn(Z, rng)
    var = val / p
    acum = np.cumsum(var)
    criterios = {
        "kaiser": int((val > 1).sum()),
        "codo": codo(val),
        "varianza_70": int(np.searchsorted(acum, UMBRALES_VARIANZA[0]) + 1),
        "varianza_80": int(np.searchsorted(acum, UMBRALES_VARIANZA[1]) + 1),
        "horn": contar_hasta(val > h95),
    }
    k = k_forzado or max(1, criterios["horn"])
    sol = solucion(Z, k)
    boot = bootstrap_bloques(Z, k, sol["Lr"], rng)
    return dict(Z=Z, pnums=pnums, n=n, p=p, val=val, var=var, acum=acum, horn95=h95, horn_media=hmed,
                criterios=criterios, k=k, sol=sol, boot=boot)


# ── salida ───────────────────────────────────────────────────────────────────

def r(x, d=4):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), d)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dimension", help="Persona, Proceso o Producto")
    ap.add_argument("--k", type=int, default=None, help="cantidad de componentes (por defecto, la del análisis paralelo)")
    ap.add_argument("--con-variantes", action="store_true",
                    help=f"incluye las versiones alternativas de una métrica ({', '.join(sorted(VARIANTES))})")
    args = ap.parse_args()
    dim = args.dimension.strip().capitalize()
    if dim not in DIM_ORDER:
        sys.exit(f"Dimensión desconocida: {args.dimension}. Opciones: {', '.join(DIM_ORDER)}")
    rng = np.random.default_rng(SEMILLA)

    print(f"=== pca.py · {dim} ===", flush=True)
    var_dict, datos = cargar_datos()
    de_dim = sorted((v for v, row in var_dict.items() if dim in row["dims_texto"].split("+")
                     and (args.con_variantes or row["metrica_id"] not in VARIANTES)),
                    key=lambda v: (var_dict[v]["nivel"] != "producto", v))
    conjuntos = {
        "producto": [v for v in de_dim if var_dict[v]["nivel"] == "producto"],
        "todas": de_dim,
    }
    conjuntos = {c: vs for c, vs in conjuntos.items() if len(vs) >= 3}
    if conjuntos.get("producto") == conjuntos.get("todas"):
        conjuntos.pop("todas", None)

    resultados = {}
    for conj, variables in conjuntos.items():
        for serie, serie_db in SERIES:
            # variables con dato en al menos MIN_COBERTURA de las ventanas de la serie
            ventanas = set().union(*(set(datos[v][serie_db]) for v in variables))
            cobertura = {v: sum(1 for t in datos[v][serie_db].values() if t[1] is not None) / max(1, len(ventanas))
                         for v in variables}
            vars_serie = [v for v in variables if cobertura[v] >= MIN_COBERTURA]
            excluidas = [v for v in variables if v not in vars_serie]
            if excluidas:
                print(f"  {conj}/{serie}: sin datos suficientes, se excluyen "
                      + ", ".join(f"{v} ({cobertura[v]:.0%})" for v in excluidas))
            for enf in ENFOQUES:
                # sin tamaño: además se excluyen las variables de la familia tamaño (son el control)
                vars_enf = [v for v in vars_serie if not (enf == "tamano" and
                            (var_dict[v].get("familia") == "tamano" or v == VARIABLE_TAMANO))]
                if len(vars_enf) < 3:
                    print(f"  {conj}/{serie}/{enf}: menos de 3 variables")
                    continue
                filas, n_bp = tabla(vars_enf, datos, serie_db)
                # variables constantes en los releases elegidos (ej. Wiki Presence vale 0 en todas
                # las ventanas desde 2020): no aportan al PCA y rompen la matriz de correlaciones
                constantes = [v for j, v in enumerate(vars_enf)
                              if len({f["valores"][j] for f in filas.values()}) < 2]
                if constantes:
                    print(f"  {conj}/{serie}/{enf}: constantes en estos releases, se excluyen {', '.join(constantes)}")
                    excluidas = excluidas + [v for v in constantes if v not in excluidas]
                    vars_enf = [v for v in vars_enf if v not in constantes]
                    filas, n_bp = tabla(vars_enf, datos, serie_db)
                res = analizar(vars_enf, filas, enf, args.k, rng) if len(filas) >= 30 else None
                if res is None:
                    print(f"  {conj}/{serie}/{enf}: pocos releases ({len(filas)})")
                    continue
                res.update(variables=vars_enf, filas=filas, backports=n_bp,
                           excluidas=excluidas + [v for v in vars_serie if v not in vars_enf and v not in excluidas])
                resultados[(conj, serie, enf)] = res
                c = res["criterios"]
                print(f"  {conj:8s} {serie:7s} {enf:8s} n={res['n']:5d}  k={res['k']}  "
                      f"(Kaiser {c['kaiser']}, codo {c['codo']}, 70% {c['varianza_70']}, "
                      f"80% {c['varianza_80']}, Horn {c['horn']})  "
                      f"congruencia bootstrap {np.round(res['boot']['congruencia_mediana'], 2).tolist()}", flush=True)

    # ── comparación con la referencia (estable, ajustado) usando su k ──
    comparacion = []
    for conj in conjuntos:
        ref = resultados.get((conj, "estable", "ajustado"))
        if not ref:
            continue
        for (cj, serie, enf), res in resultados.items():
            if cj != conj:
                continue
            # se compara sobre las variables que tienen las dos soluciones
            comunes = [v for v in res["variables"] if v in ref["variables"]]
            if len(comunes) < 3:
                continue
            i_res = [res["variables"].index(v) for v in comunes]
            i_ref = [ref["variables"].index(v) for v in comunes]
            sol_k = solucion(res["Z"], ref["k"])
            L_ref = ref["sol"]["Lr"][i_ref]
            Lal, _ = alinear(sol_k["Lr"][i_res], L_ref)
            for j in range(ref["k"]):
                comparacion.append(dict(conjunto=conj, serie=serie, enfoque=enf, componente=j + 1,
                                        k_propio=res["k"], k_comparado=ref["k"], variables=comunes,
                                        congruencia=r(tucker(Lal[:, j], L_ref[:, j]), 3),
                                        cargas=[r(x, 3) for x in Lal[:, j]]))

    SALIDA.mkdir(parents=True, exist_ok=True)
    base = f"pca_{dim.lower()}"
    nombre = {v: var_dict[v]["nombre_legible"] for v in de_dim}

    with open(SALIDA / f"{base}_autovalores.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["conjunto", "serie", "enfoque", "componente", "autovalor", "varianza", "varianza_acumulada",
                    "horn_p95", "supera_kaiser", "supera_horn", "autovalor_boot_p025", "autovalor_boot_p975"])
        for (conj, serie, enf), res in resultados.items():
            for j in range(res["p"]):
                w.writerow([conj, serie, enf, j + 1, r(res["val"][j]), r(res["var"][j]), r(res["acum"][j]),
                            r(res["horn95"][j]), res["val"][j] > 1, res["val"][j] > res["horn95"][j],
                            r(res["boot"]["autoval_p025"][j]), r(res["boot"]["autoval_p975"][j])])

    with open(SALIDA / f"{base}_cargas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["conjunto", "serie", "enfoque", "variable_id", "variable", "componente", "carga_sin_rotar",
                    "carga_varimax", "boot_p025", "boot_p975", "comunalidad", "componente_dominante_estable"])
        for (conj, serie, enf), res in resultados.items():
            L, Lr, b = res["sol"]["L"], res["sol"]["Lr"], res["boot"]
            com = (Lr ** 2).sum(axis=1)
            for i, v in enumerate(res["variables"]):
                for j in range(res["k"]):
                    w.writerow([conj, serie, enf, v, nombre[v], j + 1, r(L[i, j]), r(Lr[i, j]),
                                r(b["cargas_p025"][i, j]), r(b["cargas_p975"][i, j]), r(com[i]),
                                r(b["dominante_estable"][i], 3)])

    with open(SALIDA / f"{base}_puntajes.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        kmax = max(res["k"] for res in resultados.values())
        w.writerow(["conjunto", "serie", "enfoque", "periodo_num", "version", "fecha_hora", "anio"]
                   + [f"CP{j + 1}" for j in range(kmax)])
        for (conj, serie, enf), res in resultados.items():
            for i, pnum in enumerate(res["pnums"]):
                fl = res["filas"][pnum]
                w.writerow([conj, serie, enf, pnum, fl["version"], fl["fecha"], fl["anio"]]
                           + [r(x) for x in res["sol"]["Fr"][i]] + [""] * (kmax - res["k"]))

    with open(SALIDA / f"{base}_comparacion.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["conjunto", "serie", "enfoque", "componente", "k_propio", "k_comparado", "congruencia_con_estable_ajustado"])
        for c in comparacion:
            w.writerow([c["conjunto"], c["serie"], c["enfoque"], c["componente"], c["k_propio"], c["k_comparado"],
                        c["congruencia"]])

    # JSON para el reporte
    js = {"dimension": dim, "conjuntos": {c: vs for c, vs in conjuntos.items()},
          "nombres": nombre, "niveles": {v: var_dict[v]["nivel"] for v in de_dim},
          "series": NOMBRE_SERIE, "enfoques": NOMBRE_ENFOQUE,
          "parametros": dict(permutaciones=N_PERMUTACIONES, bootstrap=N_BOOTSTRAP, percentil_horn=PERCENTIL_HORN,
                             semilla=SEMILLA, k_forzado=args.k),
          "resultados": {}, "comparacion": comparacion}
    for (conj, serie, enf), res in resultados.items():
        b = res["boot"]
        fechas = [res["filas"][p]["fecha"] for p in res["pnums"]]
        js["resultados"][f"{conj}|{serie}|{enf}"] = dict(
            n=res["n"], p=res["p"], k=res["k"], backports=res["backports"],
            variables=res["variables"], excluidas=res["excluidas"],
            desde=min(fechas)[:8], hasta=max(fechas)[:8],
            autovalores=[r(x) for x in res["val"]], varianza=[r(x) for x in res["var"]],
            acumulada=[r(x) for x in res["acum"]], horn95=[r(x) for x in res["horn95"]],
            horn_media=[r(x) for x in res["horn_media"]], criterios=res["criterios"],
            cargas=[[r(x, 3) for x in fila] for fila in res["sol"]["L"]],
            varimax=[[r(x, 3) for x in fila] for fila in res["sol"]["Lr"]],
            boot=dict(largo_bloque=b["largo_bloque"],
                      p025=[[r(x, 3) for x in fila] for fila in b["cargas_p025"]],
                      p975=[[r(x, 3) for x in fila] for fila in b["cargas_p975"]],
                      congruencia_mediana=[r(x, 3) for x in b["congruencia_mediana"]],
                      congruencia_p05=[r(x, 3) for x in b["congruencia_p05"]],
                      autoval_p025=[r(x, 3) for x in b["autoval_p025"]],
                      autoval_p975=[r(x, 3) for x in b["autoval_p975"]],
                      dominante_estable=[r(x, 3) for x in b["dominante_estable"]]),
            puntajes=[[int(p), res["filas"][p]["version"], res["filas"][p]["fecha"][:8]]
                      + [r(x, 3) for x in res["sol"]["Fr"][i]] for i, p in enumerate(res["pnums"])],
        )
    (SALIDA / f"{base}.json").write_text(json.dumps(js, ensure_ascii=False), encoding="utf-8")
    print(f"Salidas en {SALIDA}/{base}_*.csv y {base}.json")
    import reporte_pca
    destino = reporte_pca.escribir(dim)
    print(f"Reporte: {destino} ({destino.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
