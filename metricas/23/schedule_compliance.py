import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

_QUERY_MILESTONES = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    milestones(first: 50, after: $after, states: [OPEN, CLOSED]) {
      pageInfo { hasNextPage endCursor }
      nodes { number title dueOn createdAt }
    }
  }
}
"""

_QUERY_ISSUES_MILESTONE = """
query($owner: String!, $name: String!, $number: Int!, $after: String) {
  repository(owner: $owner, name: $name) {
    milestone(number: $number) {
      issues(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes { closedAt }
      }
    }
  }
}
"""


def _fecha(raw):
    return datetime.fromisoformat(raw.replace("Z", "+00:00")) if raw else None


def compliance_a_tiempo(milestone: dict) -> float | None:
    """Parte de las issues del milestone que se cerró antes de su fecha límite.

    La versión original (calcular_schedule_compliance) usa open_issues/closed_issues de
    hoy, no al vencer el plazo, y no compara con la fecha límite: un milestone terminado
    con atraso contaba como cumplido (en next.js valía 1,0 en 39 de 41 milestones)."""
    cierres = milestone.get("cierres", [])
    if not cierres or not milestone.get("due_on"):
        return None
    a_tiempo = sum(1 for c in cierres if c is not None and c <= milestone["due_on"])
    return round(a_tiempo / len(cierres), 4)


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
        milestones, cursor = [], None
        while True:
            data = self._graphql(_QUERY_MILESTONES, {"owner": self.org, "name": self.repo, "after": cursor})
            con = data["data"]["repository"]["milestones"]
            for m in con["nodes"]:
                milestones.append({"number": m["number"], "title": m["title"],
                                   "due_on": _fecha(m.get("dueOn")), "created_at": _fecha(m.get("createdAt"))})
            if not con["pageInfo"]["hasNextPage"]:
                break
            cursor = con["pageInfo"]["endCursor"]
        # Fecha de cierre de cada issue de los milestones con fecha límite.
        for m in milestones:
            if not m["due_on"]:
                continue
            cierres, cursor = [], None
            while True:
                data = self._graphql(_QUERY_ISSUES_MILESTONE, {"owner": self.org, "name": self.repo,
                                                               "number": m["number"], "after": cursor})
                con = data["data"]["repository"]["milestone"]["issues"]
                cierres.extend(_fecha(n.get("closedAt")) for n in con["nodes"])
                if not con["pageInfo"]["hasNextPage"]:
                    break
                cursor = con["pageInfo"]["endCursor"]
            m["cierres"] = cierres
        print(f"Milestones: {len(milestones)} ({sum(1 for m in milestones if m['due_on'])} con fecha límite)")
        self.milestones = milestones

    def _milestones_en_periodo(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[dict]:
        """Milestones cuya fecha límite cae en la ventana (los que no tienen fecha límite no
        se pueden evaluar: no hay plazo con el cual comparar)."""
        return [m for m in self.milestones if m["due_on"] and fecha_inicio <= m["due_on"] <= fecha_fin]

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float | None:
        scores = [c for c in (compliance_a_tiempo(m) for m in self._milestones_en_periodo(fecha_inicio, fecha_fin))
                  if c is not None]
        if not scores:
            # Sin milestones con fecha límite la ventana no es observable (next.js dejó de
            # usarlos alrededor de 2020): None, no 0.0, que se leería como incumplimiento.
            return None
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

        print(f"\n{'Milestone':<35} {'Fecha límite':>12} {'Issues':>7} {'A tiempo':>9}")
        print("-" * 68)
        for m in milestones:
            print(f"{m['title']:<35} {m['due_on'].date().isoformat():>12} {len(m.get('cierres', [])):>7} "
                  f"{compliance_a_tiempo(m)!s:>9}")

        promedio = self.por_producto(fecha_inicio, fecha_fin)
        print("-" * 68)
        print(f"Schedule Compliance promedio del repositorio: {promedio}")
