# Gráficos por métrica en Looker Studio — Next.js (serie estable)

Fuente: `nextjs_metricas_unico_100mb.csv`. Columnas: `periodo_num`, `version`, `fecha_inicio`, `metrica_id`, `contribuyente_login`, `value`.

## Nombres completos por `metrica_id`

| `metrica_id` | Nombre completo | Nivel |
|---|---|---|
| `anmcc` | Average Number of Modified Components per Commit (ANMCC) | Producto y Persona |
| `cd` | Comment Density (CD) | Producto y Persona |
| `cfdr` | Customer-Found Defects and Regressions (CFDR) | Producto |
| `dis` | Doc Issue Survival (DIS) | Producto y Persona |
| `dloc` | Documented Lines of Code (DLOC) | Producto y Persona |
| `jarczyk_success_rate` | Jarczyk Success Rate (Tasa de Éxito de Jarczyk) | Producto |
| `le` | Learning Easy (LE) | Producto y Persona |
| `mttr` | Mean Time To Repair (MTTR) | Producto y Persona |
| `nci` | Number of Closed Issues (NCI) | Producto y Persona |
| `nob_42` | Number of Branches (NOB) | Producto |
| `noi` | Number of Open Issues (NOI) | Producto |
| `noi_28` | Number of Open Issues, implementación del registro 28 (NOI_28) | Producto |
| `nub` | Number of Bugs Detected by Users (NUB) | Producto |
| `process_performance` | Development Process Performance | Producto |
| `rc` | README Completeness (RC) | Producto y Persona |
| `schedule_compliance` | Schedule Compliance | Producto |
| `wp` | Wiki Presence (WP) | Producto |
| `cdiv` | Contribution Diversity (CDiv) | Persona |
| `dev_exp` | Development Experience (DevExp) | Persona |
| `disc_centrality` | Discussion Centrality | Persona |
| `exprev` | Review Experience (EXPRev) | Persona |
| `rexprev` | Recent Review Experience (REXPRev) | Persona |
| `fexp` | File Experience (FEXP) | Persona |
| `rexp` | Recent Experience (REXP) | Persona |
| `nc` | Number of Comments (NC) | Persona |
| `sc` | Social Contributions / Developer Contribution (SC / DC) | Persona |
| `ss` | Skill Similarity (SS) | Persona |

## Configuración común

- **Fecha:** Looker no reconoce el formato de `fecha_inicio` (`2016-11-04 10:42:31`). Dejar `fecha_inicio` como **Texto** y crear un campo calculado `fecha` = `PARSE_DATE("%Y-%m-%d", LEFT_TEXT(fecha_inicio, 10))`, de tipo **Fecha**. Usar `fecha` como eje X, con granularidad Año-Mes o Año. Es mejor que `periodo_num` porque las ventanas duran distinto: hay releases a días y otros a meses.
- **Filtro de métrica:** cada gráfico lleva el filtro `metrica_id = <clave>`.
- **Filtro de nivel:**
  - **Producto:** `contribuyente_login` *es nulo* (una fila por versión).
  - **Persona:** `contribuyente_login` *no es nulo*.

  En las métricas que tienen los dos niveles, sin este filtro las sumas quedan duplicadas.
- **Agregación según el tipo de dato:**
  - **Conteos de la ventana** (por ejemplo NCI): **SUMA** por mes. Como las ventanas no se superponen, da el total real de cada mes y corrige las duraciones desiguales.
  - **Valores del estado del código al cierre de la ventana** (DLOC, CD, README, NOI): **MÁX** o **PROMEDIO** por mes.
  - **Proporciones y tiempos:** **PROMEDIO** o **MEDIANA**.
- **Histogramas:** Looker no tiene uno nativo. Se arman con un campo calculado de rangos, por ejemplo `CASE WHEN value < 1 THEN "0-1" WHEN value < 5 THEN "1-5" ELSE "5+" END`, y un gráfico de barras.

---

## Producto: código y documentación

| # | Métrica | Qué calcula | Gráfico recomendado |
|---|---|---|---|
| 1 | **DLOC** (`dloc`) | Líneas no vacías en archivos de documentación (.md, .txt, .rst) del código en esa versión | **Área** en el tiempo, con MÁX por mes. Pasa de ~300 a ~51.000 líneas. Extra: barras con los 15 autores de más líneas de documentación, en la versión más reciente. |
| 2 | **Comment Density** (`cd`) | Líneas de comentario sobre líneas no vacías del código | **Líneas** en el tiempo, con PROMEDIO, formato % y una línea de referencia en el promedio (~6,9%). Muestra el pico de 2021 y la caída posterior. |
| 3 | **README Completeness** (`rc`) | Proporción de 7 categorías esperadas que cubre el README (qué es, cómo usarlo, cómo contribuir, etc.) | **Líneas escalonadas** en el tiempo, porque cambia pocas veces y a saltos. Más una **tarjeta** con el valor actual (~0,27). |
| 4 | **Wiki Presence** (`wp`) | 1 si el repo tiene la Wiki de GitHub habilitada, 0 si no | **Tarjeta** con el valor. Es 0 en todas las versiones, así que no tiene sentido una serie. |
| 5 | **ANMCC** (`anmcc`) | Promedio de archivos modificados por commit en la ventana | **Columnas por año** con PROMEDIO. Por persona: un **histograma por rangos** (1, 2–5, 6–20, +20 archivos) para ver si hay commits atómicos o refactors grandes. |

## Proceso: issues y flujo de trabajo

| # | Métrica | Qué calcula | Gráfico recomendado |
|---|---|---|---|
| 6 | **NOI** (`noi`) | Issues abiertas al cierre de la ventana (el backlog) | **Líneas** en el tiempo, con MÁX por mes. Muestra el crecimiento hasta ~3.100 en 2024 y la baja posterior. |
| 7 | **NOI_28** (`noi_28`) | La misma métrica que NOI, otra implementación | **No graficarla.** Da prácticamente lo mismo que NOI; mencionarla como validación cruzada. |
| 8 | **NCI** (`nci`) | Issues cerradas dentro de la ventana | **Columnas por mes o año** con SUMA, filtro de nivel Producto. Por persona: barras con los 15 que más issues cerraron. |
| 9 | **MTTR** (`mttr`) | Horas promedio entre la apertura y el cierre de las issues cerradas en la ventana | **Líneas por año** con **MEDIANA**, no promedio: algunas issues de años cerradas de golpe distorsionan el promedio. Para verlo en días, usar el campo calculado `value/24`. |
| 10 | **Doc Issue Survival** (`dis`) | Días promedio que tarda en cerrarse una issue de documentación | **Columnas por año** con MEDIANA. Hay muchas ventanas en 0 (sin issues de documentación); para excluirlas, filtrar `value > 0`. |
| 11 | **Process Performance** (`process_performance`) | Proporción de issues cerradas dentro de los 3 días de abiertas | **Líneas** por año con PROMEDIO, formato %. Baja de ~65% a ~35–45%. |
| 12 | **Tasa de éxito de Jarczyk** (`jarczyk_success_rate`) | Issues cerradas sobre el total de issues de la ventana | **Líneas** por año, en el **mismo gráfico** que Process Performance: las dos van de 0 a 1 y cuentan una historia parecida. |
| 13 | **Schedule Compliance** (`schedule_compliance`) | Proporción de issues cerradas de cada milestone de GitHub | **Tabla** con versión, fecha y valor, con barras dentro de la celda. Solo hay 41 versiones con dato; como serie quedaría con huecos. |
| 14 | **CFDR** (`cfdr`) | Issues etiquetadas como bug reportadas por gente de fuera del equipo central | **Columnas por año** con SUMA. |
| 15 | **NUB** (`nub`) | Bugs reportados por usuarios, con otro criterio de detección | **Líneas** en el mismo gráfico que CFDR (CFDR en columnas, NUB en línea), para comparar los dos criterios. |
| 16 | **Number of Branches** (`nob_42`) | Cantidad de branches del repo hoy (no histórico) | **Tarjeta** con el valor (2.706). Es constante porque se consulta el estado actual. |

## Persona: colaboradores

Ninguna de estas tiene fila de Producto, así que todas usan el filtro *no es nulo*. Cada una admite dos vistas: la evolución de la comunidad en el tiempo y el ranking o la distribución de personas.

| # | Métrica | Qué calcula | Gráfico recomendado |
|---|---|---|---|
| 17 | **Social Contribution** (`sc`) | Por colaborador: issues abiertas, issues propias cerradas, PRs abiertas, PRs rechazadas y PRs mergeadas | **Líneas** con `COUNT_DISTINCT(contribuyente_login)` por mes, que muestra cuántas personas contribuyen. Además, **barras** con los 15 que más contribuyen. |
| 18 | **Number of Comments** (`nc`) | Comentarios de cada colaborador en issues, PRs y commits | **Columnas por mes** con SUMA (volumen total de discusión). Además, un **mapa de árbol** por colaborador, que muestra cuánto concentran unos pocos. |
| 19 | **Discussion Centrality** (`disc_centrality`) | Con cuántas personas distintas compartió hilos cada colaborador | **Barras** con los 15 más conectados. En el tiempo: líneas con la MEDIANA por mes, que indica si la red se vuelve más o menos conectada. |
| 20 | **EXPRev** (`exprev`) | Puntaje de experiencia en revisión de código (issues más participación en revisiones de PRs) | **Histograma por rangos**: la mayoría tiene puntaje bajo y hay pocos revisores fuertes. Además, **barras** con los 15 primeros. |
| 21 | **REXPRev** (`rexprev`) | Igual que EXPRev, pero con más peso en la actividad reciente | **Barras** con los 15 primeros **en la última versión**, usando un control de filtro por versión. Comparado con EXPRev muestra quién revisa *hoy* y quién revisaba antes. |
| 22 | **Contribution Diversity** (`cdiv`) | Archivos distintos que tocó el colaborador (acumulado) | **Histograma por rangos** (1–10, 11–100, 101–1000, +1000 archivos): separa especialistas de generalistas. |
| 23 | **FEXP** (`fexp`) | Por cada archivo de un commit, cuántas veces el mismo autor ya lo había tocado | **Líneas** con el PROMEDIO por mes: indica si la gente vuelve a sus archivos o reparte el trabajo. Además, barras con los 15 primeros. |
| 24 | **REXP** (`rexp`) | Suma de 1/(días desde el commit + 1) por commit: experiencia ponderada hacia lo reciente | **Barras** con los 15 primeros por año, usando un control de filtro de período. Muestra el núcleo activo en cada etapa. |
| 25 | **Learning Easy** (`le`) | Días desde el primer commit del colaborador hasta que toca un componente nuevo | Nivel Producto: **líneas** con el PROMEDIO por año. Nivel Persona: **histograma por rangos** (menos de 30 días, 30–180, 180–365, más de un año). |
| 26 | **Skill Similarity** (`ss`) | Proporción de los lenguajes del repo que el colaborador ya usaba en sus propios repos (de 0 a 1) | **Histograma por rangos** (0, 0,01–0,5, 0,5–0,99, 1). Además, una **tarjeta** con el promedio (~0,57). En el tiempo varía poco. |
| 27 | **Development Experience** (`dev_exp`) | Meses desde el primer commit de cada colaborador hasta el cierre de la ventana (antigüedad) | **Histograma por rangos** de antigüedad (menos de 1 año, 1–3, 3–5, más de 5) en la última versión. Es la métrica más pesada (~900.000 filas); en la serie temporal usar MEDIANA. |

---

## Notas

- **Una página por dimensión** (Producto, Proceso, Persona), con un **control de período** arriba que afecte a todos los gráficos de la página.
- **Development Experience sube casi en línea recta con el tiempo** (0,99 de correlación). Sola está bien, pero no usarla en cruces.
- **No graficar en el tiempo** Wiki Presence, Number of Branches ni NOI_28: las dos primeras son constantes y la tercera duplica a NOI. Usar tarjetas o una nota.
- **Los rankings de personas cambian mucho según el período elegido.** Aclarar en el título si son de toda la historia o de la última versión.

---

# Paso a paso en Looker Studio

## Fase 1 — Campos calculados (una sola vez, en la fuente de datos)

Desde **Recurso → Administrar fuentes de datos → Editar → Añadir un campo**. Ya creados: `Fecha` y `nivel`.

**Para gráficos con dos métricas juntas:**

| Nombre | Fórmula |
|---|---|
| `pp_val` | `CASE WHEN metrica_id = "process_performance" THEN value END` |
| `jarczyk_val` | `CASE WHEN metrica_id = "jarczyk_success_rate" THEN value END` |
| `cfdr_val` | `CASE WHEN metrica_id = "cfdr" THEN value END` |
| `nub_val` | `CASE WHEN metrica_id = "nub" THEN value END` |

**Para MTTR en días:**

| Nombre | Fórmula |
|---|---|
| `mttr_dias` | `value / 24` |

**Rangos para histogramas.** El número al principio de cada etiqueta hace que las barras salgan en orden.

| Nombre | Fórmula |
|---|---|
| `rango_anmcc` | `CASE WHEN value <= 1 THEN "1. 1 archivo" WHEN value <= 5 THEN "2. 2-5" WHEN value <= 20 THEN "3. 6-20" ELSE "4. +20" END` |
| `rango_exprev` | `CASE WHEN value <= 1 THEN "1. 1" WHEN value <= 5 THEN "2. 2-5" WHEN value <= 20 THEN "3. 6-20" WHEN value <= 100 THEN "4. 21-100" ELSE "5. +100" END` |
| `rango_cdiv` | `CASE WHEN value <= 10 THEN "1. 1-10" WHEN value <= 100 THEN "2. 11-100" WHEN value <= 1000 THEN "3. 101-1000" ELSE "4. +1000" END` |
| `rango_le` | `CASE WHEN value < 30 THEN "1. <30 días" WHEN value < 180 THEN "2. 30-180" WHEN value < 365 THEN "3. 180-365" ELSE "4. +1 año" END` |
| `rango_ss` | `CASE WHEN value = 0 THEN "1. 0" WHEN value < 0.5 THEN "2. 0-0.5" WHEN value < 1 THEN "3. 0.5-0.99" ELSE "4. 1" END` |
| `rango_devexp` | `CASE WHEN value < 12 THEN "1. <1 año" WHEN value < 36 THEN "2. 1-3 años" WHEN value < 60 THEN "3. 3-5 años" ELSE "4. +5 años" END` |

## Nombres en el menú Insertar

| En esta guía | En el menú de Looker |
|---|---|
| Control de período | Filtro por periodo |
| Columnas | Gráfico de barras verticales |
| Barras (Top 15) | Barras horizontales, desde el ícono **Añadir un gráfico** de la barra de herramientas |
| Gráfico de áreas | Gráfico de áreas apiladas (con una sola métrica es un área común) |
| Serie temporal | Gráfico de serie temporal |
| Tarjeta de resultados | Cuadro de resultados |
| Mapa de árbol | Gráfico de rectángulos |
| Histograma | **Histograma**, nativo. Sirve para Skill Similarity y Development Experience. En las métricas muy desparejas (EXPRev, Contribution Diversity, ANMCC, Learning Easy) conviene más el campo de rangos con barras verticales. |

## Fase 2 — Páginas y control de período

1. Creá tres páginas desde **Página → Nueva página** y renombralas **Producto**, **Proceso** y **Persona**.
2. En cada página, agregá un control de período desde **Añadir un control → Control de período**, arriba de todo. Filtra por fecha todos los gráficos de la página.

## Fase 3 — Receta de cada gráfico

1. Agregá el tipo de gráfico desde **Añadir un gráfico**.
2. En **Configuración**:
   - **Dimensión:** la de la tabla. Si es `Fecha`, ajustá la granularidad con el ícono de calendario.
   - **Métrica:** la de la tabla. La agregación se cambia con el ícono al lado del campo.
   - **Dimensión de período:** `Fecha`, para que funcione el control de período.
3. En **Filtro → Añadir un filtro → Crear un filtro**, cargá las condiciones de la tabla, unidas con **Y**. Ponele al filtro un nombre claro, por ejemplo `DLOC – Producto`.
4. **Rankings (Top 15):** en **Configuración → Orden**, poné `value` descendente. En **Estilo → Número de barras**, poné 15.
5. **Histogramas:** en **Orden**, poné el campo de rango ascendente.

## Fase 4 — Ficha de cada gráfico

**Página Producto**

| # | Gráfico | Tipo | Dimensión | Métrica (agregación) | Filtro |
|---|---|---|---|---|---|
| 1 | DLOC en el tiempo | Gráfico de áreas (serie temporal) | Fecha (Año-Mes) | value (Máx.) | metrica_id = dloc · nivel = Producto |
| 1b | Autores de documentación | Barras, Top 15 | contribuyente_login | value (Máx.) | metrica_id = dloc · nivel = Persona · version = v16.3.5 |
| 2 | Comment Density | Serie temporal | Fecha (Año-Mes) | value (Media), formato Porcentaje | metrica_id = cd · nivel = Producto. En Estilo → Líneas de referencia: Media. |
| 3 | README Completeness | Serie temporal | Fecha (Año-Mes) | value (Media) | metrica_id = rc · nivel = Producto |
| 3b | README actual | Tarjeta de resultados | — | value (Máx.) | metrica_id = rc · nivel = Producto · version = v16.3.5 |
| 4 | Wiki Presence | Tarjeta de resultados | — | value (Máx.) | metrica_id = wp |
| 5 | ANMCC por año | Columnas | Fecha (Año) | value (Media) | metrica_id = anmcc · nivel = Producto |
| 5b | Tamaño de commits | Columnas (histograma) | rango_anmcc | Record Count | metrica_id = anmcc · nivel = Persona |

**Página Proceso**

| # | Gráfico | Tipo | Dimensión | Métrica (agregación) | Filtro |
|---|---|---|---|---|---|
| 6 | Backlog (NOI) | Serie temporal | Fecha (Año-Mes) | value (Máx.) | metrica_id = noi |
| 7 | NOI_28 | No se grafica | — | — | — |
| 8 | Issues cerradas | Columnas | Fecha (Año) | value (Total) | metrica_id = nci · nivel = Producto |
| 8b | Quién cierra issues | Barras, Top 15 | contribuyente_login | value (Total) | metrica_id = nci · nivel = Persona |
| 9 | MTTR | Serie temporal | Fecha (Año) | mttr_dias (Mediana) | metrica_id = mttr · nivel = Producto |
| 10 | Doc Issue Survival | Columnas | Fecha (Año) | value (Mediana) | metrica_id = dis · nivel = Producto · value > 0 |
| 11 y 12 | Process Performance y Jarczyk | Serie temporal | Fecha (Año) | pp_val (Media) y jarczyk_val (Media), formato Porcentaje | metrica_id En process_performance, jarczyk_success_rate |
| 13 | Schedule Compliance | Tabla | version, Fecha | value (Media). En Estilo, mostrar la columna como Barra. | metrica_id = schedule_compliance |
| 14 y 15 | CFDR y NUB | Gráfico combinado | Fecha (Año) | cfdr_val (Total) como barras y nub_val (Total) como línea | metrica_id En cfdr, nub |
| 16 | Number of Branches | Tarjeta de resultados | — | value (Máx.) | metrica_id = nob_42 |

**Página Persona.** Todos los filtros llevan además `nivel = Persona`.

| # | Gráfico | Tipo | Dimensión | Métrica (agregación) | Filtro |
|---|---|---|---|---|---|
| 17 | Colaboradores activos | Serie temporal | Fecha (Año-Mes) | contribuyente_login (Recuento diferenciado) | metrica_id = sc |
| 17b | Top contribuyentes | Barras, Top 15 | contribuyente_login | value (Total) | metrica_id = sc |
| 18 | Volumen de discusión | Columnas | Fecha (Año-Mes) | value (Total) | metrica_id = nc |
| 18b | Concentración de comentarios | Mapa de árbol | contribuyente_login | value (Total) | metrica_id = nc |
| 19 | Más conectados | Barras, Top 15 | contribuyente_login | value (Total) | metrica_id = disc_centrality |
| 19b | Conectividad en el tiempo | Serie temporal | Fecha (Año) | value (Mediana) | metrica_id = disc_centrality |
| 20 | Distribución EXPRev | Columnas (histograma) | rango_exprev | Record Count | metrica_id = exprev |
| 20b | Top revisores | Barras, Top 15 | contribuyente_login | value (Máx.) | metrica_id = exprev |
| 21 | Revisores recientes | Barras, Top 15 | contribuyente_login | value (Máx.) | metrica_id = rexprev · version = v16.3.6 |
| 22 | Especialistas vs. generalistas | Columnas (histograma) | rango_cdiv | Record Count | metrica_id = cdiv |
| 23 | FEXP en el tiempo | Serie temporal | Fecha (Año) | value (Media) | metrica_id = fexp |
| 23b | Top FEXP | Barras, Top 15 | contribuyente_login | value (Total) | metrica_id = fexp |
| 24 | Núcleo activo | Barras, Top 15 | contribuyente_login | value (Máx.) | metrica_id = rexp. Usar el control de período para ver cada etapa. |
| 25 | Learning Easy en el tiempo | Serie temporal | Fecha (Año) | value (Media) | metrica_id = le · **nivel = Producto** |
| 25b | Distribución Learning Easy | Columnas (histograma) | rango_le | Record Count | metrica_id = le |
| 26 | Distribución Skill Similarity | Columnas (histograma) | rango_ss | Record Count | metrica_id = ss |
| 26b | Skill Similarity promedio | Tarjeta de resultados | — | value (Media) | metrica_id = ss |
| 27 | Antigüedad de la comunidad | Columnas (histograma) | rango_devexp | Record Count | metrica_id = dev_exp · version = v16.3.6 |
| 27b | Antigüedad en el tiempo | Serie temporal | Fecha (Año) | value (Mediana) | metrica_id = dev_exp |

**Sobre los histogramas:** en los de Persona, Record Count cuenta pares colaborador-versión, no personas únicas, porque cada versión dura pocos días y tiene entre 12 y 200 colaboradores. Ponelo en el título, por ejemplo "colaboradores por versión". La excepción es Development Experience: guarda una fila por cada colaborador histórico en cada versión, así que filtrando la última versión cada barra cuenta personas únicas.

**Por qué distintas versiones:** las métricas calculadas en esta sesión llegan hasta v16.3.5 y las de Luz hasta v16.3.6.

---

# Evolución por release: estables y canary (métricas de Producto)

Fuente: `nextjs_producto_estable_canary.csv`, con 54.446 filas y solo valores de Producto. Columnas: `serie` (estable/canary), `periodo_num`, `version`, `fecha_hora` (formato AAAAMMDDhhmmss, que Looker reconoce solo), `metrica_id`, `value`.

| Serie | Métricas | Releases |
|---|---|---|
| Estable | 17 | 373–375 |
| Canary | 14 (no tiene nob_42, noi_28 ni nub) | ~3.860 |

**Receta de cada gráfico**

1. Tipo: Gráfico de serie temporal.
2. Dimensión: `fecha_hora`, con granularidad Fecha y hora. Así cada release es un punto.
3. Métrica: `value`. La agregación da igual, porque hay una fila por release.
4. Filtros: `metrica_id = X` y `serie = estable` o `serie = canary`.
5. En Estilo → Datos que faltan, elegir **Conectar puntos**.
6. En Estilo → Líneas de referencia, agregar dos líneas: Métrica `value` con cálculo **Máx.** y Métrica `value` con cálculo **Mín.**
