# Fixes de métricas (branch `ine/fixes-metricas`)

Correcciones a cómo se calculan las métricas, a partir de los problemas que aparecieron en
los análisis de correlaciones y PCA de cada dimensión. La numeración sigue la del listado de
problemas identificados. Los resultados corregidos van a una base aparte
(`resultados_metricas_fixes`), así no se mezclan con los originales.

## Qué se corrigió

### A. Ventanas y serie de releases

| # | Problema | Qué cambió | Archivos |
|---|---|---|---|
| 1 | Backports en la serie estable (60 de 369 releases) | Los releases cuya versión mayor es menor que la más alta publicada hasta ese momento ya no cortan ventanas, en estables y en canary. Los commits de las ramas de mantenimiento quedan afuera de las ventanas de la línea principal. `--con-backports` vuelve al criterio anterior | `run_versiones.py` (`_armar_ventanas`) |
| 2 | Ventanas de menos de un día (88 de 369) | Un release publicado menos de `--min-dias` después del anterior (default: 1 día en estables, 0 en canary) no corta ventana: su lapso se suma a la anterior y queda anotado en `periodo.parametros.absorbidas`. Con los fixes 1 y 2, las ventanas estables de next.js pasan de 371 a 269, ninguna de menos de un día | `run_versiones.py` |
| 3 | Las métricas de foto se medían al principio de la ventana | El runner local mide CD, DLOC, README Completeness, LOC y ownership sobre la rama principal al **cierre** de la ventana (antes, en el tag del release, que para un backport es otra rama). La versión por API ya usaba la rama principal al cierre | `run_versiones_local.py` (`ref_al_cierre`) |
| 4 | El PCA excluía backports y las correlaciones no | Las dos usan `excluir_backports()` de `generar_correlaciones.py` al cargar los datos (con las ventanas nuevas no saca nada) | `analisis/generar_correlaciones.py`, `analisis/generar_pca.py` |
| — | Releases mal etiquetados como estables | `4.4.0-canary.1`, `4.4.0-canary.2`, `v12.2.3-canary.5` y `v15.0.0-rc.1` ya no cortan ventanas | `run_versiones.py` |
| — | Corridas en días distintos daban ventanas distintas | `--hasta AAAA-MM-DD`: fecha de corte de las ventanas, para que todas las integrantes obtengan exactamente las mismas | `run_versiones.py`, `run_versiones_local.py` |

### B. Métricas constantes o sin datos

| # | Problema | Qué cambió | Archivos |
|---|---|---|---|
| 5 | NOB guardaba las branches de hoy (2.706) en todas las ventanas | Branches del repositorio principal (no de forks) con un PR abierto al cierre de cada ventana, sin PR de bots. Las branches de hoy quedan en `value_extra` | `42/nob.py` |
| 6 | Wiki Presence tomaba el estado de hoy | Usa el historial del repositorio de la wiki (`{repo}.wiki`). **next.js sí tuvo wiki**: 167 commits entre octubre de 2016 y enero de 2020, hoy deshabilitada. Vale 1 entre el primer y el último commit de la wiki y 0 fuera de ese lapso | `16/wiki_presence.py` |
| 7 | Schedule Compliance usaba el estado de hoy y no miraba la fecha límite | Para cada milestone con fecha límite: parte de sus issues cerrada antes de esa fecha. Se asigna a la ventana donde cae la fecha límite; None si no hay milestones con fecha límite | `23/schedule_compliance.py` |

### C. Métricas de foto del código

| # | Problema | Qué cambió | Archivos |
|---|---|---|---|
| 8 | Las métricas de foto miden el estado acumulado | Dos métricas nuevas de flujo, en el runner local: `dloc_flujo` (líneas de documentación agregadas o eliminadas en la ventana) y `commits_doc` (proporción de commits que tocan documentación), en total y por persona, sin bots | `run_versiones_local.py` |
| 9 | DLOC no contaba `.mdx` y contaba archivos que no son documentación | Cuenta `.md`, `.mdx`, `.txt` y `.rst`, y excluye `examples/`, tests, fixtures, snapshots, dependencias, código compilado y archivos de licencia | `16/dloc.py` (`es_documentacion`) |
| 10 | CD dominada por código de terceros compilado | Excluye `compiled/`, `vendor/`, `node_modules/`, `dist/`, `build/`, código generado y archivos minificados. En la prueba, CD queda en 0,052–0,057 en 2023–24, sin el salto de 0,117 a 0,037 | `16/cd.py` (`es_codigo_propio`) |
| 11 | README Completeness promediaba todos los README del árbol | Solo el README de la raíz. En next.js es un enlace simbólico a `packages/next/README.md`, y ahora se sigue el enlace (sin eso daba 0). Da 0,86 y llega a 1,0 en la v15 | `16/readme_completeness.py`, `run_versiones_local.py` |

### D. Valores 0 en lugar de nulo

| # | Problema | Qué cambió | Archivos |
|---|---|---|---|
| 12 | MTTR y ANMCC devolvían 0 sin datos | Devuelven None (no observable). También CD y README Completeness cuando no hay archivos | `10/mttr.py`, `10/anmcc.py`, `16/cd.py`, `16/readme_completeness.py` |
| 13 | DIS valía 0 en el 80 % de las ventanas por `--solo-etiquetas` | Devuelve None en los dos modos. Hay que volver a correrla **sin** `--solo-etiquetas` | `16/doc_issue_survival.py` |
| 14 | ANMCC: ceros por commit, merges y `--max-commits` | Descarta los commits de merge y los que no informan archivos; `fetch()` acepta `max_commits` | `10/anmcc.py` |

### E. Bots

| # | Problema | Qué cambió | Archivos |
|---|---|---|---|
| 15 | El filtro de bots no usaba `bots_clasificados.csv` | `es_bot()` también lee `bots_clasificados.csv` (tipo `bot`, `agente_ia` o `desconocido`) | `base_metric.py` |
| 16 | Ninguna métrica filtraba bots a nivel producto | Filtran a nivel producto: ANMCC (commits de bots), NCI y MTTR (cierres de bots y cierres sin actor), Jarczyk y Process Performance (issues de bots afuera; las que cerró un bot cuentan como no resueltas), DIS (cierres de bots), NOI y `noi_28`, CFDR y NUB (issues abiertas por bots), NOB (PR de bots), y las métricas de foto por persona (archivos cuyo último autor es un bot). Se guardan también las versiones originales: `nci_con_bots` y `mttr_con_bots` | `10/`, `35/nci.py`, `40/`, `43/`, `16/doc_issue_survival.py`, `27/cfdr.py`, `39/nub.py`, `42/nob.py`, `run_versiones_local.py` |
| 17 | NCI de Proceso no filtraba bots | `nci_process` (40) y `nci_resolution_time` (43) reexportan la misma clase de `35/nci.py`, así que quedan corregidas con el 16 | `35/nci.py` |

Las métricas de issues (MTTR, NCI, NOI, Process Performance, Jarczyk y DIS) ahora comparten una sola descarga
(`issues_comun.py`) con autor, quién cerró, etiquetas y tipo de issue. Si se corren juntas en la misma
invocación, la descarga se hace una sola vez.

### F. Issues, cierres y etiquetas

| # | Problema | Qué cambió | Archivos |
|---|---|---|---|
| 18 | MTTR por persona dependía de quién cierra | Por persona no cuenta los autocierres (quien cerró es quien abrió). Métrica nueva `mttr_bugs`: solo issues clasificadas como bug | `10/mttr.py` |
| 19 | MTTR era solo un promedio | Métrica nueva `mttr_p50`: mediana de las issues | `10/mttr.py` |
| 20 | SC usaba el estado de hoy | Pide `closedAt` y `mergedAt`: un issue o PR cuenta como cerrado o mergeado solo si pasó antes del cierre de la ventana. Afecta a `sc` y `sc_disc` | `20/dc.py` |
| 21 | NUB y DIS buscaban etiquetas por subcadena | Comparación exacta (ignorando prefijos como `type:` o `kind:`), con `issues_comun.normalizar_etiqueta` | `39/nub.py`, `16/doc_issue_survival.py` |
| 22 | Rol del autor en NUB (authorAssociation) | **Queda a verificar** si es el rol al abrir la issue o el actual (no se pudo probar porque el token de GitHub del `.env` está vencido). Lo que sí se corrigió: CFDR ya no usa el top 10 de hoy, sino el top 10 de contribuidores hasta el cierre de cada ventana | `27/cfdr.py`, comentario en `39/nub.py` |

### G. Definiciones

| # | Problema | Qué cambió | Archivos |
|---|---|---|---|
| 23 | REXP mide actividad, no experiencia, y tenía la familia equivocada | Pasa a la familia `intensidad` en el diccionario, y la clase documenta qué mide | `analisis/generar_diccionario.py`, `15/rexp.py` |

### Otros cambios

- `export_persona.py` y `analisis/generar_diccionario.py` leen las credenciales de las variables `POSTGRES_*` (antes estaban fijas), así se pueden apuntar a la base nueva. También se corrigió el `IndexError` de la validación V4 de `export_persona.py`.
- El diccionario agrega las métricas nuevas (`dloc_flujo`, `commits_doc`, `mttr_p50`, `mttr_bugs`, `mttr_con_bots`, `nci_con_bots`) y ahora incluye `wp` y `nob_42`, que dejaron de ser constantes.

## Cómo correr todo sobre la base nueva

Requisitos: la base original levantada (`tg_metricas_db`) y un `GITHUB_TOKEN` válido en el `.env`. Hasta
el runner local lo necesita, porque le pide a GitHub la lista de releases para armar las ventanas.

**1. Crear la base nueva** (una vez por máquina): copia de `resultados_metricas` sin los resultados de
next.js en las series de releases.

```bash
python3 db/base_fixes.py crear
```

**2. Acordar una fecha de corte común** y usarla en todas las corridas (ej. `--hasta 2026-10-01`), para que
las ventanas sean idénticas en todas las máquinas.

**3. Etapa 1: métricas del clon local** (no gastan cuota de la API, salvo la lista de releases):

```bash
POSTGRES_DB=resultados_metricas_fixes python3 run_versiones_local.py --repo vercel/next.js --hasta 2026-10-01
POSTGRES_DB=resultados_metricas_fixes python3 run_versiones_local.py --repo vercel/next.js --hasta 2026-10-01 --con-canary
```

Cubre `dloc`, `cd`, `rc`, `loc_notion`, `cdiv`, `fexp`, `le`, `rexp`, `anmcc`, `dloc_flujo`, `commits_doc` y
`developer_ownership_notion`.

**4. Etapa 2: métricas por API**, para repartir entre integrantes. Cada grupo se corre en una sola invocación
para reutilizar la descarga, en estables y después con `--con-canary`:

| Grupo | Métricas |
|---|---|
| Issues | `mttr,mttr_p50,mttr_bugs,mttr_con_bots,nci,nci_con_bots,nci_process,nci_resolution_time,noi,process_performance,jarczyk_success_rate,dis` |
| Bugs | `cfdr,nub` |
| Contribuciones y PR | `sc,sc_disc,nob_42` |
| Comentarios y revisión | `nc,disc_centrality,exprev,rexprev` |
| Resto | `wp,schedule_compliance,ss,dev_exp,noi_28` |

```bash
POSTGRES_DB=resultados_metricas_fixes python3 run_versiones.py mttr,mttr_p50,nci --repo vercel/next.js --hasta 2026-10-01
```

DIS va **sin** `--solo-etiquetas`.

**5. Juntar los resultados.** Cada una exporta sus métricas y las demás las importan:

```bash
python3 db/base_fixes.py exportar --metricas mttr,mttr_p50,nci --salida db/fixes_ine.csv.gz
python3 db/base_fixes.py importar db/fixes_luz.csv.gz
```

**6. Análisis** sobre la base nueva:

```bash
POSTGRES_DB=resultados_metricas_fixes python3 export_persona.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_diccionario.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_correlaciones.py
python3 analisis/generar_pca.py Producto
```

Antes de correr el análisis sobre la base nueva, guardar una copia de `analisis/salidas/pares_correlacion.csv`
y de `analisis/salidas/pca/`, para comparar los resultados originales con los corregidos.

## Pendiente

- Verificar `authorAssociation` en NUB (punto 22) con un token válido.
- Las métricas nuevas no tienen versión por persona agregada en `persona_agregado_estable_canary.csv`:
  `export_persona.py` exporta solo las métricas que ya conocía.

## Analizar sobre la base corregida y comparar con el análisis original

La base corregida completa (las tres etapas ya integradas) se comparte como seed
(`fixes_seed.sql.gz`, por Drive: no entra en git). Para cargarla:

```bash
docker exec tg_metricas_db dropdb -U metricas --if-exists resultados_metricas_fixes
docker exec tg_metricas_db createdb -U metricas resultados_metricas_fixes
gunzip -c fixes_seed.sql.gz | docker exec -i tg_metricas_db psql -q -U metricas -d resultados_metricas_fixes
```

Antes de regenerar nada, guardar los resultados originales (los scripts escriben siempre en los mismos
archivos, lean de la base que lean):

```bash
mkdir -p analisis/salidas_originales
cp -rp analisis/salidas/* persona_agregado_estable_canary.csv metricas_persona.csv analisis/salidas_originales/
```

Después, sobre la base corregida:

```bash
POSTGRES_DB=resultados_metricas_fixes python3 export_persona.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_diccionario.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_correlaciones.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_pca.py Persona
python3 analisis/comparar_resultados.py Persona-Persona
```

`comparar_resultados.py` compara `analisis/salidas_originales/` con `analisis/salidas/` para un cruce:
cantidad de pares por categoría, relaciones robustas que se mantienen, se pierden o aparecen, los pares
cuya ρ corregida más cambió, y si los componentes del PCA de la dimensión siguen siendo los mismos
(congruencia de Tucker sobre las variables comunes). Lo guarda en `analisis/salidas/comparacion_<cruce>.md`.

Ajustes del análisis en esta branch:

- Las variantes de una misma métrica (`mttr_p50`, `mttr_bugs`, `mttr_con_bots`, `nci_con_bots`) son
  pares de control en las correlaciones y no entran al PCA (con `--con-variantes` se incluyen).
- El PCA saca las variables constantes en los releases que usa (por ejemplo, Wiki Presence vale 0 en
  todas las ventanas desde 2020).
