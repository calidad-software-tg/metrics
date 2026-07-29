# 35 – Number of Closed Issues (NCI)

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                 |
|---|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 21 - Tiempo promedio de resolución de issues                                                                                                                                |
| **Métrica Original (ISL)** | Issue Resolution Time                                                                                                                                                       |
| **Métrica Adoptada** | Number of Closed Issues (NCI)                                                                                                                                               |
| **Dimensiones Asociadas** | Persona, Proceso                                                                                                                                                            |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

El **catálogo canónico de 2022** no contiene una métrica explícita de *tiempo de resolución* (Issue Resolution Time, Mean Time to Resolve Issues, etc.).

La métrica más cercana disponible en dicho catálogo es **Number of Closed Issues (NCI)**, ya que:

- Refleja la **capacidad de resolución** del equipo.
-  **No incorpora la dimensión temporal** (no mide cuánto tiempo tardó cada issue en resolverse, solo cuántos se resolvieron).

> **Conclusión de la sustitución:** NCI se adopta como *proxy* de Issue Resolution Time, priorizando volumen de resolución sobre velocidad de resolución.

---

## 2. Definición de la Métrica

**Number of Closed Issues (NCI)** cuantifica el **volumen de problemas (issues) y pull requests resueltos** dentro de un período de tiempo determinado.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Proceso** | Mide productividad y rendimiento del equipo (*throughput*) durante el flujo de trabajo. |
| **Persona** | Refleja el desempeño de los integradores/colaboradores que cierran los ítems. |

### 2.2 Fundamento Teórico

Según **Vasilescu et al. (2015)**, en el modelo de desarrollo basado en *pull requests*:

> La capacidad de los integradores para procesar y cerrar unidades de trabajo (ya sean Pull Requests o Issues técnicos) es un indicador clave de productividad, y se ve afectado por la práctica de Integración Continua (CI).

---

## 3. Cálculo

La función que implementa esta métrica recibe tres elementos de entrada y devuelve un único número.

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **Colección de issues/PRs** | Un listado de ítems (issues o pull requests) extraídos de GitHub API o GHTorrent. Cada ítem trae, entre otros datos, su número identificador, su estado (abierto/cerrado) y, si corresponde, la fecha en la que fue cerrado. |
| **Fecha de inicio** | El límite inferior de la ventana temporal que se quiere analizar (por ejemplo, el primer día de un mes). |
| **Fecha de fin** | El límite superior de esa misma ventana (por ejemplo, el último día de ese mes). |

### 3.2 Lógica del proceso

El cálculo recorre uno por uno todos los ítems de la colección y evalúa dos condiciones para decidir si ese ítem "cuenta" como cerrado dentro del período analizado:

1. **¿El ítem tiene fecha de cierre?** Si nunca se cerró (sigue abierto), no se contabiliza.
2. **¿Esa fecha de cierre cae dentro de la ventana de observación?** Aunque el ítem esté cerrado, solo se contabiliza si el cierre ocurrió entre la fecha de inicio y la fecha de fin definidas.

Cada vez que un ítem cumple ambas condiciones, se suma al contador total. Al terminar de recorrer toda la colección, ese contador es el resultado final.

### 3.3 Salida

| Salida | Qué representa |
|---|---|
| **Total de cerrados** | Un número entero que indica cuántos issues/PRs alcanzaron un estado terminal (cerrado o fusionado) durante el período especificado. |

En otras palabras: la métrica funciona como un **filtro + contador** — filtra los ítems que fueron cerrados dentro de la ventana temporal deseada, y cuenta cuántos quedaron después de ese filtro.

---

## 4. Salida Obtenida

**Resultado de la última ejecución:** `0`

Este valor se debe a que el repositorio tldr de entrada no contiene issues ni pull requests reales.

## 5. Referencias

- Vasilescu, B., Yu, Y., Wang, H., Devanbu, P., & Filkov, V. (2015). *Quality and productivity outcomes relating to continuous integration in GitHub*. Proceedings of the 2015 10th Joint Meeting on Foundations of Software Engineering.