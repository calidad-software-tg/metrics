import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric
from issues_comun import descargar_issues, tiene_etiqueta

# Nombres completos de etiqueta o tipo de issue de documentación. Antes se buscaban
# como subcadena ('doc' dentro de 'Docker' contaba como documentación).
_NOMBRES_DOC = {"doc", "docs", "documentation", "documentación", "documentacion"}


def _is_doc(labels: list[str], tipo: str | None = None, solo_etiquetas: bool = False) -> bool:
    """¿Es un issue de documentación? Alguna etiqueta es exactamente de documentación
    (ignorando prefijos como 'type:' o 'kind:'), o, salvo solo_etiquetas, el tipo de issue
    de GitHub ('Documentation'), que next.js usa en lugar de la etiqueta desde 2025."""
    return tiene_etiqueta(labels, tipo, _NOMBRES_DOC, solo_etiquetas)


class DocIssueSurvival(GitHubMetric):
    """DIS: días promedio entre la apertura y el cierre de las issues de documentación
    cerradas en la ventana.

    Cambios: comparación exacta de etiquetas; None (no observable) cuando no hay issues de
    documentación también con solo_etiquetas (antes devolvía 0, y la corrida de next.js con
    --solo-etiquetas dejó el 80 % de las ventanas en 0); y a nivel producto descarta los
    cierres de bots, igual que por persona.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.issues: list[dict] = []  # [{days, actor, cierre}]
        self.solo_etiquetas = False

    def fetch(self, con_actor: bool = False, solo_etiquetas: bool = False, **kwargs):
        self.solo_etiquetas = solo_etiquetas
        issues = []
        for i in descargar_issues(self):
            if not i["closed_at"] or not _is_doc(i["labels"], i["tipo"], solo_etiquetas):
                continue
            issues.append({"days": (i["closed_at"] - i["created_at"]).days,
                           "actor": i["closed_by"] or "desconocido",
                           "cierre": i["closed_at"]})
        self.issues = issues
        print(f"Issues de documentación cerradas: {len(issues)}")

    def _issues_en_rango(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[dict]:
        return [i for i in self.issues
                if fecha_inicio <= i["cierre"] <= fecha_fin and not self._es_bot(i["actor"])]

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float | None:
        incidencias = self._issues_en_rango(fecha_inicio, fecha_fin)
        if not incidencias:
            return None  # sin issues de documentación cerradas: no observable
        return round(sum(i["days"] for i in incidencias) / len(incidencias), 2)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        by_actor: dict[str, list[int]] = {}
        for i in self._issues_en_rango(fecha_inicio, fecha_fin):
            by_actor.setdefault(i["actor"], []).append(i["days"])
        result = {login: round(sum(d) / len(d), 2) for login, d in by_actor.items()}
        return dict(sorted(result.items(), key=lambda x: x[1]))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto",
            solo_etiquetas: bool = False, **kwargs):
        self.fetch(solo_etiquetas=solo_etiquetas)
        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            if not resultado:
                print("No se encontraron issues de documentación cerradas.")
                return
            print(f"{'Colaborador':<30} DIS (días)")
            print("-" * 45)
            for login, days in resultado.items():
                print(f"{login:<30} {days}")
        else:
            avg = self.por_producto(fecha_inicio, fecha_fin)
            if avg is None:
                print("No se encontraron issues de documentación cerradas.")
                return
            print(f"DIS (Doc Issue Survival): {avg} días promedio")
