# 23 – Schedule Compliance

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 23 - El cumplimiento de plazos de entrega |
| **Métrica Original (ISL)** | Schedule Compliance (alt.: Deadline Adherence) |
| **Métrica Canónica JAIIO 2022** | Schedule Variance |
| **Métrica Adoptada / Calculable** | Schedule Compliance |
| **Dimensiones Asociadas** | Proceso |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1j3ZvlK5q1byPKS3yKbnIIJvl8cylpSC7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

La consigna original refiere al cumplimiento de plazos de entrega. Está clasificada en el Systematic Mapping Study como métrica de gestión de proyectos, asociada al **SPI (Schedule Performance Index)** y al **SV (Schedule Variance)** de la literatura clásica de gestión de proyectos (EVM — Earned Value Management).

---

## 2. Definición de la Métrica

**Schedule Compliance** mide la eficiencia del cronograma comparando el trabajo completado contra el trabajo planificado para un hito (milestone) o período determinado.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Proceso** | Evalúa la capacidad del equipo para entregar los compromisos adquiridos en el tiempo pactado, a nivel de la gestión del flujo de trabajo del repositorio. |

### 2.2 Fundamento Teórico

Según el Systematic Mapping Study de Colakoglu et al. (2021), el SPI es una de las métricas de gestión de proyectos más citadas en la literatura. Se calcula como Earned Value (trabajo realmente completado) sobre Planned Value (trabajo total planificado).

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **metadata_milestone** | Diccionario del endpoint `/repos/:owner/:repo/milestones` de GitHub, con `open_issues` (tareas pendientes) y `closed_issues` (tareas finalizadas). |

### 3.2 Lógica del proceso

```python
def calcular_schedule_compliance(metadata_milestone):
    tareas_abiertas = metadata_milestone.get('open_issues', 0)
    tareas_cerradas = metadata_milestone.get('closed_issues', 0)
    tareas_totales = tareas_abiertas + tareas_cerradas
    if tareas_totales == 0:
        return 0.0
    compliance_score = tareas_cerradas / tareas_totales
    return round(compliance_score, 4)
```

### 3.3 Implementación sobre GitHub

`metrics/23/schedule_compliance.py` descarga todos los milestones del repositorio (`/repos/{org}/{repo}/milestones?state=all`, paginado) y filtra los que caen dentro del período (`due_on`, o `created_at` si el milestone no tiene fecha límite). Aplica `calcular_schedule_compliance` a cada uno.

- **`por_producto`**: promedio de `compliance_score` entre todos los milestones del período — un único número que resume el cumplimiento de cronograma del repositorio.
- **`por_persona`**: **no aplica**. El algoritmo original solo recibe metadata del milestone (`open_issues`/`closed_issues`), sin ningún dato de autoría por tarea — un milestone es un artefacto de gestión del repositorio, no de un desarrollador individual. `por_persona` tira `NotImplementedError`.

> Nota: GitHub sí expone un campo `creator.login` por milestone (quién lo creó), que en teoría podría usarse como proxy de "Persona" (ej. promedio de compliance de los milestones que gestionó cada PM). No se implementó porque el algoritmo provisto en la planilla no lo contempla y hubiera sido una extrapolación no pedida — se puede agregar después si hace falta esa apertura.

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **Compliance Score** | Float entre 0.0 y 1.0 por milestone. 1.0 = 100% de las tareas planificadas para ese hito ya están cerradas. |
| **Schedule Compliance promedio** | Promedio de los compliance scores de todos los milestones del período — indicador global de cumplimiento de cronograma del repositorio. |

---

## 4. Salida Obtenida

**Repositorio configurado en `.env`:** `calidad-software-tg/tldr` — este fork **no tiene milestones**, mismo patrón de las demás métricas basadas en artefactos de gestión de GitHub (issues/PRs/milestones) contra este repo de prueba.

**Validación contra `tldr-pages/tldr`** (repositorio original, ventana de 15 años):

| Milestone | Cerradas | Abiertas | Compliance |
|---|---|---|---|
| v2.0 | 1 | 0 | 1.0 |
| v2.1 | 4 | 0 | 1.0 |
| v2.2 | 3 | 0 | 1.0 |

**Schedule Compliance promedio del repositorio: 1.0**

> Los tres milestones de `tldr-pages/tldr` están completamente cerrados, por lo que da 1.0 parejo — no es representativo de un repo con milestones activos. La fórmula y el parseo de la API (`open_issues`, `closed_issues`, `due_on`) quedaron validados con datos reales; para ver variación en el score conviene correrla contra un repositorio con milestones aún abiertos o parcialmente completados.

---

## 5. Referencias

- Colakoglu et al. (2021). Systematic Mapping Study — SPI como métrica de gestión de proyectos más citada en la literatura.
- Earned Value Management (EVM) — SPI = Earned Value / Planned Value.
