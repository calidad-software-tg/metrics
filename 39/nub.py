import re
import sys
from pathlib import Path
from datetime import datetime

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

_QUERY_ISSUES = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    issues(first: 100, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      nodes {
        createdAt
        author { login }
        labels(first: 20) {
          nodes { name }
        }
      }
    }
  }
}
"""

# Nombres de archivo candidatos para identificar al core team, en orden de preferencia.
_MAINTAINERS_CANDIDATES = ["MAINTAINERS.md", ".github/MAINTAINERS.md", "CODEOWNERS", ".github/CODEOWNERS"]


class NumberOfBugsDetectedByUsers(GitHubMetric):
    """
    Number of Bugs Detected by Users (NUB) — Vasilescu et al. (2015).

    Cuantifica issues etiquetados como "bug" (vía labels) reportados por
    usuarios externos al core team (extraído de MAINTAINERS.md).
    Métrica de Producto/Proceso: no aplica por persona.

    Implementación fiel al algoritmo original `calcular_bugs_detectados_por_usuarios`
    provisto en la consigna (basado en labels), con una corrección de un bug
    de variable shadowing en la comprensión original (`key`/`label` mal usadas
    dos veces en el mismo generador) — ver 39 - Number of Bugs Detected by
    Users.md, sección 1, para el detalle.
    """

    _KEYWORDS_BUG = {
        "defect", "error", "bug", "issue", "mistake",
        "incorrect", "fault", "flaw",
    }

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self._issues: list[dict] = []
        self._core_team: set[str] = set()

    def _fetch_core_team(self) -> set[str]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.raw+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        for path in _MAINTAINERS_CANDIDATES:
            resp = requests.get(
                f"https://api.github.com/repos/{self.org}/{self.repo}/contents/{path}",
                headers=headers,
            )
            if resp.ok:
                contenido = resp.text
                handles = set(re.findall(r"@([A-Za-z0-9-]+)", contenido))
                if handles:
                    print(f"Core team detectado en '{path}': {len(handles)} usuarios")
                    return handles
        print("No se encontró MAINTAINERS.md/CODEOWNERS legible; core team queda vacío (revisar manualmente).")
        return set()

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, **kwargs):
        self._core_team = self._fetch_core_team()

        cursor, page = None, 0
        print("Obteniendo issues...")
        while True:
            page += 1
            data = self._graphql(_QUERY_ISSUES, {"owner": self.org, "repo": self.repo, "cursor": cursor})
            nodes = data["data"]["repository"]["issues"]["nodes"]
            page_info = data["data"]["repository"]["issues"]["pageInfo"]
            print(f"  ...issues página {page} ({len(self._issues)} acumulados)", end="\r")
            for node in nodes:
                created = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
                if not (fecha_inicio <= created <= fecha_fin):
                    continue
                login = (node.get("author") or {}).get("login", "desconocido")
                labels = [n["name"] for n in node.get("labels", {}).get("nodes", [])]
                self._issues.append({"user_login": login, "labels": labels})
            if not page_info["hasNextPage"]:
                break
            cursor = page_info["endCursor"]
        print()
        print(f"Issues en período: {len(self._issues)}")

    def _calcular_bugs_detectados_por_usuarios(self, metadata_issues: list[dict], lista_historica_core_team: set[str]) -> int:
        """
        Fiel al algoritmo original de la consigna, con una corrección:
        la comprensión original reutilizaba la variable `key` en los dos
        `for` y referenciaba una `label` nunca definida (NameError). Se
        corrige a `for label in etiquetas for keyword in keywords_bug`.
        """
        conteo_user_bugs = 0

        for issue in metadata_issues:
            reportero = issue.get("user_login")
            etiquetas = [et.lower() for et in issue.get("labels", [])]

            # Criterio de tipo: ¿está etiquetado como bug?
            es_bug = any(keyword in label for label in etiquetas for keyword in self._KEYWORDS_BUG)

            if es_bug:
                # Criterio de afiliación: ¿el reportero es externo al core team?
                if reportero not in lista_historica_core_team:
                    conteo_user_bugs += 1

        return conteo_user_bugs

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError("NUB es una métrica por producto, no aplica por persona.")

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, dict]:
        nub = self._calcular_bugs_detectados_por_usuarios(self._issues, self._core_team)
        return {
            self.repo: {
                "issues_analizados": len(self._issues),
                "core_team_size": len(self._core_team),
                "nub": nub,
            }
        }

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        if por == "persona":
            print("Number of Bugs Detected by Users no aplica por persona: es una métrica por producto.")
            return
        self.fetch(fecha_inicio, fecha_fin)
        resultado = self.por_producto(fecha_inicio, fecha_fin)
        for repo, d in resultado.items():
            print(f"\nRepositorio: {repo}")
            print(f"Issues analizados     : {d['issues_analizados']}")
            print(f"Core team detectado   : {d['core_team_size']}")
            print(f"Bugs detectados por usuarios (NUB): {d['nub']}")