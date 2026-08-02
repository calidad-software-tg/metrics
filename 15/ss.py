import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric


def calcular_skill_similarity(user_languages: set, repo_languages: set) -> float:
    """
    Calcula la Similitud de Habilidades (Skill Similarity).
    Mide la afinidad técnica inicial del desarrollador con el repositorio.

    user_languages: Conjunto (set) de lenguajes dominados por el usuario,
                    identificados por sus contribuciones en otros proyectos.
    repo_languages: Conjunto (set) de lenguajes que componen el repositorio
                    objetivo (con una contribución > 0.1% en bytes).
    """
    if not repo_languages:
        return 0

    habilidades_comunes = user_languages.intersection(repo_languages)
    return len(habilidades_comunes) / len(repo_languages)


class SkillSimilarity(GitHubMetric):
    """
    Skill Similarity (SS).
    Grado de solapamiento entre los lenguajes dominados por un colaborador
    (según sus repositorios propios) y los lenguajes que componen el
    repositorio objetivo. Solo aplica por persona.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.repo_languages: set = set()
        self.user_languages: dict[str, set] = {}

    def fetch(self, max_contributors: int = 15, max_user_repos: int = 100):
        print("Obteniendo lenguajes del repositorio...")
        repo_bytes = self._rest(f"/repos/{self.org}/{self.repo}/languages")
        total = sum(repo_bytes.values()) or 1
        self.repo_languages = {lang for lang, b in repo_bytes.items() if b / total > 0.001}
        print(f"Lenguajes del repositorio (>0.1%): {sorted(self.repo_languages)}")

        print("Obteniendo colaboradores...")
        contributors = self._rest(
            f"/repos/{self.org}/{self.repo}/contributors",
            {"per_page": max_contributors},
        )[:max_contributors]

        user_languages = {}
        for i, c in enumerate(contributors):
            login = c["login"]
            repos = self._rest(
                f"/users/{login}/repos",
                {"per_page": max_user_repos, "type": "owner"},
            )
            langs = {r["language"] for r in repos if r.get("language")}
            user_languages[login] = langs
            print(f"  ...{i + 1}/{len(contributors)} colaboradores analizados", end="\r")
        print()
        self.user_languages = user_languages

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError("SS es una métrica por persona, no aplica por producto.")

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        resultado = {
            login: round(calcular_skill_similarity(langs, self.repo_languages), 4)
            for login, langs in self.user_languages.items()
        }
        return dict(sorted(resultado.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona",
            max_contributors: int = 15, **kwargs):
        if por == "producto":
            print("Skill Similarity no aplica por producto: es una métrica por persona.")
            return
        self.fetch(max_contributors=max_contributors)
        resultado = self.por_persona(fecha_inicio, fecha_fin)
        if not resultado:
            print("No se encontraron colaboradores.")
            return
        print(f"\n{'Colaborador':<30} SS")
        print("-" * 40)
        for login, ss in resultado.items():
            print(f"{login:<30} {ss}")
