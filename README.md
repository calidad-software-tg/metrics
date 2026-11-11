# tres_p — patrones de calidad Persona, Proceso y Producto en repositorios de GitHub

Herramienta del trabajo de grado *Descubrimiento de Patrones de Calidad en repositorios CVS*
(Ingeniería en Informática, Universidad Austral). A partir de un repositorio de GitHub:

1. arma ventanas entre releases consecutivas: la serie **estable** y una serie de **réplica** con
   todas las releases (prereleases incluidas);
2. calcula en cada ventana **26 métricas** del catálogo de Alonso y Robiolo (2022), unas desde el
   clon (git) y otras desde la API de GitHub;
3. unifica las identidades (nombre de git → login) y descarta bots;
4. busca **patrones** dentro de cada dimensión, entre pares de dimensiones y entre las tres, con
   correlaciones parciales sin la tendencia ni la duración de la ventana, Benjamini–Hochberg,
   estabilidad en el tiempo, réplica, control por tamaño del equipo y exclusión de relaciones
   mecánicas; además PCA, agrupamiento, correlación canónica, multiverso de asignaciones de las
   métricas compartidas y búsqueda de cadenas entre las tres dimensiones.

Cómo funciona cada paso y cómo leer los resultados: [docs/proceso.md](docs/proceso.md).

El resultado son **patrones descriptivos**: relaciones que superaron los controles. No es un modelo
predictivo, no evalúa a personas ni genera recomendaciones.

## Inicio rápido (Docker)

Requisitos: Docker y un [token de GitHub](https://github.com/settings/tokens) (alcanza con acceso de
lectura a repositorios públicos).

```bash
cp .env.example .env            # completar GITHUB_TOKEN
docker compose pull tres-p      # imagen publicada en ghcr.io (o: docker compose build)
docker compose up -d db
docker compose run --rm tres-p iniciar --repo org/nombre
docker compose run --rm tres-p todo
```

Los hallazgos quedan en `trabajo/salidas/`:

| Archivo | Qué tiene |
|---|---|
| `relaciones/resumen.md` | los patrones, por par de dimensiones, y las cadenas entre las tres |
| `relaciones/patrones.csv` | cada par evaluado, con su correlación, sus controles y por qué es o no patrón |
| `tres_dimensiones/resumen.md` | asociación global de las tres dimensiones frente al azar |
| `multiverso_asignacion/resumen.md` | qué conexiones dependen de a qué dimensión se asignan las métricas compartidas |
| `reportes/*.html` | reportes interactivos de cada dimensión y de cada cruce |

Para usar un clon que ya tengas: en `.env`, `TRES_P_CLON_HOST=/ruta/al/clon`, y en
`trabajo/proyecto.json`, `"clon": "/repo"`.

## Sin Docker

Python 3.12, git y una base PostgreSQL 16.

```bash
pip install -r requirements.txt
cp .env.example .env            # GITHUB_TOKEN y POSTGRES_*
python3 tres_p.py iniciar --repo org/nombre [--clon /ruta/al/clon] [--hasta AAAA-MM-DD]
python3 tres_p.py todo
```

## Pasos sueltos

```bash
python3 tres_p.py base          # crea la base del proyecto (POSTGRES_DB) con el esquema
python3 tres_p.py calcular      # métricas por ventana; --series estable, --solo k1,k2, --solo-locales
python3 tres_p.py estado        # qué ventanas y métricas hay en la base
python3 tres_p.py identidades   # nombre de git -> login de GitHub (db/identidades_git.csv)
python3 tres_p.py exportar      # métricas por persona (persona_agregado_estable_canary.csv)
python3 tres_p.py analizar      # análisis completo; --sin-reportes para saltear los HTML
```

`calcular` es lo que más tarda: las métricas de la API de GitHub están limitadas a 5.000 consultas
por hora y, en repositorios grandes, pueden llevar días (el script espera solo cuando se agota la
cuota). Con `--solo-locales` se calculan solo las que salen del clon.

## Configuración del proyecto (`proyecto.json`)

| Clave | Qué es |
|---|---|
| `repo` | `org/nombre` en GitHub |
| `clon` | clon local propio (si no, se clona en `.clones/`) |
| `hasta` | fecha de corte de la historia (por defecto, hoy) |
| `excluir_estable` | tags que no deben contar como releases estables |
| `calendario` | períodos para la regla de estabilidad; `"auto"` reparte los años en cuatro |
| `cortes_epocas` | primer release de cada época; `"auto"` corta la serie estable en cuartos |
| `descartados` | CSV (`x,y,motivo`) con las relaciones descartadas al validarlas |

Cada proyecto usa su propia base (`POSTGRES_DB`): el análisis no filtra por repositorio.

## Qué queda en manos de quien analiza

- **Validación.** El último filtro del trabajo fue recalcular cada relación sin los datos que podían
  producirla (por ejemplo, sin los recién llegados). Eso depende del proyecto y no se automatiza: sin
  un CSV de `descartados`, los patrones se informan como candidatos a validar.
- **Réplica.** Si el repositorio no publica prereleases, la serie de réplica coincide con la estable
  y no aporta una réplica independiente.
- **Bots.** Se descartan los logins con `[bot]`, los conocidos (`base_metric.py`) y los de
  `bots_clasificados.csv`; conviene revisar los más activos de cada proyecto.

## Estructura

```
tres_p.py              CLI que encadena los pasos
proyecto.py            lee proyecto.json (repo, períodos, épocas, descartados)
run_versiones.py       métricas desde la API de GitHub, por ventana
run_versiones_local.py métricas desde el clon (git), por ventana
export_persona.py      métricas por persona, agregadas por ventana
metricas/              las métricas, por consigna, cada una con su ficha (.md)
analisis/              preprocesamiento, correlaciones, PCA, clustering, cruces, 3D, multiverso, relaciones
db/                    esquema de la base, catálogo de métricas y unificación de identidades
docs/                  cómo se calcula cada métrica, correcciones y selección del caso
```
