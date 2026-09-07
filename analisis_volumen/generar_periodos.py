"""
generar_periodos.py — Partición del historial por cantidad fija de eventos (criterio 4).

Corta cada N eventos acumulados (commits o issues cerradas). El eje deja de ser el
calendario: la duración de cada bloque pasa a ser una variable derivada, inversa al
throughput del proyecto en ese tramo.

Uso:
    python -m particiones.generar_periodos --diagnostico
    python -m particiones.generar_periodos --evento commits --n 500 --desde 2016 --principal
    python -m particiones.generar_periodos --evento issues_cerradas --n 50

Requiere en .env: GITHUB_TOKEN, TARGET_ORG, TARGET_REPO
                  POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST, POSTGRES_PORT
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

try:
    import psycopg2
    from psycopg2.extras import Json
except ImportError:
    psycopg2 = None

API = "https://api.github.com"

# Fecha de corte del estudio. FIJA a propósito: si fuera datetime.now(), dos corridas
# en fechas distintas darían particiones distintas y el trabajo no sería reproducible.
FECHA_CORTE = datetime(2026, 8, 31, tzinfo=timezone.utc)

PATRONES_BOT = ("[bot]", "-bot", "dependabot", "github-actions", "renovate", "bot@")

CACHE = Path(__file__).resolve().parent.parent / "data"


# ---------------------------------------------------------------------------
# .env
# ---------------------------------------------------------------------------
def cargar_env():
    for candidato in (
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent.parent / "db" / ".env",
    ):
        if candidato.exists():
            for line in candidato.read_text().splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------
def _headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_paginado(url, token, params, descripcion):
    """GET con paginación y manejo de rate limit."""
    items, page = [], 1
    while True:
        r = requests.get(url, headers=_headers(token),
                         params={**params, "per_page": 100, "page": page}, timeout=30)

        if r.status_code in (403, 429) and "rate limit" in r.text.lower():
            reset = int(r.headers.get("X-RateLimit-Reset", 0))
            espera = max(reset - time.time(), 0) + 5
            print(f"  [rate limit] esperando {espera:.0f}s...", file=sys.stderr)
            time.sleep(espera)
            continue
        r.raise_for_status()

        lote = r.json()
        if not lote:
            break
        items.extend(lote)

        if page % 10 == 0:
            print(f"  {descripcion}: pág {page} — {len(items)} items "
                  f"— quota {r.headers.get('X-RateLimit-Remaining', '?')}")
        page += 1
    return items


def _parse(fecha_iso):
    return datetime.fromisoformat(fecha_iso.replace("Z", "+00:00"))


def es_bot(login, nombre):
    txt = f"{login or ''} {nombre or ''}".lower()
    return any(p in txt for p in PATRONES_BOT)


def traer_commits(token, org, repo, usar_cache=True):
    """
    Devuelve [{fecha, login, bot}] ordenado del más viejo al más nuevo.

    Usa committer.date, NO author.date: tldr trabaja con squash merge, así que la
    fecha de autor puede ser muy anterior a la entrada real del commit a main.
    Medido sobre el historial de tldr, 1.465 commits (6,2%) romperían el orden
    cronológico si se ordenara por author.date.
    """
    cache = CACHE / f"commits_{org}_{repo}.json"
    if usar_cache and cache.exists():
        print(f"  (leyendo cache {cache.name})")
        crudo = json.loads(cache.read_text())
        return [{**c, "fecha": _parse(c["fecha"])} for c in crudo]

    print(f"Bajando commits de {org}/{repo}...")
    raw = _get_paginado(f"{API}/repos/{org}/{repo}/commits", token,
                        {"until": FECHA_CORTE.isoformat()}, "commits")

    eventos = []
    for c in raw:
        autor = c.get("author") or {}
        nombre = ((c.get("commit") or {}).get("author") or {}).get("name")
        eventos.append({
            "fecha": _parse(c["commit"]["committer"]["date"]),
            "login": autor.get("login"),
            "bot": autor.get("type") == "Bot" or es_bot(autor.get("login"), nombre),
        })

    eventos.sort(key=lambda e: e["fecha"])
    CACHE.mkdir(exist_ok=True)
    cache.write_text(json.dumps(
        [{**e, "fecha": e["fecha"].isoformat()} for e in eventos], indent=1))
    return eventos


def traer_issues_cerradas(token, org, repo, usar_cache=True):
    """
    Devuelve [{fecha, login, bot}] con la fecha de CIERRE de cada issue.

    El endpoint /issues devuelve issues Y pull requests mezclados: los PRs traen
    la clave "pull_request". Se filtran, porque para el estudio son cosas distintas
    (en tldr hay ~18.400 PRs mergeados contra ~1.500 issues cerradas; no filtrar
    cambiaría por completo la partición).
    """
    cache = CACHE / f"issues_cerradas_{org}_{repo}.json"
    if usar_cache and cache.exists():
        print(f"  (leyendo cache {cache.name})")
        crudo = json.loads(cache.read_text())
        return [{**i, "fecha": _parse(i["fecha"])} for i in crudo]

    print(f"Bajando issues cerradas de {org}/{repo}...")
    raw = _get_paginado(f"{API}/repos/{org}/{repo}/issues", token,
                        {"state": "closed", "sort": "updated", "direction": "asc"},
                        "issues")

    eventos = []
    for it in raw:
        if "pull_request" in it:
            continue
        if not it.get("closed_at"):
            continue
        fecha = _parse(it["closed_at"])
        if fecha > FECHA_CORTE:
            continue
        u = it.get("user") or {}
        eventos.append({
            "fecha": fecha,
            "login": u.get("login"),
            "bot": u.get("type") == "Bot" or es_bot(u.get("login"), None),
        })

    eventos.sort(key=lambda e: e["fecha"])
    CACHE.mkdir(exist_ok=True)
    cache.write_text(json.dumps(
        [{**e, "fecha": e["fecha"].isoformat()} for e in eventos], indent=1))
    return eventos


# ---------------------------------------------------------------------------
# Partición
# ---------------------------------------------------------------------------
def generar_bloques(eventos, n_por_bloque, evento="commits",
                    excluir_bots=True, anio_desde=None):
    """
    Corta la lista de eventos en chunks de n_por_bloque.
    Devuelve dicts con la forma de la tabla `periodo`.
    """
    usados = [e for e in eventos if not (excluir_bots and e["bot"])]
    if anio_desde:
        usados = [e for e in usados if e["fecha"].year >= anio_desde]
    if not usados:
        raise SystemExit("No quedaron eventos después de filtrar.")

    bloques = []
    for i in range(0, len(usados), n_por_bloque):
        chunk = usados[i:i + n_por_bloque]
        num = len(bloques) + 1
        ini, fin = chunk[0]["fecha"], chunk[-1]["fecha"]
        completo = len(chunk) == n_por_bloque

        bloques.append({
            "periodo_num": num,
            "fecha_inicio": ini,
            "fecha_fin": fin,
            "etiqueta": f"vol{n_por_bloque}-{num:02d} ({ini:%Y-%m}→{fin:%Y-%m})",
            "n_colaboradores": len({e["login"] for e in chunk if e["login"]}),
            # n_issues_cerradas solo se llena si el contador ES issues cerradas;
            # si el contador son commits, queda en NULL y lo completa otro proceso.
            "n_issues_cerradas": len(chunk) if evento == "issues_cerradas" else None,
            "parametros": {
                "evento": evento,
                "n_por_bloque": n_por_bloque,
                "n_real": len(chunk),
                "chunk_completo": completo,
                "bots_excluidos": excluir_bots,
                "anio_desde": anio_desde,
                "duracion_dias": round((fin - ini).total_seconds() / 86400, 2),
                "fecha_corte_estudio": FECHA_CORTE.isoformat(),
            },
        })
    return bloques


def diagnostico(eventos, evento, ns=(200, 300, 500, 750, 1000),
                anios=(None, 2016, 2018, 2020)):
    """Barrido para elegir N y punto de inicio. Correr esto ANTES de cargar nada."""
    bots = sum(1 for e in eventos if e["bot"])
    print(f"\n{'=' * 68}\nDIAGNÓSTICO — contador: {evento}\n{'=' * 68}")
    print(f"eventos totales : {len(eventos)}")
    print(f"  de bots       : {bots} ({100 * bots / max(len(eventos), 1):.1f}%)")
    print(f"rango           : {eventos[0]['fecha']:%Y-%m-%d} → {eventos[-1]['fecha']:%Y-%m-%d}")

    print(f"\n{'desde':>7} {'N':>6} {'bloques':>8} {'días med':>9} {'ratio':>7} {'colab med':>10}")
    print("-" * 52)
    for anio in anios:
        for n in ns:
            try:
                b = generar_bloques(eventos, n, evento, anio_desde=anio)
            except SystemExit:
                continue
            comp = [x for x in b if x["parametros"]["chunk_completo"]]
            if len(comp) < 2:
                continue
            dur = sorted(x["parametros"]["duracion_dias"] for x in comp)
            colab = sorted(x["n_colaboradores"] for x in comp)
            ratio = dur[-1] / max(dur[0], 0.01)
            print(f"{str(anio or 'todo'):>7} {n:6d} {len(b):8d} "
                  f"{dur[len(dur) // 2]:9.0f} {ratio:6.0f}x {colab[len(colab) // 2]:10d}")
        print()

    print("Qué mirar:")
    print("  - ratio max/min alto => bloques incomparables en cualquier métrica")
    print("    que dependa del tiempo transcurrido (tasas, frecuencias).")
    print("  - pocos bloques => no alcanza para clustering ni correlaciones.")
    print("  - recortar los primeros años suele bajar el ratio a muy bajo costo.")


# ---------------------------------------------------------------------------
# Carga en Postgres
# ---------------------------------------------------------------------------
def conectar():
    if psycopg2 is None:
        raise SystemExit("Falta psycopg2: pip install psycopg2-binary")
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        user=os.environ.get("POSTGRES_USER", "metricas"),
        password=os.environ.get("POSTGRES_PASSWORD", "metricas"),
        dbname=os.environ.get("POSTGRES_DB", "resultados_metricas"),
    )


def repo_id(cur, org, repo):
    cur.execute("SELECT repo_id FROM repos WHERE full_name = %s", (f"{org}/{repo}",))
    fila = cur.fetchone()
    if not fila:
        raise SystemExit(f"{org}/{repo} no está en la tabla repos. Corré repos_seed.sql.")
    return fila[0]


def cargar(bloques, org, repo, variante, principal=False, reemplazar=False):
    """
    Inserta en `periodo`. `variante` distingue corridas del mismo tipo_analisis
    (ej. 'n500_desde2016' vs 'n300_desde2016') — requiere migration_002.
    """
    conn = conectar()
    cur = conn.cursor()
    rid = repo_id(cur, org, repo)

    if reemplazar:
        cur.execute("""
            DELETE FROM resultado WHERE periodo_id IN (
                SELECT periodo_id FROM periodo
                WHERE repo_id=%s AND tipo_analisis='volumen' AND variante=%s)
        """, (rid, variante))
        cur.execute("""DELETE FROM periodo
                       WHERE repo_id=%s AND tipo_analisis='volumen' AND variante=%s""",
                    (rid, variante))
        print(f"  (borrados {cur.rowcount} períodos previos de variante '{variante}')")

    if principal:
        cur.execute("UPDATE periodo SET es_principal=FALSE WHERE repo_id=%s", (rid,))

    for b in bloques:
        cur.execute("""
            INSERT INTO periodo (repo_id, tipo_analisis, variante, periodo_num,
                                 fecha_inicio, fecha_fin, etiqueta, parametros,
                                 n_issues_cerradas, n_colaboradores, es_principal)
            VALUES (%s, 'volumen', %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (repo_id, tipo_analisis, variante, periodo_num)
            DO UPDATE SET fecha_inicio=EXCLUDED.fecha_inicio,
                          fecha_fin=EXCLUDED.fecha_fin,
                          etiqueta=EXCLUDED.etiqueta,
                          parametros=EXCLUDED.parametros,
                          n_issues_cerradas=EXCLUDED.n_issues_cerradas,
                          n_colaboradores=EXCLUDED.n_colaboradores,
                          es_principal=EXCLUDED.es_principal
        """, (rid, variante, b["periodo_num"], b["fecha_inicio"], b["fecha_fin"],
              b["etiqueta"], Json(b["parametros"]), b["n_issues_cerradas"],
              b["n_colaboradores"], principal))

    conn.commit()
    cur.close()
    conn.close()
    print(f"Cargados {len(bloques)} períodos (variante='{variante}', principal={principal}).")


# ---------------------------------------------------------------------------
def main():
    cargar_env()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--evento", choices=["commits", "issues_cerradas"], default="commits")
    ap.add_argument("--n", type=int, default=500, help="eventos por bloque")
    ap.add_argument("--desde", type=int, default=None, help="año de inicio (recorta prehistoria)")
    ap.add_argument("--incluir-bots", action="store_true")
    ap.add_argument("--diagnostico", action="store_true", help="solo barrido, no carga nada")
    ap.add_argument("--principal", action="store_true", help="marcar es_principal=TRUE")
    ap.add_argument("--reemplazar", action="store_true", help="borrar la variante previa")
    ap.add_argument("--dry-run", action="store_true", help="mostrar bloques sin cargar")
    ap.add_argument("--sin-cache", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    org = os.environ.get("TARGET_ORG")
    repo = os.environ.get("TARGET_REPO")
    if not all([token, org, repo]):
        raise SystemExit("Faltan GITHUB_TOKEN / TARGET_ORG / TARGET_REPO en .env")

    traer = traer_commits if args.evento == "commits" else traer_issues_cerradas
    eventos = traer(token, org, repo, usar_cache=not args.sin_cache)

    if args.diagnostico:
        ns = (200, 300, 500, 750, 1000) if args.evento == "commits" else (25, 50, 75, 100)
        diagnostico(eventos, args.evento, ns=ns)
        return

    bloques = generar_bloques(eventos, args.n, args.evento,
                              excluir_bots=not args.incluir_bots,
                              anio_desde=args.desde)

    print(f"\n{len(bloques)} bloques (evento={args.evento}, N={args.n}, desde={args.desde}):")
    for b in bloques:
        p = b["parametros"]
        marca = "" if p["chunk_completo"] else f"  <- PARCIAL {p['n_real']}/{args.n}"
        print(f"  {b['periodo_num']:3d}  {b['fecha_inicio']:%Y-%m-%d} → {b['fecha_fin']:%Y-%m-%d}"
              f"  {p['duracion_dias']:7.1f}d  {b['n_colaboradores']:4d} colab{marca}")

    if args.dry_run:
        print("\n(dry-run: no se cargó nada)")
        return

    variante = f"n{args.n}" + (f"_desde{args.desde}" if args.desde else "")
    cargar(bloques, org, repo, variante,
           principal=args.principal, reemplazar=args.reemplazar)


if __name__ == "__main__":
    main()