# 18 – Doc Issue Survival

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                 |
|---|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 18 - La calidad de la documentación                                                                                                                                         |
| **Métrica Original (ISL)** | Documentation Quality                                                                                                                   |
| **Métrica Canónica Más Cercana** | Quality of Support                                                                                                     |
| **Métrica Adoptada / Calculable** | Doc Issue Survival                                                                                                                                                          |
| **Dimensiones Asociadas** | Proceso                                                                                                                                                                     |
| **Orden ISL** | TBD                                                                                                                                                                         |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

El **catálogo de 209 métricas** no contiene una métrica explícita denominada *"Documentation Quality"*.

La métrica canónica más cercana es **Quality of Support**, ya que en proyectos OSS la documentación es un componente fundamental del soporte brindado a usuarios y desarrolladores. Sin embargo:

- La correspondencia entre "Documentation Quality" y "Quality of Support" es **débil** y deberá **validarse posteriormente**.
- "Quality of Support" sigue siendo un concepto demasiado abstracto para calcularse directamente desde la metadata de un repositorio.

Por este motivo, se adopta como métrica **efectivamente calculable** a **Doc Issue Survival**, que mide el tiempo que permanecen abiertos los problemas categorizados como documentación en el tracker del proyecto.

> **Conclusión de la sustitución:** Doc Issue Survival se adopta como *proxy* operacional de Documentation Quality / Quality of Support, priorizando la velocidad de atención del equipo a los issues de documentación como indicador indirecto de la prioridad e importancia que se le asigna a este tipo de soporte.

---

## 2. Definición de la Métrica

**Doc Issue Survival** mide el **tiempo promedio (en días) que permanecen abiertos** los issues categorizados específicamente como problemas de documentación, desde su apertura hasta su cierre.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Proceso** | Mide la eficiencia del equipo para atender y cerrar issues de documentación, reflejando la prioridad asignada a este tipo de soporte y la madurez del flujo de trabajo. |

### 2.2 Fundamento Teórico

La identificación de issues de documentación mediante etiquetas se apoya en criterios utilizados en la literatura por **Jarczyk** y **Bissyandé**, quienes analizan el etiquetado de issues como mecanismo para categorizar el tipo de trabajo pendiente en proyectos OSS.

---

## 3. Cálculo

La función que implementa esta métrica recibe un único elemento de entrada y devuelve un número.

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **Colección de issues** | Un listado de issues de GitHub, cada uno con sus etiquetas (`labels`), su fecha de apertura y su fecha de cierre (o ausencia de ella si sigue abierto). |

### 3.2 Lógica del proceso

El cálculo recorre todos los issues de la colección y, para cada uno, normaliza sus etiquetas (a minúsculas) para identificar si corresponde a la categoría de documentación, comparándolas contra un conjunto de palabras clave (*doc, documentation, docs, documentación*).

Para los issues identificados como de documentación que además tienen tanto fecha de apertura como de cierre, se calcula cuántos días transcurrieron entre ambos eventos. Esa duración se acumula, junto con un contador de cuántos issues de documentación fueron efectivamente cerrados.

Al finalizar el recorrido, se divide el total de días acumulados por la cantidad de issues de documentación cerrados, obteniendo el **tiempo promedio de supervivencia**.

Si no se encontró ningún issue de documentación cerrado en la muestra, el resultado es 0.0.

### 3.3 Salida

| Salida | Qué representa |
|---|---|
| **Promedio de supervivencia (días)** | Un valor decimal que indica, en promedio, cuántos días permanecen abiertos los issues de documentación antes de ser cerrados. |

En otras palabras: la métrica funciona como un **filtro por etiqueta + análisis de supervivencia** — aísla los issues relacionados con documentación y mide cuánto tiempo tardan en resolverse, sirviendo como indicador indirecto de la atención que recibe la documentación dentro del flujo de trabajo del equipo.

---
## 4. Salida Obtenida
**Resultado de la última ejecución:** `0`

Este valor se debe a que el repositorio tldr de entrada no contiene issues reales.

## 5. Referencias

- Jarczyk, O. et al. Etiquetado y categorización de issues en repositorios de GitHub.
- Bissyandé, T. F. et al. Análisis de issues y su clasificación por tipo de trabajo en proyectos OSS.