import sys
import time
from pathlib import Path

import requests

# Cache HTTP transparente para las llamadas a la API de GitHub.
# Motivación: el runner corre las 20+ métricas de flujo sobre cada uno de los
# ~45 bloques temporales; varias comparten los mismos endpoints (issues, PRs,
# comentarios). Sin cache cada bloque re-descarga todo. Con cache SQLite y TTL
# de 7 días la primera corrida se pega a la API y las siguientes leen del disco.
#
# Se instala como monkey-patch global de `requests` — todas las clases que
# heredan de GitHubMetric usan requests por debajo (_rest y _graphql), así que
# la cache aplica sin tener que tocar ninguna métrica.
try:
    import requests_cache
    _CACHE_PATH = Path(__file__).resolve().parent / "gh_cache"
    requests_cache.install_cache(
        str(_CACHE_PATH),
        backend="sqlite",
        expire_after=60 * 60 * 24 * 7,  # 1 semana
        allowable_methods=("GET", "POST"),  # el GraphQL de GitHub va por POST
        allowable_codes=(200,),
    )
except ImportError:
    # Si falta la dependencia, el pipeline igual funciona (solo va más lento).
    pass


_BASE_URL = "https://api.github.com"


def _es_rate_limit(resp) -> bool:
    """403/429 con mensaje de rate limit son idénticamente recuperables."""
    if resp.status_code not in (403, 429):
        return False
    txt = (resp.text or "").lower()
    return "rate limit" in txt or "api rate limit" in txt or "secondary rate limit" in txt


def _esperar_reset(resp) -> None:
    """
    Espera a X-RateLimit-Reset (o Retry-After) + un margen chico y sigue.
    El PAT tiene 5000 req/h y GraphQL su propia cuota; el reset viene en epoch.
    """
    now = int(time.time())
    reset = int(resp.headers.get("X-RateLimit-Reset") or 0)
    if reset:
        espera = max(reset - now, 0) + 5
    else:
        espera = int(resp.headers.get("Retry-After") or 60)
    print(f"  [rate limit] esperando {espera}s (hasta ~{time.strftime('%H:%M:%S', time.localtime(now + espera))})...",
          file=sys.stderr)
    time.sleep(espera)


class GitHubMetric:

    def __init__(self, token: str, org: str, repo: str):
        self.token = token
        self.org = org
        self.repo = repo

    def _rest(self, path: str, params: dict = None) -> dict:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        # Rate limit: hasta 3 reintentos con espera al reset. Con 5000 req/h la
        # cuota se agota corriendo el batch completo; sin este retry el runner
        # abandona la métrica tras 3 fallos seguidos aunque sea todo transitorio.
        for _ in range(3):
            resp = requests.get(f"{_BASE_URL}{path}", headers=headers, params=params or {})
            if _es_rate_limit(resp):
                _esperar_reset(resp)
                continue
            break
        if not resp.ok:
            raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def _graphql(self, query: str, variables: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"}
        for _ in range(3):
            resp = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers=headers,
            )
            if _es_rate_limit(resp):
                _esperar_reset(resp)
                continue
            break
        if not resp.ok:
            raise RuntimeError(f"GitHub API error {resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"GraphQL error: {data['errors']}")
        return data

    def _resolve_ref(self, fecha_fin) -> str:
        """SHA del último commit de la rama default con fecha <= fecha_fin.

        Para métricas que leen contenido del repo (árbol de archivos,
        blobs): usar este ref en vez de "HEAD" hace que reflejen el estado
        del repo a una fecha dada, no siempre el estado actual. Si no hay
        ningún commit antes de fecha_fin (fecha anterior a la creación del
        repo), cae de vuelta a "HEAD".
        """
        commits = self._rest(
            f"/repos/{self.org}/{self.repo}/commits",
            {"until": fecha_fin.isoformat(), "per_page": 1},
        )
        return commits[0]["sha"] if commits else "HEAD"

    def fetch(self, **kwargs):
        raise NotImplementedError

    def por_producto(self, fecha_inicio, fecha_fin):
        raise NotImplementedError

    def por_persona(self, fecha_inicio, fecha_fin):
        raise NotImplementedError

    def run(self, fecha_inicio, fecha_fin, por: str = "producto"):
        raise NotImplementedError
