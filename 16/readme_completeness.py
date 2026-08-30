import sys
import base64
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

_SECCIONES = {
    'What':         ['introduction', 'about', 'overview', 'background'],
    'Why':          ['purpose', 'motivation', 'advantages', 'features'],
    'How':          ['install', 'usage', 'getting started', 'setup', 'quick start', 'dependencies'],
    'When':         ['status', 'roadmap', 'version', 'changelog', 'todo'],
    'Who':          ['license', 'author', 'maintainer', 'contact', 'acknowledgement', 'team'],
    'References':   ['documentation', 'api', 'links', 'resources', 'related'],
    'Contribution': ['contribute', 'contributing', 'pull request', 'fork'],
}

_TOTAL = len(_SECCIONES)


def _score(content: str) -> float:
    """Prana et al. (2018): proporción de categorías cubiertas."""
    if not content or len(content) < 10:
        return 0.0
    texto = content.lower()
    hits = sum(1 for kws in _SECCIONES.values() if any(k in texto for k in kws))
    return round(hits / _TOTAL, 4)


class ReadmeCompleteness(GitHubMetric):

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.readmes: list[dict] = []  # [{path, score}]

    def fetch(self, fecha_fin: datetime, **kwargs):
        print("Obteniendo árbol del repositorio...")
        ref = self._resolve_ref(fecha_fin)
        tree = self._rest(
            f"/repos/{self.org}/{self.repo}/git/trees/{ref}",
            {"recursive": "1"},
        )
        readme_files = [
            e for e in tree.get("tree", [])
            if e["type"] == "blob" and Path(e["path"]).name.lower() == "readme.md"
        ]
        print(f"README.md encontrados: {len(readme_files)}")

        readmes = []
        for i, entry in enumerate(readme_files):
            blob = self._rest(f"/repos/{self.org}/{self.repo}/git/blobs/{entry['sha']}")
            try:
                content = base64.b64decode(blob["content"]).decode("utf-8", errors="replace")
            except Exception:
                continue
            readmes.append({"path": entry["path"], "score": _score(content)})
            print(f"  ...{i + 1}/{len(readme_files)} README analizados", end="\r")

        print()
        self.readmes = readmes

    def _fetch_last_author(self, path: str, fecha_fin: datetime) -> str:
        commits = self._rest(
            f"/repos/{self.org}/{self.repo}/commits",
            {"path": path, "per_page": 1, "until": fecha_fin.isoformat()},
        )
        if not commits:
            return "desconocido"
        c = commits[0]
        return (
            (c.get("author") or {}).get("login")
            or (c.get("commit", {}).get("author") or {}).get("name")
            or "desconocido"
        )

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        if not self.readmes:
            return 0.0
        return round(sum(r["score"] for r in self.readmes) / len(self.readmes), 4)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        by_author: dict[str, list[float]] = {}
        total = len(self.readmes)
        for i, r in enumerate(self.readmes):
            login = self._fetch_last_author(r["path"], fecha_fin)
            by_author.setdefault(login, []).append(r["score"])
            print(f"  ...{i + 1}/{total} READMEs con autor resuelto", end="\r")
        print()
        result = {
            login: round(sum(scores) / len(scores), 4)
            for login, scores in by_author.items()
        }
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        self.fetch(fecha_fin)
        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"{'Colaborador':<30} RC")
            print("-" * 40)
            for login, sc in resultado.items():
                print(f"{login:<30} {sc}")
        else:
            score = self.por_producto(fecha_inicio, fecha_fin)
            print(f"RC (README Completeness): {score}  (ref. óptimo = 1.0, 7 secciones Prana et al.)")
