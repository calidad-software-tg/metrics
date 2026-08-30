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

## 2. Cargar los repos

```bash
docker exec -i tg_metricas_db psql -U metricas -d resultados_metricas < repos_seed.sql
```

## 3. Cargar métricas y resultados

Pendiente — se define después qué valores cargar en `metrica`, cómo generar
los `periodo` de cada `tipo_analisis`, y cómo insertar en `resultado`.

## 4. Verificar

```bash
docker exec -it tg_metricas_db psql -U metricas -d resultados_metricas -c "\dt"
docker exec -it tg_metricas_db psql -U metricas -d resultados_metricas -c "SELECT * FROM panel LIMIT 10;"
```

## 5. Compartir resultados con el equipo

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
