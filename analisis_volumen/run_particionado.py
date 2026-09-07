"""
run_particionado.py — Corre las métricas sobre cada período y guarda en `resultado`.

Reemplaza al run.py de una métrica a la vez. Es resumible: si se corta, volver a
correrlo retoma donde quedó (salta lo que ya está en `resultado`).

Uso:
    python -m analisis_volumen.run_particionado --listar-periodos
    python -m analisis_volumen.run_particionado --variante n500_desde2016 --dry-run
    python -m analisis_volumen.run_particionado --variante n500_desde2016
    python -m analisis_volumen.run_particionado --variante n500_desde2016 --metricas nci,mttr
    python -m analisis_volumen.run_particionado --variante n500_desde2016 --firmas
    python -m analisis_volumen.run_particionado --variante n500_desde2016 --rehacer --metricas sc,dc
"""
import argparse
import importlib
import inspect
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import Json, RealDictCursor
except ImportError:
    psycopg2 = None

BASE = Path(__file__).resolve().parent.parent


# ===========================================================================
# REGISTRO DE MÉTRICAS
# ===========================================================================
# (clave, carpeta, módulo, clase, metrica_id, por, tipo, clave_valor)
#
#   por         : 'producto' -> un valor por período (login NULL)
#                 'persona'  -> un valor por colaborador dentro del período
#   tipo        : 'flujo'    -> cuenta eventos DENTRO de la ventana; se ventanea
#                 'estado'   -> snapshot; NO depende de la ventana (se saltea por defecto)
#   clave_valor : para métricas que devuelven dict COMPUESTO {clave: {..sub..}},
#                 dice de qué sub-clave sacar el número principal. El sub-dict
#                 completo igual se guarda en value_extra.
#                 None -> la métrica devuelve {clave: número} plano, o un escalar.
#
# Casos especiales:
#   - nub devuelve {repo: {.., "nub": N}}: es PRODUCTO pero su clave externa es el
#     repo, no un login. Se marca con clave_valor="nub" y por="producto"; el
#     aplanado especial en calcular() lo convierte en una sola fila con login NULL.
# ---------------------------------------------------------------------------
REGISTRO = [
    # clave                carpeta   módulo                  clase                                        metrica_id                        por         tipo      clave_valor
    ("nci",               "35",     "nci",                  "NumberOfClosedIssues",                      "number_of_closed_issues",        "producto", "flujo",  None),
    ("anmcc",             "10",     "anmcc",                "AverageNumberOfModifiedComponentsPerCommit","anmcc",                          "producto", "flujo",  None),
    ("mttr",              "10",     "mttr",                 "MeanTimeToRepair",                          "mttr",                           "producto", "flujo",  None),
    ("cd",                "16",     "cd",                   "CommentDensity",                            "cd",                             "producto", "estado", None),
    ("rc",                "16",     "readme_completeness",  "ReadmeCompleteness",                        "readme_completeness",            "producto", "estado", None),
    ("wp",                "16",     "wiki_presence",        "WikiPresence",                              "wiki_presence",                  "producto", "estado", None),
    ("dis",               "16",     "doc_issue_survival",   "DocIssueSurvival",                          "doc_issue_survival",             "producto", "flujo",  None),
    ("dloc",              "16",     "dloc",                 "DocumentationLinesOfCode",                  "dloc",                           "producto", "estado", None),
    ("dc",                "20",     "dc",                   "SocialContribution",                        "developer_contribution_dc",      "persona",  "flujo",  "sc"),
    ("le",                "15",     "le",                   "LearningEase",                              "learning_easy",                  "persona",  "flujo",  None),
    ("ss",                "15",     "ss",                   "SkillSimilarity",                           "skill_similarity",               "persona",  "flujo",  None),
    ("rexp",              "15",     "rexp",                 "RecentExperience",                          "rexp",                           "persona",  "flujo",  None),
    ("fexp",              "15",     "fexp",                 "FileExperience",                            "fexp",                           "persona",  "flujo",  None),
    ("exprev",            "15",     "exprev",               "ReviewExperience",                          "exprev",                         "persona",  "flujo",  None),
    ("rexprev",           "15",     "rexprev",              "RecentReviewExperience",                    "rexprev",                        "persona",  "flujo",  None),
    ("cdiv",              "15",     "cdiv",                 "ContributionDiversity",                     "contribution_diversity",         "persona",  "flujo",  None),
    ("nc",                "18",     "nc",                   "NumberOfComments",                          "number_of_comments",             "persona",  "flujo",  None),
    ("disc_centrality",   "18",     "disc_centrality",      "DiscussionCentrality",                      "discussion_centrality",          "persona",  "flujo",  None),
    ("sc",                "18",     "sc",                   "SocialContribution",                        "social_contributions_sc",        "persona",  "flujo",  "sc"),
    ("schedule_compliance","23",    "schedule_compliance",  "ScheduleCompliance",                        "schedule_compliance",            "producto", "flujo",  None),
    ("cfdr",              "27",     "cfdr",                 "CustomerFoundDefectsAndRegressions",        "cfdr",                           "producto", "flujo",  None),
    ("process_performance","40",    "process_performance",  "DevelopmentProcessPerformance",             "development_process_performance","producto", "flujo",  None),
    # noi: la carpeta 28 solo tiene un .md, la clase real vive en 40/noi.py
    ("noi",               "40",     "noi",                  "NumberOfOpenIssues",                        "number_of_open_issues",          "producto", "flujo",  None),
    ("jarczyk",           "43",     "tasa_exito",           "JarczykSuccessRate",                        "tasa_de_exito_de_jarczyk",       "producto", "flujo",  None),
    ("dev_exp",           "38",     "dev_experience",       "DevelopmentExperience",                     "development_experience",         "persona",  "flujo",  "experiencia_meses"),
    # nub: el módulo es nub.py; devuelve {repo:{..,"nub":N}} -> aplanar por repo
    ("nub",               "39",     "nub",                  "NumberOfBugsDetectedByUsers",               "number_of_bugs_detected_by_users","producto","flujo",   "nub"),
    ("nob",               "42",     "nob",                  "NumberOfBranches",                          "number_of_branches",             "producto", "estado", None),
    ("loc",               "Notion", "loc",                  "LinesOfCode",                               "lines_of_code",                  "producto", "estado", None),
    ("collab",            "Notion", "collaborators",        "NumberOfCollaborators",                     "number_of_collaborators",        "producto", "estado", None),
    ("commit_freq",       "Notion", "commit_frequency",     "CommitFrequency",                           "commit_frequency",               "producto", "flujo",  None),
    ("commit_entropy",    "Notion", "commit_entropy",       "CommitEntropy",                             "commit_entropy",                 "producto", "flujo",  None),
    ("ci_presence",       "Notion", "ci_presence",          "ContinuousIntegrationPresence",             "continuous_integration",         "producto", "estado", None),
    ("commits_per_author","Notion", "commits_per_author",   "CommitsPerAuthor",                          "developer_contribution",         "persona",  "flujo",  None),
    # dev_ownership devuelve {login: {"lineas": N, "porcentaje": X}}. El valor
    # principal por persona es porcentaje (0-100); "lineas" queda igual en value_extra.
    ("dev_ownership",     "Notion", "developer_ownership",  "DeveloperOwnership",                        "developer_ownership",            "persona",  "flujo",  "porcentaje"),
    ("forks",             "Notion", "forks",                "NumberOfForks",                             "number_of_forks",                "producto", "estado", None),
    ("issues_total",      "Notion", "issues_total",         "TotalIssues",                               "total_de_issues",                "producto", "flujo",  None),
    ("prs_summary",       "Notion", "pull_requests_summary","PullRequestsSummary",                       "pull_requests_summary",          "persona",  "flujo",  "totales"),
    ("core_devs_prs",     "Notion", "core_devs_prs",        "CoreDevsPullRequests",                      "number_of_pull_requests_of_core_devs","persona","flujo","prs_generadas"),

    # --- DUPLICADOS detectados en run.py (misma clase, distinto alias) ---
    # ("nci_process",    "40", "nci_reuse",    "NumberOfClosedIssues", "number_of_closed_issues", "producto", "flujo", None),
    # ("nci_resolution", "43", "nci_reuse_43", "NumberOfClosedIssues", "number_of_closed_issues", "producto", "flujo", None),
]

MAX_FILES = None

METODOS_PRODUCTO = ("por_producto", "calcular_producto", "producto")
METODOS_PERSONA  = ("por_persona", "calcular_persona", "persona")


# ===========================================================================
# Utilidades
# ===========================================================================
def cargar_env():
    for c in (BASE / ".env", BASE / "db" / ".env"):
        if c.exists():
            for line in c.read_text().splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def conectar():
    if psycopg2 is None:
        raise SystemExit("Falta psycopg2: pip install psycopg2-binary")
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        user=os.environ.get("POSTGRES_USER", "metricas"),
        password=os.environ.get("POSTGRES_PASSWORD", "metricas"),
        dbname=os.environ.get("POSTGRES_DB", "resultados_metricas"),
    )


def cargar_clase(carpeta, modulo, clase):
    """
    Import perezoso, por-métrica. Si un módulo está roto solo cae esa métrica.
    Verifica de qué carpeta salió el módulo para detectar colisiones de nombre
    en sys.path (dos .py iguales en carpetas distintas).
    """
    ruta = str(BASE / carpeta)
    if ruta not in sys.path:
        sys.path.insert(0, ruta)

    sys.modules.pop(modulo, None)
    mod = importlib.import_module(modulo)

    origen = Path(getattr(mod, "__file__", "")).resolve().parent
    if origen != Path(ruta).resolve():
        print(f"    [!] {modulo} se importó desde {origen}, no desde {ruta} "
              f"— colisión de nombres en sys.path", file=sys.stderr)

    return getattr(mod, clase)


def kwargs_soportados(fn, por):
    candidatos = {"por": por, "max_files": MAX_FILES}
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return candidatos
    if any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values()):
        return candidatos
    return {k: v for k, v in candidatos.items() if k in sig.parameters}


def llamar_fetch(inst, fecha_inicio, fecha_fin, por):
    """
    Llama a fetch() adaptándose a su firma:
      - fetch()                      -> baja todo, filtra después (NCI-style)
      - fetch(fecha_inicio, fecha_fin) -> ya trae solo la ventana
      - fetch(..., con_actor=True)   -> para atribuir por persona (NCI)
    """
    if not hasattr(inst, "fetch"):
        return
    args, kwargs = [], {}
    try:
        params = inspect.signature(inst.fetch).parameters
        if "fecha_inicio" in params and "fecha_fin" in params:
            args = [fecha_inicio, fecha_fin]
        if por == "persona" and "con_actor" in params:
            kwargs["con_actor"] = True
    except (TypeError, ValueError):
        pass
    inst.fetch(*args, **kwargs)


def calcular(inst, fecha_inicio, fecha_fin, por):
    """
    Devuelve el valor de la métrica llamando a por_producto/por_persona
    (no a run(), que solo imprime en varias clases).
    """
    llamar_fetch(inst, fecha_inicio, fecha_fin, por)
    candidatos = METODOS_PERSONA if por == "persona" else METODOS_PRODUCTO
    for nombre in candidatos:
        metodo = getattr(inst, nombre, None)
        if callable(metodo):
            return metodo(fecha_inicio, fecha_fin)
    return inst.run(fecha_inicio, fecha_fin, **kwargs_soportados(inst.run, por))


def inspeccionar_firmas(seleccion):
    print(f"{'clave':20} {'método cálculo':20} {'clave_valor':18} {'firma de fetch()'}")
    print("-" * 100)
    for clave, carpeta, modulo, clase, _mid, por, _tipo, clave_valor in seleccion:
        try:
            Clase = cargar_clase(carpeta, modulo, clase)
            candidatos = METODOS_PERSONA if por == "persona" else METODOS_PRODUCTO
            usa = next((n for n in candidatos if hasattr(Clase, n)), "run() [solo imprime?]")
            try:
                fsig = str(inspect.signature(Clase.fetch))
            except AttributeError:
                fsig = "(sin fetch)"
            print(f"{clave:20} {usa:20} {str(clave_valor):18} {fsig}")
        except Exception as e:
            print(f"{clave:20} [!] {type(e).__name__}: {e}")


def _num(v):
    if isinstance(v, bool):
        return float(v)
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def normalizar(salida, clave_valor=None, aplanar_producto=False):
    """
    Convierte lo que devuelva el cálculo a filas [(login|None, value, extra)].

    - escalar / bool                     -> una fila, login None
    - {clave: número}                    -> una fila por clave (login=clave)
    - {clave: {..sub..}} con clave_valor -> value = sub[clave_valor], extra = sub
    - {clave: {..sub..}} sin clave_valor -> intenta sub["value"]
    - lista de dicts                     -> una fila por dict

    aplanar_producto=True: el dict externo es {repo: {..}} y es PRODUCTO, no
    persona. Se toma el ÚNICO sub-dict y se emite con login None (caso nub).
    """
    if salida is None:
        return None
    if isinstance(salida, bool):
        return [(None, float(salida), None)]
    if isinstance(salida, (int, float)):
        return [(None, float(salida), None)]

    if isinstance(salida, dict):
        # dict simple {'value':.., 'extra':..}
        if "value" in salida and not isinstance(salida["value"], dict):
            return [(salida.get("login"), _num(salida["value"]), salida.get("extra"))]

        # caso nub: {repo: {.., clave_valor: N}} -> una fila producto, login None
        if aplanar_producto:
            for _clave_externa, sub in salida.items():
                if isinstance(sub, dict):
                    num = sub.get(clave_valor) if clave_valor else sub.get("value")
                    return [(None, _num(num), sub)]
            return None

        filas = []
        for k, v in salida.items():
            if isinstance(v, dict):
                num = v.get(clave_valor) if clave_valor else v.get("value")
                filas.append((str(k), _num(num), v))
            else:
                filas.append((str(k), _num(v), None))
        return filas or None

    if isinstance(salida, (list, tuple)):
        filas = []
        for it in salida:
            if isinstance(it, dict):
                num = it.get(clave_valor) if clave_valor else it.get("value")
                filas.append((it.get("login") or it.get("contribuyente"), _num(num), it))
        return filas or None

    return None


# ===========================================================================
def main():
    cargar_env()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--variante", help="ej. n500_desde2016")
    ap.add_argument("--tipo-analisis", default="volumen")
    ap.add_argument("--metricas", help="lista separada por comas; default: todas")
    ap.add_argument("--incluir-estado", action="store_true",
                    help="correr también las métricas snapshot (no ventaneables)")
    ap.add_argument("--rehacer", action="store_true", help="recalcular lo ya guardado")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--listar-periodos", action="store_true")
    ap.add_argument("--firmas", action="store_true",
                    help="mostrar qué método y clave_valor usará cada métrica y salir")
    ap.add_argument("--limite-periodos", type=int, default=None,
                    help="correr solo los primeros N períodos (para probar rápido)")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    org, repo = os.environ.get("TARGET_ORG"), os.environ.get("TARGET_REPO")
    if not all([token, org, repo]):
        raise SystemExit("Faltan GITHUB_TOKEN / TARGET_ORG / TARGET_REPO en .env")

    seleccion = [m for m in REGISTRO if args.incluir_estado or m[6] == "flujo"]
    if args.metricas:
        pedidas = {x.strip() for x in args.metricas.split(",")}
        seleccion = [m for m in REGISTRO if m[0] in pedidas]
        faltan = pedidas - {m[0] for m in seleccion}
        if faltan:
            print(f"[!] no están en el REGISTRO: {', '.join(sorted(faltan))}", file=sys.stderr)

    if args.firmas:
        inspeccionar_firmas(seleccion)
        return

    conn = conectar()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    if args.listar_periodos:
        cur.execute("""
            SELECT p.tipo_analisis, p.variante, COUNT(*) n,
                   MIN(p.fecha_inicio)::date desde, MAX(p.fecha_fin)::date hasta,
                   BOOL_OR(p.es_principal) principal
            FROM periodo p JOIN repos r USING (repo_id)
            WHERE r.full_name = %s
            GROUP BY 1, 2 ORDER BY 1, 2
        """, (f"{org}/{repo}",))
        for f in cur.fetchall():
            print(f"  {f['tipo_analisis']:12} {f['variante'] or '-':18} "
                  f"{f['n']:3d} períodos  {f['desde']} → {f['hasta']}"
                  f"{'  [PRINCIPAL]' if f['principal'] else ''}")
        return

    if not args.variante:
        raise SystemExit("Falta --variante (usá --listar-periodos para ver cuáles hay)")

    cur.execute("""
        SELECT p.periodo_id, p.periodo_num, p.fecha_inicio, p.fecha_fin, p.etiqueta
        FROM periodo p JOIN repos r USING (repo_id)
        WHERE r.full_name=%s AND p.tipo_analisis=%s AND p.variante=%s
        ORDER BY p.periodo_num
    """, (f"{org}/{repo}", args.tipo_analisis, args.variante))
    periodos = cur.fetchall()
    if not periodos:
        raise SystemExit(f"No hay períodos para variante '{args.variante}'.")

    if args.limite_periodos:
        periodos = periodos[:args.limite_periodos]

    saltadas = [m[0] for m in REGISTRO if m[6] == "estado"] if not args.incluir_estado else []

    print(f"Repo      : {org}/{repo}")
    print(f"Variante  : {args.variante} ({len(periodos)} períodos)")
    print(f"Métricas  : {len(seleccion)}")
    if saltadas:
        print(f"Salteadas : {len(saltadas)} de tipo 'estado' (no ventaneables): "
              f"{', '.join(saltadas)}")
    print(f"Total     : {len(periodos) * len(seleccion)} cálculos\n")

    if args.dry_run:
        print("(dry-run)")
        return

    cur.execute("SELECT periodo_id, metrica_id FROM resultado WHERE periodo_id = ANY(%s)",
                ([p["periodo_id"] for p in periodos],))
    hechos = {(r["periodo_id"], r["metrica_id"]) for r in cur.fetchall()}

    ok = saltados = fallos = 0
    log_fallos = []
    fallos_seguidos = {}
    abandonadas = set()
    w = conn.cursor()

    for p in periodos:
        print(f"[{p['periodo_num']:3d}/{len(periodos)}] {p['etiqueta']}")

        for clave, carpeta, modulo, clase, metrica_id, por, _tipo, clave_valor in seleccion:
            if clave in abandonadas:
                continue
            if not args.rehacer and (p["periodo_id"], metrica_id) in hechos:
                saltados += 1
                continue

            try:
                Clase = cargar_clase(carpeta, modulo, clase)
                inst = Clase(token, org, repo)
                salida = calcular(inst, p["fecha_inicio"], p["fecha_fin"], por)

                aplanar = (clave == "nub")  # producto con dict {repo: {..}}
                filas = normalizar(salida, clave_valor=clave_valor,
                                   aplanar_producto=aplanar)
                if filas is None:
                    raise ValueError(
                        "el cálculo no devolvió nada usable "
                        "(¿la clase no expone por_producto/por_persona?)")

                if args.rehacer:
                    w.execute("DELETE FROM resultado WHERE periodo_id=%s AND metrica_id=%s",
                              (p["periodo_id"], metrica_id))

                guardadas = 0
                for login, valor, extra in filas:
                    w.execute("""
                        INSERT INTO resultado (periodo_id, metrica_id, contribuyente_login,
                                               value, value_extra, calculado_en)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (p["periodo_id"], metrica_id, login, valor,
                          Json(extra) if extra else None, datetime.now(timezone.utc)))
                    guardadas += 1

                conn.commit()
                ok += 1
                fallos_seguidos[clave] = 0
                # aviso si guardó filas pero todas sin número (síntoma de clave_valor mal)
                sin_valor = sum(1 for _, v, _ in filas if v is None)
                marca = f"  [!] {sin_valor}/{guardadas} sin value" if sin_valor else ""
                print(f"    ✓ {clave:20} {guardadas:4d} fila(s){marca}")

            except Exception as e:
                conn.rollback()
                fallos += 1
                log_fallos.append((p["periodo_num"], clave, repr(e)))
                print(f"    ✗ {clave:20} {type(e).__name__}: {e}", file=sys.stderr)

                fallos_seguidos[clave] = fallos_seguidos.get(clave, 0) + 1
                if fallos_seguidos[clave] >= 3:
                    abandonadas.add(clave)
                    print(f"    [!] {clave}: 3 fallos seguidos, se abandona "
                          f"(revisar la clase y volver a correr solo esa métrica)",
                          file=sys.stderr)

    print(f"\n{'=' * 60}")
    print(f"ok: {ok}   ya estaban: {saltados}   fallos: {fallos}")
    if abandonadas:
        print(f"abandonadas: {', '.join(sorted(abandonadas))}")

    if log_fallos:
        destino = BASE / "data" / f"fallos_{args.variante}.log"
        destino.parent.mkdir(exist_ok=True)
        destino.write_text("\n".join(f"periodo {n}\t{m}\t{e}" for n, m, e in log_fallos))
        print(f"Fallos registrados en {destino}")
        print("Revisar antes de analizar: una celda vacía por fallo NO es un cero.")

    w.close()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()