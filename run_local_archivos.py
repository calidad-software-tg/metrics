"""
Variante LOCAL (sin API de GitHub) de las métricas de archivos y blame, para
los períodos ADAPTATIVOS (66 bloques), no los de versión de Inés.

Mismo enfoque que su run_versiones_local.py: clona el repo una sola vez y
usa `git ls-tree` / `git cat-file --batch` / `git log --numstat` / `git
blame` en vez de pedirle cada archivo/commit uno por uno a la API. La
FÓRMULA de cada métrica es la misma clase de siempre (loc.py, dloc.py,
cd.py, developer_ownership.py) -- lo que cambia es de dónde sale el dato
crudo.

Cubre: loc_notion, dloc, cd, developer_ownership_notion.
NO cubre cdiv/fexp/le/rexp -- esas ya están 100% completas vía API con
atribución por login de GitHub; recalcularlas acá las dejaría con nombre de
git en vez de login, mezclando dos convenciones para el mismo período.

Uso:
    python run_local_archivos.py tldr-pages/tldr
    python run_local_archivos.py tldr-pages/tldr --solo dloc,loc_notion
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_root = Path(__file__).resolve().parent
for _d in ["15", "16", "Notion"]:
    sys.path.insert(0, str(_root / _d))

from loc import _CODE_EXTENSIONS as LOC_EXT, _is_excluded, _count_lines as loc_count
from dloc import _DOC_EXTENSIONS, _count_lines as dloc_count
from cd import _COMMENT_PATTERNS, _CODE_EXTENSIONS as CD_EXT, _count_lines as cd_count
from developer_ownership import _CODE_EXTENSIONS as OWN_EXT, _is_excluded as own_excluded

import psycopg2

# --- .env ----------------------------------------------------------------
for _envf in [_root / ".env", _root / "db" / ".env"]:
    if _envf.exists():
        for line in _envf.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                __import__("os").environ.setdefault(k.strip(), v.strip())

import os
DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_USER = os.environ.get("POSTGRES_USER", "metricas")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "metricas")
DB_NAME = os.environ.get("POSTGRES_DB", "resultados_metricas")

CD_SKIP = frozenset({".md"})
CLONES_DIR = _root / ".clones"

METRICA_IDS = {
    "loc_notion": "lines_of_code",
    "dloc": "dloc",
    "cd": "cd",
    "developer_ownership": "developer_ownership",
}
ARCHIVOS = {"loc_notion", "dloc", "cd"}
BLAME = {"developer_ownership"}
TODAS = ARCHIVOS | BLAME


# --------------------------------------------------------------------------- git

def _git(dir_repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(dir_repo), *args], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"git {' '.join(args)} falló: {r.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return r.stdout


def clonar_o_actualizar(org: str, repo: str) -> Path:
    CLONES_DIR.mkdir(exist_ok=True)
    dest = CLONES_DIR / repo
    if (dest / ".git").exists():
        print(f"Actualizando clon local {dest} ...")
        _git(dest, "fetch", "--quiet", "--tags", "--force", "origin")
    else:
        print(f"Clonando {org}/{repo} en {dest} (puede tardar un rato la primera vez)...")
        r = subprocess.run(
            ["git", "clone", "--quiet", f"https://github.com/{org}/{repo}.git", str(dest)],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(f"git clone falló: {r.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
    return dest


def resolver_ref_local(dir_repo: Path, rama: str, fecha_fin: datetime) -> str:
    """SHA del último commit de `rama` con fecha <= fecha_fin. Equivalente
    local de GitHubMetric._resolve_ref(), sin pedirle nada a la API."""
    out = _git(dir_repo, "log", rama, "-1", f"--before={fecha_fin.isoformat()}", "--format=%H")
    sha = out.strip()
    return sha or rama  # si no hay ningún commit antes (raro), cae al HEAD de la rama


def archivos_en_ref(dir_repo: Path, ref: str) -> list[tuple[str, str]]:
    out = _git(dir_repo, "ls-tree", "-r", ref)
    res = []
    for linea in out.splitlines():
        partes = linea.split("\t", 1)
        if len(partes) != 2:
            continue
        meta, path = partes
        campos = meta.split()
        if len(campos) >= 3 and campos[1] == "blob":
            res.append((campos[2], path))
    return res


def contenidos(dir_repo: Path, shas: list[str]) -> dict[str, str]:
    if not shas:
        return {}
    proc = subprocess.run(
        ["git", "-C", str(dir_repo), "cat-file", "--batch"],
        input=("\n".join(shas) + "\n").encode(),
        capture_output=True,
    )
    if proc.returncode != 0:
        print(f"cat-file --batch falló: {proc.stderr.decode(errors='replace')}", file=sys.stderr)
        sys.exit(1)
    data = proc.stdout
    res: dict[str, str] = {}
    i, n = 0, len(data)
    while i < n:
        fin_linea = data.find(b"\n", i)
        if fin_linea == -1:
            break
        cab = data[i:fin_linea].decode(errors="replace").split()
        i = fin_linea + 1
        if len(cab) < 3 or cab[1] != "blob":
            continue
        sha, _tipo, tam = cab[0], cab[1], int(cab[2])
        res[sha] = data[i:i + tam].decode("utf-8", errors="replace")
        i += tam + 1
    return res


def ultimo_autor_por_archivo(dir_repo: Path, ref: str) -> dict[str, str]:
    out = _git(dir_repo, "log", ref, "--no-merges", "--pretty=format:\x01%an", "--name-only")
    autor_actual = "desconocido"
    ultimo: dict[str, str] = {}
    for linea in out.splitlines():
        if linea.startswith("\x01"):
            autor_actual = linea[1:].strip() or "desconocido"
        elif linea.strip():
            ultimo.setdefault(linea, autor_actual)
    return ultimo


def blame_propiedad(dir_repo: Path, ref: str) -> tuple[dict[str, int], int]:
    propiedad: dict[str, int] = {}
    total = 0
    for _sha, path in archivos_en_ref(dir_repo, ref):
        ext = Path(path).suffix.lower()
        if ext not in OWN_EXT or own_excluded(path):
            continue
        r = subprocess.run(
            ["git", "-C", str(dir_repo), "blame", "--line-porcelain", ref, "--", path],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            continue
        for l in r.stdout.splitlines():
            if l.startswith("author "):
                a = l[len("author "):].strip() or "desconocido"
                propiedad[a] = propiedad.get(a, 0) + 1
                total += 1
    return propiedad, total


def procesar_ref(dir_repo: Path, ref: str, quiere: set[str]) -> dict[str, dict]:
    blobs = archivos_en_ref(dir_repo, ref)
    quiere_loc, quiere_dloc, quiere_cd = "loc_notion" in quiere, "dloc" in quiere, "cd" in quiere
    sel_loc, sel_dloc, sel_cd = [], [], []
    for sha, path in blobs:
        ext = Path(path).suffix.lower()
        if quiere_loc and ext in LOC_EXT and not _is_excluded(path):
            sel_loc.append((sha, path))
        if quiere_dloc and ext in _DOC_EXTENSIONS:
            sel_dloc.append((sha, path))
        if quiere_cd and ext in CD_EXT and ext not in CD_SKIP:
            sel_cd.append((sha, path))

    shas_unicos = {s for s, _ in (sel_loc + sel_dloc + sel_cd)}
    cont = contenidos(dir_repo, list(shas_unicos))

    res: dict[str, dict] = {}
    if quiere_loc:
        por_archivo = {p: loc_count(cont.get(s, "")) for s, p in sel_loc}
        res["loc_notion"] = {"producto": sum(por_archivo.values()), "por_archivo": por_archivo}
    if quiere_dloc:
        por_archivo = {p: dloc_count(cont.get(s, "")) for s, p in sel_dloc}
        res["dloc"] = {"producto": sum(por_archivo.values()), "por_archivo": por_archivo}
    if quiere_cd:
        por_archivo, tot_c, tot_l = {}, 0, 0
        for s, p in sel_cd:
            c, l = cd_count(cont.get(s, ""), Path(p).suffix.lower())
            por_archivo[p] = (c, l)
            tot_c += c
            tot_l += l
        res["cd"] = {"producto": round(tot_c / tot_l, 4) if tot_l else 0.0, "por_archivo": por_archivo}
    return res


def persona_loc_dloc(por_archivo: dict[str, int], autores: dict[str, str]) -> dict[str, int]:
    acc: dict[str, int] = {}
    for path, lineas in por_archivo.items():
        a = autores.get(path, "desconocido")
        acc[a] = acc.get(a, 0) + lineas
    return dict(sorted(acc.items(), key=lambda x: x[1], reverse=True))


def persona_cd(por_archivo: dict[str, tuple], autores: dict[str, str]) -> dict[str, float]:
    acc: dict[str, list[int]] = {}
    for path, (c, l) in por_archivo.items():
        a = autores.get(path, "desconocido")
        acc.setdefault(a, [0, 0])
        acc[a][0] += c
        acc[a][1] += l
    return dict(sorted(
        {a: (round(c / l, 4) if l else 0.0) for a, (c, l) in acc.items()}.items(),
        key=lambda x: x[1], reverse=True,
    ))


# --------------------------------------------------------------------------- DB

def _conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD, dbname=DB_NAME)


def _upsert(cur, periodo_id, metrica_id, value, contribuyente_login=None):
    if isinstance(value, dict):
        cur.execute(
            "INSERT INTO resultado (periodo_id, metrica_id, contribuyente_login, value, value_extra) "
            "VALUES (%s,%s,%s,NULL,%s)",
            (periodo_id, metrica_id, contribuyente_login, __import__("json").dumps(value, default=str)),
        )
    else:
        cur.execute(
            "INSERT INTO resultado (periodo_id, metrica_id, contribuyente_login, value) VALUES (%s,%s,%s,%s)",
            (periodo_id, metrica_id, contribuyente_login, float(value) if value is not None else None),
        )


def main():
    ap = argparse.ArgumentParser(description="Métricas de archivos/blame por bloque adaptativo, desde clon local")
    ap.add_argument("repo", help="org/repo, ej: tldr-pages/tldr")
    ap.add_argument("--tipo-analisis", default="adaptativo")
    ap.add_argument("--solo", metavar="k1,k2", help=f"subconjunto de {sorted(TODAS)}")
    args = ap.parse_args()

    org, repo = args.repo.split("/", 1)
    quiere = set(TODAS) if not args.solo else {s.strip() for s in args.solo.split(",")}
    desconocidas = quiere - TODAS
    if desconocidas:
        print(f"--solo: claves no soportadas: {sorted(desconocidas)}", file=sys.stderr)
        sys.exit(1)

    dir_repo = clonar_o_actualizar(org, repo)
    rama = "origin/HEAD"

    con = _conn()
    cur = con.cursor()
    cur.execute("SELECT repo_id FROM repos WHERE full_name = %s", (f"{org}/{repo}",))
    row = cur.fetchone()
    if row is None:
        print(f"{org}/{repo} no está en repos.", file=sys.stderr)
        sys.exit(1)
    repo_id = row[0]

    cur.execute(
        "SELECT periodo_id, periodo_num, fecha_inicio, fecha_fin FROM periodo "
        "WHERE repo_id=%s AND tipo_analisis=%s ORDER BY periodo_num",
        (repo_id, args.tipo_analisis),
    )
    periodos = cur.fetchall()
    print(f"Repo: {org}/{repo}  |  {len(periodos)} períodos '{args.tipo_analisis}'  |  métricas: {sorted(quiere)}\n")

    metrica_ids = [METRICA_IDS[k] for k in quiere]
    periodo_ids = [p[0] for p in periodos]
    cur.execute("DELETE FROM resultado WHERE periodo_id = ANY(%s) AND metrica_id = ANY(%s)",
                (periodo_ids, metrica_ids))
    con.commit()

    q_arch = quiere & ARCHIVOS
    q_blame = quiere & BLAME

    for periodo_id, periodo_num, f_ini, f_fin in periodos:
        ref = resolver_ref_local(dir_repo, rama, f_fin)
        print(f"[{periodo_num:>2}/{len(periodos)}] {f_ini.date()} -> {f_fin.date()}  (ref={ref[:8]})")

        if q_arch:
            datos = procesar_ref(dir_repo, ref, q_arch)
            autores = ultimo_autor_por_archivo(dir_repo, ref)
            for k in sorted(q_arch):
                d = datos.get(k)
                if not d:
                    continue
                metrica_id = METRICA_IDS[k]
                prod = d["producto"]
                pers = (persona_cd if k == "cd" else persona_loc_dloc)(d["por_archivo"], autores)
                print(f"     {k:<12} producto={prod}  personas={len(pers)}")
                _upsert(cur, periodo_id, metrica_id, prod)
                for login, v in pers.items():
                    _upsert(cur, periodo_id, metrica_id, v, contribuyente_login=login)
                con.commit()

        if q_blame:
            propiedad, total = blame_propiedad(dir_repo, ref)
            metrica_id = METRICA_IDS["developer_ownership"]
            if total > 0:
                max_lineas = max(propiedad.values())
                prod = {
                    "total_lineas": total,
                    "autores_distintos": len(propiedad),
                    "max_porcentaje": round((max_lineas / total) * 100, 2),
                }
                pers = {
                    login: {"lineas": lineas, "porcentaje": round((lineas / total) * 100, 2)}
                    for login, lineas in propiedad.items()
                }
            else:
                prod = {"total_lineas": 0, "autores_distintos": 0, "max_porcentaje": 0.0}
                pers = {}
            print(f"     developer_ownership  lineas={total}  personas={len(pers)}")
            _upsert(cur, periodo_id, metrica_id, prod)
            for login, v in pers.items():
                _upsert(cur, periodo_id, metrica_id, v, contribuyente_login=login)
            con.commit()

    cur.close()
    con.close()
    print("\nListo.")


if __name__ == "__main__":
    main()
