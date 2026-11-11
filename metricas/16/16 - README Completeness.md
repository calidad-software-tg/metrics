# 16 – README Completeness

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                 |
|---|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 18 - La calidad de la documentación                                                                                                                                         |
| **Métrica Original (ISL)** | Documentation Quality                                                                                                         |
| **Métrica Canónica Más Cercana** | Quality of Support                                                                                        |
| **Métrica Adoptada / Calculable** | README Completeness                                                                                                                                                         |
| **Dimensiones Asociadas** | Producto, Proceso                                                                                                                                                           |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

El **catálogo de 209 métricas** no contiene una métrica explícita denominada *"Documentation Quality"*.

La métrica canónica más cercana es **Quality of Support**, ya que en proyectos OSS la documentación es un componente fundamental del soporte brindado a usuarios y desarrolladores. Sin embargo:

- La correspondencia entre "Documentation Quality" y "Quality of Support" es **débil** y deberá **validarse posteriormente**.
- "Quality of Support" sigue siendo un concepto demasiado abstracto para calcularse directamente desde la metadata de un repositorio.

Por este motivo, se adopta como métrica **efectivamente calculable** a **README Completeness**, que opera como *proxy* concreto de la calidad de la documentación inicial de un proyecto, evaluando la presencia de secciones esenciales en el archivo README.

> **Conclusión de la sustitución:** README Completeness se adopta como *proxy* operacional de Documentation Quality / Quality of Support, priorizando un indicador cuantificable a partir del contenido textual del README sobre un concepto de soporte más amplio y no directamente medible.

---

## 2. Definición de la Métrica

**README Completeness** evalúa el nivel de completitud del archivo README de un repositorio, basándose en la **presencia de secciones esenciales** (por ejemplo: instalación, uso, licencia, contribución, entre otras).

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Producto** | Evalúa un atributo intrínseco del repositorio: la calidad y completitud de su documentación inicial como artefacto. |
| **Proceso** | Refleja prácticas de documentación adoptadas por el equipo a lo largo del desarrollo del proyecto (mantener el README actualizado y completo). |

### 2.2 Fundamento Teórico

La métrica se basa en las **8 categorías de contenido** identificadas por **Prana et al. (2018)** para README de proyectos open source, junto con el esquema de codificación propuesto por **Jarczyk et al.**, y las **recomendaciones oficiales de GitHub** para proyectos maduros.

---

## 3. Cálculo

La función que implementa esta métrica recibe un único elemento de entrada y devuelve un número.

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **Contenido del README** | El texto plano extraído del archivo `README.md` del repositorio. |

### 3.2 Lógica del proceso

El cálculo primero verifica que el README exista y tenga contenido mínimo; si está vacío o es demasiado corto, se considera que no hay documentación evaluable y el resultado es 0.0.

Luego, se define un conjunto de **siete categorías esenciales** de contenido (qué es el proyecto, por qué existe, cómo usarlo, cuándo/estado del proyecto, quién lo mantiene, referencias adicionales y cómo contribuir), cada una asociada a un grupo de palabras clave representativas.

El texto del README se recorre buscando, para cada categoría, si al menos una de sus palabras clave está presente. Cada categoría detectada se suma a un contador.

Finalmente, se calcula la proporción de categorías detectadas sobre el total de categorías esperadas, obteniendo así el índice de completitud.

### 3.3 Salida

| Salida | Qué representa |
|---|---|
| **Índice de completitud** | Un valor decimal entre 0.0 y 1.0 que representa el porcentaje de secciones esenciales detectadas en el README. |

En otras palabras: la métrica funciona como una **checklist ponderada** — verifica la presencia de un conjunto estándar de secciones de documentación y expresa el resultado como proporción de cobertura.

---
## 4. Salida Obtenida

**Repositorio analizado:** calidad-software-tg/tldr (3 READMEs encontrados)

**Por producto (global):**

| Métrica | Valor |
|---|---|
| **RC** | 0.5714 — cubre 4 de 7 secciones (Prana et al.) |

**Por persona:**

| Colaborador | RC |
|---|---|
| Managor | 0.8571 (6/7) |
| sebastiaanspeck | 0.4286 (3/7) |
| kbdharun | 0.4286 (3/7) |

> Managor tiene el README más completo. El promedio de 0.57 indica que el repo cubre más de la mitad de las secciones recomendadas, aunque le faltan algunas (probablemente "When"/"References").
---

## 5. Referencias

- Prana, G. A. A. et al. (2018). Esquema de las 8 categorías de contenido esencial en README de proyectos OSS.
- Jarczyk, O. et al. Esquema de codificación de contenido de documentación en repositorios.
- Recomendaciones oficiales de GitHub para documentación de proyectos maduros.