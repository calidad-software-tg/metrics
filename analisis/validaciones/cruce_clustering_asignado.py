#!/usr/bin/env python3
"""Cruce con los grupos del clustering respetando la asignación de las métricas compartidas.

Ahora es una opción de cruces.py (--grupos <corte> --asignado): antes de armar cada grupo le saca las métricas
que la config asigna al otro lado, para que dos dimensiones que comparten métricas (Proceso–Producto) no
tengan grupos idénticos de los dos lados. Este script se mantiene con los argumentos de antes:

    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/cruce_clustering_asignado.py \\
        Proceso Producto analisis/cruces/proceso_producto_asignado.json [propio|pca]

Escribe en analisis/salidas/cruces/<a>_<b>/clustering_<corte>_asignado/.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cruces  # noqa: E402

dim_a, dim_b, config = sys.argv[1], sys.argv[2], sys.argv[3]
corte = sys.argv[4] if len(sys.argv) > 4 else "propio"
cruces.main([dim_a, dim_b, "--config", config, "--grupos", corte, "--asignado"])
