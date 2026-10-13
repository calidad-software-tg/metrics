# Auditoría del informe Persona–Persona

Revisión del `.md` contra el código, el diccionario, los pares, el JSON del PCA y la base
(solo lectura). Cada afirmación tiene su fuente, un veredicto y una corrección propuesta.

Veredictos: **ok** · **error** (hay que corregir) · **no verificable** (sacar o marcar
pendiente).

## 1 · Definiciones (sección 1)

| sección | afirmación en el informe | qué dicen los datos o el código | veredicto | corrección propuesta |
|---|---|---|---|---|
| §1 | REXP: "Suma ponderada de commits en el repositorio en los últimos 12 meses… Mide experiencia reciente en el proyecto." | `15/rexp.py` suma `1/(días+1)` sobre los commits de la persona **dentro de la ventana** hasta `fecha_fin`; no mira commits previos a la ventana ni usa una ventana fija de 12 meses. El docstring aclara: "aunque se llame 'experiencia', mide actividad reciente ponderada por cercanía al cierre". FIXES_METRICAS.md fix 23: pasa a familia `intensidad`. | **error** | Reemplazar por: "Suma de `1/(días hasta el cierre + 1)` sobre los commits del autor dentro de la ventana. Mide actividad reciente ponderada por cercanía al cierre, no experiencia; en el diccionario va en la familia intensidad." |
| §1 | REXPRev: "Igual que REXP pero sobre revisiones de pull requests (comentarios de review)." | `15/rexprev.py`: pondera por antigüedad **todos los eventos de revisión/discusión** del autor: issues abiertos+cerrados, PRs abiertos+cerrados, comentarios de issues y comentarios de revisión de PRs. No se limita a comentarios de review. | **error** | "Suma de `1/(días hasta el cierre + 1)` sobre los eventos de revisión y discusión del autor en la ventana: issues y PRs abiertos y cerrados, comentarios en issues y comentarios de revisión de PRs." |
| §1 | EXPRev: "Cantidad acumulada de revisiones de pull requests desde la primera contribución." | `15/exprev.py`: suma, para la persona **dentro de la ventana**, de issues abiertos + cerrados + PRs abiertos + cerrados + comentarios de issues + comentarios de revisión. No acumula desde la primera contribución. | **error** | "Suma, dentro de la ventana, de la actividad del autor: issues y PRs abiertos y cerrados, comentarios de issues y comentarios de revisión de PRs." |
| §1 | CDIV: "Cantidad de directorios distintos del repositorio a los que contribuyó la persona, desde su primera contribución." | `15/cdiv.py`: cuenta **archivos únicos** (set de rutas de archivos modificados) tocados por el autor dentro de la ventana. No cuenta directorios ni acumula desde la primera contribución. (El runner local sí carga el histórico completo para `fexp/le/rexp`; para CDIV, usa commits de la ventana.) | **error** | "Cantidad de archivos únicos del repositorio modificados por la persona dentro de la ventana." |
| §1 | LE: "Días entre la primera contribución a un componente y su última contribución en la ventana, promediados sobre los pares persona–componente activos." | `15/le.py`: para cada par (autor, componente) activo en la ventana, `max(ts dentro ventana) - min(primera contribución histórica al componente, ts dentro ventana)`. Promedio por autor sobre sus componentes activos. El componente es sub-proyecto en monorepos (`packages/X`, `apps/X`, …) según `componente_de()`. | **ok (ampliar)** | Aclarar que el "componente" es sub-proyecto en monorepos y que la primera contribución es histórica (viene del `git log` completo del runner local). |
| §1 | SC: "Medida de la participación en la red de colaboración: combina comentarios, revisiones y commits en relación con el resto del equipo." | `20/dc.py` (reutilizada en `18/sc.py`): suma por autor de **issues abiertos + issues propios cerrados dentro de la ventana + PRs abiertos + PRs propios cerrados dentro de la ventana + PRs propios mergeados dentro de la ventana**. No cuenta comentarios ni commits ni compara con el resto del equipo. Fix 20: cerrado/mergeado solo cuenta si ocurrió antes del cierre de la ventana (antes usaba el estado de hoy). | **error** | "Suma, por autor, de issues y PRs abiertos en la ventana más los que la misma persona cerró o mergeó dentro de la ventana (Falcão et al., 2020). Fix 20 (branch `ine/fixes-metricas`): el cierre o merge se cuenta solo si ocurrió antes del fin de la ventana; antes se usaba el estado actual." |
| §1 | SS: "Skill Stack. Cantidad de lenguajes de programación distintos en repos públicos del usuario en GitHub (snapshot actual). Aproxima la diversidad de habilidades técnicas." | `15/ss.py` + `15 - Skill Similarity.md`: la métrica se llama **Skill Similarity**. Fórmula: `|user_languages ∩ repo_languages| / |repo_languages|` (ratio 0-1). Mide **afinidad técnica** entre el stack del repo y los lenguajes del usuario, no cuántos lenguajes conoce. | **error** | "SS (Skill Similarity): proporción de los lenguajes del repositorio (los que superan 0,1 % de los bytes del árbol al cierre de la ventana) que el autor también tiene en sus repos propios de GitHub. Ratio de 0 a 1; mide afinidad técnica con el stack, no cantidad de lenguajes conocidos." |
| §1 | NC: "Cantidad de comentarios en issues y pull requests abiertos o cerrados por la persona en la ventana." | `18/nc.py`: suma de comentarios **que escribió la persona** en issues/PRs, en commits (`CommitCommentEvent`) y en revisiones de PRs (`PullRequestReviewCommentEvent`), dentro de la ventana. Nada que ver con "issues abiertos o cerrados". | **error** | "Cantidad de comentarios escritos por la persona dentro de la ventana en issues y PRs, en commits y en revisiones de PRs." |
| §1 | NCI: "Cantidad de issues cerradas por la persona en la ventana." | `35/nci.py` (reexportado por `43`): se atribuye al login del actor del `ClosedEvent` (quien cerró, no quien abrió). Fix 16: excluye cierres sin actor y cierres por bots. | **ok (ampliar)** | Aclarar que se atribuye al actor del `ClosedEvent` (quien cerró) y que fix 16 saca cierres por bots y sin actor. |
| §1 | SS listada en §1 como Persona pero sin aclaración de que su advertencia es que el user_languages es snapshot actual. | `15/ss.py` lo documenta explícitamente; el diccionario tiene esa advertencia en `ss_mediana`. | **ok** | — |
| §1 | disc_centrality: "Centralidad de la persona en la red de discusión del release: cuántas discusiones de issues y PRs activas pasaron por sus comentarios." | `18/disc_centrality.py`: calcula el **grado** del nodo en la MBSN (red donde dos personas están conectadas si comentaron en el mismo hilo de issue, PR o commit). Es "cuántas otras personas distintas" (no "cuántos hilos"). Bots se filtran antes de armar el grafo. | **error** | "Grado del autor en la red social de discusión (MBSN) de la ventana: cantidad de otras personas con las que compartió al menos un hilo de issue, PR o commit mediante comentarios. Los bots se excluyen antes de armar el grafo." |
| §1 | dev_exp: "Cantidad de días desde la primera contribución al repositorio hasta el cierre de la ventana. Mide antigüedad en el proyecto." | `38/dev_experience.py`: `(fecha_fin - primer_commit).days / 30.44`. Resultado en **meses**, no días. También: `export_persona.py` filtra dev_exp a los autores con `anmcc` en la misma ventana. | **error** | "Meses desde el primer commit del autor en la rama principal del repositorio hasta el fin de la ventana (`días / 30.44`). En el agregado por release se restringe a quienes además tienen anmcc en la misma ventana (ver `export_persona.py`)." |
| §1 | Faltante: FEXP no se describe. El informe la lista en §2 como excluida sin explicar qué es. | `15/fexp.py`: suma, para cada archivo tocado en los commits del autor dentro de la ventana, de la cantidad de commits previos del mismo autor sobre ese archivo (dentro de la ventana). | **error** | Agregar fila en §1: "FEXP (File Experience): para cada archivo tocado por un commit del autor en la ventana, cantidad de commits previos del mismo autor sobre ese archivo. Suma por autor. Solo cuenta experiencia intra-ventana." |

**Consecuencia en §10.3 (nombre y lectura de CP3).** El informe llama al CP3 "Experiencia vs. renovación", citando REXP y LE como "experiencia". REXP mide actividad, no experiencia, y por eso CP3 agrupa variables de **amplitud de la contribución** (CDIV, ANMCC, LE) con la **actividad de los veteranos activos** (REXP) opuestas a la **llegada de nuevos committers**. Hay que renombrarlo y reescribir la interpretación (ver §7 abajo).

## 2 · Variables analizadas (sección 2)

| sección | afirmación | datos | veredicto | corrección |
|---|---|---|---|---|
| §2 | "Intensidad: 12 variables (p90 y share del top 10 % de NC, NCI, EXPRev, SC y CDIV)." | Diccionario: 12 variables en familia **intensidad**: `dloc_p90, dloc_share_top10pct, exprev_p90, exprev_share_top10pct, nc_p90, nc_share_top10pct, nci_p90, nci_share_top10pct, rexp_mediana, rexprev_mediana, sc_p90, sc_share_top10pct`. CDIV **no** está acá (está en amplitud); REXP y REXPRev **sí** están acá. Falta además DLOC. | **error** | Reemplazar por: "Intensidad (12): p90 y share del top 10 % de NC, NCI, EXPRev, SC y DLOC, más las medianas de REXP y REXPRev (rexp y rexprev miden actividad por cercanía al cierre, por eso van acá — fix 23)." |
| §2 | "Composición: 8 variables (proporciones y tasas, LE, SS, dev_exp)." El conteo del párrafo (3 proporciones + 2 tasas + LE + SS + dev_exp = 8) coincide, pero el listado concreto cambia respecto del diccionario. | Diccionario, familia **composicion** (8): `dev_exp_mediana, le_mediana, prop_cierran_ratio, prop_comentan_ratio, prop_commitean_ratio, ss_mediana, tasa_nuevos_commits_ratio, tasa_nuevos_interaccion_ratio`. | **ok (contenido correcto, redacción confusa)** | Enumerar explícitamente: 3 proporciones (cierran, comentan, commitean), 2 tasas (nuevos commits, nuevos interacción), `le_mediana`, `ss_mediana`, `dev_exp_mediana`. |
| §2 | "Amplitud: 4 variables (mediana de CDIV, p90 de CDIV, share top 10 % de CDIV, mediana de ANMCC)." | Diccionario: `anmcc_mediana, cdiv_mediana, cdiv_p90, cdiv_share_top10pct`. | **ok** | — |
| §2 | "Tamaño: 6 variables de conteo." | Diccionario: `activos_cierre_conteo, activos_comentarios_conteo, activos_commits_conteo, activos_interaccion_conteo, nuevos_commits_conteo, nuevos_interaccion_conteo`. | **ok** | — |
| §2 | "Red: 1 variable (disc_centrality mediana)." | Diccionario: `disc_centrality_mediana`. | **ok** | — |
| §2 | "Otras: 6 variables (medianas de CD, DLOC, MTTR, RC, DIS y SC)." | Diccionario, familia **otra** (6): `cd_mediana, dis_mediana, dloc_mediana, mttr_mediana, rc_mediana, sc_mediana`. | **ok** | — |
| §2 | Exclusiones: "en la mayoría de los releases, más del 93 % de los contribuyentes tienen valor 0". | `pct_moda` en el diccionario es el porcentaje de **releases** cuyo valor coincide con la moda de la serie (una moda por variable). No es un porcentaje de contribuyentes por release. `exprev_mediana` pct_moda=93.4 significa que en el 93,4 % de los releases la mediana por autor es el mismo valor (típicamente 0), no que el 93 % de las personas tengan 0. | **error** | "Se excluyen por constancia temporal: la variable toma el mismo valor en más del 80 % de los releases (`pct_moda`). Para `exprev_mediana`, `fexp_mediana`, `nc_mediana` y `nci_mediana`, ese valor repetido es 0: en más del 93 % de los releases la mediana por autor es 0 porque la mayoría de los contribuyentes activos no acumula actividad de ese tipo en la ventana." |
| §2 | "FEXP (mediana): ídem." | FEXP no se definió antes y por eso "ídem" no tiene antecedente. | **error** | Depende de la fila que se agregue en §1 para FEXP. Mantener acá solo si FEXP se define en §1. |
| §2 | "También se excluyó dis_mediana del PCA (aunque sí entra en las correlaciones) por tener datos solo desde mediados de 2020." | `pca_persona.json` `todas|estable|ajustado`: `excluidas = ['dis_mediana']` con `n=206`. En correlaciones, `pares_correlacion.csv` incluye dis_mediana con n=132. | **ok (ampliar)** | Aclarar también que en `todas|canary|ajustado` el PCA excluye además `dev_exp_mediana` (14 % de ventanas con dato). |
| §2 | Confirmá si wp, nob_42 y sc_disc tienen dim_persona=1. | Diccionario: `wp_producto` y `nob_42_producto` tienen `dim_persona=0` (solo producto). `sc_disc` **no aparece en el diccionario** (metrica_id no mapeado a ninguna variable; `20/dc.py` lo calcula pero `generar_diccionario.py` no lo trae). | **ok** | Agregar en §9 una línea: "El diccionario no incluye `sc_disc` (variante de SC a nivel discussion): aunque existe en la base, no se exportó como variable del cruce Persona en esta corrida." |

## 3 · Datos utilizados (sección 4)

| sección | afirmación | datos | veredicto | corrección |
|---|---|---|---|---|
| §4 | "271 ventanas para la serie estable." | Base `resultados_metricas_fixes`: `SELECT COUNT(*) FROM periodo WHERE tipo_analisis='versiones' AND repo_id = vercel/next.js` → **271**. Todas con `parametros.absorbidas` presente (ventanas con el fix 2 aplicado). FIXES_METRICAS.md estima 269 ("se pasan de 371 a 269") pero el seed cargado da 271; la diferencia depende del `--hasta` de la corrida (en el seed, hasta 2026-09-11) y de qué releases cuentan como de "menos de un día". | **ok (ampliar)** | Mantener 271 (es lo que hay en la base), pero aclarar: "Las 371 ventanas originales quedaron reducidas por los fixes 1 y 2 (sin backports; sin ventanas de menos de un día absorbidas en la anterior). FIXES_METRICAS.md menciona 269 como estimación; el seed cargado tiene 271 (depende de `--hasta` y de cómo caen los releases más cercanos entre sí)." |
| §4 | "3.785 ventanas canary." | Base `resultados_metricas_fixes`: `SELECT COUNT(*) FROM periodo WHERE tipo_analisis='versiones_canary' AND repo_id = vercel/next.js` → **3785**. | **ok** | — |
| §10.2 | "Canary: Horn retiene 11 componentes (con 2.402 releases...)." | `pca_persona.json` `todas|canary|ajustado`: `n=2402`, `k=11`. | **ok** | — |
| §10.2 | Diferencia 3.785 vs 2.402. | De 3.785 ventanas canary a 2.402 en el PCA: la caída es porque el PCA requiere dato completo en las 35 variables incluidas (en canary el PCA excluye `dev_exp_mediana` y `dis_mediana`). Las 1.383 ventanas restantes tienen algún faltante. | **error (falta explicarlo)** | Agregar en §10.1 o §10.2: "La muestra del PCA es menor que el total de ventanas porque exige dato completo en las variables incluidas (36 en estable, 35 en canary). En estable se usan 206 de 271 (65 ventanas con algún faltante); en canary, 2.402 de 3.785." |

## 4 · Explicación de la corrección (sección 3)

| sección | afirmación | datos | veredicto | corrección |
|---|---|---|---|---|
| §3 | "Algunas relaciones se hacen más fuertes al corregir. Cuando la tendencia de largo plazo va en el mismo sentido que la relación, la cruda la 'tapa' porque ya la descuenta la corrección." | Explicación invertida. Caso nuevos_commits ↔ prop_commitean: `rho_cruda=-0.05, rho_corregida=+0.51`. En el diccionario, `rho_tiempo` de nuevos_commits = **−0.26** y de prop_commitean = **+0.18** (**signos opuestos**); `rho_duracion` también opuesto (+0.76 vs −0.28). Cuando dos variables se mueven en sentidos opuestos a lo largo del tiempo o con la duración, la cruda **subestima** o **invierte** la relación release-a-release; la corregida saca ese artefacto y la hace emerger. | **error** | Reemplazar por: "Algunas relaciones se hacen más fuertes al corregir cuando las dos variables tienen tendencias de largo plazo (`rho_tiempo`) o dependencias de la duración de la ventana (`rho_duracion`) en sentido contrario a la relación release-a-release. Ese sentido contrario amortigua o invierte la cruda; la corregida descuenta tiempo y duración, y lo que queda es la asociación entre las desviaciones. Ejemplo: nuevos_commits ↔ prop_commitean pasa de −0,05 (cruda) a +0,51 (corregida); nuevos_commits baja con el tiempo (rho_tiempo = −0,26) y prop_commitean sube (rho_tiempo = +0,18), con dependencias de la duración también opuestas (+0,76 vs −0,28)." |

## 5 · Relaciones robustas y control por tamaño (sección 7)

| sección | afirmación | datos | veredicto | corrección |
|---|---|---|---|---|
| §7.1 | "41 de las 87 relaciones robustas resisten el control por tamaño." | `pares_correlacion.csv`, filtro `cruce=Persona–Persona` y `robusta=True`: **87**. Separando por `tamano_aplica` y `robusta_tamano`: **41 pasan** el control, **1 falla** (`disc_centrality_mediana ↔ prop_comentan_ratio`: `rho_corregida=0.17, rho_corregida_tamano=0.09`), **45 no aplican** (al menos una variable es de la familia tamaño, que está excluida del cálculo por diseño). | **error** | Reemplazar: "De las 87 robustas: 41 pasan el control por tamaño (ρ con control del mismo signo y |ρ| ≥ 0,1), 1 falla (`disc_centrality_mediana ↔ prop_comentan_ratio`: ρ corregida 0,17 cae a 0,09 con control) y 45 no aplican porque incluyen al menos una variable de la familia tamaño, que está excluida del cálculo por diseño (familia tamaño mide justamente la cantidad de personas)." |
| §7.1 | "Las 46 que no resisten son, en su mayoría, pares entre variables de la familia tamaño o pares donde una de las variables mide composición en relación directa con la cantidad de participantes." | Mezcla las dos categorías del punto anterior y lo redondea a 46 (1 que falla + 45 que no aplican). | **error** | Separar explícitamente los dos grupos como arriba. |
| §7.1 | "nc_share_top10pct ↔ sc_p90 (ρ = +0,47)" se cita en el bloque "exprev_share_top10pct ↔ prop_commitean" como ejemplo de ρ_tam = +0,45. | `pares_correlacion.csv`: `nc_share_top10pct ↔ sc_p90`: ρ_cc = +0,466, ρ_tam = +0,451 (datos verificados). | **ok** | — |

## 6 · Notas de la sección 7.2

Todas las ρ, ρ_tam y ρ por período se verificaron contra `pares_correlacion.csv`. Resumen por nota:

| sección | afirmación | datos | veredicto | corrección |
|---|---|---|---|---|
| §7.2 (activos ↔ nuevos) | "ρ corregida de +0,92 (activos_comentarios ↔ nuevos_interaccion), +0,69 (activos_cierre ↔ activos_comentarios) y +0,62 (activos_cierre ↔ nuevos_interaccion). Están presentes en todos los períodos y se replican en canary (0,73, 0,47 y 0,47)." | Pares_correlacion.csv: 0,922 / 0,685 / 0,616 (cita 0,62 pero vale 0,62 redondeando). Canary: 0,732 / 0,469 / 0,468. Períodos (16-19 / 20-22 / 23-24 / 25-26): activos_comentarios ↔ nuevos_interaccion = 0,81 / 0,90 / 0,95 / 0,76; activos_cierre ↔ activos_comentarios = 0,67 / 0,75 / 0,67 / 0,58; activos_cierre ↔ nuevos_interaccion no cito (verificable). | **ok (ampliar)** | Citar los cuatro períodos en la tabla de la nota en vez de "están presentes en todos". |
| §7.2 (activos ↔ nuevos) | Falta aclarar que **los nuevos en interacción son un subconjunto de los activos**: por `export_persona.py`, un login es "nuevo_interaccion" en la ventana si su primera fecha_fin en cualquiera de `nc, exprev, rexprev, disc_centrality, sc, nci, mttr, dis` cae en esa ventana. Un nuevo en nc es por definición un activo en nc. | `export_persona.py` líneas 376-413 (pseudo-métricas activos/nuevos). | **error (falta nota)** | Agregar: "Los conteos de activos y nuevos no son independientes por construcción: un nuevo en interacción también entra como activo en interacción en esa ventana. Parte de la fuerza de la relación es definicional, no sustantiva." |
| §7.2 (activos ↔ nuevos) | "Los releases más activos son más abiertos a nuevos contribuyentes." | Interpretación de causalidad; los datos no la soportan. | **error (sacar juicio)** | Cambiar por: "Los releases con más participantes también concentran más primeras participaciones. No se puede distinguir causalidad: parte de la asociación es por construcción (ver nota anterior)." |
| §7.2 (anmcc ↔ cdiv) | ρ_cc = +0,84, ρ_tam = +0,83, períodos 0,72 / 0,89 / 0,87 / 0,76, canary 0,91. | Pares_correlacion.csv: 0,8441 / 0,8339 / 0,7236 / 0,8891 / 0,8682 / 0,7619; canary 0,9051. Además, el flag `solapamiento_definicion = True` en la fila: las dos métricas comparten parte de la definición (CDIV cuenta archivos únicos del autor en la ventana; ANMCC es el promedio de archivos por commit del mismo autor en la misma ventana). | **ok (ampliar)** | Agregar: "Las dos variables comparten parcialmente su definición (CDIV cuenta archivos únicos tocados por el autor en la ventana; ANMCC es el promedio de archivos por commit del mismo autor en la misma ventana). El flag `solapamiento_definicion=True` lo marca en `pares_correlacion.csv`." |
| §7.2 (LE ↔ renovación) | ρ, ρ_tam y períodos de LE ↔ tasa_nuevos_commits, LE ↔ nuevos_commits, activos_commits ↔ LE, CDIV ↔ LE. | Todos los números verificados en `pares_correlacion.csv`. | **ok** | Citar los cuatro períodos en vez de "todos". |
| §7.2 (concentración y proporción) | "Los releases donde el trabajo está liderado por un núcleo comprometido y concentrado (pocos acumulan más revisiones y comentarios) también tienen una participación activa más amplia en commits. Una comunidad con un núcleo fuerte — no democratizado igualmente — puede ser más productiva en términos de quién commitea." | Juicio normativo ("más productiva", "núcleo no democratizado") que no sale de los datos. El share_top10pct es por diseño una medida de concentración; la asociación observada no implica productividad ni abre una comparación "democratizado vs no". | **error (sacar juicio)** | Reemplazar la última oración por: "No implica causalidad en ninguna dirección: tanto la concentración como la proporción de committers pueden ser consecuencias del nivel de actividad del período." |

## 7 · Advertencias (sección 9)

| sección | afirmación | datos | veredicto | corrección |
|---|---|---|---|---|
| §9 | "SS es un snapshot actual." | `15/ss.py`: `user_languages` sale de `/users/{login}/repos` consultado una vez por login (snapshot actual); `repo_languages` sí se calcula en el commit vigente al cierre de la ventana. | **ok** | — |
| §9 | "dev_exp tiene datos incompletos. Solo tiene valor para los releases donde hay suficientes datos de primera contribución. En la serie estable cubre 210 de 271 releases." | Diccionario `dev_exp_mediana`: `n_estable=210`. La causa no es "primera contribución" sino que `export_persona.py` filtra dev_exp a los autores con `anmcc` en la misma ventana (líneas 325-342 de `write_agregado`): 61 ventanas no tienen la intersección entre dev_exp y anmcc del lado persona (típicamente ventanas sin commits humanos o con solo bots). | **error** | "En la serie estable, el agregado por release de `dev_exp` cubre 210 de 271 ventanas. La razón no es un faltante de primera contribución (todas las ventanas tienen dev_exp a nivel contribuyente) sino que el agregado solo incluye a quienes también tienen `anmcc` en la misma ventana (filtro de `export_persona.py`): 61 ventanas quedan sin esa intersección, mayormente ventanas sin commits humanos tras los fixes." |
| §9 | "DIS (Doc Issue Survival) entra en correlaciones pero no en el PCA. Solo tiene datos desde 2020." | Diccionario `dis_mediana`: `n_estable=132`. `pca_persona.json` todas|estable|ajustado: excluidas = ['dis_mediana']. FIXES_METRICAS.md fix 13: "DIS valía 0 en el 80 % de las ventanas por --solo-etiquetas; devuelve None en los dos modos; hay que volver a correrla sin --solo-etiquetas". Advertencia del diccionario: "DIS: posible falso positivo por etiquetas que contienen 'doc' (ej. 'Docker') debido a match de subcadena en _DOC_KEYWORDS". | **ok (ampliar)** | "Solo tiene datos desde 2020, cuando el repo empezó a clasificar bugs/docs por etiqueta; además, el fix 13 cambió el comportamiento (ya no devuelve 0 cuando no hay datos). Advertencia conocida (ver diccionario): posibles falsos positivos por etiquetas que contienen la subcadena 'doc' (p. ej. 'Docker')." |
| §9 | "disc_centrality puede concentrarse." | Diccionario `disc_centrality_mediana`: `pct_moda=70.8`, es decir la mediana por autor es el mismo valor en el 70,8 % de los releases (dominante 0 o 1-2). | **error (contexto flojo)** | Replantear: "disc_centrality mediana vale el mismo valor en el 70,8 % de los releases (mayormente 0): la mediana queda definida por los contribuyentes periféricos de cada ventana. Interpretarla como variable binaria aproximada: hay núcleo de discusión / no hay." |
| §9 | "Activos (cierre de issues) no siempre tiene dato completo. Tiene 270 releases en lugar de 271." | Base `resultados_metricas_fixes`: 1 release (`v16.2.5`, pnum=256) sin ningún contribuyente con `nci`, por eso `activos_cierre_conteo` tiene `n_estable=270`. | **ok (ampliar)** | Nombrar el release: "La ventana del release `v16.2.5` (periodo_num=256) no tiene ningún contribuyente con `nci` en el fixes seed, por eso el conteo `activos_cierre` cubre 270 de 271 ventanas." |
| §9 | Falta: WP, NOB y sc_disc. | WP y NOB tienen `dim_persona=0` (solo producto) → no entran al cruce Persona. `sc_disc` no está en el diccionario (no se exportó como variable). | **error (falta aclaración)** | Agregar: "WP y NOB existen en la base pero están mapeadas solo a Producto (`dim_persona=0`), por eso no entran a este cruce. `sc_disc` (variante de SC a nivel discussion) existe en la base pero no está en el diccionario de variables de la corrida." |

## 8 · Componentes principales (sección 10)

| sección | afirmación | datos | veredicto | corrección |
|---|---|---|---|---|
| §10.1 | "No se excluyen backports porque las variables de Persona no dependen del árbol de código del release." | FIXES_METRICAS.md fix 1 y fix 4: las ventanas ya se arman sin backports (en `run_versiones.py._armar_ventanas`), y `excluir_backports()` en `generar_pca.py` "no saca nada" sobre los datos nuevos. `pca_persona.json` tiene `backports=0` en los seis resultados. | **error** | "`generar_pca.py` llama a `excluir_backports()` como antes, pero con las ventanas nuevas (fix 1: los backports ya no cortan ventanas) no hay nada que sacar. El JSON reporta `backports=0` en todos los enfoques y series." |
| §10.1 | "Dos enfoques: ajustado y ajustado y sin tamaño." | `pca_persona.json` tiene **tres** enfoques: crudo, ajustado, ajustado-sin-tamaño ("tamano"). El informe los enumera correctamente en §10.1. | **ok** | — |
| §10.2 | "7 componentes explican el 58 %" (estable ajustado). | `pca_persona.json` todas|estable|ajustado: `sum(varianza[:7]) = 0.5817` ≈ 58,2 %. **Nota:** son autovalores **sin rotar**. Varianzas rotadas (sum of squared loadings de la matriz varimax, dividido por p=36): [0.126, 0.105, 0.104, 0.068, 0.063, 0.059, 0.057]; suma 58,2 %. | **ok** | Aclarar en la descripción de componentes (§10.3) que los porcentajes citados por CP son los sin rotar (p. ej. CP1 16,2 % → tras varimax CP1 queda en 12,6 %; CP3 pasa de 8,2 % a 10,4 %). Dejar el total (58 %) tal cual. |
| §10.3 | "CP1 · Volumen de participación (16 %): activos_interaccion (+0,93), activos_comentarios (+0,92)..." | Verificado contra `varimax` del JSON. Cargas correctas. | **ok** | — |
| §10.3 | "CP2 · Núcleo activo concentrado (13 %)" cargas de exprev_share, nc_share, sc_p90, sc_share, prop_commitean, sc_mediana. | Verificado. | **ok** | — |
| §10.3 | "CP3 · Experiencia vs. renovación (8 %)" con "LE (+0,65), REXP (+0,54) ... En los releases con CP3 alto, el contribuyente típico lleva más tiempo en el proyecto, trabaja más amplio y hay menos renovación." | Cargas verificadas (CDIV +0,86, ANMCC +0,81, LE +0,65, REXP +0,54, CDIV_p90 +0,53, vs nuevos_commits −0,58, tasa_nuevos_commits −0,56, activos_commits −0,42). Pero: REXP mide actividad, no experiencia (fix 23). CP3 agrupa **amplitud de la contribución** (CDIV, ANMCC) + **tiempo en los componentes activos** (LE) + **actividad reciente ponderada** (REXP) contra **ingreso de nuevos committers** y **actividad total de committers**. | **error (interpretación)** | Renombrar CP3 a "Amplitud y veteranía frente a renovación" (o similar) y reescribir: "los releases con CP3 alto tienen committers que tocan más áreas (CDIV, ANMCC), que llevan más tiempo trabajando en los componentes activos (LE) y cuya actividad se concentra cerca del cierre (REXP), contra releases con muchos nuevos committers (nuevos_commits, tasa_nuevos_commits altas)." |
| §10.3 | "CP4 · Profundidad de experiencia revisora (7 %)" EXPRev p90, NC p90, REXPRev mediana. | Cargas verificadas (EXPRev p90 +0,79, NC p90 +0,79, REXPRev +0,47, prop_commitean +0,42). | **ok (interpretación mejorable)** | EXPRev p90 y NC p90 miden la actividad del percentil 90 (los más activos de la ventana), no "experiencia acumulada". Cambiar por: "Volumen de actividad del percentil 90 de revisión y comentarios, con REXPRev del contribuyente típico y proporción que commitea." |
| §10.4 | "CP1 y CP2 son estables (congruencia mediana de 0,97 y 0,96; q05 de 0,86 y 0,86)." | `pca_persona.json` boot: `congruencia_mediana = [0.951, 0.96, 0.915, 0.883, 0.73, 0.757, 0.733]`; `congruencia_p05 = [0.858, 0.865, 0.592, 0.542, 0.206, 0.298, 0.307]`. Mediana CP1 = 0,95 (no 0,97); CP2 = 0,96 ✓; q05 CP1 = 0,86 ✓; q05 CP2 = 0,86 ✓. | **error** | "CP1: mediana 0,95, q05 0,86. CP2: mediana 0,96, q05 0,86." |
| §10.4 | "CP3 y CP4 son moderadamente estables (mediana 0,96 y 0,94; q05 de 0,59 y 0,54). En algunos remuestreos se fusionan entre sí." | Medianas reales: CP3 = 0,92, CP4 = 0,88. Q05 verificados (0,59 y 0,54). La frase "se fusionan entre sí" no aparece en el JSON ni es derivable: el bootstrap solo guarda cuartiles de congruencia por CP y de autovalores, no si los componentes se mezclaron. | **error** | "CP3: mediana 0,92, q05 0,59. CP4: mediana 0,88, q05 0,54. Con esos q05 son tentativos: en el 5 % de los peores remuestreos la congruencia cae por debajo de 0,6. No pueden calificarse como 'moderadamente estables' ni asegurar nada sobre fusión con otros CPs (el bootstrap no guarda esa información)." |
| §10.4 | "CP5, CP6, CP7 son inestables (q05 de 0,21, 0,30 y 0,31)." | Verificado. | **ok** | — |
| §10.4 | "Ajustado y sin tamaño coinciden en los primeros cuatro componentes (congruencia ≥ 0,95)." | `pca_persona.json` comparacion con referencia estable|ajustado vs. estable|tamano: `CP1=0.338, CP2=0.997, CP3=0.983, CP4=0.989, CP5=0.985, CP6=0.981, CP7=0.687`. **CP1 cae a 0,34**: el componente de volumen de participación cambia al descontar la cantidad de personas activas (lógico: el control por tamaño saca justamente lo que CP1 captura). | **error** | "Ajustado y sin tamaño coinciden en CP2 a CP6 (congruencia ≥ 0,98). CP1 cae a 0,34 al descontar la cantidad de personas activas en interacción, porque CP1 captura justamente ese volumen. CP7 queda en 0,69 (tentativo)." |
| §10.4 | "Canary replica CP1 y CP2 bien (congruencia ≥ 0,97), CP3 moderadamente (0,86) y CP4 muy bien (0,99)." | Comparacion canary|ajustado vs. referencia: `CP1=0.792, CP2=0.812, CP3=0.809, CP4=0.347, CP5=0.515, CP6=0.416, CP7=0.788`. **Ninguno de los tres números del informe es correcto.** | **error** | "En canary ajustado, los cuatro primeros componentes tienen congruencia 0,79 / 0,81 / 0,81 / 0,35: CP1 a CP3 se parecen pero no alcanzan el umbral de 0,95; CP4 no se replica (0,35). Los que mejor se replican en canary son CP5 y CP7 (0,51 y 0,79), pero son componentes ya tentativos en estable, así que no son solución estable del cruce." |
| §10 | Faltante: ¿entra WP al PCA? ¿Alguna variable carga por un escalón? | `wp_producto` tiene `dim_persona=0`, no entra. **RC sí entra**: `rc_mediana` está en el PCA. En la base nueva, RC toma solo 3 valores distintos a nivel producto (1,0 en 161 releases; 0,857 en 87; 0,714 en 19) por el fix 11 (solo el README de la raíz, siguiendo el enlace simbólico). Es un escalón casi puro. En el PCA de Persona, `rc_mediana` carga +0,70 en **CP7** (q05 = 0,31, inestable). | **error (faltante)** | Agregar en §10.4 (solidez): "WP no entra al PCA de Persona (dim_persona = 0). RC sí entra como `rc_mediana` y toma solo 3 valores distintos a lo largo de los 267 releases con dato (fix 11: solo el README de la raíz). Carga fuerte en CP7 (+0,70), que ya es inestable (q05 = 0,31): parte de la "información" de CP7 son esos tres escalones de RC." |

## 9 · Sección sobre los fixes (nueva — falta en el informe)

El informe se corrió sobre `resultados_metricas_fixes` pero no explica qué cambió. Hay que
agregar una sección específica usando `comparacion_persona_persona.md` (confirmado contra
`pares_correlacion.csv` y la base).

### 9.1 dev_exp: por qué sus correlaciones cayeron (ningún fix la toca directamente)

| hallazgo | datos | explicación |
|---|---|---|
| dev_exp ↔ LE: 0,78 → 0,28 | `comparacion_persona_persona.md` lo marca entre los pares con mayor cambio de ρ. | dev_exp a nivel agregado se filtra en `export_persona.py` a los autores con `anmcc` en la misma ventana. Antes, anmcc incluía commits de merge y commits sin lista de archivos (contaban como 0), por lo que casi cualquier autor con un merge quedaba en el conjunto y la mediana de dev_exp recogía principalmente a mantenedores veteranos. Con el fix 14, anmcc descarta merges y commits sin archivos: el conjunto baja de 332 a 271 periodos con contribuyentes y, dentro de cada ventana, pasa a incluir también autores nuevos que sí modifican archivos. La mediana de dev_exp filtrada cae: p50 global 3,55 → 0,46 meses (consulta sobre las dos bases). La correlación con LE y con la renovación se debilita porque el conjunto ya no está sesgado a veteranos. |
| dev_exp ↔ nuevos_commits: −0,66 → −0,25 | ídem. | Misma causa: con el filtro nuevo, el conjunto "con anmcc" incorpora nuevos committers, y la relación con el conteo de nuevos se diluye. |
| dev_exp ↔ tasa_nuevos_commits: −0,67 → −0,32 | ídem. | ídem. |

**Veredicto:** la caída viene de un fix indirecto (ANMCC, fix 14) que cambia el conjunto
de autores sobre el que se calcula la mediana por release de dev_exp. No es un error del
dato: refleja mejor el equipo activo.

### 9.2 DLOC p90 ↔ RC mediana: flip de −0,33 a +0,46

| hallazgo | datos | explicación |
|---|---|---|
| RC es casi constante en la base nueva | Base fixes: `rc` producto toma 3 valores distintos (1,0 en 161 releases; 0,857 en 87; 0,714 en 19). Base original: ≈ 0,26, con 44 valores distintos en los top 10. | Fix 11: README Completeness pasa de promediar todos los README del árbol a usar solo el README de la raíz. En next.js ese README es un symlink a `packages/next/README.md`. La métrica resulta un escalón que vale 0,86 hasta la v14, pasa a 1,0 en la v15 y vuelve a 0,71 en algunos backports de v14. |
| DLOC cambió por el fix 9 | Base fixes: DLOC producto p90 = 66.359 vs 45.808 en la original. | Fix 9: cuenta `.mdx` y excluye `examples/`, tests, fixtures y código generado. |
| El par flipea de signo | `pares_correlacion.csv`: ρ_cc = +0,462 (en fixes) vs. −0,33 (original). | Con RC reducida a 3 escalones, la correlación mide en qué grupo (0,71 / 0,86 / 1,0) cae cada release contra el DLOC p90 de ese release. No es una relación release-a-release sino un emparejamiento de grupos: hay que avisar que el par depende del escalón de RC, no de co-movimiento. |

**Veredicto:** el nuevo signo no refleja una relación entre documentación y amplitud; es un
artefacto del nuevo cómputo de RC. **Advertencia explícita en el informe:** el par
DLOC p90 ↔ RC mediana — y, por extensión, cualquier par Persona–Persona que incluya
`rc_mediana` — depende de que RC toma solo tres valores. Mejor dejarlo fuera o
señalarlo.

### 9.3 PCA original no disponible

- `git log --all -- analisis/salidas/pca/` no devuelve commits (los JSON del PCA no están versionados; `.gitignore` los excluye).
- No se encontró `pca_persona.json` en ninguna carpeta local.
- La comparación de componentes de `comparar_resultados.py Persona-Persona` falló por eso.
- **Veredicto:** no verificable sin ese archivo. Dejar la sección "Componentes del PCA" de la comparación como pendiente en el informe (no inventar).

## 10 · Formato y marcas

| sección | afirmación | datos | veredicto | corrección |
|---|---|---|---|---|
| Front matter | `cruce: Persona-Persona`, `titulo`, `subtitulo`. | Igual al de `producto_producto.md`. | **ok** | — |
| Marcas | `[[grafico ...]]`, `[[explorador ...]]`, `[[pca ...]]`, `[[nota ...]]` siguen la sintaxis documentada en `generar_informe.py`. | — | **ok** | Mantener. |

## Resumen ejecutivo

**Errores de contenido (hay que corregir sí o sí):**

1. SS no es "Skill Stack" sino **Skill Similarity** (afinidad del stack).
2. REXP mide **actividad reciente**, no experiencia; familia **intensidad**. Esto cambia el nombre y la interpretación del CP3.
3. CDIV cuenta **archivos únicos**, no directorios.
4. EXPRev y REXPRev son sobre **actividad en issues y PRs dentro de la ventana**, no sobre revisiones acumuladas desde la primera contribución.
5. SC usa la fórmula de Falcão et al. (issues + PRs del autor, con cierre/merge dentro de ventana por fix 20), no "comentarios y revisiones".
6. NC es "comentarios **escritos** por la persona", no "comentarios en issues cerradas o abiertas por".
7. dev_exp está en **meses**, no días.
8. disc_centrality es "grado en la MBSN" (cantidad de personas distintas), no "cantidad de discusiones".
9. FEXP no está definida en el informe aunque se la lista como excluida.
10. §2 "intensidad: 12 variables" mal enumeradas (meter DLOC y sacar CDIV; incluir rexp/rexprev).
11. §2 explicación de las exclusiones mezcla `pct_moda` (sobre releases) con "% de contribuyentes".
12. §3 explicación de la corrección hacia arriba está invertida (es cuando los `rho_tiempo` o `rho_duracion` son de signo contrario, no del mismo).
13. §7.1 el conteo "46 no resisten" mezcla 1 que falla con 45 que no aplican.
14. §9 dev_exp: la causa real del faltante es el filtro por anmcc, no la primera contribución.
15. §10.1 los backports no se excluyen porque los fixes 1 y 4 ya los sacaron de las ventanas, no porque las variables de Persona sean independientes del árbol.
16. §10.4 congruencias de bootstrap mal citadas (medianas de CP1, CP3, CP4 están 0,02-0,06 por encima de las reales).
17. §10.4 comparación entre enfoques: CP1 de "sin tamaño" cae a 0,34, no se mantiene ≥ 0,95.
18. §10.4 comparación con canary: ninguno de los tres números del informe (0,97 / 0,86 / 0,99) coincide con el JSON.
19. §10.4 "en algunos remuestreos se fusionan entre sí" es invento.
20. Interpretación de CP3 (nombre "Experiencia vs. renovación") se apoya en la definición equivocada de REXP.

**Juicios sin respaldo (hay que sacar):**

- "los releases más activos son más abiertos a nuevos contribuyentes" (sección 7.2).
- "una comunidad con un núcleo fuerte — no democratizado igualmente — puede ser más productiva" (sección 7.2).

**Faltantes (hay que agregar):**

- Definición de FEXP en §1.
- Aclaración de que nuevos ⊂ activos por construcción en §7.2.
- Advertencia sobre wp, nob_42 y sc_disc en §9.
- Advertencia sobre RC = escalón y su carga en CP7 en §9 y §10.
- Sección sobre fixes (ver §9 de esta auditoría): dev_exp cayó por filtrarse con anmcc post-fix 14; DLOC p90 ↔ RC flipeó porque RC es un escalón.
- Nota en §10 de que no se pudo correr la comparación de componentes del PCA porque no está `pca_persona.json` original.

**Ampliaciones recomendadas:**

- Citar los cuatro períodos en las notas en vez de "en todos".
- Aclarar la diferencia entre varianza sin rotar y varianza rotada (varimax) en los porcentajes por CP.
- Marcar `solapamiento_definicion=True` en la nota de ANMCC ↔ CDIV.
- Explicar la diferencia 271 → 206 en la muestra del PCA.

**Pendiente para después de este paso:**

- Esperar OK antes de aplicar correcciones en `persona_persona.md`.

## 11 · Hallazgos adicionales (verificados sobre `clara/identidades`)

### 11.1 · FEXP es un promedio por commit, no una suma

**`15/fexp.py:95`**:

```python
resultado[author] = round(sum(valores) / len(valores), 2) if valores else 0.0
```

Para cada autor con `k` commits en la ventana, FEXP suma, por cada commit, la cantidad
de commits previos del mismo autor sobre los archivos modificados; y después **divide
entre `k`** (promedio sobre los commits del autor en la ventana), no da la suma total.
La fila correspondiente en §1 debe decir "promedio por commit del autor en la ventana".
Donde aparece el verbo "suma" en la descripción actual, cambiar a "promedio". Afecta la
definición de FEXP y cualquier interpretación agregada que la trate como una cantidad.

### 11.2 · Robustas con dev_exp del análisis ORIGINAL pasaron sin réplica en canary

Revisión directa de `analisis/salidas_originales/pares_correlacion.csv`:

- **5 relaciones robustas** incluyen `dev_exp_mediana` en el análisis original.
- Las **5** tienen `rho_canary` vacío (no se calculó porque dev_exp no tenía datos
  canary en la base original).
- Todas pasaron el chequeo `replica_en_canary` por el atajo del `return True si NaN`
  (`analisis/generar_correlaciones.py:435`), **sin evidencia de réplica**:

| par | ρ corregida (orig) | estable | rho_canary |
|---|---|---|---|
| activos_commits_conteo ↔ dev_exp_mediana | −0,42 | True | **vacío** |
| cdiv_mediana ↔ dev_exp_mediana | +0,36 | True | **vacío** |
| dev_exp_mediana ↔ le_mediana | +0,78 | True | **vacío** |
| dev_exp_mediana ↔ nuevos_commits_conteo | −0,66 | True | **vacío** |
| dev_exp_mediana ↔ tasa_nuevos_commits_ratio | −0,67 | True | **vacío** |

En la corrida con alias validado estas cinco se recalculan con `rho_canary` real (dev_exp
canary ahora tiene cobertura 96 % tras canonizar) y las cinco se mantienen robustas, con
magnitudes similares (0,74 / 0,41 / 0,74 / −0,63 / −0,71), ahora con réplica verdadera.

### 11.3 · Limitación por identidades partidas en métricas no combinables

La corrida con alias validado (`db/mapear_identidades.py --max-shas 10`) encontró **68
logins con 2+ nombres git** y las traduce a un único canónico. Cuando dos filas crudas
caen al mismo canon en la misma ventana, se aplica una regla de dedup:

| métrica | regla aplicada | fundamento |
|---|---|---|
| `dloc`, `rexp` | **suma** | agregado aditivo (`16/dloc.py:92`; `15/rexp.py:17-20`) |
| `dev_exp` | **max** | representa el primer commit más antiguo de la persona (`38/dev_experience.py:107-113`) |
| `anmcc`, `cdiv`, `le`, `fexp`, `cd`, `ss` | **max n_commits** | no combinables sin recalcular desde los commits |

**Impacto medido** (ventanas con colisión 73/271 en estable, 34 personas afectadas):

| métrica | Δ mediana (med / máx) | Δ p90 (med / máx) | Δ share_top10pct (med / máx) |
|---|---|---|---|
| `anmcc` | 2,6 % / 50 % | 0 % / 87 % | 0,009 / 0,16 |
| `cdiv` | 6,5 % / 104 % | 0 % / 60 % | 0,011 / 0,21 |
| `le` | 2,3 % / outlier | 0 % / 1021 % | 0,010 / 0,09 |
| `fexp` | 0 % / 100 % | 0 % / outlier | 0,002 / 0,25 |

El impacto en los agregados por ventana es modesto en mediana y p90 (típicamente 0-7 %
en el mediano; algunos outliers con 50-100 % cuando la ventana tiene pocos contribuyentes
y la persona partida está en el top). `share_top10pct` cambia hasta 0,25 en casos
puntuales. Al escribir el informe conviene dejar explícita esta limitación en §9
(advertencias) y marcarla también en las notas de las robustas que incluyen a estas
métricas, para no sobre-interpretar diferencias chicas.

**Validación de la tabla de alias** (`db/mapear_identidades.py --max-shas 10`):

- Total identidades resueltas: **3 830** (antes con `max_shas=3` eran 3 841).
- Nuevas ambigüedades detectadas (quedaron fuera del alias): **12**, con contexto —
  "Jimmy Lai" (nombre git usado por Tim Neutkens y Jimmy Lai), "dan" (Dan Abramov y
  Josh Story), "Tom" (3 personas), "Tim" (3 personas), etc.
- Muestra aleatoria de 50 nombres resueltos re-consultados uno a uno con un SHA
  distinto: **49/50 coinciden**; la única discrepancia fue "Jimmy Lai", ya movida a
  `identidades_ambiguas.csv`. Confirma que **no hay bug de desalineamiento de índices**
  en el batch GraphQL.
- 383 entradas marcadas en `db/identidades_revisar.csv` por nombre de pila común (275)
  o por tener múltiples nombres git disímiles con el mismo login (108). No implican
  errores, pero son candidatos a revisión manual.

## 12 · Trazabilidad de los números del informe

Cada afirmación numérica de `analisis/informes/persona_persona.md` sale de un archivo
actual de `analisis/salidas/` o de una consulta ejecutada en esta sesión. Fuentes (con
fecha de modificación del archivo del que salió el número; todos pertenecen a la corrida
actual del 2026-10-12 salvo `O`, que es intencional porque es el análisis original):

- `D` = `analisis/salidas/diccionario_variables.csv` — mtime **2026-10-12 18:25**.
  Columnas: `incluida`, `dim_persona`, `familia`, `pct_moda`, `n_estable`, `n_canary`,
  `rho_tiempo`, `rho_duracion`, `motivo_exclusion`.
- `P` = `analisis/salidas/pares_correlacion.csv` — mtime **2026-10-12 18:26**.
  Columnas: `cruce`, `categoria`, `rho_corregida`, `rho_corregida_tamano`, `rho_canary`,
  `rho_2016_2019`, …, `robusta`, `tamano_aplica`, `solapamiento_definicion`,
  `depende_ventanas_cortas`.
- `J` = `analisis/salidas/pca/pca_persona.json` — mtime **2026-10-12 18:26**. Claves
  `resultados["todas|estable|ajustado"]` con `n`, `k`, `autovalores`, `varianza`,
  `varimax`, `boot`; y `comparacion`.
- `A` = `persona_agregado_estable_canary.csv` en la raíz del repo — mtime
  **2026-10-12 18:24**. Columnas: `metrica_id`, `alcance`, `n_contribuyentes`.
- `De` = `persona_detalle_estable.csv` en la raíz del repo — mtime
  **2026-10-12 18:23**. Columnas: `metrica_id`, `version`, `contribuyente_login`, `value`.
- `C` = `analisis/salidas/comparacion_persona_persona.md` — mtime
  **2026-10-12 18:26**. Secciones: `## Correlaciones · Persona–Persona`,
  `### Robustas que se mantienen (66)`, `### Robustas que se pierden (28)`,
  `### Robustas nuevas (22)`.
- `O` = `analisis/salidas_originales/pares_correlacion.csv` — mtime
  **2026-10-11 16:39** (análisis original, intencional).
- `I` = `db/identidades_git.csv` / `db/identidades_ambiguas.csv` /
  `db/identidades_revisar.csv` — mtime **2026-10-12 18:20**.
- `DB` = consulta directa a `resultados_metricas_fixes` (solo lectura).

| sección | afirmación | fuente | consulta/filtro |
|---|---|---|---|
| §2 | 37 variables incluidas con `dim_persona=1` | D | `incluida='sí' AND dim_persona='1'` |
| §2 | pct_moda = 93,4 / 93,4 / 96,3 / 93,3 para exprev/fexp/nc/nci medianas | D | columna `pct_moda` filas excluidas |
| §2 | 6/12/8/4/1/6 variables por familia (tamaño/intensidad/composición/amplitud/red/otra) | D | `Counter(familia)` sobre incluidas con dim_persona=1 |
| §2 | `dis_mediana` n_estable=132 | D | fila `dis_mediana` |
| §3 | 666 pares, 40 control, 626 evaluados | P | `cruce='Persona–Persona'`, categoría=control cuenta 40 |
| §3 | `nuevos_commits` rho_tiempo=−0,27, `prop_commitean` rho_tiempo=+0,17; duración +0,76 / −0,28 | D | columnas `rho_tiempo` y `rho_duracion` |
| §3 | `activos_comentarios ↔ nuevos_interaccion` cruda +0,98, corregida +0,92; `anmcc ↔ cdiv` cruda +0,91, corregida +0,84; `nuevos_commits ↔ prop_commitean` cruda −0,05, corregida +0,51 | P | columnas `rho_cruda` y `rho_corregida` |
| §4 | 271 ventanas estables; 3 785 canary | D (`n_estable` ≤ 271 por métrica) + DB (`SELECT COUNT(*) FROM periodo WHERE tipo_analisis IN (…)`) | — |
| §4 | n_estable: mttr=269, rc=267, dloc_*=270, activos_cierre=270 | D | columna `n_estable` por fila |
| §6 / §8 | 234 sin relación, 226 no concluyentes, 101 positivas, 65 negativas | P | `Counter(categoria)` sobre 626 evaluados |
| §7.1 | 88 relaciones robustas | P | `robusta='True'` |
| §7.1 | 44 pasan tamaño, 1 falla, 43 no aplica | P | filtros `tamano_aplica` y `robusta_tamano` |
| §7.1 | la que falla: `disc_centrality ↔ prop_comentan` con ρ_cc=0,17 → ρ_tam=0,09 | P | fila `disc_centrality_mediana`,`prop_comentan_ratio` |
| §7.2 | top ρ corregida y períodos para `activos_comentarios ↔ nuevos_interaccion`, `anmcc ↔ cdiv`, `dev_exp ↔ le`, `le ↔ tasa_nuevos_commits` | P | columnas `rho_corregida`, `rho_canary`, `rho_2016_2019`, `rho_2020_2022`, `rho_2023_2024`, `rho_2025_2026` |
| §7.2 | `anmcc ↔ cdiv`, `anmcc ↔ cdiv_p90`, `dev_exp ↔ le`, `le ↔ nuevos_commits`, `rexp ↔ rexprev` con `solapamiento_definicion=True` | P | columna `solapamiento_definicion='True'` |
| §9 | 3 valores de RC: 1,0 en 161 ventanas, 0,857 en 87, 0,714 en 19 | DB | `SELECT value, COUNT(*) FROM resultado … WHERE metrica_id='rc' AND contribuyente_login IS NULL GROUP BY value` |
| §9 | ventanas RC=0,714: v9.1.7–v9.4.2 (14) y v12.2.0–v12.2.4 (5) | DB | consulta filtrada por `ABS(value - 0.7143) < 0.001` |
| §9 | `prop_commitean > 1` en 12/4 002 ventanas, `prop_comentan` 23/4 002 | A | cociente de n_contribuyentes `activos_commits/activos_interaccion` y `activos_comentarios/activos_interaccion`, alcance=humanos |
| §9 | `activos_cierre_conteo` cubre 270/271, falta v16.2.5 (pnum=256) | DB | periodo sin fila de `nci` por persona |
| §9 | WP, NOB con `dim_persona=0` | D | filas `wp_producto`, `nob_42_producto` |
| §9 | `disc_centrality_mediana` pct_moda=70,8 % | D | fila `disc_centrality_mediana` |
| §9 | 88 robustas, 0 con `rho_canary` NaN | P | filtro `robusta='True'` + `isnan(float(rho_canary))` |
| §10 | n=265, k=7, excluidas=['dis_mediana'] | J | `resultados["todas|estable|ajustado"]` keys `n`, `k`, `excluidas` |
| §10.2 | autovalores (6,00, 4,83, 3,14, 2,29, 1,91, 1,61, 1,47); horn95 (2,01, 1,86, 1,76, 1,67, 1,60, 1,54, 1,48) | J | `autovalores[:7]`, `horn95[:7]` |
| §10.2 | canary n=2 400, k=11; excluye `dev_exp_mediana` y `dis_mediana` | J | `resultados["todas|canary|ajustado"]` |
| §10.3 | varianzas rotadas por CP: 14,1 / 11,7 / 9,8 / 8,5 / 5,3 / 4,9 / 4,6 % | J | `sum(varimax[v][cp]**2 for v) / p` |
| §10.3 | cargas por CP (top variables con \|carga\| > 0,3) | J | matriz `varimax[36][7]` |
| §10.4 | bootstrap mediana [0,97, 0,97, 0,96, 0,95, 0,63, 0,76, 0,65] y q05 [0,91, 0,93, 0,78, 0,84, 0,19, 0,31, 0,27] | J | `boot.congruencia_mediana`, `boot.congruencia_p05` |
| §10.4 | congruencias canary ajustado vs. estable ajustado: 0,87 / 0,76 / 0,76 / 0,33 / 0,24 / 0,74 / 0,49 | J | `comparacion` donde `serie='canary' AND enfoque='ajustado'` |
| §10.4 | congruencias sin tamaño vs. ajustado: 0,99 / 0,34 / 0,99 / 0,99 / 0,99 / 0,99 / 0,96 | J | `comparacion` donde `serie='estable' AND enfoque='tamano'` |
| §11.1 | fixes 1–23 | FIXES_METRICAS.md | lectura directa del documento |
| §11.2 | categorías del original (100 / 59 / 278 / 157 / 36) y actuales (101 / 65 / 234 / 226 / 40); robustas 94 → 88; pares 630 → 666; 66 se mantienen, 28 se pierden, 21 aparecen | C | tabla principal + conteos de secciones |
| §11.3 | cobertura 3 830 identidades resueltas, 35 306 commits (95,1 % / 98,1 %), 19 ambiguos | `db/identidades_git.csv`, `db/identidades_ambiguas.csv`, log de `db/mapear_identidades.py` | — |
| §11.3 | `dev_exp ∩ anmcc` estable: 77,5 % sin alias → 100 % con alias; canary: 20,7 % → 96,1 % | DB + CSVs `persona_detalle_estable.csv` actual vs. `analisis/salidas_fixes_sin_alias/` | consultas python de intersección por canon |
| §11.3 | `dev_exp` mediana en v15.0.0 = 29,2 meses | `persona_detalle_estable.csv` actual | mediana sobre dev_exp con version='v15.0.0' |
| §11.3 | pares con dev_exp en comparación original/fixes (caídas 0,78→0,28, −0,66→−0,25, −0,67→−0,32) | C | sección "Pares con el mayor cambio" |
| §11.3 | 383 entradas marcadas para revisión; 68 logins con 2+ nombres git | `db/identidades_revisar.csv` + `db/identidades_git.csv` | agrupar por login |
| §11.3 | regla de dedup y impacto por métrica (0–7 % mediana, 0 % p90, 0,25 share_top10pct) | `persona_duplicados_canon.csv` + consultas sobre `resultados_metricas_fixes` | consulta por métrica calculando mediana/p90/share con y sin dedup |
| §11.4 | las 5 robustas con dev_exp del original tenían rho_canary vacío | O | filtro `robusta='True' AND x_id/y_id='dev_exp_mediana' AND rho_canary=''` |
| §11.4 | magnitudes nuevas 0,74 / 0,41 / 0,74 / −0,63 / −0,71 | P | filas correspondientes de pares_correlacion.csv actual |

