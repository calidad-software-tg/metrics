import sys
from pathlib import Path

# ATENCIÓN — MÉTRICA REUTILIZADA, NO DUPLICADA:
# "Social Contributions (SC)" en esta consigna (18/19 - Frecuencia de
# participación en discusiones técnicas) tiene exactamente la misma fórmula
# (Falcão et al., 2020) que "Social Contributions (SC)" ya implementada para
# la consigna 20 (Contribución a proyectos del equipo) en metrics/20/dc.py.
# En vez de copiar ~100 líneas de código idéntico (fetch de issues/PRs vía
# GraphQL + suma de issues_opened/closed + prs_opened/closed/merged), este
# archivo reexporta esa misma clase. Ver metrics/20/20 - Social Contribution.md
# para la ficha técnica completa y metrics/18/18 - Social Contributions.md
# para la nota de reutilización específica de esta consigna.

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "20"))
from dc import SocialContribution  # noqa: F401
