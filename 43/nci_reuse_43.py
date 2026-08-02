import sys
from pathlib import Path

# ATENCIÓN — MÉTRICA REUTILIZADA, NO DUPLICADA:
# Esta planilla (consigna 43 - Tiempo promedio de resolución de problemas)
# incluye un algoritmo "calcular_nci(metadata_issues, fecha_inicio, fecha_fin)"
# que cuenta issues con state == 'closed' y closed_at dentro de una ventana
# de tiempo. Es exactamente la misma métrica NCI (Number of Closed Issues)
# ya implementada en metrics/35/nci.py y reutilizada previamente en
# metrics/40/nci_reuse.py.
#
# Esta es la TERCERA planilla del catálogo que llega a la misma
# operacionalización (throughput de cierre de issues) para tres consignas
# teóricas distintas (35, 40 y 43). Se reexporta la misma clase en vez de
# volver a duplicar el fetch por GraphQL + paginación + lógica de conteo.
# Ver metrics/35/35 - Number of clossed issues.md para la ficha técnica
# completa y metrics/43/43 - NCI (reutilizada).md para la nota específica
# de esta consigna.

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "35"))
from nci import NumberOfClosedIssues  # noqa: F401
