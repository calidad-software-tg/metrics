"""
Dónde lee y escribe el análisis. Todas las rutas salen de acá.

    datos/                                   entradas generadas por metricas/ (export_persona.py)
    salidas/
      LEEME.md                               índice: qué mirar primero
      1_variables/                           diccionario de variables (qué se mide y cómo)
      2_dimensiones/
        correlaciones/                       pares dentro de cada dimensión
        persona|proceso|producto/            PCA y agrupamiento de la dimensión
      3_cruces/<dima>_<dimb>/                pares entre dos dimensiones, componentes y red
      4_tres_dimensiones/                    asociación global, cadenas y perfiles
      5_patrones/                            RESULTADO: patrones validados y cadenas
        correlaciones/                       todos los pares, con sus controles
      6_robustez/
        multiverso_asignacion/               según a qué dimensión se asignan las métricas compartidas
        metricas_compartidas/                cruces sin las métricas que comparten dos dimensiones
      reportes/                              HTML interactivos, uno por nivel de análisis:
        intradimensional.html                cada dimensión: correlaciones, PCA y agrupamiento
        bidimensional.html                   cada par de dimensiones
        tridimensional.html                  las tres dimensiones a la vez
      complementarios/                       análisis complementarios (periodos, épocas, alternativas, rezago, pesos)

Las carpetas base se pueden mover con TRES_P_DATOS y TRES_P_SALIDAS (ver proyecto.py).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import proyecto  # noqa: E402

DATOS = proyecto.DATOS
SALIDAS = proyecto.SALIDAS

AGREGADO_PERSONA = DATOS / "persona_agregado_estable_canary.csv"

VARIABLES = SALIDAS / "1_variables"
DICCIONARIO = VARIABLES / "diccionario_variables.csv"

DIMENSIONES = SALIDAS / "2_dimensiones"
CORRELACIONES = DIMENSIONES / "correlaciones"

CRUCES = SALIDAS / "3_cruces"
TRES_DIMENSIONES = SALIDAS / "4_tres_dimensiones"

PATRONES = SALIDAS / "5_patrones"
PATRONES_BASE = PATRONES / "correlaciones"

ROBUSTEZ = SALIDAS / "6_robustez"
MULTIVERSO = ROBUSTEZ / "multiverso_asignacion"
METRICAS_COMPARTIDAS = ROBUSTEZ / "metricas_compartidas"

REPORTES = SALIDAS / "reportes"
# Los generadores de reportes escriben acá; reportes.py los reúne en tres páginas y borra la carpeta.
REPORTES_PARTES = REPORTES / "_partes"
REPORTES_DIMENSIONES = REPORTES_PARTES / "intradimensional"
REPORTES_CRUCES = REPORTES_PARTES / "bidimensional"
REPORTES_TRES = REPORTES_PARTES / "tridimensional"
COMPLEMENTARIOS = SALIDAS / "complementarios"


def dimension(dim):
    """Carpeta del PCA y el agrupamiento de una dimensión (Persona, Proceso o Producto)."""
    return DIMENSIONES / dim.lower()


def cruce(dim_a, dim_b):
    return CRUCES / f"{dim_a.lower()}_{dim_b.lower()}"


def omitido(clave, sub=None):
    """Por qué se salteó un paso en la última corrida de tres_p.py analizar (salidas/omitidos.json), o ""."""
    import json
    f = SALIDAS / "omitidos.json"
    if not f.exists():
        return ""
    try:
        v = json.loads(f.read_text(encoding="utf-8")).get(clave, "")
    except ValueError:
        return ""
    if sub is not None:
        v = v.get(sub, "") if isinstance(v, dict) else ""
    return v if isinstance(v, str) else ""
