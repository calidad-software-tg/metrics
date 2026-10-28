#!/usr/bin/env python3
"""Nombre anterior de las épocas con todas las métricas, que pasaron a temporal.py (temporal.py epocas).

Uso (desde la raíz del repo, igual que antes):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/epocas_todas.py [carpeta_salida]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import temporal  # noqa: E402

temporal.epocas(sys.argv[1] if len(sys.argv) > 1 else None)
