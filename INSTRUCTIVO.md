# Instructivo — clonar el repositorio, levantar la base y visualizar las métricas

Guía para reproducir el análisis de métricas 3P (Producto, Persona, Proceso) calculado sobre **`vercel/next.js`**, sin tener que volver a correr nada.

---

## 0. Contexto rápido

- **Repositorio analizado:** [`vercel/next.js`](https://github.com/vercel/next.js) — el framework de código abierto, no una app hecha con Next.js.
- **Ventanas temporales:** se cortó la historia del repo en dos series distintas:
  - `versiones` — **373 ventanas**, una por cada **release estable** (sin canary/prerelease). Es la serie principal.
  - `versiones_canary` — **~4.228 ventanas**, una por **cada release publicada** (estable + canary). Mucho más granular (ventanas de horas, no de semanas).

---

## 1. Clonar el repositorio

```bash
git clone git@github.com:calidad-software-tg/metrics.git
cd metrics
git checkout next.js
```

Todo el trabajo sobre Next.js (código de las métricas, seed, correcciones) está en la rama **`next.js`**, no en `main`.

---

## 2. Levantar la base de datos (Postgres + Docker)

```bash
cd db
cp .env.example .env   # si todavía no existe
docker compose up -d
```

Esto crea el contenedor `tg_metricas_db` y corre `schema.sql` automáticamente la primera vez (tablas `repos`, `metrica`, `periodo`, `resultado` + la vista `panel`).

- **Puerto:** publicado según `POSTGRES_PORT` en `db/.env` (en este proyecto: `5433`, no el 5432 default, para no chocar con otro Postgres local).
- Para parar: `docker compose down` (los datos quedan en el volumen). Para borrar todo: `docker compose down -v`.

Más detalle en [`db/README.md`](db/README.md).

---

## 3. Cargar los datos

```bash
# 1. catálogo de repositorios (incluye vercel/next.js)
docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas < repos_seed.sql

# 2. resultados de Next.js — viene comprimido
gunzip -c nextjs_seed.sql.gz | docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas
```

> **Usar `nextjs_seed.sql.gz`, no `resultados_seed.sql`.** Ese otro archivo es un seed viejo y separado, con resultados de **tldr-pages/tldr** (el repositorio con el que arrancó el proyecto antes de pivotear a Next.js) — no tiene nada que ver con este análisis.

`nextjs_seed.sql.gz` ya trae todo junto: el catálogo de las 27 métricas calculadas, las 4.228 ventanas (ambas series) y ~4.2 millones de filas de resultados. La carga tarda unos minutos por el volumen — es normal, no hay que interrumpirla.

Si ya tenías la base levantada de antes con un esquema viejo (sin la categoría `versiones_canary`), corré primero:
```bash
docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas < schema.sql
```

---

## 4. Visualizar los resultados

### Opción rápida: SQL directo

La vista `panel` ya deja todo unido (repo + versión + métrica + valor), lista para consultar:

```bash
docker exec -it tg_metricas_db psql -U metricas -d resultados_metricas -c "
SELECT * FROM panel
WHERE repo = 'vercel/next.js' AND tipo_analisis = 'versiones'
ORDER BY periodo_num LIMIT 20;
"
```

### Para gráficos: exportar a CSV

Para ver la evolución de una métrica release a release (nivel producto, sin desglose por persona):

```bash
docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas -c "
COPY (
  SELECT r.full_name AS repo, per.periodo_num, per.etiqueta AS version,
         per.fecha_inicio, per.fecha_fin, m.metrica_id, m.nombre AS metrica_nombre,
         res.value
  FROM resultado res
  JOIN periodo per ON per.periodo_id = res.periodo_id
  JOIN repos r ON r.repo_id = per.repo_id
  JOIN metrica m ON m.metrica_id = res.metrica_id
  WHERE r.full_name = 'vercel/next.js' AND per.tipo_analisis = 'versiones'
    AND res.contribuyente_login IS NULL
  ORDER BY per.periodo_num, m.metrica_id
) TO STDOUT WITH CSV HEADER
" > evolucion_releases.csv
```

Ese CSV se puede subir a Google Sheets y conectarlo desde **Looker Studio** 

---

## 5. Cómo se calcularon las métricas — metodología

- **Dos formas de cálculo**, según qué necesita cada métrica:
  - **API de GitHub** (`run_versiones.py`) — para métricas que dependen de issues, PRs o metadata de la plataforma (ej. MTTR, Number of Closed Issues, Wiki Presence).
  - **Clon local del repositorio** (`run_versiones_local.py`, lee de `.clones/next.js` con `git log`/`git ls-tree`/`git blame`) — para métricas que solo necesitan contenido/historial de código (ej. Comment Density, DLOC, ANMCC, README Completeness). Más rápido y sin límite de rate de la API.
- **Filtro de bots:** hay una lista centralizada en `base_metric.py` (`BOTS_CONOCIDOS`) que excluye cuentas de automatización (bots de release, `github-actions`, `dependabot`, agentes de IA) de las métricas de Persona, para que no se cuenten como si fueran colaboradores reales.
- **27 de 29 métricas del catálogo corridas** sobre Next.js. Pendientes: ROSI (Return on Security Investment) y Lines of Code. MTTF y MTBF nunca se implementaron como código (quedaron solo documentadas junto a MTTR).
- El detalle completo de qué mide cada métrica y el resultado obtenido está en el Excel mencionado arriba.

---

## 6. Dónde leer cómo está implementada cada métrica

El repositorio organiza cada métrica en una **carpeta numerada** (el número es el ID de relevamiento del catálogo original de 209 métricas). Adentro de cada carpeta hay:

- Un archivo **`N - Nombre de la métrica.md`** — la ficha técnica: qué consigna cubre, cuál es la métrica original (ISL), la fórmula, el fundamento teórico y de qué papers sale.
- Un archivo **`.py`** — la implementación real (qué endpoint/comando usa, cómo procesa los datos, la fórmula en código).

| Carpeta | Métricas que contiene |
|---|---|
| `10/` | MTTR · ANMCC |
| `15/` | Contribution Diversity · EXPRev · FEXP · Learning Easy · REXP · REXPRev · Skill Similarity |
| `16/` | Comment Density · Doc Issue Survival · Documented Lines of Code (DLOC) · README Completeness · Wiki Presence |
| `18/` | Discussion Centrality · Number of Comments · Social Contributions |
| `20/` | Social Contribution (Developer Contribution) |
| `21/` | ROSI (Return on Security Investment) — pendiente de correr |
| `23/` | Schedule Compliance |
| `27/` | Customer-Found Defects and Regressions |
| `28/` | Number of Open Issues |
| `35/` | Number of Closed Issues |
| `38/` | Development Experience |
| `39/` | Number of Bugs Detected by Users |
| `40/` | Development Process Performance · NOI · NCI (reutilizada) |
| `42/` | Number of Branches |
| `43/` | Jarczyk Success Rate · NCI (reutilizada) |

Por ejemplo, para entender **MTTR**: leer `10/10 - MTTR.md` (la teoría) y `10/mttr.py` (el código).