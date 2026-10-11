import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric


# Carpetas que por convención de monorepo agrupan sub-proyectos independientes
# (JS/TS: packages/, apps/; Rust: crates/; VS Code: extensions/; etc.). Cuando
# aparecen en los primeros dos niveles de la ruta, el componente es el
# sub-proyecto (packages/next, turbopack/crates/turbopack-core) y no la carpeta
# contenedora entera -- si no, en next.js 20 paquetes contaban como uno solo.
_CONTENEDORES = {"packages", "crates", "apps", "libs", "modules",
                 "plugins", "extensions", "services", "projects"}


def componente_de(path: str) -> str:
    """Componente de un archivo: el primer segmento de la ruta, salvo que ese
    segmento (o el segundo) sea un contenedor de monorepo con un sub-directorio
    adentro, en cuyo caso se baja hasta ese sub-directorio. Regla genérica, sin
    nombres propios de ningún repo: en repos sin contenedores (tldr) da lo
    mismo que la definición original."""
    partes = path.split("/")
    if len(partes) == 1:
        return path  # archivo en la raíz
    for i in (0, 1):
        # partes[i + 1] tiene que ser un directorio (quedan más segmentos después)
        if partes[i] in _CONTENEDORES and len(partes) > i + 2:
            return "/".join(partes[: i + 2])
    return partes[0]


def calcular_learning_easy(commits_componente: list[dict],
                           primera_contribucion: datetime | None = None) -> int:
    """
    Calcula el 'Learning Easy' (Aprendizaje Fácil).
    Define la capacidad de aprendizaje como el tiempo requerido para dominar un componente.
    Se mide como el intervalo (en días) entre la primera y la última contribución
    de un autor sobre dicho componente.

    commits_componente: contribuciones del autor al componente DENTRO de la ventana
        (la última define hasta dónde se mide).
    primera_contribucion: primera contribución del autor a ese componente en toda la
        historia del repo. Sin ella el lapso quedaría acotado por la duración de la
        ventana (en next.js, mediana 13,6 días -> 75% de los valores daban 0).
        None = se usa la primera contribución dentro de la ventana.
    """
    if not commits_componente:
        return 0

    timestamps = [c["timestamp"] for c in commits_componente]
    inicio = min(timestamps)
    if primera_contribucion is not None:
        inicio = min(inicio, primera_contribucion)
    return (max(timestamps) - inicio).days


class LearningEase(GitHubMetric):
    """
    Learning Easy (LE).
    Tiempo (en días) que le toma a un desarrollador dominar un componente del
    repositorio, aproximado como el lapso entre su primera contribución a dicho
    componente (en toda la historia) y su última contribución dentro de la
    ventana. El componente sale de componente_de().

    `primera_contribucion` ({(autor, componente): datetime}) la carga el runner
    local (run_versiones_local.py) desde el git log completo. fetch() por API
    solo ve los commits de la ventana y no la llena: sin ella la métrica cae a
    la definición acotada a la ventana, así que para resultados comparables
    entre repos se corre siempre con el runner local.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.registros: list[dict] = []  # {author, component, timestamp}, solo la ventana
        self.primera_contribucion: dict[tuple, datetime] = {}

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime, max_commits: int = 200):
        print("Descargando lista de commits...")
        commits, page = [], 1
        while len(commits) < max_commits:
            data = self._rest(
                f"/repos/{self.org}/{self.repo}/commits",
                {
                    "since": fecha_inicio.isoformat(),
                    "until": fecha_fin.isoformat(),
                    "per_page": 100,
                    "page": page,
                },
            )
            if not data:
                break
            commits.extend(data)
            if len(data) < 100:
                break
            page += 1
        commits = commits[:max_commits]
        print(f"Commits en período: {len(commits)}")

        registros = []
        for i, c in enumerate(commits):
            detail = self._rest(f"/repos/{self.org}/{self.repo}/commits/{c['sha']}")
            author = (c.get("author") or {}).get("login") \
                or (c.get("commit", {}).get("author") or {}).get("name") \
                or "desconocido"
            ts = datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00"))
            for f in detail.get("files", []):
                filename = f["filename"]
                registros.append({"author": author, "component": componente_de(filename),
                                  "timestamp": ts})
            print(f"  ...{i + 1}/{len(commits)} commits analizados", end="\r")
        print()
        self.registros = registros

    def _le_por_par(self) -> dict[tuple, int]:
        """{(autor, componente): días} para cada par con actividad en la ventana."""
        por_par: dict[tuple, list[dict]] = {}
        for r in self.registros:
            if self._es_bot(r["author"]):
                continue
            por_par.setdefault((r["author"], r["component"]), []).append(r)
        return {
            par: calcular_learning_easy(commits, self.primera_contribucion.get(par))
            for par, commits in por_par.items()
        }

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime) -> float | None:
        # Promedio sobre los pares (autor, componente) activos en la ventana: cuánto
        # les llevó en promedio a quienes trabajaron en este período dominar lo que tocaron.
        valores = list(self._le_por_par().values())
        if not valores:
            return None  # ventana sin commits: no observable (NULL, no 0.0)
        return round(sum(valores) / len(valores), 2)

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, float]:
        le_por_autor: dict[str, list[int]] = {}
        for (author, _componente), dias in self._le_por_par().items():
            le_por_autor.setdefault(author, []).append(dias)

        resultado = {
            author: round(sum(valores) / len(valores), 2)
            for author, valores in le_por_autor.items()
        }
        return dict(sorted(resultado.items(), key=lambda x: x[1]))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona",
            max_commits: int = 200, **kwargs):
        self.fetch(fecha_inicio, fecha_fin, max_commits=max_commits)
        if not self.registros:
            print("No se encontraron commits en el período.")
            return

        if por == "producto":
            le = self.por_producto(fecha_inicio, fecha_fin)
            print(f"\nLE (Learning Easy) promedio por componente: {le} días")
        else:
            resultado = self.por_persona(fecha_inicio, fecha_fin)
            print(f"\n{'Colaborador':<30} LE (días, promedio por componente)")
            print("-" * 60)
            for author, le in resultado.items():
                print(f"{author:<30} {le}")
