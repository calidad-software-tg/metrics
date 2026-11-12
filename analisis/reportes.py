#!/usr/bin/env python3
"""
analisis/reportes.py

Reúne los reportes HTML en tres páginas, una por nivel de análisis:

    salidas/reportes/intradimensional.html   cada dimensión: correlaciones y PCA con agrupamiento
    salidas/reportes/bidimensional.html      cada par de dimensiones
    salidas/reportes/tridimensional.html     las tres dimensiones a la vez

Cada página es autocontenida: lleva adentro los reportes de su nivel (los que generan reporte_pca.py,
reporte_cruce.py, reporte_cruce_dimensiones.py y reporte_tres_dimensiones.py en salidas/reportes/_partes/)
y los muestra en pestañas, cada uno en su propio marco para que no se mezclen sus estilos ni sus scripts.
Al terminar borra _partes/.

Uso: python3 analisis/reportes.py   (lo corre tres_p.py analizar después de los reportes)
"""
import html
import json
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reporte_cruce as rc  # noqa: E402  (estilo común)
import rutas  # noqa: E402

DIMS = ("Persona", "Proceso", "Producto")
PARES = (("Persona", "Proceso"), ("Persona", "Producto"), ("Proceso", "Producto"))

# nivel: (archivo, título, descripción, [(pestaña, [(vista, archivo parcial)])])
NIVELES = {
    "intradimensional": (
        "Análisis intradimensional",
        "Cada dimensión por separado: los patrones finales que se leen dentro de ella, qué métricas se mueven "
        "juntas (correlaciones) y en qué aspectos se resume (componentes principales y agrupamiento).",
        [(d, [("Patrones finales", rutas.REPORTES_DIMENSIONES / f"{d.lower()}_patrones.html"),
              ("Correlaciones", rutas.REPORTES_DIMENSIONES / f"{d.lower()}_correlaciones.html"),
              ("PCA y agrupamiento", rutas.REPORTES_DIMENSIONES / f"{d.lower()}_pca.html"),
              ("Complementarios", rutas.REPORTES_DIMENSIONES / f"{d.lower()}_complementarios.html")]) for d in DIMS]),
    "bidimensional": (
        "Análisis bidimensional",
        "Cada par de dimensiones: patrones finales, variables y componentes, grupos, cruces sin las métricas "
        "compartidas y multiverso de asignaciones.",
        [(f"{a} – {b}", [(v, rutas.REPORTES_CRUCES / f"{a.lower()}_{b.lower()}{s}.html") for v, s in (
            ("Patrones finales", "_patrones"), ("Variables y componentes", ""), ("Grupos", "_grupos"),
            ("Sin métricas compartidas", "_compartidas"), ("Multiverso", "_multiverso"),
            ("Complementarios", "_complementarios"))]) for a, b in PARES]),
    "tridimensional": (
        "Análisis tridimensional",
        "Las tres dimensiones a la vez: medida global frente al azar, red de componentes, triángulos, tríos de "
        "variables, PCA y agrupamiento conjunto y multiverso.",
        [("Persona · Proceso · Producto", [("Medida global, red y triángulos", rutas.REPORTES_TRES / "tres_dimensiones.html"),
                                           ("PCA y agrupamiento conjunto", rutas.REPORTES_TRES / "conjunto.html"),
                                           ("Multiverso y métricas compartidas", rutas.REPORTES_TRES / "multiverso.html"),
                                           ("Complementarios", rutas.REPORTES_TRES / "complementarios.html")])]),
}

ESTILO = """
html, body { height:auto; }
header { max-width:1100px; margin:0 auto; padding:24px 16px 0; }
header h1 { margin:0 0 4px; }
.niveles { display:flex; gap:6px; flex-wrap:wrap; margin:0 0 14px; font-size:13px; }
.niveles a { color:var(--texto2); text-decoration:none; padding:5px 10px; border-radius:8px; border:1px solid var(--borde); }
.niveles a[aria-current="page"] { color:var(--fondo); background:var(--texto); border-color:var(--texto); }
.barra { display:flex; flex-wrap:wrap; gap:12px; align-items:center; justify-content:space-between;
  border-bottom:1px solid var(--borde); padding-bottom:10px; margin-top:16px; }
.pestanas, .vistas { display:flex; flex-wrap:wrap; gap:6px; }
.pestanas button, .vistas button { font:inherit; font-size:14px; padding:7px 14px; border-radius:8px; cursor:pointer;
  border:1px solid var(--borde); background:var(--superficie); color:var(--texto); }
.pestanas button[aria-selected="true"] { background:var(--texto); color:var(--fondo); border-color:var(--texto); }
.vistas button { font-size:13px; padding:5px 12px; }
.pestanas[hidden] { display:none; }
.vistas button[aria-pressed="true"] { background:var(--hover); border-color:var(--serie); }
iframe { display:block; width:100%; border:0; min-height:70vh; background:var(--fondo); }
.falta { max-width:1100px; margin:24px auto; padding:0 16px; color:var(--texto2); }
"""

SCRIPT = """
const paginas = JSON.parse(document.getElementById('paginas').textContent);
const marco = document.getElementById('marco');
let obs = null;
function ajustar() {
  try { const d = marco.contentDocument; if (d && d.documentElement) marco.style.height = d.documentElement.scrollHeight + 'px'; } catch (e) {}
}
marco.addEventListener('load', () => {
  ajustar();
  try { if (obs) obs.disconnect(); obs = new ResizeObserver(ajustar); obs.observe(marco.contentDocument.body); } catch (e) {}
});
function mostrar(p, v) {
  const pest = paginas[p]; if (!pest) return;
  v = Math.min(v, pest.vistas.length - 1);
  document.querySelectorAll('.pestanas button').forEach((b, i) => b.setAttribute('aria-selected', i === p));
  const cont = document.querySelector('.vistas');
  cont.innerHTML = pest.vistas.length > 1 ? pest.vistas.map((x, i) =>
    `<button type="button" aria-pressed="${i === v}" data-v="${i}">${x.nombre}</button>`).join('') : '';
  cont.querySelectorAll('button').forEach(b => b.onclick = () => mostrar(p, +b.dataset.v));
  const doc = pest.vistas[v].html;
  marco.style.height = '70vh';
  marco.srcdoc = doc || '<p style="font-family:sans-serif;color:#888;padding:24px">Este reporte no se generó en esta corrida.</p>';
  history.replaceState(null, '', '#' + p + '-' + v);
}
document.querySelectorAll('.pestanas button').forEach((b, i) => b.onclick = () => mostrar(i, 0));
const h = (location.hash.slice(1) || '0-0').split('-').map(Number);
mostrar(h[0] || 0, h[1] || 0);
"""


def json_seguro(obj):
    """JSON que se puede poner dentro de <script> sin cerrarlo antes de tiempo."""
    return (json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
            .replace("</", "<\\/").replace("<!--", "<\\u0021--"))


def motivo_de(archivo):
    """Por qué falta una vista: el motivo que dejó tres_p.py analizar al saltear el paso que la genera."""
    n = archivo.name
    if archivo.parent == rutas.REPORTES_TRES and n in ("tres_dimensiones.html", "conjunto.html"):
        return rutas.omitido("tres_dimensiones")
    if archivo.parent == rutas.REPORTES_DIMENSIONES and n.endswith("_pca.html"):
        return rutas.omitido("pca", n[:-len("_pca.html")].capitalize())
    for a, b in PARES:
        base = f"{a.lower()}_{b.lower()}"
        if archivo.parent == rutas.REPORTES_CRUCES and n.startswith(base):
            resto = n[len(base):]
            if resto == ".html":
                return rutas.omitido("cruces", f"{a}–{b}")
            if resto == "_grupos.html":
                return rutas.omitido("grupos", f"{a}–{b}") or rutas.omitido("cruces", f"{a}–{b}")
            if resto == "_compartidas.html":
                return rutas.omitido("bloques")
    return ""


def aviso_html(titulo, motivo):
    return (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><style>{rc.ESTILO}</style></head><body><main>'
            f'<h1>{html.escape(titulo)}</h1><p class="vacio"><strong>No disponible en este proyecto.</strong> '
            f'{html.escape(motivo)}</p></main></body></html>')


def armar(nivel):
    titulo, desc, pestanas = NIVELES[nivel]
    datos, hay = [], 0
    for nombre, vistas in pestanas:
        vs = []
        for vista, archivo in vistas:
            contenido = archivo.read_text(encoding="utf-8") if archivo.exists() else ""
            hay += bool(contenido)
            if not contenido and (motivo := motivo_de(archivo)):
                contenido = aviso_html(vista, motivo)
            vs.append(dict(nombre=vista, html=contenido))
        datos.append(dict(nombre=nombre, vistas=vs))
    if not hay:
        return None
    repo = html.escape(rutas.proyecto.REPO or "proyecto")
    enlaces = "".join(f'<a href="{n}.html"{" aria-current=page" if n == nivel else ""}>{html.escape(t[0].replace("Análisis ", "").capitalize())}</a>'
                      for n, t in NIVELES.items())
    botones = "".join(f'<button type="button" role="tab" aria-selected="false">{html.escape(p["nombre"])}</button>' for p in datos)
    una = len(datos) == 1
    pagina = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(titulo)}</title>
<style>{rc.ESTILO}{ESTILO}</style></head><body>
<header>
<nav class="niveles" aria-label="Niveles de análisis">{enlaces}</nav>
<h1>{html.escape(titulo)}</h1>
<p class="sub" style="margin-bottom:0">{html.escape(desc)} · {repo} · {date.today().isoformat()}</p>
<div class="barra"><div class="pestanas" role="tablist"{' hidden' if una else ''}>{botones}</div><div class="vistas"></div></div>
</header>
<iframe id="marco" title="{html.escape(titulo)}"></iframe>
<script type="application/json" id="paginas">{json_seguro(datos)}</script>
<script>{SCRIPT}</script></body></html>"""
    destino = rutas.REPORTES / f"{nivel}.html"
    destino.write_text(pagina, encoding="utf-8")
    return destino


def main():
    rutas.REPORTES.mkdir(parents=True, exist_ok=True)
    for nivel in NIVELES:
        destino = armar(nivel)
        if destino:
            print(f"Reporte: {destino} ({destino.stat().st_size / 1e6:.1f} MB)")
        else:
            print(f"  aviso: no hay reportes de nivel {nivel}; no se genera {nivel}.html")
    if "--conservar-partes" not in sys.argv:
        shutil.rmtree(rutas.REPORTES_PARTES, ignore_errors=True)
    # restos de versiones anteriores (reportes sueltos, index.html)
    for viejo in rutas.REPORTES.iterdir():
        if viejo.name in ("_partes",) or viejo.name in {f"{n}.html" for n in NIVELES}:
            continue
        shutil.rmtree(viejo) if viejo.is_dir() else viejo.unlink()


if __name__ == "__main__":
    main()
