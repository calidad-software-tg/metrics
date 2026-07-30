import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

_DOC_KEYWORDS = {'doc', 'docs', 'documentation', 'documentación'}

_QUERY_SIN_ACTOR = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    issues(first: 100, after: $cursor, states: [CLOSED]) {
      pageInfo { hasNextPage endCursor }
      nodes {
        labels(first: 10) { nodes { name } }
        createdAt
        closedAt
      }
    }
  }
}
"""

_QUERY_CON_ACTOR = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    issues(first: 25, after: $cursor, states: [CLOSED]) {
      pageInfo { hasNextPage endCursor }
      nodes {
        labels(first: 10) { nodes { name } }
        createdAt
        closedAt
        timelineItems(last: 1, itemTypes: [CLOSED_EVENT]) {
          nodes {
            ... on ClosedEvent { actor { login } }
          }
        }
      }
    }
  }
}
"""


def _is_doc(labels: list[str]) -> bool:
    return any(any(kw in label.lower() for kw in _DOC_KEYWORDS) for label in labels)


class DocIssueSurvival(GitHubMetric):

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.issues: list[dict] = []  # [{days, actor}]

    def fetch(self, con_actor: bool = False, **kwargs):
        query = _QUERY_CON_ACTOR if con_actor else _QUERY_SIN_ACTOR
        page_size_label = "25" if con_actor else "100"
        cursor = None
        issues = []
        page = 0

        while True:
            page += 1
            data = self._graphql(query, {"owner": self.org, "repo": self.repo, "cursor": cursor})
            repo_data = data["data"]["repository"]["issues"]
            nodes = repo_data["nodes"]
            print(f"  ...página {page} ({len(issues)} doc-issues acumulados)", end="\r")

            for node in nodes:
                labels = [l["name"] for l in node["labels"]["nodes"]]
                if not _is_doc(labels):
                    continue
                created = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
                closed  = datetime.fromisoformat(node["closedAt"].replace("Z", "+00:00"))
                days = (closed - created).days
                actor = "desconocido"
                if con_actor:
                    tl = node.get("timelineItems", {}).get("nodes", [])
                    if tl:
                        actor = (tl[0].get("actor") or {}).get("login", "desconocido")
                issues.append({"days": days, "actor": actor})

            if not repo_data["pageInfo"]["hasNextPage"]:
                break
            cursor = repo_data["pageInfo"]["endCursor"]

        print()
        self.issues = issues
        print(f"Issues de documentación cerrados: {len(issues)}")

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        if not self.issues:
            return 0.0
        return round(sum(i["days"] for i in self.issues) / len(self.issues), 2)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        by_actor: dict[str, list[int]] = {}
        for i in self.issues:
            by_actor.setdefault(i["actor"], []).append(i["days"])
        result = {
            login: round(sum(days) / len(days), 2)
            for login, days in by_actor.items()
        }
        return dict(sorted(result.items(), key=lambda x: x[1]))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        if por == "persona":
            self.fetch(con_actor=True)
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            if not resultado:
                print("No se encontraron issues de documentación cerrados.")
                return
            print(f"{'Colaborador':<30} DIS (días)")
            print("-" * 45)
            for login, days in resultado.items():
                print(f"{login:<30} {days}")
        else:
            self.fetch(con_actor=False)
            avg = self.por_producto(fecha_inicio, fecha_fin)
            if avg == 0.0:
                print("No se encontraron issues de documentación cerrados.")
                return
            print(f"DIS (Doc Issue Survival): {avg} días promedio")