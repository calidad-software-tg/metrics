# tres_p — patrones de calidad Persona, Proceso y Producto en repositorios de GitHub

Herramienta del trabajo de grado *Descubrimiento de Patrones de Calidad en repositorios CVS*
(Ingeniería en Informática, Universidad Austral). Toma un repositorio de GitHub, calcula métricas de
calidad de sus tres dimensiones a lo largo de su historia y busca qué métricas **varían juntas**:
dentro de cada dimensión, entre pares de dimensiones y entre las tres a la vez.

El resultado son **patrones descriptivos**: relaciones que se repiten de un release a otro y que
superaron una serie de controles. No dice qué causa qué, no predice la calidad de un release y no evalúa
a personas.

| Documento | Qué explica |
|---|---|
| Este README | Todo el proceso: de dónde salen las métricas, qué hace cada paso, cómo levantarlo, configurarlo y correrlo |
| [metricas/README.md](metricas/README.md) | Cada métrica: consigna, dimensiones, de dónde sale y su ficha |
| [analisis/README.md](analisis/README.md) | Los tres niveles de análisis: qué técnica aplica cada paso, con qué criterios y qué reporte la muestra |
| [SALIDAS.md](SALIDAS.md) | Cómo leer los resultados y los reportes |

## 1. La idea

La calidad del software suele evaluarse sobre el producto: sus defectos, su código, su documentación.
El catálogo de Alonso y Robiolo (2022) propone mirarla en tres dimensiones:

- **Persona:** quienes desarrollan el software (experiencia, participación, forma de colaborar).
- **Proceso:** las prácticas con que lo hacen (gestión de issues, revisión de cambios, releases).
- **Producto:** el software resultante (código, documentación, defectos).

La pregunta es si, en un proyecto concreto, lo que pasa en una dimensión se mueve junto con lo que pasa
en las otras.

## 2. De dónde salen las métricas

1. **Catálogo.** Alonso y Robiolo (2022) relevaron 209 métricas de calidad de las tres dimensiones en
   entornos de desarrollo con GitHub.
2. **Priorización.** Se eligieron las consignas que se pueden medir con lo que deja un repositorio de
   GitHub: su historia de git y los datos de la plataforma (issues, pull requests, revisiones,
   comentarios, milestones).
3. **Implementación.** Quedaron **26 métricas**, cada una con su código y su ficha, más algunas
   variantes de control.

Las tres planillas de esa selección están en `metricas/catalogo/`, y el detalle de cada métrica, en
[metricas/README.md](metricas/README.md).

## 3. El proceso

```
repositorio de GitHub
   │  1. calcular      ventanas entre releases y métricas de cada ventana (clon + API) → base PostgreSQL
   │  2. identidades   nombre de git → login de GitHub                                  → datos/
   │  3. exportar      métricas por persona resumidas por ventana                       → datos/
   │  4. analizar      intradimensional, bidimensional y tridimensional, reportes       → salidas/
   ▼
patrones + 3 reportes HTML
```

### 3.1 Ventanas entre releases

La historia se divide en **ventanas**: el intervalo entre una release y la siguiente. Se usan las
releases porque son cortes que define el propio proyecto. En cada ventana se calculan todas las
métricas, así lo que pasa con las personas y el proceso se compara con el estado del producto en ese
mismo momento. Se arman dos series:

- **Serie estable:** ventanas entre releases estables. Es la base del análisis.
- **Serie de réplica** (`canary` en el código): ventanas entre todas las releases, prereleases
  incluidas. Cubre la misma historia con cortes más finos y sirve para comprobar que una relación no
  depende de dónde se cortaron las ventanas. Si el proyecto no publica prereleases, las dos series casi
  coinciden y la réplica no aporta información independiente.

Se excluyen los **backports** (una 14.2.x publicada cuando ya existe la 15) y los tags mal etiquetados
como estables; las releases a menos de un día de la anterior se unen; y todas las corridas usan una
**fecha de corte** común, para que den las mismas ventanas.

### 3.2 Métricas

Unas se calculan desde el **clon** del repositorio (documentación, comentarios, README, experiencia en
archivos y componentes, componentes por commit), sin límite de consultas. Las otras necesitan la **API
de GitHub** (issues, pull requests, revisiones, comentarios, milestones, branches), que permite 5.000
consultas por hora. Por eso, en un repositorio grande, calcular puede llevar días. Las métricas de estado
se miden al cierre de cada ventana; las de actividad, con los eventos de la ventana.

### 3.3 Personas y bots

Varias métricas se calculan por persona. Se unifican las identidades (la misma persona aparece con su
nombre de git y con su login de GitHub) y se descarta la actividad de cuentas que no son personas: logins
con `[bot]`, bots conocidos y los de `metricas/bots_clasificados.csv`. En cada ventana, las métricas por
persona se resumen con la mediana (el contribuyente típico) y, en las de volumen, el percentil 90 y la
proporción que concentra el 10 % más activo.

### 3.4 Análisis

Cada par de variables se evalúa con una correlación parcial de Spearman, sin la tendencia del proyecto
ni la duración de la ventana, y solo cuenta como **patrón** si pasa todos estos filtros:

| Filtro | Qué se exige | Para descartar que… |
|---|---|---|
| Significativa | p corregido por Benjamini–Hochberg menor que 0,05, con la muestra efectiva | …sea casualidad entre cientos de comparaciones |
| Estable | el mismo signo en todos los períodos de la historia | …dependa de una sola etapa del proyecto |
| Replicada | el mismo signo en la serie de réplica | …dependa de cómo se cortaron las ventanas |
| Resiste el tamaño | se mantiene al descontar la cantidad de contribuyentes activos | …se explique solo por cuánta gente participa |
| No mecánica | las dos métricas no comparten datos por su definición | …la relación esté garantizada por el cálculo |
| Validada | se mantiene sin los datos que podrían producirla (sección 6) | …la produzca un grupo de datos en particular |

Sobre eso se suman PCA y agrupamiento para resumir cada dimensión en aspectos, cruces entre
dimensiones, medidas globales, triángulos y cadenas entre las tres, y pruebas de que nada dependa de a
qué dimensión se asigna una métrica que el catálogo pone en dos. Todo está explicado en
[analisis/README.md](analisis/README.md).

Cuántos pares se evaluaron y cuántos patrones quedaron en cada clase se ve al principio de
`salidas/5_patrones/resumen.md` ([SALIDAS.md](SALIDAS.md)).

## 4. Levantarlo

### Con Docker (recomendado)

Requisitos: Docker y un [token de GitHub](https://github.com/settings/tokens). Alcanza con acceso de
lectura a repositorios públicos.

```bash
cp .env.example .env            # completar GITHUB_TOKEN
docker compose pull tres-p      # imagen publicada en ghcr.io, amd64 y arm64 (o: docker compose build)
docker compose up -d db         # PostgreSQL 16
docker compose run --rm tres-p iniciar --repo org/nombre
docker compose run --rm tres-p todo
```

La imagen es la versión fijada en `docker-compose.yml` (`TRES_P_VERSION`, por defecto la última
publicada al escribir esta guía); para usar otra, `TRES_P_VERSION=X.Y.Z` en `.env`. Las versiones están
en [Packages](https://github.com/calidad-software-tg/metrics/pkgs/container/tres-p).

Todo lo que genera queda en `trabajo/`: `proyecto.json`, `datos/` y `salidas/`. Para usar un clon que
ya tengas, en `.env` va `TRES_P_CLON_HOST=/ruta/al/clon` y en `trabajo/proyecto.json`, `"clon": "/repo"`.

### Sin Docker

Python 3.12, git y PostgreSQL 16.

```bash
pip install -r requirements.txt
cp .env.example .env            # GITHUB_TOKEN y POSTGRES_*
python3 tres_p.py iniciar --repo org/nombre [--clon /ruta/al/clon] [--hasta AAAA-MM-DD]
python3 tres_p.py todo
```

### `.env`

| Variable | Qué es |
|---|---|
| `GITHUB_TOKEN` | token de GitHub, para la API |
| `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` | conexión a PostgreSQL (con Docker, host y puerto los pone el compose) |
| `POSTGRES_DB` | la base del proyecto. **Cada repositorio analizado usa su propia base**, porque el análisis no filtra por repositorio |
| `TRES_P_CLON_HOST` | (solo Docker, opcional) clon propio en el host |

La base guarda las ventanas (`periodo`) y el valor de cada métrica en cada ventana, del proyecto o de
cada persona (`resultado`). El esquema está en `db/schema.sql` y el catálogo de métricas en
`db/metrics_seed.sql`; `tres_p.py base` crea la base y carga los dos.

## 5. Configurarlo: `proyecto.json`

`tres_p.py iniciar --repo org/nombre` crea `proyecto.json` (con Docker, en `trabajo/`) a partir de los
valores de [proyecto.example.json](proyecto.example.json). Para un proyecto nuevo alcanza con `repo`;
el resto se ajusta después de mirar los primeros resultados.

| Clave | Qué es | Por defecto |
|---|---|---|
| `repo` | `org/nombre` del repositorio en GitHub | — (obligatoria) |
| `clon` | ruta a un clon propio, para no volver a clonar | `null`: se clona en `.clones/` |
| `hasta` | fecha de corte de la historia (`AAAA-MM-DD`); las releases posteriores se ignoran | `null`: hoy |
| `excluir_estable` | tags que figuran como estables pero no lo son (por ejemplo, `"v2.0.0-rc.1"`): no cortan ventanas ni entran en la serie estable | `[]` |
| `calendario` | los períodos de la regla de estabilidad, como `[["2016-2019", 2016, 2019], …]` | `"auto"`: la historia repartida en cuatro tramos de años |
| `cortes_epocas` | primer release de cada época, para la prueba de sensibilidad (`["v1.4.0", "v2.1.0", "v3.0.2"]`) | `"auto"`: la serie estable cortada en cuartos |
| `descartados` | CSV con las relaciones descartadas al validarlas (columnas `x,y,motivo`), relativo a `proyecto.json` | `null`: los patrones quedan como candidatos |
| `cruces` | carpeta con la configuración de cada cruce (`persona_proceso.json`, …): qué métricas compartidas van a cada lado en los cruces de componentes | `null`: `analisis/cruces/` |
| `tres_dimensiones` | ajustes del análisis de las tres dimensiones (abajo) | `null`: automático |
| `advertencias` | notas sobre métricas de este proyecto que se suman al diccionario de variables, como `{"nub": "antes de 2019 el repo no clasificaba bugs"}` | `null`: ninguna |

`tres_dimensiones` es opcional. Sirve para fijar, después de ver los PCA, qué componentes entran y cómo
se llaman:

```json
"tres_dimensiones": {
  "elegir":  {"Persona": [1, 2, 3], "Proceso": [2, 5], "Producto": [1, 4]},
  "nombres": {"persona_cp1": "renovación del equipo", "proceso_cp5": "cierre de lo viejo"},
  "escala":  ["persona_cp2"],
  "triangulo_destacado": ["persona_cp3", "proceso_cp5", "producto_cp1"],
  "variantes_extra": {"sin_tamano_ni_renovacion": ["persona_cp1"]}
}
```

| Clave | Qué es |
|---|---|
| `elegir` | qué componentes de cada PCA entran (por defecto, los firmes) |
| `nombres` | un nombre para cada componente (por defecto, el de su variable de mayor carga) |
| `escala` | componentes que miden tamaño o volumen de actividad, no calidad: se sacan en las variantes sin tamaño |
| `triangulo_destacado` | un triángulo de componentes que se evalúa siempre |
| `variantes_extra` | variantes más de la medida global, sacando esos componentes |

## 6. Correrlo

```bash
python3 tres_p.py todo          # base + calcular + identidades + exportar + analizar
```

o paso por paso:

| Comando | Qué hace | Tiempo |
|---|---|---|
| `python3 tres_p.py base` | crea la base del proyecto con el esquema | segundos |
| `python3 tres_p.py calcular` | ventanas y métricas, en las dos series. `--series estable` solo la estable; `--solo k1,k2` algunas métricas; `--solo-locales` solo las del clon | horas a días: la API permite 5.000 consultas por hora y el script espera solo cuando se agota |
| `python3 tres_p.py estado` | qué ventanas y métricas hay en la base | segundos |
| `python3 tres_p.py identidades` | nombre de git → login de GitHub (`datos/identidades_git.csv`) | minutos |
| `python3 tres_p.py exportar` | métricas por persona resumidas por ventana (`datos/`) | minutos |
| `python3 tres_p.py analizar` | el análisis completo y los tres reportes. `--sin-complementarios` saltea los análisis complementarios (lo más lento); `--sin-reportes`, los HTML | 15 a 40 minutos |

El análisis necesita **al menos 30 releases estables** (el comando lo comprueba antes de empezar), y
bastantes más para que el PCA de Persona, que tiene muchas variables, pueda calcularse. Con pocas, los
pasos que necesitan componentes en las tres dimensiones se saltean con un aviso.

Cuando termina: `salidas/LEEME.md` es el índice y `salidas/reportes/` tiene los tres HTML. Cómo
leerlos: [SALIDAS.md](SALIDAS.md).

## 7. Validar los patrones

Los filtros se definen antes de ver los resultados. La validación se hace después, sobre los patrones
que ya pasaron todo, y depende de cada proyecto, por eso no se automatiza:

1. Para cada patrón, plantear la explicación alternativa más probable. Por ejemplo: «la mediana de
   antigüedad en los componentes baja cuando entran muchos contribuyentes nuevos, así que su relación con
   la tasa de ingreso puede deberse a quiénes entran a la mediana».
2. Recalcular las variables sin los datos que podrían producir la relación: un grupo de personas (los
   recién llegados), un tipo de commits (los que solo tocan documentación) o una parte del cálculo (las
   issues que se abren y se cierran en el mismo release). Antes, comprobar que el cálculo con todos los
   datos reproduce el valor original.
3. Si la correlación queda en ±0,15 o menos, la relación la producían esos datos: se anota en el CSV de
   `descartados` (`x,y,motivo`, con los nombres de `patrones.csv`). Al volver a correr `analizar`, deja de
   contar como patrón en todos los niveles.

Por ejemplo, si una métrica de experiencia y la tasa de ingreso de nuevos contribuyentes dejan de
relacionarse al recalcularlas sin los recién llegados, la relación reflejaba la composición del equipo,
no la experiencia.

## 8. Límites

- **Un repositorio no generaliza:** los patrones describen ese proyecto.
- **Lo que no queda en GitHub no se ve:** reuniones, chats o gestores de tareas externos.
- **Las métricas dependen de cómo trabaja cada proyecto:** las de bugs, por ejemplo, dependen de las
  etiquetas o tipos de issue que use.
- **Los bots que no se detectan distorsionan las métricas por persona:** conviene revisar las cuentas
  más activas y sumarlas a `metricas/bots_clasificados.csv`.

## 9. Estructura

```
tres_p.py             CLI que encadena los pasos
proyecto.py           lee proyecto.json y .env
proyecto.example.json configuración de ejemplo (sección 5)
metricas/             cálculo: runners, cada métrica con su ficha, identidades, exportación y catálogo de origen
analisis/             los tres niveles de análisis y los reportes
db/                   esquema de la base y catálogo de métricas
Dockerfile, docker-compose.yml, .github/workflows/   imagen y su publicación en ghcr.io

datos/                (generado) métricas por persona e identidades
salidas/              (generado) resultados y reportes
```

## Referencias

- Alonso, E. J. y Robiolo, G. (2022). Determinación de la calidad de producto, persona y proceso en
  entornos de desarrollo con GitHub: un estudio sistemático de la literatura. *Jornadas Argentinas de
  Informática (JAIIO)*, 8(3), 21–34.
- Benjamini, Y. y Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful
  approach to multiple testing. *Journal of the Royal Statistical Society: Series B*, 57(1), 289–300.
- Steegen, S., Tuerlinckx, F., Gelman, A. y Vanpaemel, W. (2016). Increasing transparency through a
  multiverse analysis. *Perspectives on Psychological Science*, 11(5), 702–712.
