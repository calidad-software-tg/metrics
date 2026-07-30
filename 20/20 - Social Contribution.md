# 20 – Social Contribution

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                |
|---|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 11 - La contribución a proyectos en su mismo equipo de trabajo                                                                                                             |
| **Métrica Original (ISL)** | Contribution to team projects / Team Contribution (alt.: Intra-team project contribution)                                                                                  |
| **Métrica Canónica JAIIO 2022** | Developer Contribution                                                                                                                                                     |
| **Métrica Adoptada / Calculable** | Social Contribution                                                                                                                                                        |
| **Dimensiones Asociadas** | Persona, Proceso                                                                                                                                                           |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

La consigna se refiere directamente al **aporte realizado por una persona dentro de los proyectos de su equipo**. Dentro del catálogo de 209 métricas, **Developer Contribution** es la correspondencia conceptual más directa y específica; no se identificó una métrica alternativa con mejor ajuste semántico.

Sin embargo, se detecta una **discrepancia** entre lo catalogado y lo efectivamente calculable:

- El nombre canónico **"Developer Contribution (DC)"** fue descripto originalmente como una métrica que opera sobre **líneas de código modificadas en commits**.
- La función provista para el cálculo corresponde en realidad a **Social Contributions (SC)**, según la definición de **Falcão et al. (2020)**, que mide la participación del desarrollador en la **gestión del ciclo de vida de issues y Pull Requests**, no en volumen de código modificado.

> **Conclusión de la sustitución:** se documenta y adopta la métrica efectivamente calculable, **Social Contributions (SC)**, dejando constancia de que su nombre difiere del originalmente catalogado como "Developer Contribution" y que esta discrepancia deberá validarse posteriormente.

---

## 2. Definición de la Métrica

**Social Contributions (SC)** cuantifica el **nivel de participación de un desarrollador en la gestión del ciclo de vida de los artefactos de discusión** (Issues y Pull Requests) dentro de un repositorio.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Persona** | Mide la actividad individual de un desarrollador específico dentro del proyecto. |
| **Proceso** | Captura su participación en el flujo de trabajo de gestión de issues y PRs (apertura, cierre, fusión). |

### 2.2 Fundamento Teórico

Según **Falcão et al. (2020)**, esta métrica representa la **influencia social** y la **capacidad del autor para estructurar el trabajo del equipo "quirúrgico"** (equipo reducido y altamente coordinado). Se compone de cinco dimensiones de actividad definidas por los autores.

Adicionalmente, según **Wu et al.**, una mayor contribución suele correlacionar con un mejor entendimiento del proyecto y una mayor calidad por parte del autor.

---

## 3. Cálculo

La función que implementa esta métrica recibe un único elemento de entrada y devuelve un número.

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **Metadata del usuario en el repositorio** | Un diccionario con conteos agregados de la actividad del usuario, obtenidos de la API de GitHub o GHTorrent. Contiene: `issues_opened` (issues creados), `issues_opened_closed` (issues propios ya cerrados), `prs_opened` (Pull Requests iniciadas), `prs_opened_closed` (PRs propias cerradas sin fusionar) y `prs_opened_merged` (PRs propias fusionadas). |

### 3.2 Lógica del proceso

El cálculo extrae cinco componentes de actividad del desarrollador: issues abiertos, issues propios resueltos, PRs abiertas, PRs rechazadas (cerradas sin fusionar) y PRs fusionadas.

Estos cinco valores se suman directamente para obtener un único indicador agregado de contribución social, sin ponderaciones diferenciales entre componentes.

### 3.3 Salida

| Salida | Qué representa |
|---|---|
| **Contribuciones Sociales (SC) total** | Un número entero que representa la suma escalar de todas las acciones de contribución social y gestión del flujo de trabajo del desarrollador. |

En otras palabras: la métrica funciona como un **agregador de actividad** — suma distintas formas de participación de un desarrollador en la gestión de issues y PRs, dando un único valor que resume su nivel de involucramiento con el trabajo del equipo.

---
## 4. Salida Obtenida

**Repositorio analizado:** tldr-pages/tldr

**Volumen general en el período:**

| Métrica | Valor |
|---|---|
| Issues en período | 278 |
| PRs en período | 5.704 |
| Contribuidores únicos | ~700+ |

**Top 5 colaboradores por Social Contributions (SC):**

| Colaborador | Issues | Issues Cerrados | PRs | PRs Cerradas | PRs Fusionadas | SC |
|---|---|---|---|---|---|---|
| Managor | 116 | 86 | 1093 | 12 | 1076 | 2383 |
| kant | 0 | 0 | 602 | 19 | 581 | 1202 |
| nelsonfigueroa | 0 | 0 | 401 | 1 | 400 | 802 |
| SpikeTheDragon40k | 0 | 0 | 301 | 6 | 294 | 601 |
| dmmqz | 11 | 8 | 240 | 2 | 238 | 499 |

> La mayoría de los contribuidores tiene SC = 2 (un PR fusionado o un issue cerrado). La distribución presenta una cola muy larga: un pequeño grupo de colaboradores concentra la mayor parte de la actividad, mientras que el resto son contribuidores ocasionales (*one-time contributors*).
---
## 5. Referencias

- Falcão, R. et al. (2020). Definición de las cinco dimensiones de Social Contributions e influencia social en equipos de desarrollo (pág. 1385).
- Wu, Y. et al. Relación entre nivel de contribución, entendimiento del proyecto y calidad del autor.