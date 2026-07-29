import sys
import re
import base64
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_metric import GitHubMetric

# Comment line patterns by file extension
_COMMENT_PATTERNS: dict[str, list[str]] = {
    ".py":   [r"^\s*#"],
    ".sh":   [r"^\s*#"],
    ".rb":   [r"^\s*#"],
    ".r":    [r"^\s*#"],
    ".js":   [r"^\s*//", r"^\s*/\*", r"^\s*\*"],
    ".ts":   [r"^\s*//", r"^\s*/\*", r"^\s*\*"],
    ".java": [r"^\s*//", r"^\s*/\*", r"^\s*\*"],
    ".c":    [r"^\s*//", r"^\s*/\*", r"^\s*\*"],
    ".cpp":  [r"^\s*//", r"^\s*/\*", r"^\s*\*"],
    ".h":    [r"^\s*//", r"^\s*/\*", r"^\s*\*"],
    ".go":   [r"^\s*//", r"^\s*/\*", r"^\s*\*"],
    ".rs":   [r"^\s*//"],
    ".kt":   [r"^\s*//", r"^\s*/\*", r"^\s*\*"],
    ".php":  [r"^\s*//", r"^\s*#", r"^\s*/\*", r"^\s*\*"],
    ".swift":[r"^\s*//", r"^\s*/\*", r"^\s*\*"],
    ".md":   [r"<!--"],
    ".yaml": [r"^\s*#"],
    ".yml":  [r"^\s*#"],
}

_CODE_EXTENSIONS = set(_COMMENT_PATTERNS.keys())


def _count_lines(text: str, ext: str) -> tuple[int, int]:
    patterns = [re.compile(p) for p in _COMMENT_PATTERNS.get(ext, [])]
    cloc = lloc = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        if any(p.search(line) for p in patterns):
            cloc += 1
        else:
            lloc += 1
    return cloc, lloc


def _count_patch_lines(patch: str, ext: str) -> tuple[int, int]:
    """Count comment/code lines only in added (+) lines of a diff patch."""
    added_lines = [l[1:] for l in patch.splitlines() if l.startswith("+") and not l.startswith("+++")]
    return _count_lines("\n".join(added_lines), ext)


class CommentDensity(GitHubMetric):

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.files: list[dict] = []        # {path, cloc, lloc}
        self.author_lines: list[dict] = [] # {author, cloc, lloc}

    def fetch(self, con_actor: bool = False, max_files: int = 500,
              skip_extensions: set = frozenset({".md"})):
        print("Obteniendo árbol del repositorio...")
        tree = self._rest(f"/repos/{self.org}/{self.repo}/git/trees/HEAD", {"recursive": "1"})

        code_files = [
            e for e in tree.get("tree", [])
            if e["type"] == "blob"
            and Path(e["path"]).suffix.lower() in _CODE_EXTENSIONS
            and Path(e["path"]).suffix.lower() not in skip_extensions
        ]
        total = len(code_files)
        code_files = code_files[:max_files]
        print(f"Archivos de código encontrados: {total} (analizando {len(code_files)})")

        files = []
        for i, entry in enumerate(code_files):
            blob = self._rest(f"/repos/{self.org}/{self.repo}/git/blobs/{entry['sha']}")
            try:
                content = base64.b64decode(blob["content"]).decode("utf-8", errors="replace")
            except Exception:
                continue
            ext = Path(entry["path"]).suffix.lower()
            cloc, lloc = _count_lines(content, ext)
            files.append({"path": entry["path"], "cloc": cloc, "lloc": lloc})
            print(f"  ...{i + 1}/{len(code_files)} archivos analizados", end="\r")

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
        return (c.get("author") or {}).get("login") \
            or (c.get("commit", {}).get("author") or {}).get("name") \
            or "desconocido"

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        total_cloc = sum(f["cloc"] for f in self.files)
        total_lloc = sum(f["lloc"] for f in self.files)
        if total_lloc == 0:
            return 0.0
        return round(total_cloc / total_lloc, 4)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        by_author: dict[str, list[int]] = {}
        total = len(self.files)
        for i, f in enumerate(self.files):
            login = self._fetch_last_author(f["path"])
            by_author.setdefault(login, [0, 0])
            by_author[login][0] += f["cloc"]
            by_author[login][1] += f["lloc"]
            print(f"  ...{i + 1}/{total} archivos con autor resuelto", end="\r")
        print()

        result = {}
        for login, (cloc, lloc) in by_author.items():
            result[login] = round(cloc / lloc, 4) if lloc > 0 else 0.0

        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto",
            max_files: int = 500):
        self.fetch(max_files=max_files)
        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"{'Colaborador':<30} CD")
            print("-" * 40)
            for login, cd in resultado.items():
                print(f"{login:<30} {cd}")
        else:
            cd = self.por_producto(fecha_inicio, fecha_fin)
            print(f"\nCD (Comment Density): {cd}  (ref. NASA óptimo ≈ 0.15)")