import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(Path(__file__).resolve().parent / "35"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "10"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "16"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "20"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "15"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "18"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "23"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "27"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "40"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "43"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "28"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "38"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "39"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "42"))
sys.path.insert(0, str(Path(__file__).resolve().parent / "Notion"))



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
from noi import NumberOfOpenIssues as NumberOfOpenIssuesRegistro28
from dev_experience import DevelopmentExperience
from nub import NumberOfBugsDetectedByUsers
from nob import NumberOfBranches
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


# --- Configuración ---
token = os.environ.get("GITHUB_TOKEN", "")
org   = os.environ.get("TARGET_ORG", "")
repo  = os.environ.get("TARGET_REPO", "")

now = datetime.now(timezone.utc)
fecha_inicio = now - timedelta(days=365)
fecha_fin    = now

metrica   = "nub"
por       = "producto"  # "producto" | "persona"
max_files = 500        # solo aplica a "cd": máximo de archivos a analizar

if not all([token, org, repo]):
    print("Faltan GITHUB_TOKEN, TARGET_ORG o TARGET_REPO en .env", file=sys.stderr)
    sys.exit(1)

print(f"Repo   : {org}/{repo}")
print(f"Período: {fecha_inicio.date()} → {fecha_fin.date()}")

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

metric = metricas[metrica](token, org, repo)
metric.run(fecha_inicio, fecha_fin, por=por, max_files=max_files)