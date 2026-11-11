#!/usr/bin/env python3
"""
Escribe salidas/LEEME.md: el índice de las salidas del análisis, con qué mirar primero, cuántos
patrones quedaron y qué hay en cada carpeta (solo lo que se generó en esta corrida).

Uso: python3 analisis/indice.py   (lo corre tres_p.py analizar al terminar)
"""
import csv
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rutas  # noqa: E402

S = rutas.SALIDAS

# (ruta relativa a salidas/, qué es). Los <dim> y <cruce> se expanden con lo que exista.
CARPETAS = [
    ("5_patrones", "**Resultado principal.** Patrones que superaron todos los controles, por par de dimensiones, y las cadenas entre las tres", [
        ("resumen.md", "los patrones explicados, agrupados por par de dimensiones"),
        ("patrones.csv", "cada par de variables evaluado: correlación, controles y por qué es o no patrón"),
        ("cadenas.csv", "tríos de variables de tres aspectos distintos: tridimensionales o cadenas"),
        ("correlaciones/", "todos los pares de variables con sus estadísticas (base de la clasificación)"),
    ]),
    ("1_variables", "Qué se mide: cada variable del análisis", [
        ("diccionario_variables.csv", "métrica, nivel (producto o persona), estadístico, dimensiones del catálogo y cobertura"),
    ]),
    ("2_dimensiones", "Cada dimensión por separado", [
        ("correlaciones/", "pares de variables dentro de cada dimensión (`metodo_correlaciones.md` explica las columnas)"),
        ("<dim>/pca_*.csv, pca.json", "componentes principales: autovalores, cargas, puntajes por release y comparación entre series"),
        ("<dim>/agrupamiento*.{json,csv}", "grupos de métricas que se mueven juntas"),
    ]),
    ("3_cruces", "Cada par de dimensiones (<dima>_<dimb>)", [
        ("resumen.md", "lo que conecta a las dos dimensiones"),
        ("pares_variables.csv · pares_componentes.csv · pares_reducido.csv", "pares de variables, de componentes y del conjunto reducido"),
        ("triangulacion.csv", "qué patrones de variables se confirman con los componentes"),
        ("red_nodos.csv · red_aristas.csv", "la red de relaciones robustas"),
        ("resumen.json · valores.json", "datos para los reportes"),
    ]),
    ("4_tres_dimensiones", "Las tres dimensiones a la vez", [
        ("resumen.md", "asociación global frente al azar, triángulos de componentes, perfiles y rezago"),
    ]),
    ("6_robustez", "Pruebas de que los hallazgos no dependen de decisiones del método", [
        ("multiverso_asignacion/resumen.md", "qué conexiones dependen de a qué dimensión se asignan las métricas compartidas"),
        ("metricas_compartidas/resumen.md", "componentes y grupos cruzados sin las métricas que comparten dos dimensiones"),
    ]),
    ("reportes", "Reportes HTML interactivos, uno por nivel de análisis (se abren en el navegador)", [
        ("intradimensional.html", "cada dimensión: patrones finales, correlaciones, PCA y agrupamiento"),
        ("bidimensional.html", "cada par: patrones finales, variables y componentes, grupos, sin métricas compartidas y multiverso"),
        ("tridimensional.html", "medida global, red, triángulos, tríos de variables, PCA conjunto y multiverso"),
    ]),
]


def contar_patrones():
    ruta = rutas.PATRONES / "patrones.csv"
    if not ruta.exists():
        return None
    with open(ruta, newline="", encoding="utf-8") as f:
        filas = [r for r in csv.DictReader(f) if r.get("patron") == "True"]
    por_tipo = {}
    for r in filas:
        por_tipo[r["tipo"]] = por_tipo.get(r["tipo"], 0) + 1
    return len(filas), por_tipo


def main():
    S.mkdir(parents=True, exist_ok=True)
    L = [f"# Salidas del análisis — {rutas.proyecto.REPO or 'proyecto'}", "",
         f"Generado el {date.today().isoformat()} con `tres_p.py analizar`. "
         "Las carpetas están numeradas en el orden en que se calculan; el resultado está en `5_patrones/`.", ""]
    c = contar_patrones()
    if c:
        n, por_tipo = c
        detalle = ", ".join(f"{v} {k}" for k, v in sorted(por_tipo.items()))
        L += [f"**{n} patrones** ({detalle}). Empezar por [`5_patrones/resumen.md`](5_patrones/resumen.md).", ""]
    if not rutas.proyecto.CFG.get("descartados"):
        L += ["> Sin un CSV de `descartados` en `proyecto.json`, los patrones son candidatos: falta "
              "validarlos recalculando cada relación sin los datos que podrían producirla.", ""]
    for carpeta, titulo, items in CARPETAS:
        if not (S / carpeta).exists():
            continue
        L += [f"## `{carpeta}/`", "", titulo + ".", "", "| Archivo | Qué tiene |", "|---|---|"]
        L += [f"| `{a}` | {b} |" for a, b in items]
        if carpeta == "3_cruces":
            hay = sorted(p.name for p in (S / carpeta).iterdir() if p.is_dir())
            L += ["", "Cruces: " + ", ".join(f"[`{h}`]({carpeta}/{h}/resumen.md)" for h in hay)]
        L.append("")
    L += ["Cómo interpretar cada archivo: `SALIDAS.md`; el método de cada paso: `analisis/README.md` (repositorio de tres_p)."]
    (S / "LEEME.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"Índice en {S / 'LEEME.md'}")


if __name__ == "__main__":
    main()
