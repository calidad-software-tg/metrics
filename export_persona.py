#!/usr/bin/env python3
"""
export_persona.py  —  Exporta métricas de persona para vercel/next.js.

Genera:
  metricas_persona.csv
  persona_detalle_estable.csv
  persona_agregado_estable_canary.csv

Y valida:
  - Tamaño / filas de cada archivo
  - % de filas y value con identidad=nombre por métrica
  - Top-20 posibles duplicados login+nombre-git (split de identidad)
  - nci suma vs. valor producto por release
  - Top-10 contribuyentes por sum(value) en estable con SOSPECHOSO
"""
import csv, os, re, sys
from collections import defaultdict
from math import ceil, isnan
from pathlib import Path

import psycopg2
import psycopg2.extras

ROOT = Path(__file__).resolve().parent
DB = dict(host="localhost", port=5432, dbname="resultados_metricas",
          user="metricas", password="metricas")

EXCLUIR_ESTABLE = frozenset({
    "4.4.0-canary.2", "4.4.0-canary.1", "v12.2.3-canary.5", "v15.0.0-rc.1"
})

METRICAS_COMMITS     = frozenset({"anmcc","cdiv","fexp","rexp","le"})
METRICAS_INTERACCION = frozenset({"nc","exprev","rexprev","disc_centrality","sc","nci","mttr","dis"})
METRICAS_FOTO        = frozenset({"cd","dloc","rc"})
METRICAS_ACUM        = frozenset({"dev_exp"})
METRICAS_PERFIL      = frozenset({"ss"})
TODAS_PERSONA = METRICAS_COMMITS | METRICAS_INTERACCION | METRICAS_FOTO | METRICAS_ACUM | METRICAS_PERFIL
NON_HUMAN = frozenset({"bot","agente_ia","desconocido"})

_LOGIN_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$')

# ── helpers ──────────────────────────────────────────────────────────────────

def identidad(login: str) -> str:
    if ' ' in login:
        return 'nombre'
    if not _LOGIN_RE.match(login):
        return 'nombre'
    return 'login'

def fmt_v(v) -> str:
    if v is None: return ''
    try:
        f = float(v)
        if isnan(f): return ''
    except (TypeError, ValueError): return ''
    s = f"{f:.4f}".rstrip('0')
    if s.endswith('.'): s += '0'
    return s

def fmt_ts(dt) -> str:
    return dt.strftime('%Y%m%d%H%M%S') if dt else ''

def fmt_dur(ini, fin) -> str:
    if ini is None or fin is None: return ''
    return f"{(fin - ini).total_seconds() / 86400:.2f}"

def agg_stats(vals: list[float]) -> dict:
    """n, suma, media, mediana, p90, maximo, share_top1, share_top10pct."""
    if not vals:
        return {k: '' for k in ('n','suma','media','mediana','p90','maximo','share_top1','share_top10pct')}
    s = sorted(vals)
    n = len(s)
    total = sum(s)
    mid   = (s[n//2-1]+s[n//2])/2 if n%2==0 else s[n//2]
    p90   = s[min(ceil(0.9*n)-1, n-1)]
    st1   = fmt_v(s[-1]/total) if total else ''
    n_top = max(1, ceil(0.1*n))
    st10  = fmt_v(sum(s[-n_top:])/total) if total else ''
    return dict(n=n, suma=fmt_v(total), media=fmt_v(total/n),
                mediana=fmt_v(mid), p90=fmt_v(p90), maximo=fmt_v(s[-1]),
                share_top1=st1, share_top10pct=st10)

def load_bots() -> dict[str, str]:
    out: dict[str,str] = {}
    with open(ROOT / 'bots_clasificados.csv', newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            out[row['login']] = row['tipo_cuenta']
    return out

def primera_fecha_lookup(cur, metricas: frozenset, tipo: str) -> dict[str,str]:
    """login → primera fecha_fin (AAAAMMDDhhmmss) en esas métricas en esa serie."""
    cur.execute("""
        SELECT r.contribuyente_login,
               MIN(p.fecha_fin) AS pf
        FROM resultado r
        JOIN periodo p ON p.periodo_id = r.periodo_id
        WHERE r.metrica_id = ANY(%s)
          AND p.tipo_analisis = %s
          AND r.contribuyente_login IS NOT NULL
        GROUP BY r.contribuyente_login
    """, (list(metricas), tipo))
    return {r[0]: fmt_ts(r[1]) for r in cur.fetchall()}

# ── ARCHIVO 3: metricas_persona.csv ──────────────────────────────────────────

METRICAS_META = [
    # (id, nombre, grupo, familia_identidad, agregacion, unidad, advertencia)
    ("anmcc","ANMCC (Número Promedio de Componentes Modificados por Commit)",
     "Actividad: commits","login (mayormente)","mediana","componentes/commit",
     "~75% de los IDs son logins GitHub; resto nombres git (fallback sin cuenta vinculada)"),
    ("cdiv","CDIV (Contribution Diversity)",
     "Actividad: commits","login o nombre git","mediana","archivos únicos",
     "~75% nombres git. Sin cap de commits (run_versiones_local, git log --numstat completo)"),
    ("fexp","FEXP (Experiencia en Archivos)",
     "Actividad: commits","login o nombre git","mediana","commits previos en mismos archivos",
     "~75% nombres git. Sin cap de commits. Experiencia intra-ventana únicamente"),
    ("rexp","REXP (Experiencia Reciente)",
     "Actividad: commits","login o nombre git","mediana","score ponderado (sum 1/(días+1))",
     "~75% nombres git. Sin cap de commits. Ponderación exponencial por recencia"),
    ("le","LE (Learning Ease)",
     "Actividad: commits","login o nombre git","mediana","días",
     "~75% nombres git. Primera contribución histórica al componente (run_versiones_local). "
     "Componente = sub-proyecto en monorepos (packages/X, apps/X, etc.)"),
    ("nc","NC (Number of Comments)",
     "Actividad: issues/PRs/comentarios","login","suma","comentarios",
     "IssueCommentEvent + CommitCommentEvent + PullRequestReviewCommentEvent. Sin tope"),
    ("exprev","EXPRev (Experiencia en Revisión de Código)",
     "Actividad: issues/PRs/comentarios","login","suma","eventos",
     "issues abiertos+cerrados + PRs abiertos+cerrados + comentarios. Sin tope"),
    ("rexprev","REXPRev (Experiencia Reciente en Revisión)",
     "Actividad: issues/PRs/comentarios","login","mediana","score ponderado",
     "Versión de EXPRev ponderada por 1/(días+1). Sin tope"),
    ("disc_centrality","Disc. Centrality (Discussion Centrality)",
     "Actividad: issues/PRs/comentarios","login","mediana","co-comentaristas únicos",
     "Grado en la MBSN (red social de discusión). Sin tope"),
    ("sc","SC (Social Contribution)",
     "Actividad: issues/PRs/comentarios","login","suma","issues+PRs abiertos",
     "issues_opened + issues_closed + prs_opened + prs_closed + prs_merged (por autor)"),
    ("nci","NCI (Number of Closed Issues)",
     "Actividad: issues/PRs/comentarios","login","suma","issues cerrados",
     "Atribuido a ClosedEvent.actor.login (quien cerró, no quien abrió)"),
    ("mttr","MTTR (Mean Time to Repair)",
     "Actividad: issues/PRs/comentarios","login","mediana","horas",
     "Atribuido a quien cerró. Compartido con NCI (misma corrida de fetch)"),
    ("dis","DIS (Doc Issue Survival)",
     "Actividad: issues/PRs/comentarios","login","mediana","días",
     "Issues con label de documentación. Atribuido a quien cerró"),
    ("dev_exp","dev_exp (Development Experience)",
     "Acumulada","login","mediana (solo activos)","meses",
     "Meses desde el primer commit histórico hasta fecha_fin. "
     "Solo incluye contribuyentes con anmcc en el mismo periodo. "
     "Cálculo acumulativo: no refleja actividad en la ventana"),
    ("cd","CD (Comment Density)",
     "Foto por último autor (500 archivos alfabéticos)","login","mediana","ratio comentarios/líneas",
     "Último autor por archivo al cierre de la ventana (blame snapshot). "
     "Solo primeros 500 archivos del árbol ordenados alfabéticamente"),
    ("dloc","DLOC (Documentation Lines of Code)",
     "Foto por último autor (500 archivos alfabéticos)","login","suma","líneas documentación",
     "Mismo criterio de atribución y tope que CD"),
    ("rc","RC (Readme Completeness)",
     "Foto por último autor (500 archivos alfabéticos)","login","mediana","ratio [0,1]",
     "7 categorías Prana et al. (2018). Atribución por último autor del README"),
    ("ss","SS (Skill Similarity)",
     "Perfil externo","login","mediana","ratio [0,1]",
     "max_contributors=15 humanos por ventana (bots excluidos del tope). "
     "user_languages = snapshot actual de repos propios del colaborador (no histórico). "
     "Cuentas con sufijo -bot y ≤12 filas clasificadas humano por regla, sin verificación individual"),
]

def write_metricas():
    p = ROOT / "metricas_persona.csv"
    cols = ["metrica_id","nombre","grupo","familia_identidad","agregacion","unidad","advertencia"]
    with open(p, 'w', newline='', encoding='utf-8') as f:
        csv.writer(f).writerows([cols] + [list(m) for m in METRICAS_META])
    return p

# ── ARCHIVO 1: persona_detalle_estable.csv ────────────────────────────────────

def write_detalle(cur, bots, pf_commits, pf_interac, exclude_cd=False):
    p = ROOT / "persona_detalle_estable.csv"
    metricas_a_exportar = (TODAS_PERSONA - METRICAS_ACUM)
    if exclude_cd:
        metricas_a_exportar = metricas_a_exportar - {"cd"}

    # anmcc contributors per periodo_id for dev_exp filter
    cur.execute("""
        SELECT p.periodo_id, r.contribuyente_login
        FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
        WHERE r.metrica_id='anmcc' AND p.tipo_analisis='versiones'
          AND r.contribuyente_login IS NOT NULL
    """)
    anmcc_set: dict[int, set] = defaultdict(set)
    for row in cur.fetchall():
        anmcc_set[row[0]].add(row[1])

    cols = ["periodo_num","version","fecha_hora","anio","duracion_dias",
            "metrica_id","contribuyente_login","tipo_cuenta","identidad",
            "value","primera_fecha_commits","primera_fecha_interaccion"]
    n = 0
    excl_tuple = tuple(EXCLUIR_ESTABLE)
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(cols)

        # Métricas no-dev_exp
        cur.execute("""
            SELECT p.periodo_id, p.periodo_num, p.etiqueta,
                   p.fecha_inicio, p.fecha_fin,
                   r.metrica_id, r.contribuyente_login, r.value
            FROM resultado r
            JOIN periodo p ON p.periodo_id=r.periodo_id
            WHERE p.tipo_analisis='versiones'
              AND r.contribuyente_login IS NOT NULL
              AND p.etiqueta NOT IN %s
              AND r.metrica_id = ANY(%s)
            ORDER BY p.periodo_num, r.metrica_id
        """, (excl_tuple, list(metricas_a_exportar)))

        while True:
            rows = cur.fetchmany(20000)
            if not rows: break
            for r in rows:
                lg = r[6]; v = r[7]
                w.writerow([
                    r[1], r[2], fmt_ts(r[4]), r[4].year, fmt_dur(r[3], r[4]),
                    r[5], lg, bots.get(lg,'humano'), identidad(lg),
                    fmt_v(v),
                    pf_commits.get(lg,''), pf_interac.get(lg,''),
                ])
                n += 1

        # dev_exp: solo si tienen anmcc en el mismo periodo
        cur.execute("""
            SELECT p.periodo_id, p.periodo_num, p.etiqueta,
                   p.fecha_inicio, p.fecha_fin,
                   r.contribuyente_login, r.value
            FROM resultado r
            JOIN periodo p ON p.periodo_id=r.periodo_id
            WHERE p.tipo_analisis='versiones'
              AND r.contribuyente_login IS NOT NULL
              AND p.etiqueta NOT IN %s
              AND r.metrica_id='dev_exp'
              AND EXISTS (
                  SELECT 1 FROM resultado r2
                  WHERE r2.periodo_id=r.periodo_id
                    AND r2.metrica_id='anmcc'
                    AND r2.contribuyente_login=r.contribuyente_login
              )
            ORDER BY p.periodo_num
        """, (excl_tuple,))
        while True:
            rows = cur.fetchmany(5000)
            if not rows: break
            for r in rows:
                lg = r[5]; v = r[6]
                w.writerow([
                    r[1], r[2], fmt_ts(r[4]), r[4].year, fmt_dur(r[3], r[4]),
                    'dev_exp', lg, bots.get(lg,'humano'), identidad(lg),
                    fmt_v(v),
                    pf_commits.get(lg,''), pf_interac.get(lg,''),
                ])
                n += 1

    mb = p.stat().st_size / 1024**2
    return p, n, mb

# ── ARCHIVO 2: persona_agregado_estable_canary.csv ────────────────────────────

def write_agregado(cur, bots, pf_commits_v, pf_interac_v, pf_commits_c, pf_interac_c):
    p = ROOT / "persona_agregado_estable_canary.csv"
    excl = tuple(EXCLUIR_ESTABLE)
    cols = ["serie","periodo_num","version","fecha_hora","anio","duracion_dias",
            "metrica_id","alcance","n_contribuyentes","suma","media","mediana",
            "p90","maximo","share_top1","share_top10pct"]

    # Structure: rows_out = list of col dicts
    rows_out: list[dict] = []

    # --- helper to make a row dict ---
    def make_row(serie, pnum, vetiq, fini, ffin, mid, alcance, stats, extra_n=None):
        n = extra_n if extra_n is not None else stats['n']
        return {
            'serie': serie, 'periodo_num': pnum, 'version': vetiq,
            'fecha_hora': fmt_ts(ffin), 'anio': ffin.year,
            'duracion_dias': fmt_dur(fini, ffin),
            'metrica_id': mid, 'alcance': alcance,
            'n_contribuyentes': n,
            'suma': stats.get('suma',''), 'media': stats.get('media',''),
            'mediana': stats.get('mediana',''), 'p90': stats.get('p90',''),
            'maximo': stats.get('maximo',''),
            'share_top1': stats.get('share_top1',''),
            'share_top10pct': stats.get('share_top10pct',''),
        }

    for serie in ('versiones', 'versiones_canary'):
        label = 'estable' if serie == 'versiones' else 'canary'
        print(f"    Procesando {label}...", flush=True)
        excl_sql = excl if serie == 'versiones' else ()

        # Load period metadata
        cur.execute("""
            SELECT periodo_id, periodo_num, etiqueta, fecha_inicio, fecha_fin
            FROM periodo WHERE tipo_analisis=%s ORDER BY periodo_num
        """, (serie,))
        periods = {r[0]: r for r in cur.fetchall()}  # {pid: (pid,pnum,etiq,ini,fin)}

        pf_commits = pf_commits_v if serie == 'versiones' else pf_commits_c
        pf_interac = pf_interac_v if serie == 'versiones' else pf_interac_c

        # ── Regular metrics ────────────────────────────────────────────────────
        for metrica in sorted(TODAS_PERSONA):
            # For dev_exp: use anmcc-filtered data
            if metrica == 'dev_exp':
                excl_clause = "AND p.etiqueta NOT IN %s" if excl_sql else ""
                params = [serie]
                if excl_sql: params.append(excl_sql)
                cur.execute(f"""
                    SELECT r.periodo_id, r.contribuyente_login, r.value
                    FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
                    WHERE p.tipo_analisis=%s
                      AND r.metrica_id='dev_exp'
                      AND r.contribuyente_login IS NOT NULL
                      {excl_clause}
                      AND EXISTS (
                        SELECT 1 FROM resultado r2
                        WHERE r2.periodo_id=r.periodo_id AND r2.metrica_id='anmcc'
                          AND r2.contribuyente_login=r.contribuyente_login
                      )
                """, params)
            else:
                excl_clause = "AND p.etiqueta NOT IN %s" if excl_sql else ""
                params = [serie, metrica]
                if excl_sql: params.append(excl_sql)
                cur.execute(f"""
                    SELECT r.periodo_id, r.contribuyente_login, r.value
                    FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
                    WHERE p.tipo_analisis=%s AND r.metrica_id=%s
                      AND r.contribuyente_login IS NOT NULL
                      {excl_clause}
                """, params)

            # Group by periodo_id
            by_period: dict[int, dict] = defaultdict(lambda: {'todas': [], 'humanos': []})
            for pid, login, val in cur.fetchall():
                if val is None: continue
                v = float(val)
                by_period[pid]['todas'].append(v)
                if bots.get(login, 'humano') == 'humano':
                    by_period[pid]['humanos'].append(v)

            for pid, pd_data in by_period.items():
                if pid not in periods: continue
                _, pnum, etiq, fini, ffin = periods[pid]
                for alcance in ('todas', 'humanos'):
                    st = agg_stats(pd_data[alcance])
                    rows_out.append(make_row(serie, pnum, etiq, fini, ffin, metrica, alcance, st))

        # ── Pseudo-métricas ─────────────────────────────────────────────────────
        # Cargar datos base para pseudo-métricas
        excl_clause = "AND p.etiqueta NOT IN %s" if excl_sql else ""

        # anmcc y exprev (base para activos/nuevos)
        for base_metrica, pf_key in [('anmcc', pf_commits), ('exprev', pf_interac)]:
            pnombre = 'activos_commits' if base_metrica == 'anmcc' else 'activos_interaccion'
            nuevos_nombre = 'nuevos_commits' if base_metrica == 'anmcc' else 'nuevos_interaccion'
            params = [serie, base_metrica] + ([excl_sql] if excl_sql else [])
            cur.execute(f"""
                SELECT r.periodo_id, r.contribuyente_login
                FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
                WHERE p.tipo_analisis=%s AND r.metrica_id=%s
                  AND r.contribuyente_login IS NOT NULL {excl_clause}
            """, params)

            by_period_logins: dict[int, list] = defaultdict(list)
            for pid, login in cur.fetchall():
                by_period_logins[pid].append(login)

            for pid, logins in by_period_logins.items():
                if pid not in periods: continue
                _, pnum, etiq, fini, ffin = periods[pid]
                ts_fin = fmt_ts(ffin)

                humanos = [l for l in logins if bots.get(l,'humano') == 'humano']
                nuevos_todas = [l for l in logins if pf_key.get(l,'') == ts_fin]
                nuevos_hum   = [l for l in humanos if pf_key.get(l,'') == ts_fin]

                for alcance, cnt_act, cnt_new in [
                    ('todas', len(logins), len(nuevos_todas)),
                    ('humanos', len(humanos), len(nuevos_hum)),
                ]:
                    rows_out.append(make_row(
                        serie, pnum, etiq, fini, ffin, pnombre, alcance,
                        {k:'' for k in ('suma','media','mediana','p90','maximo','share_top1','share_top10pct')},
                        extra_n=cnt_act
                    ))
                    rows_out.append(make_row(
                        serie, pnum, etiq, fini, ffin, nuevos_nombre, alcance,
                        {k:'' for k in ('suma','media','mediana','p90','maximo','share_top1','share_top10pct')},
                        extra_n=cnt_new
                    ))

        # activos_cierre (nci) y activos_comentarios (nc)
        for base_m, pseudo_m in [('nci','activos_cierre'), ('nc','activos_comentarios')]:
            params = [serie, base_m] + ([excl_sql] if excl_sql else [])
            cur.execute(f"""
                SELECT r.periodo_id, r.contribuyente_login
                FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
                WHERE p.tipo_analisis=%s AND r.metrica_id=%s
                  AND r.contribuyente_login IS NOT NULL {excl_clause}
            """, params)
            by_period_logins = defaultdict(list)
            for pid, login in cur.fetchall():
                by_period_logins[pid].append(login)
            for pid, logins in by_period_logins.items():
                if pid not in periods: continue
                _, pnum, etiq, fini, ffin = periods[pid]
                humanos = [l for l in logins if bots.get(l,'humano') == 'humano']
                for alcance, cnt in [('todas', len(logins)), ('humanos', len(humanos))]:
                    rows_out.append(make_row(
                        serie, pnum, etiq, fini, ffin, pseudo_m, alcance,
                        {k:'' for k in ('suma','media','mediana','p90','maximo','share_top1','share_top10pct')},
                        extra_n=cnt
                    ))

        # cuentas_por_tipo: n_contribuyentes por tipo en anmcc ∪ exprev
        params_anmcc  = [serie, 'anmcc']  + ([excl_sql] if excl_sql else [])
        params_exprev = [serie, 'exprev'] + ([excl_sql] if excl_sql else [])
        cur.execute(f"""
            SELECT DISTINCT p.periodo_id, r.contribuyente_login
            FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
            WHERE p.tipo_analisis=%s AND r.metrica_id=%s
              AND r.contribuyente_login IS NOT NULL {excl_clause}
            UNION
            SELECT DISTINCT p.periodo_id, r.contribuyente_login
            FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
            WHERE p.tipo_analisis=%s AND r.metrica_id=%s
              AND r.contribuyente_login IS NOT NULL {excl_clause}
        """, params_anmcc + params_exprev)

        by_period_tipo: dict[int, dict] = defaultdict(lambda: defaultdict(int))
        for pid, login in cur.fetchall():
            tc = bots.get(login, 'humano')
            by_period_tipo[pid][tc] += 1

        for pid, tipo_counts in by_period_tipo.items():
            if pid not in periods: continue
            _, pnum, etiq, fini, ffin = periods[pid]
            for tc, cnt in tipo_counts.items():
                rows_out.append(make_row(
                    serie, pnum, etiq, fini, ffin, 'cuentas_por_tipo', tc,
                    {k:'' for k in ('suma','media','mediana','p90','maximo','share_top1','share_top10pct')},
                    extra_n=cnt
                ))

    # Write
    with open(p, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows_out)

    mb = p.stat().st_size / 1024**2
    return p, len(rows_out), mb

# ── VALIDACIONES ─────────────────────────────────────────────────────────────

def validar(cur, bots):
    print("\n=== VALIDACIONES ===\n")

    # 1. Tamaños de archivos
    print("── [V1] Tamaños de archivos ──")
    for fn in ["metricas_persona.csv","persona_detalle_estable.csv",
               "persona_agregado_estable_canary.csv"]:
        p = ROOT / fn
        if p.exists():
            rows = sum(1 for _ in open(p, encoding='utf-8')) - 1
            print(f"  {fn}: {rows:,} filas, {p.stat().st_size/1024**2:.1f} MB")
        else:
            print(f"  {fn}: NO ENCONTRADO")

    # 2. % filas y value con identidad=nombre por métrica
    print("\n── [V2] Identidad=nombre por métrica (estable) ──")
    cur.execute("""
        SELECT r.metrica_id,
               COUNT(*) AS total,
               COUNT(*) FILTER (WHERE r.contribuyente_login LIKE '%% %%'
                                   OR r.contribuyente_login ~ '[^a-zA-Z0-9\\-]') AS cnt_nombre,
               SUM(r.value) AS total_value,
               SUM(r.value) FILTER (WHERE r.contribuyente_login LIKE '%% %%'
                                       OR r.contribuyente_login ~ '[^a-zA-Z0-9\\-]') AS val_nombre
        FROM resultado r
        JOIN periodo p ON p.periodo_id=r.periodo_id
        WHERE p.tipo_analisis='versiones'
          AND p.etiqueta NOT IN %s
          AND r.contribuyente_login IS NOT NULL
          AND r.metrica_id = ANY(%s)
        GROUP BY r.metrica_id
        ORDER BY r.metrica_id
    """, (tuple(EXCLUIR_ESTABLE), list(TODAS_PERSONA)))
    print(f"  {'metrica_id':<20} {'filas_nombre%':>14} {'value_nombre%':>14}")
    for row in cur.fetchall():
        mid, tot, cnt_n, tot_v, val_n = row
        pct_f = (cnt_n/tot*100) if tot else 0
        pct_v = (val_n/tot_v*100) if tot_v and val_n else 0
        print(f"  {mid:<20} {pct_f:>13.1f}% {pct_v:>13.1f}%")

    # 3. Top-20 duplicados login+nombre-git
    print("\n── [V3] Top-20 posibles duplicados (login ≈ nombre git) ──")
    # Encontrar pares donde un login coincide con el nombre de otro
    # Estrategia: normalizar (minúsculas, quitar espacios/guiones) y agrupar
    cur.execute("""
        SELECT contribuyente_login, SUM(value) AS total_value, COUNT(*) AS filas
        FROM resultado r
        JOIN periodo p ON p.periodo_id=r.periodo_id
        WHERE p.tipo_analisis='versiones' AND r.contribuyente_login IS NOT NULL
        GROUP BY contribuyente_login
        ORDER BY total_value DESC NULLS LAST
    """)
    rows_all = cur.fetchall()  # (login, total_value, filas)

    # Normalize: lowercase, remove spaces/hyphens
    def norm(s): return re.sub(r'[\s\-_]','', s.lower())
    by_norm: dict[str, list] = defaultdict(list)
    for login, tv, nf in rows_all:
        by_norm[norm(login)].append((login, float(tv) if tv else 0.0, nf))

    # Groups with both a login-type and a nombre-type
    candidates = []
    for key, members in by_norm.items():
        if len(members) < 2: continue
        has_login  = any(identidad(m[0]) == 'login'  for m in members)
        has_nombre = any(identidad(m[0]) == 'nombre' for m in members)
        if has_login and has_nombre:
            total_v = sum(m[1] for m in members)
            split_v = max(m[1] for m in members)  # value in "dominant" identity
            candidates.append((key, members, total_v, split_v))
    candidates.sort(key=lambda x: -x[2])

    # Known case: botv / Ben Botvinick
    print(f"  Caso conocido: botv={next((v for l,v,_ in rows_all if l=='botv'),0):.1f} | "
          f"Ben Botvinick={next((v for l,v,_ in rows_all if l=='Ben Botvinick'),0):.1f}")
    print(f"  {'login(s)':<50} {'value_total':>12} {'pct_partido%':>13}")
    printed = 0
    for key, members, total_v, split_v in candidates[:20]:
        pct = (1 - split_v/total_v)*100 if total_v else 0
        logins_str = " | ".join(f"{m[0]} ({identidad(m[0])},{m[2]}f,{m[1]:.0f}v)"
                                for m in sorted(members, key=lambda x: -x[1]))
        print(f"  {logins_str:<50} {total_v:>12.1f} {pct:>12.1f}%")
        printed += 1
    if not printed:
        print("  (Sin duplicados detectados con el criterio de normalización)")

    # 4. NCI suma vs. producto
    print("\n── [V4] NCI: suma persona vs. valor producto por release ──")
    cur.execute("""
        SELECT p.periodo_num, p.etiqueta,
               SUM(r.value) FILTER (WHERE r.contribuyente_login IS NOT NULL) AS suma_persona,
               SUM(r.value) FILTER (WHERE r.contribuyente_login IS NULL)     AS val_producto
        FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
        WHERE p.tipo_analisis='versiones'
          AND r.metrica_id='nci'
          AND p.etiqueta NOT IN %s
        GROUP BY p.periodo_num, p.etiqueta
        ORDER BY p.periodo_num
    """, (tuple(EXCLUIR_ESTABLE),))
    nci_rows = cur.fetchall()
    diffs = [(r[0], r[1], r[2], r[3],
              abs((r[2] or 0) - (r[3] or 0))) for r in nci_rows if r[4] is not None]
    diffs.sort(key=lambda x: -x[4])
    print(f"  {'pnum':>5} {'version':<25} {'suma_pers':>10} {'prod':>8} {'|diff|':>8}")
    for pnum, etiq, sp, vp, diff in diffs[:15]:
        flag = " ←" if diff > 5 else ""
        print(f"  {pnum:>5} {etiq:<25} {(sp or 0):>10.1f} {(vp or 0):>8.1f} {diff:>8.1f}{flag}")

    # 5. Top-10 contribuyentes por sum(value) en estable + SOSPECHOSO
    print("\n── [V5] Top-10 contribuyentes por métrica en estable (SOSPECHOSO si >20% del total o >80% de releases) ──")

    # Cuenta de releases sin excluir
    cur.execute("SELECT COUNT(DISTINCT periodo_id) FROM periodo WHERE tipo_analisis='versiones' AND etiqueta NOT IN %s",
                (tuple(EXCLUIR_ESTABLE),))
    n_releases = cur.fetchone()[0]

    cur.execute("""
        SELECT r.metrica_id, r.contribuyente_login,
               SUM(r.value) AS suma_v,
               COUNT(DISTINCT r.periodo_id) AS n_releases_activo,
               SUM(SUM(r.value)) OVER (PARTITION BY r.metrica_id) AS total_metrica
        FROM resultado r
        JOIN periodo p ON p.periodo_id=r.periodo_id
        WHERE p.tipo_analisis='versiones'
          AND p.etiqueta NOT IN %s
          AND r.contribuyente_login IS NOT NULL
          AND r.metrica_id = ANY(%s)
        GROUP BY r.metrica_id, r.contribuyente_login
    """, (tuple(EXCLUIR_ESTABLE), list(TODAS_PERSONA)))
    all_contrib = cur.fetchall()

    from collections import defaultdict as dd2
    by_met: dict[str, list] = dd2(list)
    for mid, login, sv, nr, tot in all_contrib:
        by_met[mid].append((login, float(sv or 0), nr, float(tot or 1)))

    for mid in sorted(by_met.keys()):
        top = sorted(by_met[mid], key=lambda x: -x[1])[:10]
        print(f"\n  {mid}  (releases con datos: {n_releases})")
        print(f"    {'login':<35} {'tipo':>10} {'sum_value':>12} {'pct_total%':>11} {'releases':>8} {'pct_rel%':>9}")
        for login, sv, nr, total_v in top:
            tc = bots.get(login,'humano')
            pct_v = sv/total_v*100 if total_v else 0
            pct_r = nr/n_releases*100
            flag = ""
            if tc == 'humano':
                if pct_v > 20 or pct_r > 80:
                    flag = "  ← SOSPECHOSO"
            print(f"    {login:<35} {tc:>10} {sv:>12.1f} {pct_v:>10.1f}% {nr:>8} {pct_r:>8.1f}%{flag}")

# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("=== export_persona.py ===", flush=True)
    bots = load_bots()
    print(f"  {len(bots):,} logins clasificados", flush=True)

    con = psycopg2.connect(**DB)
    cur = con.cursor()

    # ── Archivo 3 (estático) ──────────────────────────────────────────────────
    print("\n[1/3] metricas_persona.csv")
    mp = write_metricas()
    print(f"  {mp.stat().st_size/1024:.1f} KB, {len(METRICAS_META)} filas")

    # ── Lookups primera_fecha ─────────────────────────────────────────────────
    print("\nBuilding primera_fecha lookups (versiones)...", flush=True)
    pf_c_v = primera_fecha_lookup(cur, METRICAS_COMMITS,     'versiones')
    pf_i_v = primera_fecha_lookup(cur, METRICAS_INTERACCION, 'versiones')
    print(f"  commits: {len(pf_c_v):,} logins | interaccion: {len(pf_i_v):,} logins")

    print("Building primera_fecha lookups (versiones_canary)...", flush=True)
    pf_c_c = primera_fecha_lookup(cur, METRICAS_COMMITS,     'versiones_canary')
    pf_i_c = primera_fecha_lookup(cur, METRICAS_INTERACCION, 'versiones_canary')
    print(f"  commits: {len(pf_c_c):,} logins | interaccion: {len(pf_i_c):,} logins")

    # ── Archivo 1 ─────────────────────────────────────────────────────────────
    print("\n[2/3] persona_detalle_estable.csv...", flush=True)
    det_p, det_n, det_mb = write_detalle(cur, bots, pf_c_v, pf_i_v, exclude_cd=False)
    print(f"  {det_n:,} filas, {det_mb:.1f} MB")
    if det_mb > 90:
        print(f"  ⚠ Supera 90 MB → regenerando sin cd")
        det_p, det_n, det_mb = write_detalle(cur, bots, pf_c_v, pf_i_v, exclude_cd=True)
        print(f"  (sin cd) {det_n:,} filas, {det_mb:.1f} MB")

    # ── Archivo 2 ─────────────────────────────────────────────────────────────
    print("\n[3/3] persona_agregado_estable_canary.csv...", flush=True)
    agg_p, agg_n, agg_mb = write_agregado(cur, bots, pf_c_v, pf_i_v, pf_c_c, pf_i_c)
    print(f"  {agg_n:,} filas, {agg_mb:.1f} MB")

    # ── Validaciones ─────────────────────────────────────────────────────────
    cur2 = con.cursor()  # fresh cursor for validations (no RealDictCursor needed)
    validar(cur2, bots)

    con.close()
    print("\n=== Done ===")

if __name__ == '__main__':
    main()
