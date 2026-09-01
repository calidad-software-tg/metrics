# CAMBIOS_METRICAS_INE.md

**Autora:** Inés (`inesgassiebayle`) — criterio de partición: **VERSIONADO** (un bloque entre cada
tag/release consecutivo del repo).

## Base de comparación (git)

- `git rev-parse HEAD` == `git rev-parse main` == `git merge-base HEAD main` == **`c4a4963`**.
- **No hay rama propia.** Todo mi trabajo está en el *working tree* sin commitear. La comparación
  es `git diff main` (working tree) + 2 archivos *untracked*.
- Commits recientes en `main` que **no son míos de esta ronda** (contexto, ya mergeado):
  - `c4a4963` "metricas faltantes" — ClaraLopez1: agrega `38/dev_experience.py`, `39/nub.py`,
    `42/nob.py`; arregla imports en `run.py`.
  - `569b280` "Agrega filtrado por fecha…" — luzlaura: agrega `_resolve_ref()` a `base_metric.py`
    y filtrado por fecha en `cd/dloc/readme_completeness/loc/developer_ownership/ci_presence/
    issues_total/pull_requests_summary/collaborators`.
  - `093ed0f` "base de datos para particiones" — Inés: esquema `repos/metrica/periodo/resultado` +
    vista `panel` (`db/schema.sql`). **Ya está en main; mis cambios de esta ronda NO tocan
    `schema.sql`.**

`git diff main --stat` (working tree):

```
 .gitignore            |   4 +-
 15/exprev.py          |  25 ++-----
 15/rexprev.py         |  25 ++-----
 18/disc_centrality.py |  88 +++++++---------------
 18/nc.py              |  25 ++-----
 20/dc.py              |   2 +-
 base_metric.py        | 197 ++++++++++++++++++++++++++++++++++++++++++++++++--
 db/README.md          |  37 ++++++++--
 db/docker-compose.yml |   4 +-
```
+ untracked: `run_versiones.py`, `run_versiones_local.py`.

---

## Parte 1 — Inventario de mis cambios

### 1.1 Archivos que ya existían en `main` y modifiqué

| archivo | qué cambió (comportamiento) | por qué / bug |
|---|---|---|
| `base_metric.py` | **(a)** Nuevo `_get(url, params)`: todo GET pasa por acá — `timeout=(10,60)`, hasta 5 reintentos ante error de red / `ChunkedEncodingError` / HTTP 5xx (500,502,503,504,520,522) con backoff exponencial, y **espera hasta el reset de cuota** ante 403/429 con `x-ratelimit-remaining==0` o header `retry-after`. **(b)** `_rest()` ahora delega en `_get()` (mismo valor de retorno). **(c)** `_graphql()` reescrito con la misma lógica de reintentos/rate-limit sobre el POST. **(d)** Nuevo método `_rest_list_since(path, fecha_inicio, fecha_fin, *, date_key, id_key, label)`: paginación "since-walk" para los endpoints de comentarios en lista. **(e)** `_headers()` extraído. **(f)** Cache de proceso `_LIST_SINCE_CACHE` + slim de items (`_slim_comentario`, `_CAMPOS_SLIM`). | Corridas largas sobre `tldr` (bloques VERSIONADO grandes) morían por: (1) `requests.get` sin timeout → socket colgado bloqueaba el proceso para siempre; (2) HTTP 403 "API rate limit exceeded" mataba el batch con `sys.exit(1)` en la primera request pasada; (3) los endpoints `/issues/comments`, `/pulls/comments`, `/repos/.../comments` cortan la paginación con **HTTP 422** alrededor de la página ~150, así que en repos con muchos comentarios nunca se bajaba el histórico completo. |
| `18/disc_centrality.py` | `_fetch_issue_comments`, `_fetch_pr_review_comments`, `_fetch_commit_comments`: los 3 loops manuales `while page: self._rest(..., {since, page, per_page})` + filtro en memoria `if created > fecha_fin: continue` fueron reemplazados por **una** llamada a `self._rest_list_since(<endpoint>, fecha_inicio, fecha_fin, label=...)`. La construcción de cada registro (`item_id`, `user_login`, `fecha`) es **idéntica**. | Sin el since-walk, la 1ª ventana VERSIONADO (`since=2019…`) tiraba 422 antes de terminar → 0 datos. Ver 1.1(d). **Efecto colateral semántico documentado en Parte 2.** |
| `18/nc.py` | `_fetch_paginated(path, tipo, fi, ff)` (usado para `/issues/comments`, `/comments`, `/pulls/comments`): mismo reemplazo que arriba — loop manual → `self._rest_list_since(...)`. Construcción del evento (`type`, `login`, `fecha`) idéntica. | Igual que `disc_centrality`. |
| `15/exprev.py` | Solo el helper `_fetch_comments(path, tipo, fi, ff)` (parte de `fetch`, para `/issues/comments` y `/pulls/comments`): loop manual → `self._rest_list_since(...)`. **`_paginate_issues` / `_paginate_prs` (GraphQL) NO los toqué.** Construcción del evento idéntica. | Igual. |
| `15/rexprev.py` | Idéntico a `exprev`: solo `_fetch_comments`. `_paginate_issues`/`_paginate_prs` sin tocar. | Igual. |
| `20/dc.py` | En `_paginate()` (fetch de issues y de PRs vía GraphQL), cada registro pasa de `{"author", "state"}` a `{"author", "state", "created"}` (se agrega el `datetime` de `createdAt` ya calculado). **`por_producto` / `por_persona` sin cambios.** | El campo `created` lo consume `run_versiones_local.py` para recortar `sc`/`sc_disc` por ventana desde un clon local sin re-bajar todo. **Dentro de `dc.py` el campo no se usa** (ver Parte 2 y "inconsistencias"). |
| `db/docker-compose.yml` | **(a)** `ports: "5432:5432"` → `"${POSTGRES_PORT:-5432}:5432"`. **(b)** healthcheck `pg_isready -U $USER` → `pg_isready -U $USER -d ${POSTGRES_DB:-resultados_metricas}`. **Sin cambios a volúmenes, imagen ni `schema.sql` montado.** | En mi máquina el 5432 ya estaba ocupado por otro Postgres → necesitaba publicar en 5433 sin hardcodear. El healthcheck sin `-d` se conectaba a una base `metricas` inexistente y llenaba el log con `FATAL: database "metricas" does not exist` cada 5 s (el healthcheck igual pasaba). |
| `db/README.md` | Solo documentación: renumeré secciones (3→"cargar catálogo", agregué "4. Correr métricas"), nota sobre `POSTGRES_PORT`, nota sobre re-aplicar `schema.sql` a mano si el volumen ya existía, y ejemplos de `run_versiones.py`. | Onboarding del equipo. Sin impacto en código. |
| `.gitignore` | `.env` → `.env` + `.clones/` + `__pycache__/` (y se normalizó el salto de línea final). | `.clones/` es el clon local que usa `run_versiones_local.py` (~71 MB); `__pycache__/` aparecía como untracked en todo el repo. |

### 1.2 Archivos nuevos que agregué

> No hay carpeta `analisis_versionado/`. Mis dos runners viven en la raíz del repo.

| archivo | qué es | notas |
|---|---|---|
| `run_versiones.py` | **Mi runner + mi generador de bloques.** `ventanas_por_version(token, org, repo)` baja los tags vía REST, resuelve la fecha de commit de cada tag, ordena por fecha y arma N ventanas `[fecha_tag_i, fecha_tag_{i+1})`; la última va hasta `now`. Clase `Base` (capa Postgres). Dict `metricas` (mismo catálogo de ~40 claves que `run.py`). `_fetch()` adapta la llamada a la firma de cada `fetch`. `correr_metrica` / `_correr_sliceable`. CLI `--por auto|producto|persona`, `--repo`, `--excepto`, `--json`, `--no-guardar`, `--max-files/--max-commits/--max-contributors`. | Escribe en `repos`, `metrica`, `periodo`, `resultado`. **No hace DDL.** `tipo_analisis` fijo en `"versiones"`. |
| `run_versiones_local.py` | **Variante local, sin cap.** Para métricas de archivos/commits/blame (`loc_notion`, `dloc`, `cd`, `cdiv`, `fexp`, `le`, `rexp`, `developer_ownership_notion`) lee un clon local (`.clones/<repo>`) con `git ls-tree` + `git cat-file --batch` / `git log --numstat` / `git blame --line-porcelain`, **instancia la clase original y le carga el estado** (`m.commits`, `m.registros`, `m.propiedad`) y llama a su `por_producto`/`por_persona`. Ventanas vienen de `ventanas_por_version` (API, iguales a `run_versiones.py`). | **Hace `DELETE FROM resultado`** (ver Parte 4, destacado). No hace DDL. Requiere `git` en el PATH y red para el `git clone` inicial. |

Migraciones / cambios de esquema: **ninguno.** `db/schema.sql`, `db/metrics_seed.sql`, `db/repos_seed.sql` y la vista `panel` quedaron intactos (`git diff main -- db/schema.sql` vacío).

### 1.3 Cambios no obvios / colaterales (marcados)

- **`base_metric.py` — sigue habiendo `sys.exit(1)`, NO pasé a `raise`.** `_get`/`_graphql` reintentan, pero cuando se agotan los reintentos (red) o el rate limit es persistente, siguen haciendo `sys.exit(1)` (o `print` + seguir, en el caso 5xx agotado que devuelve el `resp` no-ok y termina en el `sys.exit(1)` de `_rest`). El contrato de "el pipeline se corta con exit 1 ante error duro" **no cambió**.
- **`base_metric.py` — el módulo ahora importa `time` y `from datetime import datetime`** (antes solo `sys`, `requests`). `_rest_list_since` parsea fechas dentro de `base_metric`.
- **`base_metric.py` — `_LIST_SINCE_CACHE` es estado global de módulo.** Vive lo que dura el proceso; clave `(org, repo, path, inicio.isoformat(), fin.isoformat())`. Si dos ventanas distintas usan exactamente el mismo rango de fechas comparten resultado (no debería pasar con bloques disjuntos, pero es un supuesto). No hay invalidación ni límite de tamaño.
- **`base_metric.py` — `_rest_list_since` slimea los items** a `("id","created_at","updated_at","issue_url","pull_request_url","commit_id","html_url","user.login")`. Cualquier métrica que en el futuro necesite otro campo del comentario (`body`, `reactions`, `author_association`…) **ya no lo va a tener**. Hoy ninguna de las 4 lo usa.
- **`base_metric.py` — `_rest_list_since` agrega `sort=updated&direction=asc` a la request.** El endpoint de issue-comments por defecto ordena por `created`. Cambia el orden de iteración (no afecta a métricas que agregan en set/contador, pero es un cambio de request).
- **`base_metric.py` — `_get` come 403 de cuota pero NO 403 de permisos.** `_es_rate_limit` devuelve `False` si no hay `retry-after` ni `x-ratelimit-remaining==0`; ese 403 "real" cae al `sys.exit(1)` de `_rest`. Correcto, pero es una distinción sutil.
- **`run_versiones.py` — arreglé un import roto del catálogo:** `from user_reported_bugs import NumberOfBugsDetectedByUsers` → `from nub import …` (el módulo real es `39/nub.py`). **Esto coincide con lo que ClaraLopez1 ya hizo en `run.py` (`c4a4963`)**, así que no es divergencia. `run_batch_anmcc.py` todavía tiene el nombre viejo (envuelto en try/except → `None`).
- **`run_versiones.py` — `noi_28` sigue apuntando a `open_issues` (módulo inexistente) → `None`, se saltea.** ClaraLopez1 en `run.py` lo reapuntó a `from noi import NumberOfOpenIssues as NumberOfOpenIssuesRegistro28`. **Divergencia de intención sobre qué es el registro 28** (¿NOI genérica o métrica propia sin implementar?).
- **`run_versiones.py` — `Base.ensure_metrica()` hace `INSERT INTO metrica (metrica_id, nombre) … ON CONFLICT DO NOTHING`** con la **clave de código** (`'nci'`, `'cd'`, `'loc_notion'`, …) y un nombre. El seed (`metrics_seed.sql`) usa otros ids (`'number_of_closed_issues'`, `'lines_of_code'`, …). Resultado: la tabla `metrica` termina con **filas de las dos convenciones conviviendo**. No rompe FKs, pero es data que las otras dos podrían no esperar.
- **`run_versiones.py` — `guardar_ventana` decide el tipo de fila según el valor:** escalar → `value`; `dict` → `_escalar_de()` busca una "clave de resumen" conocida (`sc`, `experiencia_meses`, `porcentaje`, `value`, `valor`, `total`, `score`, `count`) para `value` y manda el dict entero a `value_extra`; `list`/`tuple`/`str` → todo a `value_extra` con `value=NULL`; `bool` → `float(bool)`. Este mapeo es **una convención mía**, no está en `schema.sql`.
- **`run_versiones.py` — `_correr_sliceable` recorta atributos internos por nombre:** para `disc_centrality`→`metadata_comentarios`, `nc`/`exprev`/`rexprev`→`eventos`, `sc`/`sc_disc`→`_issues`+`_prs`, `dev_exp`→(sin recorte, solo cambia `fecha_fin`). **Depende de nombres de atributos privados de cada clase.** Si otra persona renombra `self.eventos` o `self._issues`, se rompe en silencio (recorte vacío).
- **`run_versiones_local.py` — la atribución por persona pasa a ser el NOMBRE de git** del autor (`%an`) en vez del `login` de GitHub, porque el clon local no tiene el login. Distinto label para el mismo dev en `resultado.contribuyente_login`.
- **`db/docker-compose.yml` — cambié el binding de puerto**, que es config compartida: si otra persona asume `localhost:5432` fijo, ahora depende de `POSTGRES_PORT` en `db/.env`.

---

## Parte 2 — Clasificación de cada cambio: API vs FÓRMULA

### `base_metric.py`

| cambio | categoría | detalle |
|---|---|---|
| `_get()` con timeout + reintentos (red / 5xx) + espera de rate limit | **API/infra** | Puramente "cómo se baja". Intercambiable. La "mejor versión" entre las tres se puede unificar sin discutir contenido. |
| `_graphql()` con la misma lógica | **API/infra** | Ídem. Mismo valor de retorno y mismo `sys.exit` ante error duro. |
| `_headers()` extraído, `_rest()` delega en `_get()` | **API/infra** | Refactor sin cambio de comportamiento observable. |
| `_rest_list_since()` — since-walk para pasar el 422 de paginación | **API/infra en su mecánica**, pero **arrastra un cambio de FÓRMULA** (ver recuadro) | El *cómo se pagina* es infra. El *qué queda en la lista* cambió. |
| Cache `_LIST_SINCE_CACHE` + slim de items | **API/infra** | Optimización. El slim podría ser FÓRMULA si alguien necesitara un campo borrado — hoy no. |

> **⚠️ Cambio de FÓRMULA escondido en `_rest_list_since` — afecta a `disc_centrality`, `nc`, `exprev`, `rexprev`:**
>
> - **Versión `main`** (loop manual en cada clase): `params={"since": fecha_inicio}` + en memoria `if created > fecha_fin: continue`. `since` filtra por **`updated_at ≥ fecha_inicio`**. No se chequea `created ≥ fecha_inicio`. → conjunto = **`{comentarios : updated_at ≥ inicio  AND  created_at ≤ fin}`**. Incluye comentarios viejos re-editados dentro del bloque; incluye todo lo creado antes de `fin` sin piso real por `created`.
> - **Mi versión** (`_rest_list_since`): guarda `if fecha_inicio <= created <= fecha_fin` (ambos bordes sobre **`created_at`**). → conjunto = **`{comentarios : inicio ≤ created_at ≤ fin}`**.
> - En estas 4 clases `por_persona`/`por_producto` **no re-filtran por fecha**: usan tal cual lo que dejó `fetch`. Entonces esto **cambia el input de la métrica**, no solo el transporte.
> - Mi versión es (a mi criterio) la definición correcta y coherente entre bloques ("actividad de discusión creada en el período"), y además es la única que no depende del `since=updated_at` como pseudo-borde. Pero **es una decisión de contenido**: si otra persona dejó la semántica vieja a propósito (p. ej. "cualquier hilo tocado en el bloque"), **choca** y hay que decidir cuál va.

### `18/disc_centrality.py`

- **API/paginación:** loop manual `while page` sobre `/issues/comments`, `/pulls/comments`, `/repos/.../comments` → `self._rest_list_since(...)`. Se hereda: since-walk, dedup por `id`, retries, rate-limit, cache, slim. **Puramente API en lo que escribí en esta clase.**
- **FÓRMULA:** no cambié nada *en esta clase* — el `calcular_discussion_centrality` (grafo MBSN, grado del nodo) y la construcción de `metadata_comentarios` (`item_id`, `user_login`, `fecha`) son idénticos. **PERO** hereda el cambio de conjunto de comentarios descrito en el recuadro de arriba (input distinto → resultado distinto).

### `18/nc.py`

- **API/paginación:** `_fetch_paginated` loop manual → `self._rest_list_since(...)`. API pura en esta clase.
- **FÓRMULA:** `calcular_nc` (conteo de eventos tipo comentario) y la construcción del evento (`type`, `login`, `fecha`) sin cambios. Hereda el cambio de conjunto de comentarios del recuadro.

### `15/exprev.py`

- **API/paginación:** **solo** `_fetch_comments` (los 2 endpoints REST de comentarios) → `self._rest_list_since(...)`. `_paginate_issues` / `_paginate_prs` (GraphQL, `orderBy: UPDATED_AT DESC`, early-break `updated < fecha_inicio`) **NO los toqué** — quedan como en `main`.
- **FÓRMULA:** `calcular_exprev` (suma de issues/PRs abiertos+cerrados + comentarios) sin cambios. `_closer_login` sin cambios. Hereda el cambio de conjunto solo en la **parte de comentarios** (`issue_comments`, `pull_request_comments`); la parte de issues/PRs sigue con la lógica vieja.

### `15/rexprev.py`

- Idéntico a `exprev`. **API:** solo `_fetch_comments`. **FÓRMULA:** `calcular_rexprev` (ponderación `1/(días+1)` con `fecha_fin` como referencia) sin cambios. Hereda el cambio de conjunto solo en comentarios.

### `20/dc.py` (`sc`, `sc_disc` — misma clase reexportada)

- **API/paginación:** no cambié la paginación (`_paginate` GraphQL sigue igual: `first:100`, cursor, filtro `fecha_inicio <= created <= fecha_fin` en memoria).
- **FÓRMULA / forma de datos:** agregué `"created"` al dict de cada registro. **No cambia `por_producto` ni `por_persona`** (siguen usando `author` y `state`). Es un campo extra **inerte dentro de `dc.py`**; lo consume `run_versiones_local.py`. Riesgo de choque: bajo (campo aditivo), pero si otra persona también agregó un campo con otro nombre para lo mismo, hay que unificar el nombre.

### Resumen para el merge

- **100% API (se toma la mejor versión, sin discutir contenido):** todo `base_metric.py` como *mecánica*; el reemplazo de loops por `_rest_list_since` en `disc_centrality`/`nc`/`exprev`/`rexprev`; los cambios de `db/docker-compose.yml`, `db/README.md`, `.gitignore`.
- **Requiere decisión de contenido:** el **conjunto de comentarios** que alimenta `disc_centrality`, `nc`, `exprev`, `rexprev` (`updated_at ≥ inicio ∧ created ≤ fin`  vs  `inicio ≤ created ≤ fin`). Si otra de las tres tocó estos endpoints con otra semántica, **no se puede "tomar una" a ciegas**.
- **Aditivo, bajo riesgo:** `created` en `dc.py`.

---

## Parte 3 — Supuestos sobre el runner y riesgo de divergencia

### Supuestos que mis clases modificadas hacen sobre el runner

| clase | firma de `fetch` que asumo | qué devuelve `por_persona` | ¿necesita "clave_valor" para dict compuesto? |
|---|---|---|---|
| `18/disc_centrality.py` | `fetch(fecha_inicio, fecha_fin)` — sin `con_actor`, sin `max_*`. Se llama **una vez por bloque** (o una vez sobre el rango completo si el runner la trata como "sliceable"). | `dict[str, int]` (`login -> grado de centralidad`). Escalar por persona. | No. |
| `18/nc.py` | `fetch(fecha_inicio, fecha_fin)`. | `dict[str, int]` (`login -> NC`). Escalar. | No. |
| `15/exprev.py` | `fetch(fecha_inicio, fecha_fin)`. | `dict[str, int]` (`login -> EXPRev`). Escalar. | No. |
| `15/rexprev.py` | `fetch(fecha_inicio, fecha_fin)`. `por_persona` usa `fecha_fin` como "ahora" para el decaimiento → **el runner debe pasar el borde derecho real del bloque**. | `dict[str, float]` (`login -> REXPRev`). Escalar. | No. |
| `20/dc.py` (`sc`, `sc_disc`) | `fetch(fecha_inicio, fecha_fin, **kwargs)`. | `dict[str, dict]` — cada valor es `{"issues_opened", "issues_opened_closed", "prs_opened", "prs_opened_closed", "prs_opened_merged", "sc"}`. **Compuesto.** | **Sí** — el runner necesita saber que la clave de resumen es `"sc"`. En `run_versiones.py` eso está en `_CLAVES_ESCALAR`. Si otro runner no lo sabe, guarda `value=NULL`. |

Mi `run_versiones.py` además asume, para las "sliceable" (`disc_centrality`, `nc`, `exprev`, `rexprev`, `sc`, `sc_disc`, `dev_exp`): que puede hacer **un solo `fetch` del rango completo** y después recortar los atributos internos (`metadata_comentarios`, `eventos`, `_issues`, `_prs`) por bloque. Esto **solo es válido porque `por_*` de esas clases no re-filtra por fecha**. Si otra persona agrega un filtro por fecha dentro de `por_persona`, mi recorte y su filtro se pisan (doble filtrado → posible vacío).

### Cambios míos que son correctos SOLO para VERSIONADO / marcados PELIGROSOS

- **🔴 PELIGROSO — `_rest_list_since` y el borde inferior del bloque.** Mi filtro es `inicio ≤ created ≤ fin` estricto sobre `created_at`. Para **bloques cortos** (p. ej. ADAPTATIVO con pisos chicos, o "cada N eventos") esto está bien y es más preciso que la versión vieja. Para VERSIONADO también. **Pero** si otro criterio definía el bloque por `updated_at` (actividad, no creación), mi cambio le cambia el resultado. La versión vieja mezclaba `updated_at` (piso) con `created_at` (techo); mi versión es homogénea en `created_at`. **Hay que acordar cuál es la definición de "comentario del bloque".**
- **🔴 PELIGROSO — `TOPE_PAGINA = 90` y el since-walk asumen bloques que pueden ser MUY grandes.** El since-walk existe justamente porque en VERSIONADO la 1ª ventana abarca años y dispara el 422. Para bloques chicos el since-walk igual funciona pero es *overkill* (una sola tanda y listo). No rompe nada, pero: si un criterio hace **muchísimos** bloques chiquitos, se paga el costo de re-hacer el since-walk por bloque salvo que el runner use el modo "sliceable" (1 fetch total). Mi `run_versiones.py` lo usa; otro runner que llame `fetch` por bloque no.
- **🟡 `_LIST_SINCE_CACHE` con clave por rango de fechas.** Asume bloques **disjuntos** (dos bloques nunca comparten `(inicio, fin)` exactos). Cierto en VERSIONADO y en cualquier partición sensata, pero es un supuesto no chequeado. Sin límite de memoria: un runner con cientos de bloques distintos acumula todo en RAM.
- **🟡 `run_versiones_local.py` usa `origin/HEAD` + `--since/--until` (fecha de *commit*) para elegir los commits del bloque**, replicando lo que hace `/repos/.../commits?since&until`. Asume que "los commits del bloque i" ≈ "los commits en `[fecha_tag_i, fecha_tag_{i+1})` sobre la rama default". Válido para VERSIONADO. Para otro criterio cuyos bordes no coincidan con tags, hay que revisar que el rango de fechas sea el correcto.
- **🟢 No peligroso pero a notar:** `exprev`/`rexprev` quedan **mitad y mitad** — issues/PRs con la paginación GraphQL vieja de `main`, comentarios con mi `_rest_list_since`. Es consistente, pero cualquier merge tiene que mirar las dos mitades por separado.

---

## Parte 4 — Estado para converger

### 4.1 Código COMPARTIDO que toqué (va a conflictuar con las otras dos)

| archivo | naturaleza del conflicto esperado |
|---|---|
| `base_metric.py` | **Alto.** Reescribí `_rest`, `_graphql` y agregué `_get` / `_rest_list_since` / helpers de módulo. `569b280` (luzlaura) ya había tocado este archivo (agregó `_resolve_ref`). Cualquier cambio de las otras dos a `_rest`/`_graphql` choca. La parte de retries/rate-limit/timeout es unificable; el `_rest_list_since` hay que decidir si entra tal cual. |
| `18/disc_centrality.py` | Medio. Reescribí los 3 `_fetch_*comments`. Choca si otra persona tocó esos métodos o el `fetch`. |
| `18/nc.py` | Medio. Reescribí `_fetch_paginated`. |
| `15/exprev.py` | Medio. Reescribí `_fetch_comments` (no `_paginate_issues/_prs`). |
| `15/rexprev.py` | Medio. Ídem `exprev`. |
| `20/dc.py` | Bajo. Una línea aditiva (`"created"` en el dict). |
| `db/docker-compose.yml` | Medio. Config compartida de la DB (puerto + healthcheck). |
| `db/README.md` | Bajo. Solo docs; conflicto textual probable por renumeración de secciones. |
| `.gitignore` | Bajo. Merge trivial (unión de líneas). |

### 4.2 Archivos ESPECÍFICOS de mi criterio (solo míos)

- `run_versiones.py` — runner + generador de bloques VERSIONADO (`ventanas_por_version`) + capa `Base` (Postgres).
- `run_versiones_local.py` — variante local (clon git) para métricas de archivos/commits/blame sin cap.
- `.clones/` — directorio del clon local (gitignoreado; no se commitea).

> No existe carpeta `analisis_versionado/`; si el equipo estandariza un layout `analisis_<criterio>/`, mis dos runners deberían moverse ahí.

### 4.3 🔴 Esquema de la DB — **NO lo toqué en esta ronda**, pero hay data-ops compartidas

- **`db/schema.sql`, `db/metrics_seed.sql`, `db/repos_seed.sql`, la vista `panel`: sin cambios** (`git diff main -- db/` solo muestra `README.md` y `docker-compose.yml`). El esquema `repos/metrica/periodo/resultado/panel` que uso ya estaba en `main` (commit `093ed0f`, mío, anterior a esta ronda).
- **`docker-compose.yml`:** cambié el **binding de puerto** (`${POSTGRES_PORT:-5432}`) y el **healthcheck** (`-d $POSTGRES_DB`). No es un cambio de esquema, pero es infra compartida: si otra persona levanta el contenedor esperando `5432` fijo, ahora manda `POSTGRES_PORT` de `db/.env`.
- **⚠️ `run_versiones.py` escribe en tablas compartidas en runtime:**
  - `INSERT INTO repos … ` si el repo no está.
  - `INSERT INTO metrica (metrica_id, nombre) … ON CONFLICT DO NOTHING` con **claves de código** (`'nci'`, `'cd'`, …) que **no coinciden** con los ids del seed (`'number_of_closed_issues'`, …). La tabla `metrica` termina con ambas convenciones. **Impacta a las tres** si comparten base.
  - `INSERT … ON CONFLICT … DO UPDATE` en `periodo` y `resultado` (upsert por `(repo_id, tipo_analisis, periodo_num)` y por los índices parciales de `resultado`).
- **⚠️ `run_versiones_local.py` hace `DELETE FROM resultado`** (borra las filas de una métrica en todos los `periodo` con `tipo_analisis='versiones'` de ese repo, antes de reescribir). Está acotado a `tipo_analisis='versiones'`, pero **es destructivo sobre una tabla compartida**. Si otra persona tiene resultados de `tipo_analisis='versiones'` en la misma base, se los borra.

---

## Inconsistencias comentario ↔ código detectadas

1. **`base_metric.py:91` y `:203`** — el mensaje impreso dice *"rate limit persistente tras **2** esperas, corto"* pero el guard es `esperas_rl > _MAX_ESPERAS_RL` con `_MAX_ESPERAS_RL = 4` (`base_metric.py:12`). El texto quedó de una versión anterior donde el tope era 2.
2. **`base_metric.py` docstring de `_rest_list_since` (~línea 117)** dice que GitHub corta *"alrededor de la página ~150"*, pero el código usa `TOPE_PAGINA = 90` (`:134`). El 90 es un margen deliberado por debajo del 150; no es un bug, pero el número del docstring y el del código no son el mismo y puede confundir.
3. **`20/dc.py`** — agregué `"created"` a cada registro de `_paginate`, pero ni el docstring de la clase ni los comentarios lo mencionan, y **`por_producto`/`por_persona` de `dc.py` no lo usan**. Es un campo "fantasma" desde el punto de vista de la clase (solo lo lee `run_versiones_local.py`).
4. **`run_versiones.py`** — el comentario de `SLICEABLE` dice que para `dev_exp` "no hay nada que recortar, solo cambia la fecha_fin de referencia", lo cual es correcto, pero `dev_exp` igual está listado en `SLICEABLE` (con lista de atributos vacía) — un lector podría esperar que se recorte algo.

## Cómo reproducir este análisis

```bash
git log --oneline -8
git diff main --stat
git diff main -- base_metric.py 18/disc_centrality.py 18/nc.py 15/exprev.py 15/rexprev.py 20/dc.py
git diff main -- db/docker-compose.yml db/README.md .gitignore
git show c4a4963 --stat        # base actual (ClaraLopez1)
git show 569b280 -- base_metric.py   # cambio previo de luzlaura a base_metric
# archivos nuevos (untracked):
sed -n '1,60p' run_versiones.py
sed -n '1,60p' run_versiones_local.py
```
