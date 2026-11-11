"""
Descarga común de issues para las métricas que trabajan sobre el issue tracker
(mttr, nci, noi, process_performance, jarczyk_success_rate, dis).

Antes cada métrica bajaba su propia lista con distintos campos y la mayoría no
pedía ni el autor ni quién cerró la issue, así que no podía filtrar bots a nivel
producto. Esta descarga trae todo junto una sola vez por proceso (cache por repo):
número, fechas de creación y cierre, estado, autor, quién la cerró (actor del
último ClosedEvent), etiquetas y tipo de issue.

Correr varias de estas métricas en la misma invocación de run_versiones.py
(ej. `mttr,nci,noi,process_performance`) reutiliza la descarga.
"""
from datetime import datetime

_QUERY = """
query($owner: String!, $name: String!, $after: String) {
  repository(owner: $owner, name: $name) {
    issues(first: 25, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        state
        createdAt
        closedAt
        author { login }
        labels(first: 20) { nodes { name } }
        issueType { name }
        timelineItems(last: 1, itemTypes: [CLOSED_EVENT]) {
          nodes { ... on ClosedEvent { actor { login } } }
        }
      }
    }
  }
}
"""

_CACHE: dict = {}


def _fecha(raw):
    return datetime.fromisoformat(raw.replace("Z", "+00:00")) if raw else None


def descargar_issues(metric) -> list[dict]:
    """Todas las issues del repo de `metric` (una instancia de GitHubMetric).

    Cada issue: {number, state, created_at, closed_at, author, closed_by, labels, tipo}.
    `author` y `closed_by` son None si la cuenta no existe más o la issue sigue abierta.
    """
    clave = (metric.org, metric.repo)
    if clave in _CACHE:
        return _CACHE[clave]
    issues, cursor, page = [], None, 0
    print(f"Descargando issues de {metric.org}/{metric.repo} (autor, cierre, etiquetas)...")
    while True:
        page += 1
        data = metric._graphql(_QUERY, {"owner": metric.org, "name": metric.repo, "after": cursor})
        con = data["data"]["repository"]["issues"]
        for n in con["nodes"]:
            tl = (n.get("timelineItems") or {}).get("nodes") or []
            cerrador = ((tl[0].get("actor") or {}).get("login")) if tl else None
            issues.append({
                "number": n["number"],
                "state": (n.get("state") or "").lower(),
                "created_at": _fecha(n.get("createdAt")),
                "closed_at": _fecha(n.get("closedAt")),
                "author": (n.get("author") or {}).get("login"),
                "closed_by": cerrador,
                "labels": [l["name"] for l in (n.get("labels") or {}).get("nodes", [])],
                "tipo": (n.get("issueType") or {}).get("name"),
            })
        print(f"  ...página {page} ({len(issues)} issues)", end="\r")
        if not con["pageInfo"]["hasNextPage"]:
            break
        cursor = con["pageInfo"]["endCursor"]
    print()
    _CACHE[clave] = issues
    return issues


def normalizar_etiqueta(nombre: str) -> str:
    """'Type: Bug' -> 'bug', 'kind:documentation' -> 'documentation', 'bug' -> 'bug'.

    Para comparar etiquetas completas (no por subcadena: 'error' dentro de
    'Error Overlay' o 'doc' dentro de 'Docker' daban falsos positivos)."""
    n = nombre.strip().lower()
    if ":" in n:
        prefijo, resto = n.split(":", 1)
        if prefijo.strip() in {"type", "kind", "t", "tipo"}:
            n = resto.strip()
    return n


def tiene_etiqueta(labels: list[str], tipo: str | None, nombres: set[str],
                   solo_etiquetas: bool = False) -> bool:
    """¿Alguna etiqueta (o el tipo de issue, salvo solo_etiquetas) es exactamente uno de `nombres`?"""
    if any(normalizar_etiqueta(l) in nombres for l in labels):
        return True
    if solo_etiquetas or not tipo:
        return False
    return normalizar_etiqueta(tipo) in nombres
