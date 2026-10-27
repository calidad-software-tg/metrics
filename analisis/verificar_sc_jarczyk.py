"""
Verificación del Patrón 3: SC (mediana) ↔ Jarczyk.

SC de cada persona = PRs abiertos + issues abiertas + PRs abiertos que se cerraron + PRs
abiertos que se mergearon + issues abiertas que se cerraron en la ventana (value_extra).
La última parte son issues creadas y cerradas en la misma ventana: las mismas que cuenta
Jarczyk en su numerador. Se recalcula la mediana por release (humanos, mismas reglas que
export_persona.py) con tres versiones y se correlaciona cada una con Jarczyk con el método
común (cruce_dimensiones.evaluar_par: parcial, períodos, canary y control por tamaño).
Solo lectura de la base.
"""
import os, sys, json, math, warnings
from pathlib import Path
from collections import defaultdict
import numpy as np
W = Path(sys.argv[1])
sys.path.insert(0, str(W)); sys.path.insert(0, str(W / "analisis"))
os.chdir(W)
import export_persona as ep
import generar_correlaciones as gc
import generar_pca as gp
import cruce_dimensiones as cd
import psycopg2
warnings.filterwarnings("ignore")

con = psycopg2.connect(**ep.DB); con.set_session(readonly=True); cur = con.cursor()
bots = ep.load_bots()
ESTAD = sys.argv[2] if len(sys.argv) > 2 else "mediana"
print("estadístico:", ESTAD)
VERS = {
    "sc_original": lambda e: e["sc"],
    "sc_sin_issues_propias_cerradas": lambda e: e["sc"] - e.get("issues_opened_closed", 0),
    "sc_solo_aperturas": lambda e: e.get("issues_opened", 0) + e.get("prs_opened", 0),
    "solo_issues_propias_cerradas": lambda e: e.get("issues_opened_closed", 0),
    "sc_sin_prs_cerrados_ni_mergeados": lambda e: e["sc"] - e.get("prs_opened_closed", 0) - e.get("prs_opened_merged", 0),
}
series = {k: {"versiones": {}, "versiones_canary": {}} for k in VERS}
peso = {"versiones": [], "versiones_canary": []}
excl = tuple(ep.EXCLUIR_ESTABLE)
for serie in ("versiones", "versiones_canary"):
    q = """SELECT p.periodo_num, r.contribuyente_login, r.value_extra
           FROM resultado r JOIN periodo p ON p.periodo_id = r.periodo_id
           WHERE p.tipo_analisis = %s AND r.metrica_id = 'sc' AND r.contribuyente_login IS NOT NULL"""
    params = [serie]
    if serie == "versiones" and excl:
        q += " AND p.etiqueta NOT IN %s"; params.append(excl)
    cur.execute(q, params)
    por = defaultdict(dict)
    for pnum, lg, ex in cur.fetchall():
        c = ep.canon(lg, "sc")
        if bots.get(c, "humano") != "humano" or not ex:
            continue
        por[pnum][c] = ex                      # SC es de API: una fila por login
    for pnum, personas in por.items():
        tot = sum(e["sc"] for e in personas.values())
        prop = sum(e.get("issues_opened_closed", 0) for e in personas.values())
        if tot: peso[serie].append(prop / tot)
        for k, fn in VERS.items():
            s = sorted(fn(e) for e in personas.values())
            n = len(s); med = (s[n // 2 - 1] + s[n // 2]) / 2 if n % 2 == 0 else s[n // 2]
            series[k][serie][pnum] = med if ESTAD == "mediana" else sum(s) / n

var_dict, datos = gp.cargar_datos()
ref = datos["sc_mediana"]
size_e = datos.get("activos_interaccion_conteo", {}).get("versiones", {})
jar = datos["jarczyk_success_rate_producto"]

# validación: la versión original tiene que dar igual que sc_mediana del análisis
dif = [abs(series["sc_original"]["versiones"][p] - t[1]) for p, t in ref["versiones"].items()
       if t[1] is not None and p in series["sc_original"]["versiones"]]
print(f"validación sc_original vs sc_mediana: {len(dif)} releases, máx. diferencia {max(dif):.4f}, iguales {sum(d < 1e-6 for d in dif)}")
print(f"parte de SC que son issues propias abiertas y cerradas en la ventana: mediana {np.median(peso['versiones']):.1%} (estables), {np.median(peso['versiones_canary']):.1%} (canary)")

def armar(k, serie):
    base = ref[serie]
    return {p: (t[0], series[k][serie].get(p), t[2], t[3], t[4]) for p, t in base.items() if p in series[k][serie]}

out = {}
for k in VERS:
    xe, xc = armar(k, "versiones"), armar(k, "versiones_canary")
    vals = [t[1] for t in xe.values() if t[1] is not None]
    moda = max(vals.count(v) for v in set(vals)) / len(vals)
    pr = cd.evaluar_par(xe, jar["versiones"], xc, jar["versiones_canary"], size_e, True)
    out[k] = dict(moda=moda, n=pr["n"], rho=pr["rho_corregida"], p=pr["p_corregida"], ic=(pr["ic_inf"], pr["ic_sup"]),
                  canary=pr["rho_canary"], tamano=pr["rho_corregida_tamano"],
                  periodos=[pr.get("rho_" + l.replace("-", "_")) for l, *_ in gc.ETAPAS])
for k, v in out.items():
    f = lambda x: "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:+.2f}"
    print(f"{k:32s} moda {v['moda']:.0%}  n {v['n']}  ρ {f(v['rho'])}  p {v['p']:.4f}  IC [{f(v['ic'][0])}, {f(v['ic'][1])}]  "
          f"períodos {[f(x) for x in v['periodos']]}  canary {f(v['canary'])}  tamaño {f(v['tamano'])}")
