# Selección de repositorio — estudio longitudinal 3P (Producto, Persona, Proceso)

---

## 1. Ranking final

| # | Repo | Estado                      | Motivo resumido                                                                                                            |
|---|---|-----------------------------|----------------------------------------------------------------------------------------------------------------------------|
| 1 | **VS Code / Code-OSS** | **Elegido**                 | Único candidato sin problema de delimitación de Producto, homogéneo en lenguaje y con adopción tecnológica real y fechable |
| 2 | CPython | Finalista del director      | Exige normalizar C/Python a un lenguaje para algunas metricas                                                              |
| 3 | Next.js | Elegible                    | Mejor historia de adopción tecnológica de los 10                                                                           |
| 4 | Home Assistant Core | Finalista del director      | Problema serio de delimitación de Producto (~1000 integraciones con dueños que no colaboran)                               |
| 5 | TensorFlow | Elegible                    | El más heterogéneo en lenguajes de los 10                                                                                  |
| 6 | Flutter | Elegible   | Releases mal etiquetadas + colaboradores top son bots                                                                      |
| 7 | GIMP (GitLab) | En observación              | Costo operativo: pipeline actual solo soporta GitHub                                                                       |
| 8 | raylib | Excluido por el director    | Bus factor de 1 (67% de los commits de una persona)                                                                        |
| 9 | tldr-pages/tldr | Excluido (elección original) | Es documentación, no software ejecutable                                                                                   |
| 10 | freeCodeCamp | En observación              | 92% del repo es contenido curricular, no código; 0 releases/tags                                                           |

---

## 2. Tabla de tamaño y actividad

| # | Repo | Tamaño | Commits | Contribuyentes | Issues abiertas | Releases / Tags |
|---|---|---|---|---|---|---|
| 1 | VS Code / Code-OSS | 1.46 GB | 165,345 | 3,235 | 21,138 | 239 / 390 |
| 2 | CPython | 855 MB | 133,194 | 4,040 | 9,638 | 0 (no usa Releases) / 668 |
| 3 | Next.js | 2.5 GB | 35,676 | 4,154 | 3,362 | 3,849 / 4,051 |
| 4 | Home Assistant Core | 876 MB | 116,895 | 5,815 | 3,531 | 1,644 / 1,645 |
| 5 | TensorFlow | 1.35 GB | 198,969 | 5,318 | 3,146 | 222 / 226 |
| 6 | Flutter | 461 MB | 91,537 | 2,406 | 13,176 | 7 (mal etiquetadas) / 1,115 |
| 7 | GIMP (GitLab) | — | — | — | — | 31 / 292 |
| 8 | raylib | 411 MB | 10,163 | 1,018 | 13 | 25 / 25 |
| 9 | tldr-pages/tldr | 63 MB | 23,752 | 3,478 | 270 | 6 / 11 |
| 10 | freeCodeCamp | 567 MB | 42,630 | 6,813 | 207 | **0** / **0** |

**Lenguaje dominante y homogeneidad:**

| Repo | Lenguajes (top) |
|---|---|
| VS Code | TypeScript 96% + Rust (CLI, evento de adopción fechable) + 40 lenguajes menores |
| CPython | Python 61% / C 34% |
| Next.js | JavaScript 46% / TypeScript 31% / Rust 13% (compilador SWC) |
| Home Assistant | Python 99.99% |
| TensorFlow | C++ 58% / Python 26% / MLIR 7% / Starlark 5% + Go/Java/Swift |
| Flutter | Dart 69% / C++ 15% + Java/ObjC/Kotlin/Swift/Python |
| raylib | C (single-language) |
| tldr | Markdown 99.5% |
| freeCodeCamp | curriculum (JSON/MD) 92% de archivos; `client/`+`api/` = JS/TS real |

**Concentración del top contribuyente** (riesgo de bus factor):

| Repo | Top contributor | % del total de commits |
|---|---|---|
| VS Code | bpasero | 8.9% |
| Next.js | ijjk | 9.2% |
| CPython | gvanrossum | 8.5% |
| Home Assistant | balloob | 7.8% |
| tldr | Managor | 8.0% |
| **raylib** | **raysan5** | **67%** ⚠️ bus factor 1 |
| **Flutter** | **skia-flutter-autoroll (bot)** | top-1 y top-2 son bots, no personas ⚠️ |

**Features de GitHub relevantes para métricas** (`has_wiki`, `has_discussions`):

| Repo | Wiki | Discussions (nativo GitHub) |
|---|---|---|
| tldr | Sí | Sí |
| Flutter | Sí | No |
| Home Assistant | No | No |
| VS Code | Sí | No |
| freeCodeCamp | No | No |
| Next.js | No | Sí |
| TensorFlow | No | No |
| CPython | No | No |
| raylib | Sí | Sí |
| GIMP | — (GitLab, no aplica el mismo campo) | — |

> **Corrección metodológica importante:** `has_wiki=False` no significa que la métrica **Wiki Presence** no se pueda calcular — es una métrica binaria por diseño (Jarczyk et al., 2014) y da `0` como resultado válido. Tampoco **Discussion Centrality** depende de `has_discussions` — se calcula a partir de comentarios en issues/PRs/commits (co-participación en hilos), no de la feature nativa "Discussions". En la práctica, ninguno de los 10 repos queda sin poder calcular estas dos métricas; en la mayoría simplemente da `0` en Wiki Presence.

---

## 3. Nota metodológica: homogeneidad de lenguajes — favorece a unas métricas, perjudica a otras

No conviene optimizar la elección de repo por "más homogéneo = mejor" en abstracto. Hay dos grupos de métricas que tiran en direcciones opuestas:

**Grupo A — necesitan un solo lenguaje dominante** (el cociente/comparación pierde sentido si mezclás convenciones de distintos lenguajes):
Comment Density, Documented Lines of Code, Average Number of Modified Components per Commit, REXP, REXPRev, EXPRev, FEXP, Skill Similarity.
→ Mejor caso: Home Assistant (99.99% Python). Peor caso: TensorFlow, CPython.

**Grupo B — necesitan variedad o cambio tecnológico a lo largo del tiempo** (la fórmula es `nuevas_tecnologías / tiempo`):
Development Experience, usada como proxy operacional de la Consigna 29 ("adopción de nuevas tecnologías" — el catálogo de 209 métricas no tiene una métrica explícita para esto).
→ Mejor caso: repos con un evento de adopción real, fechado y trazable en su historia de commits — VS Code (CLI en Rust, 64 commits de historia), Next.js (compilador reescrito en Rust), CPython (JIT, no-GIL). Peor caso: Home Assistant y tldr (nunca cambiaron de lenguaje — cero señal, mismo problema que ya documentó el equipo para tldr en `38/38 – Development Experience.md`).

**Conclusión práctica:** el repo ideal no es el más homogéneo ni el más heterogéneo — es uno mayormente monolenguaje (bueno para el Grupo A) que además tenga al menos un evento de adopción tecnológica real y acotado (bueno para el Grupo B). VS Code es el único que cumple ambas condiciones a la vez.

---

## 4. Análisis por candidato

### 1. VS Code / Code-OSS — ELEGIDO

**Pros:** un solo lenguaje dominante (TypeScript 96%), sin fragmentación de dueños (a diferencia de Home Assistant, las 97 extensiones incluidas las gobierna el mismo equipo — `CODEOWNERS` no tiene entradas individuales para `extensions/*`), caso real y fechable de adopción de tecnología nueva (CLI en Rust, 64 commits de historia), comunidad sana (nadie pasa el 9% de los commits), releases regulares y bien etiquetadas.

**Contras:**
- Aclarar en la tesis que se analiza "Code-OSS", el repo abierto, no la distribución empaquetada de Microsoft.
- Definir el alcance de `extensions/` (37% del código: 88 MB de 238 MB con `src/`). No es todo-o-nada: extensiones como `git` usan 34 APIs internas/propuestas no disponibles a terceros (funcionalmente parte del core), mientras que otras como `css-language-features` usan solo la API pública (equivalentes a un plugin de tercero). Proxy sugerido para clasificar: presencia/ausencia de `enabledApiProposals` en el `package.json` de cada extensión.

**Métricas que no aplican:** ninguna por falta de datos — tiene wiki activa (Wiki Presence = 1) y volumen de comentarios más que suficiente para Discussion Centrality.

**Riesgos operativos detectados en el diseño de bloques temporales** (ver sección 6): tres quiebres estructurales (flujo de PRs 2022, `state_reason` desde 2022, cadencia semanal desde marzo 2026) y posible contaminación de bots/agentes de código en la aceleración de commits de 2026 — todos manejables, ninguno descalifica al candidato.

---

### 2. CPython

**Pros:** el mejor documentado de los diez (PEPs, proceso formal de decisión), sin dueños concentrados (gvanrossum 8.5%), casos de adopción tecnológica muy documentados y fechables por versión (JIT experimental desde 3.13, modo free-threading/no-GIL desde 3.13, specializing adaptive interpreter desde 3.11).

**Contras:** 61% Python / 34% C — hay que decidir si se normalizan juntas o se reportan por separado las métricas de código; no usa la feature "Releases" de GitHub, hay que filtrar tags por patrón (`vX.Y.Z` exacto vs. sufijos `a`/`b`/`rc`) en vez de un flag booleano confiable.

**Métricas que no aplican:** ninguna por falta de datos — `has_wiki=False` da Wiki Presence = 0 (válido); Discussion Centrality se calcula con comentarios de issues/PRs igual.

---

### 3. Next.js (candidato fuerte, no fue finalista del director)

**Pros:** filtro de estable/prerelease confiable vía la API (a diferencia de Flutter), la mejor historia de adopción tecnológica de los diez — reescribieron el compilador (SWC) en Rust, 13% del código actual — comunidad sana (ijjk 9.2%).

**Contras:** 87% de los releases recientes son canary/prerelease (mucho ruido a filtrar, aunque el flag de la API es confiable), un bot (`vercel-release-bot`) aparece entre los top contribuyentes y contamina el conteo de Personas si no se filtra.

**Métricas que no aplican:** ninguna por falta de datos — `has_wiki=False` da Wiki Presence = 0 (válido); tiene Discussions activado además.

**Nota:** queda como plan B si VS Code encuentra un bloqueo real en el piloto de calculabilidad.

---

### 4. Home Assistant Core (favorito original del informe del director)

**Pros:** 99.99% un solo lenguaje (Python) — el mejor caso posible para las métricas del Grupo A; releases mensuales con flag `prerelease` nativo y confiable; comunidad grande y repartida (balloob 7.8%).

**Contras — el más grave de los diez candidatos viables:** no es "un producto", son ~1000 integraciones casi independientes en `homeassistant/components/` (999 carpetas), de las cuales **855 tienen un solo dueño** en `CODEOWNERS`. Ejemplo concreto: la integración `hue` tiene 20 archivos y 90 KB; `3_day_blinds` tiene 1 archivo y 125 bytes — ambas cuentan igual como "una integración". Antes de medir nada hay que decidir si el Producto es todo el repo o solo el núcleo compartido, y esa decisión cambia el denominador de casi todas las métricas de Producto y Persona. Tampoco tiene ningún evento de adopción tecnológica real por ser mono-lenguaje desde siempre (Grupo B = señal nula).

**Métricas que no aplican por falta de datos:** ninguna (Wiki Presence = 0 válido, Discussion Centrality se calcula con comentarios).
**Métricas en duda por el problema de delimitación** (no por falta de dato, sino porque el resultado depende de una decisión de alcance no tomada): Comment Density, Documented LOC, Contribution Diversity, Average Modified Components per Commit.

---

### 5. TensorFlow

**Pros:** producto de software inequívoco, comunidad amplia (5,318 contribuyentes).

**Contras:** el repo más heterogéneo en lenguajes de los diez — C++ 58%, Python 26%, MLIR 7% (un lenguaje intermedio propio), Starlark 5% (lenguaje de configuración de build de Bazel), más Go/Java/Swift/Objective-C en menor medida. Peor que CPython en el mismo eje que ya complicaba a CPython.

**Métricas que no aplican:** ninguna por falta de datos (mismas correcciones de Wiki/Discussion Centrality). Sí quedan complicadas por la heterogeneidad: Comment Density, Documented LOC, y cualquier métrica de Producto que asuma un lenguaje único.

---

### 6. Flutter

**Pros:** producto de software claro, casos reales de adopción tecnológica (motor de renderizado Impeller, soporte Fuchsia).

**Contras:**
- Las versiones que la propia API marca como no-prerelease llevan el sufijo `-0.1.pre` en el nombre (ej. `3.19.0-0.1.pre`) — el filtro automático `prerelease:false/true` **no es confiable** acá, a diferencia de Home Assistant, VS Code o Next.js.
- Los dos colaboradores con más commits son bots de automatización (`skia-flutter-autoroll`: 18,512 commits; `engine-flutter-autoroll`: 14,160 commits) — superan a cualquier persona real. Cualquier métrica de Personas arranca contaminada si no se filtran antes.

**Métricas que no aplican / en riesgo:** ninguna por falta de datos duros, pero Discussion Centrality y Number of Comments quedan en riesgo de contaminación por bots (mismo mecanismo que infló a `CLAassistant`/`tldr-bot` en tldr); Schedule Compliance en riesgo por el etiquetado poco confiable de versiones; Contribution Diversity/REXP en riesgo si no se filtran los bots primero.

---

### 7. GIMP (GitLab)

**Pros:** producto de software válido, dominio claro y acotado (editor de imágenes).

**Contras:** está en GitLab, no GitHub. El pipeline actual del proyecto (`run_batch_anmcc.py:175`) filtra explícitamente `WHERE plataforma = 'GitHub'` — GIMP queda excluido del batch runner tal como está hoy, aunque figure en el seed de repos. Habría que construir un conector aparte (la API de GitLab tiene semántica distinta: merge requests en vez de PRs, endpoints de releases/tags diferentes).

**Métricas que no aplican:** prácticamente todas, hasta no adaptar la extracción de datos a la API de GitLab.

---

### 8. raylib (excluido por el director)

**Pros:** producto de software limpio (C), bien documentado, wiki y discussions activados.

**Contras:** un solo autor (`raysan5`) concentra el 67% de los 10,163 commits — bus factor de 1, la comunidad alrededor reporta issues pero no codesarrolla; solo 25 releases en toda su historia (motivo de exclusión del director: cadencia longitudinal insuficiente); 0 security advisories registrados (ROSI sin señal tampoco acá, no es una ventaja diferencial real).

**Métricas que no aplican / débiles:** Contribution Diversity, Skill Similarity, Social Contribution (comunidad muy concentrada en una persona), ROSI (sin historial de seguridad).

---

### 9. tldr-pages/tldr (elección original, descartada)

**Pros:** la comunidad más rica y distribuida de los diez — 19,721 PRs mergeadas de 3,478 personas distintas, wiki y discussions activados, pipeline de extracción ya construido y con resultados históricos calculados (`10/`, `16/`, `20/`, `35/`).

**Contras:** es documentación técnica estructurada (Markdown), no software ejecutable o interpretable — falla el criterio de elegibilidad más básico del informe del director (naturaleza del Producto).

**Métricas que no aplican por validez de constructo** (no por falta de dato — esto es distinto del caso Wiki/Discussion Centrality): Comment Density, Documented Lines of Code, Customer-Found Defects and Regressions, Number of Bugs Detected by Users, Return on Security Investment, Development Experience/Technology Adoption (sin stack de tecnología que evolucione).

---

### 10. freeCodeCamp (en observación)

**Pros:** comunidad enorme (6,813 contribuyentes), hay una aplicación web real detrás (`client/`: 826 archivos, 21.2 MB; `api/`: 209 archivos, 1.2 MB).

**Contras — el peor de los diez en dos ejes a la vez:**
- El 92% de los archivos del repo (17,920 de 19,406) son contenido curricular (`curriculum/`, 56.7 MB), no código de aplicación — mismo problema de fondo que tldr, en peor proporción.
- **Cero releases y cero tags en toda su historia** — no pasa ni el criterio de "es software" ni el de "tiene versionado longitudinal" (mínimo 20 versiones estables exigido por el informe del director).

**Métricas que no aplican:** todas las basadas en versiones/releases (no existe ninguna versión etiquetada), más las mismas limitaciones de construct validity que tldr para la porción curricular del repo.

---

## 5. Diseño de bloques temporales para el candidato elegido (VS Code / Code-OSS)

*(Análisis complementario, datos consultados el 2026-09-18 vía search API de GitHub, verificados independientemente — ver detalle de verificación en el historial de la conversación.)*

### 5.1 Actividad por año

| Año | Commits | Issues cerradas | Issues cerradas "completed" | PRs mergeadas |
|---|---|---|---|---|
| 2015 (nov-dic) | 1,390 | 887 | 887 | 90 |
| 2016 | 12,004 | 12,470 | 12,470 | 626 |
| 2017 | 14,560 | 21,258 | 21,258 | 1,054 |
| 2018 | 16,287 | 21,799 | 21,799 | 1,297 |
| 2019 | 14,857 | 19,570 | 19,570 | 1,478 |
| 2020 | 15,741 | 22,581 | 22,581 (100%, verificado) | 1,471 |
| 2021 | 16,258 | 21,770 | 21,770 | 1,883 (verificado) |
| 2022 | 13,129 (*) | 21,660 | 17,039 | 6,279 (verificado) |
| 2023 | 13,134 | 19,614 | 10,887 (55.5%, verificado) | 7,696 |
| 2024 | 11,062 | 18,181 | 9,800 | 8,044 |
| 2025 | 16,684 | 30,897 | 13,999 | 10,228 |
| 2026 (a sep, ~8.5 meses) | 20,432 | 24,595 | 10,424 | 13,543 |

(*) Resultado marcado como incompleto por la API al momento del relevamiento; confirmar con clonación local.

Total histórico verificado independientemente: **235,282 issues cerradas** (vs. ~235,000 estimado), **165,345 commits**.

### 5.2 Tres quiebres estructurales detectados

1. **2022 — flujo de PRs y `state_reason`.** Las PRs mergeadas casi se triplican (1,883 → 6,279, verificado) sin que suba el volumen de commits — indica cambio de flujo de trabajo hacia PRs. En paralelo, `state_reason` deja de marcar el 100% de las issues como "completed" (verificado: 2020 = 100%, 2023 = 55.5%). Este segundo quiebre probablemente **no es específico de VS Code** — GitHub agregó el campo `state_reason` a la API de Issues recién en 2022, así que cualquier repo con historia previa a esa fecha (CPython, Home Assistant, TensorFlow, tldr, etc.) va a tener el mismo artefacto de backfill.
2. **Marzo 2026 — cadencia semanal de releases.** Verificado con precisión: la versión 1.110 (nombrada por el mes de febrero) se publicó tarde, el 2026-03-04; la 1.111 (2026-03-09) fue la primera de una cadencia semanal ininterrumpida hasta hoy (1.138.0, 2026-09-16, ~cada 7 días).
3. **Aceleración 2026.** En 8.5 meses de 2026 ya hay más commits (20,432) que en todo 2025 (16,684) — hay que verificar cuánto proviene de bots o agentes de código antes de calcular métricas de Persona (mismo riesgo ya visto con `CLAassistant`/`tldr-bot` en tldr y con los bots de autoroll en Flutter).

### 5.3 Criterio de bloques recomendado: trimestres calendario, con `regimen` como variable de control

| Tramo | Régimen | Criterio | N° bloques |
|---|---|---|---|
| 2015-11 → 2016-03 | Preview pre-1.0 | 1 bloque de arranque | 1 |
| 2016-Q2 → 2021-Q4 | Iteraciones mensuales, push directo dominante | Trimestral | 23 |
| 2022-Q1 → 2026-Q1 | Iteraciones mensuales, flujo de PRs, `state_reason` activo | Trimestral | 17 |
| 2026-Q2 → 2026-Q3 | Releases semanales | Trimestral | 2 (Q3 cierra 30-09) |

**Total: 43 bloques, 42 completos hoy.** 2026-Q1 queda como bloque de transición (contiene la última mensual y el arranque de la semanal).

**Criterios descartados:** por release/versión (pierde homogeneidad al pasar a semanal en 2026), mensual (desbalancea un eventual panel comparativo y trunca duraciones para MTTR/MTTF/MTBF), por cantidad fija de eventos (innecesario — el volumen alcanza en cualquier ventana, y rompe la legibilidad del eje X en fecha calendario).

### 5.4 Ajustes de implementación

- `criterio = 'trimestral'` — no requiere tocar `db/schema.sql`.
- **Schedule Compliance debe usar el campo `milestone` de cada issue, no `closed_at`** — verificado que el tracking de milestones existe desde noviembre de 2015 (`Nov 2015 - end`, `Feb 2016`, etc.), así que es viable en toda la historia. Excepción: excluir el milestone catch-all **"Backlog"** (17,221 issues: 11,256 cerradas + 5,965 abiertas) — no corresponde a ninguna versión real y asignarlo a un bloque sería incorrecto.
- Para MTTR/defectos, filtrar por labels en vez de `state_reason` (inconsistente antes/después de 2022) — **pendiente**: verificar que las labels usadas (`bug`, `duplicate`, etc.) no hayan cambiado de taxonomía en los 10 años de historia, con el mismo criterio de sospecha que reveló el problema de `state_reason`.
- La decisión sobre el alcance de `extensions/` (sección 4, candidato #1) afecta a las métricas de Producto, pero no a los límites de bloque — se resuelve por separado.

### 5.5 Pendiente de relevar

- Colaboradores activos por bloque.
- Lista completa de releases con fechas (más allá de la muestra ya verificada).
- Identificación de bots/agentes de código en la aceleración de 2025-2026.
- Labels de cierre exactas del proyecto y su estabilidad a lo largo del tiempo.
- Confirmar si el "regimen" de `state_reason` post-2022 es un artefacto de plataforma (GitHub-wide) replicable en otros repos, lo cual reforzaría que no es una debilidad específica de VS Code.

### 5.6 Decisión pendiente de confirmar con el director

El diseño de bloques trimestrales fue pensado para quedar comparable con el tramo trimestral que ya tiene tldr. **Esto implica combinar VS Code y tldr en un mismo panel/modelo mixto**, lo cual reintroduce parcialmente el enfoque de "comparar patrones entre repos" que el director pidió explícitamente evitar en favor de analizar un solo repo a fondo. Antes de fijar el diseño final, confirmar con el director si el plan es VS Code como caso único, o VS Code como caso principal con tldr como comparación secundaria.

---

## 6. Referencias

- Informe del director: "20260916 Informe Selección mejor Repositorio.docx"
- Jarczyk, O. et al. (2014) — fundamento de Wiki Presence y Jarczyk Success Rate.
- Brooks, F. P. (1975), *The Mythical Man-Month* — noción de equipo "quirúrgico" citada en `16/16 - Wiki Presence.md`.
- Datos de actividad: GitHub REST API y Search API, consultados el 2026-09-18.
- `run_batch_anmcc.py:175` — filtro actual del pipeline que excluye repos no-GitHub (relevante para la exclusión de GIMP).
- `38/38 – Development Experience.md` — documentación previa del equipo sobre la sustitución de Technology Adoption por Development Experience.
