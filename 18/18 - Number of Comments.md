# 18 – Number of Comments (NC)

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 18 y 19 - La frecuencia de participación en discusiones técnicas |
| **Métrica Original (ISL)** | Developer Skill Communication (alt.: Habilidad de Comunicación del Desarrollador) |
| **Métrica Canónica JAIIO 2022** | Developer Skill Communication |
| **Métrica Adoptada / Calculable** | Number of Comments (NC) |
| **Dimensiones Asociadas** | Persona, Proceso |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

La consigna original está relacionada con la capacidad de comunicación del desarrollador, pero **no mide directamente resolución de conflictos o problemas comunicacionales** — es una limitación explícita del catálogo. NC operacionaliza la parte que sí es calculable: el volumen de participación en discusiones técnicas.

---

## 2. Definición de la Métrica

**Number of Comments (NC)** cuantifica el volumen total de intervenciones de un desarrollador en los distintos canales de comunicación del repositorio: comentarios en issues/PRs, comentarios sobre líneas de código en commits, y comentarios de revisión de código.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Persona** | Cuantifica la participación individual de un desarrollador. |
| **Proceso** | Se basa en los canales de comunicación del flujo de trabajo colaborativo (issues, PRs, revisiones). |

### 2.2 Fundamento Teórico

Según la taxonomía de Falcão et al. (2020), un valor alto de NC indica un fuerte compromiso social y técnico, permitiendo medir la influencia del desarrollador en el flujo de toma de decisiones del proyecto.

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **eventos_usuario** | Lista de eventos del usuario, cada uno con `type` (tipo de evento de comentario). |

### 3.2 Lógica del proceso

```python
def calcular_nc(eventos_usuario):
    eventos_objetivo = ['IssueCommentEvent', 'CommitCommentEvent', 'PullRequestReviewCommentEvent']
    nc_total = 0
    for evento in eventos_usuario:
        if evento.get('type') in eventos_objetivo:
            nc_total += 1
    return nc_total
```

### 3.3 Implementación sobre GitHub

La planilla sugiere el endpoint `/users/:username/events`, pero este solo devuelve eventos **públicos de los últimos 90 días** de un usuario en cualquier repo, no acotado al repositorio objetivo — poco útil para un análisis histórico de un repositorio específico.

`metrics/18/nc.py` reconstruye la misma taxonomía de eventos usando los endpoints REST **scopeados al repositorio** (sin límite de 90 días, paginados):

| Tipo de evento (taxonomía original) | Endpoint REST usado |
|---|---|
| `IssueCommentEvent` | `/repos/{org}/{repo}/issues/comments` |
| `CommitCommentEvent` | `/repos/{org}/{repo}/comments` |
| `PullRequestReviewCommentEvent` | `/repos/{org}/{repo}/pulls/comments` |

Cada comentario obtenido se normaliza a `{'type': ..., 'login': ..., 'fecha': ...}`, se agrupa por autor, y se aplica `calcular_nc` a cada grupo.

- **`por_persona`**: NC por colaborador.
- **`por_producto`**: no aplica (métrica de Persona/Proceso, sin agregación de producto).

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **NC** | Entero ≥ 0. Cantidad total de comentarios técnicos y sociales realizados por el desarrollador en el período. |

---

## 4. Salida Obtenida

**Repositorio configurado en `.env`:** `calidad-software-tg/tldr` — este fork **no tiene issues, PRs ni comentarios de commits** (0 resultados en los tres endpoints), consistente con lo ya observado para EXPRev/REXPRev y para "Doc Issue Survival" en la consigna 16.

**Corrida completa contra `tldr-pages/tldr`** (ventana de 90 días): 2.028 comentarios totales en el período.

**Top colaboradores por NC:**

| Colaborador | NC |
|---|---|
| Managor | 428 |
| ivanbaluta | 424 |
| tldr-bot | 254 |
| CLAassistant | 152 |
| acuteenvy | 67 |
| SpikeTheDragon40k | 42 |
| TheRootDaemon | 35 |

> Los tres endpoints (`/issues/comments`, `/comments`, `/pulls/comments`) filtran por `since` del lado del servidor, así que la corrida sobre una ventana acotada es rápida (~20 páginas en total). `tldr-bot` y `CLAassistant` son bots de automatización — vale la pena filtrarlos si el análisis de la tesis busca aislar la comunicación humana.

---

## 5. Referencias

- Falcão, R. et al. (2020). Taxonomía de eventos de comunicación técnica y social en GitHub.
