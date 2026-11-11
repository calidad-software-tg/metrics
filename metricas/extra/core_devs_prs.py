import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

sys.path.insert(0, str(Path(__file__).resolve().parent))
from commits_per_author import CommitsPerAuthor

# ATENCIÓN — MÉTRICA SIN CONSIGNA ASIGNADA TODAVÍA:
# Combina "Number Of Pull Requests of Core Devs" y "Number of Pull Request
# of Core Developers Rejected" del Notion en una sola clase (mismo fetch de
# PRs, dos agregaciones distintas sobre el mismo resultado).
#
# DIFERENCIA DE FONDO respecto al script original: los scripts de Notion
# reciben `DEVELOPERS` como una lista hardcodeada a mano. Acá `core_devs` es
# un parámetro OPCIONAL:
# - Si se pasa una lista de logins, se usa tal cual (fiel al original).
# - Si no se pasa nada, se auto-selecciona el top-N por CANTIDAD DE COMMITS
#   (reutilizando metrics/Notion/commits_per_author.py), NO por Social
#   Contribution. Se descartó SC como criterio porque su fórmula ya incluye
#   prs_opened/prs_opened_closed/prs_opened_merged como tres de sus cinco
#   componentes: seleccionar "core devs" por SC y después contarles PRs es
#   circular (ver conversación previa). Commits es un criterio independiente
#   de la actividad en PRs que se está midiendo.
#
# NOTA sobre "rechazadas": en GraphQL, un PR fusionado tiene state MERGED,
# no CLOSED — a diferencia de la REST API, donde hay que chequear
# `merged_at is None` sobre PRs con state='closed'. Acá alcanza con filtrar
# state == "CLOSED" directamente, sin ese chequeo adicional.

_QUERY_PRS = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        author { login }
        state
      }
    }
  }
}
"""


class CoreDevsPullRequests(GitHubMetric):
    """
    PRs generadas y PRs rechazadas por el grupo de "core devs".

    core_devs: lista de logins a tratar como desarrolladores principales.
    Si es None, se auto-selecciona vía top_n por cantidad de commits.
    top_n: cuántos autores tomar si core_devs no se especifica (default 5).
    """

    def __init__(self, token: str, org: str, repo: str,
                 core_devs: list[str] | None = None, top_n: int = 5):
        super().__init__(token, org, repo)
        self.core_devs_input = core_devs
        self.top_n = top_n
        self.core_devs: list[str] = []
        self.prs: list[dict] = []  # [{author, state}]

    def _auto_seleccionar_core_devs(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[str]:
        print(f"  core_devs no especificado: auto-seleccionando top-{self.top_n} por commits...")
        cpa = CommitsPerAuthor(self.token, self.org, self.repo)
        cpa.fetch(fecha_inicio, fecha_fin)
        ranking = cpa.por_persona(fecha_inicio, fecha_fin)
        seleccionados = list(ranking.keys())[:self.top_n]
        print(f"  Core devs seleccionados: {', '.join(seleccionados)}")
        return seleccionados

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, **kwargs):
        self.core_devs = self.core_devs_input or self._auto_seleccionar_core_devs(fecha_inicio, fecha_fin)
        core_devs_set = set(self.core_devs)

        prs = []
        cursor, page = None, 0
        while True:
            page += 1
            data = self._graphql(_QUERY_PRS, {"owner": self.org, "name": self.repo, "after": cursor})
            conexion = data["data"]["repository"]["pullRequests"]
            for node in conexion["nodes"]:
                author_node = node.get("author") or {}
                login = author_node.get("login")
                if login in core_devs_set:
                    prs.append({"author": login, "state": node["state"]})
            print(f"  ...PRs página {page} ({len(prs)} de core devs acumuladas)", end="\r")
            if not conexion["pageInfo"]["hasNextPage"]:
                break
            cursor = conexion["pageInfo"]["endCursor"]
        print()
        self.prs = prs

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, dict]:
        resultado = {login: {"prs_generadas": 0, "prs_rechazadas": 0} for login in self.core_devs}
        for pr in self.prs:
            resultado[pr["author"]]["prs_generadas"] += 1
            if pr["state"] == "CLOSED":
                resultado[pr["author"]]["prs_rechazadas"] += 1
        return resultado

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        return {
            "prs_generadas_total": len(self.prs),
            "prs_rechazadas_total": sum(1 for pr in self.prs if pr["state"] == "CLOSED"),
        }

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona", **kwargs):
        print(f"Consultando PRs de core devs en {self.org}/{self.repo}...")
        self.fetch(fecha_inicio, fecha_fin)

        if por == "producto":
            r = self.por_producto(fecha_inicio, fecha_fin)
            print(f"\nCore devs: {', '.join(self.core_devs)}")
            print(f"Total de PRs generadas por core devs:   {r['prs_generadas_total']}")
            print(f"Total de PRs rechazadas de core devs:   {r['prs_rechazadas_total']}")
        else:
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"\n{'Core dev':<30} {'PRs generadas':>15} {'PRs rechazadas':>16}")
            print("-" * 63)
            total_gen, total_rech = 0, 0
            for login, d in resultado.items():
                print(f"{login:<30} {d['prs_generadas']:>15} {d['prs_rechazadas']:>16}")
                total_gen += d["prs_generadas"]
                total_rech += d["prs_rechazadas"]
            print("-" * 63)
            print(f"{'Total':<30} {total_gen:>15} {total_rech:>16}")
