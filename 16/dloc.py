import sys
import base64
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

_DOC_EXTENSIONS = {'.md', '.txt', '.rst'}


def _count_lines(content: str) -> int:
    return sum(1 for l in content.splitlines() if l.strip())


class DocumentationLinesOfCode(GitHubMetric):

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.files: list[dict] = []  # [{path, lines}]

    def fetch(self, max_files: int = 500, **kwargs):
        print("Obteniendo árbol del repositorio...")
        tree = self._rest(
            f"/repos/{self.org}/{self.repo}/git/trees/HEAD",
            {"recursive": "1"},
        )
        doc_files = [
            e for e in tree.get("tree", [])
            if e["type"] == "blob"
            and Path(e["path"]).suffix.lower() in _DOC_EXTENSIONS
        ]
        total = len(doc_files)
        doc_files = doc_files[:max_files]
        print(f"Archivos de documentación encontrados: {total} (analizando {len(doc_files)})")

        files = []
        for i, entry in enumerate(doc_files):
            blob = self._rest(f"/repos/{self.org}/{self.repo}/git/blobs/{entry['sha']}")
            try:
                content = base64.b64decode(blob["content"]).decode("utf-8", errors="replace")
            except Exception:
                continue
            files.append({"path": entry["path"], "lines": _count_lines(content)})
            print(f"  ...{i + 1}/{len(doc_files)} archivos procesados", end="\r")

        print()
        self.files = files

    def _fetch_last_author(self, path: str) -> str:
        commits = self._rest(
            f"/repos/{self.org}/{self.repo}/commits",
            {"path": path, "per_page": 1},
        )
        if not commits:
            return "desconocido"
        c = commits[0]
        return (
            (c.get("author") or {}).get("login")
            or (c.get("commit", {}).get("author") or {}).get("name")
            or "desconocido"
        )

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return sum(f["lines"] for f in self.files)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        by_author: dict[str, int] = {}
        total = len(self.files)
        for i, f in enumerate(self.files):
            login = self._fetch_last_author(f["path"])
            by_author[login] = by_author.get(login, 0) + f["lines"]
            print(f"  ...{i + 1}/{total} archivos con autor resuelto", end="\r")
        print()
        return dict(sorted(by_author.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto",
            max_files: int = 500, **kwargs):
        self.fetch(max_files=max_files)
        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"{'Colaborador':<30} DLOC")
            print("-" * 40)
            for login, lines in resultado.items():
                print(f"{login:<30} {lines}")
        else:
            total = self.por_producto(fecha_inicio, fecha_fin)
            print(f"DLOC (Documentation Lines of Code): {total} líneas")