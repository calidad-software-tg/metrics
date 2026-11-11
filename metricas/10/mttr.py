import statistics
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from base_metric import GitHubMetric
from issues_comun import descargar_issues, tiene_etiqueta

# Mismo criterio de "bug" que CFDR (27/cfdr.py): etiqueta o tipo de issue completo.
_NOMBRES_BUG = {"bug", "defect", "error", "fault", "flaw", "regression"}


class MeanTimeToRepair(GitHubMetric):
    """MTTR: tiempo entre la apertura y el cierre (horas) de las issues cerradas en la ventana.

    Cambios respecto de la versión original:
    - Filtra bots también a nivel producto: el bot de issues inactivas cierra issues
      viejas (en 2025, el 68 % de los cierres de next.js) y disparaba el promedio.
      Las issues cerradas sin actor registrado cuentan como cierre automático.
    - Devuelve None (no observable) cuando no se cerró ninguna issue, en vez de 0.
    - Por persona no cuenta los autocierres (quien cerró es quien abrió la issue): la
      mediana entre colaboradores la dominaban usuarios ocasionales cerrando rápido
      sus propias issues, no reparaciones del equipo.

    Variantes (clases de abajo): mediana en vez de promedio, solo bugs, y con bots.
    """

    estadistico = "promedio"   # "promedio" | "mediana"
    incluir_bots = False
    solo_bugs = False

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.issues: list[dict] = []

    def fetch(self, con_actor: bool = False):
        # con_actor se mantiene por compatibilidad: la descarga común siempre trae el actor.
        self.issues = [i for i in descargar_issues(self) if i["closed_at"] and i["created_at"]]

    def _issues_en_rango(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[dict]:
        res = []
        for i in self.issues:
            if not (fecha_inicio <= i["closed_at"] <= fecha_fin):
                continue
            if self.solo_bugs and not tiene_etiqueta(i["labels"], i["tipo"], _NOMBRES_BUG):
                continue
            if not self.incluir_bots and (self._es_bot(i["closed_by"] or "desconocido")
                                          or self._es_bot(i["author"])):
                continue
            res.append(i)
        return res

    def _resumir(self, horas: list[float]) -> float | None:
        if not horas:
            return None
        valor = statistics.median(horas) if self.estadistico == "mediana" else sum(horas) / len(horas)
        return round(valor, 2)

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float | None:
        horas = [(i["closed_at"] - i["created_at"]).total_seconds() / 3600
                 for i in self._issues_en_rango(fecha_inicio, fecha_fin)]
        return self._resumir(horas)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        by_actor: dict[str, list[float]] = {}
        for i in self._issues_en_rango(fecha_inicio, fecha_fin):
            login = i["closed_by"] or "desconocido"
            if self._es_bot(login) or login == i["author"]:
                continue
            by_actor.setdefault(login, []).append((i["closed_at"] - i["created_at"]).total_seconds() / 3600)
        result = {login: self._resumir(t) for login, t in by_actor.items()}
        return dict(sorted(result.items(), key=lambda x: x[1]))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto"):
        self.fetch()
        print(f"Issues cerradas descargadas: {len(self.issues)}\n")
        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"{'Colaborador':<30} MTTR (horas)")
            print("-" * 46)
            for login, mttr in resultado.items():
                print(f"{login:<30} {mttr}")
        else:
            print(f"MTTR (Mean Time to Repair): {self.por_producto(fecha_inicio, fecha_fin)} horas")


class MeanTimeToRepairMediana(MeanTimeToRepair):
    """MTTR con la mediana de las issues en vez del promedio: el promedio lo dominan las
    pocas issues muy viejas que se cierran cuando se limpia el backlog."""
    estadistico = "mediana"


class MeanTimeToRepairBugs(MeanTimeToRepair):
    """MTTR solo de las issues clasificadas como bug (etiqueta o tipo de issue)."""
    solo_bugs = True


class MeanTimeToRepairConBots(MeanTimeToRepair):
    """MTTR original: incluye los cierres de bots (el bot de inactivas es parte de la
    política del proyecto). Por persona igual descarta bots y autocierres."""
    incluir_bots = True
