import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

# ATENCIÓN — MÉTRICA SIN CONSIGNA ASIGNADA TODAVÍA:
# Proviene del Notion "Developer Contribution" (Número de Commits por
# Contribuidor). NO confundir con Social Contribution (metrics/20/dc.py,
# reexportada en metrics/18/sc.py), que en el catálogo canónico también
# quedó etiquetada como "Developer Contribution" pero mide una cosa
# distinta: participación en issues/PRs (Falcão et al. 2020), no cantidad
# de commits. Ver metrics/20/20 - Social Contribution.md, sección 1, para
# la discrepancia de nombres ya documentada.
#
# Diferencia respecto al script original: fetch vía GraphQL (mismo patrón
# que metrics/10/anmcc.py) en vez de REST paginado a mano, para traer
# commits y autor en una sola consulta por página.

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


class CommitsPerAuthor(GitHubMetric):
    """
    Developer Contribution — Número de Commits por Contribuidor.

    Cuenta cuántos commits realizó cada autor en el repositorio. Producto:
    total de commits del repo. Persona: commits por autor, ordenado de
    mayor a menor.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.commits: list[dict] = []  # [{oid, author}]

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, **kwargs):
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
            print(f"  ...{len(commits)} commits descargados", end="\r")

        self.commits = commits

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return len(self.commits)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        contador = Counter(c["author"] for c in self.commits)
        return dict(sorted(contador.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona", **kwargs):
        print(f"Descargando commits de {self.org}/{self.repo}...")
        self.fetch(fecha_inicio, fecha_fin)
        print(f"Commits descargados: {len(self.commits)}\n")

        if por == "producto":
            total = self.por_producto(fecha_inicio, fecha_fin)
            print(f"Número total de commits: {total}")
        else:
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"{'Colaborador':<30} Commits")
            print("-" * 40)
            for autor, cantidad in resultado.items():
                print(f"{autor:<30} {cantidad}")
            print("-" * 40)
            print(f"{'Total':<30} {sum(resultado.values())}")
