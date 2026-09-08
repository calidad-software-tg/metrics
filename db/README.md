# Base de resultados de métricas (Postgres + Docker)

Esquema: `repos`, `metrica`, `periodo`, `resultado` (+ vista `panel`).
La tabla `metrica` arranca vacía a propósito — se carga después con los valores reales.

## 1. Levantar la base

```bash
cd metrics/db
cp .env.example .env   # si todavía no existe
docker compose up -d
```

Al crearse el contenedor por primera vez corre `schema.sql` solo y deja las tablas listas.
Para parar: `docker compose down` (los datos persisten en el volumen `pgdata`).
Para borrar todo y empezar de cero: `docker compose down -v`.

**Puerto**: el host publica el puerto que diga `POSTGRES_PORT` en `.env` (default 5432).
Si ya tenés otro Postgres ocupando el 5432, poné `POSTGRES_PORT=5433` en `db/.env`
y la misma variable en el `.env` de la raíz para que los runners se conecten ahí.

**Si el volumen `db_pgdata` ya existía** de una versión previa del esquema, el
`schema.sql` montado NO se vuelve a correr solo. O borrás y recreás
(`docker compose down -v && docker compose up -d`) o lo aplicás a mano:

```bash
docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas < schema.sql
```

## 2. Cargar los repos

```bash
docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas < repos_seed.sql
```

## 3. Cargar el catálogo de métricas

```bash
docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas < metrics_seed.sql
```

## 4. Correr métricas y guardar resultados

Análisis por versiones (un `periodo` entre cada tag consecutivo, `tipo_analisis='versiones'`):

```bash
cd metrics
python3 run_versiones.py mttr                 # corre y guarda en periodo + resultado
python3 run_versiones.py anmcc --repo flutter/flutter
python3 run_versiones.py mttr --no-guardar    # solo imprime
```

Hace upsert: volver a correr la misma métrica sobre el mismo repo pisa los
valores en vez de duplicarlos. Necesita `POSTGRES_*` en el `.env` de la raíz.

## 5. Verificar

```bash
docker exec -it tg_metricas_db psql -U metricas -d resultados_metricas -c "\dt"
docker exec -it tg_metricas_db psql -U metricas -d resultados_metricas -c "SELECT * FROM panel LIMIT 10;"
```

## 6. Compartir resultados con el equipo

```bash
docker exec tg_metricas_db pg_dump \
  -U metricas -d resultados_metricas --data-only \
  --table=metrica --table=periodo --table=resultado \
  -f /tmp/resultados_seed.sql

docker cp tg_metricas_db:/tmp/resultados_seed.sql ./resultados_seed.sql
```

Subir `resultados_seed.sql` al repo (reemplaza el archivo existente). Cada quien
arranca importando `repos_seed.sql` + `resultados_seed.sql` antes de correr lo suyo,
y vuelve a exportar todo al terminar — así los IDs nunca se pisan entre sí.
