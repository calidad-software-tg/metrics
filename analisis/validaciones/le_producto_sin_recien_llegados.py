"""Validación de Learning Ease del proyecto (le_producto) ↔ concentración del núcleo, sin los recién llegados. Sin tocar la base.

LE del proyecto es, en cada ventana, el promedio sobre los pares (autor, componente) con commits en la ventana de los
días entre la primera contribución del autor a ese componente (en toda la historia) y la última en la ventana
(15/le.py). Quien commitea por primera vez aporta pares con LE cercano a cero, igual que en las medianas de
experiencia que se descartaron sin los recién llegados (experiencia_ingreso_sin_recien_llegados.py). Acá se rehace
le_producto desde el clon con el mismo cálculo que run_versiones_local.py y se repite la correlación con las medidas
de concentración del núcleo, que no cambian:
  1. todos los autores (réplica del valor de la base, para validar el cálculo);
  2. sin los autores cuyo primer commit en el proyecto cae en la ventana.
Solo lee la base (conexión readonly), el clon y los CSV del análisis; escribe únicamente en la carpeta de salida.

Uso (desde la raíz del repo):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/le_producto_sin_recien_llegados.py [carpeta_salida]

Por defecto escribe en analisis/salidas/validaciones/le_producto_sin_recien_llegados/.
"""
import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path.cwd()
for p in (ROOT, ROOT / "analisis", ROOT / "15"):
    sys.path.insert(0, str(p))

import numpy as np
import psycopg2

import generar_correlaciones as gc
import generar_pca as gp
import cruce_dimensiones as cd
from base_metric import es_bot
from le import componente_de

SALIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "analisis" / "salidas" / "validaciones" / "le_producto_sin_recien_llegados"
SALIDA.mkdir(parents=True, exist_ok=True)
CLON = ROOT / ".clones" / "next.js"

con = psycopg2.connect(**gc.DB)
con.set_session(readonly=True)
cur = con.cursor()
cur.execute("SELECT repo_id FROM repos WHERE full_name = 'vercel/next.js'")
repo_id = cur.fetchone()[0]
ventanas = {}
for serie in ("versiones", "versiones_canary"):
    cur.execute("SELECT periodo_num, fecha_inicio, fecha_fin FROM periodo WHERE repo_id = %s AND tipo_analisis = %s",
                (repo_id, serie))
    ventanas[serie] = {pnum: (fi, ff) for pnum, fi, ff in cur.fetchall()}
con.close()

# toda la historia, como commits_en_ventana() de run_versiones_local.py: autor y fecha de autor, ventana por fecha de commit
out = subprocess.run(["git", "-C", str(CLON), "log", "origin/HEAD", "--no-merges", "--name-only", "--date=iso-strict",
                      "--pretty=format:\x01%an\x01%aI\x01%cI"], capture_output=True, text=True, check=True).stdout
commits, actual = [], None
for linea in out.splitlines():
    if linea.startswith("\x01"):
        if actual:
            commits.append(actual)
        _, autor, fa, fc = linea.split("\x01")
        actual = {"author": autor.strip() or "desconocido", "ts": datetime.fromisoformat(fa),
                  "tc": datetime.fromisoformat(fc).timestamp(), "files": []}
    elif linea.strip() and actual is not None:
        actual["files"].append(linea.strip())
if actual:
    commits.append(actual)
commits.sort(key=lambda c: c["tc"])
tc = np.array([c["tc"] for c in commits])

primera_par, primer_commit = {}, {}
for c in commits:
    a = c["author"]
    if a not in primer_commit or c["tc"] < primer_commit[a]:
        primer_commit[a] = c["tc"]
    for f in c["files"]:
        par = (a, componente_de(f))
        if par not in primera_par or c["ts"] < primera_par[par]:
            primera_par[par] = c["ts"]


def le_ventana(fi, ff, sin_nuevos):
    a, b = np.searchsorted(tc, fi.timestamp()), np.searchsorted(tc, ff.timestamp())
    ultima = {}
    for c in commits[a:b]:
        if es_bot(c["author"]):
            continue
        if sin_nuevos and fi.timestamp() <= primer_commit[c["author"]] < ff.timestamp():
            continue
        for f in c["files"]:
            par = (c["author"], componente_de(f))
            ultima[par] = max(ultima.get(par, c["ts"]), c["ts"])
    if not ultima:
        return None
    dias = [(ts - min(ts, primera_par[par])).days for par, ts in ultima.items()]
    return round(sum(dias) / len(dias), 2)


var_dict, datos = gp.cargar_datos()
size_e = datos.get("activos_interaccion_conteo", {}).get("versiones", {})


def serie_le(sin_nuevos):
    res = {}
    for serie in ("versiones", "versiones_canary"):
        base = datos["le_producto"][serie]
        vals = {p: le_ventana(*ventanas[serie][p], sin_nuevos) for p in base if p in ventanas[serie]}
        res[serie] = {p: (t[0], vals[p], *t[2:]) for p, t in base.items() if vals.get(p) is not None}
    return res


todos, sin = serie_le(False), serie_le(True)
base = datos["le_producto"]["versiones"]
comunes = [p for p in base if base[p][1] is not None and p in todos["versiones"]]
a = np.array([base[p][1] for p in comunes]); b = np.array([todos["versiones"][p][1] for p in comunes])
chequeo = dict(n=len(comunes), iguales=round(float(np.mean(np.isclose(a, b, atol=0.01))), 4),
               corr=round(float(np.corrcoef(a, b)[0, 1]), 5))
print("réplica de le_producto:", chequeo)

CLAVES = ("n", "rho_corregida", "ic_inf", "ic_sup", "rho_corregida_tamano", "rho_2016_2019", "rho_2020_2022",
          "rho_2023_2024", "rho_2025_2026", "rho_canary")
OTRAS = ("exprev_share_top10pct", "nc_share_top10pct", "nc_p90", "tasa_nuevos_commits_ratio", "prop_commitean_ratio")
resultados = {}
for nom, x in (("1. como en el análisis (recalculado)", todos), ("2. sin recién llegados", sin)):
    for yv in OTRAS:
        y = datos[yv]
        pr = cd.evaluar_par(x["versiones"], y["versiones"], x["versiones_canary"], y["versiones_canary"], size_e, True)
        r = {k: (None if isinstance(pr[k], float) and np.isnan(pr[k]) else round(float(pr[k]), 3)) for k in CLAVES}
        r["estable"] = bool(pr["estable"])
        resultados[f"{nom} · le_producto ↔ {yv}"] = r
        print(f"\n{nom} · le_producto ↔ {yv}\n   " + "  ".join(f"{k}={val}" for k, val in r.items()))

json.dump({"chequeo": chequeo, "resultados": resultados}, open(SALIDA / "resumen.json", "w"), ensure_ascii=False, indent=2)
print(f"\nSalidas en {SALIDA}")
