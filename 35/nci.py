import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_metric import GitHubMetric
from issues_comun import descargar_issues


class NumberOfClosedIssues(GitHubMetric):
    """NCI: cantidad de issues cerradas en la ventana.

    A nivel producto ahora descarta los cierres de bots (el bot de issues inactivas y las
    issues cerradas sin actor registrado): en next.js eran el 23 % de los cierres en 2022,
    el 31 % en 2024 y el 68 % en 2025. NumberOfClosedIssuesConBots conserva el conteo
    original, porque el bot es parte de la política del proyecto.

    Las consignas 40 y 43 reexportan esta misma clase (nci_reuse.py, nci_reuse_43.py), así
    que el filtro también corrige el NCI de Proceso.
    """

    incluir_bots = False

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.issues: list[dict] = []

    def fetch(self, con_actor: bool = False):
        # con_actor se mantiene por compatibilidad: la descarga común siempre trae el actor.
        self.issues = [i for i in descargar_issues(self) if i["closed_at"]]

    def _cerrador_es_bot(self, issue: dict) -> bool:
        return self._es_bot(issue["closed_by"] or "desconocido")

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return sum(
            1 for i in self.issues
            if fecha_inicio <= i["closed_at"] <= fecha_fin
            and (self.incluir_bots or not self._cerrador_es_bot(i))
        )

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        conteo: dict[str, int] = {}
        for i in self.issues:
            if fecha_inicio <= i["closed_at"] <= fecha_fin and not self._cerrador_es_bot(i):
                conteo[i["closed_by"]] = conteo.get(i["closed_by"], 0) + 1
        return dict(sorted(conteo.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto"):
        self.fetch()
        print(f"Issues cerradas descargadas: {len(self.issues)}\n")
        if por == "persona":
            conteo = self.por_persona(fecha_inicio, fecha_fin)
            print(f"{'Colaborador':<30} NCI")
            print("-" * 40)
            for login, nci in conteo.items():
                print(f"{login:<30} {nci}")
            print("-" * 40)
            print(f"{'Total':<30} {sum(conteo.values())}")
        else:
            print(f"NCI (Number of Closed Issues): {self.por_producto(fecha_inicio, fecha_fin)}")


class NumberOfClosedIssuesConBots(NumberOfClosedIssues):
    """NCI original, con los cierres de bots. Por persona igual descarta bots."""
    incluir_bots = True
