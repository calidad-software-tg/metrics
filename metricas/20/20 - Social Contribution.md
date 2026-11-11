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

## Social Contribution (métrica 20) — tldr-pages/tldr
**Período:** 2025-08-11 → 2026-08-11

**Resumen:**
- Issues en período: 275
- PRs en período: 5614
- Colaboradores únicos: 706

| Colaborador        | Issues | I.Cerr | PRs  | PR.Cerr | PR.Merge | SC   |
|---------------------|-------:|-------:|-----:|--------:|---------:|-----:|
| Managor             | 117    | 86     | 1025 | 12      | 1006     | 2246 |
| kant                | 0      | 0      | 610  | 19      | 575      | 1204 |
| nelsonfigueroa      | 0      | 0      | 401  | 1       | 400      | 802  |
| SpikeTheDragon40k   | 0      | 0      | 300  | 6       | 293      | 599  |
| dmmqz               | 11     | 8      | 230  | 2       | 228      | 479  |
| emmanuel-ferdman    | 2      | 0      | 228  | 2       | 225      | 457  |
| IMHOJEONG           | 0      | 0      | 213  | 2       | 198      | 413  |
| ivanbaluta          | 18     | 10     | 191  | 1       | 190      | 410  |
| sebastiaanspeck     | 3      | 2      | 99   | 3       | 96       | 203  |
| reinhart1010        | 3      | 0      | 80   | 1       | 77       | 161  |
| dependabot          | 0      | 0      | 78   | 1       | 77       | 156  |
| badhon495           | 0      | 0      | 76   | 1       | 75       | 152  |
| msaf9               | 3      | 1      | 64   | 4       | 60       | 132  |
| FazleArefin         | 1      | 1      | 65   | 1       | 64       | 132  |
| cyforkk             | 0      | 0      | 65   | 65      | 0        | 130  |
| acuteenvy           | 1      | 0      | 61   | 0       | 61       | 123  |
| znarfm              | 8      | 5      | 50   | 3       | 46       | 112  |
| TheRootDaemon       | 1      | 0      | 50   | 0       | 50       | 101  |

*[685 colaboradores más con SC entre 1-66]*

El top contributor es **Managor** con SC=2246, dominado por sus 1025 PRs (1006 mergeadas) y 117 issues. Los últimos 10 tienen SC=1 (solo 1 issue abierto sin cerrar o 1 PR sin mergear).
---
## 5. Referencias

- Falcão, R. et al. (2020). Definición de las cinco dimensiones de Social Contributions e influencia social en equipos de desarrollo (pág. 1385).
- Wu, Y. et al. Relación entre nivel de contribución, entendimiento del proyecto y calidad del autor.