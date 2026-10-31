#!/usr/bin/env python3
"""
analisis/pesos_catalogo.py

Pertenencia ponderada: cada variable cuenta para las dimensiones que le asigna el catálogo (diccionario de
variables), repartida en partes iguales. EXPRev, de Persona y Proceso, cuenta mitad para cada una; MTTR, de
Proceso y Producto, mitad para cada una; una variable de una sola dimensión cuenta entera.

Los cruces y el análisis de tres dimensiones comparan una dimensión con otra, y ahí cada variable tiene que
estar en un solo lado (si estuviera en los dos se compararía consigo misma). Los pesos sirven donde no hay
lados:

  1. Patrones entre dimensiones. Para cada patrón de los cruces, de qué dimensiones son sus dos variables
     según el catálogo. Si las dos comparten una dimensión del catálogo (por ejemplo, NC del 10 % más activo,
     de Persona y Proceso, con NCI p90, de Proceso), el patrón depende de la asignación: con otra asignación
     sería una relación dentro de esa dimensión.
  2. Patrones de tres dimensiones sin asignar. PCA y clustering conjunto de todas las variables de las tres
     dimensiones, sin decir de qué lado es cada una; después, la composición de cada componente según el
     catálogo (carga al cuadrado de cada variable que lo define, repartida según sus dimensiones). Un
     componente es tridimensional si cada dimensión aporta al menos MINIMO_DIMENSION. Se comparan con la
     composición que daría la asignación única de los cruces.
  3. El factor común del análisis de tres dimensiones (tres_dimensiones.py), con la misma composición.

Uso (después de cruces.py y tres_dimensiones.py):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/pesos_catalogo.py

Salidas en analisis/salidas/pesos_catalogo/: resumen.md, patrones_cruces.csv, componentes_conjuntos.csv.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import correlaciones as corr  # noqa: E402
import cruces  # noqa: E402
import pca  # noqa: E402

SALIDA = corr.ROOT / "analisis" / "salidas" / "pesos_catalogo"
DIMS = ("Persona", "Proceso", "Producto")
CRUCES = ("persona_proceso", "persona_producto", "proceso_producto")
MINIMO_DIMENSION = 0.20
# asignación única de las métricas compartidas (la de los cruces y de tres_dimensiones.py)
LADO = {"exprev": "Persona", "rexprev": "Persona", "cdiv": "Persona", "nc": "Persona", "sc": "Persona",
        "dev_exp": "Persona", "mttr": "Proceso", "noi": "Proceso", "cfdr": "Producto", "nub": "Producto",
        "rc": "Producto", "wp": "Producto", "nob_42": "Producto", "anmcc": "Producto"}


def pesos(r):
    """Pertenencia de una variable a cada dimensión según el catálogo (suma 1)."""
    f = [int(r["dim_persona"] or 0), int(r["dim_proceso"] or 0), int(r["dim_producto"] or 0)]
    if not any(f):
        f = [1, 0, 0]
    return np.array(f, dtype=float) / sum(f)


def lado(v, r):
    """Dimensión a la que la asignación única manda la variable."""
    w = pesos(r)
    if (w > 0).sum() == 1:
        return DIMS[int(np.argmax(w))]
    m = corr.metrica_base(r["metrica_id"])
    if m in ("le", "cd"):
        return "Persona" if r["nivel"] != "producto" else "Producto"
    return LADO.get(m, DIMS[int(np.argmax(w))])


def composicion(cargas, var_dict, ponderada=True):
    """Parte de cada dimensión en un componente: carga al cuadrado de cada variable que lo define, repartida
    según el catálogo (ponderada) o entera al lado asignado."""
    tot = np.zeros(3)
    for v, x in cargas:
        w = pesos(var_dict[v]) if ponderada else np.eye(3)[DIMS.index(lado(v, var_dict[v]))]
        tot += x * x * w
    return tot / tot.sum() if tot.sum() > 0 else tot


def pct(a):
    return " · ".join(f"{d} {p:.0%}" for d, p in zip(DIMS, a))


def tipo_comp(a):
    n = int((a >= MINIMO_DIMENSION).sum())
    return {3: "tres dimensiones", 2: "dos dimensiones"}.get(n, "una dimensión")


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)
    print("=== pesos_catalogo.py ===", flush=True)
    var_dict, datos = pca.cargar_datos()

    # ── 1. patrones de los cruces ──
    filas_p = []
    for c in CRUCES:
        ruta = cruces.SALIDA / c / "pares_variables.csv"
        if not ruta.exists():
            print(f"  falta {ruta}: corré cruces.py para ese cruce")
            continue
        for r in csv.DictReader(open(ruta, encoding="utf-8")):
            if r["tipo"] != "patrón":
                continue
            x, y = r["x_id"], r["y_id"]
            wx, wy = pesos(var_dict[x]), pesos(var_dict[y])
            comunes = [d for d, a, b in zip(DIMS, wx, wy) if a > 0 and b > 0]
            filas_p.append(dict(cruce=c, x=x, y=y, rho=float(r["rho_corregida"]),
                                dims_x="+".join(d for d, a in zip(DIMS, wx) if a > 0),
                                dims_y="+".join(d for d, a in zip(DIMS, wy) if a > 0),
                                dimension_comun="+".join(comunes),
                                depende_de_asignacion=bool(comunes),
                                composicion=pct((wx + wy) / 2)))
    with open(SALIDA / "patrones_cruces.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas_p[0]) if filas_p else ["cruce"])
        w.writeheader()
        w.writerows(filas_p)

    # ── 2. PCA y clustering conjunto sin asignar ──
    variables = [v for v, r in var_dict.items() if v in datos and r["metrica_id"] not in pca.VARIANTES]
    dim_de = {v: lado(v, var_dict[v]) for v in variables}
    conj, filas_c = {}, []
    for enf in ("ajustado", "tamano"):
        print(f"  PCA conjunto ({enf})…", flush=True)
        rp = cruces.pca_conjunto(variables, datos, var_dict, enf, np.random.default_rng(pca.SEMILLA),
                                 cruces.DEFAULTS["carga_minima"], dim_de)
        rc = cruces.clustering_conjunto(variables, datos, var_dict, enf, dim_de, rp) if "error" not in rp else {}
        conj[enf] = dict(pca=rp, clustering=rc)
        for comp in rp.get("componentes", []):
            pond = composicion(comp["cargas"], var_dict)
            asig = composicion(comp["cargas"], var_dict, ponderada=False)
            filas_c.append(dict(enfoque=enf, componente=comp["n"], varianza=comp["varianza"], bootstrap=comp["bootstrap"],
                                ponderada=pct(pond), tipo_ponderada=tipo_comp(pond),
                                asignada=pct(asig), tipo_asignada=tipo_comp(asig),
                                escala=any(var_dict[v].get("familia") == "tamano" for v, _ in comp["cargas"][:3]),
                                variables=", ".join(f"{v} {x:+.2f}" for v, x in comp["cargas"])))
    with open(SALIDA / "componentes_conjuntos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas_c[0]) if filas_c else ["enfoque"])
        w.writeheader()
        w.writerows(filas_c)

    # ── 3. factor común de tres_dimensiones.py ──
    factores = []
    ruta = corr.ROOT / "analisis" / "salidas" / "tres_dimensiones" / "resumen.json"
    if ruta.exists():
        R = json.loads(ruta.read_text(encoding="utf-8"))
        comp_cat = {}
        for cid, c in R["componentes"].items():
            ws = np.array([pesos(var_dict[v]) for v in c["variables"]])
            comp_cat[cid] = ws.mean(0)
        for var in ("sin_tamano_ni_documentacion", "sin_tamano_ni_renovacion", "sin_tamano"):
            f = R["global_"][var]["factores_mfa"][0]
            tot = sum(r * r * comp_cat[c] for c, r in f["correlaciones"].items())
            factores.append(dict(variante=var, correlaciones=f["correlaciones"],
                                 asignada=pct([f["parte_por_dimension"][d] for d in DIMS]),
                                 ponderada=pct(tot / tot.sum())))

    escribir_md(filas_p, conj, filas_c, factores, var_dict)
    print(f"  listo: {SALIDA}")


def escribir_md(filas_p, conj, filas_c, factores, var_dict):
    L = ["# Pertenencia ponderada según el catálogo", "",
         "Cada variable cuenta para las dimensiones que le asigna el catálogo, en partes iguales.", "",
         "## 1. Patrones de los cruces: ¿dependen de la asignación?", "",
         "Un patrón depende de la asignación si sus dos variables comparten una dimensión del catálogo: con otra "
         "asignación sería una relación dentro de esa dimensión.", ""]
    for c in CRUCES:
        ps = [p for p in filas_p if p["cruce"] == c]
        dep = [p for p in ps if p["depende_de_asignacion"]]
        L.append(f"- **{c.replace('_', '–')}:** {len(ps)} patrones, {len(dep)} dependen de la asignación")
    L += ["", "| Cruce | Patrón | ρ | Catálogo (x / y) | Dimensión común | Composición |", "|---|---|---|---|---|---|"]
    for p in sorted(filas_p, key=lambda p: (p["cruce"], not p["depende_de_asignacion"], -abs(p["rho"]))):
        L.append(f"| {p['cruce'].replace('_', '–')} | {p['x']} ↔ {p['y']} | {p['rho']:+.2f} | {p['dims_x']} / {p['dims_y']} | "
                 f"{p['dimension_comun'] or '—'} | {p['composicion']} |")
    L += ["", "## 2. PCA conjunto de las tres dimensiones, sin asignar", "",
          f"Todas las variables juntas. Composición de cada componente: carga al cuadrado de las variables que lo definen "
          f"(|carga| ≥ 0,4), repartida según el catálogo (ponderada) o entera al lado asignado. Tridimensional: cada "
          f"dimensión aporta al menos {MINIMO_DIMENSION:.0%}.", ""]
    for enf, r in conj.items():
        rp = r["pca"]
        if "error" in rp:
            L.append(f"- {enf}: {rp['error']}")
            continue
        L += [f"**{enf}** ({rp['variables']} variables, {rp['n']} releases, k = {rp['k']}):", "",
              "| CP | Varianza | Bootstrap | Ponderada | Asignada | Variables |", "|---|---|---|---|---|---|"]
        for f in [f for f in filas_c if f["enfoque"] == enf]:
            marca = " (escala)" if f["escala"] else ""
            L.append(f"| {f['componente']}{marca} | {f['varianza']:.0%} | {f['bootstrap']:.2f} | **{f['tipo_ponderada']}**: {f['ponderada']} | "
                     f"{f['tipo_asignada']}: {f['asignada']} | {f['variables']} |")
        rc = r.get("clustering") or {}
        for nombre, s in rc.get("soluciones", {}).items():
            filas_g = []
            for g in s["grupos"]:
                comp = composicion([(v, 1.0) for v in g["variables"]], var_dict)
                if tipo_comp(comp) == "tres dimensiones":
                    filas_g.append(f"{pct(comp)}: {', '.join(g['variables'])}")
            L.append(f"- clustering ({nombre}, k = {s['k']}): grupos de tres dimensiones con el catálogo: "
                     + ("; ".join(filas_g) or "ninguno"))
        L.append("")
    if factores:
        L += ["## 3. Factor común del análisis de tres dimensiones", "",
              "| Variante | Componentes (correlación con el factor) | Con la asignación | Con el catálogo |", "|---|---|---|---|"]
        for f in factores:
            cs = ", ".join(f"{c} {v:+.2f}" for c, v in f["correlaciones"].items() if abs(v) >= 0.4)
            L.append(f"| {f['variante'].replace('_', ' ')} | {cs} | {f['asignada']} | {f['ponderada']} |")
    (SALIDA / "resumen.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
