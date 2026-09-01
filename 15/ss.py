import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

# Reutiliza el mismo filtro de carpetas de dependencias/artefactos generados
# que loc.py/developer_ownership.py (no tiene sentido que node_modules/vendor
# infle la composición de lenguajes del repo).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "Notion"))
from loc import _is_excluded

# Mapeo extensión -> nombre de lenguaje "canónico" de GitHub Linguist, para
# los lenguajes más comunes. Se usa solo para reconstruir repo_languages en
# un commit pasado (ver _repo_languages_en_ref). No es una implementación de
# Linguist: no detecta shebangs, no respeta .gitattributes ni archivos
# generados fuera de las carpetas ya excluidas. Para el propósito de esta
# métrica (set de lenguajes con >0.1% de bytes) es suficiente aproximación.
#
# NO se incluyen extensiones que Linguist marca como `type: data` (.json,
# .yml/.yaml, .csv, .xml, .toml, ...) ni `type: prose` fuera de Markdown:
# GitHub las excluye de /repos/.../languages, y `user_languages` (campo
# `.language` de los repos del usuario) tampoco las contiene nunca, así que
# meterlas solo inflaría el denominador len(repo_languages) y bajaría todos
# los SS. Markdown sí se cuenta (Linguist lo reporta para tldr).
_EXT_TO_LANG = {
    ".py": "Python", ".pyw": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".java": "Java",
    ".c": "C", ".h": "C",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++",
    ".cs": "C#",
    ".go": "Go",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin", ".kts": "Kotlin",
    ".rs": "Rust",
    ".scala": "Scala",
    ".sh": "Shell", ".bash": "Shell",
    ".ps1": "PowerShell",
    ".html": "HTML", ".htm": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".vue": "Vue",
    ".dart": "Dart",
    ".m": "Objective-C", ".mm": "Objective-C",
    ".sql": "SQL",
    ".r": "R",
    ".pl": "Perl",
    ".lua": "Lua",
    ".groovy": "Groovy",
    ".ex": "Elixir", ".exs": "Elixir",
    ".clj": "Clojure",
    ".hs": "Haskell",
    ".erl": "Erlang",
    ".md": "Markdown", ".markdown": "Markdown",
}


def calcular_skill_similarity(user_languages: set, repo_languages: set) -> float:
    """
    Calcula la Similitud de Habilidades (Skill Similarity).
    Mide la afinidad técnica del desarrollador con el repositorio.

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

    Por ventana/bloque:
      - repo_languages se recalcula en el commit vigente al cierre del bloque
        (mismo criterio que dloc/loc_notion/cd vía _resolve_ref), no siempre
        HEAD: el stack de un repo cambia entre versiones.
      - los colaboradores evaluados son los que commitearon DENTRO del bloque
        (antes: siempre el top-N de colaboradores históricos del repo entero,
        igual en todos los bloques).
      - user_languages sigue siendo un snapshot de los repos propios ACTUALES
        de cada colaborador (no hay forma de reconstruir qué lenguajes
        dominaba en una fecha pasada sin recorrer el historial de cada uno de
        sus repos); el spec ISL la define igual, sin acotar por fecha
        ("identificados por sus contribuciones en otros proyectos").
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.repo_languages: set = set()
        self.user_languages: dict[str, set] = {}

    def _repo_languages_en_ref(self, ref: str) -> set[str]:
        """Aproximación de /repos/.../languages para un commit pasado.

        GitHub no permite pedirle a ese endpoint la composición en un ref
        distinto de HEAD, así que se reconstruye a partir del árbol del repo:
        se suma el tamaño en bytes (que la API de trees ya trae por archivo,
        sin pedir el blob) agrupado por lenguaje según extensión, y se aplica
        el mismo piso de >0.1% del total que usa GitHub.
        """
        tree = self._rest(f"/repos/{self.org}/{self.repo}/git/trees/{ref}", {"recursive": "1"})
        bytes_por_lenguaje: dict[str, int] = {}
        for entry in tree.get("tree", []):
            if entry.get("type") != "blob" or _is_excluded(entry["path"]):
                continue
            lenguaje = _EXT_TO_LANG.get(Path(entry["path"]).suffix.lower())
            if not lenguaje:
                continue
            bytes_por_lenguaje[lenguaje] = bytes_por_lenguaje.get(lenguaje, 0) + entry.get("size", 0)

        total = sum(bytes_por_lenguaje.values()) or 1
        return {lang for lang, b in bytes_por_lenguaje.items() if b / total > 0.001}

    def _colaboradores_en_ventana(self, fecha_inicio: datetime, fecha_fin: datetime,
                                  max_contributors: int) -> list[str]:
        """Logins distintos con al menos un commit en [fecha_inicio, fecha_fin],
        en orden de aparición (más reciente primero), hasta max_contributors."""
        vistos: set[str] = set()
        logins: list[str] = []
        page = 1
        while len(vistos) < max_contributors:
            data = self._rest(
                f"/repos/{self.org}/{self.repo}/commits",
                {"since": fecha_inicio.isoformat(), "until": fecha_fin.isoformat(),
                 "per_page": 100, "page": page},
            )
            if not data:
                break
            for c in data:
                login = (c.get("author") or {}).get("login")
                if login and login not in vistos:
                    vistos.add(login)
                    logins.append(login)
                    if len(vistos) >= max_contributors:
                        break
            if len(data) < 100:
                break
            page += 1
        return logins

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime,
              max_contributors: int = 15, max_user_repos: int = 100):
        print("Obteniendo lenguajes del repositorio en el commit vigente al cierre del bloque...")
        ref = self._resolve_ref(fecha_fin)
        self.repo_languages = self._repo_languages_en_ref(ref)
        print(f"Lenguajes del repositorio (>0.1%, {ref[:7]}): {sorted(self.repo_languages)}")

        print("Obteniendo colaboradores activos en el bloque...")
        logins = self._colaboradores_en_ventana(fecha_inicio, fecha_fin, max_contributors)

        user_languages = {}
        for i, login in enumerate(logins):
            repos = self._rest(
                f"/users/{login}/repos",
                {"per_page": max_user_repos, "type": "owner"},
            )
            langs = {r["language"] for r in repos if r.get("language")}
            user_languages[login] = langs
            print(f"  ...{i + 1}/{len(logins)} colaboradores analizados", end="\r")
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
        self.fetch(fecha_inicio, fecha_fin, max_contributors=max_contributors)
        resultado = self.por_persona(fecha_inicio, fecha_fin)
        if not resultado:
            print("No se encontraron colaboradores.")
            return
        print(f"\n{'Colaborador':<30} SS")
        print("-" * 40)
        for login, ss in resultado.items():
            print(f"{login:<30} {ss}")
