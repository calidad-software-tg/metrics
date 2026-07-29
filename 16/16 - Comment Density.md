# 16 – Comment Density (CD)

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                 |
|---|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 18 - La calidad de la documentación                                                                                                                                         |
| **Métrica Original (ISL)** | Documentation Quality                                                                                                                                                       |
| **Métrica Canónica Más Cercana** | Quality of Support                                                                                                                                                          |
| **Métrica Adoptada / Calculable** | Comment Density (CD)                                                                                                                                                        |
| **Dimensiones Asociadas** | Producto, Persona                                                                                                                                                           |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

El **catálogo de 209 métricas** no contiene una métrica explícita denominada *"Documentation Quality"*.  La métrica canónica más cercana es **Quality of Support**, ya que en proyectos OSS la documentación es un componente fundamental del soporte brindado a usuarios y desarrolladores. Sin embargo:

- La correspondencia entre "Documentation Quality" y "Quality of Support" es **débil** y deberá **validarse posteriormente**.
- "Quality of Support" sigue siendo un concepto demasiado abstracto para calcularse directamente desde la metadata de un repositorio.

Por este motivo, se adopta como métrica **efectivamente calculable** a **Comment Density (CD)**, que opera como *proxy* concreto de la calidad interna de la documentación embebida en el código.

> **Conclusión de la sustitución:** CD se adopta como *proxy* operacional de Documentation Quality / Quality of Support, priorizando un indicador cuantificable a partir de análisis estático del código sobre un concepto de soporte más amplio y no directamente medible.

---

## 2. Definición de la Métrica

**Comment Density (CD)** mide la **relación entre las líneas de comentarios y las líneas totales de código** de un componente o archivo, funcionando como indicador de **calidad interna del producto**.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Producto** | Evalúa un atributo intrínseco del código fuente (proporción de documentación interna) a nivel de archivo o componente. |
| **Persona** | Permite comparar el hábito de documentar código entre distintos colaboradores, reflejando su estilo individual de trabajo. |

### 2.2 Fundamento Teórico

Según **Tosun et al. (2010)**, un ratio bajo de comentarios respecto al código indica un código difícil de mantener. Los estándares de la **NASA** sugieren, como referencia, un valor óptimo cercano a **0.15 (15%)**.

Las métricas base utilizadas en el cálculo —CLOC (líneas de comentarios) y LLOC (líneas lógicas de código ejecutable)— siguen las definiciones de **Bener et al. (2015)**, mientras que el algoritmo del ratio se apoya en el enfoque de **Gyimesi et al. (2015)**.

---

## 3. Cálculo

La función que implementa esta métrica recibe un único elemento de entrada y devuelve un número.

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **Metadata estática del archivo** | Un diccionario con datos obtenidos de herramientas de análisis estático (como SourceMeter o Understand), integradas con la API de GitHub. Contiene: `cloc` (líneas de comentarios), `lloc` (líneas lógicas de código ejecutable) y opcionalmente `loc` (líneas totales, para validación). |

### 3.2 Lógica del proceso

El cálculo extrae la cantidad de líneas de comentarios (CLOC) y la cantidad de líneas lógicas de código (LLOC) del archivo analizado.

Si el archivo no tiene código ejecutable (LLOC igual a cero), la densidad no es aplicable y se retorna 0.0, evitando una división inválida.

En caso contrario, se calcula el ratio dividiendo las líneas de comentarios por las líneas lógicas de código (**CD = CLOC / LLOC**), y el resultado se redondea a cuatro decimales.

> **Nota metodológica:** se utiliza LLOC (líneas lógicas) en lugar de LOC (líneas totales) porque evita sesgos introducidos por líneas en blanco, siguiendo el criterio de mayor precisión adoptado en la literatura.

### 3.3 Salida

| Salida | Qué representa |
|---|---|
| **Densidad de comentarios (CD)** | Un valor decimal, habitualmente entre 0.0 y 1.0, que representa la proporción de comentarios frente al código lógico ejecutable de un archivo. |

En otras palabras: la métrica funciona como un **ratio de proporción** — compara la cantidad de documentación interna (comentarios) contra la cantidad de código funcional, dando una medida directa de cuán documentado está un componente.

---
## 4. Salida Obtenida

**Repositorio analizado:** calidad-software-tg/tldr (28 archivos)

**Por producto (global):**

| Métrica | Valor |
|---|---|
| **CD** | 0.0616 — promedio ponderado sobre los 28 archivos |

**Por persona:**

| Colaborador | CD |
|---|---|
| acuteenvy | 0.2045 — supera el óptimo NASA (0.15) |
| kbdharun | 0.1105 |
| sebastiaanspeck | 0.0969 |
| waldyrious | 0.0549 |
| Managor | 0.0313 |
| dependabot[bot] | 0.0271 |
| RuinTD | 0.0145 |
| vitorhcl | 0.0096 |

> El valor global (0.0616) es el promedio ponderado de los 8 colaboradores sobre los mismos 28 archivos, resultado consistente entre ambos modos de

## 5. Referencias

- Tosun, A., Bener, A., & Turhan, B. (2010). *An industrial case study of classifier ensembles for locating software defects*.
- Bener, A. et al. (2015). Definiciones de métricas base CLOC/LLOC.
- Gyimesi, P. et al. (2015). Enfoque de cálculo de ratios de densidad de comentarios.
- Estándares de calidad de código de la NASA (valor de referencia ≈ 0.15).