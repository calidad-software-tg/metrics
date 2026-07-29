import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_metric import GitHubMetric

_GRAPHQL_QUERY = """
query($owner: String!, $name: String!, $after: String, $since: GitTimestamp, $until: GitTimestamp) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $after, since: $since, until: $until) {
            pageInfo { hasNextPage endCursor }
            nodes {
              oid
              changedFilesIfAvailable
              author { user { login } name }
            }
          }
        }
      }
    }
  }
}
"""


class AverageNumberOfModifiedComponentsPerCommit(GitHubMetric):

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.commits: list[dict] = []

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime):
        commits = []
        cursor = None
        since = fecha_inicio.isoformat()
        until = fecha_fin.isoformat()

        while True:
            data = self._graphql(_GRAPHQL_QUERY, {
                "owner": self.org,
                "name": self.repo,
                "after": cursor,
                "since": since,
                "until": until,
            })
            history = data["data"]["repository"]["defaultBranchRef"]["target"]["history"]

            for node in history["nodes"]:
                author_node = node.get("author") or {}
                user = author_node.get("user") or {}
                commits.append({
                    "oid": node["oid"],
                    "files_count": node.get("changedFilesIfAvailable") or 0,
                    "author": user.get("login") or author_node.get("name") or "desconocido",
                })

            if not history["pageInfo"]["hasNextPage"]:
                break
            cursor = history["pageInfo"]["endCursor"]
            print(f"  ...{len(commits)} commits descargados", end="\r")

        self.commits = commits

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        if not self.commits:
            return 0.0
        total_files = sum(c["files_count"] for c in self.commits)
        return round(total_files / len(self.commits), 2)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        by_author: dict[str, list[int]] = {}
        for commit in self.commits:
            login = commit["author"]
            by_author.setdefault(login, []).append(commit["files_count"])

        result = {
            login: round(sum(counts) / len(counts), 2)
            for login, counts in by_author.items()
        }
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto"):
        print(f"Descargando commits de {self.org}/{self.repo}...")
        self.fetch(fecha_inicio, fecha_fin)
        print(f"Commits descargados: {len(self.commits)}\n")

        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"{'Colaborador':<30} ANMCC")
            print("-" * 40)
            for login, anmcc in resultado.items():
                print(f"{login:<30} {anmcc}")
        else:
            anmcc = self.por_producto(fecha_inicio, fecha_fin)
            print(f"ANMCC (Avg Modified Components per Commit): {anmcc}")