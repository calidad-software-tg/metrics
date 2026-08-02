# 15 – EXPRev (Experiencia en Revisión de Código)

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 15 - La capacidad de aprender nuevas habilidades técnicas |
| **Métrica Original (ISL)** | Contribution Diversity (alt.: Multi-project Contribution) |
| **Métrica Canónica JAIIO 2022** | — |
| **Métrica Adoptada / Calculable** | EXPRev (Experiencia en Revisión de Código) |
| **Dimensiones Asociadas** | Persona, Proceso |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

EXPRev cuantifica la experiencia de un desarrollador en actividades de revisión de código y discusión técnica dentro del ecosistema de GitHub: apertura y cierre de issues, gestión de pull requests, y participación mediante comentarios en ambos. Es un indicador híbrido de Persona y Proceso: captura tanto la actividad individual como su inserción en el flujo de trabajo colaborativo de aprendizaje técnico.

---

## 2. Definición de la Métrica

**EXPRev** es la suma agregada de seis dimensiones de actividad de un desarrollador en un repositorio: issues abiertos, issues cerrados, PRs abiertas, PRs cerradas, comentarios en issues y comentarios en PRs.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Persona** | Mide la actividad individual de revisión y discusión de un desarrollador. |
| **Proceso** | Captura su participación en el flujo de gestión de issues y PRs del equipo. |

### 2.2 Fundamento Teórico

Representa el "capital social" y la influencia técnica que un desarrollador adquiere antes de que sus contribuciones sean evaluadas como propensas a errores. Recomendable contrastar con REXPRev para identificar si la experiencia de revisión reciente pesa más que la histórica.

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **metadata_usuario_repo** | Diccionario con conteos agregados de actividad del usuario: `issues_opened`, `issues_closed`, `pull_requests_opened`, `pull_requests_closed`, `issue_comments`, `pull_request_comments`. |

### 3.2 Lógica del proceso

```python
def calcular_exprev(metadata_usuario_repo):
    issues_abiertos = metadata_usuario_repo.get('issues_opened', 0)
    issues_cerrados = metadata_usuario_repo.get('issues_closed', 0)
    prs_abiertas = metadata_usuario_repo.get('pull_requests_opened', 0)
    prs_cerradas = metadata_usuario_repo.get('pull_requests_closed', 0)
    comentarios_issues = metadata_usuario_repo.get('issue_comments', 0)
    comentarios_prs = metadata_usuario_repo.get('pull_request_comments', 0)
    return (issues_abiertos + issues_cerrados + prs_abiertas + prs_cerradas +
            comentarios_issues + comentarios_prs)
```

### 3.3 Implementación sobre GitHub

`metrics/15/exprev.py` combina:
- **GraphQL** sobre `issues` y `pullRequests` (autor de apertura, y autor del evento de cierre vía `timelineItems(itemTypes: [CLOSED_EVENT])`, o `mergedBy` para PRs fusionadas).
- **REST** paginado sobre `/issues/comments` y `/pulls/comments` para los comentarios de discusión y de revisión de código.

Todos los eventos se filtran al período `[fecha_inicio, fecha_fin]` y se agrupan por usuario antes de aplicar `calcular_exprev`.

> **Optimización de paginación (ver sección 4):** las queries GraphQL piden `orderBy: {field: UPDATED_AT, direction: DESC}` y la paginación corta apenas aparece un nodo con `updatedAt < fecha_inicio`. Como `updatedAt` nunca es anterior a `createdAt` ni a `closedAt`, este corte no pierde eventos de apertura ni de cierre dentro de la ventana, pero evita recorrer todo el historial del repositorio — antes se paginaba TODOS los issues/PRs sin importar el período pedido.

- **`por_persona`**: EXPRev por colaborador.
- **`por_producto`**: no aplica (métrica de Persona/Proceso, sin agregación de producto).

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **EXPRev** | Entero ≥ 0. Suma escalar de todas las interacciones de revisión y discusión técnica del desarrollador en el período. |

---

## 4. Salida Obtenida

**Repositorio configurado en `.env`:** `calidad-software-tg/tldr` — este fork **no tiene issues ni pull requests** (0 nodos en ambas queries GraphQL), por lo que no arroja actividad de revisión.

**Corrida completa contra `tldr-pages/tldr`** (ventana de 30 días, 1.471 eventos totales, **34.4s**):

| Colaborador | EXPRev |
|---|---|
| Managor | 343 |
| ivanbaluta | 341 |
| tldr-bot | 87 |
| cyforkk | 65 |
| sebastiaanspeck | 62 |
| SpikeTheDragon40k | 62 |
| CLAassistant | 59 |
| kant | 55 |

> Antes de la optimización de paginación (orden `UPDATED_AT DESC` + corte temprano, ver sección 3.3), la misma consulta sin acotar quedó corriendo **más de 10 minutos sin terminar** para esta misma ventana de 30 días — porque paginaba los ~5.700 PRs históricos del repo completo antes de filtrar por fecha. Con el corte temprano, la corrida solo recorrió 1 página de issues y 10 de PRs.

**Recomendación:** para el análisis final de la tesis, correr `exprev.py` directamente sobre el repositorio objetivo con la ventana real de interés — ya no hace falta acotar artificialmente el período por costo de API.

---

## 5. Referencias

- Falcão, R. et al. (2020). Cinco dimensiones de actividad de revisión y discusión técnica.
