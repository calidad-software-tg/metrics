import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric


def calcular_fexp(commit_actual: dict, historial_commits_usuario: list[dict]) -> int:
    """
    Calcula la Experiencia en Archivos (FEXP).
    Suma la experiencia previa del desarrollador en cada archivo del commit actual.

    commit_actual: Diccionario con 'files' (lista de rutas) y 'timestamp'.
    historial_commits_usuario: Lista de commits previos del mismo autor.
    """
    fexp_total = 0
    archivos_objetivo = commit_actual["files"]
    ts_actual = commit_actual["timestamp"]

    for archivo in archivos_objetivo:
        # Se cuenta la frecuencia de commits previos del autor para cada archivo específico
        conteo_previo = sum(
            1 for c in historial_commits_usuario
            if archivo in c["files"] and c["timestamp"] < ts_actual
        )
        fexp_total += conteo_previo

    return fexp_total


class FileExperience(GitHubMetric):
    """
    FEXP (Experiencia en Archivos).
    Experiencia específica acumulada por el autor en los archivos modificados
    dentro de sus commits. Solo aplica por persona.
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
        raise NotImplementedError("FEXP es una métrica por persona, no aplica por producto.")

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        por_autor: dict[str, list[dict]] = {}
        for c in self.commits:
            por_autor.setdefault(c["author"], []).append(c)

        resultado = {}
        for author, historial in por_autor.items():
            historial_ordenado = sorted(historial, key=lambda c: c["timestamp"])
            valores = [
                calcular_fexp(commit_actual, historial_ordenado[:i])
                for i, commit_actual in enumerate(historial_ordenado)
            ]
            resultado[author] = round(sum(valores) / len(valores), 2) if valores else 0.0

        return dict(sorted(resultado.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona",
            max_commits: int = 200, **kwargs):
        if por == "producto":
            print("FEXP no aplica por producto: es una métrica por persona.")
            return
        self.fetch(fecha_inicio, fecha_fin, max_commits=max_commits)
        if not self.commits:
            print("No se encontraron commits en el período.")
            return
        resultado = self.por_persona(fecha_inicio, fecha_fin)
        print(f"\n{'Colaborador':<30} FEXP (promedio por commit)")
        print("-" * 60)
        for author, fexp in resultado.items():
            print(f"{author:<30} {fexp}")
