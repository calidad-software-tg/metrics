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
              parents { totalCount }
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
    """ANMCC: promedio de archivos modificados por commit en la ventana.

    Cambios respecto de la versión original:
    - Se descartan los commits de merge y los commits de los que GitHub no informa los
      archivos (changedFilesIfAvailable = None): antes entraban como 0 y bajaban el promedio.
    - A nivel producto se descartan los commits de bots (los bots de release de next.js
      son entre el 8 % y el 19 % de los commits desde 2023 y tocan unos 20 archivos cada
      uno), igual que por persona.
    - None (no observable) cuando no hay commits en la ventana, en vez de 0.
    - fetch acepta max_commits (antes run_versiones.py pasaba --max-commits y se ignoraba).

    El runner local (run_versiones_local.py) carga self.commits desde git con
    --no-merges y la lista de archivos completa.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.commits: list[dict] = []

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, max_commits: int | None = None):
        commits = []
        cursor = None
        since = fecha_inicio.isoformat()
        until = fecha_fin.isoformat()

        while max_commits is None or len(commits) < max_commits:
            data = self._graphql(_GRAPHQL_QUERY, {
                "owner": self.org,
                "name": self.repo,
                "after": cursor,
                "since": since,
                "until": until,
            })
            history = data["data"]["repository"]["defaultBranchRef"]["target"]["history"]

            for node in history["nodes"]:
                if (node.get("parents") or {}).get("totalCount", 1) > 1:
                    continue  # merge
                if node.get("changedFilesIfAvailable") is None:
                    continue  # GitHub no informa los archivos: no observable
                author_node = node.get("author") or {}
                user = author_node.get("user") or {}
                commits.append({
                    "oid": node["oid"],
                    "files_count": node["changedFilesIfAvailable"],
                    "author": user.get("login") or author_node.get("name") or "desconocido",
                })

            if not history["pageInfo"]["hasNextPage"]:
                break
            cursor = history["pageInfo"]["endCursor"]

        self.commits = commits if max_commits is None else commits[:max_commits]

    def _humanos(self) -> list[dict]:
        return [c for c in self.commits if not self._es_bot(c["author"])]

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float | None:
        commits = self._humanos()
        if not commits:
            return None  # ventana sin commits: no observable
        return round(sum(c["files_count"] for c in commits) / len(commits), 2)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        by_author: dict[str, list[int]] = {}
        for commit in self._humanos():
            by_author.setdefault(commit["author"], []).append(commit["files_count"])
        result = {login: round(sum(c) / len(c), 2) for login, c in by_author.items()}
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto"):
        self.fetch(fecha_inicio, fecha_fin)
        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"{'Colaborador':<30} ANMCC")
            print("-" * 40)
            for login, valor in resultado.items():
                print(f"{login:<30} {valor}")
        else:
            print(f"ANMCC: {self.por_producto(fecha_inicio, fecha_fin)} archivos por commit")
