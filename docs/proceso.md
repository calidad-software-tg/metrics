# Cómo funciona tres_p

Este documento explica qué hace la herramienta, paso por paso, y cómo leer lo que devuelve. Está
pensado para alguien que no leyó el trabajo de grado del que surge. Para instalarla y correrla, ver el
[README](../README.md).

## 1. Qué pregunta responde

La calidad del software suele evaluarse sobre el producto: sus defectos, su código, su documentación.
El catálogo de Alonso y Robiolo (2022) propone mirarla en tres dimensiones:

- **Persona:** quienes desarrollan el software (experiencia, participación, forma de colaborar).
- **Proceso:** las prácticas con que lo hacen (gestión de issues, revisión de cambios, releases).
- **Producto:** el software resultante (código, documentación, defectos).

La herramienta busca, en un proyecto concreto, si las métricas de esas tres dimensiones **varían
juntas** a lo largo de su historia, y de qué forma: dentro de cada dimensión, entre pares de
dimensiones y entre las tres a la vez.

Lo que devuelve son **patrones descriptivos**: relaciones que se repiten de un release a otro y que
superaron una serie de controles. No dice qué causa qué, no predice la calidad de un release y no
evalúa a personas.

## 2. Los datos

### 2.1 Ventanas entre releases

La historia del repositorio se divide en **ventanas**: el intervalo entre la publicación de una
release y la siguiente. Se usan las releases porque son cortes que define el propio proyecto. En cada
ventana se calculan todas las métricas, de modo que lo que pasa con las personas y el proceso se puede
comparar con el estado del producto en ese mismo momento.

Se arman dos series:

- **Serie estable:** las ventanas entre releases estables. Es la base del análisis.
- **Serie de réplica** (en el código, `canary`): las ventanas entre todas las releases, incluidas las
  prereleases. Cubre la misma historia con cortes más finos y sirve para comprobar que una relación no
  depende de dónde se cortaron las ventanas. Si el proyecto no publica prereleases, las dos series casi
  coinciden y la réplica no aporta información independiente.

Al armar las ventanas:

- se excluyen los **backports** (una 14.2.x publicada cuando ya existe la 15), porque parten en dos un
  período de trabajo de la versión vigente;
- se excluyen los tags que figuran como estables pero no lo son (`excluir_estable` en `proyecto.json`);
- en la serie estable, las releases publicadas con menos de un día de diferencia se unen;
- se usa una **fecha de corte** común (`hasta`), para que dos corridas en días distintos den las mismas
  ventanas.

### 2.2 Las métricas

Se calculan 26 métricas del catálogo, cada una con su ficha en `metricas/<consigna>/`. Hay dos tipos:

- **Desde el clon** (git): documentación, densidad de comentarios, README, experiencia en los archivos
  y componentes, componentes por commit, diversidad de contribución. No tienen límite de consultas.
- **Desde la API de GitHub:** issues, pull requests, revisiones, comentarios, milestones, branches,
  experiencia de cada persona. Están limitadas a 5.000 consultas por hora, así que en repositorios
  grandes son lo más lento.

Las métricas que describen el estado del repositorio (cuánta documentación hay) se miden al cierre de
cada ventana; las de actividad (cuántas issues se cerraron), con los eventos de la ventana.

### 2.3 Personas y bots

Algunas métricas se calculan por persona. Para eso:

- se unifican las identidades: el mismo contribuyente puede aparecer con su nombre de git y con su
  login de GitHub (`db/mapear_identidades.py`);
- se descarta la actividad de cuentas que no son personas: logins con `[bot]`, bots conocidos
  (`base_metric.py`) y los de `bots_clasificados.csv`. Conviene revisar los más activos de cada
  proyecto y sumarlos a esa lista.

### 2.4 De métricas a variables

Las métricas del proyecto aportan una variable cada una. Las que se calculan por persona se resumen en
cada ventana con:

- la **mediana**, que representa al contribuyente típico;
- en las de volumen de actividad, además, el **percentil 90** (los más activos) y la **proporción del
  total que concentra el 10 % más activo** (cuán concentrado está el trabajo).

Se agregan variables de participación: cuántas personas están activas en cada tipo de actividad,
cuántas participan por primera vez y proporciones como la tasa de ingreso de nuevos contribuyentes o
la proporción de participantes que hace commits.

Antes de analizar se descartan las variables que casi no cambian (el mismo valor en más del 80 % de
las ventanas) y las que tienen datos en menos de 30 ventanas. Por eso **el análisis necesita al menos
30 releases estables**: la herramienta lo comprueba antes de empezar.

Cada variable se transforma en rangos y se le descuentan dos efectos:

- la **tendencia del proyecto** (un spline sobre el orden de las ventanas), para que dos métricas que
  crecen con el proyecto no parezcan relacionadas solo por eso;
- la **duración de la ventana**, porque una ventana más larga acumula más actividad.

## 3. Cómo se decide que una relación es un patrón

Todos los pares de variables se evalúan una sola vez. Cada par pasa por estos filtros, en orden, y
solo los que pasan todos son **patrones**. En el trabajo de grado, de 1.368 pares evaluados quedaron
56 (alrededor del 4 %).

| Etapa | Qué se exige | Para descartar que… |
|---|---|---|
| 1. Significativa | Correlación parcial de Spearman (sin tendencia ni duración) con p corregido por Benjamini–Hochberg menor que 0,05, usando la muestra efectiva | …sea casualidad entre cientos de comparaciones |
| 2. Estable | El mismo signo en todos los períodos de la historia con datos suficientes | …dependa de una sola etapa del proyecto |
| 3. Replicada | El mismo signo en la serie de réplica | …dependa de cómo se cortaron las ventanas |
| 4. Resiste el tamaño | Se mantiene al descontar además la cantidad de contribuyentes activos | …se explique solo por cuánta gente participa |
| 5. No mecánica | Las dos métricas no comparten datos por su definición (por ejemplo, dos formas de contar las mismas issues) | …la relación esté garantizada por el cálculo |
| 6. Validada | Se mantiene al recalcularla sin los datos que podrían producirla (sección 6) | …la produzca un grupo de datos en particular |

Los pares de control (la misma métrica de dos formas, una proporción con sus propias cantidades) no se
evalúan como resultados.

Cada patrón lleva además:

- su **fuerza**: débil (0,1 a 0,3), moderada (0,3 a 0,5) o fuerte (0,5 o más);
- su **nivel de evidencia**: alto, si la relación tiene fuerza en toda la historia y se da release a
  release; bajo, si no alcanza fuerza en ningún período o refleja un cambio de etapa; medio, en el
  resto.

Los **períodos** de la etapa 2 son, por defecto, la historia repartida en cuatro tramos de años
(`calendario`). Se repite con **épocas** (`cortes_epocas`, cuatro tramos de releases): una relación
que pasa con las dos divisiones es estable con los dos cortes de la historia.

## 4. Los tres niveles del análisis

### 4.1 Dentro de cada dimensión

Además de los pares, se buscan los **aspectos** de cada dimensión, es decir, grupos de métricas que
varían juntas:

- **PCA:** resume las variables en pocos componentes. La cantidad se decide con el análisis paralelo
  de Horn; una variable define un componente si su carga es de al menos 0,4. Un componente es
  **firme** si se repite al remuestrear tramos de la historia (congruencia de Tucker de al menos 0,85)
  y en la serie de réplica (al menos 0,70). El PCA necesita al menos tres releases por variable: si una
  dimensión tiene muchas variables y el proyecto pocas releases, esa dimensión se queda sin
  componentes y los pasos que los usan se saltean con un aviso.
- **Agrupamiento (clustering):** agrupa las métricas por su correlación, sin pesos ni signos, como
  contraste del PCA.

### 4.2 Entre pares de dimensiones

Se cruzan las variables, los componentes firmes y los grupos de cada dimensión con los de las otras,
con los mismos filtros. Además, la **correlación canónica** resume en un número cuánto se relacionan
dos dimensiones completas; su significancia se mide desplazando en el tiempo una de ellas.

### 4.3 Entre las tres dimensiones

- **Medida global:** la correlación canónica generalizada (y, como confirmación, el coeficiente RV y
  el análisis factorial múltiple) dice si las tres dimensiones se mueven juntas más de lo que daría el
  azar.
- **Triángulos y cadenas:** se buscan tres elementos, uno por dimensión y de aspectos distintos,
  relacionados de a pares. Cada lado se recalcula descontando el tercer elemento:
  - si los tres lados se mantienen, el patrón es **tridimensional**;
  - si un lado desaparece, es una **cadena**: esas dos dimensiones se relacionan solo a través de la
    tercera, que funciona como eslabón.

### 4.4 Métricas que pertenecen a dos dimensiones

Muchas métricas son de dos dimensiones según el catálogo (por ejemplo, la experiencia en revisión es de
Persona y de Proceso). No se asignan a una sola: **la dimensión es una etiqueta de la relación**, y
cada patrón cuenta para todos los pares de dimensiones que el catálogo permite.

Para las medidas que comparan dimensiones completas (correlación canónica, medida global), donde una
métrica no puede estar en los dos lados, se evalúan **todas las asignaciones posibles** (multiverso):
cada métrica cambiada de lado, la asignación opuesta y 500 asignaciones al azar. Se informa en qué
proporción de ellas las dimensiones aparecen conectadas.

## 5. Cómo leer las salidas

Todo queda en `analisis/salidas/` (o en `trabajo/salidas/` con Docker).

**`relaciones/resumen.md`** es el resultado principal:

- arriba, cuántos pares se evaluaron y cuántos son patrón, por tipo:
  - *entre dimensiones*: sus variables no comparten ninguna dimensión del catálogo;
  - *entre y dentro*: pueden conectar dimensiones distintas o leerse dentro de una que comparten;
  - *dentro*: las dos variables son de la misma dimensión;
- después, una tabla por par de dimensiones con cada patrón, su correlación, su evidencia y su valor
  en la réplica y con el control por tamaño;
- al final, los triángulos: tridimensionales, cadenas y los que no conectan aspectos distintos.

**`relaciones/patrones.csv`** tiene los pares evaluados (uno por fila). Las columnas más útiles:

| Columna | Qué es |
|---|---|
| `rho` | correlación parcial en la serie estable |
| `q` | valor p corregido por Benjamini–Hochberg |
| `rho_canary` | la misma correlación en la serie de réplica |
| `rho_tamano` | la correlación descontando además la cantidad de contribuyentes |
| `rho_<período>` | la correlación en cada período de la historia |
| `robusta` | pasó la significancia, la estabilidad y la réplica |
| `patron` | pasó todos los filtros |
| `motivo` | si no es patrón, por qué (no significativo, no robusto, no resiste tamaño, mecánico, descartado al validar…) |
| `entre`, `dentro` | qué pares de dimensiones puede conectar y en cuál puede leerse dentro |
| `fuerza`, `nivel` | fuerza de la relación y nivel de evidencia |

**`tres_dimensiones/resumen.md`** trae la medida global frente al azar.
**`multiverso_asignacion/resumen.md`** muestra, para cada par de dimensiones, en qué proporción de
asignaciones aparecen conectadas. **`reportes/*.html`** son reportes interactivos de cada dimensión
y de cada cruce, para explorar cada relación release por release.

Al interpretar, conviene tener en cuenta que:

- una correlación de 0,2 o 0,3 es débil: describe una tendencia que se repite, no permite predecir un
  release en particular;
- un patrón **no indica causa**: dos métricas pueden moverse juntas porque las mueve una tercera cosa;
- una relación muy fuerte es la primera candidata a revisar: en el trabajo de grado, las más fuertes
  resultaron producidas por el cálculo o por la composición del equipo.

## 6. Cómo validar los patrones

Los filtros de la sección 3 se definen antes de ver los resultados. La validación se hace después,
sobre los patrones que ya pasaron todo, y depende de cada proyecto, por eso no se automatiza:

1. Para cada patrón, plantear la explicación alternativa más probable. Por ejemplo: «la mediana de
   antigüedad en los componentes baja cuando entran muchos contribuyentes nuevos, así que la relación
   con la tasa de ingreso puede deberse a quién entra a la mediana, no a la antigüedad de quienes ya estaban».
2. Recalcular las variables sin los datos que podrían producir la relación por sí solos: un grupo de
   personas (los recién llegados), un tipo de commits (los que solo tocan documentación) o una parte
   del cálculo (las issues que se abren y se cierran en el mismo release). Antes, comprobar que el
   cálculo con todos los datos reproduce el valor original.
3. Si la correlación queda en ±0,15 o menos, la relación la producían esos datos y se descarta; si se
   mantiene, describe algo del proyecto.

Ejemplo del trabajo de grado: la mediana de Learning Ease y la tasa de ingreso de nuevos contribuyentes
daban −0,73. Sin los recién llegados, +0,01: la relación reflejaba la composición del equipo.

Las relaciones descartadas se cargan en un CSV con columnas `x,y,motivo` (los nombres de las variables,
como aparecen en `patrones.csv`) y se indica en `proyecto.json`, clave `descartados`. Al volver a
correr `analizar`, esas relaciones dejan de contar como patrones en todos los niveles. Sin ese CSV, los
patrones son **candidatos a validar**.

## 7. Límites

- **Releases:** hacen falta al menos 30 releases estables, y bastantes más para que el PCA de Persona,
  que tiene muchas variables, pueda calcularse.
- **Un repositorio no generaliza:** los patrones describen ese proyecto. Para hablar de patrones
  generales hay que comparar varios.
- **Lo que no queda en GitHub no se ve:** reuniones, chats, gestores de tareas externos o
  integraciones que no dejan rastro en el repositorio.
- **Las métricas dependen de cómo trabaja cada proyecto:** por ejemplo, las de bugs dependen de las
  etiquetas o tipos de issue que use; si un proyecto no clasifica bugs, esas métricas quedan vacías o
  incompletas.
- **Las cuentas automatizadas cambian los resultados:** si un bot activo no se detecta, distorsiona las
  métricas por persona.

## Referencias

- Alonso, E. J. y Robiolo, G. (2022). Determinación de la calidad de producto, persona y proceso en
  entornos de desarrollo con GitHub: un estudio sistemático de la literatura. *Jornadas Argentinas de
  Informática (JAIIO)*, 8(3), 21–34.
- Benjamini, Y. y Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful
  approach to multiple testing. *Journal of the Royal Statistical Society: Series B*, 57(1), 289–300.
- Steegen, S., Tuerlinckx, F., Gelman, A. y Vanpaemel, W. (2016). Increasing transparency through a
  multiverse analysis. *Perspectives on Psychological Science*, 11(5), 702–712.
