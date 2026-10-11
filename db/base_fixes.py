"""
Base de resultados separada para las métricas corregidas (branch de fixes).

Las correcciones cambian cómo se arman las ventanas (sin backports, sin ventanas de menos
de un día), así que los resultados viejos de next.js no sirven en la base nueva: quedarían
pegados a ventanas que ya no existen. Por eso la base nueva es una copia de la original
(esquema, repos y catálogo de métricas) SIN los resultados de next.js en las series de
releases. La base original queda intacta para comparar.

Uso (desde la raíz del repo, con la base levantada):

    python3 db/base_fixes.py crear
        crea resultados_metricas_fixes como copia de resultados_metricas y borra los
        resultados y períodos de vercel/next.js en 'versiones' y 'versiones_canary'

    POSTGRES_DB=resultados_metricas_fixes python3 run_versiones.py nci,mttr --repo vercel/next.js --hasta 2026-10-01
        las corridas apuntan a la base nueva con POSTGRES_DB (no hace falta tocar el .env)

    python3 db/base_fixes.py exportar --metricas nci,mttr --salida db/fixes_ine.csv.gz
        exporta los períodos y resultados de esas métricas (en la base nueva)

    python3 db/base_fixes.py importar db/fixes_luz.csv.gz
        importa en la base nueva lo que exportó otra integrante

Para que los resultados de distintas personas se puedan juntar, todas tienen que correr con
la misma fecha de corte (--hasta), así las ventanas son idénticas.
"""
import argparse
import csv
import gzip
import json
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

ROOT = Path(__file__).resolve().parent.parent
_env = ROOT / ".env"
if _env.exists():
    for _l in _env.read_text().splitlines():
        if "=" in _l and not _l.startswith("#"):
            _k, _v = _l.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

ORIGEN = "resultados_metricas"
DESTINO = "resultados_metricas_fixes"
REPO = "vercel/next.js"
TIPOS = ("versiones", "versiones_canary")
COLUMNAS = ["repo", "tipo_analisis", "periodo_num", "fecha_inicio", "fecha_fin", "etiqueta", "parametros",
            "metrica_id", "contribuyente_login", "value", "value_extra"]


def conectar(dbname: str):
    return psycopg2.connect(host=os.environ.get("POSTGRES_HOST", "localhost"),
                            port=os.environ.get("POSTGRES_PORT", "5432"),
                            user=os.environ.get("POSTGRES_USER", "metricas"),
                            password=os.environ.get("POSTGRES_PASSWORD", "metricas"),
                            dbname=dbname)


def crear(origen: str, destino: str):
    con = conectar(origen)
    con.autocommit = True
    cur = con.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (destino,))
    if cur.fetchone():
        sys.exit(f"La base {destino} ya existe. Borrala a mano si querés recrearla.")
    con.close()
    # CREATE DATABASE ... TEMPLATE necesita que nadie esté conectado a la base de origen.
    con = conectar("postgres")
    con.autocommit = True
    cur = con.cursor()
    cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = %s AND pid <> pg_backend_pid()", (origen,))
    cur.execute(f'CREATE DATABASE "{destino}" TEMPLATE "{origen}"')
    con.close()

    con = conectar(destino)
    cur = con.cursor()
    cur.execute("SELECT repo_id FROM repos WHERE full_name = %s", (REPO,))
    fila = cur.fetchone()
    if fila:
        cur.execute("""DELETE FROM resultado WHERE periodo_id IN
                       (SELECT periodo_id FROM periodo WHERE repo_id = %s AND tipo_analisis = ANY(%s))""",
                    (fila[0], list(TIPOS)))
        borrados = cur.rowcount
        cur.execute("DELETE FROM periodo WHERE repo_id = %s AND tipo_analisis = ANY(%s)", (fila[0], list(TIPOS)))
        print(f"{destino}: borrados {borrados} resultados y {cur.rowcount} períodos de {REPO} en {', '.join(TIPOS)}")
    con.commit()
    con.close()
    print(f"Base {destino} creada como copia de {origen}. Para usarla: POSTGRES_DB={destino} python3 ...")


def exportar(dbname: str, metricas: list[str], salida: Path):
    con = conectar(dbname)
    cur = con.cursor()
    cur.execute("""
        SELECT rp.full_name, p.tipo_analisis, p.periodo_num, p.fecha_inicio, p.fecha_fin, p.etiqueta,
               p.parametros, r.metrica_id, r.contribuyente_login, r.value, r.value_extra
        FROM resultado r
        JOIN periodo p ON p.periodo_id = r.periodo_id
        JOIN repos rp ON rp.repo_id = p.repo_id
        WHERE r.metrica_id = ANY(%s)
        ORDER BY r.metrica_id, p.tipo_analisis, p.periodo_num
    """, (metricas,))
    filas = cur.fetchall()
    con.close()
    with gzip.open(salida, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNAS)
        for fila in filas:
            fila = list(fila)
            fila[3], fila[4] = fila[3].isoformat(), fila[4].isoformat()
            fila[6] = json.dumps(fila[6]) if fila[6] is not None else ""
            fila[10] = json.dumps(fila[10]) if fila[10] is not None else ""
            w.writerow(fila)
    print(f"{len(filas)} resultados de {', '.join(metricas)} exportados a {salida}")


def importar(dbname: str, archivo: Path):
    sys.path.insert(0, str(ROOT))
    os.environ["POSTGRES_DB"] = dbname
    from run_versiones import Base  # mismos upserts que las corridas
    base = Base()
    n = 0
    repos: dict[str, int] = {}
    with gzip.open(archivo, "rt", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["repo"] not in repos:
                org, repo = r["repo"].split("/", 1)
                repos[r["repo"]] = base.repo_id(org, repo)
            base.ensure_metrica(r["metrica_id"])
            periodo_id = base.upsert_periodo(repos[r["repo"]], r["tipo_analisis"], int(r["periodo_num"]),
                                             r["fecha_inicio"], r["fecha_fin"], r["etiqueta"],
                                             json.loads(r["parametros"]) if r["parametros"] else {})
            base.upsert_resultado(periodo_id, r["metrica_id"], r["contribuyente_login"] or None,
                                  float(r["value"]) if r["value"] != "" else None,
                                  json.loads(r["value_extra"]) if r["value_extra"] else None)
            n += 1
    base.commit()
    base.close()
    print(f"{n} resultados importados en {dbname} desde {archivo}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="accion", required=True)
    c = sub.add_parser("crear", help="crea la base nueva como copia sin resultados de next.js")
    c.add_argument("--origen", default=ORIGEN)
    c.add_argument("--destino", default=DESTINO)
    e = sub.add_parser("exportar", help="exporta períodos y resultados de algunas métricas")
    e.add_argument("--metricas", required=True, metavar="k1,k2")
    e.add_argument("--salida", required=True, type=Path)
    e.add_argument("--base", default=DESTINO)
    i = sub.add_parser("importar", help="importa un archivo exportado")
    i.add_argument("archivo", type=Path)
    i.add_argument("--base", default=DESTINO)
    args = ap.parse_args()
    if args.accion == "crear":
        crear(args.origen, args.destino)
    elif args.accion == "exportar":
        exportar(args.base, [m.strip() for m in args.metricas.split(",") if m.strip()], args.salida)
    else:
        importar(args.base, args.archivo)


if __name__ == "__main__":
    main()
