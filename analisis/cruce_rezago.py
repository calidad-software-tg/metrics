"""
Cruce Proceso–Producto con rezago: X en la ventana t contra Y en la ventana t+k (k = 1, 2, 3).

Usa las funciones del método común (generar_correlaciones / cruce_dimensiones):
correlación parcial de Spearman (tiempo y duración), n efectiva, Benjamini–Hochberg sobre
todos los pares con rezago, signo en los cuatro períodos, réplica en canary y control por
tamaño. Diferencias con el cruce sin rezago:
  - se controla la duración de las dos ventanas (la de X y la de Y, que son distintas);
  - el control por tamaño usa las personas activas de las dos ventanas;
  - en canary el rezago se mide en tiempo equivalente: k ventanas estables ≈ k·r ventanas
    canary, con r = duración mediana estable / duración mediana canary.
Corre las dos direcciones (Proceso → Producto y Producto → Proceso).
"""
import json, sys, math, warnings, csv
from pathlib import Path
import numpy as np

W = Path(sys.argv[1]); CFG = Path(sys.argv[2]); OUT = Path(sys.argv[3])
sys.path.insert(0, str(W / "analisis"))
import generar_correlaciones as gc
import generar_pca as gp
import cruce_dimensiones as cd

warnings.filterwarnings("ignore")
cfg = cd.mezclar(cd.DEFAULTS, json.loads(CFG.read_text(encoding="utf-8")))
var_dict, datos = gp.cargar_datos()
lados, _ = cd.armar_lados("Proceso", "Producto", var_dict, cfg)
size = {s: datos.get("activos_interaccion_conteo", {}).get(s, {}) for s in ("versiones", "versiones_canary")}

dur = {s: {} for s in ("versiones", "versiones_canary")}
for v in datos:
    if v.startswith("__"):
        continue
    for s in dur:
        for p, t in datos[v].get(s, {}).items():
            if t[0] is not None:
                dur[s].setdefault(p, t[0])
orden = {s: sorted(dur[s]) for s in dur}
r = np.median(list(dur["versiones"].values())) / np.median(list(dur["versiones_canary"].values()))

cps = {d: cd.componentes(d, cfg, dur) for d in ("Proceso", "Producto")}
series = {}
for d in ("Proceso", "Producto"):
    for v in lados[d]:
        series[v] = (d, var_dict[v]["nombre_legible"].split(" [")[0], datos[v]["versiones"], datos[v]["versiones_canary"])
    for c in cps[d]:
        series[c["id"]] = (d, cd.nombre_cp(c, cfg["carga_minima"]), c["estable"], c["canary_serie"])

def filas(xs, ys, serie, k):
    o = orden[serie]; out = []
    for i in range(len(o) - k):
        p, q = o[i], o[i + k]
        if p in xs and q in ys and xs[p][1] is not None and ys[q][1] is not None:
            out.append(dict(p=p, x=xs[p][1], y=ys[q][1], dx=dur[serie].get(p) or 1.0, dy=dur[serie].get(q) or 1.0,
                            anio=xs[p][2], sx=size[serie].get(p, (None, None))[1], sy=size[serie].get(q, (None, None))[1]))
    return out

def parcial(fs, tam=False):
    if len(fs) < 15:
        return dict(rho_corr=np.nan, p_corr=np.nan, ic_inf=np.nan, ic_sup=np.nan, n_efectiva=np.nan)
    extra = [[gc.safe_log(f["dy"]) for f in fs]]
    if tam:
        fs2 = [f for f in fs if f["sx"] is not None and f["sy"] is not None]
        if len(fs2) < 15:
            return dict(rho_corr=np.nan)
        fs = fs2
        extra = [[gc.safe_log(f["dy"]) for f in fs], [gc.safe_log(f["sx"] + 1) for f in fs], [gc.safe_log(f["sy"] + 1) for f in fs]]
    return gc.partial_spearman([f["x"] for f in fs], [f["y"] for f in fs], [f["p"] for f in fs],
                               [f["dx"] for f in fs], extra_controls=extra)

def evaluar(xid, yid, k):
    _, _, xe, xc = series[xid]; _, _, ye, yc = series[yid]
    fe = filas(xe, ye, "versiones", k)
    ps = parcial(fe)
    per = {}
    for label, y0, y1 in gc.ETAPAS:
        sub = [f for f in fe if f["anio"] is not None and y0 <= f["anio"] <= y1]
        if len(sub) >= 15:
            per[label] = parcial(sub)["rho_corr"]
    kc = max(1, int(round(k * r)))
    fc = filas(xc, yc, "versiones_canary", kc) if xc and yc else []
    can = parcial(fc)["rho_corr"] if fc else np.nan
    tam = parcial(fe, tam=True)["rho_corr"]
    return dict(x_id=xid, y_id=yid, x=series[xid][1], y=series[yid][1], x_dim=series[xid][0], k=k, kc=kc,
                n=len(fe), rho=ps["rho_corr"], p=ps["p_corr"], ic_inf=ps.get("ic_inf"), ic_sup=ps.get("ic_sup"),
                n_ef=ps.get("n_efectiva"), canary=can, tamano=tam,
                **{"rho_" + l.replace("-", "_"): per.get(l, np.nan) for l, *_ in gc.ETAPAS})

res = []
for k in (0, 1, 2, 3):
    for a, b in (("Proceso", "Producto"), ("Producto", "Proceso")):
        if k == 0 and a == "Producto":
            continue
        xs = list(lados[a]) + [c["id"] for c in cps[a]]
        ys = list(lados[b]) + [c["id"] for c in cps[b]]
        for x in xs:
            for y in ys:
                if (x in lados[a]) != (y in lados[b]):
                    continue        # variables con variables, componentes con componentes
                res.append(evaluar(x, y, k))

# Benjamini–Hochberg sobre todos los pares con rezago (k >= 1); k = 0 aparte, como control
for grupo in ([e for e in res if e["k"] >= 1], [e for e in res if e["k"] == 0]):
    ok = [e for e in grupo if isinstance(e["p"], float) and not math.isnan(e["p"])]
    ps = sorted(range(len(ok)), key=lambda i: ok[i]["p"]); m = len(ok); prev = 1.0
    for rank, i in reversed(list(enumerate(ps, start=1))):
        prev = min(prev, ok[i]["p"] * m / rank); ok[i]["p_fdr"] = prev
for e in res:
    e.setdefault("p_fdr", np.nan)
    per = [e["rho_" + l.replace("-", "_")] for l, *_ in gc.ETAPAS]
    per = [v for v in per if isinstance(v, float) and not math.isnan(v)]
    e["estable"] = len(per) >= 3 and all((v >= 0) == (e["rho"] >= 0) for v in per)
    e["sig"] = isinstance(e["p_fdr"], float) and e["p_fdr"] < 0.05
    e["robusta"] = bool(e["sig"] and e["estable"] and gc.replica_en_canary(e["rho"], e["canary"]))
    e["resiste_tamano"] = gc.resiste_tamano(e["rho"], e["tamano"])

OUT.mkdir(parents=True, exist_ok=True)
cols = list(res[0].keys())
with open(OUT / "pares_rezago.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(res)
print(f"razón duración estable/canary: {r:.1f}")
for k in (0, 1, 2, 3):
    for a in ("Proceso", "Producto"):
        g = [e for e in res if e["k"] == k and e["x_dim"] == a]
        if g:
            print(f"k={k} {a}→: {len(g)} pares · significativos {sum(e['sig'] for e in g)} · robustos {sum(e['robusta'] for e in g)} · "
                  f"robustos que resisten tamaño {sum(bool(e['robusta'] and e['resiste_tamano']) for e in g)}")
