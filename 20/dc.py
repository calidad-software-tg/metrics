import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

_QUERY_ISSUES = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    issues(first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        author { login }
        state
        createdAt
      }
    }
  }
}
"""

_QUERY_PRS = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequests(first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        author { login }
        state
        createdAt
      }
    }
  }
}
"""


class SocialContribution(GitHubMetric):
    """
    Social Contributions (SC) — Falcão et al. (2020).
    Suma de: issues abiertos + issues propios cerrados +
             PRs abiertas + PRs cerradas sin merge + PRs mergeadas.
    Solo aplica por persona.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self._issues: list[dict] = []  # filtradas al período vigente
        self._prs: list[dict] = []     # filtradas al período vigente
        self._all_issues: list[dict] | None = None  # caché: todo el repo, sin filtrar
        self._all_prs: list[dict] | None = None      # caché: todo el repo, sin filtrar

    def _fetch_all(self, query: str, key: str, label: str) -> list[dict]:
        """Baja TODOS los nodos (issues o PRs) del repo, sin filtro de fecha.

        BUG DE PERFORMANCE CORREGIDO: antes esto se llamaba una vez por
        período con un filtro de fecha aplicado recién adentro del loop
        (`if not (fecha_inicio <= created <= fecha_fin): continue`), sin
        cortar la paginación ni cachear nada -- para un análisis de 66
        períodos, eso significaba recorrer el historial COMPLETO de issues y
        de PRs 66 veces cada uno (con ~1.500 issues y ~20.000 PRs en un repo
        grande, del orden de miles de requests de más). Ahora se baja una
        sola vez por instancia y fetch() filtra por fecha sobre este caché.
        """
        cursor, results, page = None, [], 0
        while True:
            page += 1
            data = self._graphql(query, {"owner": self.org, "repo": self.repo, "cursor": cursor})
            nodes = data["data"]["repository"][key]["nodes"]
            page_info = data["data"]["repository"][key]["pageInfo"]
            print(f"  ...{label} página {page} ({len(results)} acumulados)", end="\r")
            for node in nodes:
                results.append({
                    "author": (node.get("author") or {}).get("login", "desconocido"),
                    "state": node["state"],
                    "created_at": datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00")),
                })
            if not page_info["hasNextPage"]:
                break
            cursor = page_info["endCursor"]
        print()
        return results

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, **kwargs):
        if self._all_issues is None:
            print("Obteniendo issues (una sola vez, se cachea)...")
            self._all_issues = self._fetch_all(_QUERY_ISSUES, "issues", "issues")
        if self._all_prs is None:
            print("Obteniendo pull requests (una sola vez, se cachea)...")
            self._all_prs = self._fetch_all(_QUERY_PRS, "pullRequests", "PRs")

        self._issues = [i for i in self._all_issues if fecha_inicio <= i["created_at"] <= fecha_fin]
        self._prs = [p for p in self._all_prs if fecha_inicio <= p["created_at"] <= fecha_fin]
        print(f"Issues en período: {len(self._issues)}  |  PRs en período: {len(self._prs)}")

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError("SC es una métrica por persona, no aplica por producto.")

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, dict]:
        contribs: dict[str, dict] = {}

        def get(login):
            if login not in contribs:
                contribs[login] = {
                    "issues_opened": 0, "issues_opened_closed": 0,
                    "prs_opened": 0, "prs_opened_closed": 0, "prs_opened_merged": 0,
                }
            return contribs[login]

        for i in self._issues:
            d = get(i["author"])
            d["issues_opened"] += 1
            if i["state"] == "CLOSED":
                d["issues_opened_closed"] += 1

        for p in self._prs:
            d = get(p["author"])
            d["prs_opened"] += 1
            if p["state"] == "CLOSED":
                d["prs_opened_closed"] += 1
            elif p["state"] == "MERGED":
                d["prs_opened_merged"] += 1

        result = {
            login: {**d, "sc": sum(d.values())}
            for login, d in contribs.items()
        }
        return dict(sorted(result.items(), key=lambda x: x[1]["sc"], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona", **kwargs):
        if por == "producto":
            print("Social Contribution no aplica por producto: es una métrica por persona.")
            return
        self.fetch(fecha_inicio, fecha_fin)
        resultado = self.por_persona(fecha_inicio, fecha_fin)
        if not resultado:
            print("No se encontraron contribuciones en el período.")
            return
        print(f"\n{'Colaborador':<25} {'Issues':>7} {'I.Cerr':>7} {'PRs':>6} {'PR.Cerr':>8} {'PR.Merge':>9} {'SC':>6}")
        print("-" * 68)
        for login, d in resultado.items():
            print(f"{login:<25} {d['issues_opened']:>7} {d['issues_opened_closed']:>7} "
                  f"{d['prs_opened']:>6} {d['prs_opened_closed']:>8} {d['prs_opened_merged']:>9} {d['sc']:>6}")
