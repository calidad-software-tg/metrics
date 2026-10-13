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
# Credenciales: variables POSTGRES_* del entorno o del .env (así se puede apuntar a otra
# base, ej. POSTGRES_DB=resultados_metricas_fixes).
_env = ROOT / ".env"
if _env.exists():
    for _l in _env.read_text().splitlines():
        if "=" in _l and not _l.startswith("#"):
            _k, _v = _l.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())
DB = dict(host=os.environ.get("POSTGRES_HOST", "localhost"),
          port=int(os.environ.get("POSTGRES_PORT", 5432)),
          dbname=os.environ.get("POSTGRES_DB", "resultados_metricas"),
          user=os.environ.get("POSTGRES_USER", "metricas"),
          password=os.environ.get("POSTGRES_PASSWORD", "metricas"))

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

# ── Tabla de alias nombre_git -> login (ver db/mapear_identidades.py) ────────
#
# Las métricas del runner local (run_versiones_local.py) atribuyen por el nombre
# de git del autor (%an, sin mailmap), mientras que las de la API atribuyen por
# `author.user.login`. Para unir la misma persona entre las dos fuentes, canon()
# se aplica SOLO a las métricas del runner local — si se aplicara a las de API
# (todas logins) correría el riesgo de fusionar logins reales con nombres de git
# coincidentes de otras personas.
#
# Lista exacta tomada de run_versiones_local.py (ARCHIVOS ∪ COMMITS ∪ BLAME):
METRICAS_RUNNER_LOCAL = frozenset({
    # ARCHIVOS
    "loc_notion", "dloc", "cd", "rc",
    # COMMITS
    "cdiv", "fexp", "le", "rexp", "anmcc", "dloc_flujo", "commits_doc",
    # BLAME
    "developer_ownership_notion",
})

_ALIAS: dict[str, str] = {}        # nombre_git -> login_github
_ALIAS_N_COMMITS: dict[str, int] = {}
_ALIAS_ACTIVO = True

def load_alias(path: Path = None) -> None:
    """Carga db/identidades_git.csv en _ALIAS. Llamar una vez al inicio."""
    global _ALIAS, _ALIAS_N_COMMITS
    path = path or (ROOT / "db" / "identidades_git.csv")
    if not path.exists():
        print(f"  ⚠ No encuentro {path}, canon() no traducirá nada", flush=True)
        return
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            nombre = r["nombre_git"]
            _ALIAS[nombre] = r["login"]
            try:
                _ALIAS_N_COMMITS[nombre] = int(r.get("n_commits") or 0)
            except (TypeError, ValueError):
                _ALIAS_N_COMMITS[nombre] = 0
    print(f"  {len(_ALIAS):,} aliases nombre_git -> login cargados", flush=True)

def _parece_login(s: str) -> bool:
    """True si `s` cumple el formato de login de GitHub (sin espacios, chars válidos)."""
    if not s or ' ' in s:
        return False
    return bool(_LOGIN_RE.match(s))

def canon(identidad: str | None, metrica: str) -> str | None:
    """Login canonizado si corresponde para esa métrica, o la identidad original.

    Reglas:
    - `metrica` en METRICAS_RUNNER_LOCAL (anmcc, cdiv, fexp, le, rexp, cd, dloc,
      rc, loc_notion, commits_doc, dloc_flujo, developer_ownership_notion): el
      campo guarda nombre_git → traducir con la tabla si hay entrada.
    - `metrica` == 'dev_exp': traduce solo si la identidad NO parece un login válido
      (dev_exp ya aplica `_resolver_identidades` en el fetch y guarda logins; los
      pocos nombres de git que caen son commits sin cuenta vinculada).
    - Resto (nc, exprev, rexprev, disc_centrality, sc, sc_disc, nci, mttr y
      variantes, dis, ss): sin traducción. Son métricas de API, guardan login.
    """
    if identidad is None or not _ALIAS_ACTIVO:
        return identidad
    if metrica in METRICAS_RUNNER_LOCAL:
        return _ALIAS.get(identidad, identidad)
    if metrica == "dev_exp":
        if _parece_login(identidad):
            return identidad
        return _ALIAS.get(identidad, identidad)
    return identidad

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
    """identidad canonizada -> primera fecha_fin (AAAAMMDDhhmmss) en esas métricas.

    Para pf_commits (METRICAS_COMMITS = anmcc/cdiv/fexp/rexp/le, todas locales),
    canon() traduce nombres git a logins. Para pf_interac (METRICAS_INTERACCION,
    todas API), canon() es identidad: los valores quedan iguales al comportamiento
    anterior.
    """
    cur.execute("""
        SELECT r.contribuyente_login, r.metrica_id, p.fecha_fin
        FROM resultado r
        JOIN periodo p ON p.periodo_id = r.periodo_id
        WHERE r.metrica_id = ANY(%s)
          AND p.tipo_analisis = %s
          AND r.contribuyente_login IS NOT NULL
    """, (list(metricas), tipo))
    por_persona: dict[str, object] = {}
    for lg, mid, pf in cur.fetchall():
        c = canon(lg, mid)
        prev = por_persona.get(c)
        if prev is None or pf < prev:
            por_persona[c] = pf
    return {c: fmt_ts(pf) for c, pf in por_persona.items()}

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
    """Escribe persona_detalle_estable.csv con canon() aplicado a contribuyente_login.
    El filtro de dev_exp con anmcc se hace en Python sobre identidades canonizadas,
    no por EXISTS SQL (que compara login exacto)."""
    p = ROOT / "persona_detalle_estable.csv"
    metricas_a_exportar = (TODAS_PERSONA - METRICAS_ACUM)
    if exclude_cd:
        metricas_a_exportar = metricas_a_exportar - {"cd"}

    # anmcc por periodo canonizado — set de identidades canónicas con anmcc
    cur.execute("""
        SELECT p.periodo_id, r.contribuyente_login
        FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
        WHERE r.metrica_id='anmcc' AND p.tipo_analisis='versiones'
          AND r.contribuyente_login IS NOT NULL
    """)
    anmcc_set: dict[int, set] = defaultdict(set)
    for pid, lg in cur.fetchall():
        anmcc_set[pid].add(canon(lg, 'anmcc'))

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
                mid = r[5]
                lg = canon(r[6], mid); v = r[7]
                w.writerow([
                    r[1], r[2], fmt_ts(r[4]), r[4].year, fmt_dur(r[3], r[4]),
                    mid, lg, bots.get(lg,'humano'), identidad(lg),
                    fmt_v(v),
                    pf_commits.get(lg,''), pf_interac.get(lg,''),
                ])
                n += 1

        # dev_exp: filtro por anmcc del mismo periodo, usando identidades canonizadas
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
            ORDER BY p.periodo_num
        """, (excl_tuple,))
        while True:
            rows = cur.fetchmany(5000)
            if not rows: break
            for r in rows:
                pid = r[0]; lg = canon(r[5], 'dev_exp'); v = r[6]
                if lg not in anmcc_set.get(pid, ()):   # filtro reemplaza al EXISTS
                    continue
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


# ── Reglas de dedup por métrica cuando dos identidades crudas colapsan al mismo canon.
#   suma: dloc, rexp (métricas aditivas por autor; ver 16/dloc.py:92, 15/rexp.py:17-20).
#   max:  dev_exp     (primer commit más antiguo entre las dos identidades, 38/dev_experience.py).
#   gan:  resto       (anmcc, cdiv, le, fexp, cd, ss y cualquier otra): sin recalcular desde
#                      los commits no se puede combinar; se queda con la identidad de más
#                      n_commits en el clon (como antes). CD podría ser promedio ponderado
#                      por líneas, pero value_extra no guarda cloc/lloc (verificado en DB).
DEDUPE_REGLA = {
    "dloc":    "suma",
    "rexp":    "suma",
    "dev_exp": "max",
}

def _agrupar_con_dedupe(crudo, dedupe_log, serie, metrica):
    """De [(pid, identidad_cruda, value)], devuelve {pid: {canon: value}} aplicando la
    regla de DEDUPE_REGLA (default: quedarse con la identidad de más n_commits en el clon).
    Registra en dedupe_log (serie, metrica, pid, canon, descartada, val_desc, ganadora,
    val_gan, regla, val_final).

    canon() se aplica según `metrica`: solo traduce para las métricas del runner local
    y, en dev_exp, solo para identidades que no son logins. En las métricas de API es
    identidad y, por tanto, no hay colisiones."""
    regla = DEDUPE_REGLA.get(metrica, "gan")

    # Primera pasada: juntar por (pid, canon) todas las (val, identidad, prio).
    por_canon: dict[int, dict[str, list[tuple[float, str, int]]]] = defaultdict(lambda: defaultdict(list))
    for pid, lg, val in crudo:
        if val is None: continue
        v = float(val)
        c = canon(lg, metrica)
        prio = _ALIAS_N_COMMITS.get(lg, 0)
        por_canon[pid][c].append((v, lg, prio))

    salida: dict[int, dict[str, float]] = {}
    for pid, canons in por_canon.items():
        salida[pid] = {}
        for c, items in canons.items():
            if len(items) == 1:
                salida[pid][c] = items[0][0]
                continue
            # Hay colisión: aplicar regla.
            items_ord = sorted(items, key=lambda x: -x[2])  # mayor prio primero
            ganadora = items_ord[0]
            if regla == "suma":
                val_final = sum(x[0] for x in items)
            elif regla == "max":
                val_final = max(x[0] for x in items)
            else:  # "gan": max n_commits
                val_final = ganadora[0]
            salida[pid][c] = val_final
            # Registrar las descartadas (todas menos la ganadora) con la regla aplicada.
            for desc in items_ord[1:]:
                dedupe_log.append((serie, metrica, pid, c,
                                   desc[1], desc[0],
                                   ganadora[1], ganadora[0],
                                   regla, val_final))
    return salida


def write_agregado(cur, bots, pf_commits_v, pf_interac_v, pf_commits_c, pf_interac_c, dedupe_log):
    p = ROOT / "persona_agregado_estable_canary.csv"
    excl = tuple(EXCLUIR_ESTABLE)
    cols = ["serie","periodo_num","version","fecha_hora","anio","duracion_dias",
            "metrica_id","alcance","n_contribuyentes","suma","media","mediana",
            "p90","maximo","share_top1","share_top10pct"]

    rows_out: list[dict] = []

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

        cur.execute("""
            SELECT periodo_id, periodo_num, etiqueta, fecha_inicio, fecha_fin
            FROM periodo WHERE tipo_analisis=%s ORDER BY periodo_num
        """, (serie,))
        periods = {r[0]: r for r in cur.fetchall()}

        pf_commits = pf_commits_v if serie == 'versiones' else pf_commits_c
        pf_interac = pf_interac_v if serie == 'versiones' else pf_interac_c

        # anmcc canonizado por periodo — se usa para filtrar dev_exp
        anmcc_params = [serie, 'anmcc'] + ([excl_sql] if excl_sql else [])
        excl_clause = "AND p.etiqueta NOT IN %s" if excl_sql else ""
        cur.execute(f"""
            SELECT r.periodo_id, r.contribuyente_login
            FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
            WHERE p.tipo_analisis=%s AND r.metrica_id=%s
              AND r.contribuyente_login IS NOT NULL {excl_clause}
        """, anmcc_params)
        anmcc_canon_set: dict[int, set] = defaultdict(set)
        for pid, lg in cur.fetchall():
            anmcc_canon_set[pid].add(canon(lg, 'anmcc'))

        # ── Métricas regulares ─────────────────────────────────────────────────
        for metrica in sorted(TODAS_PERSONA):
            params = [serie, metrica] + ([excl_sql] if excl_sql else [])
            cur.execute(f"""
                SELECT r.periodo_id, r.contribuyente_login, r.value
                FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
                WHERE p.tipo_analisis=%s AND r.metrica_id=%s
                  AND r.contribuyente_login IS NOT NULL
                  {excl_clause}
            """, params)
            crudo = cur.fetchall()

            # Para dev_exp, filtrar por intersección canónica con anmcc.
            if metrica == 'dev_exp':
                crudo = [(pid, lg, v) for (pid, lg, v) in crudo
                         if canon(lg, 'dev_exp') in anmcc_canon_set.get(pid, ())]

            por_canon = _agrupar_con_dedupe(crudo, dedupe_log, serie, metrica)

            for pid, canon_val in por_canon.items():
                if pid not in periods: continue
                _, pnum, etiq, fini, ffin = periods[pid]
                todas = list(canon_val.values())
                humanos = [v for c, v in canon_val.items() if bots.get(c, 'humano') == 'humano']
                for alcance, vals in [('todas', todas), ('humanos', humanos)]:
                    rows_out.append(make_row(serie, pnum, etiq, fini, ffin, metrica, alcance, agg_stats(vals)))

        # ── Pseudo-métricas: activos y nuevos ──────────────────────────────────
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

            by_period_canons: dict[int, set] = defaultdict(set)
            for pid, lg in cur.fetchall():
                by_period_canons[pid].add(canon(lg, base_metrica))

            for pid, logins_set in by_period_canons.items():
                if pid not in periods: continue
                _, pnum, etiq, fini, ffin = periods[pid]
                ts_fin = fmt_ts(ffin)

                humanos = {l for l in logins_set if bots.get(l,'humano') == 'humano'}
                nuevos_todas = {l for l in logins_set if pf_key.get(l,'') == ts_fin}
                nuevos_hum   = {l for l in humanos    if pf_key.get(l,'') == ts_fin}

                for alcance, cnt_act, cnt_new in [
                    ('todas', len(logins_set), len(nuevos_todas)),
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

        # activos_cierre (nci) y activos_comentarios (nc) — ambas API, canon() es identidad.
        for base_m, pseudo_m in [('nci','activos_cierre'), ('nc','activos_comentarios')]:
            params = [serie, base_m] + ([excl_sql] if excl_sql else [])
            cur.execute(f"""
                SELECT r.periodo_id, r.contribuyente_login
                FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
                WHERE p.tipo_analisis=%s AND r.metrica_id=%s
                  AND r.contribuyente_login IS NOT NULL {excl_clause}
            """, params)
            by_period_canons: dict[int, set] = defaultdict(set)
            for pid, lg in cur.fetchall():
                by_period_canons[pid].add(canon(lg, base_m))
            for pid, logins_set in by_period_canons.items():
                if pid not in periods: continue
                _, pnum, etiq, fini, ffin = periods[pid]
                humanos = {l for l in logins_set if bots.get(l,'humano') == 'humano'}
                for alcance, cnt in [('todas', len(logins_set)), ('humanos', len(humanos))]:
                    rows_out.append(make_row(
                        serie, pnum, etiq, fini, ffin, pseudo_m, alcance,
                        {k:'' for k in ('suma','media','mediana','p90','maximo','share_top1','share_top10pct')},
                        extra_n=cnt
                    ))

        # cuentas_por_tipo: identidades únicas en anmcc ∪ exprev. Hacemos DOS consultas
        # separadas y aplicamos canon() a cada una según su métrica (anmcc = runner local,
        # se canoniza; exprev = API, no). Después se unen y se cuentan por tipo.
        por_pid_canon_tipo: dict[tuple, str] = {}

        # anmcc → canon(lg, 'anmcc') traduce nombre git a login
        params_anmcc = [serie, 'anmcc'] + ([excl_sql] if excl_sql else [])
        cur.execute(f"""
            SELECT DISTINCT p.periodo_id, r.contribuyente_login
            FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
            WHERE p.tipo_analisis=%s AND r.metrica_id=%s
              AND r.contribuyente_login IS NOT NULL {excl_clause}
        """, params_anmcc)
        for pid, lg in cur.fetchall():
            c = canon(lg, 'anmcc')
            tc = bots.get(c, 'humano')
            prev = por_pid_canon_tipo.get((pid, c))
            if prev is None or (tc in NON_HUMAN and prev == 'humano'):
                por_pid_canon_tipo[(pid, c)] = tc

        # exprev → canon(lg, 'exprev') es identidad, los logins quedan como vienen
        params_exprev = [serie, 'exprev'] + ([excl_sql] if excl_sql else [])
        cur.execute(f"""
            SELECT DISTINCT p.periodo_id, r.contribuyente_login
            FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
            WHERE p.tipo_analisis=%s AND r.metrica_id=%s
              AND r.contribuyente_login IS NOT NULL {excl_clause}
        """, params_exprev)
        for pid, lg in cur.fetchall():
            c = canon(lg, 'exprev')
            tc = bots.get(c, 'humano')
            prev = por_pid_canon_tipo.get((pid, c))
            if prev is None or (tc in NON_HUMAN and prev == 'humano'):
                por_pid_canon_tipo[(pid, c)] = tc

        by_period_tipo: dict[int, dict] = defaultdict(lambda: defaultdict(int))
        for (pid, _c), tc in por_pid_canon_tipo.items():
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
              abs((r[2] or 0) - (r[3] or 0))) for r in nci_rows if r[3] is not None]  # la fila tiene 4 columnas: r[4] daba IndexError
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
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sin-alias", action="store_true",
                    help="No traducir nombres git a logins (comportamiento anterior).")
    args = ap.parse_args()

    print("=== export_persona.py ===", flush=True)
    global _ALIAS_ACTIVO
    if args.sin_alias:
        _ALIAS_ACTIVO = False
        print("  --sin-alias: canon() desactivado (comportamiento antiguo)", flush=True)
    else:
        load_alias()

    bots = load_bots()
    print(f"  {len(bots):,} logins clasificados", flush=True)

    con = psycopg2.connect(**DB)
    cur = con.cursor()

    # ── Archivo 3 (estático) ──────────────────────────────────────────────────
    print("\n[1/3] metricas_persona.csv")
    mp = write_metricas()
    print(f"  {mp.stat().st_size/1024:.1f} KB, {len(METRICAS_META)} filas")

    # ── Lookups primera_fecha (ya canonizados) ────────────────────────────────
    print("\nBuilding primera_fecha lookups (versiones)...", flush=True)
    pf_c_v = primera_fecha_lookup(cur, METRICAS_COMMITS,     'versiones')
    pf_i_v = primera_fecha_lookup(cur, METRICAS_INTERACCION, 'versiones')
    print(f"  commits: {len(pf_c_v):,} identidades | interaccion: {len(pf_i_v):,}")

    print("Building primera_fecha lookups (versiones_canary)...", flush=True)
    pf_c_c = primera_fecha_lookup(cur, METRICAS_COMMITS,     'versiones_canary')
    pf_i_c = primera_fecha_lookup(cur, METRICAS_INTERACCION, 'versiones_canary')
    print(f"  commits: {len(pf_c_c):,} identidades | interaccion: {len(pf_i_c):,}")

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
    dedupe_log: list = []  # (serie, metrica, pid, canon, ident_descartada, val_desc, ident_ganadora, val_gan)
    agg_p, agg_n, agg_mb = write_agregado(cur, bots, pf_c_v, pf_i_v, pf_c_c, pf_i_c, dedupe_log)
    print(f"  {agg_n:,} filas, {agg_mb:.1f} MB")

    # Volcar casos de dedupe (dos identidades crudas → mismo canónico en la misma métrica/ventana)
    if dedupe_log:
        dp = ROOT / "persona_duplicados_canon.csv"
        with open(dp, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(["serie","metrica","periodo_id","canon",
                        "descartada","value_descartada",
                        "ganadora","value_ganadora",
                        "regla","value_final"])
            w.writerows(dedupe_log)
        print(f"  Dedupe: {len(dedupe_log)} colisiones (misma persona canonizada bajo dos identidades crudas) en {dp.name}", flush=True)
    else:
        print(f"  Dedupe: 0 colisiones")

    # ── Validaciones ─────────────────────────────────────────────────────────
    cur2 = con.cursor()
    validar(cur2, bots)

    con.close()
    print("\n=== Done ===")

if __name__ == '__main__':
    main()
