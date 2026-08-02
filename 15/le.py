import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric


def calcular_learning_easy(commits_componente: list[dict]) -> int:
    """
    Calcula el 'Learning Easy' (Aprendizaje Fácil).
    Define la capacidad de aprendizaje como el tiempo requerido para dominar un componente.
    Se mide como el intervalo (en días) entre la primera y la última contribución
    de un autor sobre dicho componente.
    """
    if not commits_componente:
        return 0

    timestamps = [c["timestamp"] for c in commits_componente]
    delta = max(timestamps) - min(timestamps)
    return delta.days


class LearningEase(GitHubMetric):
    """
    Learning Easy (LE).
    Tiempo (en días) que le toma a un desarrollador dominar un componente del
    repositorio, aproximado como el lapso entre su primera y última contribución
    a dicho componente (el primer segmento de la ruta del archivo).
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.registros: list[dict] = []  # {author, component, timestamp}

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
            for f in detail.get("files", []):
                filename = f["filename"]
                componente = filename.split("/")[0] if "/" in filename else filename
                registros.append({"author": author, "component": componente, "timestamp": ts})
            print(f"  ...{i + 1}/{len(commits)} commits analizados", end="\r")
        print()
        self.registros = registros

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        por_componente: dict[str, list[dict]] = {}
        for r in self.registros:
            por_componente.setdefault(r["component"], []).append(r)

        if not por_componente:
            return 0.0

        valores = [calcular_learning_easy(commits) for commits in por_componente.values()]
        return round(sum(valores) / len(valores), 2)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        por_autor_componente: dict[tuple, list[dict]] = {}
        for r in self.registros:
            key = (r["author"], r["component"])
            por_autor_componente.setdefault(key, []).append(r)

        le_por_autor: dict[str, list[int]] = {}
        for (author, _componente), commits_componente in por_autor_componente.items():
            le_por_autor.setdefault(author, []).append(calcular_learning_easy(commits_componente))

        resultado = {
            author: round(sum(valores) / len(valores), 2)
            for author, valores in le_por_autor.items()
        }
        return dict(sorted(resultado.items(), key=lambda x: x[1]))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona",
            max_commits: int = 200, **kwargs):
        self.fetch(fecha_inicio, fecha_fin, max_commits=max_commits)
        if not self.registros:
            print("No se encontraron commits en el período.")
            return

        if por == "producto":
            le = self.por_producto(fecha_inicio, fecha_fin)
            print(f"\nLE (Learning Easy) promedio por componente: {le} días")
        else:
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"\n{'Colaborador':<30} LE (días, promedio por componente)")
            print("-" * 60)
            for author, le in resultado.items():
                print(f"{author:<30} {le}")
