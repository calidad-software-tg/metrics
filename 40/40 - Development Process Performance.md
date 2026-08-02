# 40 – Development Process Performance

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 40 - La adhesión a las prácticas / políticas de desarrollo definidas |
| **Métrica Original (ISL)** | Process Compliance (alt.: Development Policy Adherence) |
| **Métrica Canónica JAIIO 2022** | Development Process Performance |
| **Métrica Adoptada / Calculable** | Development Process Performance |
| **Dimensiones Asociadas** | Proceso |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1Ytxi7bWr0KWL9zzsFvR8J48LoaS86xH1/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

La consigna original pide adhesión a prácticas/políticas de desarrollo definidas. Según la propia observación de la planilla: *"no existe una métrica explícita de Process Compliance o Policy Compliance en la ISL 2022"* — **Development Process Performance** es la más cercana porque evalúa el desempeño del proceso global, aunque no mide adherencia a una política explícita sino la capacidad de respuesta del equipo.

---

## 2. Definición de la Métrica

Mide la eficiencia del equipo ("equipo quirúrgico") mediante la probabilidad de cierre de issues dentro de ventanas de tiempo críticas: **3 días** (respuesta rápida a problemas simples) y **365 días** (resolución de problemas difíciles/antiguos).

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Proceso** | Evalúa el desempeño del flujo de resolución de issues del equipo, no un artefacto de producto ni una persona en particular. |

### 2.2 Fundamento Teórico

Según Jarczyk et al. (2018), usa una aproximación al **análisis de supervivencia de Kaplan-Meier**: cada issue es un "sujeto" que sobrevive (permanece abierto) o "muere" (se cierra) en función del tiempo. Refleja la calidad del soporte técnico del proyecto.

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **metadata_issues** | Lista de issues, cada uno con `created_at` y `closed_at` (o `None` si sigue abierto). |
| **dias_umbral** | Ventana de evaluación: 3 días (respuesta rápida) o 365 días (problemas difíciles). |

### 3.2 Lógica del proceso

```python
def calcular_process_performance(metadata_issues, dias_umbral=3):
    if not metadata_issues:
        return 0.0
    issues_resueltos_a_tiempo = 0
    total_issues_evaluables = len(metadata_issues)
    for issue in metadata_issues:
        fecha_cierre = issue.get('closed_at')
        if fecha_cierre:
            duracion = (fecha_cierre - issue.get('created_at')).days
            if duracion <= dias_umbral:
                issues_resueltos_a_tiempo += 1
        else:
            continue  # issue "superviviente" (censurado), no cuenta como éxito
    return round(issues_resueltos_a_tiempo / total_issues_evaluables, 4)
```

Notar que el denominador es **todos** los issues evaluables (abiertos + cerrados), no solo los cerrados: un issue que sigue abierto resta al score aunque no sea técnicamente un "fallo" (es censurado en términos de supervivencia), tal como está definido literalmente en el algoritmo de la planilla.

### 3.3 Implementación sobre GitHub

`metrics/40/process_performance.py` descarga todos los issues vía GraphQL paginado (`createdAt`, `closedAt`), filtra los creados dentro del período, y aplica `calcular_process_performance` dos veces (umbral 3 y 365 días).

- **`por_producto`**: score de performance del repositorio para un `dias_umbral` dado (default 3).
- **`por_persona`**: **no aplica** (`NotImplementedError`) — el algoritmo evalúa el ciclo de vida de los issues del repositorio sin ninguna atribución a un desarrollador.

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **Performance Score** | Float entre 0.0 y 1.0. Proporción de issues resueltos dentro del umbral evaluado. |

---

## 4. Salida Obtenida

**Repositorio configurado en `.env`:** `calidad-software-tg/tldr` — sin issues, mismo patrón que las demás métricas basadas en issues/PRs contra este fork.

**Corrida completa contra `tldr-pages/tldr`** (ventana de 15 años, 1.786 issues evaluados):

| Umbral | Performance Score |
|---|---|
| 3 días (respuesta rápida) | **0.3225** |
| 365 días (problemas difíciles) | **0.7794** |

> Interpretación: ~32% de los issues de tldr se resuelven en 3 días o menos (respuesta rápida moderada), mientras que ~78% se resuelve dentro del año — es decir, un ~22% queda sin cerrar más de un año (o directamente abierto), lo cual es consistente con la naturaleza de un repo mantenido por voluntarios sin SLA formal.

---

## 5. Referencias

- Jarczyk, O. et al. (2018). Rendimiento de "equipos quirúrgicos" medido por capacidad de respuesta ante issues.
- Análisis de supervivencia de Kaplan-Meier — marco teórico de referencia para la interpretación de issues censurados.
