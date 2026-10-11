import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric
from issues_comun import descargar_issues




def calcular_nci(metadata_issues: list[dict], fecha_inicio: datetime, fecha_fin: datetime) -> int:
    """
    Calcula el Number of Closed Issues (NCI).

    Esta métrica de Proceso mide la capacidad de resolución del equipo.
    Según Jarczyk et al. (2014), el cierre de problemas es un indicador
    crítico de la calidad del soporte técnico.

    metadata_issues: Lista de diccionarios con 'closed_at' (datetime) y
        'state' ('closed').
    fecha_inicio, fecha_fin: Ventana temporal de observación para el
        conteo de éxitos.

    Retorna: Int, conteo de problemas que alcanzaron el estado 'closed'
    en el período.
    """
    nci_total = 0

    for issue in metadata_issues:
        fecha_cierre = issue.get("closed_at")
        estado = issue.get("state")

        # Criterio de Jarczyk: un issue se cuenta si su fecha de cierre
        # cae dentro del intervalo de análisis.
        if estado == "closed" and fecha_cierre:
            if fecha_inicio <= fecha_cierre <= fecha_fin:
                nci_total += 1

    return nci_total


def calcular_tasa_exito_jarczyk(nci_total: int, total_issues: int) -> float:
    """
    Calcula la proporción de éxito base para el modelo de regresión binomial.
    Referencia: n1 = n * pt.

    Esta proporción es la variable dependiente en los modelos de Jarczyk:
    el componente de "éxitos" necesario para calcular la probabilidad de
    supervivencia del problema a 3 y 365 días.
    """
    if total_issues == 0:
        return 0.0

    return round(nci_total / total_issues, 4)


class JarczykSuccessRate(GitHubMetric):
    """
    Tasa de Éxito de Jarczyk (n1 = n * pt).
    Proporción de issues cerrados sobre el total de issues observados en el
    período — el componente de "éxitos" del modelo de regresión binomial de
    Jarczyk et al. para estimar la probabilidad de supervivencia de un
    problema a 3 y 365 días. Solo aplica por producto.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.issues: list[dict] = []  # {created_at, closed_at, state}

    def fetch(self):
        # Descarga común (issues_comun.py). Se descartan las issues abiertas por bots, y
        # las que cerró un bot (o se cerraron sin actor) no cuentan como éxito: el bot de
        # issues inactivas las cierra sin que nadie las haya resuelto.
        self.issues = []
        for i in descargar_issues(self):
            if self._es_bot(i["author"]):
                continue
            cerro_bot = i["closed_at"] is not None and self._es_bot(i["closed_by"] or "desconocido")
            self.issues.append({
                "created_at": i["created_at"],
                "closed_at": None if cerro_bot else i["closed_at"],
                "state": "open" if cerro_bot else i["state"],
            })

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float | None:
        # Población total: issues creados dentro del período observado
        # (mismo universo usado en Development Process Performance, consigna 40).
        total_issues, nci_total = self._n_y_n1(fecha_inicio, fecha_fin)
        if total_issues == 0:
            return None  # ventana sin issues creados: no observable (NULL, no 0.0)
        return calcular_tasa_exito_jarczyk(nci_total, total_issues)

    def _n_y_n1(self, fecha_inicio: datetime, fecha_fin: datetime) -> tuple[int, int]:
        """n = issues creados en la ventana; n1 = de ESOS, los cerrados antes de fecha_fin.

        n1 tiene que ser un subconjunto de n (éxitos de n ensayos binomiales). Antes
        n1 era calcular_nci() sobre todo el repo (cierres en la ventana de issues
        creados en cualquier fecha): en ventanas cortas (next.js, releases del mismo
        día) cerraban más issues viejos de los que se creaban y la tasa daba > 1.
        """
        creados = [i for i in self.issues if fecha_inicio <= i["created_at"] <= fecha_fin]
        return len(creados), calcular_nci(creados, fecha_inicio, fecha_fin)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError(
            "La tasa de éxito de Jarczyk es una métrica por producto/proceso, "
            "no aplica por persona: opera sobre el universo de issues del "
            "repositorio, sin atribución a un desarrollador."
        )

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        if por == "persona":
            print("La tasa de éxito de Jarczyk no aplica por persona: es una métrica por producto/proceso.")
            return
        self.fetch()
        if not self.issues:
            print("No se encontraron issues.")
            return

        total_issues, nci_total = self._n_y_n1(fecha_inicio, fecha_fin)
        tasa = calcular_tasa_exito_jarczyk(nci_total, total_issues)

        print(f"\nIssues creados en el período (n, población total): {total_issues}")
        print(f"De esos, cerrados en el período (n1, éxitos):      {nci_total}")
        print(f"Tasa de éxito (pt = n1 / n): {tasa}")
