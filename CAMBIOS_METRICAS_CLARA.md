# Cambios a las clases de métricas — Clara (partición por VOLUMEN)

**Rama:** `feat/particion-volumen` · **Base:** `main`
**Último commit común con main:** `c4a4963 metricas faltantes`
**Fecha del análisis:** 2026-08-31

Documento generado para comparar lado a lado con los de mis compañeras. Toda
afirmación abajo sale de `git diff main -- <archivo>`. Cuando algo no lo puedo
confirmar desde el código o el historial git, lo digo explícitamente.

**No confirmable desde el código:** las ramas de mis compañeras. Solo tengo
`feat/particion-volumen` (la mía) y `main` en local. Toda referencia a lo que
"hicieron ellas" es hipótesis para el merge, no observación.

---

## Parte 1 — Inventario de mis cambios

### 1.1 Archivos que existían en `main` y modifiqué

| Archivo | Qué cambió (comportamiento) | Por qué / bug que resolvía |
|---|---|---|
| `base_metric.py` | (a) `_rest` y `_graphql` ahora lanzan `RuntimeError` en vez de `sys.exit(1)`. (b) Al importar el módulo se instala `requests_cache` (SQLite en `gh_cache.sqlite`, TTL 7 días, aplica a GET y POST — o sea también al GraphQL). (c) Ambos métodos reintentan hasta 3 veces esperando al `X-RateLimit-Reset` (o `Retry-After`) cuando la respuesta es 403/429 con texto `"rate limit"`. | (a) `SystemExit` no es subclase de `Exception` → el `try/except Exception` del runner no lo agarra y muere todo el batch por un 502 aislado. (b) El batch corre cada endpoint 20-45 veces desde métricas distintas; sin cache eran horas de red repetida. (c) Un PAT de GitHub tiene 5000 req/h; una corrida completa se los come y el runner abandonaba métricas por 3 fallos seguidos aunque fuera transitorio. |
| `20/dc.py` (SocialContribution) | Query GraphQL de `issues` y `pullRequests` ahora `orderBy: {field: CREATED_AT, direction: ASC}`. En `_paginate` se cortan las páginas cuando `created > fecha_fin`. Antes no había `orderBy` (default DESC) y se paginaba TODO el historial filtrando en Python. | Sin filtro se bajaban ~43.600 PRs de tldr por período — corridas eternas y timeouts. |
| `18/nc.py` (NumberOfComments) | `_fetch_paginated` pasa `sort=created&direction=asc` a los 3 endpoints REST (`/issues/comments`, `/comments`, `/pulls/comments`) y hace `break` cuando `created > fecha_fin` (antes era `continue`). | Sin `sort` los endpoints ordenan por `updated`, no se puede cortar; al pasar de ~1000 páginas GitHub devuelve **HTTP 422 "pagination is limited"**. |
| `18/disc_centrality.py` (DiscussionCentrality) | Mismo patrón que `nc.py` en `_fetch_issue_comments` y `_fetch_pr_review_comments`. **`_fetch_commit_comments` sin tocar** — el endpoint `/repos/.../comments` no acepta `sort`, y en tldr los commit comments son pocos (no dispara el 422). | Mismo 422 que `nc`, misma solución. |
| `15/exprev.py` (ReviewExperience) | (a) Query GraphQL cambió `UPDATED_AT DESC` → `CREATED_AT ASC` y **quitó el campo `updatedAt`** de los nodos. (b) En `_paginate_issues`/`_paginate_prs` el criterio de early-stop pasó de `updated < fecha_inicio` a `created > fecha_fin`. (c) `_fetch_comments` (REST) recibió el mismo tratamiento que `nc.py`: `sort=created&direction=asc` + early-stop. | (a) `UPDATED_AT DESC` obligaba a recorrer todo el historial antes de cortar. **Además** el código leía `node["updatedAt"]` en cada iteración → `KeyError` cuando el field faltaba/se removía. (c) Mismo 422 de `/issues/comments` que en `nc`. |
| `15/rexprev.py` (RecentReviewExperience) | Idéntico patrón que `exprev.py`. | Misma clase con ponderación por antigüedad; mismos bugs. |
| `16/doc_issue_survival.py` (DocIssueSurvival) | Se agregó `closed` al dict guardado en `self.issues`. Se agregó helper `_en_ventana(fecha_inicio, fecha_fin)`. `por_producto` y `por_persona` filtran por `_en_ventana` antes de promediar. **Firma de `fetch()` NO cambió** — sigue siendo `fetch(self, con_actor=False, **kwargs)` sin fechas. | Antes `por_producto` promediaba TODOS los doc-issues del repo → devolvía el mismo valor (305.16) en los 45 bloques. |
| `Notion/developer_ownership.py` (DeveloperOwnership) | Firma pasó de `fetch(self, fecha_fin, max_files, **kw)` a `fetch(self, fecha_inicio, fecha_fin, max_files, **kw)`. `fecha_inicio` se ignora dentro. `run()` actualizado para pasar las dos. El cálculo (git blame por archivo, agrega líneas por autor) **no cambió**. | El runner (`llamar_fetch`) inspecciona la firma con `inspect.signature` y solo pasa fechas si aparecen **las dos**. Con solo `fecha_fin`, llamaba `fetch()` sin argumentos → `TypeError`. |
| `23/schedule_compliance.py` (ScheduleCompliance) | **Solo comentario** (6 líneas antes de `_milestones_en_periodo`). **No cambia comportamiento.** | Documentar que la constante 0.0 en muchos bloques no es bug de ventana (el filtro ya está). tldr tiene ~3 milestones en todo el historial. Para que nadie lo "arregle" sin leer primero. |
| `.gitignore` | Se agregó `gh_cache.sqlite` y `gh_cache.sqlite3`. | El archivo de cache se regenera solo y pesa cientos de MB. |

### 1.2 Archivos NUEVOS (no existían en `main`)

| Archivo | Rol | Compartible? |
|---|---|---|
| `analisis_volumen/generar_periodos.py` (382 líneas) | Genera los bloques por volumen (N eventos: commits o issues cerradas). Análogo a lo que ustedes tendrán en `analisis_versionado/` o `analisis_adaptativo/`. | **No** — específico de mi criterio |
| `analisis_volumen/run_particionado.py` (446 líneas) | Runner batch. Para cada período de la tabla `periodo` corre las métricas del `REGISTRO` y guarda en `resultado`. Es resumible (salta lo que ya está). Tiene `--variante`, `--rehacer`, `--limite-periodos`, `--firmas`. | **Sí (con ajustes)** — la lógica no depende del criterio; solo `--tipo-analisis` default está en `"volumen"`. Podría ir a un `runners/` compartido. |
| `analisis_volumen/__init__.py` (0 líneas) | Marker de package. | No |
| `db/migration_002_variante.sql` (67 líneas) | Ver 1.3 abajo — cambio de esquema. | **Impacta a las tres.** |

### 1.3 Cambios no obvios / colaterales que fácil se me olvidan

- **Rate-limit retry en `base_metric`** (aparece junto con el `raise` y el
  cache, pero es un tercer cambio conceptualmente distinto). Puede bloquear
  hasta ~1h el proceso si el rate limit está agotado, y hace `time.sleep`.
  Si alguna de ustedes tiene un timeout externo (systemd, cronjob, wrapper),
  se puede pisar.
- **Cache `requests_cache` monkey-patchea `requests` global.** No es visible
  al leer los diffs de las métricas, pero cualquier otro módulo que importe
  `requests` (aunque no herede de `GitHubMetric`) va a estar cacheado también.
- **Comentario-que-solo-existe** en `23/schedule_compliance.py`. Si mergean
  sobre esta versión se pierde si no se rescata.
- **Comentario en `15/exprev.py` línea ~101 y su gemelo en `15/rexprev.py`**
  dice: *"Trade-off: issues creados antes de la ventana pero cerrados dentro
  no se capturan..."*. Revisando el código en frío, **eso es incorrecto**: el
  early-stop es solo `created > fecha_fin`; los issues con `created <
  fecha_inicio` sí se inspeccionan y el bloque separado de `if node.get("closedAt")`
  los captura. Es un comentario mal escrito, no un bug de código. Marcarlo
  para reescribir al mergear.
- **`db/migration_002_variante.sql`** hace `DROP CONSTRAINT IF EXISTS
  periodo_repo_id_tipo_analisis_periodo_num_key` y variantes: si ustedes
  crearon nombres de constraint distintos, el DROP no los encuentra y quedan
  ambos coexistiendo (uno con `variante`, otro sin) — posible pisada al
  INSERT si su `variante = ''`. Verificar con `\d periodo` post-migración.
- **`analisis_volumen/generar_periodos.py`** usa `FECHA_CORTE =
  datetime(2026, 8, 31, tzinfo=timezone.utc)` como corte FIJO para que la
  partición sea reproducible entre corridas. Si ustedes usan `datetime.now()`
  para su corte, cada corrida les genera bloques distintos — cuidado. No es
  un cambio a clases pero es una convención que conviene alinear.

---

## Parte 2 — Clasificación de cada cambio: API vs FÓRMULA

**Definiciones que uso:**

- **API/infra:** cómo bajo o filtro los datos desde GitHub (paginación,
  orderBy, sort, early-stop, retry, cache, firma de `fetch`, `raise` vs
  `sys.exit`). El resultado numérico de la métrica es el mismo con la versión
  vieja o la nueva, solo cambia el costo o la fiabilidad.
- **FÓRMULA/semántica:** *qué* calcula la métrica. Si cambio esto, dos
  personas pueden estar guardando números distintos en `resultado.value` para
  el mismo `(repo, período, métrica)`. **No se resuelve con "tomamos la
  mejor" — hay que decidir cuál interpretación es la correcta para la tesis.**

### 2.1 Cambios puramente API

| Clase | Cambios API |
|---|---|
| `base_metric.py` | (a) `sys.exit` → `raise RuntimeError`. (b) Cache HTTP SQLite via `requests_cache.install_cache`. (c) Retry con espera al reset en 403/429 rate-limit. Ninguno cambia qué se calcula, solo cómo se transporta. |
| `20/dc.py` | Cambio de `orderBy` (no había) → `CREATED_AT ASC` + early-stop. La fórmula de SC (`sum(issues_opened + issues_opened_closed + prs_opened + prs_opened_closed + prs_opened_merged)`) **no cambió**; las categorías y sus condiciones son idénticas. |
| `18/nc.py` | Agregar `sort=created&direction=asc` + `continue` → `break`. La fórmula (`sum(1 for e in eventos if e["type"] in {IssueCommentEvent, CommitCommentEvent, PullRequestReviewCommentEvent})`) **no cambió**. Los tipos son los mismos. |
| `18/disc_centrality.py` | Igual que `nc.py` en dos de los tres endpoints. El algoritmo de centralidad (grafo de coautoría de comentarios, degree centrality) **no cambió**. |
| `15/exprev.py` | Cambio de `UPDATED_AT DESC` a `CREATED_AT ASC` en el query GraphQL; se quitó el campo `updatedAt`; early-stop se movió de `updated < fecha_inicio` a `created > fecha_fin`; `_fetch_comments` con `sort` + early-stop. La fórmula (`sum` de 6 categorías: issues_opened, issues_closed, prs_opened, prs_closed, issue_comments, pull_request_comments) **no cambió**. |
| `15/rexprev.py` | Idéntico patrón. Fórmula de ponderación temporal (`sum(1 / (dias_antiguedad + 1))`) **no cambió**. |
| `Notion/developer_ownership.py` | Solo cambio de firma de `fetch`. El algoritmo (git blame por archivo, `_BLAME_QUERY` GraphQL, agregación de líneas por autor) **no cambió**. |
| `23/schedule_compliance.py` | Solo comentario. Ni API ni fórmula. |
| `.gitignore` | Infraestructura del repo. |

### 2.2 Cambios de FÓRMULA/semántica

**Uno solo, y hay que hablarlo:**

**`16/doc_issue_survival.py`:**
- **Antes** (main): `por_producto` calculaba `sum(days) / len(days)` sobre
  **todos los doc-issues cerrados en la historia del repo**. Devolvía la
  misma media global (~305 días en tldr) para todos los bloques.
- **Ahora** (mi rama): `por_producto` calcula `sum(days) / len(days)` sobre
  **los doc-issues cuyo `closedAt` cae en `[fecha_inicio, fecha_fin]`**.
  Devuelve una media distinta por bloque.

Esto **es un cambio de qué calcula la métrica.** Los dos comportamientos son
matemáticamente distintos (el mío es "media móvil sobre la ventana", el otro
es "constante = media global"). El anterior era un bug obvio para métricas
de flujo, pero:

- Si alguna de ustedes también arregló este bug, probablemente lo hizo con
  criterio idéntico (filtrar por `closedAt` en la ventana), en cuyo caso los
  merges dan igual. Verificar leyendo `por_producto` de su versión.
- Si alguna filtró por `createdAt` en vez de `closedAt`, **los números
  divergen**: un issue creado en 2020 y cerrado en 2024 va a bloque distinto
  según el criterio. Hay que decidir cuál interpretación es la buena. Yo
  usé `closedAt` porque la métrica se llama "survival" y el evento medible
  es el cierre; el comentario en el código lo dice.

### 2.3 Casos borderline (¿API o fórmula?)

- **En `15/exprev.py` / `15/rexprev.py`** el chequeo cambió de
  `if fecha_inicio <= created <= fecha_fin:` a `if fecha_inicio <= created:`
  (el `<= fecha_fin` se quitó porque queda garantizado por el early-stop
  anterior en `if created > fecha_fin: break`). **Es matemáticamente equivalente**
  — no cambia qué se cuenta. Lo listo acá porque a primera vista parece que
  se aflojó el filtro, pero es solo una simplificación consistente. **API**.
- **En `18/nc.py`** el cambio de `continue` a `break` sí depende de que el
  orden sea ascendente por `created` (garantizado por `sort=created`). Si
  alguien quitase el `sort` pero dejase el `break`, se perderían comentarios.
  **API** (pero es un acoplamiento a documentar).

### 2.4 Resumen para el merge

| Tipo | Archivos | Cómo mergear |
|---|---|---|
| **API/infra** | `base_metric.py`, `15/exprev.py`, `15/rexprev.py`, `18/nc.py`, `18/disc_centrality.py`, `20/dc.py`, `Notion/developer_ownership.py`, `.gitignore` | Tomar la mejor versión (probablemente la mía; ver Parte 2.5). No cambia números guardados. |
| **FÓRMULA** | `16/doc_issue_survival.py` | Conversación explícita. Comparar qué campo filtran ellas (`createdAt` vs `closedAt`) y decidir. |
| **Documentación** | `23/schedule_compliance.py` | Rescatar el comentario. |

### 2.5 "La mejor versión" para los cambios API

Aunque los cambios API sean intercambiables, algunos son **necesariamente**
correctos y otros son "una entre varias":

- **Obligatoriamente correctos** (si su versión no los tiene, la nuestra pierde
  contra la de ustedes):
  - `sys.exit → raise` en `base_metric` (regla dura).
  - Quitar `node["updatedAt"]` en `exprev`/`rexprev` (fixea `KeyError`).
  - Agregar `sort=created&direction=asc` en `/issues/comments` y
    `/pulls/comments` (fixea `422`).
  - Firma `fetch(fecha_inicio, fecha_fin, ...)` en `developer_ownership`
    (fixea `TypeError`).
- **Preferencia debatible:**
  - `CREATED_AT ASC` vs `UPDATED_AT DESC` en `exprev`/`rexprev`/`dc`. Ver
    Parte 3.2 — para ustedes puede ser mejor DESC.
  - `requests_cache` + retry rate-limit: solo aportan a corridas largas. Si
    ustedes corren de a poco, no molestan pero tampoco urgen.

---

## Parte 3 — Supuestos sobre el runner y riesgo de divergencia

### 3.1 Supuestos que hace mi versión sobre el runner

Todos los supuestos que sigue son **los que hace mi runner
`analisis_volumen/run_particionado.py`**. Si su runner es distinto en algo
de esto, alguna clase puede caer.

| Clase | Supuesto |
|---|---|
| `dc`, `nc`, `disc_centrality`, `exprev`, `rexprev` | El runner llama `fetch(fecha_inicio, fecha_fin)` con las dos fechas posicionalmente (o keyword, da lo mismo en Python). |
| `doc_issue_survival` | El runner llama `fetch()` sin fechas y después `por_producto(fecha_inicio, fecha_fin)` (o `por_persona`). El filtro por ventana está en `por_*`. |
| `developer_ownership` | El runner llama `fetch(fecha_inicio, fecha_fin, max_files)`. Si su runner solo pasa `fecha_fin`, hoy da `TypeError` (con la firma vieja daba `TypeError` desde el otro lado). |
| `schedule_compliance` | `fetch()` sin fechas; `por_producto(fi, ff)` filtra internamente. |
| `dc` (persona) | `por_persona` devuelve `{login: {..., "sc": N}}`. El runner necesita `clave_valor="sc"` para extraer el número. |
| `exprev`, `rexprev` | `por_persona` devuelve `{login: número_plano}`. Runner con `clave_valor=None`. |
| `developer_ownership` | `por_persona` devuelve `{login: {"lineas": N, "porcentaje": X}}`. Runner con `clave_valor="porcentaje"` (esto lo cambié en mi `REGISTRO`; si el de ustedes tiene `None`, van a ver `[!] N/N sin value`). |

### 3.2 Cambios míos que podrían dar mal en otro criterio de partición — PELIGROSOS

**El técnico principal es el orden de paginación:**

- Elegí `CREATED_AT ASC` en `exprev`/`rexprev`/`dc` porque en volumen los
  bloques son cortos y mayoritariamente pasados. Con ASC, cortar en
  `created > fecha_fin` termina en 1-15 páginas para bloques del pasado.
- Contra: en el **último bloque** (fecha_fin ≈ hoy) hay que iterar TODAS las
  páginas hasta el final. En volumen es 1 de 45 bloques, penalización
  aceptable.
- **PELIGRO para versionado**: si sus bloques son ~7 (uno por release) y el
  último cubre "desde el último release hasta hoy" que puede ser 6 meses o
  años, ese bloque final le pega el peor caso. El costo es cargar TODOS los
  issues/PRs del repo entero en RAM para ese bloque (~44k PRs en tldr).
- **PELIGRO para adaptativo**: similar si los bloques son anchos. En
  particular si el último bloque adaptativo se estira hasta hoy, mismo caso.
- Mitigación: para el último bloque específicamente, `UPDATED_AT DESC` con
  corte en `updated < fecha_inicio` puede ser más eficiente. **No hice esta
  optimización.** Ustedes pueden decidir agregarla, pero requiere que las
  dos técnicas convivan (o que se elija una según el "tamaño esperado" del
  bloque, lo cual es feo).

**Otros cambios que dependen del tamaño de la ventana:**

- **`doc_issue_survival`** filtra por `closedAt` dentro de la ventana. Si
  ustedes tienen bloques definidos por "fechas de commit del release" (sin
  necesariamente incluir las fechas de cierre de issues), issues cerrados
  entre releases pueden caer en "tierra de nadie" según cómo definan los
  bordes. No es un problema del código de la clase, sino de cómo genera los
  bloques su `generar_periodos_*.py`.
- **`exprev`/`rexprev`** paginan hasta cortar. Si sus bloques son *grandes*
  y las llamadas API paginadas se pisan con el rate limit, el retry que
  agregué en `base_metric` puede tirar la corrida a horas. Es lo correcto
  (esperar y seguir), pero avisen si el batch de una corre en 15 min y de
  golpe pasa a 2h.

### 3.3 Cambios que son SEGUROS para cualquier criterio

- `sys.exit → raise` en `base_metric`: nunca puede empeorar nada.
- Cache `requests_cache`: cachea por URL+params, no depende del criterio. En
  el peor caso (query no repetida) es lo mismo que no tenerlo.
- Retry por rate-limit: nunca puede empeorar. Peor caso: espera hasta 1h y
  sigue.
- Sacar el uso de `node["updatedAt"]` en `exprev`/`rexprev` (bugfix duro,
  seguro en cualquier lado).
- Firma `fetch(fecha_inicio, fecha_fin, ...)` en `developer_ownership`
  (compatible con cualquier runner que inspeccione firma para pasar fechas).
- Filtro por ventana en `doc_issue_survival` — SIEMPRE es lo correcto para
  una métrica de flujo, aunque su definición del corte del bloque cambie
  qué issues caen dentro.

### 3.4 Inconsistencias detectadas entre comentario y código

- **`15/exprev.py` (~línea 101) y `15/rexprev.py` (~línea 100)**: el
  comentario dice *"Trade-off: issues creados antes de la ventana pero
  cerrados dentro no se capturan"*. **El código sí los captura** — el
  early-stop es solo `created > fecha_fin`; los nodos con `created <
  fecha_inicio` sí se iteran y el bloque separado `if node.get("closedAt"):`
  los añade a `issues_closed`. Es un comentario mal escrito, no un bug de
  código. **Al mergear, reescribir o borrar el comentario.**

---

## Parte 4 — Estado para converger

### 4.1 Archivos de código COMPARTIDO que toqué (van a conflictuar)

Ordenados por probabilidad de que la otra persona también los haya tocado:

- **`base_metric.py`** — casi seguro conflicto. Este es la base de todo.
- **`15/exprev.py`**, **`15/rexprev.py`**, **`18/nc.py`**,
  **`18/disc_centrality.py`**, **`20/dc.py`** — muy probable. Son las clases
  que tenían el bug de `422` / `KeyError`, así que si les corrió el pipeline,
  las tuvieron que tocar también.
- **`16/doc_issue_survival.py`** — probable. Si vieron el valor constante,
  lo habrán arreglado.
- **`Notion/developer_ownership.py`** — probable. `TypeError` es duro de
  ignorar.
- **`23/schedule_compliance.py`** — improbable (solo comentario). Bajo
  riesgo de conflicto real.
- **`.gitignore`** — casi seguro conflicto de merge trivial; se resuelve
  concatenando ambas versiones.
- **`db/migration_002_variante.sql`** — es un archivo nuevo, no debería
  conflictuar por diff, pero sí por semántica (ver 4.3).

### 4.2 Archivos ESPECÍFICOS de mi criterio (solo míos, no compartir)

- `analisis_volumen/` (`generar_periodos.py`, `run_particionado.py`,
  `__init__.py`, `__pycache__/`).
- `data/` (untracked): cache local de commits/issues bajados por
  `generar_periodos.py` para su modo `--diagnostico`.
- `panel_n500_desde2016.csv` (untracked): export de la vista `panel`.
- `gh_cache.sqlite` (ignorado): cache HTTP. Si van a compartir la cache
  entre las tres, vale la pena discutirlo.

### 4.3 IMPACTO EN LA DB — `db/migration_002_variante.sql` ⚠️

**Este cambio SÍ impacta a las tres.** Lo destaco porque es lo más fácil
de pasar por alto.

- Agrega `periodo.variante TEXT NOT NULL DEFAULT ''`.
- **Reemplaza los UNIQUE** viejos `(repo_id, tipo_analisis, periodo_num)` y
  `(repo_id, tipo_analisis, fecha_inicio, fecha_fin)` por las versiones que
  incluyen `variante`.
- Agrega columna generada `duracion_dias`.
- Recrea la vista `panel` para incluir `variante`, `duracion_dias`,
  `parametros`.

**Implicaciones para ustedes:**

- Si su `generar_periodos_*.py` inserta en `periodo` sin especificar
  `variante`, va a caer el default `''`. Bien, funciona, pero pierden la
  capacidad de tener varias particiones del mismo `tipo_analisis`
  conviviendo. Recomiendo alinear naming: yo usé `"n500_desde2016"` para
  volumen; ustedes podrían usar `"por_release"` o `"piso15x3_mensual"`.
- Si su `run_particionado.py` filtra `WHERE variante = %s`, va a andar. Si
  no lo hace, va a leer TODOS los períodos y correr todo dos veces.
- La vista `panel` recreada trae 3 columnas nuevas. Si sus queries hacen
  `SELECT *` desde `panel`, cambia el orden de columnas — un downstream con
  posicionales se rompe (con nombres, no).

**Cómo aplicarla en su DB (idempotente, la puede correr cualquiera):**

```bash
docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas \
  < db/migration_002_variante.sql
```

**Verificar post-aplicación:**

```bash
docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas -c "\d periodo"
```

Debe aparecer:
- `variante | text | not null | default ''`
- `duracion_dias | double precision | | | generated always as (...) stored`
- constraints `periodo_uniq_num` y `periodo_uniq_fechas` con `variante` incluida.

### 4.4 Checklist de convergencia para las tres

Una vez que decidan cómo mergear (ver el doc anterior "Parte 4" para un
flujo git detallado), este es el checklist mínimo:

1. `git diff main -- <cada_archivo_de_1.1>` en las tres ramas y comparar.
2. Para cada archivo, decidir: (a) todos coinciden → merge trivial;
   (b) todas atacaron el mismo bug con criterios distintos pero equivalentes
   → tomar el más limpio; (c) atacamos bugs distintos → mergear ambos fixes;
   (d) chocan las fórmulas (caso `doc_issue_survival`) → **decidir a mano**.
3. Aplicar la migración de DB en las 3 instancias locales.
4. Cada una re-corre `--firmas` y luego `--limite-periodos 2 --rehacer` en
   su variante, para verificar que las clases mergeadas siguen funcionando.
5. Query de sanity:
   ```sql
   SELECT metrica_id, COUNT(DISTINCT value) distintos,
          COUNT(*) filas, COUNT(value) con_valor
   FROM panel WHERE variante='<la_de_uds>'
   GROUP BY 1 ORDER BY 1;
   ```
   Todas las de flujo con `distintos > 1` y `con_valor ≈ filas`.
