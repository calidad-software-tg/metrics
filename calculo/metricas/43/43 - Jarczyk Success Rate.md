# 43 – Tasa de Éxito de Jarczyk (n1 = n · pt)

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 43 - El tiempo promedio de resolución de problemas |
| **Métrica Original (ISL)** | Average Problem Resolution Time (alt.: Mean Time To Resolve Problems) |
| **Métrica Canónica JAIIO 2022** | Number of Closed Issues |
| **Métrica Adoptada / Calculable** | Tasa de éxito (proporción NCI / total de issues) |
| **Dimensiones Asociadas** | Proceso |
| **Fuente** | [Documento de referencia (Google Drive)](https://drive.google.com/file/d/1fMRgY71Hul3LNDwqw_97PLE-o1s_2Idn/view?usp=sharing) |

---

## 1. Observación

Esta no es una métrica final por sí misma en el paper de Jarczyk, sino el **insumo** (`n1`, componente de "éxitos") del modelo de regresión binomial que él usa para estimar la probabilidad de que un issue sobreviva (siga abierto) o se resuelva a 3 y 365 días. Se relaciona directamente con **Development Process Performance** (consigna 40), que aplica ese mismo marco de supervivencia con umbrales de 3 y 365 días — la diferencia es que Development Process Performance mide éxito en función del *tiempo de resolución individual* de cada issue, mientras que esta tasa mide el éxito *agregado* como proporción simple sobre el total de issues observados.

---

## 2. Definición de la Métrica

**Tasa de éxito de Jarczyk** es la proporción de issues cerrados (NCI) sobre el total de issues observados en el período: `pt = n1 / n`, donde `n1` es la cantidad de éxitos (cierres) y `n` la población total de issues.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Proceso** | Es un indicador agregado de la capacidad de resolución del flujo de trabajo del equipo, sin atribución a un artefacto de producto ni a una persona. |

### 2.2 Fundamento Teórico

Referencia: `n1 = n · pt`. Es la variable dependiente base en los modelos de regresión binomial de Jarczyk et al. para calcular la probabilidad de supervivencia de un problema — el mismo marco teórico detrás de Development Process Performance (consigna 40).

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **nci_total** | Cantidad de issues cerrados en el período (NCI, ver `43 - NCI (reutilizada).md`). |
| **total_issues** | Población total de issues observados en el período. |

### 3.2 Lógica del proceso

```python
def calcular_tasa_exito_jarczyk(nci_total, total_issues):
    if total_issues == 0:
        return 0.0
    return round(nci_total / total_issues, 4)
```

### 3.3 Implementación sobre GitHub

`metrics/43/tasa_exito.py` descarga los issues vía GraphQL (`createdAt`, `closedAt`, `state`) y define:

- **`total_issues` (n)**: cantidad de issues **creados** dentro del período `[fecha_inicio, fecha_fin]` — el mismo universo usado en Development Process Performance (consigna 40), para mantener consistencia entre métricas que comparten el marco teórico de Jarczyk.
- **`nci_total` (n1)**: cantidad de issues **cerrados** dentro del período, vía `calcular_nci` (idéntica a la NCI ya reutilizada, ver `43 - NCI (reutilizada).md`).

> Nota de diseño: el algoritmo original no especifica cómo se deriva `total_issues` a partir de `metadata_issues` — solo indica que es la población total. Se optó por "issues creados en el período" en vez de "todos los issues históricos del repo", para que la tasa sea comparable ventana a ventana (igual que NOI y Process Performance de la consigna 40). Si el análisis de la tesis necesita otra definición de población (ej. todos los issues abiertos alguna vez), es un cambio de una línea en `por_producto`.

- **`por_producto`**: tasa de éxito del repositorio en el período.
- **`por_persona`**: **no aplica** (`NotImplementedError`) — sin atribución a un desarrollador.

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **Tasa de éxito (pt)** | Float entre 0.0 y 1.0. Proporción de issues cerrados sobre el total de issues del período. |

---

## 4. Salida Obtenida

**Repositorio configurado en `.env`:** `calidad-software-tg/tldr` — sin issues.

**Corrida completa contra `tldr-pages/tldr`** (ventana de 15 años):

| n (issues creados) | n1 (issues cerrados, NCI) | Tasa de éxito (pt) |
|---|---|---|
| 1.786 | 1.556 | **0.8712** |

> El 87% de los issues creados históricamente en tldr terminaron cerrados. Es coherente con el 78% de "Development Process Performance" a 365 días (consigna 40) — números en el mismo orden, calculados con métodos algo distintos (proporción agregada vs. promedio de éxitos individuales dentro de umbral), lo cual es una buena señal de consistencia entre ambas aproximaciones al mismo fenómeno.

---

## 5. Referencias

- Jarczyk, O. et al. Modelo de regresión binomial para probabilidad de supervivencia de issues (n1 = n · pt).
- Ver también: `metrics/40/40 - Development Process Performance.md` (mismo marco teórico, aplicado con umbrales de tiempo).
