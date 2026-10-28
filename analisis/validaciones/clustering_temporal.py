#!/usr/bin/env python3
"""Nombre anterior del clustering temporal de releases, que pasó a temporal.py (temporal.py releases).

Uso (desde la raíz del repo, igual que antes):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/clustering_temporal.py [carpeta_salida]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import temporal  # noqa: E402

temporal.clustering_releases(sys.argv[1] if len(sys.argv) > 1 else None)
