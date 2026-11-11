import sys
import requests
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

# ATENCIÓN — MÉTRICA SIN CONSIGNA ASIGNADA TODAVÍA:
# Proviene del Notion "Continuous Integration" (presencia de configuración
# de CI: Travis, GitLab CI, CircleCI, GitHub Actions, Jenkins).
#
# BUG CORREGIDO respecto al script original: el script de Notion solo lista
# el contenido de la raíz del repo y compara `item['name'] in identifiers`,
# donde uno de los identifiers es el string literal '.github/workflows/'.
# Pero `item['name']` de un elemento en la raíz nunca es una ruta compuesta
# (para la carpeta .github, el name es '.github', no '.github/workflows/'),
# así que esa comparación NUNCA matchea — el script original jamás detecta
# GitHub Actions, que es el sistema de CI más común en repos de GitHub hoy.
#
# Acá se verifica cada identificador por su ruta real: se pide directamente
# el contenido de cada path candidato (`.travis.yml`, `.gitlab-ci.yml`,
# `.circleci/config.yml`, `Jenkinsfile`, y el directorio `.github/workflows`
# comprobando que tenga al menos un archivo adentro).
#
# Nota: no se puede reusar `self._rest()` de GitHubMetric para estos chequeos
# porque esa función hace sys.exit(1) ante cualquier respuesta no-200, y acá
# un 404 es un resultado válido y esperado (el archivo/carpeta simplemente
# no existe) — no un error de la API.
#
# fetch() resuelve el commit vigente a fecha_fin (self._resolve_ref) y lo
# usa como `ref` en /contents, así que "¿hay CI configurada?" refleja el
# estado del repo a esa fecha, no el HEAD actual. _fetch_last_author usa
# `until=fecha_fin` por el mismo motivo.

_CI_FILE_IDENTIFIERS = {
    "Travis CI": ".travis.yml",
    "GitLab CI": ".gitlab-ci.yml",
    "CircleCI": ".circleci/config.yml",
    "Jenkins": "Jenkinsfile",
}
_CI_WORKFLOWS_DIR = ".github/workflows"


class ContinuousIntegrationPresence(GitHubMetric):
    """
    Presencia de configuración de Integración Continua (CI).

    Verifica si el repositorio contiene archivos/directorios de
    configuración de CI conocidos (Travis, GitLab CI, CircleCI, GitHub
    Actions, Jenkins).

    Por producto: booleano (¿hay CI configurada?) + detalle de qué sistemas
    se encontraron. Por persona: quién introdujo (último autor del archivo,
    mismo heurístico que loc.py/dloc.py) cada configuración de CI
    encontrada — si no se encontró ninguna, el resultado queda vacío.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.encontrados: list[str] = []
        self.encontrados_detalle: list[dict] = []  # [{sistema, path}]

    def _get_status(self, path: str, ref: str) -> int:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        resp = requests.get(
            f"https://api.github.com/repos/{self.org}/{self.repo}/contents/{path}",
            headers=headers,
            params={"ref": ref},
        )
        return resp.status_code, resp

    def _fetch_last_author(self, path: str, fecha_fin: datetime) -> str:
        commits = self._rest(
            f"/repos/{self.org}/{self.repo}/commits",
            {"path": path, "per_page": 1, "until": fecha_fin.isoformat()},
        )
        if not commits:
            return "desconocido"
        c = commits[0]
        return (
            (c.get("author") or {}).get("login")
            or (c.get("commit", {}).get("author") or {}).get("name")
            or "desconocido"
        )

    def fetch(self, fecha_fin: datetime, **kwargs):
        ref = self._resolve_ref(fecha_fin)
        encontrados = []
        detalle = []

        for sistema, path in _CI_FILE_IDENTIFIERS.items():
            status, _ = self._get_status(path, ref)
            if status == 200:
                encontrados.append(sistema)
                detalle.append({"sistema": sistema, "path": path})
            elif status not in (404,):
                print(f"  Aviso: {path} devolvió {status}, se asume ausente", file=sys.stderr)

        status, resp = self._get_status(_CI_WORKFLOWS_DIR, ref)
        if status == 200:
            contenido = resp.json()
            if isinstance(contenido, list) and len(contenido) > 0:
                encontrados.append("GitHub Actions")
                # Se toma el primer archivo de workflow como referencia para
                # resolver autor; un repo puede tener varios .yml en esa carpeta.
                detalle.append({"sistema": "GitHub Actions", "path": contenido[0]["path"]})
        elif status not in (404,):
            print(f"  Aviso: {_CI_WORKFLOWS_DIR} devolvió {status}, se asume ausente", file=sys.stderr)

        self.encontrados = encontrados
        self.encontrados_detalle = detalle

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> bool:
        return len(self.encontrados) > 0

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, list[str]]:
        resultado: dict[str, list[str]] = {}
        for item in self.encontrados_detalle:
            login = self._fetch_last_author(item["path"], fecha_fin)
            resultado.setdefault(login, []).append(item["sistema"])
        return resultado

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        print(f"Verificando configuración de CI en {self.org}/{self.repo}...")
        self.fetch(fecha_fin)

        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            if not resultado:
                print("No se encontró configuración de CI: no hay autores que atribuir.")
                return
            print(f"\n{'Colaborador':<30} Sistema(s) de CI introducidos")
            print("-" * 60)
            for login, sistemas in resultado.items():
                print(f"{login:<30} {', '.join(sistemas)}")
        else:
            presente = self.por_producto(fecha_inicio, fecha_fin)
            if presente:
                print(f"CI detectada: {', '.join(self.encontrados)}")
            else:
                print("No se encontró configuración de CI en el repositorio.")
