import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

# ATENCIÓN — MÉTRICA SIN CONSIGNA ASIGNADA TODAVÍA:
# Proviene del punto 4 del Notion "Forks, Issues y Pull Requests"
# (Número de forks).
#
# Nota sobre "por persona": un fork lo crea una cuenta de GitHub que no
# necesariamente es colaboradora del repo analizado (puede ser cualquier
# usuario externo). Igual se expone el desglose por dueño del fork para
# consistencia con el resto del catálogo, aunque en la práctica casi
# siempre da 1 fork por cuenta (GitHub no permite que la misma cuenta
# bifurque el mismo repo dos veces) — la señal es principalmente "quiénes
# forkearon", no "quién forkeó más".

_QUERY = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    forks(first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        owner { login }
      }
    }
  }
}
"""


class NumberOfForks(GitHubMetric):
    """
    Número de Forks — cantidad de veces que el repositorio fue bifurcado.
    Por producto: total. Por persona: desglose por cuenta que forkeó
    (ver nota arriba sobre su utilidad limitada).
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.owners: list[str] = []

    def fetch(self, **kwargs):
        owners = []
        cursor, page = None, 0
        while True:
            page += 1
            data = self._graphql(_QUERY, {"owner": self.org, "name": self.repo, "after": cursor})
            conexion = data["data"]["repository"]["forks"]
            for node in conexion["nodes"]:
                owner_node = node.get("owner") or {}
                owners.append(owner_node.get("login") or "desconocido")
            print(f"  ...forks página {page} ({len(owners)} acumulados)", end="\r")
            if not conexion["pageInfo"]["hasNextPage"]:
                break
            cursor = conexion["pageInfo"]["endCursor"]
        print()
        self.owners = owners

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return len(self.owners)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        contador = Counter(self.owners)
        return dict(sorted(contador.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        print(f"Consultando forks de {self.org}/{self.repo}...")
        self.fetch()

        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            if not resultado:
                print("No se encontraron forks.")
                return
            print(f"\n{'Cuenta':<30} Forks")
            print("-" * 40)
            for login, cantidad in resultado.items():
                print(f"{login:<30} {cantidad}")
        else:
            total = self.por_producto(fecha_inicio, fecha_fin)
            print(f"Número de Forks: {total}")
