import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric


def calcular_schedule_compliance(metadata_milestone: dict) -> float:
    """
    Calcula el Schedule Compliance (Cumplimiento de Programación).

    Esta métrica de Proceso evalúa la capacidad del equipo para entregar
    los compromisos adquiridos en un tiempo pactado. Según el Systematic
    Mapping Study de Colakoglu et al. (2021), el SPI es una de las métricas
    de gestión de proyectos más citadas en la literatura.

    metadata_milestone: Diccionario obtenido del endpoint
        /repos/:owner/:repo/milestones de GitHub, con:
        - 'open_issues': cantidad de tareas aún pendientes en el hito.
        - 'closed_issues': cantidad de tareas ya finalizadas.

    Retorna: Float entre 0.0 y 1.0. 1.0 indica cumplimiento del 100%
    de las tareas planificadas para el hito.
    """
    # Extraemos los datos del hito (milestone)
    tareas_abiertas = metadata_milestone.get("open_issues", 0)
    tareas_cerradas = metadata_milestone.get("closed_issues", 0)

    # El trabajo total planificado (Planned Value en términos de unidades de trabajo)
    tareas_totales = tareas_abiertas + tareas_cerradas

    # Validación de división por cero si el hito no tiene tareas asignadas
    if tareas_totales == 0:
        return 0.0

    # El cumplimiento (Schedule Compliance) se define como el progreso real
    # frente al planificado. En gestión de proyectos, esto equivale al SPI.
    # SPI = Earned Value (tareas cerradas) / Planned Value (tareas totales)
    compliance_score = tareas_cerradas / tareas_totales

    # Se retorna el valor redondeado para facilitar su uso en tableros de control
    return round(compliance_score, 4)


class ScheduleCompliance(GitHubMetric):
    """
    Schedule Compliance (Cumplimiento de Plazos de Entrega).
    Mide la eficiencia del cronograma comparando el trabajo completado contra
    el trabajo planificado para cada hito (milestone) del repositorio.
    Solo aplica por producto: los milestones son un artefacto de gestión del
    repositorio, no de un desarrollador individual (el algoritmo original no
    recibe ningún dato de autoría por tarea).
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.milestones: list[dict] = []

    def fetch(self):
        print("Obteniendo milestones...")
        milestones, page = [], 1
        while True:
            data = self._rest(
                f"/repos/{self.org}/{self.repo}/milestones",
                {"state": "all", "per_page": 100, "page": page},
            )
            if not data:
                break
            milestones.extend(data)
            print(f"  ...{len(milestones)} milestones descargados", end="\r")
            if len(data) < 100:
                break
            page += 1
        print()
        self.milestones = milestones

    def _milestones_en_periodo(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[dict]:
        en_periodo = []
        for m in self.milestones:
            fecha_raw = m.get("due_on") or m.get("created_at")
            if not fecha_raw:
                continue
            fecha = datetime.fromisoformat(fecha_raw.replace("Z", "+00:00"))
            if fecha_inicio <= fecha <= fecha_fin:
                en_periodo.append(m)
        return en_periodo

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        milestones = self._milestones_en_periodo(fecha_inicio, fecha_fin)
        if not milestones:
            return 0.0
        scores = [calcular_schedule_compliance(m) for m in milestones]
        return round(sum(scores) / len(scores), 4)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError(
            "Schedule Compliance es una métrica por producto/proceso, no aplica por persona: "
            "el algoritmo opera sobre metadata del milestone (open_issues/closed_issues), "
            "sin atribución a un desarrollador."
        )

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        if por == "persona":
            print("Schedule Compliance no aplica por persona: es una métrica por producto/proceso.")
            return
        self.fetch()
        milestones = self._milestones_en_periodo(fecha_inicio, fecha_fin)
        if not milestones:
            print("No se encontraron milestones en el período.")
            return

        print(f"\n{'Milestone':<35} {'Cerradas':>9} {'Abiertas':>9} {'Compliance':>11}")
        print("-" * 68)
        for m in milestones:
            score = calcular_schedule_compliance(m)
            print(f"{m['title']:<35} {m['closed_issues']:>9} {m['open_issues']:>9} {score:>11}")

        promedio = self.por_producto(fecha_inicio, fecha_fin)
        print("-" * 68)
        print(f"Schedule Compliance promedio del repositorio: {promedio}")
