# 10 – Average Number of Modified Components per Commit (ANMCC)

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                 |
|---|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 52 - La utilización eficiente de recursos                                                                                                                                   |
| **Métrica Original (ISL)** | CPU Usage                                                                                                                                                                   |
| **Métrica Adoptada** | Average Number of Modified Components per Commit (ANMCC)                                                                                                                    |
| **Dimensiones Asociadas** | Producto, Proceso                                                                                                                                                           |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

El **catálogo canónico de 2022** no contiene una métrica explícita de *uso de recursos computacionales* (CPU Usage, Processor Utilization, etc.), ya que este tipo de indicador requiere instrumentación en tiempo de ejecución que excede el alcance de la metadata típicamente disponible en repositorios de control de versiones.

La métrica más cercana disponible en dicho catálogo es **Average Number of Modified Components per Commit (ANMCC)**, ya que:

- Refleja la **eficiencia en la modularidad** del proyecto, un factor que impacta indirectamente en el uso de recursos (cambios más acotados y modulares suelen implicar menor sobrecarga de recompilación, testing y despliegue).
- **No mide consumo real de CPU o procesador**, sino un *proxy* estructural basado en la cantidad de componentes (archivos) tocados por cada commit.

> **Conclusión de la sustitución:** ANMCC se adopta como *proxy* de CPU Usage / Processor Utilization, priorizando la eficiencia estructural del cambio (modularidad) sobre la medición directa del consumo de recursos de cómputo.

---

## 2. Definición de la Métrica

**Average Number of Modified Components per Commit (ANMCC)** cuantifica el **promedio de componentes (archivos) modificados por cada commit**, extraído directamente de la metadata de los commits.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Producto** | Refleja la modularidad del código: commits que tocan pocos componentes sugieren un diseño más desacoplado y cohesivo. |
| **Proceso** | Refleja la granularidad con la que el equipo estructura sus cambios dentro del flujo de trabajo de desarrollo. |

### 2.2 Fundamento

La métrica se extrae **directamente de la metadata de los commits** (sin necesidad de instrumentación adicional) y funciona como indicador de **eficiencia en la modularidad**: cuanto menor es el promedio de componentes modificados por commit, más acotados y focalizados son los cambios, lo cual típicamente se asocia a menor complejidad de integración y menor sobrecarga en los ciclos de build/test.

---

## 3. Cálculo

La función que implementa esta métrica recibe un único elemento de entrada y devuelve un número.

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **Colección de commits** | Un listado de commits extraídos de la metadata del repositorio. |

### 3.2 Lógica del proceso

El cálculo recorre todos los commits de la colección y, para cada uno, cuenta cuántos componentes (archivos) fueron modificados. Esos conteos individuales se van acumulando en un total.

Al finalizar el recorrido, ese total se divide por la cantidad de commits analizados, obteniendo así el **promedio** de componentes modificados por commit.

### 3.3 Salida

| Salida | Qué representa |
|---|---|
| **Promedio de componentes modificados** | Un número que indica, en promedio, cuántos archivos distintos se modifican por cada commit dentro de la colección analizada. |

En otras palabras: la métrica funciona como un promedio — suma la cantidad de componentes tocados en cada commit y divide ese total por la cantidad de commits, obteniendo así una medida de granularidad promedio del cambio.

---

## 4. Salida Obtenida
## 4. Salida Obtenida

**Por producto:**

| Métrica | Valor |
|---|---|
| **ANMCC** | 8.29 — en promedio cada commit toca 8.29 archivos |

**Por persona (top colaboradores):**

| Colaborador | ANMCC |
|---|---|
| github-actions[bot] | 330.75 |
| Rickyxrc | 29.0 |
| axrona | 26.0 |
| Managor | 24.36 |
| sebastiaanspeck | 14.74 |
| nelsonfigueroa | 7.08 |
| ... | ... |

---

## 5. Referencias

- Fuente de la métrica adoptada: Catálogo canónico 2022 (ver Ficha Técnica).