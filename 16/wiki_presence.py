import subprocess
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

_CLONES = Path(__file__).resolve().parent.parent / ".clones"


class WikiPresence(GitHubMetric):
    """
    Métrica binaria: 1 si el repo tenía wiki en ese momento, 0 si no.
    Proxy de Documentation Quality (Jarczyk et al., 2014). Solo aplica por producto.

    La versión original tomaba el estado de HOY (has_wiki y no fork) y lo repetía en todas
    las ventanas. La API de GitHub no guarda la historia de si la wiki estuvo habilitada,
    pero la wiki es un repositorio git aparte ({repo}.wiki): si existe, su historial de
    commits dice cuándo tuvo contenido. Para cada ventana, vale 1 si al cierre de la
    ventana la wiki ya tenía contenido y, si hoy está deshabilitada, si todavía no había
    pasado su último commit (no se sabe cuándo se deshabilitó; el último commit es el
    último momento en que se sabe que estaba en uso). Si el repo de la wiki no existe,
    vale 0 en todas las ventanas.

    En next.js la wiki tuvo 167 commits entre octubre de 2016 y enero de 2020, y hoy
    está deshabilitada.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self._meta: dict = {}
        self._primer_commit_wiki: datetime | None = None
        self._ultimo_commit_wiki: datetime | None = None

    def _historia_wiki(self) -> tuple[datetime | None, datetime | None]:
        """(primer commit, último commit) del repo de la wiki, o (None, None) si no existe."""
        url = f"https://github.com/{self.org}/{self.repo}.wiki.git"
        r = subprocess.run(["git", "ls-remote", url], capture_output=True, text=True)
        if r.returncode != 0 or not r.stdout.strip():
            return None, None
        dest = _CLONES / f"{self.repo}.wiki.git"
        if dest.exists():
            subprocess.run(["git", "-C", str(dest), "fetch", "--quiet"], capture_output=True)
        else:
            _CLONES.mkdir(exist_ok=True)
            subprocess.run(["git", "clone", "--quiet", "--bare", url, str(dest)], capture_output=True)
        r = subprocess.run(["git", "-C", str(dest), "log", "--reverse", "--format=%aI"],
                           capture_output=True, text=True)
        fechas = r.stdout.split()
        if not fechas:
            return None, None
        return datetime.fromisoformat(fechas[0]), datetime.fromisoformat(fechas[-1])

    def fetch(self, **kwargs):
        self._meta = self._rest(f"/repos/{self.org}/{self.repo}")
        self._primer_commit_wiki, self._ultimo_commit_wiki = self._historia_wiki()
        if self._primer_commit_wiki:
            print(f"Wiki con commits entre {self._primer_commit_wiki.date()} y {self._ultimo_commit_wiki.date()}"
                  f" (hoy {'habilitada' if self._meta.get('has_wiki') else 'deshabilitada'})")
        else:
            print("El repositorio de la wiki no existe: Wiki Presence vale 0 en todas las ventanas.")

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        if self._meta.get("fork", False) or self._primer_commit_wiki is None:
            return 0
        if fecha_fin < self._primer_commit_wiki:
            return 0
        if not self._meta.get("has_wiki", False) and fecha_fin > self._ultimo_commit_wiki:
            return 0
        return 1

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError("Wiki Presence es un atributo del repo, no aplica por persona.")

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        if por == "persona":
            return
        self.fetch()
        print(f"Wiki Presence al {fecha_fin.date()}: {self.por_producto(fecha_inicio, fecha_fin)}")
