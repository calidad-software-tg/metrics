import math
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

_QUERY_BRANCHES = """
query($owner: String!, $repo: String!) {
  repository(owner: $owner, name: $repo) {
    refs(refPrefix: "refs/heads/") {
      totalCount
    }
  }
}
"""


class NumberOfBranches(GitHubMetric):
    """
    Number of Branches (NOB) — Jarczyk et al. (2014).

    Cuantifica la cantidad total de branches del repositorio. Según los
    autores, es el atributo más importante identificado en su estudio:
    un NOB alto correlaciona negativamente con la supervivencia de los
    bugs (soporte más rápido). Métrica de Producto/Proceso: no aplica
    por persona.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self._branches_count: int = 0

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, **kwargs):
        print("Obteniendo branches...")
        data = self._graphql(_QUERY_BRANCHES, {"owner": self.org, "repo": self.repo})
        self._branches_count = data["data"]["repository"]["refs"]["totalCount"]
        print(f"Branches totales obtenidas: {self._branches_count}")

    def calcular_nob(self, metadata_repositorio: dict) -> int:
        lista_ramas = metadata_repositorio.get("branches", [])
        nob_total = len(lista_ramas) if isinstance(lista_ramas, list) else 0

        if nob_total == 0:
            nob_total = metadata_repositorio.get("branches_count", 0)
        return nob_total

    def normalizar_nob_jarczyk(self, nob_total: int) -> float:
        """
        Transformación logarítmica propuesta por Jarczyk et al. (2014)
        para mitigar el sesgo en distribuciones de ley de potencia.
        Referencia: x' = log10(x + 10).
        """
        return round(math.log10(nob_total + 10), 4)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError("NOB es una métrica por producto, no aplica por persona.")

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, dict]:
        metadata_repositorio = {"branches_count": self._branches_count}
        nob_total = self.calcular_nob(metadata_repositorio)
        nob_normalizado = self.normalizar_nob_jarczyk(nob_total)
        return {
            self.repo: {
                "nob": nob_total,
                "nob_normalizado": nob_normalizado,
            }
        }

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        if por == "persona":
            print("Number of Branches no aplica por persona: es una métrica por producto.")
            return
        self.fetch(fecha_inicio, fecha_fin)
        resultado = self.por_producto(fecha_inicio, fecha_fin)
        for repo, d in resultado.items():
            print(f"\nRepositorio: {repo}")
            print(f"Number of Branches (NOB)         : {d['nob']}")
            print(f"NOB normalizado (Jarczyk log10)  : {d['nob_normalizado']}")