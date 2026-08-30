import sys
import base64
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

# ATENCIÓN — MÉTRICA SIN CONSIGNA ASIGNADA TODAVÍA:
# Proviene del Notion "Número de Colaboradores, Número de Líneas de Código
# y Número de Branches". No confundir con Documented Lines of Code
# (metrics/16/dloc.py), que mide líneas de código DOCUMENTADAS (.md/.txt/.rst),
# no el tamaño total del código fuente del repositorio.
#
# Diferencia respecto al script original de Notion: acá se recorre el árbol
# del repo de forma RECURSIVA (git/trees/HEAD?recursive=1) y se filtra por
# extensiones de código fuente, en vez de solo mirar los archivos en la raíz
# del repo (limitación del script original, que subestimaría el conteo en
# cualquier proyecto con estructura de carpetas).

_CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".h", ".cpp", ".hpp",
    ".cc", ".cs", ".go", ".rb", ".php", ".swift", ".kt", ".kts", ".rs",
    ".scala", ".sh", ".bash", ".html", ".css", ".scss", ".sass", ".less",
    ".vue", ".dart", ".m", ".mm", ".sql", ".r", ".pl", ".lua", ".groovy",
    ".ex", ".exs", ".clj", ".hs", ".erl",
}

# Carpetas típicas de dependencias/artefactos generados: no son código
# "propio" del repo y distorsionarían el conteo si se incluyeran.
_EXCLUDED_DIR_PARTS = {
    "node_modules", "vendor", "dist", "build", ".git", "target",
    "venv", ".venv", "__pycache__", "coverage",
}


def _is_excluded(path: str) -> bool:
    parts = set(Path(path).parts)
    return bool(parts & _EXCLUDED_DIR_PARTS)


def _count_lines(content: str) -> int:
    return content.count("\n") + 1 if content else 0


class LinesOfCode(GitHubMetric):
    """
    Estimación de Líneas de Código (LOC) del repositorio.

    Cuenta las líneas de todos los archivos de código fuente (por extensión),
    excluyendo carpetas de dependencias/artefactos generados.

    Por persona: atribuye cada archivo COMPLETO a su último autor (mismo
    heurístico barato de "último en tocar el archivo" que ya usan
    metrics/16/dloc.py, cd.py y readme_completeness.py — un solo commit
    consultado por archivo). Es una aproximación, no precisión línea por
    línea: para eso está Developer Ownership (developer_ownership.py), que
    usa `git blame` real pero es mucho más costoso (una consulta GraphQL de
    blame por archivo en vez de una consulta REST liviana de "último commit
    de este path").
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.files: list[dict] = []  # [{path, lines}]

    def fetch(self, fecha_fin: datetime, max_files: int = 1000, **kwargs):
        print("Obteniendo árbol del repositorio (recursivo)...")
        ref = self._resolve_ref(fecha_fin)
        tree = self._rest(
            f"/repos/{self.org}/{self.repo}/git/trees/{ref}",
            {"recursive": "1"},
        )
        if tree.get("truncated"):
            print("  ADVERTENCIA: el árbol fue truncado por la API de GitHub "
                  "(repo muy grande); el conteo será parcial.", file=sys.stderr)

        code_files = [
            e for e in tree.get("tree", [])
            if e["type"] == "blob"
            and Path(e["path"]).suffix.lower() in _CODE_EXTENSIONS
            and not _is_excluded(e["path"])
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
            files.append({"path": entry["path"], "lines": _count_lines(content)})
            print(f"  ...{i + 1}/{len(code_files)} archivos procesados", end="\r")

        print()
        self.files = files

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

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return sum(f["lines"] for f in self.files)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        by_author: dict[str, int] = {}
        total = len(self.files)
        for i, f in enumerate(self.files):
            login = self._fetch_last_author(f["path"], fecha_fin)
            by_author[login] = by_author.get(login, 0) + f["lines"]
            print(f"  ...{i + 1}/{total} archivos con autor resuelto", end="\r")
        print()
        return dict(sorted(by_author.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto",
            max_files: int = 1000, **kwargs):
        self.fetch(fecha_fin, max_files=max_files)
        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"{'Colaborador':<30} LOC (por último autor del archivo)")
            print("-" * 55)
            for login, lineas in resultado.items():
                print(f"{login:<30} {lineas}")
        else:
            total = self.por_producto(fecha_inicio, fecha_fin)
            print(f"LOC (Lines of Code, estimado): {total} líneas en {len(self.files)} archivos")
