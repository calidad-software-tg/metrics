# 42 – Number of Branches

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                |
|---|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 41 - Cantidad de branches de desarrollo activas que existen en su repositorio principal                                                                                   |
| **Métrica Original (ISL)** | Number of Active Development Branches                                                                                                                                      |
| **Nombre Alternativo** | Active Branch Count                                                                                                                                                        |
| **Métrica Canónica JAIIO 2022** | Number of Branches                                                                                                                                                         |
| **Métrica Adoptada / Calculable** | Number of Branches (NOB)                                                                                                                                                   |
| **Dimensiones Asociadas** | Producto, Proceso                                                                                                                                                          |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/10I3bPeSj_n_86dO2kZdW7NSV7JBL9-R2/edit) |

---

## 1. Observación

Correspondencia prácticamente exacta. La única diferencia es que la consigna especifica "branches **activas**", mientras que la métrica canónica habla de "Number of Branches" en general. Conceptualmente representan el mismo fenómeno; se adopta la correspondencia directa sin necesidad de buscar una métrica sustituta.

**Nota:** esta implementación cuenta el total de branches existentes en el repositorio (vía la API de GitHub), no distingue entre branches "activas" e inactivas/obsoletas (por ejemplo, ramas de feature ya mergeadas pero no eliminadas). Esa distinción requeriría una definición operacional de "actividad" (ej. último commit dentro de una ventana temporal) que no está especificada en el algoritmo original.

---

## 2. Definición de la Métrica

**Number of Branches (NOB)** cuantifica la cantidad total de ramas (branches) existentes en el repositorio. Refleja la complejidad del flujo de trabajo y la concurrencia de tareas en desarrollo simultáneo.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Producto** | Refleja la estructura y complejidad del repositorio como artefacto: cuántas líneas de desarrollo paralelas coexisten. |
| **Proceso** | Es un indicador de la intensidad de la actividad técnica y del flujo de trabajo de desarrollo (branching workflow, feature branches, releases paralelos, etc.). |

### 2.2 Fundamento Teórico

Según **Jarczyk et al. (2014)**, el número de branches es **el atributo más importante** identificado en su estudio: un NOB alto tiene una **influencia positiva** en el proyecto, correlacionando negativamente con la supervivencia de los bugs (es decir, indica un soporte y resolución de errores más rápidos).

Los autores proponen además una **transformación logarítmica** para mitigar el sesgo propio de las distribuciones de ley de potencia (power law) que suele presentar esta métrica:

> x' = log₁₀(x + 10)

El desplazamiento de +10 evita `log(0)` y reduce el sesgo para valores pequeños de NOB.

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **Metadata del repositorio** | Diccionario obtenido de la API de GitHub (GraphQL) o GHTorrent. Contiene `branches_count`: el conteo total de ramas del repositorio (`refs` con prefijo `refs/heads/`). |

### 3.2 Lógica del proceso

1. Se obtiene el conteo total de branches del repositorio (`nob_total`).
2. Opcionalmente, se aplica la normalización logarítmica de Jarczyk et al. (`normalizar_nob_jarczyk`) para obtener una versión menos sesgada del valor, útil para comparaciones entre repositorios de tamaños muy distintos.

### 3.3 Salida

| Salida | Qué representa |
|---|---|
| **NOB total** | Número entero: cantidad total de branches en el repositorio. |
| **NOB normalizado (Jarczyk)** | Número decimal: `log10(NOB + 10)`, versión normalizada del valor anterior. |

---

## 4. Salida Obtenida

**Repositorio analizado:** tldr-pages/tldr
**Período analizado:** 2025-08-07 → 2026-08-07

| Métrica | Valor |
|---|---|
| Number of Branches (NOB) | 22 |
| NOB normalizado (Jarczyk log10) | 1.5051 |

> El valor obtenido (22) coincide exactamente con el contador público de GitHub para `tldr-pages/tldr` ("22 Branches"), lo que valida el cálculo.

---

## 5. Referencias

- Jarczyk, O. et al. (2014). El número de branches como atributo más importante para la supervivencia (resolución) de bugs; propuesta de normalización logarítmica x' = log₁₀(x + 10).