import sys
import re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric


def calcular_nc(eventos_usuario: list[dict]) -> int:
    """
    Calcula el Number of Comments (NC) de un desarrollador.

    Esta métrica de Persona y Proceso cuantifica la participación activa
    del autor en las discusiones técnicas del repositorio.

    eventos_usuario: Lista de diccionarios, cada uno con 'type' (el tipo
                     de evento de comentario).
    """
    # (i) IssueCommentEvent: Comentarios en Issues y Pull Requests.
    # (ii) CommitCommentEvent: Discusiones directas sobre líneas de código.
    # (iii) PullRequestReviewCommentEvent: Comentarios detallados en revisiones.
    eventos_objetivo = [
        "IssueCommentEvent",
        "CommitCommentEvent",
        "PullRequestReviewCommentEvent",
    ]

    nc_total = 0
    for evento in eventos_usuario:
        tipo_evento = evento.get("type")
        if tipo_evento in eventos_objetivo:
            nc_total += 1

    return nc_total


class NumberOfComments(GitHubMetric):
    """
    NC (Number of Comments).
    Volumen total de intervenciones del desarrollador en los canales de
    comunicación del repositorio: comentarios en issues/PRs, comentarios
    de commit y comentarios de revisión de código. Solo aplica por persona.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.eventos: list[dict] = []  # {type, login, fecha}

    def _fetch_paginated(self, path: str, tipo: str, fecha_inicio: datetime, fecha_fin: datetime):
        for c in self._rest_list_since(
            f"/repos/{self.org}/{self.repo}{path}", fecha_inicio, fecha_fin, label=tipo,
        ):
            created = datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
            login = (c.get("user") or {}).get("login", "desconocido")
            self.eventos.append({"type": tipo, "login": login, "fecha": created})

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime):
        self.eventos = []
        print("Obteniendo comentarios de issues/PRs...")
        self._fetch_paginated("/issues/comments", "IssueCommentEvent", fecha_inicio, fecha_fin)
        print("Obteniendo comentarios de commits...")
        self._fetch_paginated("/comments", "CommitCommentEvent", fecha_inicio, fecha_fin)
        print("Obteniendo comentarios de revisión de PRs...")
        self._fetch_paginated("/pulls/comments", "PullRequestReviewCommentEvent", fecha_inicio, fecha_fin)
        print(f"Comentarios totales en período: {len(self.eventos)}")

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError("NC es una métrica por persona, no aplica por producto.")

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        por_autor: dict[str, list[dict]] = {}
        for e in self.eventos:
            por_autor.setdefault(e["login"], []).append(e)

        resultado = {
            login: calcular_nc(eventos)
            for login, eventos in por_autor.items()
        }
        return dict(sorted(resultado.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona", **kwargs):
        if por == "producto":
            print("NC no aplica por producto: es una métrica por persona.")
            return
        self.fetch(fecha_inicio, fecha_fin)
        resultado = self.por_persona(fecha_inicio, fecha_fin)
        if not resultado:
            print("No se encontraron comentarios en el período.")
            return
        print(f"\n{'Colaborador':<30} NC")
        print("-" * 40)
        for login, nc in resultado.items():
            print(f"{login:<30} {nc}")
