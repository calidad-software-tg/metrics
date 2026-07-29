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

from nci import NumberOfClosedIssues
from anmcc import AverageNumberOfModifiedComponentsPerCommit
from mttr import MeanTimeToRepair
from cd import CommentDensity

# --- Configuración ---
token = os.environ.get("GITHUB_TOKEN", "")
org   = os.environ.get("TARGET_ORG", "")
repo  = os.environ.get("TARGET_REPO", "")

now = datetime.now(timezone.utc)
fecha_inicio = now - timedelta(days=365)
fecha_fin    = now

metrica   = "cd"
por       = "persona"  # "producto" | "persona"
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
}

metric = metricas[metrica](token, org, repo)
metric.run(fecha_inicio, fecha_fin, por=por, max_files=max_files)