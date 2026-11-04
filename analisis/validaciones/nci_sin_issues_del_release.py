"""Validación de la familia «resolver lo nuevo y cerrar lo viejo» de Proceso: NCI ↔ Jarczyk y Process Performance.

Una issue que se abre y se cierra dentro de la misma ventana suma un cierre en NCI y un éxito en el numerador de
Jarczyk (y de Process Performance, si se cerró en 3 días o menos). Se recalcula NCI por ventana con la misma regla
que 35/nci.py (cierres en la ventana, sin los de bots) en tres versiones:
  1. todos los cierres (réplica del análisis, para validar el cálculo);
  2. sin las issues creadas en la misma ventana: solo el cierre de lo que ya estaba abierto;
  3. solo las issues creadas en la misma ventana;
y se repite la correlación con Jarczyk, Process Performance, MTTR y DIS con la función de los cruces (evaluar_par).
Descarga las issues de la API de GitHub (solo lectura, GITHUB_TOKEN del .env); lee la base en modo de solo lectura y
escribe únicamente en la carpeta de salida.

Uso (desde la raíz del repo):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/nci_sin_issues_del_release.py [carpeta_salida]

Por defecto escribe en analisis/salidas/validaciones/nci_sin_issues_del_release/.
"""
import json
import os
import sys
import warnings
from datetime import timezone
from pathlib import Path

ROOT = Path.cwd()
for p in (ROOT, ROOT / "analisis", ROOT / "35"):
    sys.path.insert(0, str(p))
env = ROOT / ".env"
if env.exists():
    for linea in env.read_text().splitlines():
        if "=" in linea and not linea.lstrip().startswith("#"):
            k, v = linea.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import numpy as np
import psycopg2

import generar_correlaciones as gc
import generar_pca as gp
import cruce_dimensiones as cd
from base_metric import es_bot
from issues_comun import descargar_issues
from nci import NumberOfClosedIssues

warnings.filterwarnings("ignore")
SALIDA = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "analisis" / "salidas" / "validaciones" / "nci_sin_issues_del_release"
SALIDA.mkdir(parents=True, exist_ok=True)

con = psycopg2.connect(**gc.DB)
con.set_session(readonly=True)
cur = con.cursor()
cur.execute("SELECT repo_id FROM repos WHERE full_name = 'vercel/next.js'")
repo_id = cur.fetchone()[0]
ventanas = {}
for serie in ("versiones", "versiones_canary"):
    cur.execute("SELECT periodo_num, fecha_inicio, fecha_fin FROM periodo WHERE repo_id = %s AND tipo_analisis = %s",
                (repo_id, serie))
    ventanas[serie] = {pnum: tuple(f if f.tzinfo else f.replace(tzinfo=timezone.utc) for f in (fi, ff))
                       for pnum, fi, ff in cur.fetchall()}
con.close()

metrica = NumberOfClosedIssues(os.environ["GITHUB_TOKEN"], "vercel", "next.js")
issues = [i for i in descargar_issues(metrica) if i["closed_at"] and not es_bot(i["closed_by"] or "desconocido")]
issues.sort(key=lambda i: i["closed_at"])
cierres = np.array([i["closed_at"].timestamp() for i in issues])
print(f"{len(issues)} issues cerradas por personas")


def contar(serie, version):
    """{periodo_num: NCI} con la versión pedida."""
    out = {}
    for pnum, (fi, ff) in ventanas[serie].items():
        a, b = np.searchsorted(cierres, fi.timestamp()), np.searchsorted(cierres, ff.timestamp(), side="right")
        del_release = sum(1 for i in issues[a:b] if i["created_at"] >= fi)
        out[pnum] = {"todas": b - a, "sin_del_release": b - a - del_release, "solo_del_release": del_release}[version]
    return out


var_dict, datos = gp.cargar_datos()
size_e = datos.get("activos_interaccion_conteo", {}).get("versiones", {})


def serie_nci(version):
    out = {}
    for serie in ("versiones", "versiones_canary"):
        nuevos = contar(serie, version)
        base = datos["nci_producto"][serie]
        out[serie] = {p: (t[0], float(nuevos[p]), *t[2:]) for p, t in base.items() if p in nuevos}
    return out


# réplica del cálculo original
s = serie_nci("todas")
base = datos["nci_producto"]["versiones"]
comunes = [p for p in base if base[p][1] is not None and p in s["versiones"]]
a = np.array([base[p][1] for p in comunes])
b = np.array([s["versiones"][p][1] for p in comunes])
chequeo = dict(n=len(comunes), iguales=round(float(np.mean(np.isclose(a, b))), 4), corr=round(float(np.corrcoef(a, b)[0, 1]), 5))
print("réplica de NCI del análisis:", chequeo)

proporcion = [s2 / t for t, s2 in zip(contar("versiones", "todas").values(), contar("versiones", "solo_del_release").values()) if t]
print(f"proporción mediana de cierres que son issues del mismo release: {np.median(proporcion):.1%}")

CLAVES = ("n", "rho_corregida", "ic_inf", "ic_sup", "rho_corregida_tamano", "rho_2016_2019", "rho_2020_2022",
          "rho_2023_2024", "rho_2025_2026", "rho_canary")
OTRAS = ("jarczyk_success_rate_producto", "process_performance_producto", "mttr_producto", "dis_producto")
resultados = {}
for nom, version in (("1. todos los cierres (recalculado)", "todas"), ("2. sin las issues creadas en el release", "sin_del_release"),
                     ("3. solo las issues creadas en el release", "solo_del_release")):
    x = serie_nci(version)
    for yv in OTRAS:
        y = datos[yv]
        pr = cd.evaluar_par(x["versiones"], y["versiones"], x["versiones_canary"], y["versiones_canary"], size_e, True)
        r = {k: (None if isinstance(pr[k], float) and np.isnan(pr[k]) else round(float(pr[k]), 3)) for k in CLAVES}
        r["estable"] = bool(pr["estable"])
        resultados[f"{nom} · nci_producto ↔ {yv}"] = r
        print(f"\n{nom} · nci_producto ↔ {yv}\n   " + "  ".join(f"{k}={val}" for k, val in r.items()))

json.dump({"chequeo": chequeo, "proporcion_del_release_mediana": round(float(np.median(proporcion)), 3),
           "resultados": resultados}, open(SALIDA / "resumen.json", "w"), ensure_ascii=False, indent=2)
print(f"\nSalidas en {SALIDA}")
