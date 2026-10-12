#!/usr/bin/env python3
"""
analisis/generar_correlaciones.py

Genera:
  analisis/salidas/pares_correlacion.csv
  analisis/salidas/pares_valores.csv          (o _persona / _resto si > 90 MB)
  analisis/salidas/metodo_correlaciones.md
  analisis/salidas/revision_persona.csv

Además de la correlación corregida, cada par incluye chequeos de sensibilidad:
sin ventanas de menos de 1 día, con tendencia local (escala de la relación),
fuerza por período (alcance temporal) y control por tamaño; y un resumen
(hallazgo_candidato, nivel_evidencia, motivo_descarte). Ver metodo_correlaciones.md.
"""
import csv
import math
import os
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

# Chequeos de sensibilidad
UMBRAL_FUERZA        = 0.1   # |rho| mínimo para que una relación "exista"
MIN_VENTANAS_PERIODO = 15    # ventanas mínimas para evaluar un período
DIAS_MINIMOS         = 1.0   # ventanas más cortas se excluyen en rho_corregida_sin_cortas
VENTANA_LOCAL        = 21    # releases por grado de libertad del spline de tendencia local

# Pares de métricas cuya definición se solapa, además de las reglas de
# es_solapamiento_definicion: DLOC cuenta las líneas de los README.md que evalúa
# README Completeness; cada bug abierto (CFDR/NUB) es una issue abierta (NOI).
SOLAPAMIENTO_METRICAS = {frozenset({"dloc", "rc"}), frozenset({"noi", "cfdr"}), frozenset({"noi", "nub"})}
ADVERTENCIA_DLOC = ("DLOC no cuenta archivos .mdx: la documentación oficial (docs/) pasó de .md a .mdx "
                    "en 2023 (v13.4 → v14.0) y desde entonces no se cuenta")


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


# ── Chequeos de sensibilidad ─────────────────────────────────────────────────

def parcial_df(x_vals, y_vals, pnums, durs, df_spline):
    """Spearman parcial como partial_spearman (versión spline), con el df del
    spline de tendencia configurable. Devuelve rho e IC95 con n efectiva."""
    nan = dict(rho=np.nan, ic_inf=np.nan, ic_sup=np.nan)
    n = len(x_vals)
    if n < 5:
        return nan
    rx = rankdata(x_vals, method="average")
    ry = rankdata(y_vals, method="average")
    rp = rankdata(pnums, method="average")
    rd = rankdata([safe_log(d) for d in durs], method="average")
    X = np.column_stack([np.ones(n), natural_spline_basis(rp, df=df_spline), rd])

    def resid(v):
        coef, *_ = np.linalg.lstsq(X, v, rcond=None)
        return v - X @ coef

    ex, ey = resid(rx), resid(ry)
    if ex.std() == 0 or ey.std() == 0:
        return nan
    rho = float(np.corrcoef(ex, ey)[0, 1])
    orden = np.argsort(pnums)
    r1x, r1y = ar1_coef(ex[orden]), ar1_coef(ey[orden])
    den = 1.0 + r1x * r1y
    n_ef = n if den <= 0 else int(min(float(n), max(10.0, n * (1.0 - r1x * r1y) / den)))
    if n_ef <= 3:
        return dict(rho=rho, ic_inf=np.nan, ic_sup=np.nan)
    z = math.atanh(float(np.clip(rho, -1 + 1e-10, 1 - 1e-10)))
    se = 1.0 / math.sqrt(max(1e-10, n_ef - 3))
    return dict(rho=rho, ic_inf=math.tanh(z - 1.96 * se), ic_sup=math.tanh(z + 1.96 * se))


def excluye_cero(ic_inf, ic_sup):
    return (ic_inf > 0 or ic_sup < 0) if not (np.isnan(ic_inf) or np.isnan(ic_sup)) else False


def mismo_signo(a, b):
    return (a >= 0) == (b >= 0)


def alcance_temporal(estados):
    """Patrón a partir del estado de cada período ('+', '-', '0' o None)."""
    ev = [(nombre, e) for nombre, e in estados if e is not None]
    signos = {e for _, e in ev if e in "+-"}
    if not signos:
        return "sin relación en ningún período"
    if len(signos) == 2:
        return "cambia de signo"
    con = [i for i, (_, e) in enumerate(ev) if e in "+-"]
    contiguos = con == list(range(con[0], con[-1] + 1))
    if len(con) == len(ev):
        patron = "toda la historia"
    elif contiguos and con[-1] == len(ev) - 1:
        patron = f"desde {ev[con[0]][0][:4]}"
    elif contiguos:
        patron = f"solo {ev[con[0]][0][:4]}-{ev[con[-1]][0][-4:]}"
    else:
        patron = "intermitente"
    if len(ev) < 3:
        patron += f" ({len(ev)} períodos evaluables)"
    return patron


def chequeos_par(rows_e):
    """Sobre las ventanas del par (rows_e de compute_pair):
    - sin ventanas de menos de DIAS_MINIMOS días;
    - con tendencia local (un df del spline cada VENTANA_LOCAL releases);
    - por período, con IC95: '+'/'-' si |rho| >= UMBRAL_FUERZA y el IC95 no incluye el 0."""
    out = {}
    if len(rows_e) < 5:
        return out
    pn = [r[0] for r in rows_e]
    du = [r[1] if r[1] else 1.0 for r in rows_e]
    xv = [r[2] for r in rows_e]
    yv = [r[3] for r in rows_e]
    an = [r[4] for r in rows_e]
    anios = [a for a in an if a is not None]
    out["anio_desde"] = min(anios) if anios else ""
    out["anio_hasta"] = max(anios) if anios else ""

    idx = [i for i, d in enumerate(du) if d >= DIAS_MINIMOS]
    r = parcial_df([xv[i] for i in idx], [yv[i] for i in idx],
                   [pn[i] for i in idx], [du[i] for i in idx], df_spline=4)
    out.update(n_sin_cortas=len(idx), rho_corregida_sin_cortas=r["rho"],
               ic_sin_cortas_inf=r["ic_inf"], ic_sin_cortas_sup=r["ic_sup"])

    df_local = max(4, round(len(rows_e) / VENTANA_LOCAL))
    r = parcial_df(xv, yv, pn, du, df_spline=df_local)
    out.update(df_tendencia_local=df_local, rho_corregida_local=r["rho"],
               ic_local_inf=r["ic_inf"], ic_local_sup=r["ic_sup"])

    estados = []
    for label, y0, y1 in ETAPAS:
        ii = [i for i, a in enumerate(an) if a is not None and y0 <= a <= y1]
        r = dict(rho=np.nan, ic_inf=np.nan, ic_sup=np.nan)
        if len(ii) >= MIN_VENTANAS_PERIODO:
            r = parcial_df([xv[i] for i in ii], [yv[i] for i in ii],
                           [pn[i] for i in ii], [du[i] for i in ii], df_spline=4)
        clave = label.replace("-", "_")
        out[f"ic_{clave}"] = (f"[{r['ic_inf']:.2f}; {r['ic_sup']:.2f}]"
                              if not np.isnan(r["ic_inf"]) else "")
        if np.isnan(r["rho"]):
            estado = None
        elif abs(r["rho"]) >= UMBRAL_FUERZA and excluye_cero(r["ic_inf"], r["ic_sup"]):
            estado = "+" if r["rho"] > 0 else "-"
        else:
            estado = "0"
        out[f"estado_{clave}"] = estado or ""
        estados.append((label, estado))
    out["alcance_temporal"] = alcance_temporal(estados)
    return out


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


# Versiones alternativas de una misma métrica (branch de fixes): un par entre una de estas
# y su métrica base, o entre dos versiones de la misma, es control (misma métrica).
VARIANTE_DE = {"mttr_p50": "mttr", "mttr_bugs": "mttr", "mttr_con_bots": "mttr", "nci_con_bots": "nci"}


def metrica_base(metrica_id: str) -> str:
    return VARIANTE_DE.get(metrica_id, metrica_id)


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


def es_solapamiento_definicion(x_id, y_id, metricas=None):
    """metricas: (metrica_id de x, metrica_id de y), para las reglas de SOLAPAMIENTO_METRICAS."""
    if metricas and frozenset(metricas) in SOLAPAMIENTO_METRICAS:
        return True

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


def replica_en_canary(rho_corr, rho_canary):
    """Mismo signo en canary, o sin dato en canary."""
    if isinstance(rho_canary, float) and not math.isnan(rho_canary):
        return (rho_corr >= 0) == (rho_canary >= 0)
    return True


def depende_de_ventanas_cortas(rho_corr, rho_sin_cortas):
    """La relación (|rho| >= UMBRAL_FUERZA) cambia de signo o baja del umbral
    sin las ventanas de menos de DIAS_MINIMOS días."""
    if not isinstance(rho_corr, float) or math.isnan(rho_corr) or abs(rho_corr) < UMBRAL_FUERZA:
        return False
    if not isinstance(rho_sin_cortas, float) or math.isnan(rho_sin_cortas):
        return True
    return not mismo_signo(rho_sin_cortas, rho_corr) or abs(rho_sin_cortas) < UMBRAL_FUERZA


def es_robusta(cat, estable, rho_corr, rho_canary, depende_cortas=False):
    if cat not in ("positiva", "negativa"):
        return False
    if not estable or depende_cortas:
        return False
    if not isinstance(rho_corr, float) or math.isnan(rho_corr):
        return False
    return replica_en_canary(rho_corr, rho_canary)


def resiste_tamano(rho_corr, rho_tamano):
    """None si el control por tamaño no se calculó; si no, |rho_tamano| >= 0.1 y
    mismo signo que rho_corr."""
    if not isinstance(rho_tamano, float) or math.isnan(rho_tamano):
        return None
    if not isinstance(rho_corr, float) or math.isnan(rho_corr):
        return False
    return bool(abs(rho_tamano) >= UMBRAL_FUERZA and mismo_signo(rho_tamano, rho_corr))


def es_robusta_tamano(robusta, rho_corr, rho_tamano):
    """robusta AND resiste el control por tamaño. Vacío si el control no aplica."""
    ok = resiste_tamano(rho_corr, rho_tamano)
    return "" if ok is None else bool(robusta and ok)


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

No hace falta logaritmo ni dividir por días: la correlación trabaja con rangos y
descuenta la duración de la ventana en todos los pares.

### Corrección por tamaño (rho_corregida_tamano)

Para todos los pares salvo los de control y los que incluyen una variable de la
familia tamano (`tamano_aplica`): misma correlación parcial controlando además por
`rank(log(activos_interaccion+1))`. K_controles = 6; gl = `n_ef − 8`.
Si no aplica queda vacía.

## Benjamini-Hochberg (p_fdr)

Dentro de cada cruce, solo pares con `por_construccion = false`.

## Pares por_construccion

misma_metrica; activos ↔ nuevos del mismo canal; activos_comentarios/cierre ↔ activos_interaccion;
proporciones ↔ sus dos componentes (numerador y denominador); nc/sc/nci ↔ exprev.

## solapamiento_definicion

Métricas distintas cuya definición comparte ingredientes: ANMCC ↔ Contribution
Diversity; Learning Easy ↔ Development Experience; Learning Easy ↔ nuevos en commits;
REXP ↔ REXPRev; DLOC ↔ README Completeness (DLOC cuenta las líneas de los README.md);
NOI ↔ CFDR / NUB (cada bug abierto es una issue abierta).

## misma_familia

Las dos variables tienen la misma familia, salvo "otra" (que agrupa variables sin
familia propia y no es un aspecto común).

## Categorías y fuerza

| Categoría | Criterio |
|---|---|
| control | `por_construccion = true` |
| insuficiente | `n < 30` |
| sin_relacion | IC95 completamente dentro de [−0,2; 0,2] |
| positiva / negativa | `p_fdr < 0,05` |
| no_concluyente | resto |

Fuerza: débil [0.1,0.3), moderada [0.3,0.5), fuerte ≥ 0.5.

## Chequeos de sensibilidad

| Columna | Qué calcula |
|---|---|
| `rho_corregida_sin_cortas` | La correlación corregida sin las ventanas de menos de 1 día |
| `depende_ventanas_cortas` | \\|rho_corregida\\| ≥ 0,1 y, sin las ventanas cortas, cambia de signo o baja de 0,1 |
| `rho_corregida_local` | La correlación corregida con una tendencia local: spline con un grado de libertad cada ~21 releases (`df_tendencia_local`) |
| `escala_relacion` | Solo pares significativos. "release a release" si con la tendencia local mantiene el signo, \\|rho\\| ≥ 0,1 y su IC95 no incluye el 0; si no, "cambio de etapa" |
| `ic_AAAA_AAAA`, `estado_AAAA_AAAA` | Por período, IC95 de la correlación corregida y estado: `+` / `-` si \\|rho\\| ≥ 0,1 y el IC95 no incluye el 0, `0` si no, vacío si no es evaluable |
| `alcance_temporal` | Toda la historia, desde AAAA, solo AAAA-AAAA, intermitente, cambia de signo o sin relación en ningún período |
| `anio_desde`, `anio_hasta` | Años que cubren las ventanas del par (los pares con CFDR / NUB empiezan en 2019–2020) |

## estable, robusta y robusta_tamano

`estable` = al menos 3 períodos evaluables y el mismo signo que rho_corregida en todos.
`robusta` = positiva|negativa AND estable AND rho_canary mismo signo (o vacío)
AND NOT depende_ventanas_cortas.
`robusta_tamano` = robusta AND |rho_corregida_tamano| ≥ 0,1 AND mismo signo
(vacío si el control por tamaño no aplica).

## hallazgo_candidato y nivel_evidencia

`hallazgo_candidato` = robusta AND NOT solapamiento_definicion AND NOT misma_familia
AND (resiste el control por tamaño, o el control no aplica).

`nivel_evidencia` (solo hallazgos): **alta** si `alcance_temporal` = toda la historia y
`escala_relacion` = release a release; **baja** si no tiene fuerza en ningún período o
es un cambio de etapa; **media** en el resto.

`motivo_descarte` lista por qué un par no es hallazgo.

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

    excl = excluir_backports(all_data)
    print(f"  backports excluidos: {excl['versiones']} estables, {excl['versiones_canary']} canary")

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

        metricas     = (rx["metrica_id"], ry["metrica_id"])
        misma_meta   = (metrica_base(metricas[0]) == metrica_base(metricas[1]))
        por_constr   = es_por_construccion(x_id, y_id, misma_meta)
        solapamiento = es_solapamiento_definicion(x_id, y_id, metricas)

        dims_x = set(rx["dims_texto"].split("+")) if rx["dims_texto"] != "Sin dimensión" else set()
        dims_y = set(ry["dims_texto"].split("+")) if ry["dims_texto"] != "Sin dimensión" else set()
        cruces = cruces_para_par(dims_x, dims_y)

        familia_x = rx.get("familia", "")
        familia_y = ry.get("familia", "")
        # "otra" agrupa variables sin familia propia: no cuenta como familia compartida
        misma_fam = (familia_x not in ("", "otra") and familia_x == familia_y)

        # Estabilidad temporal
        n_eval = len(rho_per)
        rho_global = rho_corr if isinstance(rho_corr, float) and not math.isnan(rho_corr) else 0.0
        n_mismo = sum(1 for r in rho_per.values()
                      if isinstance(r, float) and not math.isnan(r)
                      and (r >= 0) == (rho_global >= 0))
        estable = (n_eval >= 3 and n_mismo == n_eval)

        # Corrección por tamaño: en todos los pares salvo control y familia tamaño
        rho_tamano = np.nan
        tamano_aplica = (not por_constr and familia_x != "tamano" and familia_y != "tamano")
        if tamano_aplica and n >= 5:
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

        advertencias = [rx.get("advertencia", ""), ry.get("advertencia", "")]
        if "dloc" in metricas:
            advertencias.append(ADVERTENCIA_DLOC)

        pair_results[par_id] = dict(
            chequeos_par(rows_e),
            tamano_aplica=tamano_aplica,
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
            advertencia=" | ".join(dict.fromkeys(a for a in advertencias if a)),
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
        # chequeos de sensibilidad
        "anio_desde", "anio_hasta",
        "n_sin_cortas", "rho_corregida_sin_cortas", "ic_sin_cortas_inf", "ic_sin_cortas_sup",
        "depende_ventanas_cortas",
        "df_tendencia_local", "rho_corregida_local", "ic_local_inf", "ic_local_sup",
        "escala_relacion",
        "ic_2016_2019", "ic_2020_2022", "ic_2023_2024", "ic_2025_2026",
        "estado_2016_2019", "estado_2020_2022", "estado_2023_2024", "estado_2025_2026",
        "alcance_temporal", "tamano_aplica",
        "hallazgo_candidato", "nivel_evidencia", "motivo_descarte",
    ]
    COLS_CHEQUEOS = ["anio_desde", "anio_hasta", "n_sin_cortas", "df_tendencia_local",
                     "ic_2016_2019", "ic_2020_2022", "ic_2023_2024", "ic_2025_2026",
                     "estado_2016_2019", "estado_2020_2022", "estado_2023_2024", "estado_2025_2026",
                     "alcance_temporal"]
    COLS_CHEQUEOS_NUM = ["rho_corregida_sin_cortas", "ic_sin_cortas_inf", "ic_sin_cortas_sup",
                         "rho_corregida_local", "ic_local_inf", "ic_local_sup"]
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
                significativa = cat in ("positiva", "negativa")
                depende_cortas = depende_de_ventanas_cortas(rho_corr_v, pr.get("rho_corregida_sin_cortas", np.nan))
                robusta      = es_robusta(cat, pr["estable"], rho_corr_v, pr["rho_canary"], depende_cortas)
                robusta_tam  = es_robusta_tamano(robusta, rho_corr_v, rho_tamano)
                tamano_ok    = resiste_tamano(rho_corr_v, rho_tamano)
                rho_per      = pr["rho_per"]

                # Escala: ¿la relación se mantiene con una tendencia local?
                rho_loc = pr.get("rho_corregida_local", np.nan)
                local_ok = (isinstance(rho_loc, float) and not math.isnan(rho_loc)
                            and isinstance(rho_corr_v, float) and not math.isnan(rho_corr_v)
                            and mismo_signo(rho_loc, rho_corr_v) and abs(rho_loc) >= UMBRAL_FUERZA
                            and excluye_cero(pr.get("ic_local_inf", np.nan), pr.get("ic_local_sup", np.nan)))
                escala = "" if not significativa else ("release a release" if local_ok else "cambio de etapa")

                # Hallazgo candidato y motivo de descarte
                hallazgo = bool(robusta and not pr["solapamiento_definicion"]
                                and not pr["misma_familia"] and tamano_ok is not False)
                alcance = pr.get("alcance_temporal", "")
                nivel = ""
                if hallazgo:
                    if alcance == "toda la historia" and escala == "release a release":
                        nivel = "alta"
                    elif alcance.startswith("sin relación") or escala == "cambio de etapa":
                        nivel = "baja"
                    else:
                        nivel = "media"
                motivos = []
                if pr["por_construccion"]:
                    motivos.append("control (por construcción)")
                elif not significativa:
                    motivos.append(f"categoría: {cat}")
                else:
                    if not pr["estable"]:
                        motivos.append("cambia de signo entre períodos")
                    if not replica_en_canary(rho_corr_v, pr["rho_canary"]):
                        motivos.append("no se repite en canary")
                    if depende_cortas:
                        motivos.append("depende de las ventanas de menos de 1 día")
                    if pr["solapamiento_definicion"]:
                        motivos.append("solapamiento de definición")
                    if pr["misma_familia"]:
                        motivos.append("misma familia")
                    if tamano_ok is False:
                        motivos.append("no resiste el control por tamaño")

                chequeos = {c: pr.get(c, "") for c in COLS_CHEQUEOS}
                chequeos.update({c: fmt(pr.get(c, np.nan)) for c in COLS_CHEQUEOS_NUM})
                w.writerow({
                    **chequeos,
                    "depende_ventanas_cortas": depende_cortas,
                    "escala_relacion":  escala,
                    "tamano_aplica":    pr["tamano_aplica"],
                    "hallazgo_candidato": hallazgo,
                    "nivel_evidencia":  nivel,
                    "motivo_descarte":  "" if hallazgo else "; ".join(motivos),
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
                    "advertencia":      pr["advertencia"],
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
        "alcance_temporal", "escala_relacion", "hallazgo_candidato", "nivel_evidencia",
        "motivo_descarte",
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
