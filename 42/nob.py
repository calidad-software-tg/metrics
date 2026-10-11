import math
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

_QUERY_BRANCHES = """
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    refs(refPrefix: "refs/heads/") {
      totalCount
    }
  }
}
"""

_QUERY_PRS = """
query($owner: String!, $repo: String!, $after: String) {
  repository(owner: $owner, name: $repo) {
    pullRequests(first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        createdAt
        closedAt
        isCrossRepository
        headRefName
        author { login }
      }
    }
  }
}
"""


def _fecha(raw):
    return datetime.fromisoformat(raw.replace("Z", "+00:00")) if raw else None


class NumberOfBranches(GitHubMetric):
    """
    Number of Branches (NOB) — Jarczyk et al. (2014): branches de desarrollo activas.

    La versión original guardaba la cantidad de branches que existen HOY (2.706 en
    next.js) en todas las ventanas, así que no variaba entre releases. Además, la consigna
    pide branches "activas" y se contaban todas, incluidas las obsoletas. Git no guarda la
    historia de las branches (las que se borran al mergearse no dejan rastro) y la API de
    eventos de GitHub solo guarda 90 días, así que se aproxima con los pull requests:

        NOB de una ventana = branches distintas del repositorio principal (no de forks) con
        un PR abierto al cierre de la ventana (creado antes y no cerrado todavía).

    Solo cuenta branches que tuvieron un PR. Se descartan los PR de bots. El conteo de
    branches de hoy queda en value_extra como referencia. Métrica de Producto/Proceso: no
    aplica por persona.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self._branches_count: int = 0
        self._prs: list[dict] = []

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, **kwargs):
        print("Obteniendo branches de hoy...")
        data = self._graphql(_QUERY_BRANCHES, {"owner": self.org, "repo": self.repo})
        self._branches_count = data["data"]["repository"]["refs"]["totalCount"]
        print(f"Branches existentes hoy: {self._branches_count}")

        print("Obteniendo pull requests (branch de origen y fechas)...")
        prs, cursor, page = [], None, 0
        while True:
            page += 1
            data = self._graphql(_QUERY_PRS, {"owner": self.org, "repo": self.repo, "after": cursor})
            con = data["data"]["repository"]["pullRequests"]
            for n in con["nodes"]:
                prs.append({
                    "created": _fecha(n["createdAt"]),
                    "closed": _fecha(n.get("closedAt")),
                    "fork": bool(n.get("isCrossRepository")),
                    "branch": n.get("headRefName"),
                    "author": (n.get("author") or {}).get("login"),
                })
            print(f"  ...página {page} ({len(prs)} PRs)", end="\r")
            if not con["pageInfo"]["hasNextPage"]:
                break
            cursor = con["pageInfo"]["endCursor"]
        print()
        self._prs = prs

    def calcular_nob(self, metadata_repositorio: dict) -> int:
        lista_ramas = metadata_repositorio.get("branches", [])
        nob_total = len(lista_ramas) if isinstance(lista_ramas, list) else 0
        if nob_total == 0:
            nob_total = metadata_repositorio.get("branches_count", 0)
        return nob_total

    def normalizar_nob_jarczyk(self, nob_total: int) -> float:
        """
        Transformación logarítmica propuesta por Jarczyk et al. (2014)
        para mitigar el sesgo en distribuciones de ley de potencia.
        Referencia: x' = log10(x + 10).
        """
        return round(math.log10(nob_total + 10), 4)

    def _activas(self, fecha_fin: datetime) -> tuple[int, int]:
        """(branches del repo principal con PR abierto, PR abiertos en total) al cierre."""
        abiertos = [p for p in self._prs
                    if p["created"] <= fecha_fin and (p["closed"] is None or p["closed"] > fecha_fin)
                    and not self._es_bot(p["author"])]
        branches = {p["branch"] for p in abiertos if not p["fork"] and p["branch"]}
        return len(branches), len(abiertos)

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, dict]:
        activas, prs_abiertos = self._activas(fecha_fin)
        return {
            self.repo: {
                "nob": activas,
                "nob_normalizado": self.normalizar_nob_jarczyk(activas),
                "prs_abiertos": prs_abiertos,
                "branches_hoy": self.calcular_nob({"branches_count": self._branches_count}),
                "criterio": "branches del repo principal con PR abierto al cierre de la ventana",
            }
        }

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        if por == "persona":
            print("Number of Branches no aplica por persona: es una métrica por producto.")
            return
        self.fetch(fecha_inicio, fecha_fin)
        for repo, d in self.por_producto(fecha_inicio, fecha_fin).items():
            print(f"\nRepositorio: {repo}")
            print(f"Branches activas al {fecha_fin.date()} (con PR abierto): {d['nob']}")
            print(f"NOB normalizado (Jarczyk log10)  : {d['nob_normalizado']}")
            print(f"PR abiertos (incluye forks)       : {d['prs_abiertos']}")
            print(f"Branches existentes hoy           : {d['branches_hoy']}")
