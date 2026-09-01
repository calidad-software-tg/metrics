"""
Versión LOCAL de las métricas de archivos y de commits, SIN cap.

En vez de pedir árbol/blobs/commits/blame a la API de GitHub (lento, rate
limit, obliga a capar), lee todo de un clon local. La fórmula de cada métrica
es la MISMA: se instancia la clase original y se le carga el estado interno
desde git, después se llama a su propio por_producto()/por_persona().

Cubre:
  - archivos : loc_notion, dloc, cd            (git ls-tree + cat-file --batch)
  - commits  : cdiv, fexp, le, rexp            (git log --numstat)
  - blame    : developer_ownership_notion      (git blame --line-porcelain)

Qué cambia respecto a la corrida por API:
  - se van los caps (--max-files / --max-commits) y también el tope propio de
    GitHub de 300 archivos por commit -> conteos completos, no parciales.
  - la atribución por persona pasa a ser el NOMBRE de git del autor en vez del
    login de GitHub (git local no tiene el login). Mismo criterio que ya se
    aplicó a loc_notion/dloc/cd.
  - las ventanas (periodo_num + fechas) se toman de la API, así las filas de
    `periodo` coinciden y el guardado es UPSERT (borra lo capado y reescribe).

Uso:
    python run_versiones_local.py                    # todas (archivos + commits + blame)
    python run_versiones_local.py --solo dloc,cdiv
    python run_versiones_local.py --no-guardar
"""

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_root = Path(__file__).resolve().parent
for _d in ["15", "16", "Notion"]:
    sys.path.insert(0, str(_root / _d))

# Helpers de conteo de las propias métricas de archivos.
from loc import _CODE_EXTENSIONS as LOC_EXT, _is_excluded, _count_lines as loc_count
from dloc import _DOC_EXTENSIONS, _count_lines as dloc_count
from cd import _COMMENT_PATTERNS, _CODE_EXTENSIONS as CD_EXT, _count_lines as cd_count

# Clases originales: se instancian y se les carga el estado desde git, después
# se llama a su propio por_producto()/por_persona() -> fórmula idéntica.
from cdiv import ContributionDiversity
from fexp import FileExperience
from le import LearningEase
from rexp import RecentExperience
from developer_ownership import DeveloperOwnership, _CODE_EXTENSIONS as OWN_EXT, _is_excluded as own_excluded

from run_versiones import (
    Base, ventanas_por_version, TIPO_ANALISIS, NOMBRES_METRICA,
    _fmt, os,  # os ya trae el .env cargado por run_versiones
)

CD_SKIP = frozenset({".md"})          # igual que el default de cd.fetch
CLONES_DIR = _root / ".clones"        # donde viven los clones locales

ARCHIVOS = {"loc_notion", "dloc", "cd"}
COMMITS = {"cdiv", "fexp", "le", "rexp"}
BLAME = {"developer_ownership_notion"}
TODAS = ARCHIVOS | COMMITS | BLAME


# --------------------------------------------------------------------------- git

def _git(dir_repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(dir_repo), *args],
                       capture_output=True, text=True)
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
        print(f"Clonando {org}/{repo} en {dest} ...")
        r = subprocess.run(
            ["git", "clone", "--quiet", f"https://github.com/{org}/{repo}.git", str(dest)],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            print(f"git clone falló: {r.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
    return dest


def archivos_en_ref(dir_repo: Path, ref: str) -> list[tuple[str, str]]:
    """[(sha_blob, path)] de todos los blobs en ese ref."""
    out = _git(dir_repo, "ls-tree", "-r", ref)
    res = []
    for linea in out.splitlines():
        if "\tblob\t" in linea or " blob " in linea:
            pass
        partes = linea.split("\t", 1)
        if len(partes) != 2:
            continue
        meta, path = partes
        campos = meta.split()
        if len(campos) >= 3 and campos[1] == "blob":
            res.append((campos[2], path))
    return res


def contenidos(dir_repo: Path, shas: list[str]) -> dict[str, str]:
    """{sha: texto} para muchos blobs de una, con `git cat-file --batch`."""
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
    i = 0
    n = len(data)
    while i < n:
        fin_linea = data.find(b"\n", i)
        if fin_linea == -1:
            break
        cab = data[i:fin_linea].decode(errors="replace").split()
        i = fin_linea + 1
        if len(cab) < 3 or cab[1] != "blob":
            # "<sha> missing" u otro: saltar
            continue
        sha, _tipo, tam = cab[0], cab[1], int(cab[2])
        res[sha] = data[i:i + tam].decode("utf-8", errors="replace")
        i += tam + 1  # +1 por el \n final
    return res


def ultimo_autor_por_archivo(dir_repo: Path, ref: str) -> dict[str, str]:
    """path -> autor del commit más reciente (<=ref) que tocó ese path.
    Un solo `git log` en vez de una consulta por archivo."""
    out = _git(dir_repo, "log", ref, "--no-merges", "--pretty=format:\x01%an", "--name-only")
    autor_actual = "desconocido"
    ultimo: dict[str, str] = {}
    for linea in out.splitlines():
        if linea.startswith("\x01"):
            autor_actual = linea[1:].strip() or "desconocido"
        elif linea.strip():
            ultimo.setdefault(linea, autor_actual)  # primera vez = más reciente
    return ultimo


def _path_de_numstat(campo: str) -> str:
    """Normaliza la ruta de una línea --numstat, incluyendo renames.
    'a\t{old => new}\tb' o 'old => new' -> new."""
    if "=>" not in campo:
        return campo
    # forma con llaves: pre{old => new}post
    if "{" in campo and "}" in campo:
        pre, resto = campo.split("{", 1)
        cambio, post = resto.split("}", 1)
        _old, new = [x.strip() for x in cambio.split("=>")]
        return f"{pre}{new}{post}".replace("//", "/")
    # forma simple: old => new
    return campo.split("=>")[-1].strip()


def commits_en_ventana(dir_repo: Path, ref: str, inicio: datetime, fin: datetime) -> list[dict]:
    """[{author, timestamp, files:[path]}] de los commits (no-merge) del branch
    `ref` cuya fecha de commit cae en [inicio, fin). Equivale a lo que traía
    /repos/.../commits?since&until, pero con la lista de archivos COMPLETA
    (sin el tope de 300 de la API) y sin --max-commits."""
    out = _git(
        dir_repo, "log", ref, "--no-merges", "--numstat",
        f"--since={inicio.isoformat()}", f"--until={fin.isoformat()}",
        "--date=iso-strict", "--pretty=format:\x01%an\x01%aI",
    )
    commits: list[dict] = []
    actual = None
    for linea in out.splitlines():
        if linea.startswith("\x01"):
            if actual:
                commits.append(actual)
            _, autor, fecha_iso = linea.split("\x01")
            actual = {"author": autor.strip() or "desconocido",
                      "timestamp": datetime.fromisoformat(fecha_iso),
                      "files": []}
        elif linea.strip() and actual is not None:
            partes = linea.split("\t")
            if len(partes) == 3:
                actual["files"].append(_path_de_numstat(partes[2]))
    if actual:
        commits.append(actual)
    return commits


def blame_propiedad(dir_repo: Path, ref: str) -> tuple[dict[str, int], int]:
    """{autor: lineas}, total. Mismo criterio de archivos que developer_ownership
    (código, sin carpetas de deps), pero sin cap y con git blame local."""
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


# ----------------------------------------------------------------- por métrica

def calc_loc(files: dict[str, int]) -> tuple[int, dict]:
    total = sum(files.values())
    return total, files


def procesar_tag(dir_repo: Path, ref: str, quiere: set[str]) -> dict[str, dict]:
    """Devuelve {metrica: {"producto": val, "por_archivo": {path: dato}}} para el ref."""
    blobs = archivos_en_ref(dir_repo, ref)

    quiere_loc = "loc_notion" in quiere
    quiere_dloc = "dloc" in quiere
    quiere_cd = "cd" in quiere

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
    print(f"    archivos: loc={len(sel_loc)} dloc={len(sel_dloc)} cd={len(sel_cd)} "
          f"(blobs a leer: {len(shas_unicos)})")
    cont = contenidos(dir_repo, list(shas_unicos)) if shas_unicos else {}

    res: dict[str, dict] = {}

    if quiere_loc:
        por_archivo = {p: loc_count(cont.get(s, "")) for s, p in sel_loc}
        res["loc_notion"] = {"producto": sum(por_archivo.values()), "por_archivo": por_archivo}

    if quiere_dloc:
        por_archivo = {p: dloc_count(cont.get(s, "")) for s, p in sel_dloc}
        res["dloc"] = {"producto": sum(por_archivo.values()), "por_archivo": por_archivo}

    if quiere_cd:
        por_archivo = {}
        tot_c = tot_l = 0
        for s, p in sel_cd:
            c, l = cd_count(cont.get(s, ""), Path(p).suffix.lower())
            por_archivo[p] = (c, l)
            tot_c += c
            tot_l += l
        prod = round(tot_c / tot_l, 4) if tot_l else 0.0
        res["cd"] = {"producto": prod, "por_archivo": por_archivo}

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


def _eval_commit_metric(k: str, commits: list[dict], v: dict, token, org, repo):
    """Instancia la clase original, le carga el estado desde git y llama a su
    propio por_producto()/por_persona(). Devuelve (producto|None, persona)."""
    fi, ff = v["inicio"], v["fin"]
    base_commits = [{"author": c["author"], "files": c["files"],
                     "timestamp": c["timestamp"]} for c in commits]

    if k == "cdiv":
        m = ContributionDiversity(token, org, repo)
        m.commits = base_commits
        return None, m.por_persona(fi, ff)

    if k == "fexp":
        m = FileExperience(token, org, repo)
        m.commits = base_commits
        return None, m.por_persona(fi, ff)

    if k == "rexp":
        m = RecentExperience(token, org, repo)
        m.commits = [{"author": c["author"], "date": c["timestamp"]} for c in commits]
        return None, m.por_persona(fi, ff)

    if k == "le":
        m = LearningEase(token, org, repo)
        regs = []
        for c in commits:
            for f in c["files"]:
                comp = f.split("/")[0] if "/" in f else f
                regs.append({"author": c["author"], "component": comp,
                             "timestamp": c["timestamp"]})
        m.registros = regs
        return m.por_producto(fi, ff), m.por_persona(fi, ff)

    raise ValueError(k)


# ------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="métricas de archivos/commits/blame por versión, desde un clon local (sin cap)")
    ap.add_argument("--repo", default="tldr-pages/tldr", metavar="ORG/REPO")
    ap.add_argument("--solo", metavar="k1,k2",
                    help=f"subconjunto de {sorted(TODAS)}")
    ap.add_argument("--no-guardar", dest="guardar", action="store_false", default=True)
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("Falta GITHUB_TOKEN en .env", file=sys.stderr)
        sys.exit(1)
    org, repo = args.repo.split("/", 1)

    quiere = set(TODAS) if not args.solo else {s.strip() for s in args.solo.split(",")}
    desconocidas = quiere - TODAS
    if desconocidas:
        print(f"--solo: claves no soportadas acá: {sorted(desconocidas)}", file=sys.stderr)
        sys.exit(1)

    dir_repo = clonar_o_actualizar(org, repo)
    rama = "origin/HEAD"  # branch por defecto, ya actualizado por el fetch
    ventanas = ventanas_por_version(token, org, repo)  # mismas fechas/periodo_num que run_versiones.py
    print(f"\nRepo    : {org}/{repo} (clon local)")
    print(f"Métricas: {', '.join(sorted(quiere))}")
    print(f"Ventanas: {len(ventanas)} (una por versión, SIN cap)")
    print(f"Guardar : {'sí' if args.guardar else 'no'}\n")

    base = repo_id = None
    if args.guardar:
        base = Base()
        repo_id = base.repo_id(org, repo)
        for k in quiere:
            base.ensure_metrica(k)
            # borrar lo previo: las corridas por API atribuían por login de
            # GitHub y estas por nombre de git -> un UPSERT dejaría filas
            # persona duplicadas con claves distintas.
            base.cur.execute(
                """
                DELETE FROM resultado
                WHERE metrica_id = %s
                  AND periodo_id IN (SELECT periodo_id FROM periodo
                                     WHERE repo_id = %s AND tipo_analisis = %s)
                """,
                (k, repo_id, TIPO_ANALISIS),
            )
        base.commit()

    resumen = {k: {"ok": 0, "err": 0} for k in quiere}

    def guardar(k, v, por, valor):
        if base is None:
            return
        try:
            base.guardar_ventana(repo_id, k, TIPO_ANALISIS, v, por, valor)
            base.commit()
        except Exception as exc:
            base.con.rollback()
            resumen[k]["err"] += 1
            print(f"     ERROR guardando {k}/{por}: {exc}", file=sys.stderr)

    q_arch = quiere & ARCHIVOS
    q_com = quiere & COMMITS
    q_blame = quiere & BLAME

    for v in ventanas:
        tag = v["version"]
        print(f"[{v['n']:>2}] {tag}  ({v['inicio'].date()} -> "
              f"{'ahora' if v['abierta'] else v['fin'].date()})")

        # --- métricas de archivos (estado del repo en el tag) ---
        if q_arch:
            datos = procesar_tag(dir_repo, tag, q_arch)
            autores = ultimo_autor_por_archivo(dir_repo, tag)
            for k in sorted(q_arch):
                d = datos.get(k)
                if not d:
                    continue
                prod = d["producto"]
                pers = (persona_cd if k == "cd" else persona_loc_dloc)(d["por_archivo"], autores)
                print(f"     {k:<12} producto={_fmt(prod)}  personas={len(pers)}")
                guardar(k, v, "producto", prod)
                guardar(k, v, "persona", pers)
                resumen[k]["ok"] += 1

        # --- métricas de commits (commits con fecha en la ventana) ---
        if q_com:
            commits = commits_en_ventana(dir_repo, rama, v["inicio"], v["fin"])
            print(f"     commits en ventana: {len(commits)}")
            for k in sorted(q_com):
                prod, pers = _eval_commit_metric(k, commits, v, token, org, repo)
                extra = f"producto={_fmt(prod)}  " if prod is not None else ""
                print(f"     {k:<12} {extra}personas={len(pers)}")
                if prod is not None:
                    guardar(k, v, "producto", prod)
                guardar(k, v, "persona", pers)
                resumen[k]["ok"] += 1

        # --- blame (developer ownership en el tag) ---
        if q_blame:
            propiedad, total = blame_propiedad(dir_repo, tag)
            m = DeveloperOwnership(token, org, repo)
            m.propiedad, m.total_lineas = propiedad, total
            prod = m.por_producto(v["inicio"], v["fin"])
            pers = m.por_persona(v["inicio"], v["fin"])
            print(f"     developer_ownership  lineas={total}  personas={len(pers)}")
            guardar("developer_ownership_notion", v, "producto", prod)
            guardar("developer_ownership_notion", v, "persona", pers)
            resumen["developer_ownership_notion"]["ok"] += 1

    if base is not None:
        base.close()

    print("\n=== RESUMEN ===")
    for k, r in sorted(resumen.items()):
        print(f"{k:<28} ventanas_ok={r['ok']:>2}  errores={r['err']}")


if __name__ == "__main__":
    main()
