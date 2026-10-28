#!/usr/bin/env python3
"""Estabilidad de las relaciones dentro de cada dimensión con las épocas en lugar del calendario.

Ahora es una opción de correlaciones.py: `python3 analisis/correlaciones.py --periodos ambos` corre las dos y
escribe la comparación en analisis/salidas/periodos/. Este script reproduce la salida de antes, en
analisis/salidas/validaciones/estabilidad_epocas/ (con los pares entre dimensiones, como entonces):

    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/estabilidad_epocas.py calendario
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/estabilidad_epocas.py epocas
    python3 analisis/validaciones/estabilidad_epocas.py comparar
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import correlaciones  # noqa: E402

BASE = correlaciones.SALIDA / "validaciones" / "estabilidad_epocas"

modo = sys.argv[1] if len(sys.argv) > 1 else ""
if modo in ("calendario", "epocas"):
    correlaciones.correr(BASE / modo, modo, entre_dimensiones=True)
elif modo == "comparar":
    correlaciones.comparar_periodos(BASE / "calendario", BASE / "epocas", BASE)
else:
    sys.exit(__doc__)
