import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric


def calcular_contribution_diversity(historial_commits_usuario: list[dict]) -> int:
    """
    Calcula la Diversidad de Contribución.
    Mide la versatilidad del desarrollador analizando la dispersión de sus
    cambios en el árbol de archivos (componentes) del repositorio.

    historial_commits_usuario: Lista de diccionarios, donde cada uno representa
                               un commit y contiene la lista de archivos modificados.
    """
    # Se utiliza un conjunto (set) para garantizar que solo se cuenten
    # componentes únicos a lo largo de toda la historia del usuario.
    componentes_unicos = set()

    for commit in historial_commits_usuario:
        # Se asume que 'files' contiene las rutas únicas de los archivos modificados
        componentes_unicos.update(commit["files"])

    # La métrica es el conteo escalar de componentes distintos intervenidos.
    return len(componentes_unicos)


class ContributionDiversity(GitHubMetric):
    """
    Contribution Diversity (CDIV).
    Versatilidad del desarrollador basada en la dispersión de sus cambios en
    el árbol de archivos del repositorio. Solo aplica por persona.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.commits: list[dict] = []  # {author, files, timestamp}

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, max_commits: int = 200):
        print("Descargando lista de commits...")
        commits, page = [], 1
        while len(commits) < max_commits:
            data = self._rest(
                f"/repos/{self.org}/{self.repo}/commits",
                {
                    "since": fecha_inicio.isoformat(),
                    "until": fecha_fin.isoformat(),
                    "per_page": 100,
                    "page": page,
                },
            )
            if not data:
                break
            commits.extend(data)
            if len(data) < 100:
                break
            page += 1
        commits = commits[:max_commits]
        print(f"Commits en período: {len(commits)}")

        registros = []
        for i, c in enumerate(commits):
            detail = self._rest(f"/repos/{self.org}/{self.repo}/commits/{c['sha']}")
            author = (c.get("author") or {}).get("login") \
                or (c.get("commit", {}).get("author") or {}).get("name") \
                or "desconocido"
            ts = datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00"))
            files = [f["filename"] for f in detail.get("files", [])]
            registros.append({"author": author, "files": files, "timestamp": ts})
            print(f"  ...{i + 1}/{len(commits)} commits analizados", end="\r")
        print()
        self.commits = registros

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError("Contribution Diversity es una métrica por persona, no aplica por producto.")

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        por_autor: dict[str, list[dict]] = {}
        for c in self.commits:
            por_autor.setdefault(c["author"], []).append(c)

        resultado = {
            author: calcular_contribution_diversity(historial)
            for author, historial in por_autor.items()
        }
        return dict(sorted(resultado.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona",
            max_commits: int = 200, **kwargs):
        if por == "producto":
            print("Contribution Diversity no aplica por producto: es una métrica por persona.")
            return
        self.fetch(fecha_inicio, fecha_fin, max_commits=max_commits)
        if not self.commits:
            print("No se encontraron commits en el período.")
            return
        resultado = self.por_persona(fecha_inicio, fecha_fin)
        print(f"\n{'Colaborador':<30} CDIV (archivos únicos)")
        print("-" * 55)
        for author, cdiv in resultado.items():
            print(f"{author:<30} {cdiv}")
