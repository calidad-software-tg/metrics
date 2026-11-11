import sys
import math
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

# ATENCIÓN — MÉTRICA SIN CONSIGNA ASIGNADA TODAVÍA:
# Proviene del Notion "Commit Entropy". Mide la entropía de Shannon sobre la
# distribución de "cantidad de archivos modificados por commit" (no la
# entropía de qué archivos puntuales se tocan, ver nota en el docstring de
# la clase).
#
# Diferencias respecto al script original:
# 1. Fetch vía GraphQL (mismo patrón que metrics/10/anmcc.py, reutilizando
#    `changedFilesIfAvailable`) en vez de REST + N+1 requests por commit.
# 2. La entropía se calcula a mano con math.log2 en vez de scipy.stats.entropy,
#    porque scipy no es una dependencia del resto del catálogo (que solo usa
#    `requests`). El resultado es matemáticamente idéntico: misma fórmula
#    de Shannon, mismas frecuencias normalizadas, base 2.

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
              changedFilesIfAvailable
              author { user { login } name }
            }
          }
        }
      }
    }
  }
}
"""


def _shannon_entropy(valores: list[int]) -> float:
    """
    Entropía de Shannon (base 2) sobre la distribución de frecuencias de
    `valores`. Equivalente a scipy.stats.entropy(counts, base=2).
    """
    if not valores:
        return 0.0
    counts = Counter(valores)
    total = len(valores)
    return -sum(
        (c / total) * math.log2(c / total)
        for c in counts.values()
    )


class CommitEntropy(GitHubMetric):
    """
    Commit Entropy — dispersión (entropía de Shannon) de la cantidad de
    archivos modificados por commit.

    No es lo mismo que ANMCC (metrics/10/anmcc.py): ANMCC promedia los
    valores de "archivos por commit" (tendencia central); Commit Entropy
    agrupa esos mismos valores en buckets por cantidad de archivos y mide
    qué tan repartida está la masa de commits entre esos buckets (dispersión).
    Dos repos pueden tener el mismo ANMCC y entropías muy distintas.

    Nota conceptual: mide entropía sobre la CANTIDAD de archivos tocados por
    commit, no sobre CUÁLES archivos puntuales se tocan.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.commits: list[dict] = []  # [{oid, files_count, author}]

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
                    "files_count": node.get("changedFilesIfAvailable") or 0,
                    "author": user.get("login") or author_node.get("name") or "desconocido",
                })

            if not history["pageInfo"]["hasNextPage"]:
                break
            cursor = history["pageInfo"]["endCursor"]
            print(f"  ...{len(commits)} commits descargados", end="\r")

        self.commits = commits

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float:
        valores = [c["files_count"] for c in self.commits]
        return round(_shannon_entropy(valores), 4)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        by_author: dict[str, list[int]] = {}
        for c in self.commits:
            by_author.setdefault(c["author"], []).append(c["files_count"])

        resultado = {
            login: round(_shannon_entropy(valores), 4)
            for login, valores in by_author.items()
        }
        return dict(sorted(resultado.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        print(f"Descargando commits de {self.org}/{self.repo}...")
        self.fetch(fecha_inicio, fecha_fin)
        print(f"Commits descargados: {len(self.commits)}\n")

        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"{'Colaborador':<30} Entropía")
            print("-" * 42)
            for login, ent in resultado.items():
                print(f"{login:<30} {ent}")
        else:
            ent = self.por_producto(fecha_inicio, fecha_fin)
            print(f"Commit Entropy (Shannon, base 2): {ent}")
