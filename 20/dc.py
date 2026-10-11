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
        closedAt
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
        closedAt
        mergedAt
      }
    }
  }
}
"""


def _fecha(raw):
    return datetime.fromisoformat(raw.replace("Z", "+00:00")) if raw else None


class SocialContribution(GitHubMetric):
    """
    Social Contributions (SC) — Falcão et al. (2020).
    Suma de: issues abiertos + issues propios cerrados +
             PRs abiertas + PRs cerradas sin merge + PRs mergeadas.
    Solo aplica por persona.

    Un issue o PR abierto en la ventana cuenta como cerrado o mergeado solo si se cerró
    o mergeó antes del cierre de la ventana. Antes se usaba el estado de hoy (state), así
    que en las ventanas viejas casi todo aparecía cerrado: SC = 2 en el 82,6 % de las filas
    de 2020, contra el 40,4 % en 2026, una tendencia temporal que no existía.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self._issues: list[dict] = []
        self._prs: list[dict] = []

    def _paginate(self, query: str, key: str, label: str,
                  fecha_inicio: datetime, fecha_fin: datetime) -> list[dict]:
        cursor, results, page = None, [], 0
        while True:
            page += 1
            data = self._graphql(query, {"owner": self.org, "repo": self.repo, "cursor": cursor})
            nodes = data["data"]["repository"][key]["nodes"]
            page_info = data["data"]["repository"][key]["pageInfo"]
            print(f"  ...{label} página {page} ({len(results)} acumulados)", end="\r")
            for node in nodes:
                created = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
                if not (fecha_inicio <= created <= fecha_fin):
                    continue
                login = (node.get("author") or {}).get("login", "desconocido")
                results.append({"author": login, "state": node["state"], "created": created,
                                "closed": _fecha(node.get("closedAt")),
                                "merged": _fecha(node.get("mergedAt"))})
            if not page_info["hasNextPage"]:
                break
            cursor = page_info["endCursor"]
        print()
        return results

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, **kwargs):
        print("Obteniendo issues...")
        self._issues = self._paginate(_QUERY_ISSUES, "issues", "issues", fecha_inicio, fecha_fin)
        print(f"Issues en período: {len(self._issues)}")
        print("Obteniendo pull requests...")
        self._prs = self._paginate(_QUERY_PRS, "pullRequests", "PRs", fecha_inicio, fecha_fin)
        print(f"PRs en período: {len(self._prs)}")

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
            if self._es_bot(i["author"]):
                continue
            d = get(i["author"])
            d["issues_opened"] += 1
            if i["closed"] and i["closed"] <= fecha_fin:
                d["issues_opened_closed"] += 1

        for p in self._prs:
            if self._es_bot(p["author"]):
                continue
            d = get(p["author"])
            d["prs_opened"] += 1
            if p.get("merged") and p["merged"] <= fecha_fin:
                d["prs_opened_merged"] += 1
            elif p["closed"] and p["closed"] <= fecha_fin:
                d["prs_opened_closed"] += 1

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
