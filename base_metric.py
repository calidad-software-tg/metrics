import sys
import requests

_BASE_URL = "https://api.github.com"


class GitHubMetric:

    def __init__(self, token: str, org: str, repo: str):
        self.token = token
        self.org = org
        self.repo = repo

    def _rest(self, path: str, params: dict = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        resp = requests.get(f"{_BASE_URL}{path}", headers=headers, params=params or {})
        if not resp.ok:
            print(f"GitHub API error {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)
        return resp.json()

    def _graphql(self, query: str, variables: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": variables},
            headers=headers,
        )
        if not resp.ok:
            print(f"GitHub API error {resp.status_code}: {resp.text}", file=sys.stderr)
            sys.exit(1)
        data = resp.json()
        if "errors" in data:
            print(f"GraphQL error: {data['errors']}", file=sys.stderr)
            sys.exit(1)
        return data

    def _resolve_ref(self, fecha_fin) -> str:
        """SHA del último commit de la rama default con fecha <= fecha_fin.

        Para métricas que leen contenido del repo (árbol de archivos,
        blobs): usar este ref en vez de "HEAD" hace que reflejen el estado
        del repo a una fecha dada, no siempre el estado actual. Si no hay
        ningún commit antes de fecha_fin (fecha anterior a la creación del
        repo), cae de vuelta a "HEAD".
        """
        commits = self._rest(
            f"/repos/{self.org}/{self.repo}/commits",
            {"until": fecha_fin.isoformat(), "per_page": 1},
        )
        return commits[0]["sha"] if commits else "HEAD"

    def fetch(self, **kwargs):
        raise NotImplementedError

    def por_producto(self, fecha_inicio, fecha_fin):
        raise NotImplementedError

    def por_persona(self, fecha_inicio, fecha_fin):
        raise NotImplementedError

    def run(self, fecha_inicio, fecha_fin, por: str = "producto"):
        raise NotImplementedError