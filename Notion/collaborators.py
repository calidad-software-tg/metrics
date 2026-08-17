import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric

# ATENCIÓN — MÉTRICA SIN CONSIGNA ASIGNADA TODAVÍA:
# Proviene del Notion "Número de Colaboradores, Número de Líneas de Código
# y Número de Branches".
#
# SUSTITUCIÓN DE FUENTE (documentada, mismo criterio que ANMCC/CPU Usage):
# el script original de Notion usa el campo GraphQL `collaborators`, que
# devuelve las cuentas con acceso de escritura/admin al repo. Ese campo
# requiere un token con permisos de administración sobre el repositorio
# (push/admin), algo que no está disponible al analizar repos OSS de
# terceros con un token de solo lectura — motivo por el cual no se usa acá.
#
# En su lugar se usa el endpoint REST `/repos/{owner}/{repo}/contributors`,
# que cuenta cuentas distintas con al menos un commit en el repo (no
# requiere permisos especiales). Es la aproximación estándar para "cantidad
# de colaboradores" en análisis de repos OSS públicos, aunque conceptualmente
# mide "contribuyentes por actividad" en vez de "cuentas con acceso
# administrativo".


class NumberOfCollaborators(GitHubMetric):
    """
    Número de Colaboradores del repositorio.

    Cuenta cuentas distintas con al menos un commit registrado (proxy de
    "colaboradores" vía /contributors, ver nota de sustitución arriba).

    Por persona: contribuciones (commits) de cada colaborador, tal como las
    devuelve /contributors. Es el mismo dato crudo que expone
    commits_per_author.py; se mantiene acá también porque la pregunta que
    responde es distinta ("cuánto contribuyó cada colaborador conocido")
    en vez de "cuántos commits tiene el repo en total".
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.contributors: list[dict] = []  # [{login, contributions}]

    def fetch(self, **kwargs):
        print("Obteniendo colaboradores (contributors)...")
        contributors, page = [], 1
        while True:
            data = self._rest(
                f"/repos/{self.org}/{self.repo}/contributors",
                {"per_page": 100, "page": page, "anon": "1"},
            )
            if not data:
                break
            for c in data:
                contributors.append({
                    "login": c.get("login") or c.get("name") or "desconocido",
                    "contributions": c.get("contributions", 0),
                })
            print(f"  ...{len(contributors)} colaboradores acumulados", end="\r")
            if len(data) < 100:
                break
            page += 1
        print()
        self.contributors = contributors

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> int:
        return len(self.contributors)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        resultado = {c["login"]: c["contributions"] for c in self.contributors}
        return dict(sorted(resultado.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "producto", **kwargs):
        self.fetch()
        if por == "persona":
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"\n{'Colaborador':<30} Commits")
            print("-" * 40)
            for login, contribuciones in resultado.items():
                print(f"{login:<30} {contribuciones}")
        else:
            total = self.por_producto(fecha_inicio, fecha_fin)
            print(f"Número de Colaboradores: {total}")
