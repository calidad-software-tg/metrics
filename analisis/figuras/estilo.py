"""Estilo común de las figuras del informe (capítulos 4 y 5).

Todas las figuras son estáticas (PNG a 300 dpi + SVG), Times New Roman, fondo blanco y sin título
(el título va en el informe). Los colores por dimensión y la escala divergente son los del informe.
"""
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[2]
SALIDAS = ROOT / "analisis" / "salidas"
FIGURAS = SALIDAS / "figuras"

CM = 1 / 2.54
ANCHO = 16 * CM            # ancho de página
ALTO = 10 * CM             # alto por defecto

# ── colores ──────────────────────────────────────────────────────────────────
DIM = {"Persona": "#d9520b", "Proceso": "#3149c4", "Producto": "#0a8263"}
AZUL, GRIS0, ROJO = "#2a78d6", "#f0efec", "#e34948"
TEXTO2 = "#6b6b6b"         # texto secundario
DESCARTE = "#b5b5b5"       # descartados / mecánicos
OSCURO = "#3a3a3a"         # barras neutras
GUIA = "#d8d8d8"           # líneas guía
CMAP_RHO = LinearSegmentedColormap.from_list("rho", [AZUL, GRIS0, ROJO])


def par_color(a, b):
    """Color de un par de dimensiones: mezcla simple de los dos colores."""
    import numpy as np
    ca, cb = (np.array(mpl.colors.to_rgb(DIM[d])) for d in (a, b))
    return tuple((ca + cb) / 2)


def aplicar():
    fuentes = ["Times New Roman", "Liberation Serif", "DejaVu Serif"]
    mpl.rcParams.update({
        "font.family": "serif", "font.serif": fuentes, "mathtext.fontset": "stix",
        "font.size": 9, "axes.labelsize": 9, "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 8,
        "axes.edgecolor": "#444444", "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.color": "#333333", "ytick.color": "#333333", "text.color": "#111111",
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "legend.frameon": False, "hatch.linewidth": 0.6, "svg.fonttype": "none",
        "axes.unicode_minus": True, "axes.formatter.use_locale": False,
    })


# ── números en formato español ───────────────────────────────────────────────
MENOS = "−"


def rho(v, dec=2, signo=True):
    """+0,47 / −0,12 / 0,00 con coma decimal y signo menos tipográfico."""
    if v is None or v != v:
        return "—"
    s = f"{abs(v):.{dec}f}".replace(".", ",")
    if round(v, dec) == 0:
        return s
    return (("+" if signo else "") if v > 0 else MENOS) + s


def entero(n):
    return f"{int(n):,}".replace(",", ".")


def pct(v, dec=0):
    return f"{v:.{dec}f}".replace(".", ",") + " %"


def eje_rho(ax, eje="x"):
    fmt = mpl.ticker.FuncFormatter(lambda v, _: rho(v, 1) if abs(v) > 1e-9 else "0")
    (ax.xaxis if eje == "x" else ax.yaxis).set_major_formatter(fmt)


# ── nombres legibles (nunca el id de la variable) ────────────────────────────
NOMBRES = {
    "prop_commitean_ratio": "Proporción que commitea",
    "prop_cierran_ratio": "Proporción que cierra issues",
    "prop_comentan_ratio": "Proporción que comenta",
    "tasa_nuevos_commits_ratio": "Tasa de ingreso (commits)",
    "tasa_nuevos_interaccion_ratio": "Tasa de ingreso (interacción)",
    "activos_cierre_conteo": "Activos que cierran issues",
    "activos_comentarios_conteo": "Activos que comentan",
    "activos_commits_conteo": "Activos que commitean",
    "activos_interaccion_conteo": "Activos en la interacción",
    "nuevos_commits_conteo": "Nuevos (commits)",
    "nuevos_interaccion_conteo": "Nuevos (interacción)",
    "dev_exp_mediana": "Development Experience (mediana)",
    "commits_doc_producto": "Commits que tocan documentación",
    "dloc_flujo_producto": "DLOC 2.0",
    "jarczyk_success_rate_producto": "Jarczyk Success Rate",
    "process_performance_producto": "Process Performance",
    "le_producto": "LE del proyecto",
    "disc_centrality_mediana": "Discussion Centrality (mediana)",
}
SIGLA = {"anmcc": "ANMCC", "cd": "CD", "cdiv": "CDIV", "cfdr": "CFDR", "dis": "DIS", "dloc": "DLOC", "exprev": "EXPRev",
         "le": "LE", "mttr": "MTTR", "nc": "NC", "nci": "NCI", "nob_42": "NOB", "noi": "NOI", "nub": "NUB", "rc": "RC",
         "rexp": "REXP", "rexprev": "REXPRev", "sc": "SC", "ss": "SS", "wp": "WP"}
SUFIJO = {"mediana": "mediana", "p90": "p90", "share_top10pct": "10 % más activo", "producto": None}


def nombre(var_id):
    if var_id in NOMBRES:
        return NOMBRES[var_id]
    for suf, txt in SUFIJO.items():
        if var_id.endswith("_" + suf):
            base = var_id[: -len(suf) - 1]
            if base in SIGLA:
                return SIGLA[base] + (f" ({txt})" if txt else "")
    return var_id


def par(x, y, sep=" ↔ "):
    return nombre(x) + sep + nombre(y)


# ── guardado ─────────────────────────────────────────────────────────────────
def guardar(fig, nombre_archivo):
    FIGURAS.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "svg"):
        fig.savefig(FIGURAS / f"{nombre_archivo}.{ext}", dpi=300, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    print(f"  guardada {nombre_archivo}.png/.svg")


class DatoDistinto(Exception):
    pass


def chequear(etiqueta, obtenido, esperado, tol=0.0):
    """Compara un dato con el número que afirma el texto. Devuelve un string con la diferencia o None."""
    ok = (abs(obtenido - esperado) <= tol) if isinstance(esperado, (int, float)) else obtenido == esperado
    if not ok:
        msg = f"[≠ texto] {etiqueta}: datos={obtenido} · texto={esperado}"
        print("  " + msg)
        return msg
    return None
