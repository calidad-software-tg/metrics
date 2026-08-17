# Base de resultados de métricas (Postgres + Docker)

## 1. Levantar la base

```bash
cd metrics/db
docker compose up -d
```

Esto levanta dos contenedores:

- **tg_metricas_db** (`postgres:16-alpine`, puerto `5432`): al crearse por primera vez corre `schema.sql` automáticamente y deja las tablas listas (`repos`, `runs`, `results_producto`, `results_persona`, `metric_catalog`, `metric_isl_map`).

Para parar: `docker compose down` (los datos persisten en el volumen `pgdata`).
Para borrar todo y empezar de cero: `docker compose down -v`.

---

## 2. Cargar los repositorios

`repos_seed.xlsx` es la fuente de verdad de qué repos están en el estudio.

```bash
docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas < repos_seed.sql
```

---

## 3. Cómo cargar resultados de métricas

---

## 4. Compartir resultados con el equipo (seed de resultados)

Hay un único archivo `resultados_seed.sql` en el repo que se va reemplazando cada vez que alguien termina de correr métricas. Ese archivo siempre refleja el estado acumulado de **todas** las corridas hasta el momento, sin conflictos de IDs.

### Flujo

**1. Antes de empezar:** importá el seed actual para arrancar desde donde el equipo dejó.

```bash
docker compose up -d
docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas < repos_seed.sql
docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas < resultados_seed.sql
```

**2. Corrés tus métricas** (las corridas nuevas se acumulan en la base local).

**3. Cuando terminás:** exportás toda la base como el nuevo seed y lo subís al repo (reemplazando el anterior).

```bash
docker exec tg_metricas_db pg_dump \
  -U metricas \
  -d resultados_metricas \
  --data-only \
  --table=runs \
  --table=results_producto \
  --table=results_persona \
  -f /tmp/resultados_seed.sql

docker cp tg_metricas_db:/tmp/resultados_seed.sql ./resultados_seed.sql
```

Subir `resultados_seed.sql` al repo (reemplaza el archivo existente — no crear uno nuevo).

> Como cada quien parte siempre del seed completo del equipo y exporta todo de vuelta, los IDs nunca se pisan entre sí.