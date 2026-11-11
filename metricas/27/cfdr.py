import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric, es_bot

_QUERY_ISSUES = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 50, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        author { login }
        createdAt
        labels(first: 20) { nodes { name } }
        issueType { name }
      }
    }
  }
}
"""

# Etiquetas identificadas en la literatura para errores y regresiones
# de post-lanzamiento.
KEYWORDS_ERROR = {"bug", "defect", "error", "fault", "flaw", "regression"}


def _es_defecto(issue: dict, solo_etiquetas: bool = False) -> bool:
    """¿El issue está clasificado como error o regresión?

    Algoritmo original: alguna etiqueta coincide con KEYWORDS_ERROR.
    Además (salvo solo_etiquetas): el tipo de issue de GitHub ('Bug'), que algunos
    proyectos usan en lugar de la etiqueta. next.js pasó de la etiqueta 'bug' al
    tipo 'Bug' en 2025; en repos sin tipos de issue el resultado no cambia.
    """
    # Normalizamos etiquetas para una búsqueda robusta
    etiquetas = {et.lower() for et in issue.get("labels", [])}
    if any(key in etiquetas for key in KEYWORDS_ERROR):
        return True
    if solo_etiquetas:
        return False
    return (issue.get("tipo") or "").lower() in KEYWORDS_ERROR


def calcular_customer_defects_and_regressions(metadata_issues: list[dict], lista_core_team: set,
                                              solo_etiquetas: bool = False) -> int | None:
    """
    Calcula los defectos y regresiones encontrados por el cliente.

    Esta métrica de Producto y Proceso mide la calidad del software desde la
    perspectiva del usuario final. Un valor alto sugiere una baja eficiencia
    en la eliminación de defectos (DRE) previa al lanzamiento.

    metadata_issues: Lista de diccionarios, cada uno con 'user_login',
        'labels' (lista de strings), 'tipo' (tipo de issue o None) y 'created_at'.
    lista_core_team: Set de logins identificados como equipo principal
        o contribuyentes frecuentes (Surgical Team).
    solo_etiquetas: True reproduce el algoritmo original (solo etiquetas, y 0
        cuando no hay ningún issue clasificado).

    Retorna: suma de incidentes de tipo bug o regresión reportados por no-miembros.
    None si ningún issue del período está clasificado como defecto: el proyecto
    no marcaba sus bugs (no observable), que no es lo mismo que cero bugs.
    """
    conteo_customer_defects = 0
    clasificados = 0

    for issue in metadata_issues:
        reportero = issue.get("user_login")
        if es_bot(reportero):
            continue  # issues abiertas por bots: no son reportes de usuarios

        # 1. Criterio de tipo: ¿Es un error o una regresión?
        es_defecto = _es_defecto(issue, solo_etiquetas)
        clasificados += es_defecto

        # 2. Criterio de rol: ¿El informante es externo (cliente)?
        # Se excluyen reportes de desarrolladores que eventualmente fueron
        # parte del equipo para evitar sesgos de "internal testing".
        es_externo = reportero not in lista_core_team

        if es_defecto and es_externo:
            conteo_customer_defects += 1

    if clasificados == 0 and not solo_etiquetas:
        return None
    return conteo_customer_defects


class CustomerFoundDefectsAndRegressions(GitHubMetric):
    """
    Customer-Found Defects and Regressions (CFDR).
    Cuantifica el volumen de errores y regresiones reportados por usuarios
    externos al equipo principal tras una liberación. Solo aplica por producto:
    el algoritmo agrega incidentes a nivel repositorio, no por desarrollador
    (los desarrolladores son justamente el grupo que se excluye del conteo).
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.issues: list[dict] = []  # {user_login, labels, tipo, created_at}
        self.core_team: set = set()
        self.core_team_size = 10
        self.commits: list[tuple] = []  # (fecha, login) de toda la historia, para el equipo por ventana
        self._equipo_cache: dict = {}
        self.solo_etiquetas = False
        # True: el equipo es el top 10 de contribuidores hasta el cierre de cada ventana.
        # False: el top 10 de hoy aplicado a toda la historia (algoritmo original).
        self.equipo_historico = True

    def fetch(self, core_team_size: int = 10, solo_etiquetas: bool = False):
        self.solo_etiquetas = solo_etiquetas
        self.core_team_size = core_team_size
        print("Obteniendo equipo principal (core team)...")
        contributors = self._rest(
            f"/repos/{self.org}/{self.repo}/contributors",
            {"per_page": core_team_size},
        )
        self.core_team = {c["login"] for c in contributors[:core_team_size]}
        print(f"Core team de hoy ({len(self.core_team)}): {sorted(self.core_team)}")

        if self.equipo_historico:
            # Autores de todos los commits de la rama principal, para armar el top 10 de
            # cada ventana con los commits hechos hasta su cierre.
            print("Obteniendo autores de commits (equipo por ventana)...")
            page, commits = 1, []
            while True:
                data = self._rest(f"/repos/{self.org}/{self.repo}/commits", {"per_page": 100, "page": page})
                if not data:
                    break
                for c in data:
                    login = (c.get("author") or {}).get("login")
                    fecha = (c.get("commit", {}).get("author") or {}).get("date")
                    if login and fecha and not es_bot(login):
                        commits.append((datetime.fromisoformat(fecha.replace("Z", "+00:00")), login))
                print(f"  ...{len(commits)} commits", end="\r")
                if len(data) < 100:
                    break
                page += 1
            print()
            self.commits = sorted(commits)

        print("Obteniendo issues...")
        issues, cursor, page = [], None, 0
        while True:
            page += 1
            data = self._graphql(_QUERY_ISSUES, {"owner": self.org, "name": self.repo, "after": cursor})
            conexion = data["data"]["repository"]["issues"]
            print(f"  ...issues página {page} ({len(issues)} acumulados)", end="\r")
            for node in conexion["nodes"]:
                created = datetime.fromisoformat(node["createdAt"].replace("Z", "+00:00"))
                login = (node.get("author") or {}).get("login", "desconocido")
                labels = [l["name"] for l in node.get("labels", {}).get("nodes", [])]
                tipo = (node.get("issueType") or {}).get("name")
                issues.append({"user_login": login, "labels": labels, "tipo": tipo, "created_at": created})
            if not conexion["pageInfo"]["hasNextPage"]:
                break
            cursor = conexion["pageInfo"]["endCursor"]
        print()
        self.issues = issues

    def _equipo(self, fecha_fin: datetime) -> set:
        """Top `core_team_size` de contribuidores por commits hechos hasta fecha_fin."""
        if not self.equipo_historico or not self.commits:
            return self.core_team
        if fecha_fin not in self._equipo_cache:
            conteo: dict[str, int] = {}
            for fecha, login in self.commits:
                if fecha > fecha_fin:
                    break
                conteo[login] = conteo.get(login, 0) + 1
            top = sorted(conteo.items(), key=lambda x: x[1], reverse=True)[: self.core_team_size]
            self._equipo_cache[fecha_fin] = {login for login, _ in top}
        return self._equipo_cache[fecha_fin]

    def _issues_en_periodo(self, fecha_inicio: datetime, fecha_fin: datetime) -> list[dict]:
        return [i for i in self.issues if fecha_inicio <= i["created_at"] <= fecha_fin]

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int | None:
        issues_periodo = self._issues_en_periodo(fecha_inicio, fecha_fin)
        return calcular_customer_defects_and_regressions(issues_periodo, self._equipo(fecha_fin),
                                                         self.solo_etiquetas)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError(
            "CFDR es una métrica por producto/proceso, no aplica por persona: "
            "cuantifica incidentes reportados por usuarios externos al equipo, "
            "no atribuibles a un desarrollador del proyecto."
        )

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto",
            core_team_size: int = 10, solo_etiquetas: bool = False, **kwargs):
        if por == "persona":
            print("CFDR no aplica por persona: es una métrica por producto/proceso.")
            return
        self.fetch(core_team_size=core_team_size, solo_etiquetas=solo_etiquetas)
        issues_periodo = self._issues_en_periodo(fecha_inicio, fecha_fin)
        if not issues_periodo:
            print("No se encontraron issues en el período.")
            return

        detalle = [
            i for i in issues_periodo
            if _es_defecto(i, self.solo_etiquetas) and i["user_login"] not in self.core_team
        ]

        if detalle:
            print(f"\n{'Reportero':<25} {'Etiquetas / tipo':<30} Fecha")
            print("-" * 70)
            for i in detalle:
                marcas = ", ".join(i["labels"] + ([f"tipo: {i['tipo']}"] if i.get("tipo") else []))
                print(f"{i['user_login']:<25} {marcas:<30} {i['created_at'].date()}")

        cfdr = calcular_customer_defects_and_regressions(issues_periodo, self.core_team, self.solo_etiquetas)
        if cfdr is None:
            print("Ningún issue del período está clasificado como defecto (no observable).")
            return
        print("-" * 70)
        print(f"CFDR (Customer-Found Defects and Regressions): {cfdr}")
