"""Validación del patrón A de Persona: LE, Development Experience, CDIV y REXP (medianas) ↔ tasa de ingreso (commits) y
proporción que commitea, sin los recién llegados. Sin tocar la base.

Mismo cálculo que experiencia_sin_recien_llegados.py: se rehacen las medianas de LE y Development Experience
sacando a quienes commitean por primera vez en la ventana y se repite la correlación con la tasa de ingreso y
la proporción que commitea, que no cambian (siguen contando a los nuevos). La pregunta es si, cuando entra más
gente nueva, también tienen menos experiencia los que ya estaban.
  1. todos los colaboradores (réplica del análisis, para validar el cálculo);
  2. sin los recién llegados.
Solo lee la base (conexión readonly), el clon y los CSV del análisis; escribe únicamente en la carpeta de salida.

Uso (desde la raíz del repo):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/experiencia_ingreso_sin_recien_llegados.py [carpeta_salida]

Por defecto escribe en analisis/salidas/validaciones/experiencia_ingreso_sin_recien_llegados/.
"""
import csv
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path.cwd()
for p in (ROOT, ROOT / "analisis", ROOT / "16"):
    sys.path.insert(0, str(p))

import numpy as np
import psycopg2

import export_persona as ep
import generar_correlaciones as gc
import generar_pca as gp
import cruce_dimensiones as cd
from base_metric import es_bot
from dloc import es_documentacion

SALIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "analisis" / "salidas" / "validaciones" / "experiencia_ingreso_sin_recien_llegados"
SALIDA.mkdir(parents=True, exist_ok=True)
CLON = ROOT / ".clones" / "next.js"

ep.load_alias()
bots = ep.load_bots()

con = psycopg2.connect(**gc.DB)
con.set_session(readonly=True)
cur = con.cursor()
cur.execute("SELECT repo_id FROM repos WHERE full_name = 'vercel/next.js'")
repo_id = cur.fetchone()[0]

# ventanas y primera ventana de commits de cada persona (igual que export_persona)
ventanas, pf = {}, {}
for serie in ("versiones", "versiones_canary"):
    cur.execute("SELECT periodo_id, periodo_num, fecha_inicio, fecha_fin FROM periodo WHERE repo_id = %s AND tipo_analisis = %s",
                (repo_id, serie))
    ventanas[serie] = {pid: (pnum, fi, ff) for pid, pnum, fi, ff in cur.fetchall()}
    pf[serie] = ep.primera_fecha_lookup(cur, ep.METRICAS_COMMITS, serie)


def leer(serie, metrica):
    cur.execute("""SELECT r.periodo_id, r.contribuyente_login, r.value FROM resultado r
                   JOIN periodo p ON p.periodo_id = r.periodo_id
                   WHERE p.repo_id = %s AND p.tipo_analisis = %s AND r.metrica_id = %s
                     AND r.contribuyente_login IS NOT NULL""", (repo_id, serie, metrica))
    return cur.fetchall()


crudos = {s: {m: leer(s, m) for m in ("le", "dev_exp", "anmcc", "cdiv", "rexp")} for s in ventanas}
con.close()

# ANMCC por persona sin los commits que solo tocan documentación, desde el clon
out = subprocess.run(["git", "-C", str(CLON), "log", "origin/HEAD", "--no-merges", "--numstat", "--date=iso-strict",
                      "--pretty=format:\x01%an\x01%cI"], capture_output=True, text=True, check=True).stdout
commits, actual = [], None
for linea in out.splitlines():
    if linea.startswith("\x01"):
        if actual:
            commits.append(actual)
        _, autor, fecha = linea.split("\x01")
        from datetime import datetime
        actual = {"author": autor.strip() or "desconocido", "ts": datetime.fromisoformat(fecha).timestamp(), "files": []}
    elif linea.strip() and actual is not None:
        partes = linea.split("\t")
        if len(partes) == 3:
            actual["files"].append(partes[2])
if actual:
    commits.append(actual)
commits.sort(key=lambda c: c["ts"])
ts = np.array([c["ts"] for c in commits])


@__import__('functools').lru_cache(maxsize=None)
def anmcc_sin_doc(serie):
    filas = []
    for pid, (pnum, fi, ff) in ventanas[serie].items():
        a, b = np.searchsorted(ts, fi.timestamp()), np.searchsorted(ts, ff.timestamp())
        por_autor = defaultdict(list)
        for c in commits[a:b]:
            if es_bot(c["author"]) or not c["files"] or all(es_documentacion(f) for f in c["files"]):
                continue
            por_autor[c["author"]].append(len(c["files"]))
        filas += [(pid, aut, round(sum(v) / len(v), 2)) for aut, v in por_autor.items()]
    return filas


def medianas(serie, metrica, crudo, sin_nuevos):
    """{periodo_num: mediana} con la misma regla que export_persona."""
    activos = defaultdict(set)
    for pid, lg, _ in crudos[serie]["anmcc"]:
        activos[pid].add(ep.canon(lg, "anmcc"))
    if metrica == "dev_exp":
        crudo = [(pid, lg, v) for pid, lg, v in crudo if ep.canon(lg, "dev_exp") in activos.get(pid, ())]
    agr = ep._agrupar_con_dedupe(crudo, [], serie, metrica)
    res = {}
    for pid, vals in agr.items():
        if pid not in ventanas[serie]:
            continue
        pnum, _, ff = ventanas[serie][pid]
        fin = ep.fmt_ts(ff)
        xs = [v for c, v in vals.items() if bots.get(c, "humano") == "humano" and not (sin_nuevos and pf[serie].get(c) == fin)]
        st = ep.agg_stats(xs)
        if st["mediana"] != "":
            res[pnum] = float(st["mediana"])
    return res


var_dict, datos = gp.cargar_datos()
size_e = datos.get("activos_interaccion_conteo", {}).get("versiones", {})
ID = {"le": "le_mediana", "dev_exp": "dev_exp_mediana", "anmcc": "anmcc_mediana", "cdiv": "cdiv_mediana",
      "rexp": "rexp_mediana"}


from functools import lru_cache


@lru_cache(maxsize=None)
def serie_var(metrica, sin_nuevos, anmcc_doc=False):
    out = {}
    for serie in ("versiones", "versiones_canary"):
        crudo = anmcc_sin_doc(serie) if anmcc_doc else crudos[serie][metrica]
        nuevos = medianas(serie, metrica, crudo, sin_nuevos)
        base = datos[ID[metrica]][serie]
        out[serie] = {p: (t[0], nuevos[p], *t[2:]) for p, t in base.items() if p in nuevos}
    return out


# réplica del cálculo original
chequeo = {}
for m in ID:
    s = serie_var(m, False)
    base = datos[ID[m]]["versiones"]
    comunes = [p for p in base if base[p][1] is not None and p in s["versiones"]]
    a = np.array([base[p][1] for p in comunes]); b = np.array([s["versiones"][p][1] for p in comunes])
    chequeo[m] = dict(n=len(comunes), iguales=round(float(np.mean(np.isclose(a, b))), 4), corr=round(float(np.corrcoef(a, b)[0, 1]), 5))
print("réplica de las medianas del análisis:", chequeo)

CLAVES = ("n", "rho_corregida", "ic_inf", "ic_sup", "rho_corregida_tamano", "rho_2016_2019", "rho_2020_2022",
          "rho_2023_2024", "rho_2025_2026", "rho_canary")
# la tasa de ingreso y la proporción que commitea no cambian: siguen contando a los nuevos
OTRAS = ("tasa_nuevos_commits_ratio", "prop_commitean_ratio")
resultados = {}
for nom, sin_nuevos in (("1. como en el análisis (recalculado)", False), ("2. sin recién llegados", True)):
    for xm in ("le", "dev_exp", "cdiv", "rexp"):
        x = serie_var(xm, sin_nuevos)
        for yv in OTRAS:
            y = datos[yv]
            pr = cd.evaluar_par(x["versiones"], y["versiones"], x["versiones_canary"], y["versiones_canary"], size_e, True)
            r = {k: (None if isinstance(pr[k], float) and np.isnan(pr[k]) else round(float(pr[k]), 3)) for k in CLAVES}
            r["estable"] = bool(pr["estable"])
            resultados[f"{nom} · {ID[xm]} ↔ {yv}"] = r
            print(f"\n{nom} · {ID[xm]} ↔ {yv}\n   " + "  ".join(f"{k}={val}" for k, val in r.items()))

# las medianas de experiencia entre sí, recalculando las dos sin los recién llegados
for nom, sin_nuevos in (("1. como en el análisis (recalculado)", False), ("2. sin recién llegados", True)):
    for xm, ym in (("cdiv", "le"), ("cdiv", "dev_exp"), ("cdiv", "rexp"), ("le", "rexp")):
        x, y = serie_var(xm, sin_nuevos), serie_var(ym, sin_nuevos)
        pr = cd.evaluar_par(x["versiones"], y["versiones"], x["versiones_canary"], y["versiones_canary"], size_e, True)
        r = {k: (None if isinstance(pr[k], float) and np.isnan(pr[k]) else round(float(pr[k]), 3)) for k in CLAVES}
        r["estable"] = bool(pr["estable"])
        resultados[f"{nom} · {ID[xm]} ↔ {ID[ym]}"] = r
        print(f"\n{nom} · {ID[xm]} ↔ {ID[ym]}\n   " + "  ".join(f"{k}={val}" for k, val in r.items()))

# cuánta gente nueva hay por ventana, para contexto
nuevos_por_ventana = []
for pid, (pnum, _, ff) in ventanas["versiones"].items():
    fin = ep.fmt_ts(ff)
    act = {ep.canon(lg, "anmcc") for p2, lg, _ in crudos["versiones"]["anmcc"] if p2 == pid}
    act = {c for c in act if bots.get(c, "humano") == "humano"}
    if act:
        nuevos_por_ventana.append(sum(1 for c in act if pf["versiones"].get(c) == fin) / len(act))
json.dump({"chequeo": chequeo, "resultados": resultados,
           "proporcion_nuevos_mediana": round(float(np.median(nuevos_por_ventana)), 3)},
          open(SALIDA / "resumen.json", "w"), ensure_ascii=False, indent=2)
print(f"\nproporción mediana de recién llegados entre quienes commitean: {np.median(nuevos_por_ventana):.1%}")
print(f"Salidas en {SALIDA}")
