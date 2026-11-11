import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

# Reutiliza el mismo filtro de archivos de código y exclusión de carpetas
# de dependencias/artefactos generados que ya se definió en loc.py (mismo
# criterio: no tiene sentido atribuir "propiedad" sobre vendor/node_modules).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from loc import _CODE_EXTENSIONS, _is_excluded

# ATENCIÓN — MÉTRICA SIN CONSIGNA ASIGNADA TODAVÍA:
# Proviene del Notion "Developer Ownership" (% de código por autor vía
# git blame). NO confundir con Code Density / Comment Density (16/cd.py) ni
# con Documented Lines of Code (16/dloc.py): esas atribuyen un ARCHIVO
# COMPLETO al último autor que lo tocó (heurística barata, un solo commit
# consultado por archivo); Developer Ownership atribuye LÍNEA POR LÍNEA vía
# `blame`, que es más preciso pero mucho más costoso (una consulta GraphQL
# de blame por archivo, sin importar cuántas líneas tenga).
#
# Diferencias respecto al script original:
# 1. Se filtra por extensión de código y se excluyen carpetas de
#    dependencias (mismo criterio que loc.py), en vez de recorrer TODOS los
#    archivos del árbol — el original no filtra nada, lo que en un repo
#    grande dispara cientos/miles de consultas de blame innecesarias sobre
#    binarios, lockfiles, assets, etc.
# 2. Se agrega un tope `max_files` (por defecto 300) porque blame es la
#    consulta más cara de todo el catálogo: una request GraphQL por archivo,
#    sin paginación posible dentro del archivo mismo.

_BLAME_QUERY = """
query($owner: String!, $name: String!, $path: String!, $ref: String!) {
  repository(owner: $owner, name: $name) {
    object(expression: $ref) {
      ... on Commit {
        blame(path: $path) {
          ranges {
            startingLine
            endingLine
            commit {
              author { user { login } name }
            }
          }
        }
      }
    }
  }
}
"""


class DeveloperOwnership(GitHubMetric):
    """
    Developer Ownership — porcentaje de líneas de código atribuibles a cada
    desarrollador, vía `git blame` (último autor que modificó cada línea).

    Es una métrica de distribución por persona (no tiene un valor único de
    producto con sentido propio, más allá de "cuántos autores distintos
    tienen líneas atribuidas" — ver por_producto).
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.propiedad: dict[str, int] = defaultdict(int)
        self.total_lineas: int = 0

    def _listar_archivos(self, ref: str, max_files: int) -> list[str]:
        tree = self._rest(
            f"/repos/{self.org}/{self.repo}/git/trees/{ref}",
            {"recursive": "1"},
        )
        archivos = [
            e["path"] for e in tree.get("tree", [])
            if e["type"] == "blob"
            and Path(e["path"]).suffix.lower() in _CODE_EXTENSIONS
            and not _is_excluded(e["path"])
        ]
        total = len(archivos)
        archivos = archivos[:max_files]
        print(f"Archivos de código encontrados: {total} (analizando {len(archivos)})")
        return archivos

    def fetch(self, fecha_fin: datetime, max_files: int = 300, **kwargs):
        ref = self._resolve_ref(fecha_fin)
        archivos = self._listar_archivos(ref, max_files)
        propiedad: dict[str, int] = defaultdict(int)
        total_lineas = 0

        for i, archivo in enumerate(archivos):
            data = self._graphql(_BLAME_QUERY, {
                "owner": self.org, "name": self.repo, "path": archivo, "ref": ref,
            })
            obj = data["data"]["repository"]["object"]
            rangos = (obj or {}).get("blame", {}).get("ranges", []) if obj else []
            for rango in rangos:
                author_node = (rango.get("commit") or {}).get("author") or {}
                user = author_node.get("user") or {}
                login = user.get("login") or author_node.get("name")
                if not login:
                    continue
                lineas = rango["endingLine"] - rango["startingLine"] + 1
                propiedad[login] += lineas
                total_lineas += lineas
            print(f"  ...{i + 1}/{len(archivos)} archivos analizados (blame)", end="\r")

        print()
        self.propiedad = propiedad
        self.total_lineas = total_lineas

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict:
        """
        Resumen agregado de la distribución (no un valor único con
        significado por sí solo, pero sirve como snapshot de producto):
        total de líneas analizadas, cantidad de autores distintos con
        líneas atribuidas, y el porcentaje del autor con más propiedad
        (índice de concentración simple).
        """
        if self.total_lineas == 0:
            return {"total_lineas": 0, "autores_distintos": 0, "max_porcentaje": 0.0}
        max_lineas = max(self.propiedad.values())
        return {
            "total_lineas": self.total_lineas,
            "autores_distintos": len(self.propiedad),
            "max_porcentaje": round((max_lineas / self.total_lineas) * 100, 2),
        }

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, dict]:
        if self.total_lineas == 0:
            return {}
        resultado = {
            login: {
                "lineas": lineas,
                "porcentaje": round((lineas / self.total_lineas) * 100, 2),
            }
            for login, lineas in self.propiedad.items()
        }
        return dict(sorted(resultado.items(), key=lambda x: x[1]["porcentaje"], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona",
            max_files: int = 300, **kwargs):
        print(f"Calculando Developer Ownership de {self.org}/{self.repo}...")
        self.fetch(fecha_fin, max_files=max_files)

        if por == "producto":
            r = self.por_producto(fecha_inicio, fecha_fin)
            print(f"Total de líneas analizadas: {r['total_lineas']}")
            print(f"Autores distintos con líneas atribuidas: {r['autores_distintos']}")
            print(f"Concentración máxima (top autor): {r['max_porcentaje']}%")
        else:
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            if not resultado:
                print("No se encontraron líneas atribuibles (repo vacío o sin archivos de código).")
                return
            print(f"\nTotal de líneas analizadas: {self.total_lineas}\n")
            print(f"{'Colaborador':<30} {'Líneas':>10} {'%':>8}")
            print("-" * 50)
            for login, d in resultado.items():
                print(f"{login:<30} {d['lineas']:>10} {d['porcentaje']:>7.2f}%")
