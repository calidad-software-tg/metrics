import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_metric import GitHubMetric

_GRAPHQL_QUERY = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(states: CLOSED, first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes { number createdAt closedAt }
    }
  }
}
"""

_GRAPHQL_QUERY_CON_ACTOR = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(states: CLOSED, first: 25, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number createdAt closedAt
        timelineItems(last: 1, itemTypes: [CLOSED_EVENT]) {
          nodes { ... on ClosedEvent { actor { login } } }
        }
      }
    }
  }
}
"""


class MeanTimeToRepair(GitHubMetric):

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.issues: list[dict] = []

    def fetch(self, con_actor: bool = False):
        issues = []
        cursor = None
        query = _GRAPHQL_QUERY_CON_ACTOR if con_actor else _GRAPHQL_QUERY

        while True:
            data = self._graphql(query, {"owner": self.org, "name": self.repo, "after": cursor})
            page = data["data"]["repository"]["issues"]

            for node in page["nodes"]:
                created_raw = node.get("createdAt")
                closed_raw  = node.get("closedAt")
                timeline_nodes = node.get("timelineItems", {}).get("nodes", []) if con_actor else []
                actor = (timeline_nodes[0].get("actor") or {}) if timeline_nodes else {}
                issues.append({
                    "number":    node["number"],
                    "creacion":  datetime.fromisoformat(created_raw.replace("Z", "+00:00")) if created_raw else None,
                    "cierre":    datetime.fromisoformat(closed_raw.replace("Z", "+00:00"))  if closed_raw  else None,
                    "closed_by": actor.get("login"),
                })

            if not page["pageInfo"]["hasNextPage"]:
                break
            cursor = page["pageInfo"]["endCursor"]
            print(f"  ...{len(issues)} issues descargados", end="\r")

        self.issues = issues

    def _issues_en_rango(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[dict]:
        return [
            i for i in self.issues
            if i["cierre"] and i["creacion"] and fecha_inicio <= i["cierre"] <= fecha_fin
        ]

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        incidencias = self._issues_en_rango(fecha_inicio, fecha_fin)
        if not incidencias:
            return 0.0
        total_segundos = sum((i["cierre"] - i["creacion"]).total_seconds() for i in incidencias)
        return round((total_segundos / len(incidencias)) / 3600, 2)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        by_actor: dict[str, list[float]] = {}
        for i in self._issues_en_rango(fecha_inicio, fecha_fin):
            login = i["closed_by"] or "desconocido"
            horas = (i["cierre"] - i["creacion"]).total_seconds() / 3600
            by_actor.setdefault(login, []).append(horas)

        result = {
            login: round(sum(tiempos) / len(tiempos), 2)
            for login, tiempos in by_actor.items()
        }
        return dict(sorted(result.items(), key=lambda x: x[1]))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto"):
        print(f"Descargando issues cerrados de {self.org}/{self.repo}...")

        if por == "persona":
            self.fetch(con_actor=True)
            print(f"Issues descargados: {len(self.issues)}\n")
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"{'Colaborador':<30} MTTR (horas)")
            print("-" * 46)
            for login, mttr in resultado.items():
                print(f"{login:<30} {mttr}")
        else:
            self.fetch(con_actor=False)
            print(f"Issues descargados: {len(self.issues)}\n")
            mttr = self.por_producto(fecha_inicio, fecha_fin)
            print(f"MTTR (Mean Time to Repair): {mttr} horas")