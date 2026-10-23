"""
analisis/piezas_comparacion.py

Gráficos estáticos (SVG generado en Python) para comparar el análisis original con el
corregido dentro de un informe (generar_informe.py):

    [[antes mapa]]                   mapa de calor de la ρ corregida del análisis original
    [[comparar serie dloc_producto]] la serie de una variable antes y después de los fixes

El análisis original se lee de analisis/salidas_originales/ (la copia que se guarda antes de
regenerar todo sobre la base corregida); el corregido, de analisis/salidas/.
"""
import html
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ORIGINAL = ROOT / "analisis" / "salidas_originales"
ACTUAL = ROOT / "analisis" / "salidas"

_valores: dict = {}


def _f(v, d=2):
    return "—" if v is None or pd.isna(v) else f"{v:.{d}f}".replace(".", ",").replace("-", "−")


def _miles(v):
    if abs(v) >= 1000:
        return f"{v:,.0f}".replace(",", ".")
    return _f(v, 2 if abs(v) < 10 else 0)


def _color(v):
    if v is None or pd.isna(v):
        return "transparent"
    t = round(min(1.0, abs(v)) * 100)
    return f"color-mix(in srgb, var({'--div-pos' if v >= 0 else '--div-neg'}) {t}%, var(--div-mid))"


def _nombres(carpeta: Path) -> dict:
    import reporte_cruce as rc
    d = pd.read_csv(carpeta / "diccionario_variables.csv")
    out = {}
    for _, r in d.iterrows():
        base = rc.NOMBRES_CORTOS.get(r.metrica_id)
        out[r.variable_id] = (r.nombre_legible.split(" [")[0] if base is None or r.estadistico not in rc.SUFIJOS
                              else base + rc.SUFIJOS[r.estadistico])
    return out


def mapa_antes(cruce: str) -> str:
    archivo = ORIGINAL / "pares_correlacion.csv"
    if not archivo.exists():
        return f'<p class="error-marca">Falta {html.escape(str(archivo))} (el análisis original guardado).</p>'
    p = pd.read_csv(archivo)
    p = p[p.cruce == cruce]
    nombre = _nombres(ORIGINAL)
    ids = sorted(set(p.x_id) | set(p.y_id), key=lambda v: nombre.get(v, v).lower())
    rho = {}
    for _, r in p.iterrows():
        rho[(r.x_id, r.y_id)] = rho[(r.y_id, r.x_id)] = (r.rho_corregida, r.categoria)
    n = len(ids)
    maxcar = max(len(nombre.get(v, v)) for v in ids)
    lw, lh = min(240, maxcar * 6.2 + 12), min(200, maxcar * 5.2 + 12)
    celda = max(13, min(34, (940 - lw) / n))
    extra = min(170, maxcar * 6.2 * 0.6)
    w, h = lw + celda * n + extra, lh + celda * n + 8
    s = [f'<svg viewBox="0 0 {w:.0f} {h:.0f}" role="img" aria-label="Mapa de calor del análisis original">']
    for i, v in enumerate(ids):
        nm = html.escape(nombre.get(v, v))
        s.append(f'<text x="{lw - 6:.1f}" y="{lh + celda * (i + .5):.1f}" class="lbl-fila">{nm}</text>'
                 f'<text transform="translate({lw + celda * (i + .5):.1f} {lh - 6:.1f}) rotate(-55)" class="lbl-col">{nm}</text>')
    for i, a in enumerate(ids):
        for j, b in enumerate(ids):
            x, y = lw + celda * j, lh + celda * i
            val = rho.get((a, b)) if i != j else None
            if not val:
                s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{celda:.1f}" height="{celda:.1f}" class="celda vacia"/>')
                continue
            r, cat = val
            s.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{celda:.1f}" height="{celda:.1f}" class="celda" '
                     f'style="fill:{_color(None if cat == "control" else r)}"><title>{html.escape(nombre.get(a, a))} ↔ '
                     f'{html.escape(nombre.get(b, b))}: {_f(r)} ({cat})</title></rect>')
    s.append("</svg>")
    return (f'<div class="panel inserto antes"><h4>Antes de los fixes · mapa de calor (ρ corregida)</h4>'
            f'<div class="grafico-disp">{"".join(s)}</div>'
            '<p class="nota">Análisis original (analisis/salidas_originales). Azul: negativa; naranja: positiva; '
            'gris: cerca de 0 o par de control.</p></div>')


def _serie(carpeta: Path, var: str) -> pd.Series:
    """Valores de una variable por release (serie estable), desde pares_valores.csv."""
    if carpeta not in _valores:
        import reporte_cruce as rc
        _valores[carpeta] = rc.leer_valores(["par_id", "fecha_hora", "x_valor", "y_valor"], carpeta)
    v = _valores[carpeta]
    for _, g in v[v.par_id.str.startswith(var + "__")].groupby("par_id"):
        s = g.set_index("fecha_hora")["x_valor"]
        break
    else:
        for _, g in v[v.par_id.str.endswith("__" + var)].groupby("par_id"):
            s = g.set_index("fecha_hora")["y_valor"]
            break
        else:
            return pd.Series(dtype=float)
    s = s[~s.index.duplicated()].dropna().sort_index()
    s.index = [date(int(str(f)[:4]), int(str(f)[4:6]), int(str(f)[6:8])) for f in s.index]
    return s


def serie_comparada(var: str) -> str:
    antes, despues = _serie(ORIGINAL, var), _serie(ACTUAL, var)
    if antes.empty and despues.empty:
        return f'<p class="error-marca">No hay valores para {html.escape(var)}.</p>'
    nombre = _nombres(ACTUAL if (ACTUAL / "diccionario_variables.csv").exists() else ORIGINAL).get(var, var)
    todas = pd.concat([antes, despues])
    t0, t1 = min(todas.index).toordinal(), max(todas.index).toordinal()
    y0, y1 = min(0.0, float(todas.min())), float(todas.max()) * 1.05 or 1.0
    w, h, m = 1000, 300, dict(l=70, r=14, t=12, b=30)
    sx = lambda d_: m["l"] + (d_.toordinal() - t0) / ((t1 - t0) or 1) * (w - m["l"] - m["r"])
    sy = lambda v: m["t"] + (1 - (v - y0) / ((y1 - y0) or 1)) * (h - m["t"] - m["b"])
    s = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Serie de {html.escape(nombre)} antes y después">']
    for k in range(5):
        v = y0 + (y1 - y0) * k / 4
        s.append(f'<line x1="{m["l"]}" x2="{w - m["r"]}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" class="grid"/>'
                 f'<text x="{m["l"] - 6}" y="{sy(v):.1f}" class="ticky">{_miles(v)}</text>')
    for anio in range(date.fromordinal(t0).year + 1, date.fromordinal(t1).year + 1):
        x = sx(date(anio, 1, 1))
        s.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{m["t"]}" y2="{h - m["b"]}" class="grid"/>'
                 f'<text x="{x:.1f}" y="{h - m["b"] + 6}" class="tick">{anio}</text>')
    for serie, clase in ((antes, "linea-y"), (despues, "linea-x")):
        if not serie.empty:
            s.append('<path d="' + "".join(f'{"L" if i else "M"}{sx(d_):.1f},{sy(v):.1f}'
                                           for i, (d_, v) in enumerate(serie.items())) + f'" class="{clase}"/>')
    s.append("</svg>")
    return (f'<div class="panel inserto"><h4>{html.escape(nombre)} · antes y después de los fixes (serie estable)</h4>'
            f'<div class="grafico-disp">{"".join(s)}</div>'
            '<div class="leyenda"><span><i class="y"></i>antes de los fixes</span>'
            '<span><i></i>con los fixes</span></div></div>')


def pieza(marca: str, cruce: str) -> str:
    """Resuelve [[antes ...]] y [[comparar ...]]."""
    tipo, _, resto = marca.partition(" ")
    args = resto.split()
    if tipo == "antes" and args[:1] == ["mapa"]:
        return mapa_antes(cruce)
    if tipo == "comparar" and args[:1] == ["serie"] and len(args) >= 2:
        return "".join(serie_comparada(v) for v in args[1:])
    return f'<p class="error-marca">Marca desconocida: [[{html.escape(marca)}]]</p>'
