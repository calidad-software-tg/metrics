"""
Configuración del proyecto analizado.

Lee el archivo de proyecto (por defecto `proyecto.json` en la raíz, o el que indique la variable
TRES_P_PROYECTO) y expone los valores que antes estaban fijos para vercel/next.js:

    repo             "org/nombre" del repositorio analizado
    hasta            fecha de corte de las ventanas (AAAA-MM-DD) o null = hoy
    excluir_estable  tags que no se usan en la serie estable (ej. prereleases mal etiquetados)
    calendario       [[etiqueta, año_desde, año_hasta], ...] o "auto"
    cortes_epocas    [tag, tag, tag] (primer release de cada época) o "auto"
    descartados      CSV con las relaciones descartadas al validarlas (x, y, motivo) o null

Con "auto", el calendario reparte los años de la historia en cuatro períodos contiguos y las
épocas cortan la serie estable en cuartos (por número de release). Los dos se calculan desde la
base, que tiene que tener las ventanas de la serie estable ya calculadas.

Cada proyecto usa su propia base (POSTGRES_DB): los scripts de análisis no filtran por repositorio.
"""

import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Lo que genera el pipeline queda fuera de las carpetas de código:
#   datos/    métricas por persona e identidades unificadas (export_persona, mapear_identidades)
#   salidas/  resultados del análisis (ver salidas/LEEME.md)
DATOS = Path(os.environ.get("TRES_P_DATOS") or ROOT / "datos")
SALIDAS = Path(os.environ.get("TRES_P_SALIDAS") or ROOT / "salidas")

_env = ROOT / ".env"
if _env.exists():
    for _l in _env.read_text().splitlines():
        if "=" in _l and not _l.lstrip().startswith("#"):
            _k, _v = _l.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

RUTA = Path(os.environ.get("TRES_P_PROYECTO", ROOT / "proyecto.json"))
CFG = json.loads(RUTA.read_text(encoding="utf-8")) if RUTA.exists() else {}

REPO = CFG.get("repo") or os.environ.get("TRES_P_REPO", "")
HASTA = CFG.get("hasta")
# Nunca vacío: las consultas usan "etiqueta NOT IN %s" y () no es SQL válido.
EXCLUIR_ESTABLE = frozenset(CFG.get("excluir_estable") or ["__sin_tags_excluidos__"])


def db_config():
    return dict(host=os.environ.get("POSTGRES_HOST", "localhost"),
                port=int(os.environ.get("POSTGRES_PORT", 5432)),
                dbname=os.environ.get("POSTGRES_DB", "resultados_metricas"),
                user=os.environ.get("POSTGRES_USER", "metricas"),
                password=os.environ.get("POSTGRES_PASSWORD", "metricas"))


def _es_backport(versiones):
    marca, maximo = [], -1
    for v in versiones:
        try:
            mayor = int(str(v).lstrip("vV").split(".")[0])
        except ValueError:
            marca.append(False)
            continue
        marca.append(mayor < maximo)
        maximo = max(maximo, mayor)
    return marca


def _serie_estable():
    """[(periodo_num, etiqueta, año_inicio)] de la serie estable, sin excluidos ni backports."""
    import psycopg2
    con = psycopg2.connect(**db_config())
    try:
        cur = con.cursor()
        cur.execute("""SELECT periodo_num, etiqueta, EXTRACT(YEAR FROM fecha_inicio)::int
                       FROM periodo WHERE tipo_analisis = 'versiones' ORDER BY periodo_num""")
        filas = [f for f in cur.fetchall() if f[1] not in EXCLUIR_ESTABLE]
    finally:
        con.close()
    bp = _es_backport([f[1] for f in filas])
    return [f for f, b in zip(filas, bp) if not b]


def _calendario_auto():
    filas = _serie_estable()
    if not filas:
        raise RuntimeError("calendario 'auto': la base no tiene ventanas de la serie estable")
    y0, y1 = min(f[2] for f in filas), max(f[2] for f in filas)
    anios = list(range(y0, y1 + 1))
    n = min(4, len(anios))
    grupos, i = [], 0
    for k in range(n):
        tam = len(anios) // n + (1 if k < len(anios) % n else 0)
        g = anios[i:i + tam]
        i += tam
        grupos.append((f"{g[0]}-{g[-1]}" if len(g) > 1 else str(g[0]), g[0], g[-1]))
    return grupos


def _cortes_auto():
    filas = _serie_estable()
    if len(filas) < 8:
        raise RuntimeError("cortes_epocas 'auto': hacen falta al menos 8 releases estables")
    n = len(filas)
    return tuple(filas[int(n * q)][1] for q in (0.25, 0.5, 0.75))


def _resolver(clave, auto):
    v = CFG.get(clave, "auto")
    if v in (None, "auto"):
        try:
            return auto()
        except Exception as exc:  # sin base o sin datos: se avisa cuando se usa
            print(f"[proyecto] {clave} 'auto' no disponible todavía: {exc}")
            return None
    return v


CALENDARIO = _resolver("calendario", _calendario_auto)
if CALENDARIO:
    CALENDARIO = [tuple(e) for e in CALENDARIO]
CORTES_EPOCAS = _resolver("cortes_epocas", _cortes_auto)
if CORTES_EPOCAS:
    CORTES_EPOCAS = tuple(CORTES_EPOCAS)


def descartados():
    """{frozenset((x, y)): motivo} de las relaciones descartadas al validarlas en este proyecto."""
    ruta = CFG.get("descartados")
    if not ruta:
        return {}
    ruta = Path(ruta)
    if not ruta.is_absolute():
        # relativo a proyecto.json o, si no está ahí, a la raíz del repositorio
        ruta = next((p for p in (RUTA.parent / ruta, ROOT / ruta) if p.exists()), RUTA.parent / ruta)
    with open(ruta, newline="", encoding="utf-8") as f:
        return {frozenset((r["x"], r["y"])): r["motivo"] for r in csv.DictReader(f)}
