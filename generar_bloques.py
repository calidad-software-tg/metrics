"""
Genera los períodos "adaptativos" (tipo_analisis='adaptativo') de un repo y
los persiste en la tabla `periodo`.

Criterio: arranca de una grilla candidata mensual (desde la fecha de
creación del repo hasta hoy) y fusiona meses consecutivos hasta que el
bloque acumulado junte un piso mínimo de actividad (issues cerradas +
colaboradores activos, que son el recurso más escaso del repo). El
remanente final que no llega al piso se pega al último bloque cerrado.

Uso:
    python generar_bloques.py <org>/<repo> [--piso-issues 15] [--piso-colabs 3] [--principal]
    python generar_bloques.py tldr-pages/tldr --principal
"""

import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import requests

# --- cargar .env -------------------------------------------------------
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

db_env_path = Path(__file__).resolve().parent / "db" / ".env"
if db_env_path.exists():
    for line in db_env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

DB_HOST     = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT     = os.environ.get("POSTGRES_PORT", "5432")
DB_USER     = os.environ.get("POSTGRES_USER", "metricas")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "metricas")
DB_NAME     = os.environ.get("POSTGRES_DB", "resultados_metricas")

_BASE_URL = "https://api.github.com"


def _headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _graphql(query: str, variables: dict) -> dict:
    resp = requests.post(f"{_BASE_URL}/graphql", json={"query": query, "variables": variables},
                          headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GraphQL error: {data['errors']}")
    return data


# --- 1. Datos crudos del repo (una sola vez, todo el historial) --------

def fecha_creacion_repo(org: str, repo: str) -> datetime:
    resp = requests.get(f"{_BASE_URL}/repos/{org}/{repo}", headers=_headers(), timeout=30)
    resp.raise_for_status()
    return datetime.fromisoformat(resp.json()["created_at"].replace("Z", "+00:00"))


_QUERY_ISSUES_CERRADOS = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(states: CLOSED, first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes { closedAt }
    }
  }
}
"""


def fechas_issues_cerrados(org: str, repo: str) -> list[datetime]:
    fechas = []
    cursor = None
    while True:
        data = _graphql(_QUERY_ISSUES_CERRADOS, {"owner": org, "name": repo, "after": cursor})
        page = data["data"]["repository"]["issues"]
        for node in page["nodes"]:
            if node.get("closedAt"):
                fechas.append(datetime.fromisoformat(node["closedAt"].replace("Z", "+00:00")))
        print(f"  ...{len(fechas)} issues cerrados descargados", end="\r")
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    print()
    return fechas


_QUERY_COMMITS = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $after) {
            pageInfo { hasNextPage endCursor }
            nodes { committedDate author { user { login } name } }
          }
        }
      }
    }
  }
}
"""


def commits_autor_fecha(org: str, repo: str) -> list[tuple[datetime, str]]:
    resultado = []
    cursor = None
    while True:
        data = _graphql(_QUERY_COMMITS, {"owner": org, "name": repo, "after": cursor})
        history = data["data"]["repository"]["defaultBranchRef"]["target"]["history"]
        for node in history["nodes"]:
            fecha = datetime.fromisoformat(node["committedDate"].replace("Z", "+00:00"))
            author_node = node.get("author") or {}
            user = author_node.get("user") or {}
            login = user.get("login") or author_node.get("name") or "desconocido"
            resultado.append((fecha, login))
        print(f"  ...{len(resultado)} commits descargados", end="\r")
        if not history["pageInfo"]["hasNextPage"]:
            break
        cursor = history["pageInfo"]["endCursor"]
    print()
    return resultado


# --- 2. Grilla candidata mensual + conteo de actividad por candidato ---

def _sumar_mes(fecha: datetime) -> datetime:
    if fecha.month == 12:
        return fecha.replace(year=fecha.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    return fecha.replace(month=fecha.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


def grilla_candidata_mensual(fecha_creacion: datetime, fecha_fin: datetime,
                              issues_cerrados: list[datetime],
                              commits: list[tuple[datetime, str]]) -> list[tuple]:
    inicio = fecha_creacion.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    candidatos = []
    while inicio < fecha_fin:
        fin = min(_sumar_mes(inicio), fecha_fin)
        n_issues = sum(1 for f in issues_cerrados if inicio <= f < fin)
        colabs = {login for f, login in commits if inicio <= f < fin}
        candidatos.append((inicio, fin, n_issues, len(colabs)))
        inicio = fin
    return candidatos


# --- 3. Fusión adaptativa ------------------------------------------------

def bloques_adaptativos(candidatos: list[tuple], piso_issues: int = 15, piso_colabs: int = 3) -> list[tuple]:
    bloques = []
    acumulado = None
    for inicio, fin, n_issues, n_colabs in candidatos:
        if acumulado is None:
            acumulado = [inicio, fin, n_issues, n_colabs]
        else:
            acumulado[1] = fin
            acumulado[2] += n_issues
            acumulado[3] = max(acumulado[3], n_colabs)

        if acumulado[2] >= piso_issues and acumulado[3] >= piso_colabs:
            bloques.append(tuple(acumulado))
            acumulado = None

    if acumulado:
        if bloques:
            ult = list(bloques[-1])
            ult[1] = acumulado[1]
            ult[2] += acumulado[2]
            ult[3] = max(ult[3], acumulado[3])
            bloques[-1] = tuple(ult)
        else:
            bloques.append(tuple(acumulado))
    return bloques


def etiqueta_bloque(inicio: datetime, fin_exclusivo: datetime) -> str:
    fin_incl = fin_exclusivo
    if inicio.year == fin_incl.year and inicio.month == fin_incl.month:
        return inicio.strftime("%Y-%m")
    fin_mes_previo = fin_incl.month - 1 or 12
    fin_anio = fin_incl.year if fin_incl.month != 1 else fin_incl.year - 1
    return f"{inicio.strftime('%Y-%m')}_a_{fin_anio}-{fin_mes_previo:02d}"


# --- 4. Persistencia -----------------------------------------------------

def _conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER,
                             password=DB_PASSWORD, dbname=DB_NAME)


def guardar_periodos(cur, repo_id: int, bloques: list[tuple], piso_issues: int,
                      piso_colabs: int, es_principal: bool):
    import json
    parametros = json.dumps({"piso_issues": piso_issues, "piso_colabs": piso_colabs, "grid": "mensual"})

    cur.execute("DELETE FROM resultado WHERE periodo_id IN "
                "(SELECT periodo_id FROM periodo WHERE repo_id = %s AND tipo_analisis = 'adaptativo')",
                (repo_id,))
    cur.execute("DELETE FROM periodo WHERE repo_id = %s AND tipo_analisis = 'adaptativo'", (repo_id,))

    for num, (inicio, fin, n_issues, n_colabs) in enumerate(bloques, start=1):
        cur.execute(
            """
            INSERT INTO periodo (repo_id, tipo_analisis, periodo_num, fecha_inicio, fecha_fin,
                                  etiqueta, parametros, n_issues_cerradas, n_colaboradores, es_principal)
            VALUES (%s, 'adaptativo', %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (repo_id, num, inicio, fin, etiqueta_bloque(inicio, fin), parametros,
             n_issues, n_colabs, es_principal),
        )


def main():
    parser = argparse.ArgumentParser(description="Genera períodos adaptativos para un repo")
    parser.add_argument("repo", help="org/repo, ej: tldr-pages/tldr")
    parser.add_argument("--piso-issues", type=int, default=15)
    parser.add_argument("--piso-colabs", type=int, default=3)
    parser.add_argument("--principal", action="store_true", help="marcar es_principal=TRUE")
    args = parser.parse_args()

    if not GITHUB_TOKEN:
        print("Falta GITHUB_TOKEN en .env", file=sys.stderr)
        sys.exit(1)

    org, repo = args.repo.split("/", 1)
    fecha_fin = datetime.now(timezone.utc)

    print(f"Repo: {org}/{repo}")
    print("Obteniendo fecha de creación...")
    fecha_creacion = fecha_creacion_repo(org, repo)
    print(f"  Creado: {fecha_creacion.date()}")

    print("Bajando issues cerrados (todo el historial)...")
    issues_cerrados = fechas_issues_cerrados(org, repo)
    print(f"  Total: {len(issues_cerrados)}")

    print("Bajando commits (rama default, todo el historial)...")
    commits = commits_autor_fecha(org, repo)
    print(f"  Total: {len(commits)}")

    print("Armando grilla candidata mensual...")
    candidatos = grilla_candidata_mensual(fecha_creacion, fecha_fin, issues_cerrados, commits)
    print(f"  Meses candidatos: {len(candidatos)}")

    print(f"Fusionando (piso_issues={args.piso_issues}, piso_colabs={args.piso_colabs})...")
    bloques = bloques_adaptativos(candidatos, args.piso_issues, args.piso_colabs)
    print(f"  Bloques finales: {len(bloques)}\n")

    for num, (inicio, fin, n_issues, n_colabs) in enumerate(bloques, start=1):
        print(f"  {num:>3}. {inicio.date()} -> {fin.date()}  "
              f"({etiqueta_bloque(inicio, fin)})  issues={n_issues} colabs={n_colabs}")

    con = _conn()
    cur = con.cursor()
    cur.execute("SELECT repo_id FROM repos WHERE full_name = %s", (f"{org}/{repo}",))
    row = cur.fetchone()
    if row is None:
        print(f"\nERROR: {org}/{repo} no está en la tabla repos. Cargá repos_seed.sql primero.",
              file=sys.stderr)
        sys.exit(1)
    repo_id = row[0]

    guardar_periodos(cur, repo_id, bloques, args.piso_issues, args.piso_colabs, args.principal)
    con.commit()
    cur.close()
    con.close()
    print(f"\nPersistido: {len(bloques)} períodos para repo_id={repo_id} (tipo_analisis='adaptativo').")


if __name__ == "__main__":
    main()
