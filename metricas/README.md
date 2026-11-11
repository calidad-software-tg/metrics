# Métricas

Todo lo que calcula los datos: las métricas de cada ventana entre releases, la unificación de
identidades y la exportación por persona. Cada métrica vive en la carpeta de su **consigna** del catálogo
(el número de registro de Alonso y Robiolo, 2022), con el código (`.py`) y su ficha (`.md`): qué mide,
la fórmula, de dónde salen los datos y cómo se interpreta.

## De dónde salen

| Paso | Archivo en `catalogo/` |
|---|---|
| 1. El catálogo completo: las 209 métricas de calidad Persona, Proceso y Producto relevadas por Alonso y Robiolo (2022) | `Fase1_1_catalogo_209_metricas.xlsx` |
| 2. Las consignas priorizadas: las que se pueden calcular con lo que deja un repositorio de GitHub | `Fase1_2_consignas_priorizadas.xlsx` |
| 3. Las métricas implementadas, con su consigna, sus dimensiones y su fuente | `Fase1_3_metricas_implementadas.xlsx` |

## Las métricas

**Clon** = se calcula desde la historia de git, sin límite de consultas (`run_versiones_local.py`).
**API** = necesita datos que solo tiene GitHub (issues, PR, revisiones, comentarios, milestones,
branches), y está limitada a 5.000 consultas por hora (`run_versiones.py`).

| Consigna | Métrica | Clave | Dimensiones del catálogo | Fuente | Por persona¹ |
|---|---|---|---|---|---|
| 10 | ANMCC: componentes modificados por commit | `anmcc` | Proceso, Producto | Clon | sí |
| 10 | MTTR: tiempo medio de reparación de issues | `mttr` | Proceso, Producto | API | sí |
| 15 | Contribution Diversity | `cdiv` | Persona, Proceso | Clon | sí |
| 15 | FEXP: experiencia en los archivos | `fexp` | Persona | Clon | sí |
| 15 | Learning Ease: antigüedad en los componentes | `le` | Persona, Producto | Clon | sí |
| 15 | REXP: experiencia reciente | `rexp` | Persona | Clon | sí |
| 15 | EXPRev: experiencia en revisión de código | `exprev` | Persona, Proceso | API | sí |
| 15 | REXPRev: experiencia reciente en revisión | `rexprev` | Persona, Proceso | API | sí |
| 15 | Skill Similarity | `ss` | Persona | API | sí |
| 16 | Comment Density | `cd` | Persona, Producto | Clon | sí |
| 16 | DLOC: líneas de documentación | `dloc` | Producto | Clon | sí |
| 16 | README Completeness | `rc` | Proceso, Producto | Clon | sí |
| 16 | Wiki Presence | `wp` | Proceso, Producto | API | no |
| 16 | Doc Issue Survival | `dis` | Proceso | API | sí |
| 18 | Number of Comments | `nc` | Persona, Proceso | API | sí |
| 18 | Discussion Centrality | `disc_centrality` | Persona | API | sí |
| 18, 20 | Social Contributions | `sc` | Persona, Proceso | API | sí |
| 23 | Schedule Compliance | `schedule_compliance` | Proceso | API | no |
| 27, 39 | CFDR: defectos y regresiones reportados desde fuera del equipo | `cfdr` | Proceso, Producto | API | no |
| 28, 40 | Number of Open Issues | `noi`, `noi_28` | Proceso, Producto | API | no |
| 35, 40, 43 | Number of Closed Issues | `nci` | Proceso | API | sí |
| 38 | Development Experience | `dev_exp` | Persona, Proceso | API | sí |
| 39 | Number of Bugs Detected by Users | `nub` | Proceso, Producto | API | no |
| 40 | Development Process Performance | `process_performance` | Proceso | API | no |
| 42 | Number of Branches | `nob_42` | Proceso, Producto | API | no |
| 43 | Tasa de éxito de Jarczyk | `jarczyk_success_rate` | Proceso | API | no |

¹ Las que también se resumen por persona en el análisis (`export_persona.py`).

En las consignas 40 y 43, NCI se reutiliza (fichas «NCI (reutilizada)»): es la misma métrica que la de
la consigna 35, y se calcula una sola vez.

Además se calculan **variantes** y **métricas de flujo**, que el análisis usa como control o como
complemento:

| Clave | Qué es | Fuente |
|---|---|---|
| `mttr_p50`, `mttr_bugs`, `mttr_con_bots` | MTTR con la mediana, solo de bugs y sin sacar los bots | API |
| `nci_con_bots` | NCI sin sacar los bots | API |
| `dloc_flujo` | líneas de documentación agregadas o eliminadas en la ventana (DLOC es una foto acumulada) | Clon |
| `commits_doc` | proporción de commits que tocan documentación | Clon |

Las métricas de **estado** (cuánta documentación hay, densidad de comentarios, README) se miden sobre la
rama principal al **cierre** de cada ventana; las de **actividad** (issues cerradas, commits,
revisiones), con los eventos de la ventana.

## Archivos

| Archivo | Qué hace |
|---|---|
| `run_versiones.py` | Arma las ventanas entre releases (series estable y canary) y calcula las métricas de la API en cada una. Guarda en la base (`periodo` y `resultado`); vuelve a calcular sin duplicar. |
| `run_versiones_local.py` | Las métricas del clon, con las mismas ventanas. Clona el repositorio en `.clones/` si no hay un clon propio. |
| `base_metric.py` | Clase común de las métricas y filtro de bots (`es_bot`). |
| `issues_comun.py` | Descarga de issues compartida por MTTR, NCI, NOI, DIS, Process Performance y Jarczyk: si se corren juntas, se descarga una sola vez. |
| `loc.py` | Qué archivos cuentan como código propio (sin dependencias ni código generado); lo usan otras métricas. |
| `bots_clasificados.csv` | Cuentas revisadas a mano como bot, agente de IA o desconocida; se excluyen de las métricas por persona. |
| `mapear_identidades.py` | Une el nombre de git de cada autor con su login de GitHub; deja `datos/identidades_git.csv`. |
| `export_persona.py` | Resume las métricas por persona de cada ventana (mediana, percentil 90, proporción del 10 % más activo, participación) en `datos/persona_agregado_estable_canary.csv`. |

Todos se corren con `tres_p.py` (`calcular`, `identidades`, `exportar`; ver el README principal). Para
una métrica suelta, sin guardar en la base:

```bash
python3 metricas/run_versiones.py mttr --repo org/nombre --no-guardar
python3 metricas/run_versiones_local.py --repo org/nombre --solo cd --no-guardar
```

## Correcciones al cálculo

Mientras se validaban las métricas con Next.js aparecieron problemas que se corrigieron en el código.
Los principales, por si se compara con versiones anteriores:

| Tema | Qué se corrigió |
|---|---|
| Ventanas | Los backports y los tags mal etiquetados no cortan ventanas; las releases a menos de un día se unen; fecha de corte común (`hasta`). |
| Fotos del código | CD, DLOC y README Completeness se miden al cierre de la ventana, sobre la rama principal. DLOC cuenta `.md`, `.mdx`, `.txt` y `.rst` y excluye ejemplos, tests y dependencias; CD excluye código compilado y de terceros; README Completeness mira solo el de la raíz y sigue enlaces simbólicos. |
| Estado de hoy | Wiki Presence, Number of Branches, Schedule Compliance y Social Contributions dejaron de usar el estado actual del repositorio y usan el de cada ventana. |
| Sin datos | MTTR, ANMCC, CD, README Completeness y DIS devuelven nulo, no 0, cuando no hay datos. |
| Bots | Se filtran también a nivel producto (commits, cierres e issues de bots) y con la lista de `bots_clasificados.csv`. |
| Etiquetas | NUB y DIS comparan etiquetas exactas (sin prefijos como `type:`), no subcadenas. |
| Flujo | Se agregaron `dloc_flujo` y `commits_doc`, porque DLOC solo mide lo acumulado. |
