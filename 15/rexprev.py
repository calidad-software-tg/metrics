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
        closedAt
        timelineItems(last: 1, itemTypes: [CLOSED_EVENT]) {
          nodes { ... on ClosedEvent { actor { login } } }
        }
      }
    }
  }
}
"""

_QUERY_PRS = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 50, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        author { login }
        createdAt
        closedAt
        mergedAt
        mergedBy { login }
        timelineItems(last: 1, itemTypes: [CLOSED_EVENT]) {
          nodes { ... on ClosedEvent { actor { login } } }
        }
      }
    }
  }
}
"""

_TIPOS_REVISION = [
    "issues_opened", "issues_closed",
    "pull_requests_opened", "pull_requests_closed",
    "issue_comments", "pull_request_comments",
]


def calcular_rexprev(eventos_usuario_repo: list[dict], fecha_actual: datetime) -> float:
    """
    Calcula la Experiencia Reciente en Revisión de Código (REXPRev).
    Pondera las actividades de revisión y discusión técnica por su antigüedad,
    dando más peso a las interacciones más cercanas a la fecha actual.

    eventos_usuario_repo: Lista de diccionarios, donde cada uno representa una
                          interacción (issue, PR o comentario) y contiene su fecha.
    fecha_actual: Objeto datetime que representa el punto de referencia para el cálculo.
    """
    rexprev_total = 0

    for evento in eventos_usuario_repo:
        # Verificamos si el evento pertenece a las categorías de revisión/discusión
        if evento["tipo"] in _TIPOS_REVISION:
            # Calculamos la antigüedad en días
            dias_antiguedad = (fecha_actual - evento["fecha"]).days

            # Aplicamos la ponderación de decaimiento temporal (REXP logic)
            # Se suma 1 para evitar división por cero si el evento es del mismo día
            rexprev_total += 1 / (dias_antiguedad + 1)

    return rexprev_total


class RecentReviewExperience(GitHubMetric):
    """
    REXPRev (Experiencia Reciente en Revisión de Código).
    Versión ponderada temporalmente de EXPRev: atribuye mayor peso a la
    experticia de revisión/discusión más reciente. Solo aplica por persona.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.eventos: list[dict] = []  # {tipo, login, fecha}

    def _closer_login(self, node: dict, es_pr: bool = False) -> str | None:
        timeline = node.get("timelineItems", {}).get("nodes", [])
        if timeline:
            actor = timeline[0].get("actor") or {}
            if actor.get("login"):
                return actor["login"]
        if es_pr and node.get("mergedBy"):
            return node["mergedBy"].get("login")
        return None

    def _paginate_issues(self, fecha_inicio: datetime, fecha_fin: datetime):
        cursor, page = None, 0
        while True:
            page += 1
            data = self._graphql(_QUERY_ISSUES, {"owner": self.org, "name": self.repo, "after": cursor})
            conexion = data["data"]["repository"]["issues"]
            print(f"  ...issues página {page}", end="\r")
            for node in conexion["nodes"]:
                created = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
                if fecha_inicio <= created <= fecha_fin:
                    login = (node.get("author") or {}).get("login", "desconocido")
                    self.eventos.append({"tipo": "issues_opened", "login": login, "fecha": created})

                if node.get("closedAt"):
                    closed = datetime.fromisoformat(node["closedAt"].replace("Z", "+00:00"))
                    if fecha_inicio <= closed <= fecha_fin:
                        login = self._closer_login(node) or "desconocido"
                        self.eventos.append({"tipo": "issues_closed", "login": login, "fecha": closed})
            if not conexion["pageInfo"]["hasNextPage"]:
                break
            cursor = conexion["pageInfo"]["endCursor"]
        print()

    def _paginate_prs(self, fecha_inicio: datetime, fecha_fin: datetime):
        cursor, page = None, 0
        while True:
            page += 1
            data = self._graphql(_QUERY_PRS, {"owner": self.org, "name": self.repo, "after": cursor})
            conexion = data["data"]["repository"]["pullRequests"]
            print(f"  ...PRs página {page}", end="\r")
            for node in conexion["nodes"]:
                created = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
                if fecha_inicio <= created <= fecha_fin:
                    login = (node.get("author") or {}).get("login", "desconocido")
                    self.eventos.append({"tipo": "pull_requests_opened", "login": login, "fecha": created})

                if node.get("closedAt"):
                    closed = datetime.fromisoformat(node["closedAt"].replace("Z", "+00:00"))
                    if fecha_inicio <= closed <= fecha_fin:
                        login = self._closer_login(node, es_pr=True) or "desconocido"
                        self.eventos.append({"tipo": "pull_requests_closed", "login": login, "fecha": closed})
            if not conexion["pageInfo"]["hasNextPage"]:
                break
            cursor = conexion["pageInfo"]["endCursor"]
        print()

    def _fetch_comments(self, path: str, tipo: str, fecha_inicio: datetime, fecha_fin: datetime):
        page = 1
        while True:
            data = self._rest(
                f"/repos/{self.org}/{self.repo}{path}",
                {"per_page": 100, "page": page, "since": fecha_inicio.isoformat()},
            )
            if not data:
                break
            for c in data:
                created = datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
                if created > fecha_fin:
                    continue
                login = (c.get("user") or {}).get("login", "desconocido")
                self.eventos.append({"tipo": tipo, "login": login, "fecha": created})
            print(f"  ...{tipo} página {page}", end="\r")
            if len(data) < 100:
                break
            page += 1
        print()

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime):
        self.eventos = []
        print("Obteniendo issues...")
        self._paginate_issues(fecha_inicio, fecha_fin)
        print("Obteniendo pull requests...")
        self._paginate_prs(fecha_inicio, fecha_fin)
        print("Obteniendo comentarios de issues...")
        self._fetch_comments("/issues/comments", "issue_comments", fecha_inicio, fecha_fin)
        print("Obteniendo comentarios de revisión de PRs...")
        self._fetch_comments("/pulls/comments", "pull_request_comments", fecha_inicio, fecha_fin)
        print(f"Eventos totales en período: {len(self.eventos)}")

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError("REXPRev es una métrica por persona, no aplica por producto.")

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        por_usuario: dict[str, list[dict]] = {}
        for e in self.eventos:
            por_usuario.setdefault(e["login"], []).append(e)

        resultado = {
            login: round(calcular_rexprev(eventos, fecha_fin), 4)
            for login, eventos in por_usuario.items()
        }
        return dict(sorted(resultado.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona", **kwargs):
        if por == "producto":
            print("REXPRev no aplica por producto: es una métrica por persona.")
            return
        self.fetch(fecha_inicio, fecha_fin)
        resultado = self.por_persona(fecha_inicio, fecha_fin)
        if not resultado:
            print("No se encontraron eventos en el período.")
            return
        print(f"\n{'Colaborador':<30} REXPRev")
        print("-" * 45)
        for login, rexprev in resultado.items():
            print(f"{login:<30} {rexprev}")
