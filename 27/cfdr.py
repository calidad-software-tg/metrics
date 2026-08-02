import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

_QUERY_ISSUES = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 50, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        author { login }
        createdAt
        labels(first: 20) { nodes { name } }
      }
    }
  }
}
"""


def calcular_customer_defects_and_regressions(metadata_issues: list[dict], lista_core_team: set) -> int:
    """
    Calcula los defectos y regresiones encontrados por el cliente.

    Esta métrica de Producto y Proceso mide la calidad del software desde la
    perspectiva del usuario final. Un valor alto sugiere una baja eficiencia
    en la eliminación de defectos (DRE) previa al lanzamiento.

    metadata_issues: Lista de diccionarios, cada uno con 'user_login',
        'labels' (lista de strings) y 'created_at'.
    lista_core_team: Set de logins identificados como equipo principal
        o contribuyentes frecuentes (Surgical Team).

    Retorna: suma de incidentes de tipo bug o regresión reportados por no-miembros.
    """
    # Etiquetas identificadas en la literatura para errores y regresiones
    # de post-lanzamiento.
    keywords_error = {"bug", "defect", "error", "fault", "flaw", "regression"}

    conteo_customer_defects = 0

    for issue in metadata_issues:
        reportero = issue.get("user_login")
        # Normalizamos etiquetas para una búsqueda robusta
        etiquetas = {et.lower() for et in issue.get("labels", [])}

        # 1. Criterio de tipo: ¿Es un error o una regresión?
        es_defecto = any(key in etiquetas for key in keywords_error)

        # 2. Criterio de rol: ¿El informante es externo (cliente)?
        # Se excluyen reportes de desarrolladores que eventualmente fueron
        # parte del equipo para evitar sesgos de "internal testing".
        es_externo = reportero not in lista_core_team

        if es_defecto and es_externo:
            conteo_customer_defects += 1

    return conteo_customer_defects


class CustomerFoundDefectsAndRegressions(GitHubMetric):
    """
    Customer-Found Defects and Regressions (CFDR).
    Cuantifica el volumen de errores y regresiones reportados por usuarios
    externos al equipo principal tras una liberación. Solo aplica por producto:
    el algoritmo agrega incidentes a nivel repositorio, no por desarrollador
    (los desarrolladores son justamente el grupo que se excluye del conteo).
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.issues: list[dict] = []  # {user_login, labels, created_at}
        self.core_team: set = set()

    def fetch(self, core_team_size: int = 10):
        print("Obteniendo equipo principal (core team)...")
        contributors = self._rest(
            f"/repos/{self.org}/{self.repo}/contributors",
            {"per_page": core_team_size},
        )
        self.core_team = {c["login"] for c in contributors[:core_team_size]}
        print(f"Core team ({len(self.core_team)}): {sorted(self.core_team)}")

        print("Obteniendo issues...")
        issues, cursor, page = [], None, 0
        while True:
            page += 1
            data = self._graphql(_QUERY_ISSUES, {"owner": self.org, "name": self.repo, "after": cursor})
            conexion = data["data"]["repository"]["issues"]
            print(f"  ...issues página {page} ({len(issues)} acumulados)", end="\r")
            for node in conexion["nodes"]:
                created = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
                login = (node.get("author") or {}).get("login", "desconocido")
                labels = [l["name"] for l in node.get("labels", {}).get("nodes", [])]
                issues.append({"user_login": login, "labels": labels, "created_at": created})
            if not conexion["pageInfo"]["hasNextPage"]:
                break
            cursor = conexion["pageInfo"]["endCursor"]
        print()
        self.issues = issues

    def _issues_en_periodo(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[dict]:
        return [i for i in self.issues if fecha_inicio <= i["created_at"] <= fecha_fin]

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        issues_periodo = self._issues_en_periodo(fecha_inicio, fecha_fin)
        return calcular_customer_defects_and_regressions(issues_periodo, self.core_team)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError(
            "CFDR es una métrica por producto/proceso, no aplica por persona: "
            "cuantifica incidentes reportados por usuarios externos al equipo, "
            "no atribuibles a un desarrollador del proyecto."
        )

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto",
            core_team_size: int = 10, **kwargs):
        if por == "persona":
            print("CFDR no aplica por persona: es una métrica por producto/proceso.")
            return
        self.fetch(core_team_size=core_team_size)
        issues_periodo = self._issues_en_periodo(fecha_inicio, fecha_fin)
        if not issues_periodo:
            print("No se encontraron issues en el período.")
            return

        keywords_error = {"bug", "defect", "error", "fault", "flaw", "regression"}
        detalle = [
            i for i in issues_periodo
            if any(k in {et.lower() for et in i["labels"]} for k in keywords_error)
            and i["user_login"] not in self.core_team
        ]

        if detalle:
            print(f"\n{'Reportero':<25} {'Etiquetas':<30} Fecha")
            print("-" * 70)
            for i in detalle:
                print(f"{i['user_login']:<25} {', '.join(i['labels']):<30} {i['created_at'].date()}")

        cfdr = calcular_customer_defects_and_regressions(issues_periodo, self.core_team)
        print("-" * 70)
        print(f"CFDR (Customer-Found Defects and Regressions): {cfdr}")
