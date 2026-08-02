import sys
from pathlib import Path

# ATENCIÓN — MÉTRICA REUTILIZADA, NO DUPLICADA:
# Esta planilla (consigna 40 - Adhesión a prácticas/políticas de desarrollo)
# incluye un algoritmo "calcular_number_of_closed_issues(metadata_issues,
# fecha_inicio, fecha_fin)" que cuenta issues cerrados dentro de una ventana
# de tiempo. Es exactamente la misma métrica NCI (Number of Closed Issues)
# ya implementada en metrics/35/nci.py (misma lógica: contar issues con
# closed_at dentro de [fecha_inicio, fecha_fin]).
#
# En vez de duplicar el fetch por GraphQL + paginación + lógica de conteo,
# este archivo reexporta la clase ya existente. Ver metrics/35/35 - Number
# of clossed issues.md para la ficha técnica completa y
# metrics/40/40 - NCI (reutilizada).md para la nota de reutilización
# específica de esta consigna.

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "35"))
from nci import NumberOfClosedIssues  # noqa: F401
