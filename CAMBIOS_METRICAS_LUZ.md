# CAMBIOS_METRICAS_LUZ.md

**Autora:** Luz Laura (`luzlaura`) — rama `luz/nextjs`, parte de `origin/next.js`
(trabajo de Ines y Clara). Repo: `vercel/next.js`, series `versiones` (375 ventanas
estables) y `versiones_canary` (3.862 ventanas, incluye prereleases).

El trabajo anterior sobre tldr (particiones adaptativas) quedó en la rama
`luz/tldr-adaptativo`.

## Métricas calculadas

| Registro | Métrica | Clave | Cómo se corre |
|---|---|---|---|
| 15 | Learning Easy | `le` | local (`run_versiones_local.py`) |
| 15 | Skill Similarity | `ss` | API |
| 15 | REXP | `rexp` | local |
| 15 | FEXP | `fexp` | local |
| 15 | EXPRev | `exprev` | API |
| 15 | REXPRev | `rexprev` | API |
| 15 | Contribution Diversity | `cdiv` | local |
| 18 | Number of Comments | `nc` | API |
| 18 | Discussion Centrality | `disc_centrality` | API |
| 23 | Schedule Compliance | `schedule_compliance` | API |
| 27 | Customer Found Defects and Regressions | `cfdr` | API |
| 40 | Development Process Performance | `process_performance` | API |
| 40 | Number of Open Issues | `noi` | API |
| 43 | Tasa de Éxito de Jarczyk | `jarczyk_success_rate` | API |

No se re-corren porque reusan el código de otra métrica ya calculada: NCI (40) y
NCI (43) = `35/nci.py` (`nci`, Ines); Social Contributions (18) = `20/dc.py` (`sc`, Ines).

## Cambios de definición (revisar con Esteban)

1. **Learning Easy (15/le.py)**
   - *Antes:* días entre la primera y la última contribución del autor al componente,
     **solo con commits de la ventana**. En next.js la ventana mediana dura 13,6 días:
     el 75% de los valores por persona daba 0 y el resto quedaba acotado por la
     duración de la ventana.
   - *Ahora:* desde la **primera contribución del autor al componente en toda la
     historia** hasta su última contribución dentro de la ventana. Ceros: 75% → 46%
     (los que quedan son autores que tocaron el componente por primera vez en esa
     ventana).
   - *Componente:* antes era el primer segmento de la ruta (`packages/` agrupaba 20
     paquetes). Ahora `componente_de()`: si `packages`, `crates`, `apps`, `libs`,
     `modules`, `plugins`, `extensions`, `services` o `projects` aparece en los dos
     primeros niveles, el componente es el sub-proyecto (`packages/next`,
     `turbopack/crates/turbopack-core`, `extensions/git`). Regla genérica: en repos
     sin esas carpetas (tldr) da lo mismo que antes.
   - *Por producto:* promedio sobre los pares (autor, componente) activos en la
     ventana, misma definición que por persona.

2. **Tasa de Éxito de Jarczyk (43/tasa_exito.py)**
   - *Antes:* n1 = issues **cerrados** en la ventana (creados en cualquier fecha);
     n = issues **creados** en la ventana. Poblaciones distintas: en 91 ventanas de
     next.js la "proporción" daba > 1 (máx. 13).
   - *Ahora:* n1 = issues creados en la ventana **y** cerrados antes de su fin
     (subconjunto de n, como en el modelo binomial). Queda en [0, 1].

3. **NULL en ventanas no observables** (mismo criterio que `nub` de Clara):
   Schedule Compliance (sin milestones: next.js los usó solo en 2019-2020),
   Process Performance, Jarczyk (sin issues creados) y Learning Easy por producto
   (sin commits) devuelven `None` en vez de 0.0. El runner no guarda fila para
   `None` en métricas escalares (Clara guarda fila con `value = NULL` porque `nub`
   devuelve un dict) — conviene unificar.

## Cambios de código compartido

- **`base_metric.py` — `BOTS_CONOCIDOS`:** agregados los nombres de git de los bots de
  release de next.js (`Vercel Release Bot`, `nextjs-bot`: las métricas locales
  atribuyen por nombre de git, no por login), logins de GitHub Apps que GraphQL
  devuelve sin `[bot]` (`next-js-bot`, `dependabot`, …), agentes de IA (`Copilot`,
  `copilot-swe-agent`, `devin-ai-integration`) y el placeholder de cuentas borradas
  (`desconocido`, `ghost`). **Afecta a `anmcc` local de Ines** (tenía los bots de
  release de next.js): si se re-corre, sale sin ellos.
- **`base_metric.py` — reintentos de red:** los errores de conexión/DNS tienen su
  propio contador (45 intentos, espera tope 60 s ≈ 40 min de tolerancia). Antes un
  corte de internet de un minuto mataba todas las métricas en curso.
- **Filtro de bots** (`self._es_bot`) en las 9 métricas por persona del registro
  15 y 18. En Discussion Centrality los bots se sacan antes de armar el grafo de
  co-participación.
- **Skill Similarity:** caché por login de `/users/{login}/repos` (snapshot actual,
  igual en todas las ventanas: canary ~58k → ~4k requests), los bots no ocupan
  lugar en el tope de `max_contributors` y un 404 (cuenta borrada) no corta la ventana.
- **`run_versiones_local.py`:** para `le`, calcula una vez la primera contribución
  por (autor, componente) sobre todo el `git log`.

## Pendiente de acordar en el equipo

- Atribución por persona: las métricas locales usan **nombre de git** y las de API
  **login de GitHub** (una misma persona aparece con dos claves). Pasa también con
  `cd`/`dloc`/`anmcc` locales.
- NULL guardado vs. fila ausente para ventanas no observables (ver punto 3).
