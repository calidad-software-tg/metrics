import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric
from issues_comun import descargar_issues




class NumberOfOpenIssues(GitHubMetric):
    """
    Number of Open Issues (NOI) — Registro 28 — Jarczyk et al. (2018).

    Snapshot del backlog sin resolver al final de cada ventana de análisis:
    cuenta issues creados antes de fecha_fin que siguen abiertos o se cerraron
    después de fecha_fin. Fetch global (una sola vez para todas las ventanas)
    porque el histórico completo de issues es necesario para reconstruir el
    estado en cualquier punto del tiempo. Solo aplica por producto.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.issues: list[dict] = []

    def fetch(self):
        # Descarga común (issues_comun.py), sin las issues abiertas por bots, igual que NOI (40).
        self.issues = [{"created_at": i["created_at"], "closed_at": i["closed_at"]}
                       for i in descargar_issues(self) if not self._es_bot(i["author"])]
        print(f"Issues totales obtenidos (sin bots): {len(self.issues)}")

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        total = 0
        for issue in self.issues:
            ca = issue["created_at"]
            co = issue["closed_at"]
            if ca <= fecha_fin and (co is None or co > fecha_fin):
                total += 1
        return total

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError(
            "NOI (28) es una métrica por producto/proceso, no aplica por persona."
        )

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        if por == "persona":
            print("NOI (28) no aplica por persona: es una métrica por producto/proceso.")
            return
        self.fetch()
        noi = self.por_producto(fecha_inicio, fecha_fin)
        print(f"\nNOI (Number of Open Issues) al {fecha_fin.date()}: {noi}")
