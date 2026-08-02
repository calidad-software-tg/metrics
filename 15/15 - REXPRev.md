# 15 – REXPRev (Experiencia Reciente en Revisión de Código)

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 15 - La capacidad de aprender nuevas habilidades técnicas |
| **Métrica Original (ISL)** | Contribution Diversity (alt.: Multi-project Contribution) |
| **Métrica Canónica JAIIO 2022** | — |
| **Métrica Adoptada / Calculable** | REXPRev (Experiencia Reciente en Revisión de Código) |
| **Dimensiones Asociadas** | Persona, Proceso |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

REXPRev es la versión ponderada temporalmente de EXPRev: da más peso a la experticia de revisión/discusión más reciente, bajo la premisa de que el conocimiento adquirido mediante el escrutinio de código pierde valor si no está vigente.

---

## 2. Definición de la Métrica

**REXPRev** pondera cada evento de revisión (issue/PR abierto o cerrado, comentario) por un factor de decaimiento temporal según su antigüedad respecto de una fecha de referencia.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Persona** | Mide la experticia individual reciente en revisión de código. |
| **Proceso** | Se basa en eventos del flujo de gestión de issues/PRs del repositorio. |

### 2.2 Fundamento Teórico

Fusiona el factor de Persona (experticia acumulada) con el dinamismo del Proceso (vigencia de la actividad). Permite identificar el fenómeno de "obsolescencia de conocimiento": un desarrollador con alta experiencia histórica (EXPRev/EXP) pero desconectado recientemente de la discusión técnica puede perder capacidad para evitar defectos.

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **eventos_usuario_repo** | Lista de interacciones (issue, PR o comentario) del usuario, cada una con `tipo` y `fecha`. |
| **fecha_actual** | Punto de referencia temporal para el cálculo del decaimiento. |

### 3.2 Lógica del proceso

```python
def calcular_rexprev(eventos_usuario_repo, fecha_actual):
    tipos_revision = [
        'issues_opened', 'issues_closed',
        'pull_requests_opened', 'pull_requests_closed',
        'issue_comments', 'pull_request_comments'
    ]
    rexprev_total = 0
    for evento in eventos_usuario_repo:
        if evento['tipo'] in tipos_revision:
            dias_antiguedad = (fecha_actual - evento['fecha']).days
            rexprev_total += 1 / (dias_antiguedad + 1)
    return rexprev_total
```

### 3.3 Implementación sobre GitHub

`metrics/15/rexprev.py` reutiliza la misma recolección de eventos que EXPRev (GraphQL sobre issues/PRs + REST sobre comentarios de issues y de revisión de PRs), pero en lugar de sumar conteos, conserva la fecha de cada evento y aplica `calcular_rexprev` por colaborador usando `fecha_fin` del período como `fecha_actual`.

- **`por_persona`**: REXPRev por colaborador.
- **`por_producto`**: no aplica (métrica de Persona/Proceso).

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **REXPRev** | Número real ≥ 0. A mayor valor, mayor actividad de revisión/discusión reciente del desarrollador (eventos del mismo día suman ~1; eventos de hace un año suman ~0.003). |

---

## 4. Salida Obtenida

**Repositorio configurado en `.env`:** `calidad-software-tg/tldr` — sin issues ni PRs (fork sin actividad de revisión), por lo que no arroja eventos.

**Validación:** la query GraphQL compartida con EXPRev fue verificada contra `tldr-pages/tldr` (ver `15 - EXPRev.md`, sección 4), confirmando estructura y campos correctos. No se ejecutó una corrida completa en esta sesión por el volumen de PRs del repositorio original (~5.700), que insumiría muchas páginas GraphQL.

**Recomendación:** correr `rexprev.py` contra el repositorio objetivo real del trabajo de grado, acotando el período de análisis para limitar el volumen de páginas.

---

## 5. Referencias

- REXPRev como versión ponderada temporalmente de EXPRev — fusión de Persona (experticia) y Proceso (vigencia de la actividad).
