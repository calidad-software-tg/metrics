#!/usr/bin/env python3
"""PCA y clustering sobre los componentes ya formados, con los controles del análisis principal.

Análisis de segundo nivel del cruce entre dimensiones: en lugar de correlacionar los componentes de a pares
(cruces.py), toma los puntajes por release de los componentes firmes de cada dimensión y les aplica un PCA
(análisis paralelo de Horn, bootstrap de bloques) y un clustering (el de clustering.py). Como dentro de una
dimensión los componentes son casi independientes, cualquier estructura que aparezca viene de relaciones entre
dimensiones. Se corre en cada cruce y con las tres dimensiones juntas (sin repetir el componente de bugs, que
es el mismo en Proceso y en Producto), con estas variantes:

  base                      los componentes tal cual;
  sin tamaño                cada serie sin el efecto del log de activos en interacción (como el enfoque
                            "sin tamaño" del PCA);
  sin escala                sin los componentes de escala (la mitad o más de sus variables son de tamaño);
  sin escala y sin tamaño   las dos cosas.

Para la base y para la versión con los dos controles: réplica en canary (congruencia de Tucker para el PCA,
ARI para el clustering) y estabilidad por período de calendario. Cada metacomponente lista cómo clasifica
el cruce (pares_componentes.csv) los pares de componentes de distintas dimensiones que junta: patrón, escala,
mecánico o no robusto.

Uso (desde la raíz del repo, después de pca.py de las tres dimensiones y de cruces.py de cada cruce):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/pca_clustering_componentes.py \\
        [--persona-proceso analisis/cruces/persona_proceso.json]

Sin la config de Persona–Proceso (está en la rama clara/persona-proceso) corre los otros dos cruces y no las
tres dimensiones juntas. Escribe analisis/salidas/validaciones/pca_clustering_componentes/resumen.txt.
Solo lee la base.
"""
import argparse
import csv
import json
import sys
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import clustering as cl  # noqa: E402
import cruces  # noqa: E402
import pca  # noqa: E402
from preprocesamiento import CALENDARIO, ROOT  # noqa: E402

warnings.filterwarnings("ignore")
SALIDA = ROOT / "analisis" / "salidas" / "validaciones" / "pca_clustering_componentes"
LINEAS = []


def salida(*args):
    texto = " ".join(str(a) for a in args)
    print(texto, flush=True)
    LINEAS.append(texto)


def matriz(comps, serie, enfoque):
    clave = "estable" if serie == "versiones" else "canary_serie"
    comunes = sorted(set.intersection(*(set(c[clave]) for c in comps)))
    filas = {}
    for p in comunes:
        t = TAM[serie].get(p, (None, None))[1]
        if enfoque == "tamano" and t is None:
            continue
        filas[p] = dict(valores=[c[clave][p][1] for c in comps], dur=dur[serie].get(p) or 1.0,
                        anio=comps[0][clave][p][2], version="", fecha="", tamano=t)
    Z, pnums = pca.transformar(filas, enfoque)
    return Z, pnums, filas

def horn_k(Z):
    rng = np.random.default_rng(pca.SEMILLA)
    val, _ = pca.autodescomponer(Z)
    h95, _ = pca.horn(Z, rng)
    return pca.contar_hasta(val > h95), val, h95

def describir(ids, Lr, tipos):
    out = []
    for j in range(Lr.shape[1]):
        fuertes = [(ids[i], round(float(Lr[i, j]), 2)) for i in np.argsort(-np.abs(Lr[:, j])) if abs(Lr[i, j]) >= 0.4]
        dims = sorted({x.split("_")[0] for x, _ in fuertes})
        pares = []
        for (a, _), (b, _) in combinations(fuertes, 2):
            if a.split("_")[0] != b.split("_")[0]:
                t = tipos.get(frozenset((a, b)))
                pares.append(f"{a}↔{b}: {t[0] if t else '?'} ({t[1] if t else ''})")
        out.append(f"      meta{j + 1}{' MEZCLA' if len(dims) > 1 else ''}: {fuertes}" + (f"\n         pares en el cruce: {'; '.join(pares)}" if pares else ""))
    return "\n".join(out)

def clustering(Z, k=None):
    p = Z.shape[1]
    ks = list(range(2, p))
    if not ks:
        return None, None, "pocas columnas"
    D = cl.distancias(Z); L = cl.arbol(D); cut = cl.cortes(L, ks)
    if k is not None:
        return cut.get(k, cl.fcluster(L, k, "maxclust")), None, ""
    sil = {kk: cl.silueta(D, cut[kk]) for kk in ks}
    nula = cl.nula_silueta(Z, ks, np.random.default_rng(pca.SEMILLA))
    sup = [kk for kk in ks if sil[kk] > nula[kk]]
    if not sup:
        return None, None, "ningún corte supera a los datos permutados"
    kk = max(sup, key=lambda x: sil[x] - nula[x])
    est = cl.estabilidad(Z, kk, cut[kk], np.random.default_rng(pca.SEMILLA))
    return cut[kk], kk, f"k={kk} silueta {sil[kk]:+.2f} (nula {nula[kk]:+.2f}) estabilidad {est['mediana']:.2f}"

def grupos(ids, lab):
    g = {}
    for i, l in zip(ids, lab):
        g.setdefault(int(l), []).append(i)
    return list(g.values())

def correr(titulo, comps, tipos):
    ids = [c["id"] for c in comps]
    salida(f"\n######## {titulo}: {', '.join(ids)}")
    resultados = {}
    for nombre, cs, enf in (("base", comps, "crudo"), ("sin tamaño", comps, "tamano"),
                            ("sin escala", [c for c in comps if not c["escala"]], "crudo"),
                            ("sin escala y sin tamaño", [c for c in comps if not c["escala"]], "tamano")):
        ii = [c["id"] for c in cs]
        Z, pnums, filas = matriz(cs, "versiones", enf)
        k, val, h95 = horn_k(Z)
        salida(f"  [{nombre}] {len(ii)} componentes, {Z.shape[0]} releases · Horn retiene {k} · autovalores {np.round(val, 2).tolist()} (umbral {np.round(h95, 2).tolist()})")
        if k >= 1:
            sol = pca.solucion(Z, k)
            boot = pca.bootstrap_bloques(Z, k, sol["Lr"], np.random.default_rng(pca.SEMILLA))
            salida(describir(ii, sol["Lr"], tipos))
            salida(f"      bootstrap {np.round(boot['congruencia_mediana'], 2).tolist()}")
        lab, kk, txt = clustering(Z)
        salida(f"      clustering: {txt}" + (f" → {grupos(ii, lab)}" if lab is not None else ""))
        resultados[nombre] = (cs, enf, Z, pnums, filas, k, lab, kk)
    for nombre in ("base", "sin escala y sin tamaño"):
        replicar(nombre, *resultados[nombre])


def replicar(nombre, cs, enf, Z, pnums, filas, k, lab, kk):
    """Réplica en canary y por período de la solución de PCA (congruencia de Tucker) y del clustering (ARI)."""
    Zc, _, _ = matriz(cs, "versiones_canary", enf)
    anios = np.array([filas[p]["anio"] for p in pnums])
    periodos = [(n, np.where((anios >= a) & (anios <= b))[0]) for n, a, b in CALENDARIO]
    if k >= 1:
        ref = pca.solucion(Z, k)["Lr"]
        Lc, _ = pca.alinear(pca.solucion(Zc, k)["Lr"], ref)
        cong = [f"{n} ({len(idx)}): " + "/".join(f"{pca.tucker(pca.alinear(pca.solucion(Z[idx], k)['Lr'], ref)[0][:, j], ref[:, j]):.2f}" for j in range(k))
                for n, idx in periodos if len(idx) >= 30]
        salida(f"  [{nombre} · PCA] canary ({Zc.shape[0]} ventanas): {[round(pca.tucker(Lc[:, j], ref[:, j]), 2) for j in range(k)]} · por período: {'; '.join(cong)}")
    if lab is not None:
        labc, _, _ = clustering(Zc, kk)
        aris = [f"{n}: {cl.ari(lab, clustering(Z[idx], kk)[0]):.2f}" for n, idx in periodos if len(idx) >= 30]
        salida(f"  [{nombre} · clustering k={kk}] canary ARI {cl.ari(lab, labc) if len(labc) == len(lab) else float('nan'):.2f} · por período: {'; '.join(aris)}")


def main():
    global var_dict, datos, dur, TAM
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--persona-proceso", help="config del cruce Persona–Proceso")
    args = ap.parse_args()
    cfgs = {"Persona–Producto": ("Persona", "Producto", ROOT / "analisis/cruces/persona_producto.json"),
            "Proceso–Producto": ("Proceso", "Producto", ROOT / "analisis/cruces/proceso_producto_asignado.json")}
    if args.persona_proceso:
        cfgs["Persona–Proceso"] = ("Persona", "Proceso", Path(args.persona_proceso))
    var_dict, datos = pca.cargar_datos()
    dur = {s: {} for s in ("versiones", "versiones_canary")}
    for v, d in datos.items():
        if not v.startswith("__"):
            for s in dur:
                for p, t in d.get(s, {}).items():
                    if t[0] is not None:
                        dur[s].setdefault(p, t[0])
    TAM = {s: datos["activos_interaccion_conteo"][s] for s in dur}
    todos, tipos_todos = {}, {}
    for titulo, (a, b, cfgp) in cfgs.items():
        cfg = cruces.mezclar(cruces.DEFAULTS, json.loads(Path(cfgp).read_text(encoding="utf-8")))
        comps = [c for d in (a, b) for c in cruces.componentes(d, cfg, dur)]
        for c in comps:
            c["escala"] = cruces.es_escala_cp(c, cfg["carga_minima"], var_dict, cfg)
            todos.setdefault(c["id"], c)
        carpeta = cruces.SALIDA / f"{a.lower()}_{b.lower()}"
        if not (carpeta / "pares_componentes.csv").exists():
            sys.exit(f"Falta {carpeta / 'pares_componentes.csv'}: corré antes cruces.py {a} {b}.")
        tipos = {frozenset((r["x_id"], r["y_id"])): (r["tipo"] or "no robusto", f"{float(r['rho_corregida']):+.2f}")
                 for r in csv.DictReader(open(carpeta / "pares_componentes.csv", encoding="utf-8"))}
        tipos_todos.update(tipos)
        salida(f"\nescala en {titulo}:", [c["id"] for c in comps if c["escala"]])
        correr(titulo, comps, tipos)
    if len(cfgs) == 3:
        # el componente de bugs de Proceso (CFDR y NUB) es el mismo que el de Producto
        correr("Las tres dimensiones", [c for i, c in todos.items() if i != "proceso_cp1"], tipos_todos)
    SALIDA.mkdir(parents=True, exist_ok=True)
    (SALIDA / "resumen.txt").write_text("\n".join(LINEAS) + "\n", encoding="utf-8")
    print("salida:", SALIDA / "resumen.txt")


if __name__ == "__main__":
    main()
