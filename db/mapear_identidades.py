"""
db/mapear_identidades.py

Construye una tabla de equivalencias nombre_git -> login_github para next.js, usando
exactamente la misma clave que las métricas del runner local (run_versiones_local.py
atribuye por el nombre de git del autor, `%an`, sin mailmap).

Fuentes de resolución, en este orden:
    1. Emails `*@users.noreply.github.com` (sacan el login del email).
    2. GraphQL object(oid: $sha).author.user.login para los que no resolvieron, hasta
       3 SHAs por identidad (el más reciente primero).

Salidas:
    db/identidades_git.csv       nombre_git, login, fuente, n_commits
    db/identidades_ambiguas.csv  nombre_git, logins (|-separados), n_commits

Uso:
    python3 db/mapear_identidades.py
Flags:
    --repo-dir .clones/next.js   dónde está el clon
    --max-shas 10                cuántos SHAs probar por identidad en la fase API
    --batch 50                   alias por request GraphQL
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_env = ROOT / ".env"
if _env.exists():
    for _l in _env.read_text().splitlines():
        if "=" in _l and not _l.startswith("#"):
            _k, _v = _l.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Email noreply con y sin ID numérico delante.
_NOREPLY_RE = re.compile(r"^(?:(\d+)\+)?([a-zA-Z0-9][a-zA-Z0-9\-]{0,38})@users\.noreply\.github\.com$")

GRAPHQL_URL = "https://api.github.com/graphql"


def ejecutar_git(dir_repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(dir_repo), *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def leer_commits(dir_repo: Path) -> list[tuple[str, str, str]]:
    """[(sha, nombre, email)] de todos los commits no-merge, en orden del log (más reciente primero)."""
    out = ejecutar_git(dir_repo, "log", "--no-merges", "--pretty=format:%H\t%an\t%ae")
    filas = []
    for linea in out.splitlines():
        partes = linea.split("\t", 2)
        if len(partes) == 3:
            sha, nombre, email = partes
            filas.append((sha, nombre.strip() or "desconocido", email.strip().lower()))
    return filas


def verificar_token() -> None:
    if not TOKEN:
        sys.exit("GITHUB_TOKEN no está en el entorno/.env — paro.")
    req = urllib.request.Request(
        "https://api.github.com/rate_limit",
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
    except Exception as e:
        sys.exit(f"GITHUB_TOKEN no funciona: {e}")
    gr = data["resources"]["graphql"]
    print(f"  Token OK · GraphQL remaining {gr['remaining']}/{gr['limit']}")


def consulta_graphql(query: str, variables: dict | None = None, intento: int = 0) -> dict:
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(
        GRAPHQL_URL,
        data=body,
        headers={"Authorization": f"Bearer {TOKEN}",
                 "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        if "errors" in data:
            # Error no transiente (ej. query mal armado): propagar.
            # Rate limit o abuse detection: reintentar con backoff.
            msg = str(data["errors"])[:500]
            if "RATE_LIMITED" in msg or "secondary rate" in msg.lower():
                if intento >= 4:
                    sys.exit(f"GraphQL rate limit insistente: {msg}")
                espera = min(2 ** intento, 60)
                print(f"  GraphQL rate limit, espero {espera}s...", flush=True)
                time.sleep(espera)
                return consulta_graphql(query, variables, intento + 1)
            # Si hay 'data', devolvemos lo que haya; algunos nodos pueden tener error.
            if data.get("data") is not None:
                return data
            sys.exit(f"GraphQL error: {msg}")
        return data
    except urllib.error.HTTPError as e:
        if e.code in (403, 429, 502, 503, 504) and intento < 4:
            espera = min(2 ** intento, 60)
            print(f"  HTTP {e.code}, reintento en {espera}s...", flush=True)
            time.sleep(espera)
            return consulta_graphql(query, variables, intento + 1)
        sys.exit(f"GraphQL HTTP {e.code}: {e.read()[:300]}")
    except urllib.error.URLError as e:
        if intento < 4:
            espera = min(2 ** intento, 60)
            print(f"  URLError, reintento en {espera}s...", flush=True)
            time.sleep(espera)
            return consulta_graphql(query, variables, intento + 1)
        sys.exit(f"URLError: {e}")


def login_por_noreply(email: str) -> str | None:
    m = _NOREPLY_RE.match(email)
    return m.group(2) if m else None


def resolver_por_api(pendientes: dict[str, list[str]], batch: int, max_shas: int) -> tuple[dict[str, str], dict[str, set[str]]]:
    """Para cada nombre pendiente, prueba HASTA max_shas SHAs vía GraphQL (no corta
    cuando encuentra el primero: siempre consulta todos los SHAs disponibles para detectar
    nombres git que apuntan a varios logins reales, como "Jimmy Lai" que aparece bajo
    `laijimmy0@gmail.com` → feedthejim y `tim@timneutkens.nl` → timneutkens).

    Un nombre queda ambiguo si al cabo de todas las rondas vemos 2+ logins distintos.
    Devuelve (nombre→login resuelto, nombre→{logins conflictivos})."""
    logins_por_nombre: dict[str, set[str]] = defaultdict(set)
    sin_login: set[str] = set()

    # Hasta `max_shas` rondas: ronda i = i-ésimo sha por nombre.
    for ronda in range(max_shas):
        a_consultar: list[tuple[str, str]] = []
        for nombre, shas in pendientes.items():
            if ronda < len(shas):
                a_consultar.append((nombre, shas[ronda]))
        if not a_consultar:
            break
        print(f"  Ronda {ronda + 1}/{max_shas}: {len(a_consultar)} nombres por consultar", flush=True)

        for i in range(0, len(a_consultar), batch):
            lote = a_consultar[i:i + batch]
            partes_q = []
            for j, (_, sha) in enumerate(lote):
                partes_q.append(
                    f'a{j}: object(oid: "{sha}") {{ ... on Commit {{ author {{ user {{ login }} }} }} }}'
                )
            query = ('query { repository(owner: "vercel", name: "next.js") { '
                     + " ".join(partes_q) + " } }")
            data = consulta_graphql(query)
            repo_obj = ((data or {}).get("data") or {}).get("repository") or {}
            for j, (nombre, _) in enumerate(lote):
                nodo = repo_obj.get(f"a{j}")
                if not nodo:
                    continue
                autor = (nodo.get("author") or {})
                user = autor.get("user") or {}
                lg = user.get("login")
                if lg:
                    logins_por_nombre[nombre].add(lg)
                else:
                    sin_login.add(nombre)

        n_resueltos = sum(1 for s in logins_por_nombre.values() if len(s) == 1)
        n_amb = sum(1 for s in logins_por_nombre.values() if len(s) > 1)
        print(f"    acumulado: con 1 login={n_resueltos}, ambiguos={n_amb}", flush=True)

    resueltos: dict[str, str] = {n: next(iter(s)) for n, s in logins_por_nombre.items() if len(s) == 1}
    ambiguos: dict[str, set[str]] = {n: s for n, s in logins_por_nombre.items() if len(s) > 1}
    return resueltos, ambiguos


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-dir", default=".clones/next.js")
    ap.add_argument("--max-shas", type=int, default=3)
    ap.add_argument("--batch", type=int, default=50)
    args = ap.parse_args()

    repo_dir = Path(args.repo_dir)
    if not (repo_dir / ".git").exists() and not (repo_dir / "HEAD").exists():
        sys.exit(f"No encuentro el clon en {repo_dir}")

    print(f"Leyendo commits de {repo_dir}...", flush=True)
    commits = leer_commits(repo_dir)
    print(f"  {len(commits):,} commits no-merge, {len({c[1] for c in commits}):,} nombres distintos")

    verificar_token()

    # Agrupar por nombre: n_commits y SHAs recientes y emails observados.
    por_nombre: dict[str, dict] = {}
    for sha, nombre, email in commits:
        d = por_nombre.setdefault(nombre, {"n": 0, "shas": [], "emails": set()})
        d["n"] += 1
        if len(d["shas"]) < args.max_shas:
            d["shas"].append(sha)  # commits llegan en orden "más reciente primero"
        if email:
            d["emails"].add(email)

    # Fase a) noreply.
    resueltos: dict[str, tuple[str, str]] = {}  # nombre -> (login, fuente)
    ambiguos_noreply: dict[str, set[str]] = defaultdict(set)
    for nombre, d in por_nombre.items():
        logins = set()
        for em in d["emails"]:
            lg = login_por_noreply(em)
            if lg:
                logins.add(lg)
        if len(logins) == 1:
            resueltos[nombre] = (next(iter(logins)), "noreply")
        elif len(logins) > 1:
            ambiguos_noreply[nombre] = logins

    print(f"\nFase a) noreply: {len(resueltos):,} nombres resueltos, {len(ambiguos_noreply):,} ambiguos")

    # Fase b) GraphQL para los no resueltos ni ambiguos.
    pendientes = {nombre: d["shas"] for nombre, d in por_nombre.items()
                  if nombre not in resueltos and nombre not in ambiguos_noreply}
    print(f"\nFase b) GraphQL: {len(pendientes):,} nombres a consultar", flush=True)

    api_resueltos, api_ambiguos = resolver_por_api(pendientes, args.batch, args.max_shas)
    for nombre, lg in api_resueltos.items():
        resueltos[nombre] = (lg, "api")

    print(f"  Fase b: {len(api_resueltos):,} resueltos por API, {len(api_ambiguos):,} ambiguos")

    # Guardar
    out_csv = ROOT / "db" / "identidades_git.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nombre_git", "login", "fuente", "n_commits"])
        for nombre, (lg, fuente) in sorted(resueltos.items(), key=lambda x: -por_nombre[x[0]]["n"]):
            w.writerow([nombre, lg, fuente, por_nombre[nombre]["n"]])

    out_amb = ROOT / "db" / "identidades_ambiguas.csv"
    ambiguos: dict[str, set[str]] = {}
    ambiguos.update(ambiguos_noreply)
    for n, logins in api_ambiguos.items():
        ambiguos.setdefault(n, set()).update(logins)
    with open(out_amb, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nombre_git", "logins", "n_commits"])
        for nombre in sorted(ambiguos.keys(), key=lambda n: -por_nombre[n]["n"]):
            w.writerow([nombre, "|".join(sorted(ambiguos[nombre])), por_nombre[nombre]["n"]])

    # Revisión manual: nombres de una palabra típicos de nombre de pila (p. ej. "Henrik",
    # "Chris") + logins con 2+ nombres git disímiles entre sí y respecto del login.
    # Son candidatos a ambiguos no detectados por la API (una persona dominante hace que
    # todas las queries devuelvan el mismo login aunque otra persona haya commiteado
    # ocasionalmente bajo el mismo nombre).
    import re as _re
    _NOMBRE_PILA_RE = _re.compile(r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{2,11}$")

    def _norm(s): return _re.sub(r"[\s\-_.]", "", (s or "").lower())

    # Agrupar nombres resueltos por login
    nombres_por_login: dict[str, list[str]] = defaultdict(list)
    for n, (lg, _f) in resueltos.items():
        nombres_por_login[lg].append(n)

    revisar: list[tuple[str, str, str]] = []  # (nombre_git, login, motivo)
    for nombre, (lg, _f) in resueltos.items():
        if _NOMBRE_PILA_RE.match(nombre) and _norm(nombre) != _norm(lg):
            revisar.append((nombre, lg, "nombre_de_pila_de_una_palabra"))

    for lg, nombres in nombres_por_login.items():
        if len(nombres) < 2:
            continue
        normas = {_norm(n) for n in nombres}
        norma_lg = _norm(lg)
        # Si alguno de los nombres NO se parece al login ni a otro de los nombres: avisar.
        disimiles = [n for n in nombres if _norm(n) != norma_lg
                     and sum(1 for n2 in nombres if n2 != n and _norm(n) == _norm(n2)) == 0]
        if len(disimiles) >= 1 and len(normas) >= 2:
            for n in disimiles:
                motivo = f"login_con_varios_nombres_disimiles(todos: {' | '.join(sorted(nombres))})"
                revisar.append((n, lg, motivo))

    # Deduplicar revisar
    revisar = sorted(set(revisar))
    out_rev = ROOT / "db" / "identidades_revisar.csv"
    with open(out_rev, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["nombre_git", "login", "motivo", "n_commits"])
        for n, lg, motivo in revisar:
            w.writerow([n, lg, motivo, por_nombre[n]["n"]])

    # Cobertura.
    n_nombres = len(por_nombre)
    n_commits = sum(d["n"] for d in por_nombre.values())
    n_res = len(resueltos)
    n_amb = len(ambiguos)
    com_res = sum(por_nombre[n]["n"] for n in resueltos)
    com_amb = sum(por_nombre[n]["n"] for n in ambiguos)
    print(f"\n=== Cobertura ===")
    print(f"  Identidades: {n_res:,} resueltas / {n_amb:,} ambiguas / {n_nombres:,} total "
          f"({100*n_res/n_nombres:.1f}% resueltas)")
    print(f"  Commits:     {com_res:,} resueltos / {com_amb:,} ambiguos / {n_commits:,} total "
          f"({100*com_res/n_commits:.1f}% resueltos)")
    print(f"  Para revisión manual: {len(revisar)} entradas marcadas")
    print(f"\nSalidas:")
    print(f"  {out_csv}")
    print(f"  {out_amb}")
    print(f"  {out_rev}")


if __name__ == "__main__":
    main()
