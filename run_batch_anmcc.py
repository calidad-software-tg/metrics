"""
Corre una métrica por producto para todos los repos GitHub en `repos`
y persiste resultados en `runs` + `results_producto`.

Uso:
    python run_batch_anmcc.py <metric_key>
    python run_batch_anmcc.py anmcc
    python run_batch_anmcc.py mttr
    python run_batch_anmcc.py loc_notion

Las métricas disponibles son las mismas que en run.py.
"""

import argparse
import inspect
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# --- cargar .env -----------------------------------------------------------
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

_root = Path(__file__).resolve().parent
for _d in ["35", "10", "16", "20", "15", "18", "23", "27", "40", "43", "28", "38", "39", "42", "Notion"]:
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
try:
    from open_issues import NumberOfOpenIssues as NumberOfOpenIssuesRegistro28
except ImportError:
    NumberOfOpenIssuesRegistro28 = None
try:
    from dev_experience import DevelopmentExperience
except ImportError:
    DevelopmentExperience = None
try:
    from user_reported_bugs import NumberOfBugsDetectedByUsers
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

import psycopg2

# --- config ----------------------------------------------------------------
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not GITHUB_TOKEN:
    print("Falta GITHUB_TOKEN en .env", file=sys.stderr)
    sys.exit(1)

DB_HOST     = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT     = os.environ.get("POSTGRES_PORT", "5432")
DB_USER     = os.environ.get("POSTGRES_USER", "metricas")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "metricas")
DB_NAME     = os.environ.get("POSTGRES_DB", "resultados_metricas")

DIAS = 365

# --- mismo dict que run.py -------------------------------------------------
metricas = {
    "nci":   NumberOfClosedIssues,
    "anmcc": AverageNumberOfModifiedComponentsPerCommit,
    "mttr":  MeanTimeToRepair,
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

# ---------------------------------------------------------------------------


def _do_fetch(metric, fecha_inicio, fecha_fin):
    """Llama fetch con fechas si el método las acepta, sin ellas si no."""
    sig = inspect.signature(metric.fetch)
    if "fecha_inicio" in sig.parameters:
        metric.fetch(fecha_inicio, fecha_fin)
    else:
        metric.fetch()


def _conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, dbname=DB_NAME,
    )


def _ensure_metric_catalog(cur):
    seed_path = Path(__file__).resolve().parent / "db" / "metrics_seed.sql"
    cur.execute(seed_path.read_text())


def _fetch_repos(cur):
    cur.execute(
        "SELECT repo_id, org, repo FROM repos WHERE plataforma = 'GitHub' ORDER BY repo_id"
    )
    return cur.fetchall()


def _insert_run(cur, repo_id, fecha_inicio, fecha_fin, ejecutado_en):
    cur.execute(
        """
        INSERT INTO runs (repo_id, fecha_inicio, fecha_fin, ejecutado_en)
        VALUES (%s, %s, %s, %s)
        RETURNING run_id
        """,
        (repo_id, fecha_inicio, fecha_fin, ejecutado_en),
    )
    return cur.fetchone()[0]


def _upsert_result(cur, run_id, metric_key, value):
    if isinstance(value, dict):
        cur.execute(
            """
            INSERT INTO results_producto (run_id, metric_key, value, value_extra)
            VALUES (%s, %s, NULL, %s)
            ON CONFLICT (run_id, metric_key) DO UPDATE
                SET value = NULL, value_extra = EXCLUDED.value_extra
            """,
            (run_id, metric_key, json.dumps(value)),
        )
    else:
        cur.execute(
            """
            INSERT INTO results_producto (run_id, metric_key, value)
            VALUES (%s, %s, %s)
            ON CONFLICT (run_id, metric_key) DO UPDATE SET value = EXCLUDED.value
            """,
            (run_id, metric_key, float(value) if value is not None else None),
        )


def main():
    parser = argparse.ArgumentParser(description="Batch runner de métricas por producto")
    parser.add_argument("metric", choices=sorted(metricas.keys()), help="Clave de la métrica")
    parser.add_argument("--desde", metavar="REPO", help="Empezar desde este repo (ej: flutter/flutter)")
    args = parser.parse_args()

    metric_key   = args.metric
    MetricClass  = metricas[metric_key]

    now          = datetime.now(timezone.utc)
    fecha_inicio = now - timedelta(days=DIAS)
    fecha_fin    = now

    con = _conn()
    cur = con.cursor()
    _ensure_metric_catalog(cur)
    con.commit()

    repos = _fetch_repos(cur)

    if args.desde:
        desde = args.desde.lower()
        repos_filtrados = [(rid, org, repo) for rid, org, repo in repos if f"{org}/{repo}".lower() >= desde]
        print(f"Saltando hasta: {args.desde} ({len(repos) - len(repos_filtrados)} repos omitidos)")
        repos = repos_filtrados

    print(f"Métrica : {metric_key}")
    print(f"Repos   : {len(repos)}")
    print(f"Período : {fecha_inicio.date()} → {fecha_fin.date()}\n")

    for repo_id, org, repo in repos:
        print(f"[{org}/{repo}]")
        try:
            metric = MetricClass(GITHUB_TOKEN, org, repo)
            _do_fetch(metric, fecha_inicio, fecha_fin)
            value = metric.por_producto(fecha_inicio, fecha_fin)
            print(f"  {metric_key} = {value}")

            run_id = _insert_run(cur, repo_id, fecha_inicio, fecha_fin, now)
            _upsert_result(cur, run_id, metric_key, value)
            con.commit()
            print(f"  Persistido (run_id={run_id})")
        except (Exception, SystemExit) as exc:
            con.rollback()
            print(f"  ERROR: {exc}", file=sys.stderr)

    cur.close()
    con.close()
    print("\nListo.")


if __name__ == "__main__":
    main()
