#!/usr/bin/env python3
"""
analisis/relaciones.py

Relaciones entre métricas sin asignar las métricas compartidas a una dimensión. La dimensión es una etiqueta de
la relación, no de la variable: el catálogo asocia dieciséis métricas a dos dimensiones (EXPRev es de Persona y de
Proceso; CFDR, de Proceso y de Producto), y una relación con una de ellas es, a la vez, una relación de cada par
de dimensiones que permite el catálogo. La restricción de poner cada variable de un solo lado solo hace falta en
los métodos que juntan variables en bloques (componentes, grupos, correlación canónica); en un par de variables
nunca se compara una variable consigo misma.

  1. Todos los pares de variables, una sola vez y en una sola familia para Benjamini–Hochberg (sin las variantes
     de una métrica, que se usan solo como control). Mismos cálculos y filtros que correlaciones.py: Spearman
     parcial, muestra efectiva, estabilidad por períodos, réplica en canary, ventanas cortas, control por tamaño,
     definiciones superpuestas, pares de control y nivel de evidencia. Se calculan con
     correlaciones.correr(..., entre_dimensiones=True) en salidas/relaciones/base y acá se clasifican de nuevo con
     una única corrección.
  2. Lecturas del catálogo de cada patrón: los pares de dimensiones que puede conectar y si también tiene lectura
     dentro de una dimensión. Tipos: entre dimensiones (sus variables no comparten ninguna dimensión), entre y
     dentro (pueden conectar dimensiones distintas o leerse dentro de una que comparten) y dentro (las dos son de la
     misma dimensión y de ninguna otra). Cada patrón cuenta para cada par de dimensiones que puede conectar.
  3. Triángulos de tres dimensiones entre variables: tres variables relacionadas de a pares (los tres lados son
     patrón) a las que el catálogo permite asignar tres dimensiones distintas. Cada lado se recalcula descontando el
     tercer vértice: tridimensional si los tres se mantienen como patrón; cadena si alguno desaparece. Solo cuentan
     los triángulos de tres aspectos distintos (temas de multiverso_asignacion.py).

Los patrones descartados al validar (sección de validación) se marcan y no cuentan como hallazgos.

Uso:
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/relaciones.py [--recalcular]

--recalcular vuelve a calcular todos los pares (correlaciones.correr) antes de clasificarlos.
Salidas en analisis/salidas/relaciones/: resumen.md, patrones.csv, triangulos.csv.
"""
import csv
import math
import sys
import warnings
from collections import defaultdict
from itertools import combinations, product
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import correlaciones as corr  # noqa: E402
import multiverso_asignacion as mv  # noqa: E402
import pca  # noqa: E402
import tres_dimensiones as td  # noqa: E402

SALIDA = corr.ROOT / "analisis" / "salidas" / "relaciones"
BASE = SALIDA / "base"
DIMS = ("Persona", "Proceso", "Producto")
MISMA_MEDIDA = 0.99   # dos métricas con |ρ| ≥ 0,99 miden lo mismo (CFDR y NUB): no es una relación entre aspectos
PARES_DIM = [("Persona", "Proceso"), ("Persona", "Producto"), ("Proceso", "Producto")]
# descartados al validar (recalculando las variables sin los datos que podían fabricar la relación)
DESCARTADOS = {
    frozenset(("sc_mediana", "jarczyk_success_rate_producto")): "sin las issues propias cerradas en el mismo release",
    frozenset(("le_mediana", "anmcc_mediana")): "sin los recién llegados",
    frozenset(("dev_exp_mediana", "anmcc_mediana")): "sin los recién llegados",
    frozenset(("cdiv_mediana", "commits_doc_producto")): "sin los commits que solo tocan documentación",
    frozenset(("tasa_nuevos_commits_ratio", "le_producto")): "construcción de LE (los recién llegados)",
    frozenset(("prop_commitean_ratio", "le_producto")): "construcción de LE (los recién llegados)",
}


def num(v):
    try:
        f = float(v)
        return f if not math.isnan(f) else np.nan
    except (TypeError, ValueError):
        return np.nan


def dims_de(r):
    return [d for d, f in zip(DIMS, (r["dim_persona"], r["dim_proceso"], r["dim_producto"])) if f == "1"]


def lecturas(dx, dy):
    entre = sorted({tuple(sorted((a, b), key=DIMS.index)) for a, b in product(dx, dy) if a != b}, key=PARES_DIM.index)
    dentro = sorted({a for a, b in product(dx, dy) if a == b}, key=DIMS.index)
    return entre, dentro


# ── 1. clasificación con una sola familia ────────────────────────────────────

def clasificar(var_dict):
    pares = {}
    for r in csv.DictReader(open(BASE / "pares_correlacion.csv", encoding="utf-8")):
        if r["par_id"] in pares:
            continue
        x, y = r["x_id"], r["y_id"]
        if var_dict[x]["metrica_id"] in pca.VARIANTES or var_dict[y]["metrica_id"] in pca.VARIANTES:
            continue
        pares[r["par_id"]] = r
    control = {k for k, r in pares.items() if r["por_construccion"] == "True"}
    q = corr.benjamini_hochberg([(k, num(r["p_corregida"])) for k, r in pares.items() if k not in control])
    filas = []
    for k, r in pares.items():
        rho = num(r["rho_corregida"])
        p_fdr = q.get(k, "")
        cat, fuerza = corr.categoria_y_fuerza(k in control, int(float(r["n"] or 0)), p_fdr if isinstance(p_fdr, float) else np.nan,
                                              rho, num(r["ic_inf"]), num(r["ic_sup"]))
        cortas = corr.depende_de_ventanas_cortas(rho, num(r["rho_corregida_sin_cortas"]))
        robusta = corr.es_robusta(cat, r["estable"] == "True", rho, num(r["rho_canary"]), cortas)
        tam = corr.resiste_tamano(rho, num(r["rho_corregida_tamano"]))
        con_tamano = k not in control and "tamano" in (r["x_familia"], r["y_familia"])
        pasa = bool(robusta and r["solapamiento_definicion"] != "True" and tam is not False)
        rloc = num(r["rho_corregida_local"])
        local_ok = (not np.isnan(rloc) and not np.isnan(rho) and corr.mismo_signo(rloc, rho) and abs(rloc) >= corr.UMBRAL_FUERZA
                    and corr.excluye_cero(num(r["ic_local_inf"]), num(r["ic_local_sup"])))
        alcance = r.get("alcance_temporal", "")
        nivel = ""
        if pasa:
            nivel = ("alta" if alcance == "toda la historia" and local_ok else
                     "baja" if alcance.startswith("sin relación") or not local_ok else "media")
        x, y = r["x_id"], r["y_id"]
        dx, dy = dims_de(var_dict[x]), dims_de(var_dict[y])
        entre, dentro = lecturas(dx, dy)
        validacion = DESCARTADOS.get(frozenset((x, y)), "")
        misma_medida = not np.isnan(rho) and abs(rho) >= MISMA_MEDIDA
        patron = pasa and not con_tamano and not validacion and not misma_medida
        tipo = ("entre dimensiones" if entre and not dentro else "entre y dentro" if entre else "dentro")
        motivo = ("control" if k in control else "" if pasa and not con_tamano else
                  "escala" if pasa and con_tamano else
                  "no significativo" if cat not in ("positiva", "negativa") else
                  "no robusto" if not robusta else "mecánico" if r["solapamiento_definicion"] == "True" else "no resiste tamaño")
        if pasa and not con_tamano and validacion:
            motivo = "descartado al validar: " + validacion
        if pasa and not con_tamano and misma_medida:
            motivo = "misma medida"
        filas.append(dict(par_id=k, x=x, y=y, x_nombre=r["x_nombre"], y_nombre=r["y_nombre"], dims_x="+".join(dx), dims_y="+".join(dy),
                          rho=rho, q=p_fdr, categoria=cat, fuerza=fuerza, rho_canary=num(r["rho_canary"]),
                          rho_tamano=num(r["rho_corregida_tamano"]), rho_2016_2019=num(r["rho_2016_2019"]), rho_2020_2022=num(r["rho_2020_2022"]),
                          rho_2023_2024=num(r["rho_2023_2024"]), rho_2025_2026=num(r["rho_2025_2026"]),
                          robusta=robusta, patron=patron, nivel=nivel if patron else "", motivo=motivo,
                          tipo=tipo, entre="; ".join(f"{a}–{b}" for a, b in entre), dentro="; ".join(dentro),
                          mismo_tema=mv.tema(x) == mv.tema(y), tema_x=mv.tema(x), tema_y=mv.tema(y)))
    return filas


# ── 3. triángulos ────────────────────────────────────────────────────────────

def triangulos(filas, var_dict, datos):
    pat = {frozenset((f["x"], f["y"])): f for f in filas if f["patron"]}
    vecinos = defaultdict(set)
    for k in pat:
        a, b = tuple(k)
        vecinos[a].add(b)
        vecinos[b].add(a)
    trios = set()
    for a in vecinos:
        for b, c in combinations(sorted(vecinos[a]), 2):
            if c in vecinos[b]:
                trios.add(tuple(sorted((a, b, c))))
    size = datos["activos_interaccion_conteo"]
    cortes = corr.cortes_epocas(datos)
    validos, cond = [], {}
    for t in sorted(trios):
        ds = [dims_de(var_dict[v]) for v in t]
        asignaciones = [a for a in product(*ds) if len(set(a)) == 3]
        if not asignaciones:
            continue
        series = [dict(id=v, estable=datos[v]["versiones"], canary_serie=datos[v]["versiones_canary"]) for v in t]
        ep = {p: 1 + sum(p >= c for c in cortes) for p in datos[t[0]]["versiones"]}
        E = td.Serie(series, "estable", size["versiones"], ep)
        C = td.Serie(series, "canary_serie", size["versiones_canary"])
        for x, y, z in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
            cond[(t, x, y)] = td.evaluar(x, y, (z,), E, C)
        validos.append((t, asignaciones))
    td.clasificar(cond, lambda k: False, lambda k: False)
    out = []
    for t, asignaciones in validos:
        lados = []
        for x, y, z in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
            f = pat[frozenset((t[x], t[y]))]
            c = cond[(t, x, y)]
            lados.append(dict(par=f"{t[x]} ↔ {t[y]}", rho=f["rho"], sin_tercero=c["rho"], se_mantiene=c["patron"], nivel=f["nivel"]))
        caen = [l["par"] for l in lados if not l["se_mantiene"]]
        temas = {mv.tema(v) for v in t}
        if len(temas) < 3:
            tipo = "un solo aspecto" if len(temas) == 1 else "dos aspectos"
        else:
            tipo = "tridimensional" if not caen else "cadena"
        out.append(dict(variables=" · ".join(t), tipo=tipo,
                        desaparece_al_descontar="; ".join(caen),
                        asignaciones=" | ".join(", ".join(f"{v}→{d}" for v, d in zip(t, a)) for a in asignaciones),
                        temas=" + ".join(sorted(temas)), temas_distintos=len(temas),
                        **{f"lado{i + 1}": l["par"] for i, l in enumerate(lados)},
                        **{f"lado{i + 1}_rho": l["rho"] for i, l in enumerate(lados)},
                        **{f"lado{i + 1}_sin_tercero": l["sin_tercero"] for i, l in enumerate(lados)},
                        **{f"lado{i + 1}_nivel": l["nivel"] for i, l in enumerate(lados)}))
    return out


def escribir_csv(ruta, filas):
    if not filas:
        ruta.write_text("", encoding="utf-8")
        return
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        for r in filas:
            w.writerow({k: (round(v, 4) if isinstance(v, float) and not np.isnan(v) else "" if isinstance(v, float) else v) for k, v in r.items()})


def f2(v):
    return f"{v:+.2f}".replace(".", ",") if isinstance(v, float) and not np.isnan(v) else "—"


def main():
    warnings.filterwarnings("ignore")
    SALIDA.mkdir(parents=True, exist_ok=True)
    print("=== relaciones.py ===", flush=True)
    if "--recalcular" in sys.argv or not (BASE / "pares_correlacion.csv").exists():
        corr.correr(BASE, "calendario", entre_dimensiones=True)
    var_dict, datos = pca.cargar_datos()
    filas = clasificar(var_dict)
    patrones = [f for f in filas if f["patron"]]
    print(f"  {len(filas)} pares, {len(patrones)} patrones", flush=True)
    tris = triangulos(filas, var_dict, datos)
    print(f"  {len(tris)} triángulos con tres dimensiones posibles", flush=True)
    escribir_csv(SALIDA / "patrones.csv", sorted(filas, key=lambda f: (not f["patron"], f["tipo"], -abs(f["rho"]) if not np.isnan(f["rho"]) else 0)))
    escribir_csv(SALIDA / "triangulos.csv", tris)
    escribir_md(filas, patrones, tris)
    print(f"  listo: {SALIDA}")


def escribir_md(filas, patrones, tris):
    L = ["# Relaciones entre métricas con las lecturas del catálogo", "",
         f"{len(filas)} pares de variables (sin las variantes), evaluados una sola vez y corregidos con Benjamini–Hochberg "
         f"en una sola familia. {len(patrones)} son patrón (robustos, resisten el tamaño, no son mecánicos ni de escala, no "
         f"se descartaron al validar).", "",
         "| Tipo | Patrones | Qué significa |", "|---|---|---|"]
    desc = {"entre dimensiones": "sus variables no comparten ninguna dimensión del catálogo",
            "entre y dentro": "pueden conectar dimensiones distintas o leerse dentro de una dimensión que comparten",
            "dentro": "las dos variables son de la misma dimensión y de ninguna otra"}
    for t in ("entre dimensiones", "entre y dentro", "dentro"):
        L.append(f"| {t} | {sum(1 for p in patrones if p['tipo'] == t)} | {desc[t]} |")
    descartados = [f for f in filas if f["motivo"].startswith("descartado al validar")]
    L += ["", f"Descartados al validar (no cuentan): {len(descartados)}.", ""]
    for a, b in PARES_DIM:
        par = f"{a}–{b}"
        sub = [p for p in patrones if par in p["entre"].split("; ")]
        excl = [p for p in sub if p["tipo"] == "entre dimensiones"]
        L += [f"## {par}", "", f"{len(sub)} patrones pueden conectar estas dos dimensiones; {len(excl)} solo pueden leerse como "
              f"entre dimensiones.", "", "| Patrón | ρ | Nivel | Catálogo | Otras lecturas | Canary | Con tamaño |", "|---|---|---|---|---|---|---|"]
        for p in sorted(sub, key=lambda p: (p["mismo_tema"], p["tipo"] != "entre dimensiones", -abs(p["rho"]))):
            otras = [e for e in p["entre"].split("; ") if e != par] + [f"dentro de {d}" for d in p["dentro"].split("; ") if d]
            L.append(f"| {p['x']} ↔ {p['y']}{' (mismo tema)' if p['mismo_tema'] else ''} | {f2(p['rho'])} | {p['nivel']} | "
                     f"{p['dims_x']} / {p['dims_y']} | {', '.join(otras) or '—'} | {f2(p['rho_canary'])} | {f2(p['rho_tamano'])} |")
        L.append("")
    L += ["## Tres dimensiones entre variables", "",
          "Triángulos de tres variables relacionadas de a pares a las que el catálogo permite asignar tres dimensiones distintas. "
          "Tridimensional: los tres lados se mantienen como patrón al descontar el tercer vértice. Cadena: el lado que se "
          "debilita conecta dos dimensiones solo a través de la tercera. Los triángulos con dos medidas del mismo aspecto (por "
          "ejemplo, dos medidas de la concentración del núcleo) o de un solo aspecto no conectan aspectos distintos y no cuentan.", ""]
    for t in ("tridimensional", "cadena", "dos aspectos", "un solo aspecto"):
        sub = [x for x in tris if x["tipo"] == t]
        L += [f"### {t.capitalize()} ({len(sub)})", "",
              "| Variables | Temas | Lados: ρ → sin el tercero | Asignaciones que lo hacen de tres dimensiones |", "|---|---|---|---|"]
        for x in sorted(sub, key=lambda x: (-x["temas_distintos"], -min(abs(x[f"lado{i}_rho"]) for i in (1, 2, 3)))):
            lados = "; ".join(f"{x[f'lado{i}']} {f2(x[f'lado{i}_rho'])} → {f2(x[f'lado{i}_sin_tercero'])}" for i in (1, 2, 3))
            L.append(f"| {x['variables']} | {x['temas']} | {lados} | {x['asignaciones']} |")
        L.append("")
    (SALIDA / "resumen.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
