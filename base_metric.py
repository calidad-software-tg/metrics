import sys
import time
from datetime import datetime

import requests

_BASE_URL = "https://api.github.com"

_TIMEOUT = (10, 60)          # (connect, read) en segundos: sin esto un socket colgado bloquea para siempre
_REINTENTOS = 5
_STATUS_REINTENTABLES = {500, 502, 503, 504, 520, 522}
_MAX_ESPERAS_RL = 4          # cuántas veces dormir hasta un reset de cuota por request


class GitHubAPIError(RuntimeError):
    """Error de la API de GitHub que ya agotó los reintentos/esperas posibles.

    _get()/_graphql() reintentan solo/en lo que se puede resolver con tiempo
    (red transitoria, 5xx, rate limit agotado). Cuando se agotan los
    reintentos, se levanta esto en vez de sys.exit(1): en un script de una
    sola métrica (run.py) el proceso muere igual (con traceback en vez de
    un renglón), pero en un hilo de un ThreadPoolExecutor (run_adaptativo.py
    con --threads) sys.exit() solo corta ESE hilo en silencio, sin que el
    resto del programa se entere -- levantar una excepción normal deja que
    cada caller decida.
    """


def _backoff(intento: int, motivo: str):
    espera = min(2 ** intento, 45)
    print(f"  (reintento {intento}/{_REINTENTOS} por {motivo}, espero {espera}s)", file=sys.stderr)
    time.sleep(espera)


def _es_rate_limit(resp) -> bool:
    """403/429 de GitHub por cuota (no un 403 de permisos)."""
    if resp.status_code not in (403, 429):
        return False
    if resp.headers.get("retry-after"):
        return True
    return resp.headers.get("x-ratelimit-remaining") == "0"


def _dormir_hasta_reset(resp):
    ra = resp.headers.get("retry-after")
    if ra:
        espera = int(ra) + 3
    else:
        reset = int(resp.headers.get("x-ratelimit-reset", time.time() + 120))
        espera = max(reset - time.time(), 0) + 5
    espera = int(min(espera, 3900))
    print(f"  (rate limit: duermo {espera}s hasta el reset de cuota)", file=sys.stderr)
    time.sleep(espera)


# Cache de proceso para _rest_list_since: varias métricas (disc_centrality, nc,
# exprev, rexprev) piden EXACTAMENTE los mismos endpoints de comentarios sobre
# el mismo rango. Con esto la 1ª los baja y las demás los reusan al instante.
_LIST_SINCE_CACHE: dict = {}

# Solo estos campos usan las métricas; guardar el item completo (con diff_hunk,
# body, reactions...) come cientos de MB en repos grandes.
_CAMPOS_SLIM = ("id", "created_at", "updated_at",
                "issue_url", "pull_request_url", "commit_id", "html_url")


def _slim_comentario(item: dict) -> dict:
    d = {k: item[k] for k in _CAMPOS_SLIM if k in item}
    u = item.get("user")
    d["user"] = {"login": u.get("login")} if isinstance(u, dict) else None
    return d


class GitHubMetric:

    def __init__(self, token: str, org: str, repo: str):
        self.token = token
        self.org = org
        self.repo = repo

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _get(self, url: str, params: dict = None) -> requests.Response:
        """GET con timeout, reintentos (red / 5xx) y espera de rate limit (403/429)."""
        intento = 0
        esperas_rl = 0
        while True:
            try:
                resp = requests.get(url, headers=self._headers(),
                                    params=params or {}, timeout=_TIMEOUT)
            except requests.exceptions.RequestException as exc:
                intento += 1
                if intento >= _REINTENTOS:
                    raise GitHubAPIError(f"sin respuesta tras {intento} intentos: {exc}")
                _backoff(intento, type(exc).__name__)
                continue
            if _es_rate_limit(resp):
                esperas_rl += 1
                if esperas_rl > _MAX_ESPERAS_RL:
                    raise GitHubAPIError(f"rate limit persistente tras {esperas_rl} esperas de reset")
                _dormir_hasta_reset(resp)
                continue  # no gasta 'intento'
            if resp.status_code in _STATUS_REINTENTABLES:
                intento += 1
                if intento >= _REINTENTOS:
                    return resp
                _backoff(intento, f"HTTP {resp.status_code}")
                continue
            return resp

    def _rest(self, path: str, params: dict = None) -> dict:
        resp = self._get(f"{_BASE_URL}{path}", params)
        if not resp.ok:
            print(f"GitHub API error {resp.status_code}: {resp.text}", file=sys.stderr)
            raise GitHubAPIError(f"{resp.status_code}: {resp.text[:300]}")
        return resp.json()

    def _rest_list_since(self, path: str, fecha_inicio, fecha_fin, *,
                         date_key: str = "created_at", id_key: str = "id",
                         label: str = "") -> list[dict]:
        """Baja TODOS los ítems de un endpoint-lista tipo comentarios y devuelve
        los que caen en [fecha_inicio, fecha_fin] según ``date_key``.

        GitHub corta la paginación de ``/issues/comments`` y similares antes
        de la página ~150 (HTTP 422). Para pasar el tope se pagina en tandas
        ordenadas por ``updated`` asc y se avanza ``since`` al ``updated_at``
        del último ítem visto cada vez que se toca el tope (TOPE_PAGINA, con
        margen bajo el límite duro real de GitHub). Dedup por ``id_key``.
        Endpoints que ignoran ``since`` (ej. commit comments) igual funcionan
        si su volumen entra en una tanda.

        LÍMITE DE SEGURIDAD: ``since`` de GitHub filtra por ``updated_at``,
        no por ``created_at`` -- para un rango angosto y viejo (ej. un
        bloque cerca de la creación del repo), recorrer completo hasta
        encontrar todo lo que cae en rango puede implicar bajar el
        historial COMPLETO de comentarios hasta hoy (un comentario viejo
        editado recién puede aparecer tarde en el orden por updated_at). Sin
        tope, esto puede tardar horas en un repo con mucho volumen. Con
        TOPE_ITEMS_TOTAL, si se superan esa cantidad de ítems vistos sin
        terminar, se corta y se devuelve lo encontrado hasta ahí -- el
        período queda con datos parciales (posible subconteo) en vez de
        colgar el proceso indefinidamente.
        """
        clave_cache = (self.org, self.repo, path,
                       fecha_inicio.isoformat(), fecha_fin.isoformat())
        if clave_cache in _LIST_SINCE_CACHE:
            cacheado = _LIST_SINCE_CACHE[clave_cache]
            if label:
                print(f"  ...{label}: {len(cacheado)} (cache)")
            return cacheado

        resultados: list[dict] = []
        vistos: set = set()
        since = fecha_inicio.isoformat()
        TOPE_PAGINA = 90              # margen bajo el límite duro de GitHub
        TOPE_ITEMS_TOTAL = 5_000      # tope de seguridad, ver docstring -- bajado de 20k:
                                       # en la práctica casi todos los períodos lo tocaban
                                       # igual (~24 min/período constante, sin mejora real
                                       # entre períodos viejos y nuevos), así que 20k no
                                       # daba más completitud, solo más tiempo
        tope_alcanzado = False

        while True:
            if len(vistos) >= TOPE_ITEMS_TOTAL:
                tope_alcanzado = True
                break
            page, ultimo_updated, terminado = 1, None, False
            while page <= TOPE_PAGINA:
                if len(vistos) >= TOPE_ITEMS_TOTAL:
                    tope_alcanzado = True
                    break
                resp = self._get(
                    f"{_BASE_URL}{path}",
                    {"per_page": 100, "page": page, "since": since,
                     "sort": "updated", "direction": "asc"},
                )
                if resp.status_code == 422:          # tope de paginación
                    break
                if not resp.ok:
                    print(f"GitHub API error {resp.status_code}: {resp.text}", file=sys.stderr)
                    raise GitHubAPIError(f"{resp.status_code}: {resp.text[:300]}")
                data = resp.json()
                if not data:
                    terminado = True
                    break
                for item in data:
                    iid = item.get(id_key)
                    if iid in vistos:
                        continue
                    vistos.add(iid)
                    ultimo_updated = item.get("updated_at") or item.get("created_at")
                    raw = item.get(date_key)
                    if not raw:
                        continue
                    fecha = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                    if fecha_inicio <= fecha <= fecha_fin:
                        resultados.append(_slim_comentario(item))
                if label:
                    print(f"  ...{label}: {len(resultados)} en rango / {len(vistos)} vistos", end="\r")
                if len(data) < 100:
                    terminado = True
                    break
                page += 1

            if terminado or tope_alcanzado or not ultimo_updated or ultimo_updated == since:
                break
            since = ultimo_updated

        if label:
            print()
        if tope_alcanzado:
            print(f"  AVISO: {label or path} tocó el tope de seguridad ({TOPE_ITEMS_TOTAL} ítems vistos) "
                  f"antes de terminar el rango [{fecha_inicio.date()}, {fecha_fin.date()}] -- "
                  f"puede haber subconteo en este período.", file=sys.stderr)
        else:
            # Solo se cachea si el resultado quedó completo -- uno parcial
            # no debería reusarse "tal cual" para otra llamada exacta.
            _LIST_SINCE_CACHE[clave_cache] = resultados
        return resultados

    def _graphql(self, query: str, variables: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.token}"}
        intento = 0
        esperas_rl = 0
        while True:
            try:
                resp = requests.post(
                    "https://api.github.com/graphql",
                    json={"query": query, "variables": variables},
                    headers=headers,
                    timeout=_TIMEOUT,
                )
            except requests.exceptions.RequestException as exc:
                intento += 1
                if intento >= _REINTENTOS:
                    raise GitHubAPIError(f"GraphQL sin respuesta tras {intento} intentos: {exc}")
                _backoff(intento, type(exc).__name__)
                continue
            if _es_rate_limit(resp):
                esperas_rl += 1
                if esperas_rl > _MAX_ESPERAS_RL:
                    raise GitHubAPIError(f"GraphQL rate limit persistente tras {esperas_rl} esperas de reset")
                _dormir_hasta_reset(resp)
                continue
            if resp.status_code in _STATUS_REINTENTABLES:
                intento += 1
                if intento >= _REINTENTOS:
                    break
                _backoff(intento, f"HTTP {resp.status_code}")
                continue
            break
        if not resp.ok:
            print(f"GitHub API error {resp.status_code}: {resp.text}", file=sys.stderr)
            raise GitHubAPIError(f"{resp.status_code}: {resp.text[:300]}")
        data = resp.json()
        if "errors" in data:
            print(f"GraphQL error: {data['errors']}", file=sys.stderr)
            raise GitHubAPIError(str(data["errors"])[:300])
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
