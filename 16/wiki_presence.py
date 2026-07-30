import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric


class WikiPresence(GitHubMetric):
    """
    Métrica binaria: 1 si el repo tiene Wiki habilitada y no es fork, 0 si no.
    Proxy de Documentation Quality (Jarczyk et al., 2014).
    Solo aplica por producto — es un atributo del repositorio, no de personas.
    """

    def fetch(self, **kwargs):
        self._meta = self._rest(f"/repos/{self.org}/{self.repo}")

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        has_wiki = self._meta.get("has_wiki", False)
        is_fork  = self._meta.get("fork", False)
        return 1 if (has_wiki and not is_fork) else 0

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError("Wiki Presence es un atributo del repo, no aplica por persona.")

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        if por == "persona":
            print("Wiki Presence no aplica por persona: es un atributo del repositorio.")
            return
        self.fetch()
        valor    = self.por_producto(fecha_inicio, fecha_fin)
        has_wiki = self._meta.get("has_wiki", False)
        is_fork  = self._meta.get("fork", False)
        print(f"WP (Wiki Presence): {valor}  (has_wiki={has_wiki}, fork={is_fork})")
        if valor == 1:
            print("→ El repositorio tiene Wiki habilitada y es un proyecto original.")
        elif has_wiki and is_fork:
            print("→ Wiki habilitada pero es un fork: no se considera presencia genuina.")
        else:
            print("→ El repositorio no tiene Wiki habilitada.")