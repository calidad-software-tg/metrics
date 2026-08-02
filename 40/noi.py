import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

_QUERY_ISSUES = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        createdAt
        closedAt
      }
    }
  }
}
"""


def calcular_open_issues(metadata_issues: list[dict], fecha_snapshot: datetime = None) -> int:
    """
    Calcula el Number of Open Issues (NOI).

    Mide la acumulación de tareas pendientes en un repositorio. Según
    Jarczyk et al. (2018), el volumen de open issues refleja la capacidad
    del equipo para manejar la carga de trabajo.

    metadata_issues: Lista de diccionarios con 'created_at' y 'closed_at'
        (o None si sigue abierto).
    fecha_snapshot: Punto en el tiempo para el análisis histórico. Si es
        None, usa 'ahora'.

    Retorna: Int, conteo de issues en estado 'abierto' en la fecha del snapshot.
    """
    if fecha_snapshot is None:
        fecha_snapshot = datetime.now()

    total_open = 0

    for issue in metadata_issues:
        fecha_creacion = issue.get("created_at")
        fecha_cierre = issue.get("closed_at")

        # Un issue está abierto en el snapshot si:
        # 1. Se creó antes o el mismo día del snapshot.
        # 2. No se ha cerrado aún (None) O se cerró después del snapshot.
        if fecha_creacion and fecha_creacion <= fecha_snapshot:
            if fecha_cierre is None or fecha_cierre > fecha_snapshot:
                total_open += 1

    return total_open


class NumberOfOpenIssues(GitHubMetric):
    """
    NOI (Number of Open Issues).
    Acumulación de tareas pendientes en el repositorio a un momento dado
    (snapshot). Solo aplica por producto.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.issues: list[dict] = []  # {created_at, closed_at}

    def fetch(self):
        print("Obteniendo issues...")
        issues, cursor, page = [], None, 0
        while True:
            page += 1
            data = self._graphql(_QUERY_ISSUES, {"owner": self.org, "name": self.repo, "after": cursor})
            conexion = data["data"]["repository"]["issues"]
            print(f"  ...issues página {page} ({len(issues)} acumulados)", end="\r")
            for node in conexion["nodes"]:
                created = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
                closed = datetime.fromisoformat(node["closedAt"].replace("Z", "+00:00")) if node.get("closedAt") else None
                issues.append({"created_at": created, "closed_at": closed})
            if not conexion["pageInfo"]["hasNextPage"]:
                break
            cursor = conexion["pageInfo"]["endCursor"]
        print()
        self.issues = issues

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        # El snapshot se toma al final del período analizado.
        return calcular_open_issues(self.issues, fecha_snapshot=fecha_fin)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError(
            "NOI es una métrica por producto/proceso, no aplica por persona: "
            "el algoritmo no atribuye issues abiertos a un desarrollador."
        )

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        if por == "persona":
            print("NOI no aplica por persona: es una métrica por producto/proceso.")
            return
        self.fetch()
        if not self.issues:
            print("No se encontraron issues.")
            return
        noi = self.por_producto(fecha_inicio, fecha_fin)
        print(f"\nNOI (Number of Open Issues) al {fecha_fin.date()}: {noi}")
