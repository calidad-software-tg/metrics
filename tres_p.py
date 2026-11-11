#!/usr/bin/env python3
"""
tres_p — patrones de calidad Persona, Proceso y Producto a partir de un repositorio de GitHub.

Encadena los pasos del trabajo: calcula las 26 métricas por ventana entre releases, unifica las
identidades, exporta las métricas por persona y corre el análisis (correlaciones con controles,
PCA, agrupamiento, cruces entre dimensiones, análisis de las tres dimensiones, multiverso de
asignaciones y clasificación final de los patrones).

Uso:
    python3 tres_p.py iniciar --repo org/nombre [--clon /ruta/al/clon] [--hasta AAAA-MM-DD]
    python3 tres_p.py todo                 # base + calcular + identidades + exportar + analizar
    python3 tres_p.py base                 # crea la base del proyecto (si no existe)
    python3 tres_p.py calcular [--series estable,canary] [--solo k1,k2] [--solo-locales]
    python3 tres_p.py identidades          # nombre de git -> login de GitHub
    python3 tres_p.py exportar             # métricas por persona (CSV)
    python3 tres_p.py analizar             # análisis completo y reportes (--sin-complementarios, --sin-reportes)
    python3 tres_p.py estado               # qué hay calculado en la base

La configuración del proyecto está en proyecto.json (ver proyecto.example.json); las credenciales
(GITHUB_TOKEN y POSTGRES_*) en .env. Cada proyecto usa su propia base (POSTGRES_DB).
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROYECTO = Path(os.environ.get("TRES_P_PROYECTO", ROOT / "proyecto.json"))
PY = sys.executable

# Métricas del trabajo (26 implementadas, más las variantes que usa el análisis).
LOCALES = ["dloc", "cd", "rc", "cdiv", "fexp", "le", "rexp", "anmcc", "dloc_flujo", "commits_doc"]
REMOTAS = ["mttr", "mttr_p50", "mttr_bugs", "mttr_con_bots", "nci", "nci_con_bots", "noi", "noi_28",
           "dis", "wp", "sc", "nc", "disc_centrality", "exprev", "rexprev", "dev_exp", "ss", "nub",
           "cfdr", "process_performance", "jarczyk_success_rate", "schedule_compliance", "nob_42"]
DIMS = ["Persona", "Proceso", "Producto"]
CRUCES = [("Persona", "Proceso"), ("Persona", "Producto"), ("Proceso", "Producto")]


# ── utilidades ────────────────────────────────────────────────────────────────

def cargar_env():
    env = ROOT / ".env"
    if env.exists():
        for linea in env.read_text().splitlines():
            if "=" in linea and not linea.lstrip().startswith("#"):
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def leer_proyecto():
    if not PROYECTO.exists():
        sys.exit(f"No existe {PROYECTO}. Primero: python3 tres_p.py iniciar --repo org/nombre")
    cfg = json.loads(PROYECTO.read_text(encoding="utf-8"))
    if cfg.get("clon"):
        os.environ["TRES_P_CLON"] = str(Path(cfg["clon"]).expanduser())
    os.environ["TRES_P_PROYECTO"] = str(PROYECTO)
    return cfg


def correr(*args, opcional=False):
    cmd = [PY, *map(str, args)]
    print(f"\n$ {' '.join(cmd[1:])}", flush=True)
    t0 = time.time()
    r = subprocess.run(cmd, cwd=ROOT, env=os.environ.copy())
    print(f"  ({time.time() - t0:.0f} s)", flush=True)
    if r.returncode != 0:
        msg = f"falló: {' '.join(cmd[1:])} (código {r.returncode})"
        if opcional:
            print(f"  aviso: {msg}; sigo con el resto", flush=True)
        else:
            sys.exit(msg)


def conectar(dbname=None):
    import psycopg2
    return psycopg2.connect(host=os.environ.get("POSTGRES_HOST", "localhost"),
                            port=int(os.environ.get("POSTGRES_PORT", 5432)),
                            user=os.environ.get("POSTGRES_USER", "metricas"),
                            password=os.environ.get("POSTGRES_PASSWORD", "metricas"),
                            dbname=dbname or os.environ.get("POSTGRES_DB", "resultados_metricas"))


# ── comandos ──────────────────────────────────────────────────────────────────

def cmd_iniciar(a):
    if PROYECTO.exists() and not a.forzar:
        sys.exit(f"{PROYECTO} ya existe (usá --forzar para reemplazarlo)")
    if "/" not in a.repo:
        sys.exit("--repo tiene que ser org/nombre, como en GitHub")
    cfg = {
        "repo": a.repo,
        "clon": a.clon,
        "hasta": a.hasta,
        "excluir_estable": [],
        "calendario": "auto",
        "cortes_epocas": "auto",
        "descartados": None,
        "cruces": None,
        "tres_dimensiones": None,
        "advertencias": None,
    }
    PROYECTO.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Proyecto creado en {PROYECTO}:\n{json.dumps(cfg, ensure_ascii=False, indent=2)}")
    nombre = "tres_p_" + "".join(c if c.isalnum() else "_" for c in a.repo.lower())
    print(f"\nSugerencia: usá una base propia para este repositorio, POSTGRES_DB={nombre} en .env")


def cmd_base(a):
    leer_proyecto()
    import psycopg2
    nombre = os.environ.get("POSTGRES_DB", "resultados_metricas")
    con = conectar("postgres")
    con.autocommit = True
    cur = con.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (nombre,))
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{nombre}"')
        print(f"Base {nombre} creada")
    con.close()
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT to_regclass('public.resultado')")
    if cur.fetchone()[0] is None:
        cur.execute((ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))
        cur.execute((ROOT / "db" / "metrics_seed.sql").read_text(encoding="utf-8"))
        con.commit()
        print("Esquema y catálogo de métricas cargados")
    else:
        print(f"La base {nombre} ya tiene el esquema")
    con.close()


def cmd_calcular(a):
    cfg = leer_proyecto()
    repo = cfg["repo"]
    series = [s.strip() for s in a.series.split(",")]
    solo = {s.strip() for s in a.solo.split(",")} if a.solo else None
    locales = [m for m in LOCALES if not solo or m in solo]
    remotas = [] if a.solo_locales else [m for m in REMOTAS if not solo or m in solo]
    hasta = ["--hasta", cfg["hasta"]] if cfg.get("hasta") else []
    for serie in series:
        canary = ["--con-canary"] if serie == "canary" else []
        if locales:
            correr("metricas/run_versiones_local.py", "--repo", repo, "--solo", ",".join(locales), *hasta, *canary)
        if remotas:
            correr("metricas/run_versiones.py", ",".join(remotas), "--repo", repo, *hasta, *canary)


def cmd_identidades(a):
    cfg = leer_proyecto()
    correr("metricas/mapear_identidades.py", "--repo", cfg["repo"])


def cmd_exportar(a):
    leer_proyecto()
    correr("metricas/export_persona.py")


MIN_RELEASES = 30   # preprocesamiento excluye las variables con datos en menos de 30 releases


def cmd_analizar(a):
    cfg_p = leer_proyecto()
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT count(*) FROM periodo WHERE tipo_analisis = 'versiones'")
    n = cur.fetchone()[0]
    con.close()
    if n < MIN_RELEASES:
        sys.exit(f"La serie estable tiene {n} ventanas entre releases y el análisis necesita al menos "
                 f"{MIN_RELEASES}: cada correlación se calcula sobre las ventanas, y con menos no es "
                 "confiable. Elegí un repositorio con más releases (o un --hasta posterior).")
    # Regla de estabilidad: al menos MIN_PERIODOS períodos del calendario con MIN_RELEASES_PERIODO releases
    import proyecto
    por_periodo = proyecto.releases_por_periodo()
    evaluables = [lab for lab, k in por_periodo if k >= proyecto.MIN_RELEASES_PERIODO]
    if len(evaluables) < proyecto.MIN_PERIODOS:
        detalle = ", ".join(f"{lab}: {k}" for lab, k in por_periodo) or "sin períodos"
        sys.exit(f"Un patrón tiene que mantener el signo en al menos {proyecto.MIN_PERIODOS} períodos de la historia, "
                 f"con {proyecto.MIN_RELEASES_PERIODO} releases estables o más en cada uno "
                 f"(al menos {proyecto.MIN_PERIODOS * proyecto.MIN_RELEASES_PERIODO} en total). Este proyecto tiene "
                 f"{n} ({detalle}), así que ninguna relación podría ser patrón. Elegí un repositorio con más releases "
                 "o, si el calendario de proyecto.json es manual, revisá sus períodos.")
    print("Períodos de la regla de estabilidad: "
          + ", ".join(f"{lab} ({k} releases)" for lab, k in por_periodo), flush=True)
    sys.path.insert(0, str(ROOT / "analisis"))
    import rutas
    rutas.VARIABLES.mkdir(parents=True, exist_ok=True)
    correr("analisis/generar_diccionario.py")
    correr("analisis/correlaciones.py")
    # El PCA necesita al menos 3 releases por variable: en una dimensión sin componentes se saltean el
    # agrupamiento y los cruces de componentes con ella. Las correlaciones y los patrones no dependen de esto.
    con_pca = []
    for d in DIMS:
        correr("analisis/pca.py", d)
        if (rutas.dimension(d) / "pca.json").exists():
            con_pca.append(d)
    for d in con_pca:
        correr("analisis/clustering.py", d, "--sin-reporte")
    cruces_pca = [(x, y) for x, y in CRUCES if x in con_pca and y in con_pca]
    sin = [f"{x}–{y}" for x, y in CRUCES if (x, y) not in cruces_pca]
    if sin:
        print(f"\nSin PCA en {', '.join(d for d in DIMS if d not in con_pca)}: se saltean los cruces de "
              f"componentes {', '.join(sin)}", flush=True)
    for x, y in cruces_pca:
        cfg = ROOT / (cfg_p.get("cruces") or "analisis/cruces") / f"{x.lower()}_{y.lower()}.json"
        correr("analisis/cruces.py", x, y, "--config", cfg)
        correr("analisis/cruces.py", x, y, "--config", cfg, "--grupos", "propio", opcional=True)
    # Tres dimensiones, multiverso y bloques usan los componentes de las tres dimensiones.
    tres = len(con_pca) == len(DIMS)
    if tres:
        correr("analisis/tres_dimensiones.py", opcional=True)
        correr("analisis/multiverso_asignacion.py", opcional=True)
    else:
        print("\nSin componentes en las tres dimensiones: se saltean tres_dimensiones, multiverso_asignacion "
              "y bloques_etiquetas", flush=True)
    correr("analisis/relaciones.py", "--recalcular")
    if tres:
        correr("analisis/bloques_etiquetas.py", opcional=True)
    if not getattr(a, "sin_complementarios", False):
        # Análisis que no son técnica principal (analisis/README.md, secciones 10 y 12); son los más lentos.
        comp = rutas.COMPLEMENTARIOS
        correr("analisis/correlaciones.py", "--periodos", "ambos", "--salida", comp / "periodos", opcional=True)
        correr("analisis/complementarios/temporal.py", "releases", opcional=True)
        correr("analisis/complementarios/temporal.py", "epocas", opcional=True)
        for x, y in cruces_pca:
            cfg = ROOT / (cfg_p.get("cruces") or "analisis/cruces") / f"{x.lower()}_{y.lower()}.json"
            correr("analisis/cruces.py", x, y, "--config", cfg, "--periodos", "epocas", opcional=True)
            correr("analisis/complementarios/cruce_alternativos.py", x, y, "--config", cfg, opcional=True)
        if ("Proceso", "Producto") in cruces_pca:
            cfg_pp = ROOT / (cfg_p.get("cruces") or "analisis/cruces") / "proceso_producto.json"
            correr("analisis/complementarios/cruce_rezago.py", ROOT, cfg_pp, comp / "rezago", opcional=True)
        correr("analisis/complementarios/pesos_catalogo.py", opcional=True)
    if not a.sin_reportes:
        for d in con_pca:
            correr("analisis/reporte_pca.py", d, opcional=True)
        for d in DIMS:
            correr("analisis/reporte_cruce.py", f"{d}-{d}", opcional=True)
        for x, y in cruces_pca:
            correr("analisis/reporte_cruce_dimensiones.py", x, y, opcional=True)
        if tres:
            correr("analisis/reporte_tres_dimensiones.py", opcional=True)
        correr("analisis/reporte_resultados.py", opcional=True)
        if not getattr(a, "sin_complementarios", False):
            correr("analisis/reporte_complementarios.py", opcional=True)
        correr("analisis/reportes.py")
    correr("analisis/indice.py")
    print(f"\nListo. Índice de las salidas: {rutas.SALIDAS / 'LEEME.md'}\n"
          f"Patrones: {rutas.PATRONES / 'resumen.md'}")


def cmd_estado(a):
    leer_proyecto()
    con = conectar()
    cur = con.cursor()
    cur.execute("""SELECT p.tipo_analisis, count(DISTINCT p.periodo_id), count(DISTINCT r.metrica_id)
                   FROM periodo p LEFT JOIN resultado r ON r.periodo_id = p.periodo_id
                   GROUP BY 1 ORDER BY 1""")
    filas = cur.fetchall()
    if not filas:
        print("La base no tiene ventanas todavía (correr: python3 tres_p.py calcular)")
    for tipo, n_v, n_m in filas:
        print(f"{tipo:18s} {n_v:6d} ventanas · {n_m:3d} métricas")
    cur.execute("""SELECT metrica_id FROM resultado GROUP BY 1 ORDER BY 1""")
    hechas = {f[0] for f in cur.fetchall()}
    faltan = [m for m in LOCALES + REMOTAS if m not in hechas]
    print("Faltan:", ", ".join(faltan) if faltan else "ninguna")
    con.close()


def cmd_todo(a):
    cmd_base(a)
    cmd_calcular(a)
    cmd_identidades(a)
    cmd_exportar(a)
    cmd_analizar(a)


def main():
    cargar_env()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("iniciar", help="crea proyecto.json para un repositorio")
    p.add_argument("--repo", required=True, metavar="ORG/NOMBRE")
    p.add_argument("--clon", help="clon local ya existente (si no, se clona en .clones/)")
    p.add_argument("--hasta", metavar="AAAA-MM-DD", help="fecha de corte de la historia (por defecto, hoy)")
    p.add_argument("--forzar", action="store_true")
    p.set_defaults(f=cmd_iniciar)

    for nombre, f, ayuda in [("base", cmd_base, "crea la base del proyecto"),
                             ("identidades", cmd_identidades, "nombre de git -> login de GitHub"),
                             ("exportar", cmd_exportar, "métricas por persona"),
                             ("estado", cmd_estado, "qué hay calculado")]:
        sub.add_parser(nombre, help=ayuda).set_defaults(f=f)

    for nombre, f, ayuda in [("calcular", cmd_calcular, "métricas por ventana entre releases"),
                             ("todo", cmd_todo, "todos los pasos en orden")]:
        p = sub.add_parser(nombre, help=ayuda)
        p.add_argument("--series", default="estable,canary",
                       help="estable (releases estables) y canary (todas las releases, réplica)")
        p.add_argument("--solo", metavar="k1,k2", help="solo estas métricas")
        p.add_argument("--solo-locales", action="store_true",
                       help="solo las métricas que salen del clon (sin la API de GitHub)")
        p.add_argument("--sin-reportes", action="store_true")
        p.add_argument("--sin-complementarios", action="store_true", help="saltea los análisis complementarios (los más lentos)")
        p.set_defaults(f=f)

    p = sub.add_parser("analizar", help="análisis completo y reportes")
    p.add_argument("--sin-reportes", action="store_true")
    p.add_argument("--sin-complementarios", action="store_true", help="saltea los análisis complementarios (los más lentos)")
    p.set_defaults(f=cmd_analizar)

    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
