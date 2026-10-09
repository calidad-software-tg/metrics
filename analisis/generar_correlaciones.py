#!/usr/bin/env python3
"""
analisis/generar_correlaciones.py

Genera:
  analisis/salidas/pares_correlacion.csv
  analisis/salidas/pares_valores.csv          (o _persona / _resto si > 90 MB)
  analisis/salidas/metodo_correlaciones.md
  analisis/salidas/revision_persona.csv
"""
import csv
import math
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
import psycopg2
from scipy.stats import rankdata, t as t_dist, spearmanr, pearsonr

ROOT      = Path(__file__).resolve().parent.parent
DICT_CSV  = ROOT / "analisis" / "salidas" / "diccionario_variables.csv"
AGG_CSV   = ROOT / "persona_agregado_estable_canary.csv"
OUT_PARES = ROOT / "analisis" / "salidas" / "pares_correlacion.csv"
OUT_VALS  = ROOT / "analisis" / "salidas" / "pares_valores.csv"
OUT_VALS_P = ROOT / "analisis" / "salidas" / "pares_valores_persona.csv"
OUT_VALS_R = ROOT / "analisis" / "salidas" / "pares_valores_resto.csv"
OUT_MD    = ROOT / "analisis" / "salidas" / "metodo_correlaciones.md"
OUT_REV   = ROOT / "analisis" / "salidas" / "revision_persona.csv"

DB = dict(host="localhost", port=5432, dbname="resultados_metricas",
          user="metricas", password="metricas")

EXCLUIR_ESTABLE = frozenset({
    "4.4.0-canary.2", "4.4.0-canary.1", "v12.2.3-canary.5", "v15.0.0-rc.1"
})

ETAPAS = [
    ("2016-2019", 2016, 2019),
    ("2020-2022", 2020, 2022),
    ("2023-2024", 2023, 2024),
    ("2025-2026", 2025, 2026),
]
DIM_ORDER = ["Persona", "Proceso", "Producto"]

# por_construccion: activos ↔ nuevos del mismo canal, activos_comentarios/cierre ↔ activos_interaccion
ACTIVOS_NUEVOS = {
    frozenset(["activos_commits_conteo",      "nuevos_commits_conteo"]),
    frozenset(["activos_interaccion_conteo",  "nuevos_interaccion_conteo"]),
    frozenset(["activos_comentarios_conteo",  "activos_interaccion_conteo"]),
    frozenset(["activos_cierre_conteo",       "activos_interaccion_conteo"]),
}

# proporciones: cada ratio es por_construccion con sus dos componentes
RATIO_DEFS_CORR = [
    ("tasa_nuevos_commits_ratio",     "nuevos_commits_conteo",      "activos_commits_conteo"),
    ("tasa_nuevos_interaccion_ratio", "nuevos_interaccion_conteo",  "activos_interaccion_conteo"),
    ("prop_commitean_ratio",          "activos_commits_conteo",     "activos_interaccion_conteo"),
    ("prop_cierran_ratio",            "activos_cierre_conteo",      "activos_interaccion_conteo"),
    ("prop_comentan_ratio",           "activos_comentarios_conteo", "activos_interaccion_conteo"),
]
RATIO_POR_CONSTRUCCION = frozenset(
    frozenset([vid, comp])
    for vid, num_id, den_id in RATIO_DEFS_CORR
    for comp in (num_id, den_id)
)

K_CONTROLS_LIN = 2   # periodo_num + log(dur)
K_CONTROLS_SPL = 5   # 4 spline df + log(dur)


# ── helpers ──────────────────────────────────────────────────────────────────

def safe_log(x):
    return math.log(x) if x and x > 0 else 0.0


def ar1_coef(r):
    r = np.asarray(r, dtype=float)
    if len(r) < 3:
        return 0.0
    rc = r - r.mean()
    den = float(np.dot(rc, rc))
    return 0.0 if den == 0 else float(np.dot(rc[:-1], rc[1:]) / den)


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


def partial_spearman(x_vals, y_vals, pnums, durs, extra_controls=None):
    """
    Spearman parcial. extra_controls: lista de listas adicionales (ya en escala raw,
    se rankean internamente). Devuelve dict con rho_lineal, rho_corr, p_corr,
    ic_inf, ic_sup, rx_r, ry_r, r1x, r1y, n_efectiva.
    """
    nan_r = dict(rho_lineal=np.nan, rho_corr=np.nan,
                 p_corr=np.nan, ic_inf=np.nan, ic_sup=np.nan,
                 rx_r=[], ry_r=[], r1x=0.0, r1y=0.0, n_efectiva=10)
    n = len(x_vals)
    if n < 5:
        return nan_r

    n_extra = len(extra_controls) if extra_controls else 0
    K_SPL = K_CONTROLS_SPL + n_extra

    rx = rankdata(x_vals, method="average")
    ry = rankdata(y_vals, method="average")
    rp = rankdata(pnums,  method="average")
    rd = rankdata([safe_log(d) for d in durs], method="average")

    def resid(v, X):
        coef, *_ = np.linalg.lstsq(X, v, rcond=None)
        return v - X @ coef

    # Versión lineal (rho_corregida_lineal)
    X_lin = np.column_stack([np.ones(n), rp, rd])
    rx_lin = resid(rx, X_lin)
    ry_lin = resid(ry, X_lin)
    rho_lin, _ = pearsonr(rx_lin, ry_lin)
    if np.isnan(rho_lin):
        rho_lin = np.nan

    # Versión spline
    ns = natural_spline_basis(rp, df=4)
    extra_ranked = []
    if extra_controls:
        for ec in extra_controls:
            extra_ranked.append(rankdata(ec, method="average"))
    X_spl = np.column_stack([np.ones(n), ns, rd] + extra_ranked)
    rx_spl = resid(rx, X_spl)
    ry_spl = resid(ry, X_spl)
    rho_spl, _ = pearsonr(rx_spl, ry_spl)

    if np.isnan(rho_spl):
        return dict(rho_lineal=rho_lin, rho_corr=np.nan,
                    p_corr=np.nan, ic_inf=np.nan, ic_sup=np.nan,
                    rx_r=list(rx_spl), ry_r=list(ry_spl),
                    r1x=0.0, r1y=0.0, n_efectiva=10)

    sort_idx = np.argsort(pnums)
    r1x = ar1_coef(rx_spl[sort_idx])
    r1y = ar1_coef(ry_spl[sort_idx])

    denom = 1.0 + r1x * r1y
    if denom <= 0:
        n_ef = n
    else:
        raw = n * (1.0 - r1x * r1y) / denom
        n_ef = int(min(float(n), max(10.0, raw)))

    df_spl = n_ef - 2 - K_SPL
    if df_spl >= 1:
        t_stat = rho_spl * math.sqrt(df_spl) / math.sqrt(max(1e-15, 1 - rho_spl ** 2))
        p_corr = 2 * t_dist.sf(abs(t_stat), df_spl)
    else:
        p_corr = np.nan

    if n_ef > 3:
        z  = math.atanh(float(np.clip(rho_spl, -1 + 1e-10, 1 - 1e-10)))
        se = 1.0 / math.sqrt(max(1e-10, n_ef - 3))
        ic_inf = math.tanh(z - 1.96 * se)
        ic_sup = math.tanh(z + 1.96 * se)
    else:
        ic_inf = ic_sup = np.nan

    return dict(rho_lineal=rho_lin, rho_corr=rho_spl,
                p_corr=p_corr, ic_inf=ic_inf, ic_sup=ic_sup,
                rx_r=list(rx_spl), ry_r=list(ry_spl),
                r1x=r1x, r1y=r1y, n_efectiva=n_ef)


def benjamini_hochberg(pairs_pvals):
    valid = [(k, p) for k, p in pairs_pvals if isinstance(p, float) and not math.isnan(p)]
    valid.sort(key=lambda x: x[1])
    m = len(valid)
    if m == 0:
        return {k: "" for k, _ in pairs_pvals}
    p_adj_arr = np.empty(m)
    for i, (_, p) in enumerate(valid):
        p_adj_arr[i] = p * m / (i + 1)
    for i in range(m - 2, -1, -1):
        p_adj_arr[i] = min(p_adj_arr[i], p_adj_arr[i + 1])
    p_adj_arr = np.minimum(p_adj_arr, 1.0)
    result = {k: "" for k, _ in pairs_pvals}
    for i, (k, _) in enumerate(valid):
        result[k] = round(float(p_adj_arr[i]), 6)
    return result


def cruces_para_par(dims_x, dims_y):
    seen = set()
    out = []
    for a in DIM_ORDER:
        if a not in dims_x:
            continue
        for b in DIM_ORDER:
            if b not in dims_y:
                continue
            pair = (a, b) if DIM_ORDER.index(a) <= DIM_ORDER.index(b) else (b, a)
            cruce = f"{pair[0]}–{pair[1]}"
            if cruce not in seen:
                seen.add(cruce)
                out.append(cruce)
    return out


def etapa_de(anio):
    for label, y0, y1 in ETAPAS:
        if y0 <= anio <= y1:
            return label
    return ""


def fmt(v, decimals=4):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return round(v, decimals) if isinstance(v, float) else v


def es_por_construccion(x_id, y_id, misma_metrica):
    if misma_metrica:
        return True
    if frozenset([x_id, y_id]) in ACTIVOS_NUEVOS:
        return True
    if frozenset([x_id, y_id]) in RATIO_POR_CONSTRUCCION:
        return True
    def _nc_sc_nci(vid):
        return vid.startswith("nc_") or vid.startswith("sc_") or vid.startswith("nci_")
    if _nc_sc_nci(x_id) and y_id.startswith("exprev_"):
        return True
    if _nc_sc_nci(y_id) and x_id.startswith("exprev_"):
        return True
    return False


def es_solapamiento_definicion(x_id, y_id):
    def _starts(vid, prefix):
        return vid.startswith(prefix + "_")
    if (_starts(x_id, "anmcc") and _starts(y_id, "cdiv")) or \
       (_starts(y_id, "anmcc") and _starts(x_id, "cdiv")):
        return True
    if (_starts(x_id, "le") and _starts(y_id, "dev_exp")) or \
       (_starts(y_id, "le") and _starts(x_id, "dev_exp")):
        return True
    if (_starts(x_id, "le") and y_id == "nuevos_commits_conteo") or \
       (_starts(y_id, "le") and x_id == "nuevos_commits_conteo"):
        return True
    if (_starts(x_id, "rexp") and _starts(y_id, "rexprev")) or \
       (_starts(y_id, "rexp") and _starts(x_id, "rexprev")):
        return True
    return False


def es_robusta(cat, estable, rho_corr, rho_canary):
    if cat not in ("positiva", "negativa"):
        return False
    if not estable:
        return False
    if not isinstance(rho_corr, float) or math.isnan(rho_corr):
        return False
    if isinstance(rho_canary, float) and not math.isnan(rho_canary):
        return (rho_corr >= 0) == (rho_canary >= 0)
    return True


def es_robusta_tamano(robusta, rho_corr, rho_tamano):
    """robusta AND |rho_tamano| >= 0.1 AND mismo signo que rho_corr."""
    if not robusta:
        return False
    if not isinstance(rho_tamano, float) or math.isnan(rho_tamano):
        return False
    if not isinstance(rho_corr, float) or math.isnan(rho_corr):
        return False
    if abs(rho_tamano) < 0.1:
        return False
    return (rho_corr >= 0) == (rho_tamano >= 0)


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
               EXTRACT(YEAR FROM p.fecha_inicio)::int,
               p.etiqueta,
               TO_CHAR(p.fecha_inicio, 'YYYYMMDDHHMMSS'),
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


# ── Calcular correlaciones por par ────────────────────────────────────────────

def compute_pair(x_data_e, y_data_e, x_data_c, y_data_c):
    common = sorted(set(x_data_e) & set(y_data_e))
    rows_e = []
    for pnum in common:
        xd, yd = x_data_e[pnum], y_data_e[pnum]
        if xd[1] is None or yd[1] is None:
            continue
        dur = xd[0] if xd[0] is not None else yd[0]
        rows_e.append((pnum, dur, xd[1], yd[1], xd[2], xd[3], xd[4]))

    n = len(rows_e)
    empty = (n, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan,
             0.0, 0.0, 10, {}, [], [], rows_e, np.nan)
    if n < 5:
        return empty

    x_vals = [r[2] for r in rows_e]
    y_vals = [r[3] for r in rows_e]
    pnums  = [r[0] for r in rows_e]
    durs   = [r[1] for r in rows_e]
    anios  = [r[4] for r in rows_e]

    rho_c, p_c = spearmanr(x_vals, y_vals)
    ps = partial_spearman(x_vals, y_vals, pnums, durs)

    rho_lin  = ps["rho_lineal"]
    rho_corr = ps["rho_corr"]
    p_corr   = ps["p_corr"]
    ic_inf   = ps["ic_inf"]
    ic_sup   = ps["ic_sup"]
    rx_r     = ps["rx_r"]
    ry_r     = ps["ry_r"]
    r1x      = ps["r1x"]
    r1y      = ps["r1y"]
    n_ef     = ps["n_efectiva"]

    rho_per = {}
    for label, y0, y1 in ETAPAS:
        idx = [i for i, a in enumerate(anios) if a is not None and y0 <= a <= y1]
        if len(idx) < 15:
            continue
        xp = [x_vals[i] for i in idx]; yp = [y_vals[i] for i in idx]
        pp = [pnums[i] for i in idx];  dp = [durs[i] for i in idx]
        rho_per[label] = partial_spearman(xp, yp, pp, dp)["rho_corr"]

    rho_canary = np.nan
    if x_data_c and y_data_c:
        common_c = sorted(set(x_data_c) & set(y_data_c))
        rows_c = [(x_data_c[p][1], y_data_c[p][1], x_data_c[p][0], p)
                  for p in common_c
                  if x_data_c[p][1] is not None and y_data_c[p][1] is not None]
        if len(rows_c) >= 5:
            xc = [r[0] for r in rows_c]; yc = [r[1] for r in rows_c]
            dc = [r[2] for r in rows_c]; pc = [r[3] for r in rows_c]
            rho_canary = partial_spearman(xc, yc, pc, dc)["rho_corr"]

    return (n, rho_c, p_c, rho_lin, rho_corr, ic_inf, ic_sup, p_corr,
            r1x, r1y, n_ef, rho_per, rx_r, ry_r, rows_e, rho_canary)


# ── Categoría y fuerza ────────────────────────────────────────────────────────

def categoria_y_fuerza(por_construccion, n, p_fdr, rho_corr, ic_inf, ic_sup):
    if por_construccion:
        return "control", ""
    if n < 30:
        return "insuficiente", ""
    rho = rho_corr if (isinstance(rho_corr, float) and not math.isnan(rho_corr)) else 0.0
    ic_ok = (isinstance(ic_inf, float) and not math.isnan(ic_inf) and
             isinstance(ic_sup, float) and not math.isnan(ic_sup))
    if ic_ok and ic_inf >= -0.2 and ic_sup <= 0.2:
        cat = "sin_relacion"
    elif isinstance(p_fdr, float) and p_fdr < 0.05:
        cat = "positiva" if rho > 0 else "negativa"
    else:
        cat = "no_concluyente"
    if abs(rho) < 0.1:
        fuerza = ""
    elif abs(rho) < 0.3:
        fuerza = "debil"
    elif abs(rho) < 0.5:
        fuerza = "moderada"
    else:
        fuerza = "fuerte"
    return cat, fuerza


# ── Escribir metodo_correlaciones.md ──────────────────────────────────────────

def write_metodo():
    md = """# Método: Correlaciones por Dimensión (3P)

## Fuente y serie

Datos de **vercel/next.js**, serie **estable** (`tipo_analisis = 'versiones'`),
excluyendo las 4 releases: `4.4.0-canary.2`, `4.4.0-canary.1`,
`v12.2.3-canary.5`, `v15.0.0-rc.1`.

Se incluye `rho_canary` calculada sobre la serie `versiones_canary`.

## Variables

- **nivel=producto**: valor de producto (`contribuyente_login IS NULL`).
- **nivel=persona_agregada**: mediana, p90, share_top10pct o conteo desde
  `persona_agregado_estable_canary.csv`, alcance=humanos.
- **ratios derivados** (estadistico=ratio): tasa_nuevos y prop_* calculados
  dividiendo conteos por release. Vacío si denominador = 0.

### Familia (variables con Persona)
tamano · composicion · intensidad · red · amplitud · otra

## Correlación corregida (Spearman parcial con tendencia flexible)

Spline natural de 4 df sobre `rank(periodo_num)` + `rank(log(duracion_días))`.
`rho_corregida_lineal` conserva el control lineal anterior.

### Muestra efectiva (n_efectiva)

Pyper-Peterman 1998: `n_ef = n × (1−r1x×r1y) / (1+r1x×r1y)`, acotado [10, n].
p_corregida: t con `n_ef − 7` gl. IC95: Fisher z con `se = 1/√(n_ef−3)`.

### Corrección por tamaño (rho_corregida_tamano)

Para pares con al menos una variable de Persona (excluye familia tamano):
misma correlación parcial controlando además por `rank(log(activos_interaccion+1))`.
K_controles = 6; gl = `n_ef − 8`.

## Benjamini-Hochberg (p_fdr)

Dentro de cada cruce, solo pares con `por_construccion = false`.

## Pares por_construccion

misma_metrica; activos ↔ nuevos del mismo canal; activos_comentarios/cierre ↔
activos_interaccion; proporciones ↔ sus dos componentes (numerador y denominador);
nc/sc/nci ↔ exprev.

## Categorías y fuerza

| Categoría | Criterio |
|---|---|
| control | `por_construccion = true` |
| insuficiente | `n < 30` |
| sin_relacion | IC95 completamente dentro de [−0,2; 0,2] |
| positiva / negativa | `p_fdr < 0,05` |
| no_concluyente | resto |

Fuerza: débil [0.1,0.3), moderada [0.3,0.5), fuerte ≥ 0.5.

## robusta y robusta_tamano

`robusta` = positiva|negativa AND estable AND rho_canary mismo signo (o vacío).
`robusta_tamano` = robusta AND |rho_corregida_tamano| ≥ 0,1 AND mismo signo.

## Unión en Looker

`pares_correlacion.par_id = pares_valores.par_id`.
"""
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  {OUT_MD.name} escrito.")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=== generar_correlaciones.py ===", flush=True)

    print("Cargando diccionario...", flush=True)
    var_dict = load_dict()
    var_ids  = sorted(var_dict.keys())
    n_vars   = len(var_ids)
    print(f"  {n_vars} variables incluidas")

    print("Cargando datos de producto (DB)...", flush=True)
    prod_data = load_producto(var_dict)

    print("Cargando persona_agregado_estable_canary.csv...", flush=True)
    agg_data   = load_persona_agg(var_dict)
    ratio_data = compute_ratio_agg(agg_data)

    all_data: dict[str, dict] = {}
    for vid in var_ids:
        r = var_dict[vid]
        if r["nivel"] == "producto":
            all_data[vid] = prod_data.get(vid, {"versiones": {}, "versiones_canary": {}})
        elif r["estadistico"] == "ratio":
            all_data[vid] = ratio_data.get(vid, {"versiones": {}, "versiones_canary": {}})
        else:
            all_data[vid] = agg_data.get(vid, {"versiones": {}, "versiones_canary": {}})

    # Datos de tamaño (activos_interaccion) para corrección de tamaño
    size_data_e = all_data.get("activos_interaccion_conteo", {}).get("versiones", {})

    n_pairs_total = n_vars * (n_vars - 1) // 2
    print(f"Generando pares ({n_vars}×{n_vars-1}//2 = {n_pairs_total})...", flush=True)

    # ── Compute all pairs ─────────────────────────────────────────────────────
    pair_results: dict[str, dict] = {}
    for x_id, y_id in combinations(var_ids, 2):
        par_id = f"{x_id}__{y_id}"
        rx = var_dict[x_id]
        ry = var_dict[y_id]

        x_data_e = all_data[x_id]["versiones"]
        y_data_e = all_data[y_id]["versiones"]
        x_data_c = all_data[x_id]["versiones_canary"]
        y_data_c = all_data[y_id]["versiones_canary"]

        (n, rho_c, p_c, rho_lin, rho_corr, ic_inf, ic_sup, p_corr,
         r1x, r1y, n_ef, rho_per, rxr, ryr, rows_e, rho_canary) = compute_pair(
            x_data_e, y_data_e, x_data_c, y_data_c)

        misma_meta   = (rx["metrica_id"] == ry["metrica_id"])
        por_constr   = es_por_construccion(x_id, y_id, misma_meta)
        solapamiento = es_solapamiento_definicion(x_id, y_id)

        dims_x = set(rx["dims_texto"].split("+")) if rx["dims_texto"] != "Sin dimensión" else set()
        dims_y = set(ry["dims_texto"].split("+")) if ry["dims_texto"] != "Sin dimensión" else set()
        cruces = cruces_para_par(dims_x, dims_y)

        familia_x = rx.get("familia", "")
        familia_y = ry.get("familia", "")
        misma_fam = (familia_x != "" and familia_x == familia_y)

        # Estabilidad temporal
        n_eval = len(rho_per)
        rho_global = rho_corr if isinstance(rho_corr, float) and not math.isnan(rho_corr) else 0.0
        n_mismo = sum(1 for r in rho_per.values()
                      if isinstance(r, float) and not math.isnan(r)
                      and (r >= 0) == (rho_global >= 0))
        estable = (n_eval >= 3 and n_mismo == n_eval)

        # Corrección por tamaño
        rho_tamano = np.nan
        has_persona = "Persona" in dims_x or "Persona" in dims_y
        if (has_persona and not por_constr
                and familia_x != "tamano" and familia_y != "tamano"
                and n >= 5):
            size_rows = [
                (vx, vy, pnum, dur if dur else 1.0, size_data_e[pnum][1])
                for pnum, dur, vx, vy, anio, ver, fh in rows_e
                if pnum in size_data_e and size_data_e[pnum][1] is not None
            ]
            if len(size_rows) >= 5:
                xv = [r[0] for r in size_rows]
                yv = [r[1] for r in size_rows]
                pp = [r[2] for r in size_rows]
                dd = [r[3] for r in size_rows]
                sv = [safe_log(r[4] + 1) for r in size_rows]
                ps_sz = partial_spearman(xv, yv, pp, dd, extra_controls=[sv])
                rho_tamano = ps_sz["rho_corr"]

        pair_results[par_id] = dict(
            x_id=x_id, y_id=y_id,
            x_nombre=rx["nombre_legible"], y_nombre=ry["nombre_legible"],
            x_dims=rx["dims_texto"], y_dims=ry["dims_texto"],
            x_persona_por_nivel=rx.get("dim_persona_por_nivel", 0),
            y_persona_por_nivel=ry.get("dim_persona_por_nivel", 0),
            x_familia=familia_x, y_familia=familia_y, misma_familia=misma_fam,
            misma_metrica=misma_meta,
            por_construccion=por_constr,
            solapamiento_definicion=solapamiento,
            n=n,
            rho_cruda=rho_c, p_cruda=p_c,
            rho_corregida_lineal=rho_lin,
            rho_corregida=rho_corr, ic_inf=ic_inf, ic_sup=ic_sup,
            p_corregida=p_corr,
            r1x=r1x, r1y=r1y, n_efectiva=n_ef,
            rho_per=rho_per,
            n_periodos_evaluables=n_eval,
            n_periodos_mismo_signo=n_mismo,
            estable=estable,
            rho_canary=rho_canary,
            rho_corregida_tamano=rho_tamano,
            cruces=cruces,
            rx_r=rxr, ry_r=ryr,
            rows_e=rows_e,
            adv_x=rx.get("advertencia", ""),
            adv_y=ry.get("advertencia", ""),
        )

    print(f"  {len(pair_results)} pares calculados")

    # ── Benjamini-Hochberg por cruce ──────────────────────────────────────────
    print("Aplicando Benjamini-Hochberg por cruce...", flush=True)
    cruce_pvals: dict[str, list] = defaultdict(list)
    for par_id, pr in pair_results.items():
        if pr["por_construccion"]:
            continue
        for cruce in pr["cruces"]:
            p = pr.get("p_corregida")
            cruce_pvals[cruce].append(((cruce, par_id),
                                       p if isinstance(p, float) else np.nan))

    bh_results: dict[tuple, float | str] = {}
    for cruce, kp_list in cruce_pvals.items():
        bh_results.update(benjamini_hochberg(kp_list))

    # ── Escribir pares_correlacion.csv ────────────────────────────────────────
    print("Escribiendo pares_correlacion.csv...", flush=True)
    COLS_PARES = [
        "par_id", "cruce", "x_id", "y_id", "x_nombre", "y_nombre",
        "x_dims", "y_dims", "x_persona_por_nivel", "y_persona_por_nivel",
        "x_familia", "y_familia", "misma_familia",
        "misma_metrica", "por_construccion", "solapamiento_definicion",
        "n", "rho_cruda", "p_cruda",
        "rho_corregida_lineal",
        "rho_corregida", "ic_inf", "ic_sup", "p_corregida",
        "r1x", "r1y", "n_efectiva",
        "p_fdr",
        "rho_2016_2019", "rho_2020_2022", "rho_2023_2024", "rho_2025_2026",
        "n_periodos_evaluables", "n_periodos_mismo_signo", "estable",
        "rho_canary", "rho_corregida_tamano",
        "categoria", "fuerza", "robusta", "robusta_tamano", "advertencia",
    ]
    n_pares_rows = 0
    with open(OUT_PARES, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS_PARES)
        w.writeheader()
        for par_id, pr in sorted(pair_results.items()):
            for cruce in pr["cruces"]:
                p_fdr       = bh_results.get((cruce, par_id), "")
                rho_corr_v  = pr["rho_corregida"]
                rho_tamano  = pr["rho_corregida_tamano"]
                cat, fuerza = categoria_y_fuerza(
                    pr["por_construccion"], pr["n"],
                    p_fdr if isinstance(p_fdr, float) else np.nan,
                    rho_corr_v, pr["ic_inf"], pr["ic_sup"])
                robusta      = es_robusta(cat, pr["estable"], rho_corr_v, pr["rho_canary"])
                robusta_tam  = es_robusta_tamano(robusta, rho_corr_v, rho_tamano)
                rho_per      = pr["rho_per"]
                adv = " | ".join(dict.fromkeys(a for a in [pr["adv_x"], pr["adv_y"]] if a))
                w.writerow({
                    "par_id":   par_id, "cruce":   cruce,
                    "x_id":     pr["x_id"], "y_id": pr["y_id"],
                    "x_nombre": pr["x_nombre"], "y_nombre": pr["y_nombre"],
                    "x_dims":   pr["x_dims"],   "y_dims":   pr["y_dims"],
                    "x_persona_por_nivel": pr["x_persona_por_nivel"],
                    "y_persona_por_nivel": pr["y_persona_por_nivel"],
                    "x_familia":     pr["x_familia"],
                    "y_familia":     pr["y_familia"],
                    "misma_familia": pr["misma_familia"],
                    "misma_metrica":         pr["misma_metrica"],
                    "por_construccion":      pr["por_construccion"],
                    "solapamiento_definicion": pr["solapamiento_definicion"],
                    "n":               pr["n"],
                    "rho_cruda":       fmt(pr["rho_cruda"]),
                    "p_cruda":         fmt(pr["p_cruda"]),
                    "rho_corregida_lineal": fmt(pr["rho_corregida_lineal"]),
                    "rho_corregida":   fmt(rho_corr_v),
                    "ic_inf":          fmt(pr["ic_inf"]),
                    "ic_sup":          fmt(pr["ic_sup"]),
                    "p_corregida":     fmt(pr["p_corregida"]),
                    "r1x":             fmt(pr["r1x"]),
                    "r1y":             fmt(pr["r1y"]),
                    "n_efectiva":      pr["n_efectiva"],
                    "p_fdr":    fmt(p_fdr) if isinstance(p_fdr, float) else "",
                    "rho_2016_2019":  fmt(rho_per.get("2016-2019", np.nan)),
                    "rho_2020_2022":  fmt(rho_per.get("2020-2022", np.nan)),
                    "rho_2023_2024":  fmt(rho_per.get("2023-2024", np.nan)),
                    "rho_2025_2026":  fmt(rho_per.get("2025-2026", np.nan)),
                    "n_periodos_evaluables":  pr["n_periodos_evaluables"],
                    "n_periodos_mismo_signo": pr["n_periodos_mismo_signo"],
                    "estable":          pr["estable"],
                    "rho_canary":       fmt(pr["rho_canary"]),
                    "rho_corregida_tamano": fmt(rho_tamano),
                    "categoria":        cat,
                    "fuerza":           fuerza,
                    "robusta":          robusta,
                    "robusta_tamano":   robusta_tam,
                    "advertencia":      adv,
                })
                n_pares_rows += 1

    mb_pares = OUT_PARES.stat().st_size / 1e6
    print(f"  {n_pares_rows} filas, {mb_pares:.1f} MB")

    # ── Escribir pares_valores (con split si > 90 MB) ─────────────────────────
    print("Escribiendo pares_valores.csv...", flush=True)
    COLS_VALS = [
        "par_id", "cruces", "relacion", "periodo_num", "version", "fecha_hora",
        "anio", "etapa", "duracion_dias", "x_valor", "y_valor",
        "x_ajustado", "y_ajustado",
    ]

    # Collect rows first to check size
    vals_rows_persona = []
    vals_rows_resto   = []
    for par_id, pr in sorted(pair_results.items()):
        if not pr["rows_e"]:
            continue
        relacion    = f"{pr['x_nombre']} vs {pr['y_nombre']}"
        cruces_str  = "|".join(pr["cruces"])
        rx_r = pr["rx_r"]
        ry_r = pr["ry_r"]
        has_persona_pair = (
            pr["x_dims"] != "Sin dimensión" and "Persona" in pr["x_dims"] or
            pr["y_dims"] != "Sin dimensión" and "Persona" in pr["y_dims"]
        )
        for i, (pnum, dur, vx, vy, anio, ver, fh) in enumerate(pr["rows_e"]):
            row_d = {
                "par_id":   par_id, "cruces": cruces_str, "relacion": relacion,
                "periodo_num": pnum, "version": ver, "fecha_hora": fh,
                "anio": anio, "etapa": etapa_de(anio) if anio else "",
                "duracion_dias": fmt(dur, 2),
                "x_valor": fmt(vx), "y_valor": fmt(vy),
                "x_ajustado": fmt(rx_r[i]) if i < len(rx_r) else "",
                "y_ajustado": fmt(ry_r[i]) if i < len(ry_r) else "",
            }
            if has_persona_pair:
                vals_rows_persona.append(row_d)
            else:
                vals_rows_resto.append(row_d)

    n_vals_total = len(vals_rows_persona) + len(vals_rows_resto)
    # Estimate MB: ~240 bytes/row
    est_mb = n_vals_total * 240 / 1e6
    split = est_mb > 90

    if not split:
        with open(OUT_VALS, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS_VALS)
            w.writeheader()
            w.writerows(vals_rows_persona + vals_rows_resto)
        mb_vals = OUT_VALS.stat().st_size / 1e6
        print(f"  {n_vals_total:,} filas, {mb_vals:.1f} MB  → {OUT_VALS.name}")
    else:
        with open(OUT_VALS_P, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS_VALS)
            w.writeheader(); w.writerows(vals_rows_persona)
        with open(OUT_VALS_R, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS_VALS)
            w.writeheader(); w.writerows(vals_rows_resto)
        mb_p = OUT_VALS_P.stat().st_size / 1e6
        mb_r = OUT_VALS_R.stat().st_size / 1e6
        print(f"  SPLIT: pares_valores_persona.csv {len(vals_rows_persona):,} filas "
              f"{mb_p:.1f} MB  +  pares_valores_resto.csv {len(vals_rows_resto):,} filas "
              f"{mb_r:.1f} MB")

    write_metodo()

    # ── revision_persona.csv ──────────────────────────────────────────────────
    print("Escribiendo revision_persona.csv...", flush=True)
    COLS_REV = [
        "x_id", "y_id", "x_familia", "y_familia", "misma_familia",
        "solapamiento_definicion",
        "n", "n_efectiva", "rho_cruda", "rho_corregida", "rho_corregida_tamano",
        "ic_inf", "ic_sup",
        "rho_2016_2019", "rho_2020_2022", "rho_2023_2024", "rho_2025_2026",
        "rho_canary", "categoria", "robusta", "robusta_tamano",
    ]
    all_par_rows = []
    with open(OUT_PARES, newline="", encoding="utf-8") as f:
        all_par_rows = list(csv.DictReader(f))

    n_rev = 0
    with open(OUT_REV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS_REV)
        w.writeheader()
        for r in all_par_rows:
            if r["cruce"] != "Persona–Persona" or r["categoria"] == "control":
                continue
            w.writerow({c: r[c] for c in COLS_REV})
            n_rev += 1
    mb_rev = OUT_REV.stat().st_size / 1e6
    print(f"  {n_rev:,} filas, {mb_rev:.1f} MB")

    # ── Validaciones ──────────────────────────────────────────────────────────
    print("\n=== VALIDACIONES ===\n", flush=True)
    mb_vals_show = OUT_VALS.stat().st_size / 1e6 if not split else mb_p + mb_r
    print(f"  pares_correlacion.csv : {n_pares_rows:>7,} filas, {mb_pares:.1f} MB")
    print(f"  pares_valores         : {n_vals_total:>7,} filas, {mb_vals_show:.1f} MB "
          f"({'split' if split else 'único'})")
    print(f"  revision_persona.csv  : {n_rev:>7,} filas, {mb_rev:.1f} MB")

    cruces_list = ["Persona–Persona", "Persona–Proceso", "Persona–Producto",
                   "Proceso–Proceso", "Proceso–Producto", "Producto–Producto"]

    print("\n── Persona–Persona: conteo por categoría ──")
    cr = "Persona–Persona"
    pp_rows = [r for r in all_par_rows if r["cruce"] == cr]
    cat_cnt = defaultdict(int)
    for r in pp_rows:
        cat_cnt[r["categoria"]] += 1
    for cat in ["control","negativa","no_concluyente","positiva","sin_relacion"]:
        print(f"  {cat:<18}: {cat_cnt.get(cat,0):>4}")
    n_rob   = sum(1 for r in pp_rows if r["robusta"] == "True")
    n_robt  = sum(1 for r in pp_rows if r["robusta_tamano"] == "True")
    print(f"  {'robusta':<18}: {n_rob:>4}")
    print(f"  {'robusta_tamano':<18}: {n_robt:>4}")

    # Familia breakdown for PP non-control pairs
    pp_nc = [r for r in pp_rows if r["categoria"] != "control"]
    familias = ["tamano","composicion","intensidad","red","amplitud","otra"]

    print("\n── Persona–Persona: robusta y robusta_tamano dentro/entre familias ──")
    print(f"  {'par':<26} {'total':>5} {'robusta':>7} {'rob_tam':>7}")
    print("  " + "-" * 50)

    def fam_label(fx, fy):
        if not fx and not fy:
            return "sin_familia"
        if fx == fy:
            return f"{fx} × {fx}"
        pair = tuple(sorted([fx, fy]))
        return f"{pair[0]} × {pair[1]}"

    fam_stats = defaultdict(lambda: [0, 0, 0])  # [total, robusta, rob_tam]
    for r in pp_nc:
        lbl = fam_label(r["x_familia"], r["y_familia"])
        fam_stats[lbl][0] += 1
        if r["robusta"] == "True":
            fam_stats[lbl][1] += 1
        if r["robusta_tamano"] == "True":
            fam_stats[lbl][2] += 1

    for lbl, (tot, rob, robt) in sorted(fam_stats.items(),
                                         key=lambda x: -x[1][2]):
        print(f"  {lbl:<26} {tot:>5} {rob:>7} {robt:>7}")

    print("\n── Matriz familia × familia: robusta_tamano (count / max |rho_tam|) ──")
    fam_mat = defaultdict(lambda: defaultdict(lambda: [0, 0.0]))
    for r in pp_nc:
        fx, fy = r["x_familia"], r["y_familia"]
        if not fx or not fy:
            continue
        f1, f2 = (fx, fy) if fx <= fy else (fy, fx)
        if r["robusta_tamano"] == "True" and r["rho_corregida_tamano"]:
            fam_mat[f1][f2][0] += 1
            fam_mat[f1][f2][1] = max(fam_mat[f1][f2][1],
                                     abs(float(r["rho_corregida_tamano"])))

    hdr_cols = [f[:6] for f in familias]
    print(f"  {'':>12} " + " ".join(f"{h:>8}" for h in hdr_cols))
    for f1 in familias:
        row_str = f"  {f1:<12} "
        for f2 in familias:
            k1, k2 = (f1, f2) if f1 <= f2 else (f2, f1)
            entry = fam_mat[k1][k2]
            if entry[0] > 0:
                row_str += f"{entry[0]:>3}/{entry[1]:.2f} "
            else:
                row_str += f"{'':>8} "
        print(row_str)

    print("\n── Robusta_tamano entre familias distintas, sin solapamiento "
          "(ordenado por |rho_corregida_tamano|) ──")
    between = [r for r in pp_nc
               if r["robusta_tamano"] == "True"
               and r["x_familia"] != r["y_familia"]
               and r["solapamiento_definicion"] == "False"
               and r["rho_corregida_tamano"]]
    between.sort(key=lambda r: abs(float(r["rho_corregida_tamano"])), reverse=True)
    hdr = (f"  {'x_id':<30} {'y_id':<30} {'xfam':<12} {'yfam':<12} "
           f"{'rho_cc':>7} {'rho_tam':>7}")
    print(hdr)
    print("  " + "-"*(len(hdr)-2))
    for r in between:
        print(f"  {r['x_id']:<30} {r['y_id']:<30} "
              f"{r['x_familia']:<12} {r['y_familia']:<12} "
              f"{r['rho_corregida']:>7} {r['rho_corregida_tamano']:>7}")
    if not between:
        print("  (ninguno)")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
