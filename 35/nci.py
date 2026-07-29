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
      nodes { number state closedAt }
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
        number state closedAt
        timelineItems(last: 1, itemTypes: [CLOSED_EVENT]) {
          nodes { ... on ClosedEvent { actor { login } } }
        }
      }
    }
  }
}
"""


class NumberOfClosedIssues(GitHubMetric):

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
                closed_raw = node.get("closedAt")
                timeline_nodes = node.get("timelineItems", {}).get("nodes", []) if con_actor else []
                actor = (timeline_nodes[0].get("actor") or {}) if timeline_nodes else {}
                issues.append({
                    "number": node["number"],
                    "state": node["state"].lower(),
                    "closed_at": datetime.fromisoformat(closed_raw.replace("Z", "+00:00")) if closed_raw else None,
                    "closed_by": actor.get("login"),
                    "pull_request": None,
                })

            if not page["pageInfo"]["hasNextPage"]:
                break
            cursor = page["pageInfo"]["endCursor"]
            print(f"  ...{len(issues)} issues descargados", end="\r")

        self.issues = issues

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return sum(
            1 for issue in self.issues
            if issue["closed_at"] and fecha_inicio <= issue["closed_at"] <= fecha_fin
        )

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        conteo: dict[str, int] = {}
        for issue in self.issues:
            if issue["closed_at"] and fecha_inicio <= issue["closed_at"] <= fecha_fin:
                login = issue["closed_by"] or "desconocido"
                conteo[login] = conteo.get(login, 0) + 1
        return dict(sorted(conteo.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto"):
        print(f"Descargando issues cerrados de {self.org}/{self.repo}...")

        if por == "persona":
            self.fetch(con_actor=True)
            print(f"Issues descargados: {len(self.issues)}\n")
            conteo = self.por_persona(fecha_inicio, fecha_fin)
            print(f"{'Colaborador':<30} NCI")
            print("-" * 40)
            for login, nci in conteo.items():
                print(f"{login:<30} {nci}")
            print("-" * 40)
            print(f"{'Total':<30} {sum(conteo.values())}")
        else:
            self.fetch(con_actor=False)
            print(f"Issues descargados: {len(self.issues)}\n")
            nci = self.por_producto(fecha_inicio, fecha_fin)
            print(f"NCI (Number of Closed Issues): {nci}")