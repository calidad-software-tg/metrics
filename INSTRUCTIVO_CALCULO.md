# Instructivo de cálculo — cómo correr cada métrica sobre Next.js

Este instructivo es para volver a calcular las métricas (no solo verlas ya calculadas — para eso está `INSTRUCTIVO.md`). Pensado para poder correr cada métrica de punta a punta y ver el proceso real.

---

## 0. Antes de arrancar

- Repositorio de este proyecto clonado y en la rama `next.js` (ver paso 1 de `INSTRUCTIVO.md`).
- Base de datos levantada (`docker compose up -d` en `db/`) con el schema aplicado.
- Un archivo `.env` en la raíz del proyecto con:
  ```
  GITHUB_TOKEN=<tu token personal de GitHub>
  POSTGRES_HOST=localhost
  POSTGRES_PORT=5433
  POSTGRES_USER=metricas
  POSTGRES_PASSWORD=metricas
  POSTGRES_DB=resultados_metricas
  ```
  El token de GitHub necesita permisos de lectura estándar (no hace falta ningún scope especial) — se usa para no toparse con el límite de 60 requests/hora sin autenticar (autenticado son 5.000/hora).

---

## 1. Clonar `vercel/next.js` (el repositorio bajo análisis)

Ojo: esto **no** es el repo de este proyecto (que ya clonaste en el paso 0) — es una copia aparte del repositorio que se está analizando, **vercel/next.js**, que algunas métricas necesitan tener en el disco para leer directo con `git` en vez de la API de GitHub.

**No hace falta clonarlo a mano.** El script que corre las métricas locales lo clona solo la primera vez que lo necesita:

```bash
python3 run_versiones_local.py --solo cd --repo vercel/next.js
```

Al llamarlo así, si no existe todavía, hace un `git clone` completo de `https://github.com/vercel/next.js.git` dentro de `.clones/next.js/` (relativo a la raíz del proyecto). **Pesa ~2.7 GB y tarda entre 15 y 20 minutos** — es un clon completo con toda la historia, no superficial, porque las métricas necesitan recorrer commits viejos. Se hace una sola vez; las corridas siguientes solo actualizan (`git fetch`) en segundos.

Si preferís clonarlo aparte antes de correr nada, el equivalente manual es:

```bash
mkdir -p .clones
git clone https://github.com/vercel/next.js.git .clones/next.js
```

---

## 2. Qué corre local y qué corre remoto — y por qué

Hay dos scripts distintos, y **no es intercambiable** — cada métrica solo puede correr por una de las dos vías, según qué datos necesita:

- **Local** (`run_versiones_local.py`, lee de `.clones/next.js` con `git log` / `git ls-tree` / `git blame`): solo para métricas que se calculan a partir del **contenido de archivos o del historial de commits** — cosas que existen dentro del propio repositorio git. Más rápido, sin límite de rate, sin necesidad de token (aunque igual lo usa para armar las ventanas).
- **Remoto** (`run_versiones.py`, vía API/GraphQL de GitHub): para métricas que necesitan **issues, pull requests, comentarios, milestones, wiki o cualquier metadata de la plataforma GitHub** — eso no vive en el git, solo existe en los servidores de GitHub.

| Métrica | Clave | Dónde corre | Motivo |
|---|---|---|---|
| ANMCC | `anmcc` | **Local** | Archivos modificados por commit — está en el git |
| Comment Density | `cd` | **Local** | Contenido de archivos de código |
| DLOC | `dloc` | **Local** | Contenido de archivos de documentación |
| README Completeness | `rc` | **Local** | Contenido de README.md |
| Contribution Diversity | `cdiv` | **Local** | Archivos tocados por autor — historial de commits |
| FEXP | `fexp` | **Local** | Historial de commits por archivo |
| Learning Easy | `le` | **Local** | Historial de commits por componente |
| REXP | `rexp` | **Local** | Historial de commits con fecha |
| Lines of Code (LOC) | `loc_notion` | **Local** | Contenido de archivos de código *(pendiente de correr)* |
| Developer Ownership | `developer_ownership_notion` | **Local** | `git blame` *(pendiente de correr)* |
| MTTR | `mttr` | Remoto | Fechas de apertura/cierre de issues |
| Wiki Presence | `wp` | Remoto | Metadata del repo (`has_wiki`) |
| Doc Issue Survival | `dis` | Remoto | Issues etiquetadas como documentación |
| Social Contribution / Developer Contribution | `sc` | Remoto | Issues + PRs por persona |
| Number of Closed Issues | `nci` | Remoto | Issues cerradas |
| Number of Open Issues | `noi` / `noi_28` | Remoto | Issues abiertas |
| Number of Bugs Detected by Users | `nub` | Remoto | Issues con label "bug" + rol del autor |
| Customer-Found Defects and Regressions | `cfdr` | Remoto | Issues + rol del autor |
| Schedule Compliance | `schedule_compliance` | Remoto | Milestones de GitHub |
| Development Process Performance | `process_performance` | Remoto | Fechas de issues |
| Jarczyk Success Rate | `jarczyk_success_rate` | Remoto | Issues cerradas/totales |
| Development Experience | `dev_exp` | Remoto | Fecha de commits vía GraphQL, con login de GitHub |
| EXPRev / REXPRev | `exprev` / `rexprev` | Remoto | Actividad de revisión de PRs |
| Discussion Centrality | `disc_centrality` | Remoto | Comentarios en issues/PRs/commits |
| Number of Comments | `nc` | Remoto | Comentarios en issues/PRs/commits |
| Skill Similarity | `ss` | Remoto | Lenguajes de los propios repos del colaborador (API de usuarios) |
| Number of Branches | `nob_42` | Remoto | Cantidad de branches vía GraphQL |
| ROSI | `rosi` | Remoto | Security advisories *(pendiente de correr)* |

---

## 3. Cómo correr cada métrica

### Métricas locales

```bash
python3 run_versiones_local.py --solo <clave> --repo vercel/next.js
```

Ejemplos reales:
```bash
python3 run_versiones_local.py --solo cd --repo vercel/next.js
python3 run_versiones_local.py --solo anmcc --repo vercel/next.js
python3 run_versiones_local.py --solo dloc,rc --repo vercel/next.js   # varias juntas, separadas por coma
python3 run_versiones_local.py --repo vercel/next.js                  # TODAS las locales de una
```

### Métricas remotas

```bash
python3 run_versiones.py <clave> --repo vercel/next.js
```

Ejemplos reales:
```bash
python3 run_versiones.py mttr --repo vercel/next.js
python3 run_versiones.py sc --repo vercel/next.js
python3 run_versiones.py nci,noi,dis --repo vercel/next.js   # varias juntas, separadas por coma
```

### Para incluir también las ventanas canary (opcional)

Por defecto las dos formas de arriba calculan sobre las **373 ventanas estables** (`tipo_analisis='versiones'`). Si además querés la serie más granular con canary (~4.228 ventanas), agregá `--con-canary` — guarda en una categoría separada (`versiones_canary`), nunca pisa la serie estable:

```bash
python3 run_versiones.py mttr --repo vercel/next.js --con-canary
python3 run_versiones_local.py --solo cd --repo vercel/next.js --con-canary
```

Ojo: con canary son ~10x más ventanas — tarda bastante más (para las métricas remotas que hacen un fetch por cada ventana, como `sc`, puede ser un salto grande de tiempo).

### Filtro de bots

No requiere ninguna acción — está integrado en el código (`base_metric.py`, función `es_bot`). Cuentas de automatización conocidas (bots de release, `github-actions`, `dependabot`, agentes de IA) se excluyen solas de los resultados por persona.

### Probar sin guardar en la base

Para ver el resultado impreso en pantalla sin tocar la base de datos (útil para probar antes de correr en serio):

```bash
python3 run_versiones.py mttr --repo vercel/next.js --no-guardar
python3 run_versiones_local.py --solo cd --repo vercel/next.js --no-guardar
```

---

## 4. Verificar que quedó guardado

```bash
docker exec -it tg_metricas_db psql -U metricas -d resultados_metricas -c "
SELECT metrica_id, count(*) FROM resultado res
JOIN periodo p ON p.periodo_id = res.periodo_id
JOIN repos r ON r.repo_id = p.repo_id
WHERE r.full_name = 'vercel/next.js' AND res.metrica_id = 'mttr'
GROUP BY metrica_id;
"
```

Cada corrida hace **upsert**: volver a correr la misma métrica sobre el mismo repo pisa los valores anteriores en vez de duplicarlos, así que no hay riesgo de correr algo dos veces por error.
