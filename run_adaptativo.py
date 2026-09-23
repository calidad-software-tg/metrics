"""
Corre las métricas ya date-aware sobre los períodos 'adaptativo' de un repo
(generados por generar_bloques.py) y persiste en `resultado`.

No toca run_batch_anmcc.py -- es un runner nuevo, independiente, pensado
para correr un solo repo sobre la tabla `periodo` en vez de una ventana
fija global sobre los 10 repos.

Uso:
    python run_adaptativo.py tldr-pages/tldr
    python run_adaptativo.py tldr-pages/tldr --metric nci
    python run_adaptativo.py tldr-pages/tldr --solo-baratas
    python run_adaptativo.py tldr-pages/tldr --solo-caras --max-files 80
"""

import argparse
import inspect
import json
import os
import sys
from pathlib import Path

# --- cargar .env (raíz + db/) ------------------------------------------
_root = Path(__file__).resolve().parent
for _envf in [_root / ".env", _root / "db" / ".env"]:
    if _envf.exists():
        for line in _envf.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

for _d in ["35", "10", "16", "20", "15", "18", "23", "27", "38", "39", "40", "42", "43", "Notion"]:
    sys.path.insert(0, str(_root / _d))

from nci import NumberOfClosedIssues
from anmcc import AverageNumberOfModifiedComponentsPerCommit
from mttr import MeanTimeToRepair
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
from dev_experience import DevelopmentExperience
from nub import NumberOfBugsDetectedByUsers
from nob import NumberOfBranches

import psycopg2

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
DB_HOST     = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT     = os.environ.get("POSTGRES_PORT", "5432")
DB_USER     = os.environ.get("POSTGRES_USER", "metricas")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "metricas")
DB_NAME     = os.environ.get("POSTGRES_DB", "resultados_metricas")

# El metrica_id de la tabla `metrica` NO coincide con la clave corta que usa
# el código (lo genera metrics_seed.sql desde el Excel, con slugs propios:
# 'nci' -> 'number_of_closed_issues', 'wp' -> 'wiki_presence', etc). Acá cada
# entrada es (Clase, metrica_id real) para no romper la FK de `resultado`.
#
# Quedan afuera a propósito (duplicados exactos de otra clave, mismo
# metrica_id -- correrlas las dos pisaría la fila o violaría el índice único):
#   - nci_process (40/nci_reuse.py) y nci_resolution_time (43/nci_reuse_43.py):
#     mismo id_registro "35, 40, 43" que nci -> mismo metrica_id
#     'number_of_closed_issues'. Se corre solo nci (35, la más completa).
#   - sc_disc (18/sc.py): reexporta la misma clase que sc (20/dc.py) literal,
#     mismo id_registro "18, 20" -> mismo metrica_id 'social_contributions_sc'.
#
# Gaps conocidos, sin cubrir hoy (no hay -- o no alcanza -- código para esa
# fila puntual de `metrica`, aunque sí para una relacionada):
#   - mtbf / mttf: mttr.py solo calcula MTTR, no las otras dos.
#   - developer_contribution_dc (id_registro "18, 20"): fila separada de
#     social_contributions_sc en la base, sin implementación propia distinta.
#   - number_of_pull_request_of_core_developers_rejected: CoreDevsPullRequests
#     calcula "rechazadas" también, pero acá solo se persiste bajo
#     number_of_pull_requests_of_core_devs (value_extra trae ambas).
METRICAS_BARATAS = {
    "nci":   (NumberOfClosedIssues, "number_of_closed_issues"),
    "anmcc": (AverageNumberOfModifiedComponentsPerCommit, "anmcc"),
    "mttr":  (MeanTimeToRepair, "mttr"),
    "wp":    (WikiPresence, "wiki_presence"),
    "dis":   (DocIssueSurvival, "doc_issue_survival"),
    "sc":    (SocialContribution, "social_contributions_sc"),
    "le":      (LearningEase, "learning_easy"),
    "ss":      (SkillSimilarity, "skill_similarity"),
    "rexp":    (RecentExperience, "rexp"),
    "fexp":    (FileExperience, "fexp"),
    "exprev":  (ReviewExperience, "exprev"),
    "rexprev": (RecentReviewExperience, "rexprev"),
    "cdiv":    (ContributionDiversity, "contribution_diversity"),
    "nc":              (NumberOfComments, "number_of_comments"),
    "disc_centrality": (DiscussionCentrality, "discussion_centrality"),
    "schedule_compliance": (ScheduleCompliance, "schedule_compliance"),
    "cfdr": (CustomerFoundDefectsAndRegressions, "cfdr"),
    "process_performance": (DevelopmentProcessPerformance, "development_process_performance"),
    "noi": (NumberOfOpenIssues, "number_of_open_issues"),
    "jarczyk_success_rate": (JarczykSuccessRate, "tasa_de_exito_de_jarczyk"),
    "collab_notion": (NumberOfCollaborators, "number_of_collaborators"),
    "commit_freq_notion": (CommitFrequency, "commit_frequency"),
    "commit_entropy_notion": (CommitEntropy, "commit_entropy"),
    "commits_per_author_notion": (CommitsPerAuthor, "developer_contribution"),
    "forks_notion": (NumberOfForks, "number_of_forks"),
    "issues_total_notion": (TotalIssues, "total_de_issues"),
    "prs_summary_notion": (PullRequestsSummary, "pull_requests_summary"),
    "core_devs_prs_notion": (CoreDevsPullRequests, "number_of_pull_requests_of_core_devs"),
    "dev_exp": (DevelopmentExperience, "development_experience"),
    "nub": (NumberOfBugsDetectedByUsers, "number_of_bugs_detected_by_users"),
    "nob_42": (NumberOfBranches, "number_of_branches"),
}

# Caras: fetch() por período recorre el árbol de archivos y hace 1 request
# (REST blob o GraphQL blame) POR ARCHIVO encontrado. Correrlas en todos los
# períodos multiplica rápido -- usar --max-files chico.
METRICAS_CARAS = {
    "cd":    (CommentDensity, "cd"),
    "rc":    (ReadmeCompleteness, "readme_completeness"),
    "dloc":  (DocumentationLinesOfCode, "dloc"),
    "loc_notion": (LinesOfCode, "lines_of_code"),
    "developer_ownership_notion": (DeveloperOwnership, "developer_ownership"),
    "ci_presence_notion": (ContinuousIntegrationPresence, "continuous_integration"),  # barata en los hechos (4-5 requests fijos), pero comparte el fetch(fecha_fin) por período
}

metricas = {**METRICAS_BARATAS, **METRICAS_CARAS}


_SIN_VALOR = object()  # sentinel: distingue "por_producto no calculó nada" de "calculó None/0"


def _conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER,
                             password=DB_PASSWORD, dbname=DB_NAME)


def _fetch_mode(metric) -> str:
    params = inspect.signature(metric.fetch).parameters
    if "fecha_inicio" in params and "fecha_fin" in params:
        return "windowed2"
    if "fecha_fin" in params:
        return "windowed1"
    return "full"


def _call_fetch(metric, mode, fecha_inicio, fecha_fin, **extra):
    if mode == "windowed2":
        metric.fetch(fecha_inicio, fecha_fin, **extra)
    elif mode == "windowed1":
        metric.fetch(fecha_fin, **extra)
    else:
        metric.fetch(**extra)


def _upsert_resultado(cur, periodo_id, metrica_id, value, contribuyente_login=None):
    if isinstance(value, dict):
        cur.execute(
            """INSERT INTO resultado (periodo_id, metrica_id, contribuyente_login, value, value_extra)
               VALUES (%s, %s, %s, NULL, %s)""",
            (periodo_id, metrica_id, contribuyente_login, json.dumps(value, default=str)),
        )
    else:
        try:
            v = float(value) if value is not None else None
        except (TypeError, ValueError):
            v = None
        cur.execute(
            """INSERT INTO resultado (periodo_id, metrica_id, contribuyente_login, value)
               VALUES (%s, %s, %s, %s)""",
            (periodo_id, metrica_id, contribuyente_login, v),
        )


def _procesar_metrica(key: str, org: str, repo: str, periodos: list, max_files: int | None) -> str:
    """Corre UNA métrica sobre todos los períodos. Abre su propia conexión a
    la base (una conexión de psycopg2 no se puede compartir entre hilos)."""
    MetricClass, metrica_id = metricas[key]
    prefijo = f"[{key}]"
    con = _conn()
    cur = con.cursor()
    try:
        try:
            metric = MetricClass(GITHUB_TOKEN, org, repo)
        except Exception as exc:
            print(f"{prefijo} ERROR instanciando: {exc}", file=sys.stderr)
            return f"{prefijo} ERROR instanciando: {exc}"

        mode = _fetch_mode(metric)
        extra = {}
        if key in METRICAS_CARAS and max_files:
            extra["max_files"] = max_files

        # Resume por período: si esta métrica ya tiene datos guardados para
        # algunos períodos (una corrida anterior que se cortó a la mitad,
        # por red o lo que sea), no se vuelven a pedir ni a recalcular.
        # Solo se procesan los que faltan. (--forzar ya limpió todo antes de
        # llegar acá, así que en ese caso esto da un set vacío.)
        cur.execute(
            "SELECT DISTINCT periodo_id FROM resultado WHERE metrica_id = %s AND periodo_id = ANY(%s)",
            (metrica_id, [p[0] for p in periodos]),
        )
        ya_hechos = {row[0] for row in cur.fetchall()}
        periodos_pendientes = [p for p in periodos if p[0] not in ya_hechos]
        if ya_hechos:
            print(f"{prefijo} {len(ya_hechos)}/{len(periodos)} períodos ya calculados, retomando el resto...")
        if not periodos_pendientes:
            print(f"{prefijo} ya estaba completa.")
            return f"{prefijo} ya estaba completa"

        if mode == "full":
            try:
                metric.fetch(**extra)
            except (Exception, SystemExit) as exc:
                print(f"{prefijo} ERROR fetch (full): {exc}", file=sys.stderr)
                return f"{prefijo} ERROR fetch (full): {exc}"

        ok, fallidos = 0, 0
        for periodo_id, periodo_num, f_ini, f_fin in periodos_pendientes:
            if mode != "full":
                try:
                    _call_fetch(metric, mode, f_ini, f_fin, **extra)
                except (Exception, SystemExit) as exc:
                    print(f"{prefijo} período {periodo_num}: ERROR fetch: {exc}", file=sys.stderr)
                    fallidos += 1
                    continue

            escrito_algo = False

            try:
                valor = metric.por_producto(f_ini, f_fin)
            except (Exception, SystemExit, NotImplementedError):
                valor = _SIN_VALOR
            if valor is not _SIN_VALOR:
                try:
                    _upsert_resultado(cur, periodo_id, metrica_id, valor)
                    escrito_algo = True
                except psycopg2.Error as exc:
                    con.rollback()
                    print(f"{prefijo} período {periodo_num}: ERROR insert (producto): {exc}", file=sys.stderr)

            try:
                valores_persona = metric.por_persona(f_ini, f_fin)
            except (Exception, SystemExit, NotImplementedError):
                valores_persona = None
            if isinstance(valores_persona, dict):
                for login, v in valores_persona.items():
                    try:
                        _upsert_resultado(cur, periodo_id, metrica_id, v, contribuyente_login=login)
                        escrito_algo = True
                    except psycopg2.Error as exc:
                        con.rollback()
                        print(f"{prefijo} período {periodo_num}: ERROR insert (persona={login}): {exc}",
                              file=sys.stderr)

            con.commit()
            if escrito_algo:
                ok += 1

        total_ok = ok + len(ya_hechos)
        print(f"{prefijo} listo: {total_ok}/{len(periodos)} períodos con datos "
              f"({ok} nuevos esta corrida), {fallidos} con error de fetch.")
        return f"{prefijo} {total_ok}/{len(periodos)} ok, {fallidos} fallidos"
    finally:
        cur.close()
        con.close()


def main():
    parser = argparse.ArgumentParser(description="Corre métricas sobre los períodos adaptativos de un repo")
    parser.add_argument("repo", help="org/repo, ej: tldr-pages/tldr")
    parser.add_argument("--tipo-analisis", default="adaptativo")
    parser.add_argument("--metric", help="correr una sola métrica (clave)")
    parser.add_argument("--solo-baratas", action="store_true")
    parser.add_argument("--solo-caras", action="store_true")
    parser.add_argument("--max-files", type=int, default=None,
                         help="tope de archivos para cd/dloc/loc_notion/developer_ownership_notion "
                              "(default de cada métrica si no se pasa)")
    parser.add_argument("--threads", type=int, default=1,
                         help="cuántas métricas correr en paralelo (cada una con su propia conexión a la base)")
    parser.add_argument("--forzar", action="store_true",
                         help="recalcular igual las métricas que ya tienen los 66 períodos completos "
                              "(por default, si no se pasa --metric, esas se saltean)")
    parser.add_argument("--excepto", default="",
                         help="claves separadas por coma a excluir de esta corrida, ej: "
                              "disc_centrality,nc,exprev,rexprev")
    args = parser.parse_args()

    if not GITHUB_TOKEN:
        print("Falta GITHUB_TOKEN en .env", file=sys.stderr)
        sys.exit(1)

    org, repo = args.repo.split("/", 1)

    con = _conn()
    cur = con.cursor()
    cur.execute("SELECT repo_id FROM repos WHERE full_name = %s", (f"{org}/{repo}",))
    row = cur.fetchone()
    if row is None:
        print(f"{org}/{repo} no está en repos. Cargá repos_seed.sql.", file=sys.stderr)
        sys.exit(1)
    repo_id = row[0]

    cur.execute(
        """SELECT periodo_id, periodo_num, fecha_inicio, fecha_fin
           FROM periodo WHERE repo_id = %s AND tipo_analisis = %s ORDER BY periodo_num""",
        (repo_id, args.tipo_analisis),
    )
    periodos = cur.fetchall()
    if not periodos:
        print(f"No hay períodos '{args.tipo_analisis}' para {org}/{repo}. "
              f"Corré generar_bloques.py primero.", file=sys.stderr)
        sys.exit(1)
    print(f"Repo: {org}/{repo}  (repo_id={repo_id})  |  {len(periodos)} períodos '{args.tipo_analisis}'")

    if args.metric:
        keys = [args.metric]
    elif args.solo_baratas:
        keys = sorted(METRICAS_BARATAS.keys())
    elif args.solo_caras:
        keys = sorted(METRICAS_CARAS.keys())
    else:
        keys = sorted(metricas.keys())

    if args.excepto:
        excluir = {k.strip() for k in args.excepto.split(",") if k.strip()}
        antes = len(keys)
        keys = [k for k in keys if k not in excluir]
        if len(keys) < antes:
            print(f"Excluyendo {antes - len(keys)} métrica(s) por --excepto: {', '.join(sorted(excluir))}")

    if not args.metric and not args.forzar:
        cur.execute(
            """SELECT res.metrica_id, count(DISTINCT res.periodo_id) FROM resultado res
               JOIN periodo per ON per.periodo_id = res.periodo_id
               WHERE per.repo_id = %s AND per.tipo_analisis = %s
               GROUP BY res.metrica_id""",
            (repo_id, args.tipo_analisis),
        )
        completas = {mid for mid, n in cur.fetchall() if n >= len(periodos)}
        antes = len(keys)
        keys = [k for k in keys if metricas[k][1] not in completas]
        saltadas = antes - len(keys)
        if saltadas:
            print(f"Saltando {saltadas} métrica(s) que ya tienen los {len(periodos)} períodos completos "
                  f"(usá --forzar para recalcularlas igual).")
        if not keys:
            print("No queda nada por correr.")
            cur.close()
            con.close()
            return

    metrica_ids = [metricas[k][1] for k in keys]
    periodo_ids = [p[0] for p in periodos]
    if args.forzar:
        # --forzar es un recálculo explícito: borra lo que haya, sin
        # confiar en el skip por período (útil después de un cambio de
        # código en la fórmula, donde los datos viejos ya no son válidos).
        cur.execute(
            "DELETE FROM resultado WHERE periodo_id = ANY(%s) AND metrica_id = ANY(%s)",
            (periodo_ids, metrica_ids),
        )
        con.commit()
    con.close()

    print(f"Corriendo {len(keys)} métricas con --threads {args.threads}...\n")

    if args.threads <= 1:
        for key in keys:
            _procesar_metrica(key, org, repo, periodos, args.max_files)
    else:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=args.threads) as pool:
            futuros = {pool.submit(_procesar_metrica, key, org, repo, periodos, args.max_files): key
                       for key in keys}
            for fut in as_completed(futuros):
                key = futuros[fut]
                try:
                    fut.result()
                except Exception as exc:
                    print(f"[{key}] ERROR no capturado: {exc}", file=sys.stderr)

    print("\nListo.")


if __name__ == "__main__":
    main()
