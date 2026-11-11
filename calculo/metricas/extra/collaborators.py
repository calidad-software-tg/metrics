import sys
from collections import Counter
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

# ATENCIÓN — MÉTRICA SIN CONSIGNA ASIGNADA TODAVÍA:
# Proviene del Notion "Número de Colaboradores, Número de Líneas de Código
# y Número de Branches".
#
# SUSTITUCIÓN DE FUENTE (documentada, mismo criterio que ANMCC/CPU Usage):
# el script original de Notion usa el campo GraphQL `collaborators`, que
# devuelve las cuentas con acceso de escritura/admin al repo. Ese campo
# requiere un token con permisos de administración sobre el repositorio
# (push/admin), algo que no está disponible al analizar repos OSS de
# terceros con un token de solo lectura — motivo por el cual no se usa acá.
#
# SEGUNDA SUSTITUCIÓN (esta vez para poder filtrar por fecha): la primera
# versión de este archivo usaba el REST `/repos/{owner}/{repo}/contributors`,
# que cuenta cuentas distintas con al menos un commit — pero ese endpoint
# es un acumulado a todo el historial y NO acepta `since`/`until`, así que
# no hay forma de pedirle "colaboradores hasta tal fecha". Se reemplaza acá
# por el mismo enfoque que ya usa commits_per_author.py: bajar el historial
# de commits vía GraphQL con `since`/`until` y contar autores distintos
# sobre esos commits. Mismo dato crudo, mismo costo, pero ahora sí es
# posible ventanear por fecha.

_GRAPHQL_QUERY = """
query($owner: String!, $name: String!, $after: String, $since: GitTimestamp, $until: GitTimestamp) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $after, since: $since, until: $until) {
            pageInfo { hasNextPage endCursor }
            nodes {
              oid
              author { user { login } name }
            }
          }
        }
      }
    }
  }
}
"""


class NumberOfCollaborators(GitHubMetric):
    """
    Número de Colaboradores del repositorio.

    Cuenta cuentas de autor distintas con al menos un commit en
    [fecha_inicio, fecha_fin] (proxy de "colaboradores" vía historial de
    commits, ver nota de sustitución arriba).

    Por persona: cantidad de commits de cada colaborador en ese período. Es
    el mismo dato crudo que expone commits_per_author.py; se mantiene acá
    también porque la pregunta que responde es distinta ("cuánto contribuyó
    cada colaborador conocido") en vez de "cuántos commits tiene el repo en
    total".
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.commits: list[dict] = []  # [{oid, author}]

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, **kwargs):
        print("Obteniendo colaboradores (historial de commits)...")
        commits = []
        cursor = None
        since = fecha_inicio.isoformat()
        until = fecha_fin.isoformat()

        while True:
            data = self._graphql(_GRAPHQL_QUERY, {
                "owner": self.org,
                "name": self.repo,
                "after": cursor,
                "since": since,
                "until": until,
            })
            history = data["data"]["repository"]["defaultBranchRef"]["target"]["history"]

            for node in history["nodes"]:
                author_node = node.get("author") or {}
                user = author_node.get("user") or {}
                commits.append({
                    "oid": node["oid"],
                    "author": user.get("login") or author_node.get("name") or "desconocido",
                })

            if not history["pageInfo"]["hasNextPage"]:
                break
            cursor = history["pageInfo"]["endCursor"]
            print(f"  ...{len(commits)} commits acumulados", end="\r")

        print()
        self.commits = commits

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return len({c["author"] for c in self.commits})

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        contador = Counter(c["author"] for c in self.commits)
        return dict(sorted(contador.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        self.fetch(fecha_inicio, fecha_fin)
        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"\n{'Colaborador':<30} Commits")
            print("-" * 40)
            for login, contribuciones in resultado.items():
                print(f"{login:<30} {contribuciones}")
        else:
            total = self.por_producto(fecha_inicio, fecha_fin)
            print(f"Número de Colaboradores: {total}")
