"""Validación de Contribution Diversity (mediana) ↔ commits que tocan documentación (cruce Persona–Producto), sin tocar la base.

Recalcula Contribution Diversity por colaborador en cada ventana, desde el clon local, sin los commits
que solo tocan documentación, y repite la correlación del cruce (misma función evaluar_par) contra
la proporción de commits que tocan documentación. Solo lee: la base (periodos y resultados), el CSV
de persona agregada y el clon. Escribe solo en la carpeta de salida que se le pasa.

Uso (desde la raíz del repo):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/cdiv_sin_commits_doc.py [carpeta_salida]

Por defecto escribe en analisis/salidas/validaciones/cdiv_sin_commits_doc/.
"""
import csv
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analisis"))
sys.path.insert(0, str(ROOT / "16"))

import numpy as np
import psycopg2

import export_persona as ep
import generar_pca as gp
import cruce_dimensiones as cd
from base_metric import es_bot
from dloc import es_documentacion

SALIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "analisis" / "salidas" / "validaciones" / "cdiv_sin_commits_doc"
SALIDA.mkdir(parents=True, exist_ok=True)
CLON = ROOT / ".clones" / "next.js"
RAMA = "origin/HEAD"


import generar_correlaciones as gc


def conectar():
    return psycopg2.connect(**gc.DB)  # credenciales del .env, como el resto del análisis


# ── 1. ventanas (solo lectura) ──
con = conectar()
con.set_session(readonly=True)
cur = con.cursor()
cur.execute("""SELECT p.tipo_analisis, p.periodo_num, p.fecha_inicio, p.fecha_fin
               FROM periodo p JOIN repos r ON r.repo_id = p.repo_id
               WHERE r.full_name = 'vercel/next.js' AND p.tipo_analisis IN ('versiones', 'versiones_canary')""")
ventanas = {"versiones": [], "versiones_canary": []}
for tipo, pnum, fi, ff in cur.fetchall():
    ventanas[tipo].append((pnum, fi, ff))
con.close()

# ── 2. todos los commits de la rama, una sola vez (fecha de commit, como git log --since/--until) ──
out = subprocess.run(["git", "-C", str(CLON), "log", RAMA, "--no-merges", "--numstat", "--date=iso-strict",
                      "--pretty=format:\x01%an\x01%cI"], capture_output=True, text=True, check=True).stdout
commits, actual = [], None
for linea in out.splitlines():
    if linea.startswith("\x01"):
        if actual:
            commits.append(actual)
        _, autor, fecha = linea.split("\x01")
        actual = {"author": autor.strip() or "desconocido", "ts": datetime.fromisoformat(fecha), "files": []}
    elif linea.strip() and actual is not None:
        partes = linea.split("\t")
        if len(partes) == 3:
            actual["files"].append(partes[2].split("=>")[-1].strip(" {}") if "=>" in partes[2] else partes[2])
if actual:
    commits.append(actual)
commits.sort(key=lambda c: c["ts"])
ts = np.array([c["ts"].timestamp() for c in commits])
solo_doc = np.array([bool(c["files"]) and all(es_documentacion(f) for f in c["files"]) for c in commits])
print(f"commits en la rama: {len(commits)} · solo documentación: {int(solo_doc.sum())} ({solo_doc.mean():.1%})")

# ── 3. CDIV por persona y mediana por ventana, igual que export_persona (canon + humanos) ──
ep.load_alias()
bots = ep.load_bots()


def mediana_cdiv(idx):
    por_autor = defaultdict(set)
    for i in idx:
        c = commits[i]
        if es_bot(c["author"]):
            continue
        por_autor[c["author"]].update(c["files"])
    crudo = [(0, a, len(f)) for a, f in por_autor.items()]
    agrup = ep._agrupar_con_dedupe(crudo, [], "x", "cdiv").get(0, {})
    vals = [v for c, v in agrup.items() if bots.get(c, "humano") == "humano"]
    st = ep.agg_stats(vals)
    return float(st["mediana"]) if st["mediana"] != "" else None


series = {}
for tipo, vs in ventanas.items():
    orig, sin, n_doc = {}, {}, {}
    for pnum, fi, ff in vs:
        a, b = np.searchsorted(ts, fi.timestamp(), "left"), np.searchsorted(ts, ff.timestamp(), "left")
        idx = list(range(a, b))
        orig[pnum] = mediana_cdiv(idx)
        sin[pnum] = mediana_cdiv([i for i in idx if not solo_doc[i]])
        n_doc[pnum] = (int(solo_doc[a:b].sum()), b - a)
    series[tipo] = (orig, sin, n_doc)
    print(f"{tipo}: {len(vs)} ventanas")

# ── 4. comparación con lo que hay en el análisis y correlación con el mismo método del cruce ──
var_dict, datos = gp.cargar_datos()
size_e = datos.get("activos_interaccion_conteo", {}).get("versiones", {})


def reemplazar(base, nuevos):
    return {p: (t[0], nuevos.get(p), *t[2:]) for p, t in base.items() if nuevos.get(p) is not None}


chequeo = {}
for tipo in ("versiones", "versiones_canary"):
    base = datos["cdiv_mediana"][tipo]
    comunes = [p for p in base if base[p][1] is not None and series[tipo][0].get(p) is not None]
    a = np.array([base[p][1] for p in comunes]); b = np.array([series[tipo][0][p] for p in comunes])
    chequeo[tipo] = dict(n=len(comunes), iguales=float(np.mean(np.isclose(a, b))), corr=float(np.corrcoef(a, b)[0, 1]))
print("réplica del cálculo original (CDIV mediana recalculada vs. la del análisis):", chequeo)

y = "commits_doc_producto"
resultados = {}
for nombre, x_e, x_c in [
    ("cdiv_mediana (análisis)", datos["cdiv_mediana"]["versiones"], datos["cdiv_mediana"]["versiones_canary"]),
    ("cdiv_mediana recalculada, todos los commits", reemplazar(datos["cdiv_mediana"]["versiones"], series["versiones"][0]),
     reemplazar(datos["cdiv_mediana"]["versiones_canary"], series["versiones_canary"][0])),
    ("cdiv_mediana sin commits solo de documentación", reemplazar(datos["cdiv_mediana"]["versiones"], series["versiones"][1]),
     reemplazar(datos["cdiv_mediana"]["versiones_canary"], series["versiones_canary"][1])),
]:
    pr = cd.evaluar_par(x_e, datos[y]["versiones"], x_c, datos[y]["versiones_canary"], size_e, True)
    resultados[nombre] = {k: (None if isinstance(v, float) and np.isnan(v) else round(float(v), 4))
                          for k, v in pr.items() if k in ("n", "rho_cruda", "rho_corregida", "ic_inf", "ic_sup", "p_corregida",
                                                          "rho_canary", "rho_corregida_tamano", "rho_2016_2019",
                                                          "rho_2020_2022", "rho_2023_2024", "rho_2025_2026")}
    resultados[nombre]["estable"] = bool(pr["estable"])

for k, v in resultados.items():
    print(f"\n{k}\n   " + "  ".join(f"{kk}={vv}" for kk, vv in v.items()))

# ── 5. salidas (solo en la carpeta de validación) ──
with open(SALIDA / "cdiv_sin_doc_por_ventana.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["serie", "periodo_num", "cdiv_mediana_todos", "cdiv_mediana_sin_doc", "commits_solo_doc", "commits"])
    for tipo, (orig, sin, n_doc) in series.items():
        for p in sorted(orig):
            w.writerow([tipo, p, orig[p], sin[p], *n_doc[p]])
json.dump({"chequeo": chequeo, "resultados": resultados,
           "commits_solo_doc": int(solo_doc.sum()), "commits": len(commits)},
          open(SALIDA / "resumen.json", "w"), ensure_ascii=False, indent=2)
print(f"\nSalidas en {SALIDA}")
