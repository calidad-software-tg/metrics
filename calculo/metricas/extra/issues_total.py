import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

# ATENCIÓN — MÉTRICA SIN CONSIGNA ASIGNADA TODAVÍA:
# Proviene del punto 5 del Notion "Forks, Issues y Pull Requests" (Número
# total de issues, `issues.totalCount`, SIN filtrar por estado).
#
# NO confundir con:
# - NOI (metrics/28, metrics/40/noi.py): cuenta issues abiertos a un
#   momento dado (snapshot), no el total histórico.
# - NCI (metrics/35, 40, 43): cuenta issues cerrados dentro de una ventana
#   de tiempo, no el total histórico.
# Esta métrica es la suma de ambos universos sin distinguir estado: todos
# los issues que existen en el repo, punto.
#
# Por persona: cuántos issues abrió cada autor (sin distinguir si están
# abiertos o cerrados). Requiere paginar por los nodos en vez de pedir solo
# `totalCount`, así que el fetch es más costoso que una consulta agregada.
#
# fetch() trae TODOS los issues (paginado completo, sin filtro), y el
# filtro por [fecha_inicio, fecha_fin] se aplica recién en por_producto/
# por_persona sobre createdAt — mismo criterio que nci.py.

_QUERY = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        author { login }
        createdAt
      }
    }
  }
}
"""


class TotalIssues(GitHubMetric):
    """
    Número Total de Issues (abiertos + cerrados, sin distinguir estado).
    Por producto: total del repo. Por persona: issues abiertos por autor.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.issues: list[dict] = []  # [{author, created_at}]

    def fetch(self, **kwargs):
        issues = []
        cursor, page = None, 0
        while True:
            page += 1
            data = self._graphql(_QUERY, {"owner": self.org, "name": self.repo, "after": cursor})
            conexion = data["data"]["repository"]["issues"]
            for node in conexion["nodes"]:
                author_node = node.get("author") or {}
                issues.append({
                    "author": author_node.get("login") or "desconocido",
                    "created_at": datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00")),
                })
            print(f"  ...issues página {page} ({len(issues)} acumulados)", end="\r")
            if not conexion["pageInfo"]["hasNextPage"]:
                break
            cursor = conexion["pageInfo"]["endCursor"]
        print()
        self.issues = issues

    def _en_periodo(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[dict]:
        return [i for i in self.issues if fecha_inicio <= i["created_at"] <= fecha_fin]

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return len(self._en_periodo(fecha_inicio, fecha_fin))

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        contador = Counter(i["author"] for i in self._en_periodo(fecha_inicio, fecha_fin))
        return dict(sorted(contador.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        print(f"Consultando issues totales de {self.org}/{self.repo}...")
        self.fetch()

        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"\n{'Colaborador':<30} Issues abiertos")
            print("-" * 45)
            for login, cantidad in resultado.items():
                print(f"{login:<30} {cantidad}")
        else:
            total = self.por_producto(fecha_inicio, fecha_fin)
            print(f"Número Total de Issues: {total}")
