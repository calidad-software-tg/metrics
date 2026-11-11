# 16 – DLOC (Documented Lines of Code)

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                 |
|---|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 18 - La calidad de la documentación                                                                                                                                         |
| **Métrica Original (ISL)** | Documentation Quality                                                                                                                                                       |
| **Métrica Canónica Más Cercana** | Quality of Support                                                                                                                                                          |
| **Métrica Adoptada / Calculable** | DLOC (Documented Lines of Code)                                                                                                                                             |
| **Dimensiones Asociadas** | Producto                                                                                                                                                                    |
| **Orden ISL** | TBD                                                                                                                                                                         |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

El **catálogo de 209 métricas** no contiene una métrica explícita denominada *"Documentation Quality"*.

La métrica canónica más cercana es **Quality of Support**, ya que en proyectos OSS la documentación es un componente fundamental del soporte brindado a usuarios y desarrolladores. Sin embargo:

- La correspondencia entre "Documentation Quality" y "Quality of Support" es **débil** y deberá **validarse posteriormente**.
- "Quality of Support" sigue siendo un concepto demasiado abstracto para calcularse directamente desde la metadata de un repositorio.

Por este motivo, se adopta como métrica **efectivamente calculable** a **DLOC**, que cuantifica de forma objetiva el volumen de documentación externa del proyecto, diferenciándola del código fuente ejecutable.

> **Conclusión de la sustitución:** DLOC se adopta como *proxy* operacional de Documentation Quality / Quality of Support, priorizando una medida cuantitativa y objetiva del volumen de material de soporte sobre un concepto de calidad de soporte más amplio y no directamente medible.

---

## 2. Definición de la Métrica

**DLOC (Documentation Lines of Code)** cuantifica la **cantidad total de líneas de documentación** contenidas en archivos externos al código fuente (`.md`, `.txt`, `.pdf`, entre otros).

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Producto** | Evalúa un atributo cuantitativo del repositorio como artefacto: el volumen total de material de documentación que lo acompaña, independientemente de quién lo generó o cuándo. |

### 2.2 Fundamento

La métrica busca medir de forma objetiva el **volumen de soporte técnico y documentación externa** del proyecto, diferenciándola explícitamente del código fuente ejecutable, con el fin de evaluar la exhaustividad del material de soporte disponible.

---

## 3. Cálculo

La función que implementa esta métrica recibe un único elemento de entrada y devuelve un número.

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **Colección de archivos** | Un listado de archivos del repositorio, cada uno con su nombre completo (incluyendo extensión) y su cantidad total de líneas (físicas o lógicas). |

### 3.2 Lógica del proceso

El cálculo define primero un conjunto de **extensiones consideradas documentación técnica** (`.md`, `.txt`, `.rst`, `.pdf`, `.doc`, `.docx`), es decir, archivos externos al código fuente ejecutable.

Luego recorre todos los archivos de la colección y, para cada uno, verifica si su nombre termina en alguna de esas extensiones. Cuando un archivo cumple ese criterio, se suman sus líneas al total acumulado.

Al finalizar el recorrido, ese total representa la cantidad agregada de líneas de documentación de todo el repositorio.

### 3.3 Salida

| Salida | Qué representa |
|---|---|
| **DLOC total** | Un número entero que indica la suma agregada de líneas de todos los archivos identificados estrictamente como documentación. |

En otras palabras: la métrica funciona como un **filtro por extensión + acumulador** — identifica qué archivos corresponden a documentación externa y suma su volumen total en líneas, dando una medida cruda del tamaño del material de soporte del proyecto.

---
## 4. Salida Obtenida

**Repositorio analizado:** calidad-software-tg/tldr (muestra de 500 archivos)

**Por producto (global):**

| Métrica | Valor |
|---|---|
| **DLOC** | 7.437 líneas |

**Por persona:**

| Colaborador | DLOC |
|---|---|
| Managor | 2.684 |
| danielbg14 | 1.185 |
| ivanbaluta | 570 |
| MachiavelliII | 552 |
| github-actions[bot] | 368 |
| nelsonfigueroa | 341 |
| Ninzero | 319 |
| FazleArefin | 251 |
| acuteenvy | 240 |
| sebastiaanspeck | 174 |
| ... | ... |

> Managor domina con casi el doble de líneas de documentación que el segundo colaborador. Resultado consistente con lo observado en otras métricas del mismo repositorio, donde aparece como el contribuidor más activo dentro de esta muestra.
---

## 5. Referencias

- Fuente de la métrica adoptada: Catálogo canónico 2022 (ver Ficha Técnica).