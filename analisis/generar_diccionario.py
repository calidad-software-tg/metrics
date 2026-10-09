#!/usr/bin/env python3
"""
analisis/generar_diccionario.py

Genera analisis/salidas/diccionario_variables.csv:
  - Variables de producto: resultado con contribuyente_login IS NULL, serie estable.
  - Variables de persona agregada: persona_agregado_estable_canary.csv,
    alcance='humanos', serie=versiones (estable).
  - activos_commits, activos_interaccion, nuevos_commits, nuevos_interaccion:
    columna n_contribuyentes, Persona.

Exclusiones automáticas:
  - pct_moda > 80 %
  - n_estable < 30

Dimensiones por métrica (planilla del equipo):
  Persona               : ss, rexp, fexp, disc_centrality
  Persona+Proceso       : exprev, rexprev, cdiv, nc, sc, dev_exp
  Persona+Producto      : le, cd
  Proceso               : dis, schedule_compliance, process_performance,
                          jarczyk_success_rate
  Proceso+Producto      : anmcc, mttr, rc, cfdr, nub, noi
  Producto              : dloc
  nci                   : Proceso (confirmado por planilla del equipo)
  wp/nob_42/noi_28      : excluidas (constante o casi-duplicada)
  activos_cierre, activos_comentarios: conteo (n_contribuyentes), Persona
"""
import csv
import sys
from collections import Counter
from math import isnan
from pathlib import Path

import psycopg2
from scipy.stats import spearmanr

ROOT   = Path(__file__).resolve().parent.parent
SALIDA = ROOT / "analisis" / "salidas" / "diccionario_variables.csv"
AGG_CSV = ROOT / "persona_agregado_estable_canary.csv"

DB = dict(host="localhost", port=5432, dbname="resultados_metricas",
          user="metricas", password="metricas")

EXCLUIR_ESTABLE = frozenset({
    "4.4.0-canary.2", "4.4.0-canary.1", "v12.2.3-canary.5", "v15.0.0-rc.1"
})

# ── Dimensiones por métrica ──────────────────────────────────────────────────
DIMS: dict[str, tuple[int, int, int]] = {
    # metrica_id: (dim_persona, dim_proceso, dim_producto)
    "ss":                    (1, 0, 0),
    "rexp":                  (1, 0, 0),
    "fexp":                  (1, 0, 0),
    "disc_centrality":       (1, 0, 0),
    "exprev":                (1, 1, 0),
    "rexprev":               (1, 1, 0),
    "cdiv":                  (1, 1, 0),
    "nc":                    (1, 1, 0),
    "sc":                    (1, 1, 0),
    "dev_exp":               (1, 1, 0),
    "le":                    (1, 0, 1),
    "cd":                    (1, 0, 1),
    "dis":                   (0, 1, 0),
    "schedule_compliance":   (0, 1, 0),
    "process_performance":   (0, 1, 0),
    "jarczyk_success_rate":  (0, 1, 0),
    "anmcc":                 (0, 1, 1),
    "mttr":                  (0, 1, 1),
    "rc":                    (0, 1, 1),
    "cfdr":                  (0, 1, 1),
    "nub":                   (0, 1, 1),
    "noi":                   (0, 1, 1),
    "dloc":                  (0, 0, 1),
    "nci":                   (0, 1, 0),  # PENDIENTE — tratada como Proceso
    # activos/nuevos: Persona
    "activos_commits":       (1, 0, 0),
    "activos_interaccion":   (1, 0, 0),
    "activos_cierre":        (1, 0, 0),
    "activos_comentarios":   (1, 0, 0),
    "nuevos_commits":        (1, 0, 0),
    "nuevos_interaccion":    (1, 0, 0),
    # proporciones derivadas: Persona
    "tasa_nuevos_commits":     (1, 0, 0),
    "tasa_nuevos_interaccion": (1, 0, 0),
    "prop_commitean":          (1, 0, 0),
    "prop_cierran":            (1, 0, 0),
    "prop_comentan":           (1, 0, 0),
}

DIM_NAMES = {(1,0,0): "Persona", (1,1,0): "Persona+Proceso",
             (1,0,1): "Persona+Producto", (0,1,0): "Proceso",
             (0,1,1): "Proceso+Producto", (0,0,1): "Producto"}

ADVERTENCIAS = {
    "nub": ("NUB inflado en 2025-2026: 39 ventanas cuentan 'Error Handling'/'Error Overlay' como bugs "
            "(substring match en _KEYWORDS_BUG); solo releases desde mediados de 2020 — antes el repo no clasificaba bugs"),
    "cfdr": "Solo releases desde mediados de 2020 — antes el repo no clasificaba bugs",
    "dis": "DIS: posible falso positivo por etiquetas que contienen 'doc' (ej. 'Docker') debido a match de subcadena en _DOC_KEYWORDS",
    "ss": ("Lenguajes del usuario tomados hoy (snapshot actual de repos propios), no en cada release; "
           "tope de 15 contribuyentes activos por ventana (bots excluidos del tope)"),
}

# Métricas a incluir como producto (tienen contribuyente_login IS NULL en versiones)
METRICAS_PRODUCTO = {
    "anmcc", "cd", "cfdr", "dis", "dloc", "jarczyk_success_rate",
    "le", "mttr", "nci", "nob_42", "noi", "noi_28", "nub",
    "process_performance", "rc", "schedule_compliance", "wp",
}
# Excluidas explícitamente por ser constantes o casi-duplicadas
EXCLUIDAS_FIJAS = {
    "wp":     "valor constante 0 en todas las ventanas estables",
    "nob_42": "valor constante 2706 en todas las ventanas estables",
    "noi_28": "prácticamente idéntica a noi (difieren en 1 ventana de 371)",
}

# Métricas de persona con estadísticos adicionales (p90 y share_top10pct)
EXTRA_STATS = {"nc", "exprev", "sc", "nci", "cdiv", "dloc"}

# Nombres legibles
NOMBRES = {
    "anmcc":               "ANMCC (Avg Modified Components per Commit)",
    "cd":                  "CD (Comment Density)",
    "cdiv":                "CDIV (Contribution Diversity)",
    "cfdr":                "CFDR (Customer Found Defects & Regressions)",
    "dev_exp":             "dev_exp (Development Experience)",
    "dis":                 "DIS (Doc Issue Survival)",
    "disc_centrality":     "Disc. Centrality (Discussion Centrality)",
    "dloc":                "DLOC (Documentation Lines of Code)",
    "exprev":              "EXPRev (Code Review Experience)",
    "fexp":                "FEXP (File Experience)",
    "jarczyk_success_rate":"Jarczyk Success Rate",
    "le":                  "LE (Learning Ease)",
    "mttr":                "MTTR (Mean Time to Repair)",
    "nc":                  "NC (Number of Comments)",
    "nci":                 "NCI (Number of Closed Issues)",
    "noi":                 "NOI (Number of Open Issues)",
    "nub":                 "NUB (Bugs Detected by Users)",
    "process_performance": "Process Performance",
    "rc":                  "RC (Readme Completeness)",
    "rexp":                "REXP (Recent Experience)",
    "rexprev":             "REXPRev (Recent Review Experience)",
    "sc":                  "SC (Social Contribution)",
    "schedule_compliance": "Schedule Compliance",
    "ss":                  "SS (Skill Similarity)",
    "activos_commits":         "Activos (commits)",
    "activos_interaccion":     "Activos (interacción)",
    "activos_cierre":          "Activos (cierre de issues)",
    "activos_comentarios":     "Activos (comentarios)",
    "nuevos_commits":          "Nuevos contribuyentes (commits)",
    "nuevos_interaccion":      "Nuevos contribuyentes (interacción)",
    "tasa_nuevos_commits":     "Tasa de ingreso (commits)",
    "tasa_nuevos_interaccion": "Tasa de ingreso (interacción)",
    "prop_commitean":          "Proporción que commitea",
    "prop_cierran":            "Proporción que cierra issues",
    "prop_comentan":           "Proporción que comenta",
}


# ── Familia (solo para variables con Persona) ────────────────────────────────
_TAMANO      = {"activos_commits","activos_interaccion","activos_cierre",
                "activos_comentarios","nuevos_commits","nuevos_interaccion"}
_COMPOSICION = {"dev_exp","le","rexp","ss",
                "tasa_nuevos_commits","tasa_nuevos_interaccion",
                "prop_commitean","prop_cierran","prop_comentan"}
_INTENSIDAD  = {"nc","exprev","sc","nci","dloc"}    # solo p90/share_top10pct
_AMPLITUD    = {"cdiv","anmcc","fexp"}


def get_familia(metrica_id: str, estadistico: str, dp_eff: int) -> str:
    if not dp_eff:
        return ""
    if metrica_id in _TAMANO:
        return "tamano"
    if metrica_id in _COMPOSICION:
        return "composicion"
    if metrica_id in _INTENSIDAD and estadistico in ("p90", "share_top10pct"):
        return "intensidad"
    if metrica_id == "rexprev":
        return "intensidad"
    if metrica_id == "disc_centrality":
        return "red"
    if metrica_id in _AMPLITUD:
        return "amplitud"
    return "otra"


# Ratios derivados: (metrica_id_ratio, numerador_mid, denominador_mid)
RATIO_DEFS = [
    ("tasa_nuevos_commits",     "nuevos_commits",     "activos_commits"),
    ("tasa_nuevos_interaccion", "nuevos_interaccion", "activos_interaccion"),
    ("prop_commitean",          "activos_commits",    "activos_interaccion"),
    ("prop_cierran",            "activos_cierre",     "activos_interaccion"),
    ("prop_comentan",           "activos_comentarios","activos_interaccion"),
]
RATIO_ADVERTENCIA = ("Proporción derivada: numerador/denominador por release; "
                     "vacío si denominador = 0")


def pct_moda(vals: list) -> float:
    if not vals:
        return 0.0
    c = Counter(round(v, 4) if isinstance(v, float) else v for v in vals)
    return c.most_common(1)[0][1] / len(vals) * 100


def spearman_safe(x: list, y: list) -> str:
    pairs = [(xi, yi) for xi, yi in zip(x, y)
             if xi is not None and yi is not None
             and not (isinstance(xi, float) and isnan(xi))
             and not (isinstance(yi, float) and isnan(yi))]
    if len(pairs) < 5:
        return ""
    xs, ys = zip(*pairs)
    rho, _ = spearmanr(xs, ys)
    return f"{rho:.3f}"


def dims_texto(dp, dpr, dpo) -> str:
    parts = []
    if dp:  parts.append("Persona")
    if dpr: parts.append("Proceso")
    if dpo: parts.append("Producto")
    return "+".join(parts) if parts else "Sin dimensión"


# ── Leer datos de producto desde la DB ──────────────────────────────────────

def fetch_producto(cur) -> dict[str, dict]:
    """Devuelve {metrica_id: {(periodo_num, duracion_dias, value), ...}}"""
    cur.execute("""
        SELECT r.metrica_id,
               p.periodo_num,
               EXTRACT(EPOCH FROM (p.fecha_fin - p.fecha_inicio)) / 86400.0 AS duracion_dias,
               r.value,
               p.tipo_analisis
        FROM resultado r
        JOIN periodo p ON p.periodo_id = r.periodo_id
        WHERE r.contribuyente_login IS NULL
          AND p.etiqueta NOT IN %s
        ORDER BY r.metrica_id, p.periodo_num
    """, (tuple(EXCLUIR_ESTABLE),))
    out: dict[str, list] = {}
    for metrica_id, pnum, dur, val, tipo in cur.fetchall():
        out.setdefault(metrica_id, []).append((pnum, dur, val, tipo))
    return out


# ── Leer persona_agregado_estable_canary.csv ─────────────────────────────────

def load_agregado() -> dict[str, dict]:
    """
    Devuelve {metrica_id: {estadistico: [(periodo_num, duracion_dias, value)]}}
    Solo alcance='humanos', estable (serie='versiones').
    Para activos_*/nuevos_*: estadistico='conteo', value=n_contribuyentes.
    """
    data: dict[str, dict] = {}
    is_activos = {"activos_commits", "activos_interaccion",
                  "activos_cierre", "activos_comentarios",
                  "nuevos_commits", "nuevos_interaccion", "cuentas_por_tipo"}
    with open(AGG_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["alcance"] != "humanos":
                continue
            mid = row["metrica_id"]
            serie = row["serie"]
            try:
                pnum = int(row["periodo_num"])
                dur  = float(row["duracion_dias"]) if row["duracion_dias"] else None
            except (ValueError, KeyError):
                continue

            def safe_float(s):
                try:
                    v = float(s)
                    return None if isnan(v) else v
                except (TypeError, ValueError):
                    return None

            if mid in is_activos:
                v = safe_float(row.get("n_contribuyentes", ""))
                data.setdefault(mid, {}).setdefault("conteo", []).append(
                    (pnum, dur, v, serie))
                continue

            # Métricas normales: siempre mediana
            for stat, col in [("mediana", "mediana"), ("p90", "p90"),
                               ("share_top10pct", "share_top10pct")]:
                if stat != "mediana" and mid not in EXTRA_STATS:
                    continue
                v = safe_float(row.get(col, ""))
                data.setdefault(mid, {}).setdefault(stat, []).append(
                    (pnum, dur, v, serie))

    # ── Proporciones derivadas ────────────────────────────────────────────────
    for ratio_mid, num_mid, den_mid in RATIO_DEFS:
        # Index denominador y numerador por (pnum, serie)
        den_idx = {(pnum, s): v for pnum, _, v, s in data.get(den_mid, {}).get("conteo", [])}
        num_idx = {(pnum, s): v for pnum, _, v, s in data.get(num_mid, {}).get("conteo", [])}
        dur_idx = {(pnum, s): d for pnum, d, _, s in data.get(den_mid, {}).get("conteo", [])}
        ratio_list = []
        for (pnum, serie), den_v in sorted(den_idx.items()):
            num_v = num_idx.get((pnum, serie))
            if den_v is None or den_v == 0 or num_v is None:
                continue
            dur = dur_idx.get((pnum, serie))
            ratio_list.append((pnum, dur, num_v / den_v, serie))
        data[ratio_mid] = {"ratio": ratio_list}
    return data


# ── Construir filas del diccionario ──────────────────────────────────────────

def build_rows(prod_data, agg_data) -> list[dict]:
    rows = []

    def make_row(variable_id, nombre_legible, metrica_id, nivel, estadistico,
                 dp, dpr, dpo, series_data, extra_advertencia="",
                 motivo_exclusion="", obs=""):
        estable = [(pn, dur, v) for pn, dur, v, s in series_data
                   if s == "versiones"]
        canary  = [(pn, dur, v) for pn, dur, v, s in series_data
                   if s == "versiones_canary"]

        vals_e = [v for _, _, v in estable if v is not None]
        n_e = len(vals_e)
        n_c = len([v for _, _, v in canary if v is not None])

        pm = pct_moda(vals_e) if vals_e else 0.0

        nums_e  = [pn  for pn, _, v in estable if v is not None]
        durs_e  = [dur for _, dur, v in estable if v is not None and dur is not None]
        rho_t   = spearman_safe(nums_e, vals_e)
        rho_d   = spearman_safe(durs_e[:len(vals_e)], vals_e[:len(durs_e)])

        # Regla de dimensión por nivel:
        #   producto      → sin Persona (0, dpr, dpo)
        #   persona_agreg → siempre dim_persona=1; dim_persona_por_nivel=True
        #                   cuando la métrica no la tiene intrínsecamente
        if nivel == "producto":
            dp_eff, dpr_eff, dpo_eff = 0, dpr, dpo
            dp_por_nivel = False
        else:
            dp_eff = 1          # persona_agregada siempre tiene Persona
            dpr_eff, dpo_eff = dpr, dpo
            dp_por_nivel = (dp == 0)  # True cuando la métrica no tenía dim_persona

        dt = dims_texto(dp_eff, dpr_eff, dpo_eff)

        incluida = "sí"
        motivo = motivo_exclusion
        if not motivo:
            if n_e < 30:
                incluida = "no"
                motivo = f"n_estable={n_e} < 30"
            elif pm > 80:
                incluida = "no"
                motivo = f"pct_moda={pm:.1f}% > 80%"
            # Excluidas fijas (producto)
            if metrica_id in EXCLUIDAS_FIJAS and not motivo_exclusion:
                incluida = "no"
                motivo = EXCLUIDAS_FIJAS[metrica_id]
        else:
            incluida = "no"

        adv = ADVERTENCIAS.get(metrica_id, "")
        if extra_advertencia:
            adv = (adv + " | " + extra_advertencia).strip(" |")
        if obs:
            adv = (adv + " | " + obs).strip(" |")

        return dict(
            variable_id=variable_id,
            nombre_legible=nombre_legible,
            metrica_id=metrica_id,
            nivel=nivel,
            estadistico=estadistico,
            dim_persona=dp_eff,
            dim_proceso=dpr_eff,
            dim_producto=dpo_eff,
            dim_persona_por_nivel=int(dp_por_nivel) if nivel == "persona_agregada" else 0,
            dims_texto=dt,
            familia=get_familia(metrica_id, estadistico, dp_eff),
            n_estable=n_e,
            n_canary=n_c,
            pct_moda=f"{pm:.1f}",
            rho_tiempo=rho_t,
            rho_duracion=rho_d,
            incluida=incluida,
            motivo_exclusion=motivo,
            advertencia=adv,
        )

    # ── Variables de PRODUCTO ─────────────────────────────────────────────────
    for mid, series_list in sorted(prod_data.items()):
        if mid not in DIMS and mid not in EXCLUIDAS_FIJAS:
            continue  # ignorar métricas sin dimensión (viejos seeds, etc.)
        dp, dpr, dpo = DIMS.get(mid, (0, 0, 0))
        nombre = NOMBRES.get(mid, mid)
        excl_motivo = EXCLUIDAS_FIJAS.get(mid, "")
        # Producto hereda dims SIN Persona
        dp_prod, dpr_prod, dpo_prod = 0, dpr, dpo
        # Si era solo Persona (dp=1, dpr=0, dpo=0) no hay variable de producto
        if dp == 1 and dpr == 0 and dpo == 0:
            continue
        vid = f"{mid}_producto"
        rows.append(make_row(
            vid, f"{nombre} [producto]", mid, "producto", "valor",
            dp_prod, dpr_prod, dpo_prod,
            series_list, motivo_exclusion=excl_motivo,
        ))

    # ── Variables de PERSONA AGREGADA ─────────────────────────────────────────
    ratio_mids = {r[0] for r in RATIO_DEFS}
    for mid, stats in sorted(agg_data.items()):
        if mid == "cuentas_por_tipo":
            continue
        dp, dpr, dpo = DIMS.get(mid, (0, 0, 0))
        nombre = NOMBRES.get(mid, mid)
        extra_adv = RATIO_ADVERTENCIA if mid in ratio_mids else ""
        for stat, series_list in sorted(stats.items()):
            vid = f"{mid}_{stat}" if stat != "valor" else mid
            rows.append(make_row(
                vid, f"{nombre} [{stat}]", mid, "persona_agregada", stat,
                dp, dpr, dpo, series_list, extra_advertencia=extra_adv,
            ))

    return rows


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("=== generar_diccionario.py ===", flush=True)

    con = psycopg2.connect(**DB)
    cur = con.cursor()

    print("Cargando datos de producto desde DB...", flush=True)
    prod_data = fetch_producto(cur)
    con.close()

    print("Cargando persona_agregado_estable_canary.csv...", flush=True)
    agg_data = load_agregado()

    print("Construyendo diccionario...", flush=True)
    rows = build_rows(prod_data, agg_data)

    COLS = [
        "variable_id", "nombre_legible", "metrica_id", "nivel", "estadistico",
        "dim_persona", "dim_proceso", "dim_producto", "dim_persona_por_nivel",
        "dims_texto", "familia",
        "n_estable", "n_canary", "pct_moda", "rho_tiempo", "rho_duracion",
        "incluida", "motivo_exclusion", "advertencia",
    ]
    with open(SALIDA, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)

    incluidas = [r for r in rows if r["incluida"] == "sí"]
    excluidas = [r for r in rows if r["incluida"] == "no"]
    print(f"\nTotal variables: {len(rows)} ({len(incluidas)} incluidas, {len(excluidas)} excluidas)")
    print(f"CSV escrito en: {SALIDA}")

    # ── Resumen por dimensión ─────────────────────────────────────────────────
    from collections import defaultdict
    dims_count: dict[str, int] = defaultdict(int)
    for r in incluidas:
        dims_count[r["dims_texto"]] += 1

    print("\nIncluidas por dimensión:")
    for d, n in sorted(dims_count.items()):
        print(f"  {d}: {n}")

    # ── Pares por cruce ───────────────────────────────────────────────────────
    from itertools import combinations
    dim_vars: dict[str, list] = defaultdict(list)
    for r in incluidas:
        for d in r["dims_texto"].split("+"):
            dim_vars[d].append(r["variable_id"])

    # unique variables per dimension (a variable can appear in multiple dims)
    cruces = {
        "Persona–Persona":   sum(1 for a, b in combinations(incluidas, 2)
                                  if a["dim_persona"] and b["dim_persona"]),
        "Persona–Proceso":   sum(1 for a, b in combinations(incluidas, 2)
                                  if (a["dim_persona"] and b["dim_proceso"])
                                  or (a["dim_proceso"] and b["dim_persona"])),
        "Persona–Producto":  sum(1 for a, b in combinations(incluidas, 2)
                                  if (a["dim_persona"] and b["dim_producto"])
                                  or (a["dim_producto"] and b["dim_persona"])),
        "Proceso–Proceso":   sum(1 for a, b in combinations(incluidas, 2)
                                  if a["dim_proceso"] and b["dim_proceso"]),
        "Proceso–Producto":  sum(1 for a, b in combinations(incluidas, 2)
                                  if (a["dim_proceso"] and b["dim_producto"])
                                  or (a["dim_producto"] and b["dim_proceso"])),
        "Producto–Producto": sum(1 for a, b in combinations(incluidas, 2)
                                  if a["dim_producto"] and b["dim_producto"]),
    }
    print("\nPares por cruce (variables incluidas):")
    for cruce, n in cruces.items():
        print(f"  {cruce}: {n} pares")

    # ── Tabla resumen ─────────────────────────────────────────────────────────
    print("\n── Tabla completa ──")
    header = f"{'variable_id':<35} {'nivel':<16} {'estadistico':<14} {'dims_texto':<22} {'n_estable':>9} {'n_canary':>9} {'pct_moda':>8} {'rho_t':>6} {'rho_d':>6} {'inc':>4}"
    print(header)
    print("-" * len(header))
    for r in rows:
        inc = "SÍ" if r["incluida"] == "sí" else "--"
        print(f"{r['variable_id']:<35} {r['nivel']:<16} {r['estadistico']:<14} "
              f"{r['dims_texto']:<22} {r['n_estable']:>9} {r['n_canary']:>9} "
              f"{r['pct_moda']:>8} {str(r['rho_tiempo']):>6} {str(r['rho_duracion']):>6} {inc:>4}")
        if r["motivo_exclusion"]:
            print(f"  ↳ EXCLUIDA: {r['motivo_exclusion']}")
        if r["advertencia"]:
            print(f"  ⚠  {r['advertencia']}")


if __name__ == "__main__":
    main()
