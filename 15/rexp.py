import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric


def calcular_rexp(user_commits: list[dict], fecha_actual: datetime) -> float:
    """
    Calcula la Experiencia Reciente (REXP).
    Pondera la experiencia del desarrollador (EXP) por la antigüedad de sus cambios,
    otorgando mayor peso a las habilidades técnicas aplicadas recientemente.
    """
    rexp_total = 0
    for commit in user_commits:
        # Se suma 1 para evitar división por cero en commits del mismo día
        dias_antiguedad = (fecha_actual - commit["date"]).days
        rexp_total += 1 / (dias_antiguedad + 1)
    return rexp_total


class RecentExperience(GitHubMetric):
    """
    REXP (Experiencia Reciente).
    Experiencia reciente ponderada, dando más peso a las contribuciones
    realizadas en fechas cercanas a la actual. Solo aplica por persona.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.commits: list[dict] = []  # {author, date}

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, max_commits: int = 1000):
        print("Descargando commits...")
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
            for c in data:
                author = (c.get("author") or {}).get("login") \
                    or (c.get("commit", {}).get("author") or {}).get("name") \
                    or "desconocido"
                date = datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00"))
                commits.append({"author": author, "date": date})
            print(f"  ...{len(commits)} commits descargados", end="\r")
            if len(data) < 100:
                break
            page += 1
        print()
        self.commits = commits[:max_commits]

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError("REXP es una métrica por persona, no aplica por producto.")

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        por_autor: dict[str, list[dict]] = {}
        for c in self.commits:
            por_autor.setdefault(c["author"], []).append(c)

        resultado = {
            author: round(calcular_rexp(commits, fecha_fin), 4)
            for author, commits in por_autor.items()
        }
        return dict(sorted(resultado.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona",
            max_commits: int = 1000, **kwargs):
        if por == "producto":
            print("REXP no aplica por producto: es una métrica por persona.")
            return
        self.fetch(fecha_inicio, fecha_fin, max_commits=max_commits)
        resultado = self.por_persona(fecha_inicio, fecha_fin)
        if not resultado:
            print("No se encontraron commits en el período.")
            return
        print(f"\n{'Colaborador':<30} REXP")
        print("-" * 40)
        for author, rexp in resultado.items():
            print(f"{author:<30} {rexp}")
