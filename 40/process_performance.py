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


def calcular_process_performance(metadata_issues: list[dict], dias_umbral: int = 3) -> float:
    """
    Calcula el Rendimiento del Proceso de Desarrollo basado en el cierre de issues.

    Según Jarczyk et al. (2018), el rendimiento del proceso de un "equipo quirúrgico"
    se define por su capacidad de respuesta. El algoritmo utiliza una aproximación
    al análisis de supervivencia para calcular el porcentaje de issues resueltos
    dentro de un umbral específico.

    metadata_issues: Lista de diccionarios con 'created_at' y 'closed_at' (o None
        si sigue abierto).
    dias_umbral: Ventana temporal de evaluación. Jarczyk et al. sugieren:
        - 3 días: mide la "respuesta rápida" a problemas simples.
        - 365 días: mide la capacidad de resolver problemas difíciles/antiguos.

    Retorna: Float (0.0 a 1.0), porcentaje de problemas resueltos dentro del umbral.
    """
    if not metadata_issues:
        return 0.0

    issues_resueltos_a_tiempo = 0
    total_issues_evaluables = len(metadata_issues)

    for issue in metadata_issues:
        fecha_creacion = issue.get("created_at")
        fecha_cierre = issue.get("closed_at")

        if fecha_cierre:
            # Calculamos la duración de vida del issue (Lead Time)
            duracion = (fecha_cierre - fecha_creacion).days

            # Si se resolvió dentro del umbral definido por la investigación
            if duracion <= dias_umbral:
                issues_resueltos_a_tiempo += 1
        else:
            # Si el issue sigue abierto, se considera "superviviente" (censurado)
            # y no suma al rendimiento del proceso en esa ventana temporal.
            continue

    # El rendimiento es la proporción de éxito sobre el total de reportes
    performance_score = issues_resueltos_a_tiempo / total_issues_evaluables

    return round(performance_score, 4)


class DevelopmentProcessPerformance(GitHubMetric):
    """
    Development Process Performance.
    Eficiencia del equipo medida como la probabilidad de cierre de issues
    dentro de ventanas de tiempo críticas (respuesta rápida a 3 días,
    resolución de problemas difíciles a 365 días). Solo aplica por producto.
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

    def _issues_en_periodo(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[dict]:
        return [i for i in self.issues if fecha_inicio <= i["created_at"] <= fecha_fin]

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime, dias_umbral: int = 3) -> float:
        issues_periodo = self._issues_en_periodo(fecha_inicio, fecha_fin)
        return calcular_process_performance(issues_periodo, dias_umbral=dias_umbral)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError(
            "Development Process Performance es una métrica por producto/proceso, "
            "no aplica por persona: el algoritmo evalúa el ciclo de vida de los "
            "issues del repositorio, sin atribución a un desarrollador."
        )

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        if por == "persona":
            print("Development Process Performance no aplica por persona: es una métrica por producto/proceso.")
            return
        self.fetch()
        issues_periodo = self._issues_en_periodo(fecha_inicio, fecha_fin)
        if not issues_periodo:
            print("No se encontraron issues en el período.")
            return

        print(f"\nIssues evaluados en el período: {len(issues_periodo)}")
        score_rapido = calcular_process_performance(issues_periodo, dias_umbral=3)
        score_dificil = calcular_process_performance(issues_periodo, dias_umbral=365)
        print(f"Performance (umbral 3 días, respuesta rápida):   {score_rapido}")
        print(f"Performance (umbral 365 días, problemas difíciles): {score_dificil}")
