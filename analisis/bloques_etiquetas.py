#!/usr/bin/env python3
"""
analisis/bloques_etiquetas.py

Cruce de componentes y de grupos entre dimensiones sin asignar las métricas compartidas (el mismo criterio que
relaciones.py para las variables: la dimensión es una etiqueta de la relación).

  1. Cada dimensión usa todas las variables que el catálogo le asocia, compartidas incluidas: los componentes
     firmes del PCA de la dimensión con todas sus variables (conjunto "todas", con bootstrap y canary) y los grupos
     del clustering del mismo conjunto (corte propio). Se excluyen los componentes que forma una métrica que cambia
     pocas veces en la historia (README, Wiki, NOB), como en los cruces.
  2. El puntaje de cada componente o grupo es el promedio de los rangos ajustados de las variables que lo definen
     (|carga| >= 0,4 en el PCA; los miembros en el clustering), orientados según su signo. Así no se cuela, con un
     peso chico, una variable que define un elemento del otro lado.
  3. Se cruza cada elemento de una dimensión con cada elemento de otra. Si comparten métricas (la misma variable
     o resúmenes de la misma métrica), los puntajes se recalculan sin esas métricas: se cruza la parte propia de
     cada uno. Solo si a alguno no le queda nada el cruce no se evalúa (sería comparar una métrica consigo misma).
     Mismos cálculos y criterios que cruces.py (Spearman parcial, períodos, canary, tamaño, Benjamini–Hochberg en
     una sola familia por tipo de elemento); escala y mecánico como en los cruces.
  4. Cada patrón se etiqueta con sus lecturas: un elemento puede leerse como de una dimensión si todas las
     variables que lo forman (después de sacar las compartidas) son de esa dimensión según el catálogo.
  5. Triángulos de tres dimensiones entre componentes y entre grupos: un elemento de cada dimensión, sin métricas en
     común y de tres aspectos distintos, con los tres pares patrón y tres dimensiones distintas posibles; cada lado se
     recalcula descontando el tercero.

Uso (después de pca.py y clustering.py de las tres dimensiones):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/bloques_etiquetas.py

Salidas en analisis/salidas/bloques_etiquetas/: resumen.md, pares.csv, triangulos.csv.
"""
import csv
import sys
import warnings
from itertools import combinations, product
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import correlaciones as corr  # noqa: E402
import cruces  # noqa: E402
import multiverso_asignacion as mv  # noqa: E402
import pca  # noqa: E402
import tres_dimensiones as td  # noqa: E402

SALIDA = corr.ROOT / "analisis" / "salidas" / "bloques_etiquetas"
DIMS = ("Persona", "Proceso", "Producto")
CFG = cruces.mezclar(cruces.DEFAULTS, {"componentes": {"conjunto": {d: "todas" for d in DIMS}}})
CARGA = CFG["carga_minima"]
ESCALONES = ("rc_", "wp_", "nob_")          # métricas que cambian pocas veces (componentes que no se cruzan)


def dims_de(var_dict, v):
    r = var_dict[v]
    return {d for d, f in zip(DIMS, (r["dim_persona"], r["dim_proceso"], r["dim_producto"])) if f == "1"}


def base(var_dict, v):
    return corr.metrica_base(var_dict[v]["metrica_id"])


def elementos(var_dict, datos, duraciones):
    """Componentes firmes y grupos de cada dimensión, con sus variables y signos, y las matrices de puntajes."""
    els, mats = [], {}
    for d in DIMS:
        cps = cruces.componentes(d, CFG, duraciones)
        P, _ = cruces.cargar_pca(d, CFG)
        vs = P["resultados"]["todas|estable|ajustado"]["variables"]
        for serie in ("estable", "canary"):
            mats[(d, serie)] = cruces.matriz(vs, datos, serie, "ajustado")
        for c in cps:
            fuertes = [(v, x) for v, x in c["cargas"] if abs(x) >= CARGA]
            peso_escalon = sum(x * x for v, x in fuertes if v.startswith(ESCALONES)) / max(1e-9, sum(x * x for _, x in fuertes))
            if not fuertes or peso_escalon >= 0.5:
                continue
            els.append(dict(id=f"{d.lower()}_cp{c['n']}", dim=d, tipo="componente", vars=[(v, 1.0 if x >= 0 else -1.0) for v, x in fuertes],
                            tema=mv.tema_de(fuertes)))
        C = cruces.cargar_clustering(d)["resultados"]["todas|estable|ajustado"]
        sol = C["soluciones"]["propio"]
        miembros = {}
        for v, g in zip(C["variables"], sol["etiquetas"]):
            miembros.setdefault(g, []).append(v)
        Ze, pe, _ = mats[(d, "estable")]
        for g, mvs in miembros.items():
            if len(mvs) < 2 or any(v not in vs for v in mvs):
                continue
            idx = [vs.index(v) for v in mvs]
            R = np.corrcoef(Ze[:, idx], rowvar=False)
            central = int(np.argmax(np.abs(R).mean(axis=0)))
            els.append(dict(id=f"{d.lower()}_g{g}", dim=d, tipo="grupo", vars=[(v, 1.0 if R[central, i] >= 0 else -1.0) for i, v in enumerate(mvs)],
                            tema=mv.tema_de([(v, 1.0) for v in mvs])))
    return els, mats


def puntaje(el, quitar, var_dict, mats, duraciones):
    """Serie estable y canary del promedio de los rangos ajustados de las variables del elemento, sin las métricas
    de `quitar`."""
    vs = [(v, s) for v, s in el["vars"] if base(var_dict, v) not in quitar]
    if not vs:
        return None, None, []
    out = []
    for serie, db in (("estable", "versiones"), ("canary", "versiones_canary")):
        Z, pn, filas = mats[(el["dim"], serie)]
        if Z is None:
            out.append({})
            continue
        P, _ = cruces.cargar_pca(el["dim"], CFG)
        lista = P["resultados"]["todas|estable|ajustado"]["variables"]
        cols = [(lista.index(v), s) for v, s in vs if v in lista]
        val = np.mean([Z[:, j] * s for j, s in cols], axis=0)
        out.append(cruces.a_serie(val, pn, filas, duraciones, db))
    return out[0], out[1], [v for v, _ in vs]


def lecturas(vx, vy, var_dict):
    dx = set.intersection(*(dims_de(var_dict, v) for v in vx))
    dy = set.intersection(*(dims_de(var_dict, v) for v in vy))
    entre = sorted({"–".join(sorted((a, b), key=DIMS.index)) for a, b in product(dx, dy) if a != b})
    dentro = sorted({a for a, b in product(dx, dy) if a == b}, key=DIMS.index)
    return dx, dy, entre, dentro


def cruzar(els, tipo, var_dict, mats, duraciones, size_e):
    pares = {}
    sub = [e for e in els if e["tipo"] == tipo]
    for a, b in combinations(sub, 2):
        if a["dim"] == b["dim"]:
            continue
        comunes = {base(var_dict, v) for v, _ in a["vars"]} & {base(var_dict, v) for v, _ in b["vars"]}
        xa, ca, va = puntaje(a, comunes, var_dict, mats, duraciones)
        xb, cb, vb = puntaje(b, comunes, var_dict, mats, duraciones)
        k = f"{a['id']}__{b['id']}"
        base_fila = dict(par_id=k, x_id=a["id"], y_id=b["id"], x_tema=a["tema"], y_tema=b["tema"], comparten=", ".join(sorted(comunes)))
        if xa is None or xb is None:
            pares[k] = dict(base_fila, evaluado=False, motivo="mismo contenido", n=0, p_corregida=np.nan, rho_corregida=np.nan,
                            ic_inf=np.nan, ic_sup=np.nan, estable=False, rho_canary=np.nan, rho_corregida_tamano=np.nan)
            continue
        pr = cruces.evaluar_par(xa, xb, ca, cb, size_e, True)
        dx, dy, entre, dentro = lecturas(va, vb, var_dict)
        escala = any(sum(var_dict[v].get("familia") == "tamano" for v in vv) / len(vv) >= 0.5 for vv in (va, vb))
        pr.update(base_fila, evaluado=True, motivo="", vars_x=", ".join(va), vars_y=", ".join(vb), lect_x="+".join(sorted(dx, key=DIMS.index)),
                  lect_y="+".join(sorted(dy, key=DIMS.index)), entre="; ".join(entre), dentro="; ".join(dentro),
                  escala=escala, mecanico=cruces.solapan(va, vb, var_dict), _sa=xa, _sb=xb, _ca=ca, _cb=cb)
        pares[k] = pr
    evaluados = {k: p for k, p in pares.items() if p["evaluado"]}
    cruces.clasificar(evaluados, set())
    for p in pares.values():
        if not p["evaluado"]:
            p.update(patron=False, robusta=False, categoria="", p_fdr="")
            continue
        p["patron"] = bool(p["robusta"] and not p["escala"] and not p["mecanico"] and p["resiste_tamano"] is not False)
        p["motivo"] = ("" if p["patron"] else "escala" if p["robusta"] and p["escala"] else "mecánico" if p["robusta"] and p["mecanico"]
                       else "no resiste tamaño" if p["robusta"] else "no robusto" if p["categoria"] in ("positiva", "negativa") else p["categoria"])
    return pares


def triangulos(els, pares, var_dict, size, tipo="componente"):
    cps = [e for e in els if e["tipo"] == tipo]
    porpar = {frozenset((p["x_id"], p["y_id"])): p for p in pares.values()}
    out, cond = [], {}
    candidatos = []
    for a, b, c in product(*([e for e in cps if e["dim"] == d] for d in DIMS)):
        trio = (a, b, c)
        bases = [{base(var_dict, v) for v, _ in e["vars"]} for e in trio]
        if any(bases[i] & bases[j] for i, j in ((0, 1), (0, 2), (1, 2))):
            continue
        lados = [porpar.get(frozenset((trio[i]["id"], trio[j]["id"]))) for i, j in ((0, 1), (0, 2), (1, 2))]
        if not all(l and l.get("patron") for l in lados):
            continue
        ds = [set.intersection(*(dims_de(var_dict, v) for v, _ in e["vars"])) for e in trio]
        asign = [x for x in product(*ds) if len(set(x)) == 3]
        if not asign or len({e["tema"] for e in trio}) < 3:
            continue
        candidatos.append((trio, lados, asign))
    for trio, lados, asign in candidatos:
        series = [dict(id=e["id"], estable=lados[0]["_sa"] if k == 0 else None) for k, e in enumerate(trio)]
        s = {trio[0]["id"]: (lados[0]["_sa"], lados[0]["_ca"]), trio[1]["id"]: (lados[0]["_sb"], lados[0]["_cb"]),
             trio[2]["id"]: (lados[1]["_sb"], lados[1]["_cb"])}
        series = [dict(id=e["id"], estable=s[e["id"]][0], canary_serie=s[e["id"]][1]) for e in trio]
        E = td.Serie(series, "estable", size["versiones"])
        C = td.Serie(series, "canary_serie", size["versiones_canary"])
        E.anio = [y for y in E.anio]
        E.epoca = [None] * E.n
        for x, y, z in ((0, 1, 2), (0, 2, 1), (1, 2, 0)):
            cond[(tuple(e["id"] for e in trio), x, y)] = td.evaluar(x, y, (z,), E, C)
    if cond:
        td.clasificar(cond, lambda k: False, lambda k: False)
    for trio, lados, asign in candidatos:
        ids = tuple(e["id"] for e in trio)
        res = [cond[(ids, x, y)] for x, y, _ in ((0, 1, 2), (0, 2, 1), (1, 2, 0))]
        caen = [f"{ids[x]}↔{ids[y]}" for (x, y, _), r in zip(((0, 1, 2), (0, 2, 1), (1, 2, 0)), res) if not r["patron"]]
        out.append(dict(elementos=tipo, componentes=" · ".join(f"{e['id']} ({e['tema']})" for e in trio), tipo="tridimensional" if not caen else "cadena",
                        desaparece=", ".join(caen),
                        lados="; ".join(f"{l['x_id']}↔{l['y_id']} {l['rho_corregida']:+.2f} → {r['rho']:+.2f}" for l, r in zip(lados, res)),
                        asignaciones=" | ".join(", ".join(f"{e['id']}→{d}" for e, d in zip(trio, a)) for a in asign)))
    return out


def main():
    warnings.filterwarnings("ignore")
    SALIDA.mkdir(parents=True, exist_ok=True)
    print("=== bloques_etiquetas.py ===", flush=True)
    var_dict, datos = pca.cargar_datos()
    duraciones = {s: {} for s in ("versiones", "versiones_canary")}
    for v in datos:
        if v.startswith("__"):
            continue
        for s in duraciones:
            for p, t in datos[v].get(s, {}).items():
                if t[0] is not None:
                    duraciones[s].setdefault(p, t[0])
    els, mats = elementos(var_dict, datos, duraciones)
    print("  " + ", ".join(f"{d}: {sum(1 for e in els if e['dim'] == d and e['tipo'] == 'componente')} componentes, "
                           f"{sum(1 for e in els if e['dim'] == d and e['tipo'] == 'grupo')} grupos" for d in DIMS), flush=True)
    size = datos["activos_interaccion_conteo"]
    todos = {}
    for tipo in ("componente", "grupo"):
        pares = cruzar(els, tipo, var_dict, mats, duraciones, size["versiones"])
        for k, p in pares.items():
            p["tipo_elemento"] = tipo
        todos[tipo] = pares
    tris = triangulos(els, todos["componente"], var_dict, size) + triangulos(els, todos["grupo"], var_dict, size, "grupo")
    cols = ["tipo_elemento", "par_id", "x_tema", "y_tema", "comparten", "evaluado", "vars_x", "vars_y", "lect_x", "lect_y", "entre", "dentro",
            "rho_corregida", "p_fdr", "rho_2016_2019", "rho_2020_2022", "rho_2023_2024", "rho_2025_2026", "rho_canary", "rho_corregida_tamano",
            "robusta", "escala", "mecanico", "patron", "motivo"]
    with open(SALIDA / "pares.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for tipo in todos:
            for p in todos[tipo].values():
                w.writerow({k: (round(v, 4) if isinstance(v, float) and not np.isnan(v) else "" if isinstance(v, float) else v) for k, v in p.items()})
    with open(SALIDA / "triangulos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["elementos", "componentes", "tipo", "desaparece", "lados", "asignaciones"])
        w.writeheader()
        w.writerows(tris)
    escribir_md(els, todos, tris)
    print(f"  listo: {SALIDA}")


def f2(v):
    return f"{v:+.2f}".replace(".", ",") if isinstance(v, float) and not np.isnan(v) else "—"


def escribir_md(els, todos, tris):
    L = ["# Componentes y grupos entre dimensiones, con las lecturas del catálogo", "",
         "Cada dimensión con todas sus variables (compartidas incluidas). Si dos elementos comparten métricas, se cruza la "
         "parte propia de cada uno; si a alguno no le queda nada, el cruce no se evalúa.", ""]
    L += ["## Elementos", "", "| Elemento | Tipo | Tema | Variables |", "|---|---|---|---|"]
    for e in els:
        L.append(f"| {e['id']} | {e['tipo']} | {e['tema']} | {', '.join(v for v, _ in e['vars'])} |")
    for tipo, pares in todos.items():
        ev = [p for p in pares.values() if p["evaluado"]]
        pat = [p for p in ev if p["patron"] and p["x_tema"] != p["y_tema"]]
        mismo = sum(1 for p in pares.values() if not p["evaluado"])
        L += ["", f"## Cruce de {tipo}s", "",
              f"{len(pares)} pares entre dimensiones; {mismo} no se evalúan (mismo contenido); {sum(1 for p in ev if p['comparten'])} se "
              f"evaluaron sin las métricas compartidas. {len(pat)} patrones entre aspectos distintos.", "",
              "| Par | Temas | ρ | Canary | Con tamaño | Puede conectar | También dentro de | Sin |", "|---|---|---|---|---|---|---|---|"]
        for p in sorted(pat, key=lambda p: -abs(p["rho_corregida"])):
            L.append(f"| {p['x_id']} ↔ {p['y_id']} | {p['x_tema']} ↔ {p['y_tema']} | {f2(p['rho_corregida'])} | {f2(p['rho_canary'])} | "
                     f"{f2(p['rho_corregida_tamano'])} | {p['entre'] or '—'} | {p['dentro'] or '—'} | {p['comparten'] or '—'} |")
    for tipo in ("componente", "grupo"):
        sub = [t for t in tris if t["elementos"] == tipo]
        L += ["", f"## Triángulos de tres dimensiones entre {tipo}s", ""]
        if not sub:
            L.append(f"Ninguno: no hay tres {tipo}s de dimensiones distintas, sin métricas en común y de tres aspectos distintos, relacionados de a pares.")
        for t in sub:
            L.append(f"- **{t['tipo']}**: {t['componentes']} · {t['lados']}" + (f" · se debilita: {t['desaparece']}" if t["desaparece"] else ""))
    (SALIDA / "resumen.md").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
