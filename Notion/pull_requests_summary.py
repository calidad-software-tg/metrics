import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

# ATENCIÓN — MÉTRICA SIN CONSIGNA ASIGNADA TODAVÍA:
# Combina dos entradas del Notion que comparten exactamente el mismo campo
# GraphQL `pullRequests` con distintos filtros de estado:
# - Punto 6 de "Forks, Issues y Pull Requests": PRs totales, fusionados
#   (MERGED) y cerrados sin fusionar / rechazados (CLOSED).
# - "Pull Requests sin Fusionar (Number of Opened Pull Requests)": PRs
#   abiertas (OPEN) — la misma consulta, un estado más.
#
# NO confundir con Social Contribution (20/dc.py): ahí los mismos estados
# de PR (abierta/cerrada/fusionada) se cuentan POR AUTOR y se suman en un
# score individual junto con datos de issues; acá son SOLO PRs, desglosados
# por estado, tanto a nivel producto (totales del repo) como por persona
# (por autor) — pero sin mezclarlos en un score compuesto.
#
# Por persona requiere paginar por los nodos de PR (author + state) en vez
# de usar `totalCount`, que es agregado y no distingue autor.

_QUERY = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        author { login }
        state
      }
    }
  }
}
"""


class PullRequestsSummary(GitHubMetric):
    """
    Resumen de Pull Requests del repositorio: totales, abiertas (sin
    fusionar / pendientes), fusionadas y rechazadas (cerradas sin fusionar).

    Por producto: los 4 totales del repo. Por persona: los mismos 4
    campos, desglosados por autor de la PR.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.prs: list[dict] = []  # [{author, state}]

    def fetch(self, **kwargs):
        prs = []
        cursor, page = None, 0
        while True:
            page += 1
            data = self._graphql(_QUERY, {"owner": self.org, "name": self.repo, "after": cursor})
            conexion = data["data"]["repository"]["pullRequests"]
            for node in conexion["nodes"]:
                author_node = node.get("author") or {}
                prs.append({
                    "author": author_node.get("login") or "desconocido",
                    "state": node["state"],
                })
            print(f"  ...PRs página {page} ({len(prs)} acumuladas)", end="\r")
            if not conexion["pageInfo"]["hasNextPage"]:
                break
            cursor = conexion["pageInfo"]["endCursor"]
        print()
        self.prs = prs

    @staticmethod
    def _resumir(prs: list[dict]) -> dict[str, int]:
        return {
            "totales": len(prs),
            "abiertas": sum(1 for p in prs if p["state"] == "OPEN"),
            "fusionadas": sum(1 for p in prs if p["state"] == "MERGED"),
            "rechazadas": sum(1 for p in prs if p["state"] == "CLOSED"),
        }

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        return self._resumir(self.prs)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, dict]:
        by_author: dict[str, list[dict]] = {}
        for pr in self.prs:
            by_author.setdefault(pr["author"], []).append(pr)

        resultado = {login: self._resumir(prs) for login, prs in by_author.items()}
        return dict(sorted(resultado.items(), key=lambda x: x[1]["totales"], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        print(f"Consultando pull requests de {self.org}/{self.repo}...")
        self.fetch()

        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"\n{'Colaborador':<30} {'Totales':>8} {'Abiertas':>9} {'Fusion.':>8} {'Rechaz.':>8}")
            print("-" * 68)
            for login, r in resultado.items():
                print(f"{login:<30} {r['totales']:>8} {r['abiertas']:>9} {r['fusionadas']:>8} {r['rechazadas']:>8}")
        else:
            r = self.por_producto(fecha_inicio, fecha_fin)
            print(f"PRs totales:     {r['totales']}")
            print(f"PRs abiertas (sin fusionar): {r['abiertas']}")
            print(f"PRs fusionadas:  {r['fusionadas']}")
            print(f"PRs rechazadas:  {r['rechazadas']}")
