import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

_QUERY_ISSUES = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 50, after: $after, orderBy: {field: UPDATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        author { login }
        createdAt
        updatedAt
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
    pullRequests(first: 50, after: $after, orderBy: {field: UPDATED_AT, direction: DESC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        author { login }
        createdAt
        updatedAt
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


def calcular_exprev(metadata_usuario_repo: dict) -> int:
    """
    Calcula la Experiencia en Revisión de Código (EXPRev).
    Cuantifica la influencia y participación del desarrollador basada en
    actividades de revisión y discusión técnica.

    metadata_usuario_repo: Diccionario con los conteos de actividades del
                           usuario en el repositorio analizado.
    """
    # Se extraen los conteos de las dimensiones especificadas en la literatura
    # (i) Actividad en Issues
    issues_abiertos = metadata_usuario_repo.get("issues_opened", 0)
    issues_cerrados = metadata_usuario_repo.get("issues_closed", 0)

    # (ii) Actividad en Pull Requests
    prs_abiertas = metadata_usuario_repo.get("pull_requests_opened", 0)
    prs_cerradas = metadata_usuario_repo.get("pull_requests_closed", 0)

    # (iii) Actividad de Discusión (Comentarios)
    comentarios_issues = metadata_usuario_repo.get("issue_comments", 0)
    comentarios_prs = metadata_usuario_repo.get("pull_request_comments", 0)

    # La métrica es la suma agregada de estas interacciones técnicas y sociales
    exprev_total = (issues_abiertos + issues_cerrados +
                    prs_abiertas + prs_cerradas +
                    comentarios_issues + comentarios_prs)

    return exprev_total


class ReviewExperience(GitHubMetric):
    """
    EXPRev (Experiencia en Revisión de Código).
    Cuantifica la experiencia de un desarrollador en actividades de revisión
    de código y discusión técnica: apertura/cierre de issues y PRs, y
    comentarios en ambos. Solo aplica por persona.
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
            fuera_de_ventana = False
            for node in conexion["nodes"]:
                # Orden UPDATED_AT DESC: en cuanto un nodo quede antes de
                # fecha_inicio, todos los siguientes también (updatedAt nunca
                # es anterior a createdAt ni a closedAt, así que no se pierde
                # ningún evento de apertura ni de cierre dentro de la ventana).
                updated = datetime.fromisoformat(node["updatedAt"].replace("Z", "+00:00"))
                if updated < fecha_inicio:
                    fuera_de_ventana = True
                    break

                created = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
                if fecha_inicio <= created <= fecha_fin:
                    login = (node.get("author") or {}).get("login", "desconocido")
                    self.eventos.append({"tipo": "issues_opened", "login": login, "fecha": created})

                if node.get("closedAt"):
                    closed = datetime.fromisoformat(node["closedAt"].replace("Z", "+00:00"))
                    if fecha_inicio <= closed <= fecha_fin:
                        login = self._closer_login(node) or "desconocido"
                        self.eventos.append({"tipo": "issues_closed", "login": login, "fecha": closed})
            if fuera_de_ventana or not conexion["pageInfo"]["hasNextPage"]:
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
            fuera_de_ventana = False
            for node in conexion["nodes"]:
                updated = datetime.fromisoformat(node["updatedAt"].replace("Z", "+00:00"))
                if updated < fecha_inicio:
                    fuera_de_ventana = True
                    break

                created = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
                if fecha_inicio <= created <= fecha_fin:
                    login = (node.get("author") or {}).get("login", "desconocido")
                    self.eventos.append({"tipo": "pull_requests_opened", "login": login, "fecha": created})

                if node.get("closedAt"):
                    closed = datetime.fromisoformat(node["closedAt"].replace("Z", "+00:00"))
                    if fecha_inicio <= closed <= fecha_fin:
                        login = self._closer_login(node, es_pr=True) or "desconocido"
                        self.eventos.append({"tipo": "pull_requests_closed", "login": login, "fecha": closed})
            if fuera_de_ventana or not conexion["pageInfo"]["hasNextPage"]:
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
        raise NotImplementedError("EXPRev es una métrica por persona, no aplica por producto.")

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        metadata_por_usuario: dict[str, dict] = {}
        for e in self.eventos:
            d = metadata_por_usuario.setdefault(e["login"], {})
            d[e["tipo"]] = d.get(e["tipo"], 0) + 1

        resultado = {
            login: calcular_exprev(metadata)
            for login, metadata in metadata_por_usuario.items()
        }
        return dict(sorted(resultado.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona", **kwargs):
        if por == "producto":
            print("EXPRev no aplica por producto: es una métrica por persona.")
            return
        self.fetch(fecha_inicio, fecha_fin)
        resultado = self.por_persona(fecha_inicio, fecha_fin)
        if not resultado:
            print("No se encontraron eventos en el período.")
            return
        print(f"\n{'Colaborador':<30} EXPRev")
        print("-" * 45)
        for login, exprev in resultado.items():
            print(f"{login:<30} {exprev}")
