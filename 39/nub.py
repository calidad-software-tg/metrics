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
        authorAssociation
        author { login }
        labels(first: 20) {
          nodes { name }
        }
      }
    }
  }
}
"""

# Asociaciones que indican pertenencia al core team en GitHub.
# authorAssociation = afiliación al momento de reportar el issue (no la de hoy).
_CORE_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}

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
        "defect", "error", "bug", "mistake",
        "incorrect", "fault", "flaw",
        # "issue" eliminado: como substring matchea "good first issue",
        # "open issue", etc. — demasiados falsos positivos.
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
        # Fallback: miembros de la organización (funciona para orgs públicas
        # como vercel cuando no hay MAINTAINERS.md/CODEOWNERS).
        headers_json = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        handles: set[str] = set()
        page = 1
        while True:
            resp = requests.get(
                f"https://api.github.com/orgs/{self.org}/members",
                headers=headers_json,
                params={"per_page": 100, "page": page},
            )
            if not resp.ok:
                break
            batch = resp.json()
            if not batch:
                break
            handles |= {m["login"] for m in batch if "login" in m}
            if len(batch) < 100:
                break
            page += 1
        if handles:
            print(f"Core team vía org members ({self.org}): {len(handles)} usuarios")
            return handles
        print("No se encontró MAINTAINERS.md/CODEOWNERS ni org members; core team queda vacío.")
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
                # 'created' se guarda para que SLICEABLE pueda recortar por ventana
                # sin necesidad de repetir el fetch en cada una.
                self._issues.append({
                    "user_login": login,
                    "labels": labels,
                    "created": created,
                    "author_association": node.get("authorAssociation", ""),
                })
            if not page_info["hasNextPage"]:
                break
            cursor = page_info["endCursor"]
        print()
        print(f"Issues en período: {len(self._issues)}")

    def _calcular_bugs_detectados_por_usuarios(
        self, metadata_issues: list[dict], lista_historica_core_team: set[str]
    ) -> dict:
        """
        Fiel al algoritmo original de la consigna, con dos correcciones:
        1. La comprensión original reutilizaba la variable `key` y referenciaba
           una `label` nunca definida (NameError). Corregido a `for label in
           etiquetas for keyword in keywords_bug`.
        2. Criterio de afiliación: se usa `authorAssociation` (campo GraphQL,
           afiliación al momento del reporte) como fuente principal. Solo si
           el campo no está disponible se cae al fallback de la lista de core team.

        Devuelve un dict con el desglose completo. `nub=None` cuando ningún issue
        tiene label de bug en la ventana (métrica no observable, ≠ "cero bugs").
        """
        conteo_user_bugs = 0
        con_label_bug = 0
        por_asociacion: dict[str, int] = {}
        labels_bug_vistos: set[str] = set()

        for issue in metadata_issues:
            labels_orig = issue.get("labels", [])
            etiquetas = [l.lower() for l in labels_orig]

            bug_labels_orig = [
                orig for orig, low in zip(labels_orig, etiquetas)
                if any(kw in low for kw in self._KEYWORDS_BUG)
            ]
            es_bug = bool(bug_labels_orig)

            if es_bug:
                con_label_bug += 1
                labels_bug_vistos.update(bug_labels_orig)

                association = issue.get("author_association", "")
                por_asociacion[association] = por_asociacion.get(association, 0) + 1

                if association:
                    es_externo = association not in _CORE_ASSOCIATIONS
                else:
                    reportero = issue.get("user_login", "")
                    es_externo = reportero not in lista_historica_core_team
                if es_externo:
                    conteo_user_bugs += 1

        return {
            # None = no observable (sin labels de bug en la ventana).
            # 0 = observable pero todos los bugs los reportó el core team.
            "nub": conteo_user_bugs if con_label_bug > 0 else None,
            "con_label_bug": con_label_bug,
            "por_asociacion": por_asociacion,
            # Lista vacía es el detector de ventana no observable.
            "labels_bug_vistos": sorted(labels_bug_vistos),
        }

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError("NUB es una métrica por producto, no aplica por persona.")

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, dict]:
        breakdown = self._calcular_bugs_detectados_por_usuarios(self._issues, self._core_team)
        return {
            self.repo: {
                "nub": breakdown["nub"],
                "issues_analizados": len(self._issues),
                "con_label_bug": breakdown["con_label_bug"],
                "por_asociacion": breakdown["por_asociacion"],
                "labels_bug_vistos": breakdown["labels_bug_vistos"],
                "criterio_afiliacion": "authorAssociation",
                "core_team_fallback_size": len(self._core_team),
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
            print(f"Con label bug         : {d['con_label_bug']}")
            print(f"Distribución afiliación: {d['por_asociacion']}")
            print(f"Labels bug vistos     : {d['labels_bug_vistos']}")
            print(f"Bugs detectados por usuarios (NUB): {d['nub']}")