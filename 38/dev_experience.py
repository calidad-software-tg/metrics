import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

_QUERY_COMMITS = """
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $cursor) {
            pageInfo { hasNextPage endCursor }
            nodes {
              committedDate
              author {
                user { login name }
                name
                email
              }
            }
          }
        }
      }
    }
  }
}
"""


class DevelopmentExperience(GitHubMetric):
    """
    Development Experience (DE) — Eyolfson et al. (2011), Wu et al. (2014).

    Mide la antigüedad (en meses) de cada desarrollador dentro del repositorio,
    calculada como el tiempo transcurrido desde su primer commit hasta una
    fecha de referencia. Métrica de Persona/Proceso: no aplica por producto.

    Nota: catalogada originalmente como sustituta de "Technology Adoption"
    (ISL), con la cual no guarda relación conceptual — ver 38 - Development
    Experience.md, sección 1, para el detalle de la discrepancia.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self._commits: list[dict] = []

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, **kwargs):
        cursor, page = None, 0
        print("Obteniendo commits...")
        while True:
            page += 1
            data = self._graphql(_QUERY_COMMITS, {"owner": self.org, "repo": self.repo, "cursor": cursor})
            history = data["data"]["repository"]["defaultBranchRef"]["target"]["history"]
            nodes = history["nodes"]
            page_info = history["pageInfo"]
            print(f"  ...commits página {page} ({len(self._commits)} acumulados)", end="\r")
            for node in nodes:
                author = node.get("author") or {}
                user = author.get("user") or {}
                committed = datetime.fromisoformat(node["committedDate"].replace("Z", "+00:00"))
                self._commits.append({
                    "login": user.get("login"),
                    "profile_name": user.get("name"),
                    "git_name": author.get("name"),
                    "email": author.get("email"),
                    "timestamp": committed,
                })
            if not page_info["hasNextPage"]:
                break
            cursor = page_info["endCursor"]
        print()
        print(f"Commits totales obtenidos: {len(self._commits)}")

    def _resolver_identidades(self) -> list[dict]:
        """
        Normaliza la identidad de cada commit a un único 'author' por persona.

        Problema: un mismo desarrollador puede aparecer partido en dos
        identidades — una vez como su login de GitHub (cuando el commit
        está vinculado a su cuenta) y otra como el nombre crudo de
        `git config` (cuando no lo está), si usó distintos emails.

        Solución: se construye un mapa {nombre de perfil de GitHub -> login}
        a partir de los commits que sí están vinculados a una cuenta. Los
        commits sin vínculo se reasignan al mismo login si su `git_name`
        coincide (case-insensitive) con el nombre de perfil de algún login
        ya visto. Si no hay coincidencia, se usa el `git_name` tal cual.
        """
        nombre_perfil_a_login: dict[str, str] = {}
        for c in self._commits:
            if c["login"] and c["profile_name"]:
                nombre_perfil_a_login[c["profile_name"].strip().lower()] = c["login"]

        resueltos = []
        for c in self._commits:
            if c["login"]:
                identidad = c["login"]
            else:
                clave = (c["git_name"] or "").strip().lower()
                identidad = nombre_perfil_a_login.get(clave, c["git_name"] or "desconocido")
            resueltos.append({"author": identidad, "timestamp": c["timestamp"]})
        return resueltos

    def _calcular_development_experience(self, historial_commits_usuario: list[dict], fecha_referencia: datetime) -> float:
        if not historial_commits_usuario:
            return 0.0
        fecha_primer_commit = min(c["timestamp"] for c in historial_commits_usuario)
        diferencia = fecha_referencia - fecha_primer_commit
        experiencia_meses = diferencia.days / 30.44
        return round(experiencia_meses, 2)

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError("Development Experience es una métrica por persona, no aplica por producto.")

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, dict]:
        commits_resueltos = self._resolver_identidades()
        por_autor: dict[str, list] = {}
        for c in commits_resueltos:
            por_autor.setdefault(c["author"], []).append(c)

        result = {}
        for login, commits in por_autor.items():
            experiencia = self._calcular_development_experience(commits, fecha_fin)
            primer_commit = min(c["timestamp"] for c in commits)
            result[login] = {
                "primer_commit": primer_commit.isoformat(),
                "experiencia_meses": experiencia,
            }
        return dict(sorted(result.items(), key=lambda x: x[1]["experiencia_meses"], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona", **kwargs):
        if por == "producto":
            print("Development Experience no aplica por producto: es una métrica por persona.")
            return
        self.fetch(fecha_inicio, fecha_fin)
        resultado = self.por_persona(fecha_inicio, fecha_fin)
        if not resultado:
            print("No se encontraron commits en el período.")
            return
        print(f"\n{'Colaborador':<25} {'Primer commit':<28} {'Experiencia (meses)':>20}")
        print("-" * 75)
        for login, d in resultado.items():
            print(f"{login:<25} {d['primer_commit']:<28} {d['experiencia_meses']:>20}")