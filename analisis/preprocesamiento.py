#!/usr/bin/env python3
"""
analisis/preprocesamiento.py

Preprocesamiento común a todos los análisis (sección 3.2.3 del informe). No se corre solo: lo importan
correlaciones.py, pca.py, clustering.py, cruces.py y temporal.py, así todos usan los mismos datos y la
misma transformación.

  1. Variables: lee el diccionario (analisis/salidas/diccionario_variables.csv, que arma
     generar_diccionario.py con la limpieza de variables y las familias).
  2. Datos: las métricas del proyecto desde la base y las de Persona desde
     persona_agregado_estable_canary.csv (export_persona.py: identidades unificadas y sin bots), en las
     dos series (estable y canary), y las proporciones de participación a partir de los conteos.
     Todas las series usan la fecha del release (fin de la ventana).
  3. Releases: saca los backports (parches de una versión mayor anterior).
  4. Tabla: releases con dato en todas las variables pedidas (tabla) y su transformación en rangos,
     sin tendencia temporal ni duración de la ventana, y opcionalmente sin tamaño (transformar).
  5. Períodos para la estabilidad: los cuatro de calendario (criterio principal) o las épocas que
     encuentra temporal.py, asignadas por número de release.
"""
import csv
import math
import os
from collections import defaultdict
from pathlib import Path

import numpy as np
import psycopg2
from scipy.stats import rankdata

ROOT      = Path(__file__).resolve().parent.parent
DICT_CSV  = ROOT / "analisis" / "salidas" / "diccionario_variables.csv"
AGG_CSV   = ROOT / "persona_agregado_estable_canary.csv"

# Credenciales: variables POSTGRES_* del .env de la raíz si existen.
_env = ROOT / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        if "=" in _line and not _line.startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())
DB = dict(host=os.environ.get("POSTGRES_HOST", "localhost"),
          port=int(os.environ.get("POSTGRES_PORT", 5432)),
          dbname=os.environ.get("POSTGRES_DB", "resultados_metricas"),
          user=os.environ.get("POSTGRES_USER", "metricas"),
          password=os.environ.get("POSTGRES_PASSWORD", "metricas"))

EXCLUIR_ESTABLE = frozenset({
    "4.4.0-canary.2", "4.4.0-canary.1", "v12.2.3-canary.5", "v15.0.0-rc.1"
})

DIM_ORDER = ["Persona", "Proceso", "Producto"]
SERIES = [("estable", "versiones"), ("canary", "versiones_canary")]
VARIABLE_TAMANO = "activos_interaccion_conteo"
# Versiones alternativas de una misma métrica (para comparar, no para el PCA): si entran junto
# con la principal forman un componente entre ellas (las 4 de MTTR cargaban 0,81–0,92 en el CP1).
VARIANTES = {"mttr_p50", "mttr_bugs", "mttr_con_bots", "nci_con_bots"}
MIN_COBERTURA = 0.5       # una variable entra en una serie si tiene dato en al menos la mitad de sus ventanas
SEMILLA = 20261011

# Proporciones de participación: (variable, numerador, denominador)
RATIO_DEFS_CORR = [
    ("tasa_nuevos_commits_ratio",     "nuevos_commits_conteo",      "activos_commits_conteo"),
    ("tasa_nuevos_interaccion_ratio", "nuevos_interaccion_conteo",  "activos_interaccion_conteo"),
    ("prop_commitean_ratio",          "activos_commits_conteo",     "activos_interaccion_conteo"),
    ("prop_cierran_ratio",            "activos_cierre_conteo",      "activos_interaccion_conteo"),
    ("prop_comentan_ratio",           "activos_comentarios_conteo", "activos_interaccion_conteo"),
]

# Períodos para la estabilidad de las relaciones. El calendario es el criterio principal (se fijó antes
# de mirar los datos); las épocas (temporal.py: todas las métricas, toda la historia, peso por dimensión)
# se usan como prueba de sensibilidad y empiezan en estos releases.
CALENDARIO = [
    ("2016-2019", 2016, 2019),
    ("2020-2022", 2020, 2022),
    ("2023-2024", 2023, 2024),
    ("2025-2026", 2025, 2026),
]
CORTES_EPOCAS = ("v9.1.7", "v12.0.5", "v14.1.1")


# ── helpers ──────────────────────────────────────────────────────────────────

def safe_log(x):
    return math.log(x) if x and x > 0 else 0.0


def natural_spline_basis(x, df=4):
    x = np.asarray(x, dtype=float)
    xmin, xmax = x.min(), x.max()
    if xmax <= xmin:
        return np.zeros((len(x), df))
    xn = (x - xmin) / (xmax - xmin)
    n_int = df - 1
    qt = np.linspace(0, 1, n_int + 2)[1:-1]
    int_knots = np.quantile(xn, qt)
    all_k = np.concatenate([[0.0], int_knots, [1.0]])
    K = len(all_k)

    def hp(v, t):
        return np.where(v > t, (v - t) ** 3, 0.0)

    def d(v, k):
        tk, tK = all_k[k], all_k[-1]
        denom = tK - tk
        return np.zeros_like(v) if abs(denom) < 1e-10 else (hp(v, tk) - hp(v, tK)) / denom

    ref = d(xn, K - 2)
    cols = [xn]
    for k in range(K - 2):
        cols.append(d(xn, k) - ref)
    return np.column_stack(cols)


# ── Cargar diccionario ────────────────────────────────────────────────────────

def load_dict():
    out = {}
    with open(DICT_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["incluida"] == "sí":
                out[row["variable_id"]] = row
    return out


# ── Cargar datos de producto desde DB ────────────────────────────────────────

def load_producto(var_dict):
    prod_vars = {vid: r for vid, r in var_dict.items() if r["nivel"] == "producto"}
    metricas  = {r["metrica_id"] for r in prod_vars.values()}
    if not metricas:
        return {}
    con = psycopg2.connect(**DB)
    cur = con.cursor()
    cur.execute("""
        SELECT r.metrica_id,
               p.periodo_num,
               EXTRACT(EPOCH FROM (p.fecha_fin - p.fecha_inicio)) / 86400.0,
               r.value,
               EXTRACT(YEAR FROM p.fecha_fin)::int,
               p.etiqueta,
               TO_CHAR(p.fecha_fin, 'YYYYMMDDHH24MISS'),
               p.tipo_analisis
        FROM resultado r
        JOIN periodo p ON p.periodo_id = r.periodo_id
        WHERE r.contribuyente_login IS NULL
          AND r.metrica_id = ANY(%s)
          AND p.tipo_analisis IN ('versiones', 'versiones_canary')
          AND p.etiqueta NOT IN %s
        ORDER BY r.metrica_id, p.tipo_analisis, p.periodo_num
    """, (list(metricas), tuple(EXCLUIR_ESTABLE)))
    rows = cur.fetchall()
    con.close()
    by_metric = defaultdict(lambda: defaultdict(dict))
    for mid, pnum, dur, val, anio, ver, fh, tipo in rows:
        by_metric[mid][tipo][pnum] = (float(dur) if dur else None, val, anio, ver, fh)
    out = {}
    for vid, r in prod_vars.items():
        mid = r["metrica_id"]
        out[vid] = {
            "versiones":        by_metric[mid].get("versiones", {}),
            "versiones_canary": by_metric[mid].get("versiones_canary", {}),
        }
    return out


# ── Cargar datos de persona_agregada desde CSV ────────────────────────────────

def load_persona_agg(var_dict):
    # Skip ratio variables — they're computed from conteo data by compute_ratio_agg
    agg_vars = {vid: r for vid, r in var_dict.items()
                if r["nivel"] == "persona_agregada" and r["estadistico"] != "ratio"}
    if not agg_vars:
        return {}

    stat_col = {"mediana": "mediana", "p90": "p90",
                "share_top10pct": "share_top10pct", "conteo": "n_contribuyentes"}
    var_parse = {vid: (r["metrica_id"], r["estadistico"]) for vid, r in agg_vars.items()}
    needed = {(mid, stat) for mid, stat in var_parse.values()}
    buf = defaultdict(lambda: {"versiones": {}, "versiones_canary": {}})

    with open(AGG_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["alcance"] != "humanos":
                continue
            mid  = row["metrica_id"]
            serie = row["serie"]
            if serie not in ("versiones", "versiones_canary"):
                continue
            for stat, col in stat_col.items():
                if (mid, stat) not in needed:
                    continue
                raw = row.get(col, "")
                try:
                    val = float(raw)
                    if math.isnan(val):
                        val = None
                except (ValueError, TypeError):
                    val = None
                pnum = int(row["periodo_num"])
                try:
                    dur = float(row.get("duracion_dias", "") or "") if row.get("duracion_dias") else None
                except ValueError:
                    dur = None
                try:
                    anio = int(float(row.get("anio", "") or "")) if row.get("anio") else None
                except ValueError:
                    anio = None
                ver = row.get("version", "")
                fh  = row.get("fecha_hora", "")
                buf[(mid, stat)][serie][pnum] = (dur, val, anio, ver, fh)

    out = {}
    for vid, (mid, stat) in var_parse.items():
        out[vid] = {
            "versiones":        buf[(mid, stat)].get("versiones", {}),
            "versiones_canary": buf[(mid, stat)].get("versiones_canary", {}),
        }
    return out


def compute_ratio_agg(agg_data):
    """Compute 5 ratio variables from existing conteo agg_data."""
    out = {}
    for vid, num_id, den_id in RATIO_DEFS_CORR:
        result = {"versiones": {}, "versiones_canary": {}}
        num_d = agg_data.get(num_id, {})
        den_d = agg_data.get(den_id, {})
        for serie in ("versiones", "versiones_canary"):
            num_s = num_d.get(serie, {})
            den_s = den_d.get(serie, {})
            for pnum in set(num_s) & set(den_s):
                num_tup = num_s[pnum]
                den_tup = den_s[pnum]
                if num_tup[1] is None or den_tup[1] is None or den_tup[1] == 0:
                    continue
                dur  = den_tup[0]
                anio = den_tup[2]
                ver  = den_tup[3]
                fh   = den_tup[4]
                result[serie][pnum] = (dur, num_tup[1] / den_tup[1], anio, ver, fh)
        out[vid] = result
    return out


# ── Backports ─────────────────────────────────────────────────────────────────

def es_backport(versiones):
    """Para releases ordenados en el tiempo: True si es parche de una versión mayor anterior
    (ej. una v14.2.x publicada cuando ya salió la v15)."""
    marca, maximo = [], -1
    for v in versiones:
        try:
            mayor = int(str(v).lstrip("vV").split(".")[0])
        except ValueError:
            marca.append(False)
            continue
        marca.append(mayor < maximo)
        maximo = max(maximo, mayor)
    return marca


def excluir_backports(all_data):
    """Saca de todas las variables las ventanas de backports, en las dos series.

    Con las ventanas nuevas de run_versiones.py (que ya excluyen backports) no saca nada;
    con datos viejos, hace que las correlaciones y el PCA usen los mismos releases (antes
    el PCA los excluía y las correlaciones no). Devuelve {serie: cantidad excluida}."""
    excluidos = {}
    for serie in ("versiones", "versiones_canary"):
        version = {}
        for d in all_data.values():
            for pnum, t in d.get(serie, {}).items():
                version.setdefault(pnum, t[3])
        orden = sorted(version)
        bp = {p for p, b in zip(orden, es_backport([version[p] for p in orden])) if b}
        for d in all_data.values():
            for pnum in bp:
                d.get(serie, {}).pop(pnum, None)
        excluidos[serie] = len(bp)
    return excluidos

# ── Datos de todas las variables ─────────────────────────────────────────────

def cargar_datos():
    """Todas las variables incluidas del diccionario, con sus dos series (estable y canary), sin backports."""
    var_dict = load_dict()
    prod = load_producto(var_dict)
    agg = load_persona_agg(var_dict)
    ratios = compute_ratio_agg(agg)
    vacio = {"versiones": {}, "versiones_canary": {}}
    datos = {}
    for vid, r in var_dict.items():
        if r["nivel"] == "producto":
            datos[vid] = prod.get(vid, vacio)
        elif r["estadistico"] == "ratio":
            datos[vid] = ratios.get(vid, vacio)
        else:
            datos[vid] = agg.get(vid, vacio)
    datos["__backports__"] = excluir_backports(datos)
    return var_dict, datos


def tabla(variables, datos, serie_db):
    """Releases con valor en todas las variables (y en el tamaño), sin backports."""
    filas = {}
    tam = datos.get(VARIABLE_TAMANO, {}).get(serie_db, {})
    comunes = set.intersection(*(set(datos[v][serie_db]) for v in variables))
    for pnum in sorted(comunes):
        vals = [datos[v][serie_db][pnum][1] for v in variables]
        if any(x is None for x in vals):
            continue
        ref = datos[variables[0]][serie_db][pnum]
        dur = next((datos[v][serie_db][pnum][0] for v in variables if datos[v][serie_db][pnum][0]), None)
        t = tam.get(pnum, (None, None))[1]
        filas[pnum] = dict(valores=vals, dur=dur or 1.0, anio=ref[2], version=ref[3], fecha=str(ref[4] or ""),
                           tamano=t)
    # los backports ya se excluyeron al cargar (cargar_datos)
    return filas, datos.get("__backports__", {}).get(serie_db, 0)


def transformar(filas, enfoque):
    """Matriz estandarizada (releases × variables) según el enfoque."""
    pnums = sorted(filas)
    if enfoque == "tamano":
        pnums = [p for p in pnums if filas[p]["tamano"] is not None]
    X = np.array([filas[p]["valores"] for p in pnums], dtype=float)
    R = np.column_stack([rankdata(X[:, j], method="average") for j in range(X.shape[1])])
    if enfoque != "crudo":
        n = len(pnums)
        rp = rankdata(pnums, method="average")
        rd = rankdata([safe_log(filas[p]["dur"]) for p in pnums], method="average")
        controles = [np.ones(n), natural_spline_basis(rp, df=4), rd]
        if enfoque == "tamano":
            controles.append(rankdata([safe_log(filas[p]["tamano"] + 1) for p in pnums], method="average"))
        C = np.column_stack(controles)
        coef, *_ = np.linalg.lstsq(C, R, rcond=None)
        R = R - C @ coef
    sd = R.std(axis=0, ddof=1)
    sd[sd == 0] = 1.0
    return (R - R.mean(axis=0)) / sd, pnums


# ── Períodos ─────────────────────────────────────────────────────────────────

def cortes_epocas(datos, cortes=CORTES_EPOCAS):
    """Número de release (periodo_num, el mismo en todas las series) del primer release de cada época.

    Se busca por versión en la serie estable, después de sacar los backports. La época se asigna por
    número de release y no por fecha, para que el release del corte caiga en la misma época en todas
    las variables."""
    pnum = {}
    for v, d in datos.items():
        if v.startswith("__"):
            continue
        for p, t in d.get("versiones", {}).items():
            if t[3] in cortes:
                assert pnum.setdefault(t[3], p) == p, f"{t[3]} con dos periodo_num"
    assert set(pnum) == set(cortes), f"faltan cortes: {set(cortes) - set(pnum)}"
    return sorted(pnum.values())


def con_epoca(serie, cortes_pnum):
    """La serie con el año de cada release reemplazado por su época (1, 2, ...), que es lo que usan los
    períodos cuando se trabaja con épocas."""
    return {p: (t[0], t[1], 1 + sum(p >= c for c in cortes_pnum), t[3], t[4]) for p, t in serie.items()}
