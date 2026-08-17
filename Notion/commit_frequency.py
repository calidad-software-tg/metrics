import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

# ATENCIÓN — MÉTRICA SIN CONSIGNA ASIGNADA TODAVÍA:
# Proviene del Notion "Commit Frequency". El script original agrupa commits
# por día (YYYY-MM-DD) y grafica un histograma con matplotlib.
#
# Diferencia respecto al original: acá se usa la consulta GraphQL de
# historial de commits (mismo patrón que metrics/10/anmcc.py) en vez de la
# API REST paginada manualmente, y se reportan estadísticos numéricos sobre
# la distribución (promedio, máximo, días con actividad) en vez de solo
# graficar — matplotlib no es una dependencia del resto del catálogo, así
# que el gráfico queda como opcional (se genera solo si matplotlib está
# instalado; si no, se omite sin romper la ejecución).

_GRAPHQL_QUERY = """
query($owner: String!, $name: String!, $after: String, $since: GitTimestamp, $until: GitTimestamp) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $after, since: $since, until: $until) {
            pageInfo { hasNextPage endCursor }
            nodes {
              oid
              committedDate
              author { user { login } name }
            }
          }
        }
      }
    }
  }
}
"""


class CommitFrequency(GitHubMetric):
    """
    Commit Frequency — cantidad de commits por día.

    Mide la actividad del repositorio a lo largo del tiempo agrupando los
    commits por fecha de autoría (día calendario). Producto: distribución
    completa + estadísticos agregados. Persona: misma distribución pero
    filtrada por autor.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.commits: list[dict] = []  # [{oid, date, author}]

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, **kwargs):
        commits = []
        cursor = None
        since = fecha_inicio.isoformat()
        until = fecha_fin.isoformat()

        while True:
            data = self._graphql(_GRAPHQL_QUERY, {
                "owner": self.org,
                "name": self.repo,
                "after": cursor,
                "since": since,
                "until": until,
            })
            history = data["data"]["repository"]["defaultBranchRef"]["target"]["history"]

            for node in history["nodes"]:
                author_node = node.get("author") or {}
                user = author_node.get("user") or {}
                commits.append({
                    "oid": node["oid"],
                    "date": node["committedDate"][:10],
                    "author": user.get("login") or author_node.get("name") or "desconocido",
                })

            if not history["pageInfo"]["hasNextPage"]:
                break
            cursor = history["pageInfo"]["endCursor"]
            print(f"  ...{len(commits)} commits descargados", end="\r")

        self.commits = commits

    def _distribucion(self, commits: list[dict]) -> dict[str, int]:
        contador = Counter(c["date"] for c in commits)
        return dict(sorted(contador.items()))

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict:
        distribucion = self._distribucion(self.commits)
        if not distribucion:
            return {"por_dia": {}, "avg_por_dia": 0.0, "max_por_dia": 0,
                     "dias_con_actividad": 0}
        valores = list(distribucion.values())
        return {
            "por_dia": distribucion,
            "avg_por_dia": round(sum(valores) / len(valores), 2),
            "max_por_dia": max(valores),
            "dias_con_actividad": len(distribucion),
        }

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, dict]:
        by_author: dict[str, list[dict]] = {}
        for c in self.commits:
            by_author.setdefault(c["author"], []).append(c)

        resultado = {}
        for login, commits in by_author.items():
            distribucion = self._distribucion(commits)
            valores = list(distribucion.values())
            resultado[login] = {
                "total_commits": len(commits),
                "avg_por_dia": round(sum(valores) / len(valores), 2) if valores else 0.0,
                "max_por_dia": max(valores) if valores else 0,
                "dias_con_actividad": len(distribucion),
            }
        return dict(sorted(resultado.items(), key=lambda x: x[1]["total_commits"], reverse=True))

    def _graficar(self, distribucion: dict[str, int]):
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            print("  (matplotlib no instalado: se omite el histograma)")
            return
        fechas, frecuencias = zip(*distribucion.items())
        plt.figure(figsize=(10, 6))
        plt.bar(fechas, frecuencias)
        plt.xlabel("Fecha")
        plt.ylabel("Número de Commits")
        plt.title(f"Frecuencia de Commits por Día — {self.org}/{self.repo}")
        plt.xticks(rotation=90)
        plt.tight_layout()
        out_path = Path(__file__).parent / f"commit_frequency_{self.repo}.png"
        plt.savefig(out_path)
        print(f"  Histograma guardado en {out_path}")

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto",
            graficar: bool = False, **kwargs):
        print(f"Descargando commits de {self.org}/{self.repo}...")
        self.fetch(fecha_inicio, fecha_fin)
        print(f"Commits descargados: {len(self.commits)}\n")

        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"{'Colaborador':<30} {'Total':>7} {'avg/día':>9} {'max/día':>9} {'días act.':>10}")
            print("-" * 68)
            for login, r in resultado.items():
                print(f"{login:<30} {r['total_commits']:>7} {r['avg_por_dia']:>9} "
                      f"{r['max_por_dia']:>9} {r['dias_con_actividad']:>10}")
        else:
            r = self.por_producto(fecha_inicio, fecha_fin)
            print(f"Promedio de commits por día:     {r['avg_por_dia']}")
            print(f"Máximo de commits en un día:     {r['max_por_dia']}")
            print(f"Días con actividad:              {r['dias_con_actividad']}")
            if graficar:
                self._graficar(r["por_dia"])
