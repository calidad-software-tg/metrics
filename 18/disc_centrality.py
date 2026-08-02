import sys
import re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from base_metric import GitHubMetric


def calcular_discussion_centrality(metadata_comentarios: list[dict], login_usuario_objetivo: str) -> int:
    """
    Calcula la Centralidad de Discusión basada en el grado del nodo en la MBSN.

    Esta métrica de Persona mide la influencia y conectividad social del autor.
    Se asume que si dos desarrolladores intercambian comentarios en un mismo
    hilo (issue, pull request o commit), existe un reconocimiento técnico mutuo,
    formando un enlace en la red social de discusión.

    metadata_comentarios: Lista de diccionarios, cada uno con:
        - 'item_id': identificador único del hilo (issue, PR o commit).
        - 'user_login': login del usuario que realizó el comentario.
    login_usuario_objetivo: login del desarrollador cuya centralidad se desea medir.

    Retorna: cantidad de desarrolladores distintos con los que el usuario ha
    interactuado en hilos de discusión comunes (grado de centralidad).

    Nota de implementación: el algoritmo original de la planilla usa la
    librería networkx para construir la MBSN (Multidimensional Behavioral
    Social Network) y calcular la centralidad de grado (degree centrality).
    Como el proyecto no depende de networkx en ningún otro punto, se
    reimplementa el mismo resultado (conteo de vecinos únicos en un grafo
    no dirigido) con estructuras nativas de Python, sin agregar la dependencia.
    """
    # 1. Agrupamos a los usuarios por cada hilo de discusión (MBSN logic)
    hilos: dict = {}
    for comentario in metadata_comentarios:
        id_hilo = comentario.get("item_id")
        usuario = comentario.get("user_login")
        hilos.setdefault(id_hilo, set()).add(usuario)

    # 2. Construcción de la adyacencia del grafo MBSN (sin networkx):
    # cada par de usuarios que compartió un hilo queda conectado.
    adyacencia: dict[str, set] = {}
    for usuarios_en_hilo in hilos.values():
        lista_usuarios = list(usuarios_en_hilo)
        for i in range(len(lista_usuarios)):
            for j in range(i + 1, len(lista_usuarios)):
                a, b = lista_usuarios[i], lista_usuarios[j]
                adyacencia.setdefault(a, set()).add(b)
                adyacencia.setdefault(b, set()).add(a)

    # 3. Cálculo de la Centralidad de Grado (Degree Centrality)
    if login_usuario_objetivo not in adyacencia:
        return 0

    return len(adyacencia[login_usuario_objetivo])


_ISSUE_NUM_RE = re.compile(r"/(\d+)$")


class DiscussionCentrality(GitHubMetric):
    """
    Discussion Centrality.
    Mide la importancia de un desarrollador dentro de la red social de
    discusión (MBSN) del proyecto, según con cuántos otros desarrolladores
    distintos comparte hilos de issues, PRs o commits. Solo aplica por persona.
    """

    def __init__(self, token: str, org: str, repo: str):
        super().__init__(token, org, repo)
        self.metadata_comentarios: list[dict] = []  # {item_id, user_login, fecha}

    def _fetch_issue_comments(self, fecha_inicio: datetime, fecha_fin: datetime):
        page = 1
        while True:
            data = self._rest(
                f"/repos/{self.org}/{self.repo}/issues/comments",
                {"per_page": 100, "page": page, "since": fecha_inicio.isoformat()},
            )
            if not data:
                break
            for c in data:
                created = datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
                if created > fecha_fin:
                    continue
                match = _ISSUE_NUM_RE.search(c.get("issue_url", ""))
                item_id = f"issue-{match.group(1)}" if match else c.get("issue_url")
                login = (c.get("user") or {}).get("login", "desconocido")
                self.metadata_comentarios.append({"item_id": item_id, "user_login": login, "fecha": created})
            print(f"  ...comentarios de issues/PRs página {page}", end="\r")
            if len(data) < 100:
                break
            page += 1
        print()

    def _fetch_pr_review_comments(self, fecha_inicio: datetime, fecha_fin: datetime):
        page = 1
        while True:
            data = self._rest(
                f"/repos/{self.org}/{self.repo}/pulls/comments",
                {"per_page": 100, "page": page, "since": fecha_inicio.isoformat()},
            )
            if not data:
                break
            for c in data:
                created = datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
                if created > fecha_fin:
                    continue
                match = _ISSUE_NUM_RE.search(c.get("pull_request_url", ""))
                item_id = f"pr-{match.group(1)}" if match else c.get("pull_request_url")
                login = (c.get("user") or {}).get("login", "desconocido")
                self.metadata_comentarios.append({"item_id": item_id, "user_login": login, "fecha": created})
            print(f"  ...comentarios de revisión de PRs página {page}", end="\r")
            if len(data) < 100:
                break
            page += 1
        print()

    def _fetch_commit_comments(self, fecha_inicio: datetime, fecha_fin: datetime):
        page = 1
        while True:
            data = self._rest(
                f"/repos/{self.org}/{self.repo}/comments",
                {"per_page": 100, "page": page, "since": fecha_inicio.isoformat()},
            )
            if not data:
                break
            for c in data:
                created = datetime.fromisoformat(c["created_at"].replace("Z", "+00:00"))
                if created > fecha_fin:
                    continue
                item_id = f"commit-{c.get('commit_id')}"
                login = (c.get("user") or {}).get("login", "desconocido")
                self.metadata_comentarios.append({"item_id": item_id, "user_login": login, "fecha": created})
            print(f"  ...comentarios de commits página {page}", end="\r")
            if len(data) < 100:
                break
            page += 1
        print()

    def fetch(self, fecha_inicio: datetime, fecha_fin: datetime):
        self.metadata_comentarios = []
        print("Obteniendo comentarios de issues/PRs...")
        self._fetch_issue_comments(fecha_inicio, fecha_fin)
        print("Obteniendo comentarios de revisión de PRs...")
        self._fetch_pr_review_comments(fecha_inicio, fecha_fin)
        print("Obteniendo comentarios de commits...")
        self._fetch_commit_comments(fecha_inicio, fecha_fin)
        print(f"Comentarios totales en período: {len(self.metadata_comentarios)}")

    def por_producto(self, fecha_inicio: datetime, fecha_fin: datetime):
        raise NotImplementedError("Discussion Centrality es una métrica por persona, no aplica por producto.")

    def por_persona(self, fecha_inicio: datetime, fecha_fin: datetime) -> dict[str, int]:
        usuarios = {c["user_login"] for c in self.metadata_comentarios}
        resultado = {
            login: calcular_discussion_centrality(self.metadata_comentarios, login)
            for login in usuarios
        }
        return dict(sorted(resultado.items(), key=lambda x: x[1], reverse=True))

    def run(self, fecha_inicio: datetime, fecha_fin: datetime, por: str = "persona", **kwargs):
        if por == "producto":
            print("Discussion Centrality no aplica por producto: es una métrica por persona.")
            return
        self.fetch(fecha_inicio, fecha_fin)
        resultado = self.por_persona(fecha_inicio, fecha_fin)
        if not resultado:
            print("No se encontraron comentarios en el período.")
            return
        print(f"\n{'Colaborador':<30} Centralidad")
        print("-" * 45)
        for login, centralidad in resultado.items():
            print(f"{login:<30} {centralidad}")
