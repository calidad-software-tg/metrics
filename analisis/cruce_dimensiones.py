#!/usr/bin/env python3
"""
analisis/cruce_dimensiones.py

Análisis entre dos dimensiones (por ejemplo Persona–Producto o Proceso–Producto), con el mismo
método que el análisis dentro de cada dimensión:

  1. Cruce de variables: correlación parcial de Spearman entre cada variable de un lado y cada
     variable del otro, con muestra efectiva, Benjamini–Hochberg, estabilidad por período, réplica
     en canary y control por tamaño. Cada par se marca como control, escala (involucra conteos de
     participantes), mecánico (misma familia o definición superpuesta) o patrón.
  2. Cruce de componentes: la misma correlación entre los puntajes por release de los componentes
     firmes de cada dimensión (PCA ya calculado por generar_pca.py).
  3. Conjunto reducido: de cada lado, un puntaje por cada componente firme (o su variable de carga
     más alta) más las variables que no cargan en ningún componente firme. Cruza aspectos completos
     y métricas independientes sin repetir la misma información varias veces.
  4. Correlación canónica (CCA) entre los dos conjuntos de componentes, con una prueba de
     permutación que respeta el orden en el tiempo (corrimiento circular).
  5. Triangulación: un patrón de variables se confirma si sus variables cargan en componentes
     que también se relacionan.
  6. PCA conjunto con las variables de los dos lados: componentes que mezclan dimensiones.
  7. Red de métricas: nodos y aristas de las relaciones robustas, para ver qué variables hacen de puente.

Uso (todo con la base corregida):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruce_dimensiones.py Persona Producto
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruce_dimensiones.py Proceso Producto \\
        --config analisis/cruces/proceso_producto.json

Requisitos: analisis/salidas/diccionario_variables.csv (generar_diccionario.py) y
analisis/salidas/pca/pca_<dim>.json de las dos dimensiones (generar_pca.py <Dim>).

Configuración (JSON, todo opcional; ver analisis/cruces/*.json):
    lados.<Dim>.niveles      niveles de variable que aporta cada lado ("producto", "persona_agregada").
                             Por defecto, Persona aporta todas las suyas y las otras dimensiones solo las
                             del proyecto (los resúmenes por colaborador son de Persona).
    lados.<Dim>.excluir      variables que no entran.
    lados.<Dim>.variantes    true para incluir las variantes de una métrica (MTTR con bots, etc.).
    compartidas              qué hacer con una variable que queda en los dos lados:
                             "excluir" (por defecto), o el nombre de la dimensión que se la queda.
    asignar                  {variable: dimensión} para resolver compartidas una por una.
    escala.familias          familias que cuentan como escala (por defecto ["tamano"]).
    escala.variables         variables sueltas que cuentan como escala.
    componentes.conjunto     {Dim: "producto" | "todas"} conjunto del PCA a usar.
    componentes.enfoque      "ajustado" (por defecto), "crudo" o "tamano".
    componentes.elegir       {Dim: [1, 4]} componentes a usar; si no, se eligen los firmes.
    componentes.umbral_bootstrap / umbral_canary   umbrales de congruencia para "firme".
    carga_minima             |carga| desde la que una variable define un componente (0,4).
    permutaciones            permutaciones de la prueba de la CCA (1000).
    reducido.modo            "puntajes" (por defecto: el puntaje de cada componente firme) o "marcadoras"
                             (la variable de carga más alta de cada componente).
    reducido.escala_si       proporción de variables de escala entre las que definen un componente a partir
                             de la cual el componente cuenta como escala (0,5).
    pca_conjunto             false para no correr el PCA conjunto.
    pca_conjunto_variables   "componentes" (por defecto: las variables con |carga| >= carga_minima en los
                             componentes elegidos de cada lado) o "todas" (necesita 3 releases por variable).

Salidas en analisis/salidas/cruces/<dima>_<dimb>/:
    pares_variables.csv, pares_componentes.csv, pares_reducido.csv, triangulacion.csv, red_nodos.csv, red_aristas.csv,
    resumen.json y resumen.md.
"""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

import warnings

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generar_correlaciones as gc  # noqa: E402
import generar_pca as gp  # noqa: E402

ROOT = gc.ROOT
SALIDA = ROOT / "analisis" / "salidas" / "cruces"
PCA_DIR = ROOT / "analisis" / "salidas" / "pca"

DEFAULTS = {
    "lados": {},
    "compartidas": "excluir",
    "asignar": {},
    "escala": {"familias": ["tamano"], "variables": []},
    "componentes": {"conjunto": {}, "enfoque": "ajustado", "elegir": {},
                    "umbral_bootstrap": 0.85, "umbral_canary": 0.70},
    "carga_minima": 0.4,
    "reducido": {"modo": "puntajes", "escala_si": 0.5},
    "permutaciones": 1000,
    "pca_conjunto": True,
    "pca_conjunto_variables": "componentes",
}


# ── utilidades ───────────────────────────────────────────────────────────────

def mezclar(base, extra):
    out = json.loads(json.dumps(base))
    for k, v in (extra or {}).items():
        out[k] = mezclar(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def num(v):
    return isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v))


def r4(v):
    return round(float(v), 4) if num(v) else ""


def dims_de(row):
    t = row.get("dims_texto", "")
    return set() if t in ("", "Sin dimensión") else set(t.split("+"))


# ── 1. lados ─────────────────────────────────────────────────────────────────

def armar_lados(dim_a, dim_b, var_dict, cfg):
    def niveles_por_defecto(dim):
        return None if dim == "Persona" else ["producto"]

    lados = {}
    for dim in (dim_a, dim_b):
        c = cfg["lados"].get(dim, {})
        niveles = c.get("niveles", niveles_por_defecto(dim))
        excluir = set(c.get("excluir", []))
        variantes = c.get("variantes", False)
        lados[dim] = sorted(
            v for v, row in var_dict.items()
            if dim in dims_de(row)
            and (niveles is None or row["nivel"] in niveles)
            and v not in excluir
            and (variantes or row["metrica_id"] not in gp.VARIANTES))

    compartidas = sorted(set(lados[dim_a]) & set(lados[dim_b]))
    resueltas = {}
    for v in compartidas:
        destino = cfg["asignar"].get(v, cfg["compartidas"])
        resueltas[v] = destino
        for dim in (dim_a, dim_b):
            if destino != dim and v in lados[dim]:
                lados[dim].remove(v)
    return lados, resueltas


def es_escala(v, var_dict, cfg):
    return var_dict[v].get("familia", "") in cfg["escala"]["familias"] or v in cfg["escala"]["variables"]


# ── 2. un par: el mismo cálculo que generar_correlaciones.main() ─────────────

def evaluar_par(x_e, y_e, x_c, y_c, size_e, tamano_aplica):
    (n, rho_c, p_c, rho_lin, rho_corr, ic_inf, ic_sup, p_corr,
     r1x, r1y, n_ef, rho_per, rxr, ryr, rows_e, rho_canary) = gc.compute_pair(x_e, y_e, x_c, y_c)

    rho_global = rho_corr if num(rho_corr) else 0.0
    n_eval = len(rho_per)
    n_mismo = sum(1 for r in rho_per.values() if num(r) and (r >= 0) == (rho_global >= 0))
    estable = n_eval >= 3 and n_mismo == n_eval

    rho_tamano = np.nan
    if tamano_aplica and n >= 5:
        filas = [(vx, vy, p, d if d else 1.0, size_e[p][1]) for p, d, vx, vy, *_ in rows_e
                 if p in size_e and size_e[p][1] is not None]
        if len(filas) >= 5:
            rho_tamano = gc.partial_spearman([f[0] for f in filas], [f[1] for f in filas],
                                             [f[2] for f in filas], [f[3] for f in filas],
                                             extra_controls=[[gc.safe_log(f[4] + 1) for f in filas]])["rho_corr"]
    out = dict(gc.chequeos_par(rows_e), n=n, n_efectiva=n_ef, rho_cruda=rho_c, rho_corregida=rho_corr,
               ic_inf=ic_inf, ic_sup=ic_sup, p_corregida=p_corr, rho_canary=rho_canary,
               rho_corregida_tamano=rho_tamano, estable=estable,
               _pn=[r[0] for r in rows_e], _xr=list(rxr) if rxr is not None else [], _yr=list(ryr) if ryr is not None else [])
    for label, *_ in gc.ETAPAS:
        out["rho_" + label.replace("-", "_")] = rho_per.get(label, np.nan)
    return out


def clasificar(pares, claves_control):
    """BH sobre los pares que no son de control, categoría, robustez y control por tamaño."""
    p_fdr = gc.benjamini_hochberg([(k, pr["p_corregida"]) for k, pr in pares.items() if k not in claves_control])
    for k, pr in pares.items():
        pr["p_fdr"] = p_fdr.get(k, "")
        cat, fuerza = gc.categoria_y_fuerza(k in claves_control, pr["n"], pr["p_fdr"] if pr["p_fdr"] != "" else np.nan,
                                            pr["rho_corregida"], pr["ic_inf"], pr["ic_sup"])
        pr["categoria"], pr["fuerza"] = cat, fuerza
        cortas = gc.depende_de_ventanas_cortas(pr["rho_corregida"], pr.get("rho_corregida_sin_cortas", np.nan))
        pr["robusta"] = gc.es_robusta(cat, pr["estable"], pr["rho_corregida"], pr["rho_canary"], cortas)
        ok = gc.resiste_tamano(pr["rho_corregida"], pr["rho_corregida_tamano"])
        pr["resiste_tamano"] = "" if ok is None else ok


# ── 3. componentes ───────────────────────────────────────────────────────────

def cargar_pca(dim, cfg):
    archivo = PCA_DIR / f"pca_{dim.lower()}.json"
    if not archivo.exists():
        sys.exit(f"Falta {archivo}: corré generar_pca.py {dim} sobre la misma base.")
    d = json.loads(archivo.read_text(encoding="utf-8"))
    conj = cfg["componentes"]["conjunto"].get(dim) or ("todas" if dim == "Persona" else "producto")
    if f"{conj}|estable|{cfg['componentes']['enfoque']}" not in d["resultados"]:
        conj = next(iter(d["conjuntos"]))
    return d, conj


def congruencia_canary(d, conj, enfoque, j):
    for c in d.get("comparacion", []):
        if (c["conjunto"], c["serie"], c["enfoque"], c["componente"]) == (conj, "canary", enfoque, j + 1):
            return c["congruencia"]
    return np.nan


def alinear_canary(r_e, r_c, j, umbral):
    """Componente de la solución canary que corresponde al j estable (congruencia de Tucker sobre
    las variables comunes) y su signo. None si ninguno llega al umbral."""
    if not r_c:
        return None
    ve, vc = r_e["variables"], r_c["variables"]
    comunes = [v for v in ve if v in vc]
    if len(comunes) < 3:
        return None
    Le = np.array(r_e["varimax"], dtype=float)[[ve.index(v) for v in comunes], j]
    Lc = np.array(r_c["varimax"], dtype=float)[[vc.index(v) for v in comunes]]
    t = [gp.tucker(Le, Lc[:, i]) for i in range(Lc.shape[1])]
    i = int(np.argmax(np.abs(t)))
    return (i, 1.0 if t[i] >= 0 else -1.0) if abs(t[i]) >= umbral else None


def componentes(dim, cfg, duraciones):
    d, conj = cargar_pca(dim, cfg)
    enf = cfg["componentes"]["enfoque"]
    r_e = d["resultados"][f"{conj}|estable|{enf}"]
    r_c = d["resultados"].get(f"{conj}|canary|{enf}")
    k = r_e["k"]
    elegidos = cfg["componentes"]["elegir"].get(dim)
    out = []
    for j in range(k):
        boot = r_e["boot"]["congruencia_mediana"][j]
        can = congruencia_canary(d, conj, enf, j)
        firme = boot >= cfg["componentes"]["umbral_bootstrap"] and num(can) and can >= cfg["componentes"]["umbral_canary"]
        if elegidos is not None and (j + 1) not in elegidos:
            continue
        if elegidos is None and not firme:
            continue
        L = np.array(r_e["varimax"], dtype=float)[:, j]
        cargas = sorted(((v, float(x)) for v, x in zip(r_e["variables"], L)), key=lambda t: -abs(t[1]))

        def serie(res, col, signo, serie_db):
            s = {}
            for fila in res["puntajes"]:
                pnum, ver, fecha = fila[0], fila[1], str(fila[2])
                s[pnum] = (duraciones[serie_db].get(pnum), signo * float(fila[3 + col]),
                           int(fecha[:4]) if fecha[:4].isdigit() else None, ver, fecha)
            return s

        al = alinear_canary(r_e, r_c, j, cfg["componentes"]["umbral_canary"])
        out.append(dict(
            id=f"{dim.lower()}_cp{j + 1}", dim=dim, n=j + 1, conjunto=conj, enfoque=enf,
            varianza=r_e["varianza"][j], bootstrap=boot, canary=can, firme=firme,
            cargas=cargas, variables=r_e["variables"],
            estable=serie(r_e, j, 1.0, "versiones"),
            canary_serie=serie(r_c, al[0], al[1], "versiones_canary") if al else {}))
    return out


def metricas_cp(c, carga_min, var_dict):
    """Métricas base de las variables que definen un componente (|carga| >= carga_min)."""
    return {gc.metrica_base(var_dict[v]["metrica_id"]) for v, x in c["cargas"] if abs(x) >= carga_min and v in var_dict}


def es_escala_cp(c, carga_min, var_dict, cfg):
    """Un componente cuenta como escala si al menos reducido.escala_si de sus variables fuertes son de escala."""
    fuertes = [v for v, x in c["cargas"] if abs(x) >= carga_min and v in var_dict]
    return bool(fuertes) and sum(es_escala(v, var_dict, cfg) for v in fuertes) / len(fuertes) >= cfg["reducido"]["escala_si"]


def nombre_cp(c, carga_min):
    fuertes = [f"{v} ({x:+.2f})" for v, x in c["cargas"] if abs(x) >= carga_min][:4]
    return f"CP{c['n']} {c['dim']}: " + (", ".join(fuertes) or "sin cargas ≥ umbral")


# ── 4. CCA con permutaciones por corrimiento circular ────────────────────────

def cca(cps_a, cps_b, n_perm, rng):
    comunes = sorted(set.intersection(*(set(c["estable"]) for c in cps_a + cps_b)))
    if len(comunes) < 30 or not cps_a or not cps_b:
        return None
    X = np.array([[c["estable"][p][1] for c in cps_a] for p in comunes])
    Y = np.array([[c["estable"][p][1] for c in cps_b] for p in comunes])

    def corr_canonicas(X, Y):
        Qx, _ = np.linalg.qr(X - X.mean(0))
        Qy, _ = np.linalg.qr(Y - Y.mean(0))
        return np.linalg.svd(Qx.T @ Qy, compute_uv=False)

    obs = corr_canonicas(X, Y)
    n = len(comunes)
    margen = max(10, n // 10)
    nulas = np.array([corr_canonicas(X, np.roll(Y, rng.integers(margen, n - margen), axis=0))[0]
                      for _ in range(n_perm)])
    return dict(n=n, correlaciones=[round(float(v), 4) for v in obs],
                p_primera=round(float((1 + (nulas >= obs[0]).sum()) / (n_perm + 1)), 4),
                nula_p95=round(float(np.percentile(nulas, 95)), 4))


# ── 5. PCA conjunto ──────────────────────────────────────────────────────────

def pca_conjunto(variables, datos, var_dict, enfoque, rng, carga_min, dim_de):
    ventanas = set().union(*(set(datos[v]["versiones"]) for v in variables))
    cob = {v: sum(1 for t in datos[v]["versiones"].values() if t[1] is not None) / max(1, len(ventanas)) for v in variables}
    vs = [v for v in variables if cob[v] >= gp.MIN_COBERTURA]
    if enfoque == "tamano":
        vs = [v for v in vs if var_dict[v].get("familia") != "tamano" and v != gp.VARIABLE_TAMANO]
    filas, _ = gp.tabla(vs, datos, "versiones")
    constantes = [v for j, v in enumerate(vs) if len({f["valores"][j] for f in filas.values()}) < 2]
    if constantes:
        vs = [v for v in vs if v not in constantes]
        filas, _ = gp.tabla(vs, datos, "versiones")
    res = gp.analizar(vs, filas, enfoque, None, rng) if len(filas) >= 30 else None
    if res is None:
        return dict(error=f"pocas ventanas con todos los datos ({len(filas)}) para {len(vs)} variables")
    L = res["sol"]["Lr"]
    comps = []
    for j in range(res["k"]):
        fuertes = [(vs[i], float(L[i, j])) for i in np.argsort(-np.abs(L[:, j])) if abs(L[i, j]) >= carga_min]
        dims = sorted({dim_de[v] for v, _ in fuertes})
        comps.append(dict(n=j + 1, varianza=round(float(res["var"][j]), 4),
                          bootstrap=round(float(res["boot"]["congruencia_mediana"][j]), 4),
                          mixto=len(dims) > 1, dimensiones=dims,
                          cargas=[(v, round(x, 3)) for v, x in fuertes]))
    return dict(n=res["n"], variables=len(vs), excluidas=sorted(set(variables) - set(vs)), k=res["k"],
                criterios=res["criterios"], componentes=comps)


# ── salida ───────────────────────────────────────────────────────────────────

def escribir_csv(ruta, filas, columnas):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas, extrasaction="ignore")
        w.writeheader()
        for fila in filas:
            w.writerow({c: (r4(fila[c]) if isinstance(fila.get(c), float) else fila.get(c, "")) for c in columnas})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dim_a")
    ap.add_argument("dim_b")
    ap.add_argument("--config", help="archivo JSON con la configuración del cruce")
    args = ap.parse_args()
    dim_a, dim_b = (d.strip().capitalize() for d in (args.dim_a, args.dim_b))
    for d in (dim_a, dim_b):
        if d not in gc.DIM_ORDER:
            sys.exit(f"Dimensión desconocida: {d}. Opciones: {', '.join(gc.DIM_ORDER)}")
    if dim_a == dim_b:
        sys.exit("Las dos dimensiones tienen que ser distintas.")
    cfg = mezclar(DEFAULTS, json.loads(Path(args.config).read_text(encoding="utf-8")) if args.config else {})
    rng = np.random.default_rng(gp.SEMILLA)
    warnings.filterwarnings("ignore", message="An input array is constant")
    destino = SALIDA / f"{dim_a.lower()}_{dim_b.lower()}"
    destino.mkdir(parents=True, exist_ok=True)

    print(f"=== cruce_dimensiones.py · {dim_a}–{dim_b} ===", flush=True)
    var_dict, datos = gp.cargar_datos()
    lados, compartidas = armar_lados(dim_a, dim_b, var_dict, cfg)
    for dim in (dim_a, dim_b):
        print(f"  {dim}: {len(lados[dim])} variables")
    if compartidas:
        print(f"  variables en los dos lados: {', '.join(f'{v} → {d}' for v, d in compartidas.items())}")
    dim_de = {v: dim for dim in (dim_a, dim_b) for v in lados[dim]}
    size_e = datos.get("activos_interaccion_conteo", {}).get("versiones", {})

    # ── 1. variables ──
    pares, control = {}, set()
    for x in lados[dim_a]:
        for y in lados[dim_b]:
            rx, ry = var_dict[x], var_dict[y]
            misma = gc.metrica_base(rx["metrica_id"]) == gc.metrica_base(ry["metrica_id"])
            constr = gc.es_por_construccion(x, y, misma)
            fx, fy = rx.get("familia", ""), ry.get("familia", "")
            pr = evaluar_par(datos[x]["versiones"], datos[y]["versiones"], datos[x]["versiones_canary"],
                             datos[y]["versiones_canary"], size_e, not constr and "tamano" not in (fx, fy))
            k = f"{x}__{y}"
            pr.update(par_id=k, x_id=x, y_id=y, x_dim=dim_a, y_dim=dim_b,
                      x_nombre=rx["nombre_legible"], y_nombre=ry["nombre_legible"],
                      escala=es_escala(x, var_dict, cfg) or es_escala(y, var_dict, cfg),
                      misma_familia=fx not in ("", "otra") and fx == fy,
                      solapamiento=gc.es_solapamiento_definicion(x, y, (rx["metrica_id"], ry["metrica_id"])))
            pares[k] = pr
            if constr:
                control.add(k)
    clasificar(pares, control)
    for k, pr in pares.items():
        pr["control"] = k in control
        pr["mecanico"] = pr["misma_familia"] or pr["solapamiento"]
        pr["patron"] = bool(pr["robusta"] and not pr["control"] and not pr["escala"] and not pr["mecanico"]
                            and pr["resiste_tamano"] is not False)
        pr["tipo"] = ("control" if pr["control"] else "patrón" if pr["patron"] else "escala" if pr["robusta"] and pr["escala"]
                      else "mecánico" if pr["robusta"] and pr["mecanico"] else "no resiste tamaño" if pr["robusta"] else "")
    print(f"  pares de variables: {len(pares)} · robustos {sum(p['robusta'] for p in pares.values())} · "
          f"patrones {sum(p['patron'] for p in pares.values())}")

    # ── 2. componentes ──
    duraciones = {s: {} for s in ("versiones", "versiones_canary")}
    for v in datos:
        if v.startswith("__"):
            continue
        for s in duraciones:
            for p, t in datos[v].get(s, {}).items():
                if t[0] is not None:
                    duraciones[s].setdefault(p, t[0])
    cps = {dim: componentes(dim, cfg, duraciones) for dim in (dim_a, dim_b)}
    pares_cp, control_cp = {}, set()
    for ca in cps[dim_a]:
        for cb in cps[dim_b]:
            pr = evaluar_par(ca["estable"], cb["estable"], ca["canary_serie"], cb["canary_serie"], size_e, True)
            k = f"{ca['id']}__{cb['id']}"
            comunes = metricas_cp(ca, cfg["carga_minima"], var_dict) & metricas_cp(cb, cfg["carga_minima"], var_dict)
            pr.update(par_id=k, x_id=ca["id"], y_id=cb["id"], x_nombre=nombre_cp(ca, cfg["carga_minima"]),
                      y_nombre=nombre_cp(cb, cfg["carga_minima"]), comparten=", ".join(sorted(comunes)),
                      escala=es_escala_cp(ca, cfg["carga_minima"], var_dict, cfg) or es_escala_cp(cb, cfg["carga_minima"], var_dict, cfg))
            pares_cp[k] = pr
    clasificar(pares_cp, control_cp)
    for pr in pares_cp.values():
        pr["tipo"] = ("escala" if pr["robusta"] and pr["escala"]
                      else "mecánico" if pr["robusta"] and pr["comparten"]
                      else "no resiste tamaño" if pr["robusta"] and pr["resiste_tamano"] is False
                      else "patrón" if pr["robusta"] else "")
    print(f"  componentes: {dim_a} {[c['n'] for c in cps[dim_a]]} · {dim_b} {[c['n'] for c in cps[dim_b]]} · "
          f"pares robustos {sum(p['robusta'] for p in pares_cp.values())} de {len(pares_cp)}")

    # ── 3. conjunto reducido ──
    def elementos(dim):
        """Puntaje (o variable marcadora) de cada componente firme + variables que no cargan en ninguno."""
        els, cubiertas = [], set()
        for c in cps[dim]:
            fuertes = [v for v, x in c["cargas"] if abs(x) >= cfg["carga_minima"]]
            cubiertas |= set(fuertes)
            escala_cp = es_escala_cp(c, cfg["carga_minima"], var_dict, cfg)
            if cfg["reducido"]["modo"] == "marcadoras" and fuertes:
                v = fuertes[0]
                if v in datos:
                    els.append(dict(id=v, tipo="marcadora", componente=c["id"], nombre=f"{var_dict[v]['nombre_legible']} (marca CP{c['n']})",
                                    e=datos[v]["versiones"], c=datos[v]["versiones_canary"], escala=es_escala(v, var_dict, cfg), familia=var_dict[v].get("familia", ""),
                                    metricas={gc.metrica_base(var_dict[v]["metrica_id"])}))
            else:
                els.append(dict(id=c["id"], tipo="componente", componente=c["id"], nombre=nombre_cp(c, cfg["carga_minima"]),
                                e=c["estable"], c=c["canary_serie"], escala=escala_cp, familia="",
                                metricas=metricas_cp(c, cfg["carga_minima"], var_dict)))
        for v in lados[dim]:
            if v not in cubiertas:
                els.append(dict(id=v, tipo="variable", componente="", nombre=var_dict[v]["nombre_legible"],
                                e=datos[v]["versiones"], c=datos[v]["versiones_canary"], escala=es_escala(v, var_dict, cfg), familia=var_dict[v].get("familia", ""),
                                metricas={gc.metrica_base(var_dict[v]["metrica_id"])}))
        return els
    red_a, red_b = elementos(dim_a), elementos(dim_b)
    pares_red, control_red = {}, set()
    for ea in red_a:
        for eb in red_b:
            k = f"{ea['id']}__{eb['id']}"
            dos_vars = ea["tipo"] != "componente" and eb["tipo"] != "componente"
            if dos_vars and k in pares:
                base = pares[k]
                constr, misma_fam, solap = base["control"], base["misma_familia"], base["solapamiento"]
            else:
                constr = False
                solap = bool(ea["metricas"] & eb["metricas"])     # el componente contiene la misma métrica que el otro lado
                misma_fam = dos_vars and ea["familia"] not in ("", "otra") and ea["familia"] == eb["familia"]
            tam_aplica = not constr and not (dos_vars and "tamano" in (ea["familia"], eb["familia"]))
            pr = evaluar_par(ea["e"], eb["e"], ea["c"], eb["c"], size_e, tam_aplica)
            pr.update(par_id=k, x_id=ea["id"], y_id=eb["id"], x_nombre=ea["nombre"], y_nombre=eb["nombre"],
                      x_tipo=ea["tipo"], y_tipo=eb["tipo"], escala=ea["escala"] or eb["escala"],
                      misma_familia=misma_fam, solapamiento=solap)
            pares_red[k] = pr
            if constr:
                control_red.add(k)
    clasificar(pares_red, control_red)
    for k, pr in pares_red.items():
        pr["control"] = k in control_red
        pr["mecanico"] = pr["misma_familia"] or pr["solapamiento"]
        pr["patron"] = bool(pr["robusta"] and not pr["control"] and not pr["escala"] and not pr["mecanico"]
                            and pr["resiste_tamano"] is not False)
        pr["tipo"] = ("control" if pr["control"] else "patrón" if pr["patron"] else "escala" if pr["robusta"] and pr["escala"]
                      else "mecánico" if pr["robusta"] and pr["mecanico"] else "no resiste tamaño" if pr["robusta"] else "")
    print(f"  conjunto reducido: {dim_a} {len(red_a)} · {dim_b} {len(red_b)} · pares {len(pares_red)} · "
          f"patrones {sum(p['patron'] for p in pares_red.values())}")

    # ── 4. CCA ──
    res_cca = cca(cps[dim_a], cps[dim_b], cfg["permutaciones"], rng)

    # ── 5. triangulación ──
    def comps_de(v, dim):
        return [c for c in cps[dim] if any(var == v and abs(x) >= cfg["carga_minima"] for var, x in c["cargas"])]
    triang = []
    for pr in pares.values():
        if not pr["patron"]:
            continue
        en_a, en_b = comps_de(pr["x_id"], dim_a), comps_de(pr["y_id"], dim_b)
        apoyos = [pares_cp[f"{ca['id']}__{cb['id']}"] for ca in en_a for cb in en_b]
        robustos = [a for a in apoyos if a["tipo"] == "patrón"]
        triang.append(dict(par_id=pr["par_id"], x_nombre=pr["x_nombre"], y_nombre=pr["y_nombre"],
                           rho_corregida=pr["rho_corregida"],
                           componentes_x=", ".join(f"CP{c['n']}" for c in en_a),
                           componentes_y=", ".join(f"CP{c['n']}" for c in en_b),
                           par_componentes_robusto=", ".join(a["par_id"] for a in robustos),
                           triangulado=bool(robustos)))

    # ── 6. PCA conjunto ──
    res_pca = None
    if cfg["pca_conjunto"]:
        print("  PCA conjunto…", flush=True)
        if cfg["pca_conjunto_variables"] == "todas":
            vars_pca = lados[dim_a] + lados[dim_b]
        else:
            vars_pca = sorted({v for d in (dim_a, dim_b) for c in cps[d] for v, x in c["cargas"]
                               if abs(x) >= cfg["carga_minima"] and v in dim_de})
        res_pca = pca_conjunto(vars_pca, datos, var_dict, cfg["componentes"]["enfoque"],
                               rng, cfg["carga_minima"], dim_de)

    # ── 7. red ──
    aristas = [dict(origen=p["x_id"], destino=p["y_id"], rho=p["rho_corregida"], tipo=p["tipo"])
               for p in pares.values() if p["robusta"] and not p["control"]]
    grado = {}
    for a in aristas:
        if a["tipo"] == "patrón":
            for v in (a["origen"], a["destino"]):
                grado[v] = grado.get(v, 0) + 1
    nodos = [dict(variable=v, dimension=dim_de[v], nombre=var_dict[v]["nombre_legible"], grado_patrones=grado.get(v, 0))
             for v in sorted({a["origen"] for a in aristas} | {a["destino"] for a in aristas})]

    # ── escribir ──
    cols = ["par_id", "x_id", "y_id", "x_nombre", "y_nombre", "tipo", "categoria", "fuerza", "n", "n_efectiva",
            "rho_cruda", "rho_corregida", "ic_inf", "ic_sup", "p_corregida", "p_fdr", "rho_2016_2019", "rho_2020_2022",
            "rho_2023_2024", "rho_2025_2026", "estable", "rho_canary", "rho_corregida_tamano", "resiste_tamano",
            "rho_corregida_sin_cortas", "rho_corregida_local", "alcance_temporal", "robusta", "escala", "misma_familia",
            "solapamiento", "control", "patron"]
    escribir_csv(destino / "pares_variables.csv", sorted(pares.values(), key=lambda p: -abs(p["rho_corregida"]) if num(p["rho_corregida"]) else 0), cols)
    escribir_csv(destino / "pares_componentes.csv", list(pares_cp.values()), [c for c in cols if c not in ("escala", "misma_familia", "solapamiento", "control", "patron")] + ["comparten", "escala"])
    escribir_csv(destino / "pares_reducido.csv", sorted(pares_red.values(), key=lambda p: -abs(p["rho_corregida"]) if num(p["rho_corregida"]) else 0),
                 ["x_tipo", "y_tipo"] + cols)
    escribir_csv(destino / "triangulacion.csv", triang, list(triang[0]) if triang else ["par_id"])
    escribir_csv(destino / "red_aristas.csv", aristas, ["origen", "destino", "rho", "tipo"])
    escribir_csv(destino / "red_nodos.csv", nodos, ["variable", "dimension", "nombre", "grado_patrones"])
    resumen = dict(
        dimensiones=[dim_a, dim_b], configuracion=cfg, variables={d: lados[d] for d in (dim_a, dim_b)},
        compartidas=compartidas,
        conteo_variables={t: sum(1 for p in pares.values() if p["tipo"] == t) for t in ("patrón", "escala", "mecánico", "no resiste tamaño", "control")},
        componentes={d: [dict(n=c["n"], conjunto=c["conjunto"], varianza=c["varianza"], bootstrap=c["bootstrap"],
                              canary=r4(c["canary"]), cargas=[(v, round(x, 3)) for v, x in c["cargas"] if abs(x) >= cfg["carga_minima"]])
                         for c in cps[d]] for d in (dim_a, dim_b)},
        reducido=dict(modo=cfg["reducido"]["modo"],
                      elementos={d: [dict(id=e["id"], tipo=e["tipo"], componente=e["componente"], nombre=e["nombre"], escala=e["escala"])
                                     for e in els] for d, els in ((dim_a, red_a), (dim_b, red_b))},
                      conteo={t: sum(1 for p in pares_red.values() if p["tipo"] == t) for t in ("patrón", "escala", "mecánico", "no resiste tamaño", "control")}),
        cca=res_cca, pca_conjunto=res_pca)
    # valores por release para el reporte (reporte_cruce_dimensiones.py)
    releases = {}
    for v in dim_de:
        for pnum, t in datos[v]["versiones"].items():
            if pnum not in releases and t[3]:
                fh = str(t[4] or "")
                releases[pnum] = [t[3], f"{fh[:4]}-{fh[4:6]}-{fh[6:8]}" if len(fh) >= 8 else "", t[2]]
    def residuos(pr):
        return dict(p=pr["_pn"], xr=[r4(v) for v in pr["_xr"]], yr=[r4(v) for v in pr["_yr"]])
    valores = dict(
        releases=releases,
        serie={v: {p: r4(t[1]) for p, t in datos[v]["versiones"].items() if t[1] is not None} for v in dim_de},
        residuos={k: residuos(pr) for k, pr in pares.items() if pr["robusta"] and not pr["control"]},
        componentes={c["id"]: {p: r4(t[1]) for p, t in c["estable"].items()} for d in (dim_a, dim_b) for c in cps[d]},
        residuos_cp={k: residuos(pr) for k, pr in pares_cp.items()},
        residuos_red={k: residuos(pr) for k, pr in pares_red.items() if pr["robusta"] and not pr["control"]},
    )
    (destino / "valores.json").write_text(json.dumps(valores, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (destino / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    f = lambda v, d=2: f"{v:+.{d}f}".replace(".", ",") if num(v) else "—"
    md = [f"# Cruce {dim_a}–{dim_b}", "",
          f"Variables: {dim_a} {len(lados[dim_a])}, {dim_b} {len(lados[dim_b])}" +
          (f". En los dos lados: {', '.join(f'{v} → {d}' for v, d in compartidas.items())}." if compartidas else "."), "",
          "## Variables", "", "| Tipo | Pares |", "|---|---|"]
    md += [f"| {t} | {n} |" for t, n in resumen["conteo_variables"].items()] + ["", "### Patrones (robustos, sin escala ni construcción)", "",
           "| Par | ρ corregida | con tamaño | canary | alcance |", "|---|---|---|---|---|"]
    md += [f"| {p['x_nombre']} ↔ {p['y_nombre']} | {f(p['rho_corregida'])} | {f(p['rho_corregida_tamano'])} | {f(p['rho_canary'])} | {p.get('alcance_temporal', '')} |"
           for p in sorted(pares.values(), key=lambda p: -abs(p["rho_corregida"]) if num(p["rho_corregida"]) else 0) if p["patron"]]
    md += ["", "## Componentes", ""]
    for d in (dim_a, dim_b):
        md += [f"- {nombre_cp(c, cfg['carga_minima'])} · bootstrap {f(c['bootstrap'])} · canary {f(c['canary'])}" for c in cps[d]]
    md += ["", "| Par de componentes | ρ corregida | con tamaño | canary | resultado |", "|---|---|---|---|---|"]
    md += [f"| {p['x_nombre']} ↔ {p['y_nombre']} | {f(p['rho_corregida'])} | {f(p['rho_corregida_tamano'])} | {f(p['rho_canary'])} | {p['tipo'] or 'no robusto'} |"
           for p in pares_cp.values()]
    md += ["", "## Conjunto reducido", "",
           f"De cada lado: {'el puntaje de cada componente firme' if cfg['reducido']['modo'] == 'puntajes' else 'la variable de carga más alta de cada componente firme'} "
           f"más las variables que no cargan en ningún componente. {dim_a}: {len(red_a)} elementos · {dim_b}: {len(red_b)} · {len(pares_red)} pares.", "",
           "| Tipo | Pares |", "|---|---|"] + [f"| {t} | {n} |" for t, n in resumen["reducido"]["conteo"].items()]
    md += ["", "| Par | ρ corregida | con tamaño | canary | tipo |", "|---|---|---|---|---|"]
    md += [f"| {p['x_nombre']} ↔ {p['y_nombre']} | {f(p['rho_corregida'])} | {f(p['rho_corregida_tamano'])} | {f(p['rho_canary'])} | {p['tipo']} |"
           for p in sorted(pares_red.values(), key=lambda p: -abs(p["rho_corregida"]) if num(p["rho_corregida"]) else 0) if p["robusta"] and not p["control"]]
    if res_cca:
        md += ["", "## Correlación canónica entre componentes", "",
               f"Correlaciones canónicas: {', '.join(f(v) for v in res_cca['correlaciones'])} (n = {res_cca['n']}). "
               f"Primera frente a la nula por corrimiento circular: p = {res_cca['p_primera']:.3f} (percentil 95 nulo {f(res_cca['nula_p95'])})."]
    if triang:
        md += ["", "## Triangulación", "", "| Par | componentes | par de componentes robusto |", "|---|---|---|"]
        md += [f"| {t['x_nombre']} ↔ {t['y_nombre']} | {t['componentes_x'] or '—'} / {t['componentes_y'] or '—'} | {t['par_componentes_robusto'] or 'no'} |" for t in triang]
    if res_pca and "componentes" in res_pca:
        md += ["", "## PCA conjunto", "", f"{res_pca['variables']} variables, {res_pca['n']} releases, Horn retiene {res_pca['k']}.", ""]
        md += [f"- CP{c['n']} ({c['varianza']:.0%}){' · **mezcla dimensiones**' if c['mixto'] else ''}: " +
               ", ".join(f"{v} ({x:+.2f})" for v, x in c["cargas"][:6]) for c in res_pca["componentes"]]
    elif res_pca:
        md += ["", "## PCA conjunto", "", res_pca["error"]]
    (destino / "resumen.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"  salida: {destino}")


if __name__ == "__main__":
    main()
