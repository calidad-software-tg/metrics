"""
Corre UNA métrica sobre cada ventana entre versiones (tags) consecutivas de un repo.

Las ventanas se arman solas: se bajan los tags del repo, se ordenan por fecha del
commit apuntado, y cada par de tags consecutivos define una ventana
[fecha_tag_i, fecha_tag_{i+1}). El último tag define una ventana abierta hasta ahora.
Para tldr-pages/tldr esto da 11 ventanas (v1.0 .. v2.3).

Uso:
    python run_versiones.py                      # usa METRICA de abajo (mttr)
    python run_versiones.py nc                   # una métrica
    python run_versiones.py nc,rc,wp             # varias
    python run_versiones.py todas                # todas menos las de YA_CORRIDAS
    python run_versiones.py todas --excepto ss,cd
    python run_versiones.py nc --por persona     # forzar modo (default: auto)
    python run_versiones.py todas --repo flutter/flutter --json salida.json
    python run_versiones.py nc --no-guardar      # solo imprime, no toca la base

Con --por auto (default) cada métrica se prueba en producto y en persona, y se
guarda lo que aplique. Las claves son las mismas que en run.py / run_batch_anmcc.py.

Por defecto persiste en la base (tablas periodo + resultado, tipo_analisis
'versiones'). Necesita la base levantada (ver db/README.md) y las variables
POSTGRES_* en .env. Cada corrida hace upsert: volver a correr la misma métrica
sobre el mismo repo pisa los valores anteriores en vez de duplicarlos.
"""

import argparse
import inspect
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- config editable -----------------------------------------------------------
METRICA   = "mttr"               # <<< cambiá esta clave para correr otra métrica
POR       = "producto"           # "producto" | "persona"
REPO_FULL = "tldr-pages/tldr"    # "org/repo"
MAX_FILES = 500                  # solo lo usan algunas métricas (ej. cd)
GUARDAR   = True                 # persistir en la base (se apaga con --no-guardar)
TIPO_ANALISIS = "versiones"      # valor que va en periodo.tipo_analisis
# -----------------------------------------------------------------------------

# Nombre humano para el catálogo `metrica` cuando la clave de código no existe
# todavía en la tabla (se inserta al vuelo para respetar la FK de `resultado`).
NOMBRES_METRICA = {
    "mttr": "MTTR (Tiempo Medio de Reparación)",
    "mttr_p50": "MTTR, mediana de las issues (sin bots)",
    "mttr_bugs": "MTTR solo de bugs (sin bots)",
    "mttr_con_bots": "MTTR con los cierres de bots (versión original)",
    "anmcc": "ANMCC (Número Promedio de Componentes Modificados por Commit)",
    "nci": "Number of Closed Issues (NCI)",
    "nci_con_bots": "NCI con los cierres de bots (versión original)",
    "dloc_flujo": "Líneas de documentación agregadas o eliminadas en la ventana",
    "commits_doc": "Proporción de commits que tocan documentación",
}

# --- cargar .env -------------------------------------------------------------
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

_root = Path(__file__).resolve().parent
for _d in ["35", "10", "16", "20", "15", "18", "23", "27", "40", "43", "28", "38", "39", "42", "Notion"]:
    sys.path.insert(0, str(_root / _d))

import requests

try:
    import psycopg2
    from psycopg2.extras import Json
except ImportError:
    psycopg2 = None

from nci import NumberOfClosedIssues, NumberOfClosedIssuesConBots
from anmcc import AverageNumberOfModifiedComponentsPerCommit
from mttr import MeanTimeToRepair, MeanTimeToRepairMediana, MeanTimeToRepairBugs, MeanTimeToRepairConBots
from cd import CommentDensity
from readme_completeness import ReadmeCompleteness
from wiki_presence import WikiPresence
from doc_issue_survival import DocIssueSurvival
from dloc import DocumentationLinesOfCode
from dc import SocialContribution
from le import LearningEase
from ss import SkillSimilarity
from rexp import RecentExperience
from fexp import FileExperience
from exprev import ReviewExperience
from rexprev import RecentReviewExperience
from cdiv import ContributionDiversity
from nc import NumberOfComments
from disc_centrality import DiscussionCentrality
from sc import SocialContribution as SocialContributionDiscussion
from schedule_compliance import ScheduleCompliance
from cfdr import CustomerFoundDefectsAndRegressions
from process_performance import DevelopmentProcessPerformance
from noi import NumberOfOpenIssues
from nci_reuse import NumberOfClosedIssues as NumberOfClosedIssuesProcess
from tasa_exito import JarczykSuccessRate
from nci_reuse_43 import NumberOfClosedIssues as NumberOfClosedIssuesResolutionTime
try:
    from open_issues import NumberOfOpenIssues as NumberOfOpenIssuesRegistro28
except ImportError:
    NumberOfOpenIssuesRegistro28 = None
try:
    from dev_experience import DevelopmentExperience
except ImportError:
    DevelopmentExperience = None
try:
    from nub import NumberOfBugsDetectedByUsers  # 39/nub.py
except ImportError:
    NumberOfBugsDetectedByUsers = None
try:
    from nob import NumberOfBranches
except ImportError:
    NumberOfBranches = None
from loc import LinesOfCode
from collaborators import NumberOfCollaborators
from commit_frequency import CommitFrequency
from commit_entropy import CommitEntropy
from ci_presence import ContinuousIntegrationPresence
from commits_per_author import CommitsPerAuthor
from developer_ownership import DeveloperOwnership
from forks import NumberOfForks
from issues_total import TotalIssues
from pull_requests_summary import PullRequestsSummary
from core_devs_prs import CoreDevsPullRequests

# --- mismo dict que run.py / run_batch_anmcc.py ----------------------------
metricas = {
    "nci":   NumberOfClosedIssues,
    "nci_con_bots": NumberOfClosedIssuesConBots,
    "anmcc": AverageNumberOfModifiedComponentsPerCommit,
    "mttr":  MeanTimeToRepair,
    "mttr_p50": MeanTimeToRepairMediana,
    "mttr_bugs": MeanTimeToRepairBugs,
    "mttr_con_bots": MeanTimeToRepairConBots,
    "cd":    CommentDensity,
    "rc":    ReadmeCompleteness,
    "wp":    WikiPresence,
    "dis":   DocIssueSurvival,
    "dloc":  DocumentationLinesOfCode,
    "sc":    SocialContribution,
    "le":      LearningEase,
    "ss":      SkillSimilarity,
    "rexp":    RecentExperience,
    "fexp":    FileExperience,
    "exprev":  ReviewExperience,
    "rexprev": RecentReviewExperience,
    "cdiv":    ContributionDiversity,
    "nc":              NumberOfComments,
    "disc_centrality": DiscussionCentrality,
    "sc_disc":         SocialContributionDiscussion,
    "schedule_compliance": ScheduleCompliance,
    "cfdr": CustomerFoundDefectsAndRegressions,
    "process_performance": DevelopmentProcessPerformance,
    "noi": NumberOfOpenIssues,
    "nci_process": NumberOfClosedIssuesProcess,
    "jarczyk_success_rate": JarczykSuccessRate,
    "nci_resolution_time": NumberOfClosedIssuesResolutionTime,
    "noi_28": NumberOfOpenIssuesRegistro28,
    "dev_exp": DevelopmentExperience,
    "nub": NumberOfBugsDetectedByUsers,
    "nob_42": NumberOfBranches,
    "loc_notion": LinesOfCode,
    "collab_notion": NumberOfCollaborators,
    "commit_freq_notion": CommitFrequency,
    "commit_entropy_notion": CommitEntropy,
    "ci_presence_notion": ContinuousIntegrationPresence,
    "commits_per_author_notion": CommitsPerAuthor,
    "developer_ownership_notion": DeveloperOwnership,
    "forks_notion": NumberOfForks,
    "issues_total_notion": TotalIssues,
    "prs_summary_notion": PullRequestsSummary,
    "core_devs_prs_notion": CoreDevsPullRequests,
}

_BASE_URL = "https://api.github.com"


from base_metric import GitHubMetric

_cliente_gh = None


def _gh(path: str, token: str, params: dict = None) -> requests.Response:
    """Igual que antes pero pasa por GitHubMetric._get: timeout, reintentos y
    espera de rate limit. Sin esto, un 403 de cuota al armar las ventanas
    mataba todo el batch antes de tocar una métrica."""
    global _cliente_gh
    if _cliente_gh is None:
        _cliente_gh = GitHubMetric(token, "", "")
    resp = _cliente_gh._get(f"{_BASE_URL}{path}", params)
    if not resp.ok:
        print(f"GitHub API error {resp.status_code}: {resp.text}", file=sys.stderr)
        sys.exit(1)
    return resp


# --- criterio de ventanas ------------------------------------------------------
# Releases marcados como estables en GitHub que en realidad son prereleases (mal
# etiquetados en next.js): no cortan ventanas.
EXCLUIR_VERSIONES = frozenset({"4.4.0-canary.2", "4.4.0-canary.1", "v12.2.3-canary.5", "v15.0.0-rc.1"})

# excluir_backports: un release cuya versión mayor es menor que la más alta publicada hasta
#   ese momento (ej. una v14.2.x de 2025, cuando la principal ya es v15/v16) es un parche de
#   una rama de mantenimiento: no corta ventanas. Con backports, las ventanas de la línea
#   principal quedaban partidas por releases de otra rama y las métricas de foto saltaban
#   entre dos árboles de código.
# min_dias: un release publicado menos de min_dias después del anterior que quedó no corta
#   ventana: su lapso se suma a la ventana anterior. En next.js, 88 de 369 ventanas estables
#   duraban menos de un día (releases de varias líneas a la vez, hotfixes a las pocas horas)
#   y casi no tenían actividad. None = 1 día en estables y 0 (sin unir) en canary.
# hasta: fecha de corte. Los releases posteriores se ignoran y la última ventana termina ahí
#   (sin corte, termina "ahora"). Sirve para que corridas hechas en días distintos (por
#   ejemplo, cada integrante con sus métricas) den exactamente las mismas ventanas.
VENTANAS = {"excluir_backports": True, "min_dias": None, "hasta": None}


def _fecha_corte(texto: str | None):
    if not texto:
        return None
    return datetime.fromisoformat(texto).replace(tzinfo=timezone.utc)


def _version_mayor(version: str) -> int | None:
    try:
        return int(str(version).lstrip("vV").split(".")[0])
    except ValueError:
        return None


def _armar_ventanas(versiones: list[dict], min_dias_default: float) -> list[dict]:
    """Ordena las versiones, aplica el criterio de VENTANAS y arma [inicio, fin) por versión."""
    hasta = VENTANAS["hasta"]
    versiones = sorted((v for v in versiones if v["version"] not in EXCLUIR_VERSIONES
                        and (hasta is None or v["fecha"] <= hasta)),
                       key=lambda v: v["fecha"])
    if VENTANAS["excluir_backports"]:
        principales, maximo = [], -1
        for v in versiones:
            mayor = _version_mayor(v["version"])
            if mayor is not None and mayor < maximo:
                continue  # backport
            if mayor is not None:
                maximo = max(maximo, mayor)
            principales.append(v)
        versiones = principales
    min_dias = VENTANAS["min_dias"] if VENTANAS["min_dias"] is not None else min_dias_default
    quedan: list[dict] = []
    for v in versiones:
        if quedan and min_dias and (v["fecha"] - quedan[-1]["fecha"]).total_seconds() < min_dias * 86400:
            quedan[-1].setdefault("absorbidas", []).append(v["version"])
            continue
        quedan.append(dict(v))
    ahora = hasta or datetime.now(timezone.utc)
    ventanas = []
    for i, v in enumerate(quedan):
        fin = quedan[i + 1]["fecha"] if i + 1 < len(quedan) else ahora
        ventanas.append({
            "n": i + 1,
            "version": v["version"],
            "inicio": v["fecha"],
            "fin": fin,
            "abierta": i + 1 == len(quedan),
            "absorbidas": v.get("absorbidas", []),
        })
    return ventanas


def ventanas_por_version(token: str, org: str, repo: str) -> list[dict]:
    """Una ventana [inicio, fin) por cada versión estable consecutiva. El último va hasta ahora.

    Usa /releases, no /tags: trae el flag `prerelease` para descartar versiones
    de prueba (ej. canary de next.js, ~88% de sus tags) sin adivinar por el
    nombre, y ya incluye `published_at`, así que no hace falta una llamada
    extra a /commits/{sha} por versión como en la implementación anterior
    basada en tags (para un repo con miles de tags, esa llamada extra por
    cada uno se comía casi toda la cuota antes de calcular una sola métrica).

    Fallback a /tags (comportamiento anterior, sin filtrar) para repos que no
    usan GitHub Releases o donde ninguna release está marcada como estable
    (ej. cpython). Si el repo sí usa Releases pero con nombres tipo canary,
    usar siempre la rama de /releases de arriba, nunca este fallback.
    """
    releases = []
    page = 1
    while True:
        batch = _gh(f"/repos/{org}/{repo}/releases", token, {"per_page": 100, "page": page}).json()
        if not batch:
            break
        releases.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    estables = [r for r in releases if not r["prerelease"] and not r["draft"]]

    if estables:
        versiones = [
            {"version": r["tag_name"],
             "fecha": datetime.fromisoformat(r["published_at"].replace("Z", "+00:00"))}
            for r in estables
        ]
    else:
        print(f"{org}/{repo}: sin releases estables, uso tags crudos (sin filtrar prerelease)", file=sys.stderr)
        tags = []
        page = 1
        while True:
            batch = _gh(f"/repos/{org}/{repo}/tags", token, {"per_page": 100, "page": page}).json()
            if not batch:
                break
            tags.extend(batch)
            if len(batch) < 100:
                break
            page += 1

        if not tags:
            print(f"{org}/{repo} no tiene tags ni releases; no se puede cortar por versiones", file=sys.stderr)
            sys.exit(1)

        versiones = []
        for t in tags:
            sha = t["commit"]["sha"]
            commit = _gh(f"/repos/{org}/{repo}/commits/{sha}", token).json()
            fecha = datetime.fromisoformat(
                commit["commit"]["committer"]["date"].replace("Z", "+00:00")
            )
            versiones.append({"version": t["name"], "fecha": fecha})

    return _armar_ventanas(versiones, min_dias_default=1.0)


def ventanas_por_version_todas(token: str, org: str, repo: str) -> list[dict]:
    """Igual que ventanas_por_version, pero SIN filtrar prerelease/canary --
    una ventana por cada release publicada, estable o no. Para un repo con
    cadencia canary diaria (ej. next.js) esto multiplica por ~10 la cantidad
    de ventanas y las angosta a horas en vez de semanas/meses -- guardar bajo
    tipo_analisis='versiones_canary', nunca pisa a 'versiones' (estables).
    """
    releases = []
    page = 1
    while True:
        batch = _gh(f"/repos/{org}/{repo}/releases", token, {"per_page": 100, "page": page}).json()
        if not batch:
            break
        releases.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    if releases:
        versiones = [
            {"version": r["tag_name"],
             "fecha": datetime.fromisoformat(r["published_at"].replace("Z", "+00:00"))}
            for r in releases if not r["draft"]
        ]
    else:
        print(f"{org}/{repo}: sin releases, uso tags crudos", file=sys.stderr)
        tags = []
        page = 1
        while True:
            batch = _gh(f"/repos/{org}/{repo}/tags", token, {"per_page": 100, "page": page}).json()
            if not batch:
                break
            tags.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        if not tags:
            print(f"{org}/{repo} no tiene tags ni releases; no se puede cortar por versiones", file=sys.stderr)
            sys.exit(1)
        versiones = []
        for t in tags:
            sha = t["commit"]["sha"]
            commit = _gh(f"/repos/{org}/{repo}/commits/{sha}", token).json()
            fecha = datetime.fromisoformat(
                commit["commit"]["committer"]["date"].replace("Z", "+00:00")
            )
            versiones.append({"version": t["name"], "fecha": fecha})

    return _armar_ventanas(versiones, min_dias_default=0.0)


# --- persistencia ----------------------------------------------------------

class Base:
    """Envuelve la conexión y los upserts a periodo + resultado."""

    def __init__(self):
        if psycopg2 is None:
            raise RuntimeError("psycopg2 no está instalado; usá --no-guardar")
        self.con = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
            user=os.environ.get("POSTGRES_USER", "metricas"),
            password=os.environ.get("POSTGRES_PASSWORD", "metricas"),
            dbname=os.environ.get("POSTGRES_DB", "resultados_metricas"),
        )
        self.cur = self.con.cursor()

    def repo_id(self, org: str, repo: str) -> int:
        full = f"{org}/{repo}"
        self.cur.execute("SELECT repo_id FROM repos WHERE full_name = %s", (full,))
        row = self.cur.fetchone()
        if row:
            return row[0]
        self.cur.execute(
            """INSERT INTO repos (org, repo, full_name, url, plataforma)
               VALUES (%s, %s, %s, %s, 'GitHub') RETURNING repo_id""",
            (org, repo, full, f"https://github.com/{full}"),
        )
        return self.cur.fetchone()[0]

    def ensure_metrica(self, metrica_id: str):
        self.cur.execute(
            """INSERT INTO metrica (metrica_id, nombre)
               VALUES (%s, %s) ON CONFLICT (metrica_id) DO NOTHING""",
            (metrica_id, NOMBRES_METRICA.get(metrica_id, metrica_id)),
        )

    def upsert_periodo(self, repo_id: int, tipo: str, num: int,
                       inicio, fin, etiqueta: str, parametros: dict) -> int:
        self.cur.execute(
            """
            INSERT INTO periodo (repo_id, tipo_analisis, periodo_num,
                                 fecha_inicio, fecha_fin, etiqueta, parametros)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (repo_id, tipo_analisis, periodo_num) DO UPDATE SET
                fecha_inicio = EXCLUDED.fecha_inicio,
                fecha_fin    = EXCLUDED.fecha_fin,
                etiqueta     = EXCLUDED.etiqueta,
                parametros   = EXCLUDED.parametros
            RETURNING periodo_id
            """,
            (repo_id, tipo, num, inicio, fin, etiqueta, Json(parametros)),
        )
        return self.cur.fetchone()[0]

    def upsert_resultado(self, periodo_id: int, metrica_id: str,
                         login, value, value_extra):
        if login is None:
            self.cur.execute(
                """
                INSERT INTO resultado (periodo_id, metrica_id, contribuyente_login,
                                       value, value_extra)
                VALUES (%s, %s, NULL, %s, %s)
                ON CONFLICT (periodo_id, metrica_id) WHERE contribuyente_login IS NULL
                DO UPDATE SET value = EXCLUDED.value,
                             value_extra = EXCLUDED.value_extra,
                             calculado_en = now()
                """,
                (periodo_id, metrica_id, value,
                 Json(value_extra) if value_extra is not None else None),
            )
        else:
            self.cur.execute(
                """
                INSERT INTO resultado (periodo_id, metrica_id, contribuyente_login,
                                       value, value_extra)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (periodo_id, metrica_id, contribuyente_login)
                    WHERE contribuyente_login IS NOT NULL
                DO UPDATE SET value = EXCLUDED.value,
                             value_extra = EXCLUDED.value_extra,
                             calculado_en = now()
                """,
                (periodo_id, metrica_id, login, value,
                 Json(value_extra) if value_extra is not None else None),
            )

    def guardar_ventana(self, repo_id: int, metrica_id: str, tipo: str,
                        ventana: dict, por: str, valor):
        periodo_id = self.upsert_periodo(
            repo_id, tipo, ventana["n"],
            ventana["inicio"], ventana["fin"], ventana["version"],
            {"tag": ventana["version"], "abierta": ventana["abierta"],
             "absorbidas": ventana.get("absorbidas", []),
             "excluye_backports": VENTANAS["excluir_backports"]},
        )
        if por == "persona":
            for login, val in (valor or {}).items():
                if isinstance(val, dict):
                    # salida compuesta por persona (ej. dev_exp, sc): número al
                    # 'value' si hay un escalar obvio, y el detalle a value_extra.
                    escalar = _escalar_de(val)
                    self.upsert_resultado(periodo_id, metrica_id, login, escalar, val)
                elif isinstance(val, (list, tuple, str, bool)):
                    # salida no numérica por persona (ej. ci_presence: lista de
                    # sistemas de CI que introdujo). Va entera a value_extra.
                    self.upsert_resultado(periodo_id, metrica_id, login, None, list(val)
                                          if isinstance(val, (list, tuple)) else val)
                else:
                    self.upsert_resultado(periodo_id, metrica_id, login, float(val), None)
        elif isinstance(valor, (dict, list)):
            # Para métricas de producto que devuelven {repo: {key: escalar, ...}},
            # extraer el número principal a value y guardar el dict completo en
            # value_extra para no perder el desglose (ej. nub, nob_42).
            escalar = None
            if isinstance(valor, dict):
                if len(valor) == 1:
                    inner = next(iter(valor.values()))
                    if isinstance(inner, dict):
                        escalar = _escalar_de(inner)
                else:
                    escalar = _escalar_de(valor)
            self.upsert_resultado(periodo_id, metrica_id, None, escalar, valor)
        elif isinstance(valor, bool):
            self.upsert_resultado(periodo_id, metrica_id, None, float(valor), None)
        elif valor is not None:
            self.upsert_resultado(periodo_id, metrica_id, None, float(valor), None)

    def commit(self):
        self.con.commit()

    def close(self):
        self.cur.close()
        self.con.close()


# Topes opcionales para métricas caras (se setean desde --max-files / --max-commits).
LIMITES = {"max_files": None, "max_commits": None, "max_contributors": None}

# Opciones de criterio que se pasan a fetch si la métrica las acepta (se setean desde la línea de comandos).
# solo_etiquetas: cfdr, nub y dis reconocen bugs/documentación solo por etiqueta, sin el tipo de
# issue de GitHub (algoritmo original de la consigna).
OPCIONES = {"solo_etiquetas": False}


def _fetch(metric, fecha_inicio, fecha_fin, por: str):
    """Llama fetch adaptándose a su firma (fecha_inicio/fecha_fin y/o con_actor)."""
    params = inspect.signature(metric.fetch).parameters
    kwargs = {}
    if por == "persona" and "con_actor" in params:
        kwargs["con_actor"] = True
    for nombre, valor in LIMITES.items():
        if valor is not None and nombre in params:
            kwargs[nombre] = valor
    for nombre, valor in OPCIONES.items():
        if nombre in params:
            kwargs[nombre] = valor
    if "fecha_inicio" in params and "fecha_fin" in params:
        metric.fetch(fecha_inicio, fecha_fin, **kwargs)
    elif "fecha_fin" in params:
        metric.fetch(fecha_fin, **kwargs)
    else:
        metric.fetch(**kwargs)


def _fetch_por_ventana(MetricClass) -> bool:
    """True si fetch toma alguna fecha -> hay que llamarlo por ventana."""
    params = inspect.signature(MetricClass.fetch).parameters
    return "fecha_inicio" in params or "fecha_fin" in params


def _calcular(metric, fecha_inicio, fecha_fin, por: str):
    if por == "persona":
        return metric.por_persona(fecha_inicio, fecha_fin)
    return metric.por_producto(fecha_inicio, fecha_fin)


def _fmt(valor) -> str:
    if isinstance(valor, dict):
        return json.dumps(valor, ensure_ascii=False)
    return str(valor)


# Claves de resumen conocidas en salidas compuestas por persona.
_CLAVES_ESCALAR = ("sc", "experiencia_meses", "porcentaje", "value", "valor",
                   "total", "score", "count", "nub", "nob")


def _escalar_de(d: dict):
    """Extrae el número de resumen de un dict compuesto; None si no hay uno claro."""
    for k in _CLAVES_ESCALAR:
        if k in d and isinstance(d[k], (int, float)):
            return float(d[k])
    numericos = [v for v in d.values() if isinstance(v, (int, float))]
    return float(numericos[0]) if len(numericos) == 1 else None


# Marcas de "esta métrica no aplica en este modo" (no es un error real de datos).
_MARCAS_DIM = (
    "no aplica", "por persona", "por producto", "solo aplica", "sólo aplica",
    "not implemented", "notimplementederror", "no soporta", "no está definid",
)


def _es_error_dimension(exc) -> bool:
    if isinstance(exc, NotImplementedError):
        return True
    s = f"{type(exc).__name__} {exc}".lower()
    return any(m in s for m in _MARCAS_DIM)


def _meta(v: dict) -> dict:
    return {"n": v["n"], "version": v["version"], "inicio": v["inicio"],
            "fin": v["fin"], "abierta": v["abierta"], "absorbidas": v.get("absorbidas", [])}


# Ya corridas por separado; 'todas' las saltea.
YA_CORRIDAS = {"anmcc", "cdiv", "mttr"}

# Métricas cuyo fetch(fi, ff) baja historial y cuyo por_persona/por_producto NO
# re-filtra por fecha (el recorte lo hace fetch). Correrlas por ventana implica
# bajar 11 veces el mismo historial (para la 1ª ventana, todo desde 2019 a hoy).
# En vez de eso: UN fetch del rango completo y recorte en memoria de las listas
# internas por ventana. {code_key: [(atributo_lista, clave_fecha_del_item), ...]}
# Lista vacía = no hay nada que recortar, sólo cambia la fecha_fin de referencia.
SLICEABLE = {
    "disc_centrality": [("metadata_comentarios", "fecha")],
    "nc":              [("eventos", "fecha")],
    "exprev":          [("eventos", "fecha")],
    "rexprev":         [("eventos", "fecha")],
    "sc":              [("_issues", "created"), ("_prs", "created")],
    "sc_disc":         [("_issues", "created"), ("_prs", "created")],
    "dev_exp":         [],
    # nob_42: devuelve conteo actual de branches (no histórico); un fetch global
    # evita repetirlo una vez por ventana sin cambiar el resultado.
    "nob_42":          [],
    # nub: un fetch global descarga todos los issues del rango completo; SLICEABLE
    # los filtra por ventana usando 'created'. Evita ~373 fetches completos del
    # issue tracker de next.js (que tiene >40k issues).
    "nub":             [("_issues", "created")],
}


def _correr_sliceable(key, MetricClass, ventanas, token, org, repo, modos):
    """Un solo fetch del rango completo; recorta las listas internas por ventana."""
    attrs = SLICEABLE[key]
    modo_fetch = "persona" if "persona" in modos else "producto"
    rango_ini = min(v["inicio"] for v in ventanas)
    rango_fin = max(v["fin"] for v in ventanas)

    metric = MetricClass(token, org, repo)
    try:
        _fetch(metric, rango_ini, rango_fin, modo_fetch)
    except (Exception, SystemExit) as exc:
        err = f"fetch: {exc}"
        return {"por": [], "filas": [{**_meta(v), "por": None, "valor": None, "error": err}
                                     for v in ventanas]}

    full = {a: list(getattr(metric, a)) for a, _ in attrs}

    filas, modos_ok = [], set()
    for v in ventanas:
        for a, clave in attrs:
            setattr(metric, a, [r for r in full[a] if v["inicio"] <= r[clave] <= v["fin"]])
        for modo in modos:
            try:
                valor = _calcular(metric, v["inicio"], v["fin"], modo)
            except (Exception, SystemExit) as exc:
                if _es_error_dimension(exc):
                    continue
                filas.append({**_meta(v), "por": modo, "valor": None, "error": str(exc)})
                continue
            modos_ok.add(modo)
            filas.append({**_meta(v), "por": modo, "valor": valor, "error": None})
    for a, _ in attrs:
        setattr(metric, a, full[a])
    return {"por": sorted(modos_ok), "filas": filas}


def correr_metrica(key, MetricClass, ventanas, token, org, repo, modos):
    """Corre `key` sobre todas las ventanas probando cada modo de `modos`.

    Devuelve {"por": [modos que dieron algo], "filas": [ {..meta.., por, valor, error} ]}.
    `valor` None con `error` None = corrió pero sin datos en esa ventana.
    """
    if key in SLICEABLE:
        return _correr_sliceable(key, MetricClass, ventanas, token, org, repo, modos)

    fetch_por_ventana = _fetch_por_ventana(MetricClass)
    modo_fetch = "persona" if "persona" in modos else "producto"

    compartido = None
    fetch_global_error = None
    if not fetch_por_ventana:
        compartido = MetricClass(token, org, repo)
        rango_ini = min(v["inicio"] for v in ventanas)
        rango_fin = max(v["fin"] for v in ventanas)
        try:
            _fetch(compartido, rango_ini, rango_fin, modo_fetch)
        except (Exception, SystemExit) as exc:
            fetch_global_error = f"fetch: {exc}"

    filas = []
    modos_ok = set()
    for v in ventanas:
        if fetch_global_error:
            filas.append({**_meta(v), "por": None, "valor": None, "error": fetch_global_error})
            continue

        metric = compartido or MetricClass(token, org, repo)
        if fetch_por_ventana:
            try:
                _fetch(metric, v["inicio"], v["fin"], modo_fetch)
            except (Exception, SystemExit) as exc:
                filas.append({**_meta(v), "por": None, "valor": None, "error": f"fetch: {exc}"})
                continue

        for modo in modos:
            try:
                valor = _calcular(metric, v["inicio"], v["fin"], modo)
            except (Exception, SystemExit) as exc:
                if _es_error_dimension(exc):
                    continue
                filas.append({**_meta(v), "por": modo, "valor": None, "error": str(exc)})
                continue
            modos_ok.add(modo)
            filas.append({**_meta(v), "por": modo, "valor": valor, "error": None})

    return {"por": sorted(modos_ok), "filas": filas}


def main():
    parser = argparse.ArgumentParser(
        description="Corre métrica(s) ventana por ventana entre versiones y las guarda")
    parser.add_argument("objetivo", nargs="?", default=METRICA,
                        help="clave, lista 'k1,k2', o 'todas' (todas menos las ya corridas)")
    parser.add_argument("--por", default="auto", choices=["auto", "producto", "persona"],
                        help="auto = prueba producto y persona y guarda lo que aplique")
    parser.add_argument("--repo", default=REPO_FULL, metavar="ORG/REPO")
    parser.add_argument("--excepto", default="", metavar="k1,k2",
                        help="claves extra a saltear cuando objetivo='todas'")
    parser.add_argument("--json", metavar="ARCHIVO", help="volcar todos los resultados a este JSON")
    parser.add_argument("--no-guardar", dest="guardar", action="store_false",
                        default=GUARDAR, help="no persistir en la base, solo imprimir")
    parser.add_argument("--max-files", type=int, help="tope de archivos para métricas de árbol (cd, dloc, loc_notion...)")
    parser.add_argument("--max-commits", type=int, help="tope de commits para métricas de historial (fexp, le, rexp...)")
    parser.add_argument("--max-contributors", type=int, help="tope de contribuidores (ss)")
    parser.add_argument("--solo-etiquetas", action="store_true",
                        help="cfdr, nub y dis: reconocer bugs/documentación solo por etiqueta, sin el tipo "
                             "de issue de GitHub (algoritmo original de la consigna)")
    parser.add_argument("--con-backports", action="store_true",
                        help="no excluye los backports (releases de una versión mayor anterior) al armar ventanas")
    parser.add_argument("--min-dias", type=float, default=None,
                        help="une las ventanas más cortas que esto con la anterior "
                             "(default: 1 en estables, 0 en canary)")
    parser.add_argument("--hasta", metavar="AAAA-MM-DD",
                        help="fecha de corte de las ventanas (para que corridas de distintos días coincidan)")
    parser.add_argument("--con-canary", action="store_true",
                        help="no filtra prerelease/canary: una ventana por cada release publicada "
                             "(muchas más, mucho más angostas). Guarda en tipo_analisis='versiones_canary', "
                             "nunca pisa a 'versiones' (solo estables)")
    args = parser.parse_args()

    global TIPO_ANALISIS
    if args.con_canary:
        TIPO_ANALISIS = "versiones_canary"

    VENTANAS["excluir_backports"] = not args.con_backports
    VENTANAS["min_dias"] = args.min_dias
    VENTANAS["hasta"] = _fecha_corte(args.hasta)
    LIMITES["max_files"] = args.max_files
    LIMITES["max_commits"] = args.max_commits
    LIMITES["max_contributors"] = args.max_contributors
    OPCIONES["solo_etiquetas"] = args.solo_etiquetas

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("Falta GITHUB_TOKEN en .env", file=sys.stderr)
        sys.exit(1)
    if "/" not in args.repo:
        print("--repo debe ser ORG/REPO", file=sys.stderr)
        sys.exit(1)
    org, repo = args.repo.split("/", 1)

    # --- resolver qué métricas correr ---
    if args.objetivo.lower() in ("todas", "all", "todo", "*"):
        extra = {s.strip() for s in args.excepto.split(",") if s.strip()}
        claves = [k for k, C in sorted(metricas.items())
                  if C is not None and k not in YA_CORRIDAS and k not in extra]
    else:
        claves = [s.strip() for s in args.objetivo.split(",") if s.strip()]
        desconocidas = [k for k in claves if k not in metricas]
        if desconocidas:
            print(f"Claves desconocidas: {desconocidas}", file=sys.stderr)
            sys.exit(1)
        no_disp = [k for k in claves if metricas[k] is None]
        if no_disp:
            print(f"Salteando (no disponibles en este entorno): {no_disp}", file=sys.stderr)
        claves = [k for k in claves if metricas[k] is not None]
    if not claves:
        print("Nada para correr.", file=sys.stderr)
        sys.exit(1)

    modos = ["producto", "persona"] if args.por == "auto" else [args.por]

    base = None
    repo_id = None
    if args.guardar:
        try:
            base = Base()
            repo_id = base.repo_id(org, repo)
            base.commit()
        except Exception as exc:
            print(f"No se pudo conectar a la base ({exc}).", file=sys.stderr)
            print("Corré con --no-guardar, o levantá la base (db/README.md).", file=sys.stderr)
            sys.exit(1)

    ventanas = (ventanas_por_version_todas if args.con_canary else ventanas_por_version)(token, org, repo)

    print(f"Repo     : {org}/{repo}")
    print(f"Métricas : {len(claves)} -> {', '.join(claves)}")
    print(f"Modos    : {', '.join(modos)}")
    print(f"Ventanas : {len(ventanas)} (una por versión)")
    print(f"Guardar  : {'sí (tipo=' + TIPO_ANALISIS + ')' if base else 'no'}\n")

    resumen = []
    salida_json = []
    fallos_seguidos = 0
    for idx, key in enumerate(claves, 1):
        MetricClass = metricas[key]
        print(f"=== [{idx}/{len(claves)}] {key} ({MetricClass.__name__}) ===")
        if base is not None:
            base.ensure_metrica(key)
            base.commit()

        try:
            res = correr_metrica(key, MetricClass, ventanas, token, org, repo, modos)
        except Exception as exc:
            print(f"  fallo total: {exc}", file=sys.stderr)
            resumen.append((key, "-", 0, 0, len(ventanas)))
            fallos_seguidos += 1
            if fallos_seguidos >= 5:
                print("\n5 métricas seguidas fallaron por completo -> corto (¿rate limit?).", file=sys.stderr)
                break
            continue

        n_val = n_err = n_guardadas = 0
        for f in res["filas"]:
            fin_lbl = "ahora" if f["abierta"] else f["fin"].date().isoformat()
            cab = f"  [{f['n']:>2}] {f['version']:<6} {f['inicio'].date().isoformat()}->{fin_lbl}"
            if f["error"]:
                n_err += 1
                print(f"{cab}  ERROR ({f['por'] or '-'}): {f['error'][:120]}")
                continue
            print(f"{cab}  {f['por']:<8} = {_fmt(f['valor'])}")
            if f["valor"] is not None:
                n_val += 1
            if base is not None:
                try:
                    base.guardar_ventana(repo_id, key, TIPO_ANALISIS, f, f["por"], f["valor"])
                    base.commit()
                    n_guardadas += 1
                except Exception as exc:
                    base.con.rollback()
                    print(f"{cab}  ERROR guardando: {exc}", file=sys.stderr)

        resumen.append((key, ",".join(res["por"]) or "-", n_val, n_guardadas, n_err))
        fallos_seguidos = 0 if (n_val or n_guardadas) else fallos_seguidos + 1
        if fallos_seguidos >= 5:
            print("\n5 métricas seguidas sin ningún resultado -> corto (¿rate limit?).", file=sys.stderr)
            break

        salida_json.append({
            "metrica": key,
            "por": res["por"],
            "filas": [
                {"n": f["n"], "version": f["version"],
                 "inicio": f["inicio"].isoformat(), "fin": f["fin"].isoformat(),
                 "por": f["por"], "valor": f["valor"], "error": f["error"]}
                for f in res["filas"]
            ],
        })
        print()

    if base is not None:
        base.close()

    print("\n=== RESUMEN ===")
    print(f"{'metrica':28} {'por':16} {'con_valor':>9} {'guardadas':>9} {'errores':>7}")
    for key, por, n_val, n_g, n_err in resumen:
        print(f"{key:28} {por:16} {n_val:>9} {n_g:>9} {n_err:>7}")

    if args.json:
        Path(args.json).write_text(json.dumps({
            "repo": f"{org}/{repo}",
            "modos": modos,
            "generado_en": datetime.now(timezone.utc).isoformat(),
            "metricas": salida_json,
        }, ensure_ascii=False, indent=2))
        print(f"\nJSON escrito en {args.json}")


if __name__ == "__main__":
    main()
