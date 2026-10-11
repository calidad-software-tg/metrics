#!/usr/bin/env python3
"""
analisis/generar_informe.py

Genera el informe HTML de análisis de un cruce a partir de un texto en Markdown
(analisis/informes/<cruce>.md) y de las piezas del reporte genérico (reporte_cruce.py).

Uso:
    python3 analisis/generar_informe.py analisis/informes/producto_producto.md

El texto lo escribe quien analiza; el script lo convierte a HTML y reemplaza las marcas
por gráficos y tablas calculados con los datos actuales (pares_correlacion.csv y
pares_valores.csv). Además regenera el reporte interactivo del cruce (reporte_cruce.py) y lo enlaza en el anexo.

Encabezado del .md (obligatorio el cruce):
    ---
    cruce: Producto-Producto
    titulo: Análisis de correlaciones dentro de Producto
    ---

Marcas (cada una sola en su línea):
    [[grafico kpis]]              indicadores del cruce
    [[grafico categorias]]        pares por categoría
    [[grafico embudo]]            embudo de filtrado
    [[grafico cruda_corregida]]   ρ cruda vs. ρ corregida
    [[grafico red]]               red de relaciones significativas
    [[grafico forest]]            intervalos de las relaciones significativas
    [[grafico estabilidad]]       estabilidad por período
    [[grafico mapa]]              mapa de calor (ρ corregida)
    [[grafico red | chico]]       cualquier gráfico, más angosto y centrado
    [[tabla robustas]]            también: positivas, negativas, significativas, hallazgos
    [[tabla significativas | direccion]]   con selector Todas / Positivas / Negativas
    [[ficha x_id y_id]]           resultados de un par
    [[explorador robustas tabla]]       tabla seleccionable (también significativas, positivas,
                                        negativas, hallazgos; "| direccion" agrega el selector)
    [[explorador robustas detalle]]     análisis particular del par elegido en esa tabla:
                                        ficha, gráficos y las notas de ese par
    [[nota x_id y_id; x2 y2]] ... [[/nota]]
        texto (con marcas) que se muestra en el análisis particular al elegir alguno de esos pares
    [[pca cargas producto estable ajustado]]   piezas del PCA de la dimensión (generar_pca.py):
        cargas, scree, solidez y puntajes (conjunto serie enfoque), criterios y comparacion (conjunto)
    [[par x_id y_id: periodos, sensibilidad, movil, dispersion, temporal]]
        gráficos de un par; opciones después de "|":  periodo=2023-2024  modo=ajustado
        (dispersion = ajustada y original; también dispersion_ajustada, dispersion_original)

Markdown soportado: títulos (#), párrafos, listas con - o 1. (anidadas con sangría),
tablas con |, citas con > (se muestran como notas), >> (texto aparte, con sangría y más chico), **negrita**, *cursiva*, `código` y [enlaces](url).
"""
import argparse
import json
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reporte_cruce as rc  # noqa: E402
import reporte_pca as rpca  # noqa: E402

SALIDA = rc.SALIDA
GRAFICOS = {
    "embudo": ("Embudo: de los pares evaluados a los hallazgos",
               "Cada paso agrega una condición a la anterior."),
    "cruda_corregida": ("ρ cruda vs. ρ corregida",
                        "Cada punto es un par. Sobre la diagonal, la relación no cambia al corregir; los que caen a la franja "
                        "(−0,2 a 0,2) eran crecimiento del proyecto o efecto de la duración de las ventanas."),
    "red": ("Red de relaciones significativas",
            "Cada línea une dos variables con una relación significativa; el grosor es la fuerza."),
    "forest": ("Intervalos de las relaciones significativas",
               "Punto: ρ corregida (relleno si es robusta); línea: intervalo de confianza del 95%. La franja marca la zona despreciable."),
    "estabilidad": ("Estabilidad por período de las relaciones significativas",
                    "Naranja / azul: relación positiva / negativa en ese período (|ρ| ≥ 0,1 e intervalo sin el 0); "
                    "gris: sin relación; vacío: menos de 15 ventanas."),
    "mapa": ("Mapa de calor",
             "Azul: negativa; naranja: positiva; gris: cerca de 0. La ρ cruda compara los valores tal como se midieron; "
             "la corregida descuenta el momento del proyecto y la duración de cada ventana."),
}
TABLAS = {"robustas", "positivas", "negativas", "significativas", "hallazgos"}
GRAF_PAR = {
    "periodos": ("Correlación corregida por período y en canary",
                 "Bigotes: intervalo de confianza del 95%. Tono claro: período sin relación. Punteada: toda la historia."),
    "sensibilidad": ("Sensibilidad: la ρ con cada control", "Líneas punteadas: ±0,1."),
    "movil": ("Correlación móvil (41 releases)", "Correlación de los valores ajustados alrededor de cada release."),
    "dispersion_ajustada": ("Relación ajustada (sin tiempo ni duración)", "Naranja: backports."),
    "dispersion_original": ("Valores originales", "Naranja: backports."),
    "temporal": ("Evolución en el tiempo", "Marcas naranjas: backports."),
}


# ── Markdown mínimo ──────────────────────────────────────────────────────────
def inline(t: str) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', t)
    return t


def lista(lineas: list[str]) -> str:
    """Listas anidadas por sangría, con - o 1. (una lista numerada sigue desde su primer número)."""
    items = []  # (sangría, número o None, texto)
    for l in lineas:
        m = re.match(r"^(\s*)(?:([-*])|(\d+)\.)\s+(.*)$", l)
        if m:
            items.append([len(m.group(1).replace("\t", "    ")), int(m.group(3)) if m.group(3) else None, m.group(4)])
        elif items:
            items[-1][2] += " " + l.strip()
    out, pila = [], []  # pila de (sangría, etiqueta)
    for sang, numero, texto in items:
        etiqueta = "ol" if numero is not None else "ul"
        while pila and sang < pila[-1][0]:
            out.append(f"</li></{pila.pop()[1]}>")
        if not pila or sang > pila[-1][0]:
            out.append(f'<ol start="{numero}">' if numero not in (None, 1) else f"<{etiqueta}>")
            pila.append((sang, etiqueta))
        else:
            out.append("</li>")
        out.append(f"<li>{inline(texto)}")
    while pila:
        out.append(f"</li></{pila.pop()[1]}>")
    return "".join(out)


def tabla_md(lineas: list[str]) -> str:
    filas = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lineas]
    filas = [f for f in filas if not all(re.fullmatch(r":?-{3,}:?", c) for c in f)]
    cab, cuerpo = filas[0], filas[1:]
    return ('<div class="tabla"><table><thead><tr>' + "".join(f"<th>{inline(c)}</th>" for c in cab)
            + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in f) + "</tr>" for f in cuerpo)
            + "</tbody></table></div>")


def markdown(texto: str, inserto) -> tuple[str, list]:
    """Devuelve (html, índice de títulos h2)."""
    lineas = texto.splitlines()
    out, indice, i = [], [], 0
    while i < len(lineas):
        l = lineas[i]
        if not l.strip():
            i += 1
            continue
        m = re.match(r"^\[\[nota\s+(.+?)\]\]\s*$", l.strip())
        if m:
            fin = next((j for j in range(i + 1, len(lineas)) if lineas[j].strip() == "[[/nota]]"), None)
            if fin is None:
                out.append('<p class="error-marca">Falta [[/nota]] para cerrar la nota.</p>')
                i += 1
                continue
            pares = ";".join(" ".join(p.split()[:2]) for p in m.group(1).split(";") if p.strip())
            contenido = markdown("\n".join(lineas[i + 1:fin]), inserto)[0]
            out.append(f'<div class="nota-par-fuente" data-pares="{html.escape(pares)}">{contenido}</div>')
            i = fin + 1
            continue
        m = re.match(r"^\[\[(.+)\]\]\s*$", l.strip())
        if m:
            out.append(inserto(m.group(1).strip()))
            i += 1
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", l)
        if m:
            nivel, txt = len(m.group(1)), m.group(2).strip()
            ancla = re.sub(r"[^a-z0-9]+", "-", txt.lower()).strip("-")
            if nivel in (2, 3, 4):
                indice.append((nivel, ancla, txt))
            out.append(f'<h{nivel} id="{ancla}">{inline(txt)}</h{nivel}>')
            i += 1
            continue
        if l.lstrip().startswith("|"):
            bloque = []
            while i < len(lineas) and lineas[i].lstrip().startswith("|"):
                bloque.append(lineas[i]); i += 1
            out.append(tabla_md(bloque))
            continue
        if re.match(r"^\s*(?:[-*]|\d+\.)\s+", l):
            bloque = []
            while i < len(lineas) and lineas[i].strip() and not lineas[i].strip().startswith("[[") \
                    and (re.match(r"^\s*(?:[-*]|\d+\.)\s+", lineas[i]) or lineas[i].startswith(" ")):
                bloque.append(lineas[i]); i += 1
            out.append(lista(bloque))
            continue
        if l.lstrip().startswith(">>"):
            bloque = []
            while i < len(lineas) and lineas[i].lstrip().startswith(">>"):
                bloque.append(lineas[i].lstrip()[2:].strip()); i += 1
            out.append(f'<div class="aparte">{markdown(chr(10).join(bloque), inserto)[0]}</div>')
            continue
        if l.lstrip().startswith(">"):
            bloque = []
            while i < len(lineas) and lineas[i].lstrip().startswith(">"):
                bloque.append(lineas[i].lstrip()[1:].strip()); i += 1
            out.append(f'<div class="nota-editor">{markdown(chr(10).join(bloque), inserto)[0]}</div>')
            continue
        bloque = []
        while i < len(lineas) and lineas[i].strip() and not re.match(r"^(#{1,4}\s|\||>|\[\[|\s*(?:[-*]|\d+\.)\s)", lineas[i]):
            bloque.append(lineas[i].strip()); i += 1
        out.append(f"<p>{inline(' '.join(bloque))}</p>")
    return "\n".join(out), indice


# ── Marcas → HTML ────────────────────────────────────────────────────────────
def hacer_inserto(piezas: dict, pca: dict | None = None):
    def inserto(marca: str) -> str:
        tipo, _, resto = marca.partition(" ")
        resto = resto.strip()
        if tipo == "pca":
            if pca is None:
                return '<p class="error-marca">No hay resultados de PCA: corré analisis/generar_pca.py para esta dimensión.</p>'
            args = resto.split()
            if len(args) < 2:
                return f'<p class="error-marca">Marca de PCA incompleta: [[{html.escape(marca)}]]</p>'
            return rpca.pieza(pca, *args[:4])
        if tipo == "grafico":
            resto, _, opcion = resto.partition("|")
            resto, opcion = resto.strip(), opcion.strip()
            ancho = ' style="max-width:560px;margin-left:auto;margin-right:auto"' if opcion == "chico" else ""
            if resto == "kpis":
                return piezas["kpis"]
            if resto == "categorias":
                return f'<div class="panel inserto"><h4>Pares por categoría</h4>{piezas["grafico_categorias"]}</div>'
            if resto in GRAFICOS:
                titulo, nota = GRAFICOS[resto]
                arriba, extra = "", ""
                if resto == "mapa":
                    arriba = ('<div class="modo modo-mapa" role="group" aria-label="Correlación del mapa">'
                              '<button type="button" data-modo="corr" class="activo">ρ corregida</button>'
                              '<button type="button" data-modo="cruda">ρ cruda</button></div>')
                    extra = '<div class="leyenda-mapa"></div>'
                return (f'<div class="panel inserto"{ancho}><h4>{titulo}</h4>{arriba}<div class="grafico-disp" data-inserto="{resto}"></div>'
                        f'{extra}<p class="nota">{nota}</p></div>')
        if tipo == "tabla":
            nombre_t, _, op = resto.partition("|")
            nombre_t, op = nombre_t.strip(), op.strip()
            if nombre_t in TABLAS:
                selector = ""
                if op == "direccion":
                    selector = ('<div class="modo modo-dir" role="group" aria-label="Dirección de la relación">'
                                '<button type="button" data-dir="todas" class="activo">Todas</button>'
                                '<button type="button" data-dir="pos">Positivas</button>'
                                '<button type="button" data-dir="neg">Negativas</button></div>')
                return (f'<div class="panel inserto">{selector}<div class="tabla" data-inserto="tabla" '
                        f'data-filtro="{nombre_t}"></div><p class="nota conteo-t"></p></div>')
        if tipo == "explorador":
            cuerpo_m, _, op = resto.partition("|")
            nombre_t, _, parte = cuerpo_m.strip().partition(" ")
            parte, op = parte.strip(), op.strip()
            if nombre_t not in TABLAS or parte not in ("tabla", "detalle"):
                return f'<p class="error-marca">Marca de explorador inválida: [[{html.escape(marca)}]]</p>'
            if parte == "tabla":
                selector = ""
                if op == "direccion":
                    selector = ('<div class="modo modo-dir" role="group" aria-label="Dirección de la relación">'
                                '<button type="button" data-dir="todas" class="activo">Todas</button>'
                                '<button type="button" data-dir="pos">Positivas</button>'
                                '<button type="button" data-dir="neg">Negativas</button></div>')
                return (f'<div class="panel inserto">{selector}<div class="tabla" data-inserto="tabla" data-filtro="{nombre_t}" '
                        f'data-local="{nombre_t}"></div><p class="nota conteo-t"></p></div>')
            paneles = []
            for g in ("periodos", "sensibilidad", "movil", "dispersion_ajustada", "dispersion_original", "temporal"):
                titulo, nota = GRAF_PAR[g]
                ley = '<div class="leyenda leyenda-t"></div>' if g == "temporal" else ""
                paneles.append(f'<div class="panel{" ancho" if g in ("temporal", "periodos") else ""}"><h4>{titulo}</h4>'
                               f'<div class="grafico-disp" data-inserto="par" data-graf="{g}" data-x="" data-y=""></div>'
                               f'{ley}<p class="nota">{nota}</p></div>')
            return (f'<div class="inserto bloque-par detalle-local" data-local="{nombre_t}">'
                    f'<div class="par-cab" data-inserto="parcab" data-x="" data-y=""></div>'
                    f'<div class="panel" style="margin:0 0 12px"><div data-inserto="ficha" data-sin-titulo="1" data-x="" data-y=""></div></div>'
                    f'<div class="graficos-par">{"".join(paneles)}</div>'
                    f'<div class="notas-local"></div></div>')
        if tipo == "ficha":
            x, y = resto.split()[:2]
            return f'<div class="panel inserto" data-inserto="ficha" data-x="{x}" data-y="{y}"></div>'
        if tipo == "par":
            partes = [p.strip() for p in resto.split("|")]
            ids, _, lista_g = partes[0].partition(":")
            x, y = ids.split()[:2]
            graf = [g.strip() for g in (lista_g or "periodos, dispersion, temporal").split(",") if g.strip()]
            graf = [h for g in graf for h in (("dispersion_ajustada", "dispersion_original") if g == "dispersion" else (g,))]
            ops = dict(o.split("=", 1) for o in partes[1:] if "=" in o)
            periodo, modo = ops.get("periodo", "").strip(), ops.get("modo", "original").strip()
            paneles = []
            for g in graf:
                if g not in GRAF_PAR:
                    return f'<p class="error-marca">Gráfico de par desconocido: {html.escape(g)}</p>'
                titulo, nota = GRAF_PAR[g]
                ley = '<div class="leyenda leyenda-t"></div>' if g == "temporal" else ""
                paneles.append(f'<div class="panel{" ancho" if g in ("temporal", "periodos") else ""}"><h4>{titulo}</h4>'
                               f'<div class="grafico-disp" data-inserto="par" data-graf="{g}" data-x="{x}" data-y="{y}" '
                               f'data-periodo="{periodo}" data-modo="{modo}"></div>{ley}<p class="nota">{nota}</p></div>')
            cab = (f'<div class="par-cab" data-inserto="parcab" data-x="{x}" data-y="{y}" data-periodo="{periodo}"></div>')
            return f'<div class="inserto bloque-par">{cab}<div class="graficos-par">{"".join(paneles)}</div></div>'
        return f'<p class="error-marca">Marca no reconocida: [[{html.escape(marca)}]]</p>'
    return inserto


ESTILO_INFORME = """
.informe { max-width: 900px; }
.informe p, .informe li { font-size: 15.5px; line-height: 1.65; }
.informe h2 { font-size: 21px; margin: 44px 0 10px; padding-top: 8px; border-top: 1px solid var(--borde); }
.informe h3 { font-size: 17px; margin: 28px 0 8px; }
.informe h4 { font-size: 14px; margin: 0 0 8px; }
.informe ul, .informe ol { padding-left: 22px; }
.informe code { font-size: 13px; background: var(--hover); padding: 1px 5px; border-radius: 4px; }
.informe .tabla table { font-size: 13.5px; }
.inserto { margin: 16px 0; }
.informe .panel .nota { font-size: 13px; line-height: 1.5; }
.informe [data-inserto=tabla] td:nth-child(2) { min-width: 230px; }
.informe [data-inserto=tabla] td:nth-child(9) { min-width: 120px; }
.modo-dir { margin: 0 0 10px; }
.nota-editor { border-left: 3px solid var(--serie2); background: var(--hover); padding: 8px 14px; border-radius: 0 8px 8px 0; margin: 14px 0; }
.nota-editor p { margin: 6px 0; }
.aparte { margin: 4px 0 14px 28px; font-size: 13.5px; color: var(--texto2); }
.aparte p, .aparte ul { margin: 4px 0; }
.error-marca { color: #c03; font-weight: 600; }
.indice { background: var(--superficie); border: 1px solid var(--borde); border-radius: 10px; padding: 12px 18px; margin: 16px 0 8px; }
.indice ol { margin: 6px 0; padding-left: 0; list-style: none; } .indice li { margin: 2px 0; } .indice a { color: var(--texto); }
.bloque-par { border: 1px solid var(--borde); border-radius: 12px; padding: 12px; background: var(--fondo); }
.par-cab { display: flex; flex-wrap: wrap; gap: 6px 14px; align-items: baseline; margin: 2px 4px 10px; }
.par-cab b { font-size: 15px; }
.par-cab button { font: inherit; font-size: 12.5px; border: 1px solid var(--borde); border-radius: 8px; padding: 3px 9px;
  background: var(--superficie); color: var(--texto); cursor: pointer; margin-left: auto; }
.graficos-par { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }
.graficos-par .panel { margin-top: 0; } .graficos-par .panel.ancho { grid-column: 1 / -1; }
.inserto .per-grupo { cursor: default; }
.nota-par-fuente { display: none; }
.notas-local .nota-par { margin: 0 0 14px; padding: 4px 16px 8px; border: 1px solid var(--borde); border-radius: 10px; background: var(--superficie); }
.notas-local .nota-par:empty { display: none; }
.notas-local { margin-top: 14px; }
.detalle-local .par-cab b { font-size: 16px; }
.informe table.clic tbody tr.sel { background: var(--hover); box-shadow: inset 3px 0 0 var(--serie); }
.indice li.n3 { margin-left: 18px; font-size: 14px; }
.indice li.n4 { margin-left: 36px; font-size: 13.5px; }
.informe h4[id] { font-size: 15px; margin: 26px 0 6px; }
.anexo { border-top: 2px solid var(--borde); margin-top: 56px; padding-top: 8px; }
"""

SCRIPT_INSERTOS = r"""
(function () {
  const parId = {};
  for (const [id, p] of Object.entries(D.pares)) { parId[p.x + '|' + p.y] = id; parId[p.y + '|' + p.x] = id; }
  const ETAPA_IDX = { '2016-2019': 0, '2020-2022': 1, '2023-2024': 2, '2025-2026': 3 };
  const si = b => b ? 'sí' : 'no';
  const err = (c, t) => { c.innerHTML = `<p class="error-marca">${t}</p>`; };

  function tablaInserto(c, dir = 'todas') {
    const f = c.dataset.filtro;
    const cond = { robustas: p => p.robusta, positivas: p => p.cat === 'Positiva', negativas: p => p.cat === 'Negativa',
      significativas: p => signif(p), hallazgos: p => p.hallazgo }[f];
    const filas = evaluados.filter(([, p]) => cond(p))
      .filter(([, p]) => dir === 'todas' || (p.corr !== null && (dir === 'pos' ? p.corr > 0 : p.corr < 0)))
      .sort((a, b) => Math.abs(b[1].corr ?? 0) - Math.abs(a[1].corr ?? 0));
    const conteo = c.parentElement.querySelector('.conteo-t');
    if (conteo) conteo.textContent = `${filas.length} ${filas.length === 1 ? 'par' : 'pares'} · de mayor a menor |ρ corregida| · clic en una fila para verla en el explorador`;
    if (!filas.length) { c.innerHTML = '<p class="vacio">Ningún par.</p>'; return; }
    c.innerHTML = `<table class="clic"><thead><tr><th>#</th><th>Par</th><th>ρ corregida</th><th>IC 95%</th><th>Fuerza</th>
      <th>Robusta</th><th>Control por tamaño</th><th>Solapamiento</th><th>Alcance temporal</th><th>Hallazgo</th></tr></thead><tbody>`
      + filas.map(([id, p], i) => `<tr data-par="${id}" title="Ver en el explorador"><td class="n">${i + 1}</td><td>${nPar(p)}</td>
        <td class="n">${fmt(p.corr)}</td><td class="n">[${fmt(p.ic[0])}; ${fmt(p.ic[1])}]</td><td>${p.fuerza}</td>
        <td>${si(p.robusta)}</td><td>${p.tamano}</td><td>${si(p.solap)}</td><td>${p.alcance}</td><td>${si(p.hallazgo)}</td></tr>`).join('')
      + '</tbody></table>';
    const loc = c.dataset.local;
    c.querySelectorAll('tr[data-par]').forEach(tr => tr.addEventListener('click', () => {
      if (loc) seleccionarLocal(loc, tr.dataset.par, true); else if (abrirPar) abrirPar(tr.dataset.par);
    }));
    if (loc) {
      const ids = filas.map(([id]) => id), actual = seleccionLocal[loc];
      seleccionarLocal(loc, ids.includes(actual) ? actual : ids[0], false);
    }
  }

  // ── explorador local: la tabla elige el par y el detalle muestra su análisis particular ──
  const seleccionLocal = {};
  const periodoLocal = {};   // período elegido con un clic en los gráficos del análisis particular
  window.elegirPeriodoLocal = (det, i) => {
    const loc = det.dataset.local;
    periodoLocal[loc] = (i === null || periodoLocal[loc] === i) ? null : i;
    const etiqueta = periodoLocal[loc] === null ? '' : Object.keys(ETAPA_IDX)[periodoLocal[loc]];
    const graficos = det.querySelector('.graficos-par');
    graficos.querySelectorAll('[data-inserto="par"]').forEach(c => { c.dataset.periodo = etiqueta; });
    renderInsertos(graficos);
  };
  const mismaClave = (a, b) => a.split(' ').sort().join(' ') === b.split(' ').sort().join(' ');
  function seleccionarLocal(loc, id, desplazar) {
    seleccionLocal[loc] = id;
    document.querySelectorAll(`[data-inserto="tabla"][data-local="${loc}"] tr[data-par]`)
      .forEach(tr => tr.classList.toggle('sel', tr.dataset.par === id));
    const det = document.querySelector(`.detalle-local[data-local="${loc}"]`);
    if (!det || !id) return;
    const p = D.pares[id];
    det.querySelectorAll('[data-x]').forEach(c => { c.dataset.x = p.x; c.dataset.y = p.y; });
    periodoLocal[loc] = null;
    det.querySelectorAll('.graficos-par [data-inserto="par"]').forEach(c => { c.dataset.periodo = ''; });
    const notas = det.querySelector('.notas-local');
    notas.innerHTML = '';
    renderInsertos(det);
    document.querySelectorAll('.nota-par-fuente').forEach(fuente => {
      if (!fuente.dataset.pares.split(';').some(par => mismaClave(par.trim(), p.x + ' ' + p.y))) return;
      const nota = fuente.cloneNode(true);
      nota.className = 'nota-par';
      notas.appendChild(nota);
      renderInsertos(nota);
    });
    if (desplazar) det.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function fichaHtml(p, x, y) {
    return `<div class="ficha">
      <div><b>ρ corregida</b><span>${fmt(p.corr)} [${fmt(p.ic[0])}; ${fmt(p.ic[1])}]</span></div>
      <div><b>ρ cruda</b><span>${fmt(p.cruda)}</span></div>
      <div><b>Categoría</b><span>${p.cat}${p.fuerza ? ' · ' + p.fuerza : ''}</span></div>
      <div><b>Releases</b><span>${p.n}</span></div>
      <div><b>Robusta · hallazgo</b><span>${si(p.robusta)} · ${si(p.hallazgo)}</span></div>
      <div><b>Control por tamaño</b><span>${p.tamano}${p.rtam !== null ? ' (' + fmt(p.rtam) + ')' : ''}</span></div>
      <div><b>Solapamiento de definición</b><span>${si(p.solap)}</span></div>
      <div><b>Por período (16–19 · 20–22 · 23–24 · 25–26)</b><span>${p.per.map(v => fmt(v)).join(' · ')}</span></div>
      <div><b>Canary · sin ventanas cortas · tendencia local</b><span>${fmt(p.canary)} · ${fmt(p.sincortas)} · ${fmt(p.local)}</span></div>
      <div><b>Alcance temporal · escala</b><span>${p.alcance || '—'} · ${p.escala || '—'}</span></div>
    </div>${p.motivo ? `<div class="motivo">Por qué no es hallazgo: ${p.motivo}</div>` : ''}`;
  }

  function graficoPar(c) {
    const x = c.dataset.x, y = c.dataset.y, id = parId[x + '|' + y];
    if (!id) return err(c, `El par ${x} ↔ ${y} no está en este cruce.`);
    if (!D.con_valores) return err(c, 'Faltan los valores por release (pares_valores.csv).');
    const p = D.pares[id], inv = p.x !== x, g = c.dataset.graf;
    const guardP = periodoSel, guardM = modoTiempo;
    periodoSel = c.dataset.periodo in ETAPA_IDX ? ETAPA_IDX[c.dataset.periodo] : null;
    modoTiempo = c.dataset.modo === 'ajustado' ? 'ajustado' : 'original';
    const enPeriodo = q => periodoSel === null || q.rel[2] === ETAPA_ID[periodoSel];
    try {
      if (g === 'periodos') barrasPeriodo(c, p);
      else if (g === 'sensibilidad') sensibilidad(c, p);
      else if (g === 'movil') movil(c, p, inv);
      else if (g === 'temporal') temporal(c, x, y, p, inv, c.parentElement.querySelector('.leyenda-t'));
      else if (g === 'dispersion_ajustada') {
        const xa = inv ? p.ya : p.xa, ya = inv ? p.xa : p.ya;
        dispersion(c, p.p.map((n, i) => ({ x: xa[i], y: ya[i], rel: D.releases[n] })).filter(enPeriodo),
          nombre[x] + ' (ajustado)', nombre[y] + ' (ajustado)', true);
      } else if (g === 'dispersion_original') {
        dispersion(c, p.p.map(n => ({ x: D.serie[x][n], y: D.serie[y][n], rel: D.releases[n] }))
          .filter(q => q.x != null && q.y != null).filter(enPeriodo), nombre[x], nombre[y], false);
      }
    } finally { periodoSel = guardP; modoTiempo = guardM; }
  }

  function renderInsertos(raiz) {
  raiz.querySelectorAll('[data-inserto]').forEach(c => {
    if (c.closest('.nota-par-fuente')) return;                           // las notas se dibujan al copiarlas
    if (raiz === document && c.closest('.detalle-local')) return;        // el detalle lo dibuja su tabla
    const t = c.dataset.inserto;
    if (t === 'embudo') renderEmbudo(c);
    else if (t === 'cruda_corregida') { renderCrudaCorr(c); interactivo(c); }
    else if (t === 'red') { renderRed(c); interactivo(c); }
    else if (t === 'forest') { renderForest(c); interactivo(c); }
    else if (t === 'estabilidad') { renderEstab(c); interactivo(c); }
    else if (t === 'mapa') {
      // cada mapa insertado tiene su propio selector, independiente del mapa del anexo
      const ley = c.parentElement.querySelector('.leyenda-mapa'), botones = c.parentElement.querySelectorAll('.modo-mapa button');
      const dibujar = modo => { const g = modoMapa; modoMapa = modo; try { renderMapa(c, ley); } finally { modoMapa = g; } };
      botones.forEach(b => b.addEventListener('click', () => {
        botones.forEach(o => o.classList.toggle('activo', o === b));
        dibujar(b.dataset.modo);
      }));
      dibujar('corr');
    }
    else if (t === 'tabla') {
      const botones = c.parentElement.querySelectorAll('.modo-dir button');
      botones.forEach(b => b.addEventListener('click', () => {
        botones.forEach(o => o.classList.toggle('activo', o === b));
        tablaInserto(c, b.dataset.dir);
      }));
      tablaInserto(c);
    }
    else if (t === 'ficha' || t === 'parcab') {
      const x = c.dataset.x, y = c.dataset.y, id = parId[x + '|' + y];
      if (!id) return err(c, `El par ${x} ↔ ${y} no está en este cruce.`);
      const p = D.pares[id];
      if (t === 'ficha') c.innerHTML = (c.dataset.sinTitulo ? '' : `<h4>${nombre[x]} ↔ ${nombre[y]}</h4>`) + fichaHtml(p, x, y);
      else {
        c.innerHTML = `<b>${nombre[x]} ↔ ${nombre[y]}</b><span class="etiqueta">${p.cat}${p.fuerza ? ' · ' + p.fuerza : ''}</span>`
          + `<span>ρ corregida ${fmt(p.corr)}</span>${c.dataset.periodo ? `<span>· mostrando ${c.dataset.periodo}</span>` : ''}`
          + (abrirPar ? '<button type="button">Abrir en el reporte interactivo</button>' : '');
        const b = c.querySelector('button'); if (b) b.addEventListener('click', () => abrirPar(id));
      }
    } else if (t === 'par') graficoPar(c);
  });
  }
  renderInsertos(document);
})();
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("texto", help="archivo .md del informe, por ejemplo analisis/informes/producto_producto.md")
    args = ap.parse_args()
    origen = Path(args.texto)
    texto = origen.read_text(encoding="utf-8")

    meta = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", texto, re.S)
    if m:
        for linea in m.group(1).splitlines():
            if ":" in linea:
                k, v = linea.split(":", 1)
                meta[k.strip()] = v.strip()
        texto = texto[m.end():]
    if "cruce" not in meta:
        sys.exit("Falta 'cruce:' en el encabezado del .md (entre las líneas ---).")
    cruce = rc.normalizar_cruce(meta["cruce"])
    piezas = rc.construir(cruce)
    reporte = rc.escribir_reporte(cruce, piezas)
    lados = cruce.split("–")
    pca = SALIDA / f"reporte_pca_{lados[0].lower()}.html" if len(set(lados)) == 1 else None
    enlace_pca = (f'<p>El análisis de componentes principales de la dimensión está en '
                  f'<a href="{html.escape(pca.name)}" target="_blank">{html.escape(pca.name)}</a>.</p>'
                  if pca and pca.exists() else "")

    datos_pca = rpca.cargar(lados[0]) if len(set(lados)) == 1 else None
    cuerpo, indice = markdown(texto, hacer_inserto(piezas, datos_pca))
    titulo = meta.get("titulo", f"Análisis {cruce}")
    nav = ("<nav class='indice'><b>Contenido</b><ol>"
           + "".join(f'<li class="n{n}"><a href="#{a}">{html.escape(t)}</a></li>' for n, a, t in indice)
           + '<li><a href="#anexo">Anexo: reporte interactivo</a></li></ol></nav>')
    doc = f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo)}</title><style>{rc.ESTILO}{rpca.ESTILO_PIEZAS}{ESTILO_INFORME}</style></head>
<body><main>
<h1>{html.escape(titulo)}</h1>
<p class="sub">{html.escape(meta.get("subtitulo", f"Cruce {cruce} · serie estable de next.js"))} · generado desde {html.escape(origen.name)}</p>
{nav}
<article class="informe">
{cuerpo}
</article>

<section class="anexo" id="anexo">
<h2>Anexo: reporte interactivo</h2>
<p>El reporte completo del cruce, con la tabla de todos los pares y sus filtros, el mapa de calor, la vista general
y el explorador de pares, está en <a href="{html.escape(reporte.name)}" target="_blank">{html.escape(reporte.name)}</a>.</p>
{enlace_pca}
</section>
<div hidden>
{piezas["kpis"]}
{piezas["tabla_pares"]}
{piezas["categorias"]}
{piezas["explorador"]}
</div>
{piezas["scripts"]}
<script>abrirPar = id => window.open({json.dumps(reporte.name)} + '#par=' + encodeURIComponent(id), '_blank');</script>
<script>{SCRIPT_INSERTOS}</script>
{rc.NOTA_FINAL}
</main></body></html>
"""
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / f"informe_{origen.stem}.html"
    destino.write_text(doc, encoding="utf-8")
    print(piezas["resumen"])
    print(f"Informe: {destino} ({destino.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
