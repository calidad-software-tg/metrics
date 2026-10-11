#!/usr/bin/env python3
"""
Corrección 3: Unificación de identidades git-name → GitHub login.

Fases
─────
1. Fetch GraphQL de vercel/next.js (todos los commits con author info).
   Cache en disco: /tmp/nextjs_commit_aliases.json
2. Genera alias_identidades.csv
3. Agrega columna "persona" al final de persona_detalle_estable.csv
   y recalcula tipo_cuenta según "persona".
4. Validación:
   - Cuántos nombres se resolvieron (n y % del value por métrica)
   - Top-20 duplicados usando "persona" (debería casi vaciarse)
   - Top unresolved con más value
5. Recalcula persona_agregado_estable_canary.csv en las columnas
   que dependen de identidad, usando la tabla de alias.
"""

import csv, json, re, sys, time
from collections import defaultdict
from math import ceil
from pathlib import Path

import psycopg2
import requests

# ── Constantes ──────────────────────────────────────────────────────────────

ROOT  = Path(__file__).resolve().parent
CACHE = Path("/tmp/nextjs_commit_aliases.json")
TOKEN = open(ROOT / ".env").read()
TOKEN = next(l.split("=",1)[1].strip() for l in TOKEN.splitlines() if l.startswith("GITHUB_TOKEN="))
HDR   = {"Authorization": f"Bearer {TOKEN}",
         "Accept": "application/vnd.github+json",
         "X-GitHub-Api-Version": "2022-11-28"}

DB = dict(host="localhost", port=5432, dbname="resultados_metricas",
          user="metricas", password="metricas")

EXCLUIR_ESTABLE = tuple(["4.4.0-canary.2","4.4.0-canary.1","v12.2.3-canary.5","v15.0.0-rc.1"])

COMMIT_METRICS  = ["anmcc","cdiv","fexp","le","rexp"]
TODAS_PERSONA   = ["anmcc","cdiv","fexp","le","rexp",
                   "nc","exprev","rexprev","disc_centrality","sc","nci","mttr","dis",
                   "cd","dloc","rc","dev_exp","ss"]

_LOGIN_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$')

def identidad(login):
    if ' ' in login: return 'nombre'
    if not _LOGIN_RE.match(login): return 'nombre'
    return 'login'

def fmt_v(v):
    if v is None: return ''
    try:
        from math import isnan
        f = float(v)
        if isnan(f): return ''
    except: return ''
    s = f"{f:.4f}".rstrip('0')
    if s.endswith('.'): s += '0'
    return s

def agg_stats(vals):
    if not vals:
        return {k: '' for k in ('n','suma','media','mediana','p90','maximo','share_top1','share_top10pct')}
    s = sorted(vals)
    n = len(s)
    total = sum(s)
    mid = (s[n//2-1]+s[n//2])/2 if n%2==0 else s[n//2]
    p90 = s[min(ceil(0.9*n)-1, n-1)]
    st1  = fmt_v(s[-1]/total) if total else ''
    n10  = max(1, ceil(0.1*n))
    st10 = fmt_v(sum(s[-n10:])/total) if total else ''
    return dict(n=n, suma=fmt_v(total), media=fmt_v(total/n),
                mediana=fmt_v(mid), p90=fmt_v(p90), maximo=fmt_v(s[-1]),
                share_top1=st1, share_top10pct=st10)

def load_bots():
    out = {}
    with open(ROOT / 'bots_clasificados.csv', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            out[r['login']] = r['tipo_cuenta']
    return out

# ── FASE 1: Fetch GraphQL ────────────────────────────────────────────────────

_GQL_HISTORY = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $cursor) {
            pageInfo { hasNextPage endCursor }
            nodes {
              oid
              author {
                user { login name }
                name
              }
            }
          }
        }
      }
    }
  }
}
"""

def _graphql(query, variables, retries=3):
    for attempt in range(retries):
        try:
            r = requests.post(
                "https://api.github.com/graphql",
                headers={**HDR, "Content-Type": "application/json"},
                json={"query": query, "variables": variables},
                timeout=60,
            )
            if r.status_code == 429 or (r.status_code == 403 and "rate limit" in r.text.lower()):
                reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait = max(5, reset - int(time.time()) + 2)
                print(f"\n  rate-limit, espero {wait}s...", flush=True)
                time.sleep(wait)
                continue
            r.raise_for_status()
            data = r.json()
            if "errors" in data:
                print(f"\n  GQL errors: {data['errors']}", flush=True)
                if attempt < retries - 1:
                    time.sleep(5)
                    continue
            return data
        except requests.exceptions.Timeout:
            if attempt < retries - 1:
                time.sleep(10)
                continue
            raise
    raise RuntimeError("GraphQL request failed after retries")

def fetch_commit_aliases() -> dict:
    """
    Returns {git_name: {login, sha, profile_name}}.
    Uses /tmp/nextjs_commit_aliases.json as cache.
    """
    if CACHE.exists():
        print(f"  Cargando cache desde {CACHE}")
        with open(CACHE) as f:
            return json.load(f)

    print("  Fetching commit history de vercel/next.js via GraphQL...")
    # Maps built during fetch:
    # git_name_exact → {login, sha}        (commits with linked account)
    # profile_name_lower → {login, sha}    (for secondary matching)
    git_exact: dict = {}   # git_name → {login, sha}
    profile_map: dict = {} # profile_name.lower() → {login, sha}

    cursor = None
    page = 0
    total = 0
    while True:
        data = _graphql(_GQL_HISTORY, {"owner": "vercel", "repo": "next.js", "cursor": cursor})
        history = data["data"]["repository"]["defaultBranchRef"]["target"]["history"]
        nodes = history["nodes"]
        page_info = history["pageInfo"]

        for node in nodes:
            oid = node["oid"]
            author = node.get("author") or {}
            git_name = (author.get("name") or "").strip()
            user = author.get("user") or {}
            login = user.get("login")
            profile_name = (user.get("name") or "").strip()

            if git_name and login:
                if git_name not in git_exact:
                    git_exact[git_name] = {"login": login, "sha": oid,
                                           "profile_name": profile_name}
                if profile_name and profile_name.lower() not in profile_map:
                    profile_map[profile_name.lower()] = {"login": login, "sha": oid}

        total += len(nodes)
        page += 1
        print(f"  ...página {page}, {total:,} commits procesados", end="\r", flush=True)

        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]
        time.sleep(0.15)  # cortesía

    print(f"\n  Commits procesados: {total:,}")
    print(f"  git_names con login: {len(git_exact):,}")
    print(f"  profile_names mapeados: {len(profile_map):,}")

    result = {}
    # Build: git_name → {login, sha}
    for git_name, rec in git_exact.items():
        result[git_name] = rec

    # Save cache including profile_map for secondary lookup
    cache_data = {"git_exact": git_exact, "profile_map": profile_map}
    with open(CACHE, "w") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)
    print(f"  Cache guardado en {CACHE}")
    return cache_data


def build_alias_lookup(cache_data):
    """Returns lookup(nombre_git) → (login, sha, metodo) or None."""
    if "git_exact" in cache_data:
        git_exact = cache_data["git_exact"]
        profile_map = cache_data["profile_map"]
    else:
        # Old format: flat dict git_name → rec
        git_exact = cache_data
        profile_map = {}

    # Build case-insensitive fallback
    git_lower = {k.lower(): v for k, v in git_exact.items()}

    def lookup(nombre):
        # 1. Exact match
        if nombre in git_exact:
            r = git_exact[nombre]
            return (r["login"], r["sha"], "resolver_dev_exp")
        # 2. Case-insensitive git_name
        k = nombre.lower()
        if k in git_lower:
            r = git_lower[k]
            return (r["login"], r["sha"], "resolver_dev_exp")
        # 3. profile_name match (Tim Neutkens → timneutkens)
        if k in profile_map:
            r = profile_map[k]
            return (r["login"], r["sha"], "resolver_dev_exp")
        return None

    return lookup


# ── FASE 2: alias_identidades.csv ────────────────────────────────────────────

def build_alias_csv(lookup):
    print("\n── FASE 2: alias_identidades.csv ──")
    con = psycopg2.connect(**DB)
    cur = con.cursor()

    # All unique nombres (identidad="nombre") in commit metrics across both series
    cur.execute("""
        SELECT DISTINCT r.contribuyente_login
        FROM resultado r
        WHERE r.metrica_id = ANY(%s)
          AND r.contribuyente_login IS NOT NULL
    """, (COMMIT_METRICS,))
    all_contribuyentes = [row[0] for row in cur.fetchall()]
    nombres = [l for l in all_contribuyentes if identidad(l) == 'nombre']
    con.close()
    print(f"  Nombres únicos a resolver: {len(nombres):,}")

    alias_path = ROOT / "alias_identidades.csv"
    rows = []
    resolved = 0
    for nombre in nombres:
        result = lookup(nombre)
        if result:
            login, sha, metodo = result
            rows.append({"nombre_git": nombre, "login": login,
                         "metodo": metodo, "sha_usado": sha})
            resolved += 1
        else:
            rows.append({"nombre_git": nombre, "login": "",
                         "metodo": "sin_resolver", "sha_usado": ""})

    with open(alias_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["nombre_git","login","metodo","sha_usado"])
        w.writeheader()
        w.writerows(rows)

    print(f"  Resueltos: {resolved:,} / {len(nombres):,}  ({resolved/len(nombres)*100:.1f}%)")
    print(f"  Sin resolver: {len(nombres)-resolved:,}")
    print(f"  Guardado: {alias_path}")

    # Build the alias dict for use in subsequent phases
    alias = {}
    for r in rows:
        if r["login"]:
            alias[r["nombre_git"]] = r["login"]
    return alias


# ── FASE 3: Agregar columna "persona" a persona_detalle_estable.csv ──────────

def update_detalle(alias, bots):
    print("\n── FASE 3: persona_detalle_estable.csv — agregar columna 'persona' ──")
    detalle_path = ROOT / "persona_detalle_estable.csv"
    tmp_path     = ROOT / "persona_detalle_estable.csv.tmp"

    # Read header
    with open(detalle_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames_orig = reader.fieldnames

    if "persona" in fieldnames_orig:
        print("  Columna 'persona' ya existe. Recalculando...")
        new_fields = fieldnames_orig
    else:
        new_fields = fieldnames_orig + ["persona"]

    n_rows = 0
    n_resolved = 0
    n_tipo_changed = 0

    with open(detalle_path, newline="", encoding="utf-8") as fin, \
         open(tmp_path, "w", newline="", encoding="utf-8") as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=new_fields)
        writer.writeheader()

        for row in reader:
            login = row["contribuyente_login"]
            # "persona": resolved login if available, else original
            persona = alias.get(login, login)
            row["persona"] = persona

            # Recalculate tipo_cuenta based on "persona"
            if persona != login:
                # Resolved to a login; look it up in bots
                new_tc = bots.get(persona, "humano")
                if new_tc != row["tipo_cuenta"]:
                    n_tipo_changed += 1
                row["tipo_cuenta"] = new_tc
                n_resolved += 1

            writer.writerow(row)
            n_rows += 1
            if n_rows % 50_000 == 0:
                print(f"  ...{n_rows:,} filas", end="\r", flush=True)

    tmp_path.replace(detalle_path)
    mb = detalle_path.stat().st_size / 1024**2
    print(f"  {n_rows:,} filas procesadas, {mb:.1f} MB")
    print(f"  Filas con identidad resuelta: {n_resolved:,}")
    print(f"  Cambios en tipo_cuenta: {n_tipo_changed:,}")


# ── FASE 4: Validación ────────────────────────────────────────────────────────

def validate(alias, bots):
    print("\n── FASE 4: Validación ──")

    con = psycopg2.connect(**DB)
    cur = con.cursor()

    # 4a. Cuántos nombres resueltos y % de value por métrica (estable, commit metrics)
    print("\n  [4a] Resolución por métrica (estable):")
    cur.execute("""
        SELECT r.metrica_id, r.contribuyente_login, SUM(r.value) AS tv
        FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
        WHERE p.tipo_analisis='versiones'
          AND p.etiqueta NOT IN %s
          AND r.metrica_id = ANY(%s)
          AND r.contribuyente_login IS NOT NULL
        GROUP BY r.metrica_id, r.contribuyente_login
    """, (EXCLUIR_ESTABLE, COMMIT_METRICS))

    by_met = defaultdict(lambda: {"total_v": 0, "nombre_v": 0,
                                   "resuelto_v": 0, "nombre_n": 0, "resuelto_n": 0})
    for mid, login, tv in cur.fetchall():
        tv = float(tv or 0)
        by_met[mid]["total_v"] += tv
        if identidad(login) == 'nombre':
            by_met[mid]["nombre_v"] += tv
            by_met[mid]["nombre_n"] += 1
            if login in alias:
                by_met[mid]["resuelto_v"] += tv
                by_met[mid]["resuelto_n"] += 1

    print(f"    {'metrica':<10} {'nom_n':>7} {'res_n':>7} {'%res_n':>8}  {'nom_v%':>9} {'res_v%':>9}")
    print("    " + "─"*60)
    for mid in sorted(by_met.keys()):
        d = by_met[mid]
        pct_n = d["resuelto_n"]/d["nombre_n"]*100 if d["nombre_n"] else 0
        pct_v = d["resuelto_v"]/d["nombre_v"]*100 if d["nombre_v"] else 0
        v_pct_total = d["nombre_v"]/d["total_v"]*100 if d["total_v"] else 0
        print(f"    {mid:<10} {d['nombre_n']:>7,} {d['resuelto_n']:>7,} {pct_n:>7.1f}%  "
              f"{v_pct_total:>7.1f}% of total  {pct_v:>7.1f}% resolved")

    # 4b. Top-20 duplicados usando "persona" (from the updated detalle file)
    print("\n  [4b] Top-20 duplicados usando 'persona' (persona_detalle_estable.csv):")
    detalle_path = ROOT / "persona_detalle_estable.csv"
    persona_totals = defaultdict(float)
    persona_filas  = defaultdict(int)
    persona_mets   = defaultdict(set)

    commit_set = set(COMMIT_METRICS)
    with open(detalle_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        has_persona = "persona" in (reader.fieldnames or [])
        for row in reader:
            mid  = row["metrica_id"]
            key  = row["persona"] if has_persona else row["contribuyente_login"]
            val  = float(row["value"]) if row["value"] else 0.0
            persona_totals[key] += val
            persona_filas[key]  += 1
            persona_mets[key].add(mid)

    by_norm = defaultdict(list)
    for login in persona_totals:
        nk = re.sub(r'[\s\-_]','', login.lower())
        by_norm[nk].append(login)

    candidates = []
    for key, members in by_norm.items():
        if len(members) < 2: continue
        has_lg  = any(identidad(m) == 'login'  for m in members)
        has_nm  = any(identidad(m) == 'nombre' for m in members)
        if has_lg and has_nm:
            total_v = sum(persona_totals[m] for m in members)
            candidates.append((key, members, total_v))
    candidates.sort(key=lambda x: -x[2])

    if candidates:
        print(f"    {'#':>3}  {'identidad':<12} {'persona':<40} {'value':>12}  métricas")
        print("    " + "─"*90)
        for rank, (key, members, total_v) in enumerate(candidates[:20], 1):
            for i, m in enumerate(sorted(members, key=lambda x: -persona_totals[x])):
                tv = persona_totals[m]
                mets = ','.join(sorted(persona_mets[m]))
                idf = identidad(m)
                if i == 0:
                    print(f"    {rank:>3}  {idf:<12} {m:<40} {tv:>12,.1f}  {mets}")
                else:
                    pct = tv/total_v*100 if total_v else 0
                    print(f"         {idf:<12} {m:<40} {tv:>12,.1f}  {mets}  ({pct:.1f}%)")
            print(f"         {'':12} {'TOTAL PAR':<40} {total_v:>12,.1f}")
            print()
    else:
        print("    (Sin duplicados restantes — unificación completa)")

    # 4c. Top unresolved por value (commit metrics, estable)
    print("\n  [4c] Top-20 sin resolver por value (commit metrics, estable):")
    cur.execute("""
        SELECT r.contribuyente_login, SUM(r.value) AS tv, COUNT(*) AS nf
        FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
        WHERE p.tipo_analisis='versiones'
          AND p.etiqueta NOT IN %s
          AND r.metrica_id = ANY(%s)
          AND r.contribuyente_login IS NOT NULL
        GROUP BY r.contribuyente_login
        ORDER BY tv DESC
    """, (EXCLUIR_ESTABLE, COMMIT_METRICS))
    unresolved = [(l, float(tv), nf) for l, tv, nf in cur.fetchall()
                  if identidad(l) == 'nombre' and l not in alias]
    print(f"    Total sin resolver: {len(unresolved):,}")
    print(f"    {'nombre_git':<45} {'value':>12} {'filas':>6}")
    print("    " + "─"*66)
    for l, tv, nf in unresolved[:20]:
        print(f"    {l:<45} {tv:>12,.1f} {nf:>6,}")

    con.close()


# ── FASE 5: Recalcular persona_agregado_estable_canary.csv ───────────────────

def recalc_agregado(alias, bots):
    print("\n── FASE 5: Recalculando persona_agregado_estable_canary.csv ──")
    agg_path = ROOT / "persona_agregado_estable_canary.csv"
    tmp_path  = ROOT / "persona_agregado_estable_canary.csv.tmp"

    con = psycopg2.connect(**DB)
    cur = con.cursor()

    # Build primera_fecha lookups with alias applied
    def primera_fecha_lookup_alias(metricas, tipo):
        cur.execute("""
            SELECT r.contribuyente_login, MIN(p.fecha_fin) AS pf
            FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
            WHERE r.metrica_id = ANY(%s)
              AND p.tipo_analisis = %s
              AND r.contribuyente_login IS NOT NULL
            GROUP BY r.contribuyente_login
        """, (list(metricas), tipo))
        raw = {}
        for login, pf in cur.fetchall():
            persona = alias.get(login, login)
            ts = pf.strftime('%Y%m%d%H%M%S') if pf else ''
            if persona not in raw or ts < raw[persona]:
                raw[persona] = ts
        return raw

    METRICAS_COMMITS_SET = frozenset(COMMIT_METRICS)
    METRICAS_INTERAC_SET = frozenset(["nc","exprev","rexprev","disc_centrality","sc","nci","mttr","dis"])

    print("  Building primera_fecha lookups con alias...")
    pf_c_v = primera_fecha_lookup_alias(METRICAS_COMMITS_SET, 'versiones')
    pf_i_v = primera_fecha_lookup_alias(METRICAS_INTERAC_SET, 'versiones')
    pf_c_c = primera_fecha_lookup_alias(METRICAS_COMMITS_SET, 'versiones_canary')
    pf_i_c = primera_fecha_lookup_alias(METRICAS_INTERAC_SET, 'versiones_canary')
    print(f"  pf_commits versiones: {len(pf_c_v):,} | pf_interac: {len(pf_i_v):,}")
    print(f"  pf_commits canary:   {len(pf_c_c):,} | pf_interac: {len(pf_i_c):,}")

    def fmt_ts(dt):
        return dt.strftime('%Y%m%d%H%M%S') if dt else ''

    def fmt_dur(ini, fin):
        if ini is None or fin is None: return ''
        return f"{(fin - ini).total_seconds() / 86400:.2f}"

    # Build period metadata for both series
    period_meta = {}
    for serie in ('versiones', 'versiones_canary'):
        cur.execute("""
            SELECT periodo_id, periodo_num, etiqueta, fecha_inicio, fecha_fin
            FROM periodo WHERE tipo_analisis=%s ORDER BY periodo_num
        """, (serie,))
        for row in cur.fetchall():
            period_meta[(serie, row[0])] = row  # (pid, pnum, etiq, ini, fin)

    # Read existing agregado CSV to preserve rows not needing recalculation
    print("  Leyendo archivo original...")
    with open(agg_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        orig_rows = list(reader)
    print(f"  {len(orig_rows):,} filas leídas")

    # Recalculate only affected rows (commit metrics in BOTH series)
    # Strategy: rebuild a lookup of new values, then merge into orig_rows
    # Affected: any metric in COMMIT_METRICS (alias changes aggregation)

    print("  Recalculando métricas de commits con alias...")

    # Load per-period data for commit metrics (both series)
    recalc_data = {}  # (serie, tipo_analisis, periodo_id, metrica_id) → (alias-applied list of (persona, val))

    for serie in ('versiones', 'versiones_canary'):
        excl_sql = EXCLUIR_ESTABLE if serie == 'versiones' else ()
        excl_clause = "AND p.etiqueta NOT IN %s" if excl_sql else ""
        for metrica in COMMIT_METRICS + ['dev_exp']:
            if metrica == 'dev_exp':
                params = [serie] + ([excl_sql] if excl_sql else [])
                cur.execute(f"""
                    SELECT r.periodo_id, r.contribuyente_login, r.value
                    FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
                    WHERE p.tipo_analisis=%s AND r.metrica_id='dev_exp'
                      AND r.contribuyente_login IS NOT NULL {excl_clause}
                      AND EXISTS (
                        SELECT 1 FROM resultado r2
                        WHERE r2.periodo_id=r.periodo_id AND r2.metrica_id='anmcc'
                          AND r2.contribuyente_login=r.contribuyente_login
                      )
                """, params)
            else:
                params = [serie, metrica] + ([excl_sql] if excl_sql else [])
                cur.execute(f"""
                    SELECT r.periodo_id, r.contribuyente_login, r.value
                    FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
                    WHERE p.tipo_analisis=%s AND r.metrica_id=%s
                      AND r.contribuyente_login IS NOT NULL {excl_clause}
                """, params)

            by_period = defaultdict(lambda: defaultdict(float))
            for pid, login, val in cur.fetchall():
                if val is None: continue
                persona = alias.get(login, login)
                by_period[pid][persona] += float(val)

            for pid, pvals in by_period.items():
                recalc_data[(serie, pid, metrica)] = {
                    p: v for p, v in pvals.items()
                }

    # Also recalculate pseudo-metrics
    for serie in ('versiones', 'versiones_canary'):
        excl_sql = EXCLUIR_ESTABLE if serie == 'versiones' else ()
        excl_clause = "AND p.etiqueta NOT IN %s" if excl_sql else ""
        for base_m in ['anmcc', 'exprev']:
            params = [serie, base_m] + ([excl_sql] if excl_sql else [])
            cur.execute(f"""
                SELECT r.periodo_id, r.contribuyente_login
                FROM resultado r JOIN periodo p ON p.periodo_id=r.periodo_id
                WHERE p.tipo_analisis=%s AND r.metrica_id=%s
                  AND r.contribuyente_login IS NOT NULL {excl_clause}
            """, params)
            by_period = defaultdict(set)
            for pid, login in cur.fetchall():
                persona = alias.get(login, login)
                by_period[pid].add(persona)
            for pid, personas in by_period.items():
                recalc_data[(serie, pid, f"__logins_{base_m}")] = personas

    con.close()

    # Build a dict for fast lookup of recalculated stats
    # Key: (serie_label, periodo_num, metrica_id, alcance) → new row dict
    new_stats = {}

    for serie in ('versiones', 'versiones_canary'):
        label = 'estable' if serie == 'versiones' else 'canary'
        pf_commits = pf_c_v if serie == 'versiones' else pf_c_c
        pf_interac = pf_i_v if serie == 'versiones' else pf_i_c

        # Metrics
        for metrica in COMMIT_METRICS + ['dev_exp']:
            pids = {pid for (s,pid,m) in recalc_data if s == serie and m == metrica}
            for pid in pids:
                meta_key = (serie, pid)
                if meta_key not in period_meta:
                    continue
                _, pnum, etiq, fini, ffin = period_meta[meta_key]
                pvals = recalc_data[(serie, pid, metrica)]
                ts_fin = fmt_ts(ffin)

                todas_vals = list(pvals.values())
                hum_vals   = [v for p,v in pvals.items() if bots.get(p,'humano')=='humano']

                for alcance, vals in [('todas', todas_vals), ('humanos', hum_vals)]:
                    st = agg_stats(vals)
                    key = (serie, pnum, metrica, alcance)
                    new_stats[key] = {
                        "n_contribuyentes": st['n'],
                        "suma": st['suma'], "media": st['media'],
                        "mediana": st['mediana'], "p90": st['p90'],
                        "maximo": st['maximo'],
                        "share_top1": st['share_top1'],
                        "share_top10pct": st['share_top10pct'],
                    }

        # Pseudo-metrics (activos_commits, nuevos_commits, activos_interaccion, nuevos_interaccion)
        for base_m, activos_m, nuevos_m, pf_key in [
            ('anmcc',  'activos_commits',     'nuevos_commits',     pf_commits),
            ('exprev', 'activos_interaccion', 'nuevos_interaccion', pf_interac),
        ]:
            pids = {pid for (s,pid,m) in recalc_data
                    if s == serie and m == f"__logins_{base_m}"}
            for pid in pids:
                meta_key = (serie, pid)
                if meta_key not in period_meta:
                    continue
                _, pnum, etiq, fini, ffin = period_meta[meta_key]
                ts_fin = fmt_ts(ffin)
                personas = recalc_data[(serie, pid, f"__logins_{base_m}")]

                humanos = {p for p in personas if bots.get(p,'humano') == 'humano'}
                nuevos_todas = {p for p in personas if pf_key.get(p,'') == ts_fin}
                nuevos_hum   = {p for p in humanos if pf_key.get(p,'') == ts_fin}

                for alcance, cnt_act, cnt_new in [
                    ('todas',   len(personas), len(nuevos_todas)),
                    ('humanos', len(humanos),  len(nuevos_hum)),
                ]:
                    new_stats[(serie, pnum, activos_m, alcance)] = {"n_contribuyentes": cnt_act}
                    new_stats[(serie, pnum, nuevos_m,  alcance)] = {"n_contribuyentes": cnt_new}

    print(f"  Nuevos stats calculados: {len(new_stats):,} combinaciones")

    # Merge into original rows
    n_updated = 0
    out_rows = []
    UPDATABLE_COLS = {"n_contribuyentes","suma","media","mediana","p90","maximo",
                      "share_top1","share_top10pct"}
    PSEUDO_ONLY_N  = {"activos_commits","nuevos_commits","activos_interaccion",
                      "nuevos_interaccion"}

    for row in orig_rows:
        serie  = row["serie"]
        pnum   = int(row["periodo_num"])
        mid    = row["metrica_id"]
        alcance = row["alcance"]

        key = (serie, pnum, mid, alcance)
        if key in new_stats:
            upd = new_stats[key]
            if mid in PSEUDO_ONLY_N:
                row["n_contribuyentes"] = upd["n_contribuyentes"]
            else:
                for col, val in upd.items():
                    if col in row and col in UPDATABLE_COLS:
                        row[col] = val
            n_updated += 1
        out_rows.append(row)

    with open(tmp_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)

    tmp_path.replace(agg_path)
    mb = agg_path.stat().st_size / 1024**2
    print(f"  Filas actualizadas: {n_updated:,} / {len(out_rows):,}")
    print(f"  {agg_path.name}: {len(out_rows):,} filas, {mb:.1f} MB")


# ── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("=== resolver_y_unificar.py ===\n")
    bots = load_bots()

    # FASE 1
    print("── FASE 1: Fetch commit aliases ──")
    cache_data = fetch_commit_aliases()

    lookup = build_alias_lookup(cache_data)

    # FASE 2
    alias = build_alias_csv(lookup)
    print(f"\n  Alias map: {len(alias):,} nombres→logins")

    # FASE 3
    update_detalle(alias, bots)

    # FASE 4
    validate(alias, bots)

    # FASE 5
    recalc_agregado(alias, bots)

    print("\n=== Done ===")

if __name__ == '__main__':
    main()
