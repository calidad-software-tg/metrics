# 18 – Discussion Centrality

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 18 y 19 - La frecuencia de participación en discusiones técnicas |
| **Métrica Original (ISL)** | Developer Skill Communication (alt.: Habilidad de Comunicación del Desarrollador) |
| **Métrica Canónica JAIIO 2022** | Developer Skill Communication |
| **Métrica Adoptada / Calculable** | Discussion Centrality |
| **Dimensiones Asociadas** | Persona |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

> **Nota de implementación:** el algoritmo original de la planilla usa la librería `networkx` para construir la MBSN (Multidimensional Behavioral Social Network) y calcular su centralidad de grado. El proyecto no depende de `networkx` en ningún otro punto (`requests` es la única dependencia externa usada en todo `metrics/`), así que `metrics/18/disc_centrality.py` reimplementa el mismo cálculo (conteo de vecinos únicos en un grafo no dirigido) con estructuras nativas de Python, sin agregar una librería nueva. El resultado matemático es idéntico al de `G.degree(usuario)` de networkx para un grafo simple no ponderado.

---

## 1. Observación

Mientras que NC mide el **volumen** de participación, Discussion Centrality mide su **alcance social**: con cuántos desarrolladores distintos interactuó un autor al compartir hilos de discusión. Complementa a NC — un desarrollador puede tener muchos comentarios pero concentrados con pocas personas (baja centralidad), o pocos comentarios pero repartidos entre muchos hilos y personas distintas (alta centralidad).

---

## 2. Definición de la Métrica

**Discussion Centrality** mide la importancia de un desarrollador dentro de la red social de discusión del proyecto, basándose en con quién intercambia comentarios. Se construye una red (MBSN) donde dos desarrolladores quedan conectados si comentaron en el mismo hilo (issue, PR o commit), y se mide el grado del nodo del desarrollador objetivo: la cantidad de vecinos distintos.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Persona** | Mide la influencia y conectividad social individual del autor dentro de la red de discusión. |

### 2.2 Fundamento Teórico

Se asume que compartir un hilo de discusión implica un reconocimiento técnico mutuo entre los participantes. Una alta centralidad indica que el usuario es un nodo crítico en la resolución de problemas y solicitudes de extracción — más conectado con el resto del equipo que un colaborador aislado.

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **metadata_comentarios** | Lista de todos los comentarios del repositorio, cada uno con `item_id` (hilo) y `user_login` (autor). |
| **login_usuario_objetivo** | El desarrollador cuya centralidad se desea medir. |

### 3.2 Lógica del proceso

```python
def calcular_discussion_centrality(metadata_comentarios, login_usuario_objetivo):
    hilos = {}
    for comentario in metadata_comentarios:
        hilos.setdefault(comentario['item_id'], set()).add(comentario['user_login'])

    adyacencia = {}
    for usuarios_en_hilo in hilos.values():
        lista_usuarios = list(usuarios_en_hilo)
        for i in range(len(lista_usuarios)):
            for j in range(i + 1, len(lista_usuarios)):
                a, b = lista_usuarios[i], lista_usuarios[j]
                adyacencia.setdefault(a, set()).add(b)
                adyacencia.setdefault(b, set()).add(a)

    if login_usuario_objetivo not in adyacencia:
        return 0
    return len(adyacencia[login_usuario_objetivo])
```

### 3.3 Implementación sobre GitHub

`metrics/18/disc_centrality.py` reutiliza las mismas tres fuentes de comentarios que NC (`/issues/comments`, `/pulls/comments`, `/comments`), pero en lugar de contarlos por autor, arma `item_id` por hilo:

| Fuente | `item_id` |
|---|---|
| Comentarios de issues/PRs | `issue-{número}` (extraído de `issue_url`) |
| Comentarios de revisión de PRs | `pr-{número}` (extraído de `pull_request_url`) |
| Comentarios de commits | `commit-{sha}` (campo `commit_id`) |

- **`por_persona`**: centralidad de grado por colaborador (para todos los que aparecen como autores de al menos un comentario).
- **`por_producto`**: no aplica (métrica exclusivamente de Persona).

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **Centralidad** | Entero ≥ 0. Cantidad de desarrolladores distintos con los que el usuario compartió al menos un hilo de discusión. |

---

## 4. Salida Obtenida

**Repositorio configurado en `.env`:** `calidad-software-tg/tldr` — sin comentarios (mismo fork sin issues/PRs que afecta a NC, EXPRev y REXPRev).

**Validación de la lógica:** se probó `calcular_discussion_centrality` con datos sintéticos (dos usuarios compartiendo un hilo, un tercero en otro hilo distinto) y devolvió el grado esperado. Los endpoints REST fueron validados con datos reales de `tldr-pages/tldr` (`issue_url`, `pull_request_url`, `commit_id` presentes y parseables).

**Recomendación:** correr `disc_centrality.py` contra el repositorio objetivo real de la tesis para obtener valores representativos.

---

## 5. Referencias

- MBSN (Multidimensional Behavioral Social Network) — modelo de red social de discusión basado en co-participación en hilos.
