#!/usr/bin/env python3
"""
analisis/comparar_resultados.py

Compara el análisis original con el corregido (branch de fixes) para un cruce: cómo cambian
las categorías, qué relaciones robustas se mantienen, se pierden o aparecen, y si los
componentes del PCA de la dimensión siguen siendo los mismos.

Uso:
    python3 analisis/comparar_resultados.py Producto-Producto
    python3 analisis/comparar_resultados.py Persona-Persona --antes analisis/salidas_originales

Lee {antes}/pares_correlacion.csv y {antes}/pca/pca_<dim>.json, y lo mismo de --despues
(por defecto analisis/salidas). Imprime el resumen y lo guarda en
{despues}/comparacion_<cruce>.md.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

ROOT = Path(__file__).resolve().parent.parent


def normalizar_cruce(texto: str) -> str:
    partes = [p.strip().capitalize() for p in texto.replace("–", "-").split("-")]
    return "–".join(partes if len(partes) == 2 else partes * 2)


def tucker(a, b):
    den = float(np.sqrt((a ** 2).sum() * (b ** 2).sum()))
    return float((a * b).sum() / den) if den else float("nan")


def es_si(v) -> bool:
    return str(v).strip().lower() in ("true", "sí", "si", "1")


def comparar_correlaciones(antes: pd.DataFrame, despues: pd.DataFrame, cruce: str) -> list[str]:
    a, d = antes[antes.cruce == cruce], despues[despues.cruce == cruce]
    out = [f"## Correlaciones · {cruce}", ""]
    cats = ["positiva", "negativa", "sin_relacion", "no_concluyente", "insuficiente", "control"]
    out += ["| Categoría | Antes | Después |", "|---|---|---|"]
    out += [f"| {c} | {(a.categoria == c).sum()} | {(d.categoria == c).sum()} |" for c in cats]
    out += [f"| **Robustas** | {a.robusta.map(es_si).sum()} | {d.robusta.map(es_si).sum()} |",
            f"| Pares en total | {len(a)} | {len(d)} |", ""]

    ra = a[a.robusta.map(es_si)].set_index("par_id")
    rd = d[d.robusta.map(es_si)].set_index("par_id")
    da = a.set_index("par_id")
    dd = d.set_index("par_id")

    def fila(pid):
        x = (dd if pid in dd.index else da).loc[pid]
        nombre = f"{x.x_nombre} ↔ {x.y_nombre}"
        ant = f"{da.loc[pid].rho_corregida:+.2f} ({da.loc[pid].categoria})" if pid in da.index else "no existía"
        des = f"{dd.loc[pid].rho_corregida:+.2f} ({dd.loc[pid].categoria})" if pid in dd.index else "ya no existe"
        return f"| {nombre} | {ant} | {des} |"

    for titulo, ids in [("Robustas que se mantienen", sorted(set(ra.index) & set(rd.index))),
                        ("Robustas que se pierden", sorted(set(ra.index) - set(rd.index))),
                        ("Robustas nuevas", sorted(set(rd.index) - set(ra.index)))]:
        out += [f"### {titulo} ({len(ids)})", ""]
        if ids:
            out += ["| Par | ρ corregida antes | ρ corregida después |", "|---|---|---|"] + [fila(p) for p in ids]
        else:
            out.append("Ninguna.")
        out.append("")

    comunes = sorted(set(da.index) & set(dd.index))
    if comunes:
        cambio = (dd.loc[comunes].rho_corregida - da.loc[comunes].rho_corregida).abs().sort_values(ascending=False)
        out += ["### Pares con el mayor cambio de ρ corregida", "",
                "| Par | Antes | Después |", "|---|---|---|"]
        for pid in cambio.head(10).index:
            out.append(fila(pid))
        out.append("")
    return out


def comparar_pca(antes_dir: Path, despues_dir: Path, dim: str) -> list[str]:
    pa, pd_ = antes_dir / "pca" / f"pca_{dim.lower()}.json", despues_dir / "pca" / f"pca_{dim.lower()}.json"
    out = [f"## Componentes principales · {dim}", ""]
    if not pa.exists() or not pd_.exists():
        return out + [f"Falta {pa if not pa.exists() else pd_}.", ""]
    A, D = json.loads(pa.read_text()), json.loads(pd_.read_text())
    for clave in ("producto|estable|ajustado", "todas|estable|ajustado"):
        ra, rd = A["resultados"].get(clave), D["resultados"].get(clave)
        if not ra or not rd:
            continue
        va = ra.get("variables") or A["conjuntos"][clave.split("|")[0]]
        vd = rd.get("variables") or D["conjuntos"][clave.split("|")[0]]
        out += [f"### {clave} (estables, ajustado)", "",
                "| | Antes | Después |", "|---|---|---|",
                f"| Releases | {ra['n']} | {rd['n']} |",
                f"| Variables | {len(va)} | {len(vd)} |",
                f"| Componentes (Horn) | {ra['k']} | {rd['k']} |",
                f"| Varianza explicada | {round(ra['acumulada'][ra['k'] - 1] * 100)} % | {round(rd['acumulada'][rd['k'] - 1] * 100)} % |", ""]
        nuevas, salen = sorted(set(vd) - set(va)), sorted(set(va) - set(vd))
        if nuevas or salen:
            out += [f"Variables nuevas: {', '.join(nuevas) or 'ninguna'}. Variables que ya no están: {', '.join(salen) or 'ninguna'}.", ""]

        def resumen(r, vs):
            L = np.array(r["varimax"], dtype=float)
            return [", ".join(f"{vs[i]} ({L[i, j]:+.2f})" for i in np.argsort(-np.abs(L[:, j])) if abs(L[i, j]) >= .4)
                    or "(ninguna variable ≥ 0,4)" for j in range(L.shape[1])]

        comunes = [v for v in vd if v in va]
        if len(comunes) >= 3:
            La = np.array(ra["varimax"], dtype=float)[[va.index(v) for v in comunes]]
            Ld = np.array(rd["varimax"], dtype=float)[[vd.index(v) for v in comunes]]
            M = np.array([[abs(tucker(La[:, i], Ld[:, j])) for j in range(Ld.shape[1])] for i in range(La.shape[1])])
            fi, co = linear_sum_assignment(-M)
            out += ["Componentes emparejados por la congruencia de Tucker sobre las variables comunes "
                    "(≥ 0,95: el mismo; 0,85–0,95: parecido; < 0,85: distinto):", "",
                    "| Antes | Después | Congruencia |", "|---|---|---|"]
            ra_res, rd_res = resumen(ra, va), resumen(rd, vd)
            for i, j in sorted(zip(fi, co)):
                out.append(f"| CP{i + 1}: {ra_res[i]} | CP{j + 1}: {rd_res[j]} | {M[i, j]:.2f} |")
            sin_par = sorted(set(range(Ld.shape[1])) - set(co))
            for j in sin_par:
                out.append(f"| — | CP{j + 1}: {rd_res[j]} (nuevo) | — |")
            out.append("")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cruce", help="por ejemplo Producto-Producto")
    ap.add_argument("--antes", default=str(ROOT / "analisis" / "salidas_originales"))
    ap.add_argument("--despues", default=str(ROOT / "analisis" / "salidas"))
    args = ap.parse_args()
    cruce = normalizar_cruce(args.cruce)
    antes_dir, despues_dir = Path(args.antes), Path(args.despues)
    for d in (antes_dir, despues_dir):
        if not (d / "pares_correlacion.csv").exists():
            sys.exit(f"No encuentro {d / 'pares_correlacion.csv'}")
    antes = pd.read_csv(antes_dir / "pares_correlacion.csv")
    despues = pd.read_csv(despues_dir / "pares_correlacion.csv")
    lineas = [f"# Antes y después de los fixes · {cruce}", ""]
    lineas += comparar_correlaciones(antes, despues, cruce)
    lados = cruce.split("–")
    if lados[0] == lados[1]:
        lineas += comparar_pca(antes_dir, despues_dir, lados[0])
    texto = "\n".join(lineas)
    print(texto)
    destino = despues_dir / f"comparacion_{cruce.replace('–', '_').lower()}.md"
    destino.write_text(texto, encoding="utf-8")
    print(f"\nGuardado en {destino}")


if __name__ == "__main__":
    main()
