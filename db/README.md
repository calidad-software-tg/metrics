# Base de resultados

| Archivo | Qué es |
|---|---|
| `schema.sql` | tablas `repos`, `metrica`, `periodo` (una fila por ventana entre releases) y `resultado` (valor de cada métrica en cada ventana, por persona o por producto), más la vista `panel` |
| `metrics_seed.sql` | catálogo de métricas (`metrica`): clave, nombre, dimensión y consigna |

`python3 tres_p.py base` crea la base del proyecto (`POSTGRES_DB` del `.env`) y carga los dos
archivos. Con Docker, el servicio `db` de `docker-compose.yml` levanta un PostgreSQL 16 vacío.

Los runners de `calculo/` hacen *upsert*: volver a calcular la misma métrica en la misma ventana pisa
el valor en vez de duplicarlo.

Consultas útiles:

```bash
python3 tres_p.py estado                       # ventanas y métricas cargadas
docker compose exec db psql -U metricas -d "$POSTGRES_DB" -c "SELECT * FROM panel LIMIT 10;"
```

Para compartir una base ya calculada:

```bash
docker compose exec db pg_dump -U metricas -d "$POSTGRES_DB" > base.sql
```
