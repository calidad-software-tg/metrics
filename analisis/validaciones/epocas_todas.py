"""
Épocas con todas las métricas juntas: ¿dónde cambia el proyecto si se mira todo a la vez, sin separar por dimensión?

clustering_temporal.py (A1) arma las épocas por dimensión y los cortes coinciden entre las tres. Este script
las arma una sola vez con todas las métricas incluidas (sin variantes), sin importar a qué dimensión están
mapeadas, y compara los cortes con los de cada dimensión.

Mismo procedimiento que A1: cada release estable es un punto, valores crudos (rangos estandarizados, sin
descontar la tendencia), Ward con restricción de contigüidad (solo se juntan releases vecinos), k = 2..6.
Los releases con un valor extremo (> 6 desvíos) quedan fuera, como en clustering_temporal.py.

Dos versiones de las variables:
    desde_2019  todas, con CFDR y NUB (los releases empiezan en 2019, como el PCA de Proceso y Producto)
    historia    todas menos CFDR y NUB (toda la historia)
y dos pesos:
    variable    cada variable pesa lo mismo (Persona, con más variables, pesa más)
    dimension   cada dimensión pesa lo mismo: bloques Persona / Proceso / Producto divididos por la raíz de su
                tamaño; una variable de dos dimensiones va a Persona si es de Persona y si no al lado que le
                asigna cruces/proceso_producto_asignado.json

Para cada corrida informa:
    R² de la segmentación (varianza entre épocas / total) frente a una nula en la que cada variable se corre
    en el tiempo por separado (conserva la forma de cada serie y rompe los cambios simultáneos);
    los cortes, el acuerdo (ARI) con las épocas de cada dimensión sola y con los períodos de calendario;
    la réplica en canary (mismos cortes en la serie canary).

Uso (desde la raíz del repo):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/epocas_todas.py [carpeta_salida]

Por defecto escribe en analisis/salidas/validaciones/epocas_todas/. Solo lee la base.
"""
import csv
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.sparse import diags
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import adjusted_rand_score

ROOT = Path.cwd()
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "analisis" / "salidas" / "validaciones" / "epocas_todas"
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "analisis"))
import generar_correlaciones as gc  # noqa: E402
import generar_pca as gp  # noqa: E402
warnings.filterwarnings("ignore")

rng = np.random.default_rng(gp.SEMILLA)
KS = range(2, 7)
N_NULA = 200
SOLO_DESDE_2019 = {"cfdr_producto", "nub_producto"}
ASIGNAR = json.loads((ROOT / "analisis" / "cruces" / "proceso_producto_asignado.json").read_text(encoding="utf-8"))["asignar"]
SERIES = {"estable": "versiones", "canary": "versiones_canary"}


def fecha(s):
    return datetime.strptime(str(s)[:8], "%Y%m%d")


def etapa(anio):
    for i, (_, a, b) in enumerate(gc.ETAPAS):
        if a <= anio <= b:
            return i
    return len(gc.ETAPAS) - 1


def escribir(nombre, filas):
    if not filas:
        return
    claves = list(dict.fromkeys(k for f in filas for k in f))
    with open(OUT / nombre, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=claves)
        w.writeheader()
        for f in filas:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in f.items()})


# ── datos ────────────────────────────────────────────────────────────────────

var_dict, datos = gp.cargar_datos()


def dims(v):
    t = var_dict[v]["dims_texto"]
    return set() if t in ("", "Sin dimensión") else set(t.split("+"))


def bloque(v):
    d = dims(v)
    if "Persona" in d:
        return "Persona"
    if len(d) == 1:
        return next(iter(d))
    return ASIGNAR.get(v, "Proceso")


def variables(serie_db, historia, solo_dim=None):
    vs = sorted(v for v in var_dict if dims(v) and var_dict[v]["metrica_id"] not in gp.VARIANTES)
    if solo_dim == "Persona":
        vs = [v for v in vs if "Persona" in dims(v)]
    elif solo_dim:
        vs = [v for v in vs if solo_dim in dims(v) and var_dict[v]["nivel"] == "producto"]
    if historia:
        vs = [v for v in vs if v not in SOLO_DESDE_2019]
    vent = set().union(*(set(datos[v][serie_db]) for v in vs))
    cob = {v: sum(1 for t in datos[v][serie_db].values() if t[1] is not None) / max(1, len(vent)) for v in vs}
    return [v for v in vs if cob[v] >= gp.MIN_COBERTURA]


def matriz(vs, serie_db):
    """Rangos crudos estandarizados, sin constantes ni releases extremos (como clustering_temporal.matriz)."""
    filas, _ = gp.tabla(vs, datos, serie_db)
    const = [v for j, v in enumerate(vs) if len({f["valores"][j] for f in filas.values()}) < 2]
    if const:
        vs = [v for v in vs if v not in const]
        filas, _ = gp.tabla(vs, datos, serie_db)
    Z, pnums = gp.transformar(filas, "crudo")
    meta = [dict(pnum=p, fecha=fecha(filas[p]["fecha"]), anio=filas[p]["anio"], version=filas[p]["version"]) for p in pnums]
    ext = np.abs(Z).max(axis=1) > 6
    extremos = [m["version"] for m, e in zip(meta, ext) if e]
    X = np.array([filas[p]["valores"] for p in pnums], dtype=float)
    return Z[~ext], vs, [m for m, e in zip(meta, ext) if not e], X[~ext], extremos


def pesar(Z, vs, peso):
    if peso == "variable":
        return Z
    tam = {b: sum(bloque(v) == b for v in vs) for b in ("Persona", "Proceso", "Producto")}
    return Z / np.sqrt(np.array([tam[bloque(v)] for v in vs]))


def segmentar(Z, k):
    n = len(Z)
    con = diags([np.ones(n - 1), np.ones(n - 1)], [-1, 1])
    return AgglomerativeClustering(k, linkage="ward", connectivity=con).fit_predict(Z)


def r2_seg(Z, lab):
    tot = ((Z - Z.mean(0)) ** 2).sum()
    dentro = sum(((Z[lab == g] - Z[lab == g].mean(0)) ** 2).sum() for g in np.unique(lab))
    return float(1 - dentro / tot)


def corrida_circular(Z):
    n = len(Z)
    m = max(5, n // 10)
    return np.column_stack([np.roll(Z[:, j], rng.integers(m, n - m)) for j in range(Z.shape[1])])


def tramos(lab, meta):
    out, i = [], 0
    while i < len(lab):
        j = i
        while j + 1 < len(lab) and lab[j + 1] == lab[i]:
            j += 1
        out.append(dict(desde=meta[i]["fecha"], hasta=meta[j]["fecha"], desde_v=meta[i]["version"],
                        hasta_v=meta[j]["version"], releases=j - i + 1))
        i = j + 1
    return out


def cortes(lab, meta):
    """Fecha y versión del primer release de cada época salvo la primera."""
    return [(meta[i]["fecha"], meta[i]["version"]) for i in range(1, len(lab)) if lab[i] != lab[i - 1]]


def etiquetas_por_fecha(cs, fechas):
    return np.array([sum(f >= c for c in cs) for f in fechas])


# ── épocas de cada dimensión sola (referencia, como A1 de clustering_temporal.py) ──

ref = {}
for dim in ("Persona", "Proceso", "Producto"):
    for historia in (False, True):
        if dim == "Persona" and historia:
            continue
        Z, vs, meta, _, _ = matriz(variables("versiones", historia, dim), "versiones")
        ref[(dim, historia)] = {k: cortes(segmentar(Z, k), meta) for k in KS}

# ── todas las métricas juntas ────────────────────────────────────────────────

filas_k, filas_ep, filas_cmp, filas_perfil, filas_lab = [], [], [], [], []
resumen = {}
for historia in (False, True):
    version = "historia" if historia else "desde_2019"
    vs0 = variables("versiones", historia)
    Z0, vs, meta, X, extremos = matriz(vs0, "versiones")
    fechas = [m["fecha"] for m in meta]
    et = [etapa(m["anio"]) for m in meta]
    vsc = variables("versiones_canary", historia)
    comunes_c = [v for v in vs if v in vsc]
    Zc0, vsc, metac, _, _ = matriz(comunes_c, "versiones_canary")
    print(f"=== {version}: {len(vs)} variables ({', '.join(f'{b} {sum(bloque(v) == b for v in vs)}' for b in ('Persona', 'Proceso', 'Producto'))}), "
          f"{len(Z0)} releases {meta[0]['version']}–{meta[-1]['version']}, extremos fuera: {extremos}", flush=True)
    resumen[version] = dict(variables=vs, releases=len(Z0), extremos=extremos, por_peso={})
    for peso in ("variable", "dimension"):
        Z = pesar(Z0, vs, peso)
        Zc = pesar(Zc0, vsc, peso)
        nombre = f"{version}/{peso}"
        resumen[version]["por_peso"][peso] = {}
        for k in KS:
            lab = segmentar(Z, k)
            obs = r2_seg(Z, lab)
            nula = [r2_seg(Zn, segmentar(Zn, k)) for Zn in (corrida_circular(Z) for _ in range(N_NULA))]
            cs = cortes(lab, meta)
            # canary: segmentación propia, comparada con la que darían los cortes estables
            labc = segmentar(Zc, k)
            fc = [m["fecha"] for m in metac]
            ari_canary = adjusted_rand_score(labc, etiquetas_por_fecha([c[0] for c in cs], fc))
            fila = dict(conjunto=nombre, k=k, releases=len(Z), variables=len(vs), r2=obs,
                        r2_nula_p95=float(np.percentile(nula, 95)), p=float((1 + np.sum(np.array(nula) >= obs)) / (1 + N_NULA)),
                        ari_calendario=adjusted_rand_score(et, lab), ari_canary=ari_canary,
                        cortes=" | ".join(f"{f:%Y-%m-%d} {v}" for f, v in cs),
                        cortes_canary=" | ".join(f"{f:%Y-%m-%d} {v}" for f, v in cortes(labc, metac)))
            for (dim, hist), rk in ref.items():
                if hist == historia or dim == "Persona":
                    fila[f"ari_{dim.lower()}"] = adjusted_rand_score(etiquetas_por_fecha([c[0] for c in rk[k]], fechas), lab)
            filas_k.append(fila)
            resumen[version]["por_peso"][peso][k] = fila
            print(f"  {peso:9s} k={k}: R² {obs:.2f} (nula p95 {fila['r2_nula_p95']:.2f}, p {fila['p']:.3f}) "
                  f"ARI calendario {fila['ari_calendario']:.2f} canary {ari_canary:.2f} | {fila['cortes']}", flush=True)
            for e in tramos(lab, meta):
                filas_ep.append(dict(conjunto=nombre, k=k, **{**e, "desde": f"{e['desde']:%Y-%m-%d}", "hasta": f"{e['hasta']:%Y-%m-%d}"}))
            for m, l in zip(meta, lab):
                filas_lab.append(dict(conjunto=nombre, k=k, pnum=m["pnum"], version=m["version"], fecha=f"{m['fecha']:%Y-%m-%d}", epoca=int(l)))
            if k == 4:
                for g in range(k):
                    idx = lab == g
                    for j, v in enumerate(vs):
                        filas_perfil.append(dict(conjunto=nombre, epoca=g, desde=f"{fechas[np.where(idx)[0][0]]:%Y-%m-%d}",
                                                 variable=v, dimension=var_dict[v]["dims_texto"], mediana=float(np.median(X[idx, j]))))

# cortes de cada dimensión sola, para comparar
for (dim, hist), rk in ref.items():
    for k, cs in rk.items():
        filas_cmp.append(dict(dimension=dim, historia=hist, k=k, cortes=" | ".join(f"{f:%Y-%m-%d} {v}" for f, v in cs)))

escribir("segmentacion_k.csv", filas_k)
escribir("epocas.csv", filas_ep)
escribir("epocas_por_dimension.csv", filas_cmp)
escribir("perfil_k4.csv", filas_perfil)
escribir("etiquetas.csv", filas_lab)
with open(OUT / "resumen.json", "w", encoding="utf-8") as fh:
    json.dump(resumen, fh, ensure_ascii=False, indent=1, default=str)
print("\ncortes de cada dimensión sola (k=4):")
for (dim, hist), rk in ref.items():
    print(f"  {dim:8s} {'historia' if hist else 'desde 2019' if dim != 'Persona' else 'todas':10s} " + " | ".join(f"{f:%Y-%m-%d} {v}" for f, v in rk[4]))
print("salida:", OUT)
