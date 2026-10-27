"""Sensibilidad de los cruces al corte de la historia: épocas del clustering temporal en lugar de períodos de calendario.

La regla de estabilidad pide el mismo signo en los cuatro períodos de calendario (generar_correlaciones.ETAPAS:
2016–2019, 2020–2022, 2023–2024, 2025–2026). Este script corre cruce_dimensiones.py sin modificarlo, con las
cuatro épocas que encuentra el clustering temporal (clustering_temporal.py), cortadas en el primer release
estable de cada una: 4.1.4 (4/12/2017), v12.0.5 (5/12/2021) y v14.1.1 (4/3/2024). Antes de cada par, el año de
cada ventana (que solo se usa para asignar el período) se reemplaza por el número de época.

Las columnas del CSV conservan los nombres de los períodos, pero contienen las épocas:
rho_2016_2019 = E1 (hasta dic 2017), rho_2020_2022 = E2 (hasta dic 2021), rho_2023_2024 = E3 (hasta mar 2024),
rho_2025_2026 = E4 (desde mar 2024).

Uso (desde la raíz del repo, con los PCA y clustering generados):
    POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/cruce_epocas.py \\
        Persona Proceso --config analisis/cruces/persona_proceso.json

Escribe en analisis/salidas/validaciones/cruce_epocas/<a>_<b>/ (no pisa la salida del cruce).
"""
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "analisis"))
import generar_correlaciones as gc  # noqa: E402

CORTES = ["20171204233132", "20211205010857", "20240304213137"]   # 4.1.4, v12.0.5, v14.1.1
gc.ETAPAS = [(n, i + 1, i + 1) for i, (n, *_) in enumerate(gc.ETAPAS)]


def epoca(fecha):
    return 1 + sum(str(fecha)[:14] >= c for c in CORTES)


def con_epoca(serie):
    return {p: (t[0], t[1], epoca(t[4]) if t[4] else None, t[3], t[4]) for p, t in serie.items()}


_compute_pair = gc.compute_pair
gc.compute_pair = lambda x_e, y_e, x_c, y_c, *a, **k: _compute_pair(con_epoca(x_e), con_epoca(y_e), x_c, y_c, *a, **k)

import cruce_dimensiones as cd  # noqa: E402
cd.SALIDA = ROOT / "analisis" / "salidas" / "validaciones" / "cruce_epocas"
sys.argv = ["cruce_dimensiones.py"] + sys.argv[1:]
cd.main()
