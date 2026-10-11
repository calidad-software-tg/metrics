---
cruce: Producto-Producto
titulo: Análisis de la dimensión Producto
subtitulo: Correlaciones y componentes principales entre métricas de la misma dimensión · next.js
---

## 1. Métricas de Producto

El primer paso es analizar las correlaciones entre las métricas mapeadas dentro de una misma dimensión, en este caso Producto. Las métricas identificadas son:

| IDs registro | Métrica original ISL | Métrica | ID consigna | Texto consigna |
|---|---|---|---|---|
| 10 | CPU Usage | ANMCC (Número Promedio de Componentes Modificados por Commit) | 52 | La utilización eficiente de recursos |
| 10 | CPU Usage | MTTR (Tiempo Medio de Reparación), MTTF (Tiempo Medio de Falla) y MTBF (Tiempo Medio entre Fallas) | 52 | La utilización eficiente de recursos |
| 15 | Contribution Diversity | Learning Easy | 15 | La capacidad de aprender nuevas habilidades técnicas |
| 16 | Documentation Quality | CD (Comment Density) | 18 | La calidad de la documentación |
| 16 | Documentation Quality | README Completeness | 18 | La calidad de la documentación |
| 16 | Documentation Quality | Wiki Presence | 18 | La calidad de la documentación |
| 16 | Documentation Quality | DLOC | 18 | La calidad de la documentación |
| 39, 27 | User-Detected Bugs, Solution Quality | Customer Found Defects and Regressions / Number of Bugs Detected by Users | 35, 22 | Número de Bugs detectados por Usuarios, La calidad de las soluciones implementadas |
| 28, 40 | Number of Open Issues, Process Compliance | Number of Open Issues (NOI) | 43, 47 | Cantidad de problemas (issues) abiertos en su repositorio, La adhesión a las prácticas / políticas de desarrollo definidas |
| 42 | Number of Active Development Branches | Number of Branches | 41 | Cantidad de branches de desarrollo activas que existen en su repositorio principal |

De la fila de MTTR, MTTF y MTBF se calculó solo MTTR.

Métricas excluidas por no variar en el tiempo:

- **Wiki Presence** vale 0 en todos los releases, porque next.js no tiene wiki.
- **Number of Branches** vale lo mismo en todos los releases (2.706), porque es una foto del momento en que se calculó y no una serie.

Sin variación no es posible calcular correlaciones, así que estas dos métricas no entran al análisis.

## 2. Variables analizadas

Quedan **9 métricas de Producto que varían en el tiempo**: ANMCC, MTTR, Learning Easy, CD, DLOC, README Completeness, CFDR, NUB y NOI. Todas se calculan sobre el producto completo, con un valor por release.

Seis de ellas (ANMCC, MTTR, Learning Easy, CD, DLOC y README Completeness) también se calcularon **para cada colaborador individualmente**. Esos valores individuales se resumieron en un valor por release:

- **Mediana:** el valor del colaborador típico del release. Se calculó para las seis métricas.
- **p90:** el valor que alcanzan los colaboradores que más aportan (supera al 90% de los colaboradores). Mide la intensidad del aporte de los más activos. Se calculó solo para DLOC.
- **Share del top 10%:** qué parte del total aporta el 10% de colaboradores que más aporta. Mide la concentración del trabajo. Se calculó solo para DLOC.

El p90 y el share del top 10% se calcularon solo para DLOC porque es la única métrica de Producto que representa un volumen de trabajo: líneas de documentación que se suman entre colaboradores, de modo que el total del release es la suma de lo que aportó cada uno. Las otras cinco métricas son promedios, proporciones o puntajes por colaborador, no cantidades que se suman, así que "qué parte del total aportan los más activos" no tiene interpretación para ellas.

CFDR, NUB y NOI no tienen versión por colaborador porque su definición no atribuye las issues a un desarrollador: cuentan bugs reportados por usuarios externos o issues abiertas del repositorio. Por eso solo tienen versión de producto.

En total se obtuvieron **17 variables**:

- 9 calculadas sobre el producto;
- 8 calculadas a partir de los colaboradores: 6 medianas, el p90 de DLOC y el share del top 10% de DLOC.

## 3. Pares analizados

Combinando las 17 variables de a dos se obtienen **136 pares**:

- 36 entre variables de producto;
- 72 entre una variable de producto y una de colaboradores;
- 28 entre variables de colaboradores.

De ellos se excluyen **11 pares de control**, que comparan una misma métrica calculada de distintas formas: cada métrica de producto contra su mediana por colaborador (6 pares) y las distintas versiones de DLOC entre sí (5 pares). Estos pares están relacionados por construcción, así que no aportan información. Quedan **125 pares evaluados**.

[[grafico kpis]]

El mapa de calor muestra la correlación de cada par (las celdas vacías son la diagonal). Con el selector se puede ver la correlación corregida o la cruda:

[[grafico mapa]]

**Por qué el mapa se ve distinto con la correlación cruda y con la corregida.** La correlación cruda compara los valores tal como se midieron. Si dos métricas crecen a lo largo de la historia del proyecto, aparecen muy correlacionadas aunque no estén relacionadas, solo porque comparten la tendencia. La corregida descuenta el momento del proyecto y la duración de cada ventana, y mide si las métricas se mueven juntas más allá de esa tendencia.

- **La mayoría de las relaciones se debilitan al corregir.** 40 de los 125 pares tienen una correlación cruda de 0,3 o más en valor absoluto; con la corregida quedan 11. Son métricas que crecen con la edad y el tamaño del proyecto (más documentación, más antigüedad de los colaboradores, más issues abiertas), así que la correlación cruda refleja ese crecimiento compartido. Por ejemplo:
  - DLOC ↔ Learning Easy: de +0,77 a +0,06.
  - Learning Easy ↔ NOI: de +0,69 a −0,12.
  - MTTR (mediana por colaborador) ↔ NOI: de +0,65 a −0,03.
  - ANMCC ↔ Learning Easy: de +0,58 a +0,04.
- **Algunas relaciones se hacen más fuertes al corregir.** En estos casos la tendencia de largo plazo tapaba la relación: las métricas evolucionan de forma parecida a lo largo de los años, pero de un release al siguiente se mueven en sentido opuesto (o en el mismo sentido), y eso solo se ve al sacar la tendencia. Por ejemplo:
  - DLOC ↔ README Completeness: de −0,06 a −0,44.
  - CD ↔ DLOC: de −0,33 a −0,66.
  - CD ↔ README Completeness: de +0,05 a +0,35.
- **Una relación cambia de signo:** DLOC ↔ NOI es +0,64 en crudo (las dos crecen con el proyecto) y −0,36 corregida.

## 4. Datos utilizados

- **Unidad de análisis:** la ventana entre un release estable y el siguiente. Son 371 ventanas, excluyendo 4 releases mal etiquetados como estables.
- **Datos faltantes:** cada par usa solo las ventanas donde las dos variables tienen dato.
  - Los pares que incluyen CFDR o NUB quedan limitados al período desde fines de 2020. Entre 2016 y 2020 estas variables no tienen valor porque los bugs no se etiquetaban.
  - Los demás pares usan toda la historia, desde 2016.
- **Réplica:** los releases canary se usan para verificar si los resultados se repiten en otra serie de datos.

## 5. Tipos de correlación calculados

Para cada par se calcularon las siguientes correlaciones:

1. **Correlación cruda.** Correlación de Spearman directa entre las dos variables, sin ninguna corrección. Muestra la relación tal como se ve a simple vista.
2. **Correlación corregida lineal.** Descuenta el tiempo, modelado como una recta según el orden de los releases, y la duración de la ventana. Se usa solo como referencia.
3. **Correlación corregida (análisis principal).** Descuenta el crecimiento del proyecto y la duración de la ventana, para que dos métricas no parezcan relacionadas solo porque ambas crecen con el tiempo o porque dependen de cuánto duró la ventana. Se calcula así:
   1. Se pasan a rangos (posición de menor a mayor) las dos variables y la duración de la ventana.
   2. Para cada variable se estima, mediante una regresión, qué parte de su valor se explica por el momento del proyecto y por la duración de la ventana. El momento del proyecto se modela con una curva suave según el orden de los releases, que puede captar un crecimiento que no es parejo.
   3. A cada release se le resta lo que predice esa regla. Queda lo que la variable tiene de más o de menos respecto de lo esperable para ese momento y esa duración.
   4. Se correlacionan esas diferencias entre las dos variables.
4. **Correlación corregida por tamaño.** Se explica más abajo, en esta sección.

El efecto de la corrección se ve comparando, para cada par, la correlación cruda con la corregida. Los pares que caen a la franja central eran crecimiento del proyecto:

[[grafico cruda_corregida]]

**Correlación corregida por tamaño.** Las variables calculadas a partir de los colaboradores dependen de cuánta gente participó en cada release. Por ejemplo, la concentración del top 10% o el p90 cambian si participan 5 o 200 personas, aunque nadie trabaje distinto. Esto puede hacer que dos variables parezcan relacionadas solo porque ambas varían con la cantidad de participantes.

El control por tamaño toma la correlación corregida, que ya descuenta el tiempo y la duración de la ventana, y le agrega el descuento del **número de personas activas en interacción** en el release: personas que abrieron o cerraron issues o pull requests, o comentaron. El resultado indica cuánto se relacionan dos variables una vez descontado el efecto de la cantidad de gente.

**Cómo se calcula:** con el mismo procedimiento de la correlación corregida.

1. Se pasan a rangos las dos variables y la cantidad de personas activas.
2. Se estima mediante una regresión qué parte de cada variable se explica por la cantidad de personas, el momento del proyecto y la duración de la ventana.
3. A cada release se le resta lo que predice esa regla, y se correlacionan las diferencias.

**No se divide por la cantidad de personas ni se descartan releases:** se usan todos los releases y la regresión estima cuánto influye la cantidad de gente en cada variable.

**Cuándo se aplica:** solo a los pares que incluyen al menos una variable calculada a partir de los colaboradores. En Producto–Producto son 89 pares.

**Releases independientes.** Como los releases consecutivos se parecen entre sí, los datos contienen menos información independiente que la cantidad de releases. Por eso se estima a cuántos releases independientes equivalen los que hay, y ese número se usa para calcular el p-valor y el intervalo de confianza de la correlación corregida. Con menos releases independientes el intervalo es más ancho y es más difícil que una relación resulte significativa.

**Correlación por período.** La correlación corregida también se calculó por separado en cuatro períodos (2016–19, 2020–22, 2023–24 y 2025–26), aplicando la misma corrección dentro de cada uno y con al menos 15 ventanas por período. Esto permite verificar si la relación se mantiene a lo largo del tiempo y cómo evoluciona.

## 6. Clasificación de los resultados

La clasificación se basa en la correlación corregida.

**Significancia.** Se calculan un p-valor y un intervalo de confianza a partir de la cantidad de releases independientes. Como se evalúan muchos pares a la vez, el p-valor se ajusta por comparaciones múltiples (Benjamini–Hochberg), dentro de cada cruce de dimensiones.

**Categoría:**

- **Positiva o negativa:** la relación es significativa (p-valor ajustado menor a 0,05). El signo indica la dirección.
- **Sin relación:** todo el intervalo de confianza queda entre −0,2 y 0,2. Los datos permiten afirmar que la relación es nula o despreciable.
- **No concluyente:** no se cumple ninguna de las anteriores. El intervalo es demasiado amplio o la relación no es significativa tras el ajuste, así que los datos no alcanzan para afirmar ni descartar una relación.

**Fuerza:** débil (entre 0,1 y 0,3), moderada (entre 0,3 y 0,5) o fuerte (más de 0,5), en valor absoluto.

**Estabilidad:** una relación es estable si la correlación tiene el mismo signo que la de toda la historia en todos los períodos con datos, y hay al menos tres períodos evaluables.

[[grafico categorias]]

[[grafico embudo]]

## 7. Relaciones robustas

Una relación es **robusta** cuando no depende de cómo o dónde se mire: se mantiene en la misma dirección a lo largo del tiempo y se repite en otra serie de datos. Debe cumplir tres condiciones:

1. **Es significativa:** su categoría es positiva o negativa.
2. **Es estable en el tiempo:** en cada período tiene el mismo signo que en toda la historia.
3. **Se repite en los releases canary:** calculada sobre los releases canary, tiene el mismo signo que sobre los estables.

### 7.1 Tabla y gráficos generales

Se identificaron **7 relaciones robustas**:

1. CD ↔ DLOC
2. DLOC ↔ README Completeness
3. DLOC ↔ README Completeness (mediana por colaborador)
4. DLOC p90 ↔ README Completeness (mediana por colaborador)
5. CFDR ↔ MTTR (mediana por colaborador)
6. NUB ↔ MTTR (mediana por colaborador)
7. CFDR ↔ NUB

Al hacer clic en una fila, el análisis particular de esa relación se muestra en la sección 7.2:

[[explorador robustas tabla]]

### 7.2 Análisis particular

Para cada relación robusta se revisa a qué se debe, cómo es, si se cumple en todos los períodos y cómo podría explicarse. Se muestra la relación elegida en la tabla de 7.1; también se puede abrir en el explorador del anexo para mirarla con más detalle.

[[explorador robustas detalle]]

[[nota cd_producto dloc_producto]]
**Qué muestran los datos:**

- Es la relación más fuerte del bloque (−0,66) y pasa todos los controles. Pero solo aparece en los últimos años: entre 2016 y 2022 es prácticamente 0, en 2023–24 es muy fuerte (−0,87) y en 2025–26 moderada (−0,46). Se la considera estable porque el signo es negativo en todos los períodos, aunque en los primeros sea casi nulo (la correlación móvil incluso llega a ser positiva en 2020–21).
- **Por qué aparece desde 2023.** En esos años el repositorio de next.js cambió de estructura varias veces, y en cada cambio las dos métricas saltaron en sentido contrario en el mismo release. La corrección por tiempo solo descuenta el crecimiento gradual, no los saltos, así que esos saltos opuestos quedan como una relación negativa:

| Cuándo | Qué pasó en el repositorio | DLOC | CD |
|---|---|---|---|
| Mediados de 2023 | La documentación oficial y los mensajes de error se pasan a un formato de archivo (`.mdx`) que DLOC no cuenta | Baja de 33.700 a 17.500 líneas | Sin cambio |
| Fines de 2023 | Se borran ejemplos viejos y se actualizan las librerías externas que el proyecto guarda dentro de su código | Baja | Sube (0,09 → 0,12) |
| Fines de 2024 | Se suma al repositorio Turbopack, una herramienta que antes estaba en otro repositorio, y se vuelven a actualizar las librerías externas | Sube de 15.500 a 47.700 líneas | Baja (0,12 → 0,04) |

- **CD casi no mide los comentarios del equipo.** La mayoría de los comentarios que cuenta están en copias de librerías externas (como React) que next.js guarda dentro de su repositorio. Cuando esas copias se actualizan, CD cambia aunque nadie haya tocado los comentarios del propio proyecto. Eso explica los dos saltos de CD de la tabla.
- **Desde fines de 2024 se mezclan además dos versiones del código.** La serie de releases estables intercala parches de la versión vieja (v14) con releases de la nueva (v15 y v16), y cada uno mide su propio código. Por eso las dos métricas saltan juntas entre dos niveles. En el gráfico, los puntos naranjas son los parches de la versión vieja:

[[par cd_producto dloc_producto: dispersion, temporal | periodo=2025-2026]]

**Qué indica:** la relación no muestra que más documentación vaya con menos comentarios en el código, sino que ciertos cambios de estructura del repositorio movieron las dos métricas al mismo tiempo. Que se repita en canary no lo descarta, porque canary mide el mismo repositorio.
[[/nota]]

[[nota dloc_producto rc_producto; dloc_producto rc_mediana; dloc_p90 rc_mediana]]
**Qué muestran los datos** (las tres versiones de DLOC ↔ README Completeness):

- Las tres son negativas y moderadas (−0,33 a −0,44): en los releases donde DLOC queda por encima de lo esperable para su época, README Completeness queda por debajo. Como CD ↔ DLOC, son más fuertes en los últimos años, aunque cada versión tiene su propio recorrido:

| Período | DLOC ↔ README | DLOC ↔ README (mediana) | DLOC p90 ↔ README (mediana) |
|---|---|---|---|
| 2016–19 | −0,34 | −0,07 | −0,11 |
| 2020–22 | −0,26 | −0,01 | −0,27 |
| 2023–24 | −0,89 | −0,39 | −0,50 |
| 2025–26 | −0,13 | −0,59 | −0,43 |

- **Miden en parte lo mismo.** DLOC cuenta todas las líneas de documentación, incluidas las de los README, y README Completeness evalúa justamente esos README. Algo de relación es esperable por definición.
- **README Completeness depende de cuántos ejemplos hay.** next.js tiene cientos de proyectos de ejemplo, cada uno con su README, así que casi todos los README del repositorio son de ejemplos. La métrica es el promedio de todos, y cambia cuando se agregan o se borran ejemplos aunque nadie edite un README.
- **Por qué se intensifica desde 2023.** Igual que con CD, los cambios de estructura del repositorio movieron las dos métricas en sentido contrario en el mismo release. A fines de 2023 se borraron ejemplos viejos: DLOC bajó y README Completeness subió (de 0,26 a 0,28). A fines de 2024 se sumó Turbopack: DLOC subió de 15.500 a 47.700 líneas y README Completeness bajó. El cambio de formato de la documentación a mediados de 2023 bajó DLOC pero no movió README Completeness.
- Desde fines de 2024 también las afecta la mezcla de parches de la versión vieja con releases de la nueva, igual que a CD ↔ DLOC.

**Qué indica:** como en CD ↔ DLOC, la relación refleja cambios de estructura del repositorio más que un patrón de cómo el equipo documenta.
[[/nota]]

[[nota cfdr_producto mttr_mediana; mttr_mediana nub_producto]]
**Qué muestran los datos** (CFDR ↔ MTTR y NUB ↔ MTTR son la misma relación):

- Es débil (−0,22): en los releases con más bugs reportados por usuarios, el MTTR del colaborador típico es más bajo. Cubre desde fines de 2020 y se concentra desde 2023 (−0,42 en 2023–24 y −0,26 en 2025–26).
- **Por qué baja: cambia quiénes entran en la cuenta.** MTTR (mediana) no mide cuánto tarda el equipo en reparar bugs. En cada ventana toma a todas las personas que cerraron alguna issue (de cualquier tipo), calcula cuánto tardó cada una en promedio y se queda con el valor del medio. La mayoría de quienes cierran son usuarios ocasionales que cierran rápido (mediana de 44 horas), mientras que los 21 colaboradores frecuentes cierran issues que llevan semanas abiertas (mediana de 667 horas). Cuando se reportan más bugs aparecen más usuarios ocasionales, pasan a ser mayoría entre quienes cierran y el valor del medio baja. El equipo no repara más rápido.
- **Más débil en canary (−0,12).** Las ventanas canary duran una mediana de medio día, contra 5 días en las estables. Tienen una mediana de 4 bugs y 2 personas que cierran issues, y en el 65 % cierran 2 personas o menos. Con tan pocos casos, la mediana de MTTR depende de una o dos personas y el ruido tapa la relación.
- **Con el control por tamaño baja a −0,14.** El control descuenta la cantidad de personas activas en la ventana. CFDR y la cantidad de personas que cierran issues van juntas (0,74 aun descontando la duración y el tiempo), y son justamente esas personas las que bajan la mediana. Al descontar el tamaño se saca esa parte de la relación.
- **No la afectan los backports.** Los backports son releases que parchean una versión mayor anterior (por ejemplo, una v14.2.x publicada en 2025, cuando la rama principal ya está en la v15). Afectan a las métricas que miden el código del release (CD, DLOC y README Completeness), porque ese código es el de la versión vieja. CFDR, NUB y MTTR cuentan issues abiertas o cerradas entre dos fechas, sin importar qué código se publicó.
[[/nota]]

[[nota cfdr_producto nub_producto]]
**CFDR y NUB** cuentan las issues de bug (por etiqueta o por tipo de issue) creadas en la ventana y reportadas por alguien externo al equipo. Solo difieren en a quién consideran equipo: CFDR, a los 10 contribuidores con más commits (el "Surgical Team" de su ficha); NUB, a quienes tenían un rol formal al abrir la issue (dueños, miembros de la organización o colaboradores con permisos de escritura). Como next.js recién empezó a clasificar bugs a fines de 2020, las dos tienen datos solo desde entonces.

**Qué muestran los datos:** coinciden en 191 de las 231 ventanas con dato en ambas (0,9999). Es la misma medida con dos definiciones de equipo, así que **no constituye un hallazgo**; por eso CFDR ↔ MTTR y NUB ↔ MTTR cuentan como una sola relación.
[[/nota]]

## 8. Relaciones significativas

Una relación es **significativa** cuando su categoría es positiva o negativa: el p-valor ajustado por comparaciones múltiples es menor a 0,05. Son las relaciones que pasan el primer filtro, antes de exigirles estabilidad en el tiempo y réplica en canary.

### 8.1 Tabla y gráficos generales

Los 125 pares evaluados se distribuyen así: 59 no concluyentes, 50 sin relación, 9 con relación negativa y 7 con relación positiva.

**7 pares tienen relación positiva:**

1. CFDR ↔ NUB
2. ANMCC ↔ MTTR
3. ANMCC (mediana por colaborador) ↔ Learning Easy (mediana por colaborador)
4. CD ↔ README Completeness (mediana por colaborador)
5. CD ↔ README Completeness
6. CD ↔ NOI
7. DLOC ↔ Learning Easy (mediana por colaborador)

Solo CFDR ↔ NUB es robusta, y no es un hallazgo porque es la misma métrica. Las demás no son estables: cambian de signo en algún período.

**9 pares tienen relación negativa:**

1. CD ↔ DLOC
2. DLOC ↔ README Completeness
3. CD ↔ DLOC (share del top 10%)
4. DLOC ↔ README Completeness (mediana por colaborador)
5. DLOC ↔ NOI
6. DLOC p90 ↔ README Completeness (mediana por colaborador)
7. CD ↔ DLOC (mediana por colaborador)
8. MTTR (mediana por colaborador) ↔ NUB
9. CFDR ↔ MTTR (mediana por colaborador)

**Observaciones:**

- 6 de los 9 vinculan DLOC con otra métrica de documentación (CD o README Completeness).
- CFDR / NUB ↔ MTTR (mediana por colaborador) es una sola relación contada dos veces, porque CFDR y NUB son la misma métrica.

Algunos pares de métricas comparten parte de su definición, por lo que una correlación entre ellas es en parte esperable y no constituye un hallazgo:

- **CFDR ↔ NUB:** las dos cuentan issues de bug reportadas por personas externas; coinciden en 0,9999.
- **DLOC ↔ README Completeness** (y sus versiones por colaborador): DLOC cuenta las líneas de todos los archivos `.md`, `.txt` y `.rst`, incluidos los README.md, mientras que README Completeness evalúa solo los README.md. Entre el 28% y el 80% de las líneas de DLOC están en READMEs, según la versión.
- **NOI ↔ CFDR / NUB:** cada bug reportado es también una issue, y si sigue abierta se suma a NOI.

La tabla lista todas las relaciones significativas, de mayor a menor correlación; con el selector se pueden ver solo las positivas o solo las negativas. Al hacer clic en una fila, el análisis particular de esa relación se muestra en la sección 8.2:

[[explorador significativas tabla | direccion]]

Cada relación significativa con su intervalo de confianza (punto relleno si además es robusta):

[[grafico forest]]

Y en qué períodos existe cada una:

[[grafico estabilidad]]

La red resume las 16 relaciones significativas: el grupo de documentación se arma alrededor de DLOC.

[[grafico red]]

### 8.2 Análisis particular

Se muestra la relación elegida en la tabla de 8.1, con sus gráficos y, si las tiene, sus observaciones (las de las relaciones robustas son las mismas de 7.2).

[[explorador significativas detalle]]

[[nota dloc_producto noi_producto]]
**Observación:** DLOC ↔ NOI sale negativa en el total, pero dentro de los períodos es prácticamente 0 y en 2023–24 es positiva. La correlación global viene de diferencias entre períodos, no de una relación dentro de ninguna etapa.
[[/nota]]

## 9. Robustez frente al control por tamaño

El control por tamaño se explica en la sección 5.

**Robusta por tamaño:** una relación lo es si ya era robusta y, tras el control, su correlación sigue teniendo el mismo signo y un valor absoluto de al menos 0,1. Cuatro de las siete relaciones robustas cumplen esta condición:

1. DLOC ↔ README Completeness (mediana por colaborador)
2. DLOC p90 ↔ README Completeness (mediana por colaborador)
3. CFDR ↔ MTTR (mediana por colaborador)
4. NUB ↔ MTTR (mediana por colaborador)

En las relaciones de documentación la cantidad de gente casi no influye. En la relación entre CFDR / NUB y MTTR, parte se explica por la cantidad de participantes, pero se mantiene por encima del umbral.

Las otras tres relaciones robustas (CD ↔ DLOC, DLOC ↔ README Completeness y CFDR ↔ NUB) son entre variables de producto, por lo que el control no se les aplica.

## 10. Advertencias sobre los datos de Producto

- **Backports en la serie estable.** De los 369 releases estables, 60 son parches de una versión mayor anterior (8 en 2024, 30 en 2025 y 20 en 2026). Las métricas que son una foto del código en el release (CD, DLOC y README Completeness, y sus versiones por colaborador) saltan entre dos árboles de código distintos. Las relaciones entre ellas desde fines de 2024 pueden ser un efecto de esa mezcla. Opciones: sacar los backports de la serie estable, o calcular esas métricas sobre la rama principal al cierre de cada ventana.
- **DLOC no cuenta `.mdx`.** Desde junio y julio de 2023, cuando `docs/` y `errors/` pasaron a `.mdx`, deja de contar la documentación oficial.
- **DLOC suma Turbopack.** Desde la v15.0.0 incluye unas 27.000 líneas de `turbopack/crates`, y parte son salidas de tests, no documentación.
- **CD está dominada por código de terceros.** La mayoría de sus comentarios está en `packages/next/src/compiled`, no en el código propio del proyecto.
- **README Completeness depende de la cantidad de ejemplos.** Es un promedio sobre todos los README.md, y la mayoría son de `examples/`.
- **CFDR y NUB desde fines de 2020.** Los pares con estas métricas cubren menos años y no son comparables directamente con los demás.

## 11. Componentes principales

El análisis de componentes principales (PCA, por *Principal Component Analysis*) es una técnica estadística que reduce muchas variables correlacionadas a unas pocas variables nuevas, los **componentes**, que conservan la mayor parte de la información. Cada componente es una combinación de las métricas originales: el primero se elige para captar la mayor variación posible de los datos, el segundo la mayor variación que queda, y así sucesivamente, sin que se repita información entre ellos. Así, métricas que se mueven juntas quedan resumidas en un mismo componente, y cada componente tiene un valor (puntaje) en cada release.

### 11.1 Cómo se calcularon

- **Matriz de datos:** una fila por release y una columna por métrica. El PCA necesita que cada release tenga valor en todas las métricas, así que se usan 200 releases estables, desde fines de 2020 (cuando empiezan CFDR y NUB) hasta 2026, y 2.223 releases canary. Se excluyen los backports (24 en la serie estable), porque las métricas que miden el código saltan entre dos versiones distintas.
- **Escala por rangos:** cada métrica se reemplaza por su posición (rango) entre los releases y se estandariza. Es el mismo criterio que la correlación de Spearman: no lo afectan los valores extremos ni los saltos bruscos, y no supone una relación lineal.
- **Dos conjuntos de variables:** las **9 métricas a nivel producto** (versión principal, cada métrica pesa una vez) y las **17 variables**, que suman las versiones por colaborador (mediana, p90, share del top 10 %).
- **Tres enfoques**, para ver si los componentes dependen de cómo se preparan los datos:
  - **Crudo:** los rangos tal cual.
  - **Ajustado:** a cada rango se le descuenta la tendencia de largo plazo y la duración de la ventana, igual que en la correlación corregida.
  - **Ajustado y sin tamaño:** además se descuenta la cantidad de personas activas.

**Cómo se obtiene cada componente.** Con la matriz de correlaciones entre las métricas se calculan:

- los **autovalores**: cuánta variación de los datos explica cada componente. Se mide en "métricas": cada métrica estandarizada tiene una variación de 1, así que con 9 métricas el total es 9, y un autovalor de 2,4 significa que el componente resume tanta variación como 2,4 métricas enteras (el 27 % del total). No indica cuántas métricas forman el componente; eso lo muestran las cargas;
- las **cargas**: la correlación entre cada métrica y cada componente. Indican qué métricas forman cada componente;
- los **puntajes**: el valor del componente en cada release.

**Rotación varimax.** Los componentes del PCA se ordenan por cuánta variación explican, y eso suele hacer que muchas métricas carguen un poco en varios a la vez, lo que los hace difíciles de interpretar. La rotación varimax gira los componentes retenidos para que cada métrica cargue fuerte en uno solo y casi nada en los demás. No cambia cuánta variación explican entre todos; solo la reparte de una forma más fácil de leer.

### 11.2 Cuántos componentes se retienen

Se calcularon cuatro criterios:

- **Kaiser:** retiene los componentes con autovalor mayor a 1, es decir, que explican más que una sola métrica. Es simple, pero suele quedarse con demasiados.
- **Codo del gráfico de sedimentación (scree):** retiene los componentes hasta el punto donde la curva de autovalores se aplana.

**Con las 9 variables a nivel producto:**

[[pca scree producto estable ajustado]]

Los tres primeros autovalores (2,38, 1,96 y 1,34) quedan por encima de la línea de Horn. El cuarto (1,03) cae apenas por debajo de lo que da el azar (1,11), y a partir de ahí la curva se aplana.

**Con las 17 variables:**

[[pca scree todas estable ajustado]]

La curva baja de forma más gradual y no tiene un codo marcado. Los cinco primeros autovalores (3,25, 2,25, 1,90, 1,57 y 1,39) superan la línea de Horn (1,66, 1,52, 1,41, 1,32 y 1,25); el sexto (1,18) queda justo por debajo (1,19). Con más variables, los componentes se reparten la variación en partes más chicas.

- **Varianza acumulada:** retiene los componentes necesarios para explicar el 70 % o el 80 % de la variación. Es una meta de cuánto resumir, no una prueba de que el componente sea real.
- **Análisis paralelo de Horn:** mezcla al azar los valores de cada métrica (así se rompe cualquier relación real entre ellas), repite el PCA 500 veces y retiene solo los componentes cuyo autovalor supera al 95 % de los que da el azar. Es el criterio principal, porque es el único que separa un componente real del ruido.

**Con las 9 variables a nivel producto:**

[[pca criterios producto]]

- Con las 9 métricas, **Horn retiene 3 componentes en los tres enfoques y en las dos series**.
- Kaiser y la varianza acumulada indican 4, porque el cuarto autovalor (1,03) está apenas por encima de 1. Pero queda por debajo de lo que da el azar (1,11), y en el bootstrap su autovalor varía entre 0,92 y 1,17. Si se lo agrega, ese cuarto componente lo forman ANMCC (0,84) y LE (0,57), y es inestable (congruencia de 0,60 en el 5 % de los peores remuestreos). Por eso se retienen 3.

**Con las 17 variables:**

[[pca criterios todas]]

- En la serie estable, **Horn retiene 5 componentes con el enfoque ajustado y con el ajustado sin tamaño, y 3 con el crudo**. En canary retiene 7 en los tres enfoques.
- Kaiser y la varianza acumulada piden más (7 a 9), porque con 17 variables hay muchos componentes chicos con autovalor apenas mayor a 1. El sexto y el séptimo (1,18 y 1,07) no superan al azar (1,19 y 1,13).
- **El crudo retiene menos** porque la tendencia común de las métricas concentra la variación en el primer componente (autovalor de 5,79, frente a 3,25 en el ajustado).
- **Canary retiene más** porque, con 1.824 releases, el umbral del azar es más bajo (1,20 para el primer componente, frente a 1,66 en la serie estable). Componentes más chicos pasan a distinguirse del ruido.

### 11.3 Componentes identificados

#### 11.3.1 Con las 9 variables a nivel producto

Con las 9 métricas a nivel producto, estables y ajustado, los **3 componentes explican el 63 % de la variación**:

[[pca cargas producto estable ajustado]]

1. **CP1 · Bugs reportados por usuarios (23 %):** CFDR (+0,99) y NUB (+0,99). Como las dos métricas son casi iguales, este componente es en la práctica su promedio.
2. **CP2 · Documentación (23 %):** CD (+0,87), README Completeness (+0,71) y DLOC (−0,86). Es el mismo patrón de las relaciones robustas de documentación: en los releases donde DLOC queda por encima de lo esperable, CD y README Completeness quedan por debajo. Hereda los mismos efectos de cambios de estructura del repositorio descritos en 7.2.
3. **CP3 · Issues (17 %):** MTTR (+0,76), NOI (−0,75) y LE (+0,47). En los releases donde las issues cerradas tardaron más en cerrarse, quedan menos issues abiertas. Una explicación posible es mecánica: cuando en un release se cierran muchas issues viejas, sube el tiempo medio de cierre y baja la cantidad de issues abiertas.

**ANMCC no queda representada:** los 3 componentes explican solo el 9 % de su variación (comunalidad 0,09). LE queda representada solo en parte (0,23).

[[pca puntajes producto estable ajustado]]

En los puntajes se ve que el componente de documentación (CP2) tiene un nivel alto entre mediados de 2023 y octubre de 2024 (promedio de 0,71) y cae de golpe a fines de 2024 (−0,30 desde entonces), en las mismas fechas que los cambios de estructura del repositorio descritos en 7.2. Bugs (CP1) e issues (CP3) oscilan alrededor de 0 sin etapas marcadas.

#### 11.3.2 Con las 17 variables

Con las 17 variables (196 releases), Horn retiene **5 componentes, que explican el 61 %**:

1. **Documentación (17 %):** CD (+0,81), README Completeness por colaborador (+0,73), README Completeness (+0,71) y DLOC (−0,78).
2. **Bugs (13 %):** CFDR y NUB (+0,94).
3. **Amplitud de los cambios y facilidad de aprendizaje (12 %):** LE por colaborador (+0,80), ANMCC por colaborador (+0,75), LE (+0,61) y ANMCC (+0,56). Con las versiones por colaborador, ANMCC sí forma un componente.
4. **Issues (9 %):** MTTR (+0,84), NOI (−0,60) y MTTR por colaborador (+0,49).
5. **Concentración de la documentación (9 %):** DLOC por colaborador, mediana (+0,83) y p90 (+0,55), frente al share del top 10 % (−0,64).

[[pca cargas todas estable ajustado]]

- Los componentes de las 9 métricas aparecen también acá: documentación, bugs e issues. Las versiones por colaborador se suman a ellos (README Completeness y MTTR por colaborador) o forman componentes nuevos.
- Los dos componentes nuevos son amplitud de los cambios y facilidad de aprendizaje (CP3), que incluye a ANMCC, y concentración de la documentación (CP5).
- CD por colaborador y MTTR por colaborador quedan poco representadas (comunalidad de 0,24 y 0,36).

[[pca puntajes todas estable ajustado]]

El componente de documentación (CP1) repite el patrón de las 9 métricas: alto entre mediados de 2023 y octubre de 2024 (0,68) y más bajo desde fines de 2024 (−0,28).

### 11.4 Solidez y consistencia de los resultados

**Bootstrap de bloques.** Para ver si los componentes dependen de unos pocos releases, se remuestrearon los datos 500 veces y se recalculó el PCA cada vez. Como los releases consecutivos se parecen entre sí, no se remuestrean de a uno sino en **bloques de releases consecutivos** (14 en la serie estable), que conservan esa dependencia. En cada remuestreo se compara cada componente con el original mediante la **congruencia de Tucker**, una medida de 0 a 1 de cuánto se parecen sus cargas: desde 0,95 se considera el mismo componente, entre 0,85 y 0,95 parecido, y por debajo de 0,85 distinto.

**Con las 9 variables a nivel producto:**

[[pca solidez producto estable ajustado]]

- **CP1 (bugs) y CP2 (documentación) son muy estables:** congruencia mediana de 0,97, y 0,91 y 0,89 aun en el 5 % de los peores remuestreos.
- **CP3 (issues) es estable en la mediana (0,96)**, pero en algunos remuestreos se mezcla con otro componente (0,28 en el 5 % de los peores). Es el menos firme de los tres.

**Con las 17 variables:**

[[pca solidez todas estable ajustado]]

- Documentación, bugs y amplitud de los cambios son estables (congruencia mediana de 0,95, 0,94 y 0,96).
- Issues (0,86) y concentración de la documentación (0,79) lo son menos, y en el 5 % de los peores remuestreos bajan a 0,50 y 0,33: son los componentes más débiles.

**Consistencia entre enfoques y series.** Cada solución se compara con la de referencia (estables, ajustado) mediante la congruencia de Tucker.

**Con las 9 variables a nivel producto:**

[[pca comparacion producto]]

- **Ajustado y sin tamaño dan los mismos componentes** (0,97 a 0,99): descontar la cantidad de personas activas no cambia nada. Los componentes no se explican por el tamaño del equipo.
- **Canary replica los tres componentes** en el enfoque ajustado (0,98, 0,95 y 0,91), con muchos más releases (2.223) y ventanas mucho más cortas. Con el control por tamaño, issues queda justo por debajo del umbral (0,83).
- **El crudo da otra cosa:** bugs se parece (0,90), documentación en parte (0,72) e issues no (0,14). En los datos crudos las métricas se parecen más entre sí (correlación media de 0,27 frente a 0,17 en el ajustado) porque casi todas cambian con los años, y el PCA las agrupa por cómo evolucionan en el tiempo, no por cómo se mueven de un release a otro. Por eso el crudo explica más variación (73 % con 3 componentes) y por eso el ajustado es el enfoque principal.

**Con las 17 variables:**

[[pca comparacion todas]]

- Con las 17 variables, ajustado y sin tamaño también coinciden (0,95 a 0,99). En canary se replican bien documentación (0,86) y bugs (0,94), pero no los otros tres (0,48 a 0,76). Canary retiene además 7 componentes: con más de 1.800 releases, el análisis paralelo detecta más estructura.

**Prueba sin CFDR y NUB.** Como CFDR y NUB forman un componente solas y son las que reducen la serie a 200 releases, se repitió el PCA de las otras 7 métricas (prueba hecha aparte, todavía no incluida en el script):

- Sobre los mismos 200 releases, Horn retiene 2 componentes, idénticos a documentación e issues (congruencia de 1,00).
- Sobre toda la historia (300 releases desde 2016), siguen siendo los mismos dos componentes (0,98 y 0,97), y en issues entra también ANMCC (−0,46).

Es decir, los componentes de documentación e issues no dependen de CFDR y NUB y se sostienen desde 2016.

### 11.5 Síntesis

- Producto se resume en **3 componentes: bugs reportados por usuarios, documentación e issues**, que explican el 63 % de la variación de las 9 métricas.
- Los tres superan al azar, son estables en el bootstrap (issues algo menos) y se repiten sin el efecto del tamaño y en los releases canary.
- Dependen del ajuste por tiempo: con los datos crudos aparecen otros agrupamientos, que reflejan el crecimiento del proyecto.
- El componente de documentación arrastra los problemas de medición de CD, DLOC y README Completeness (sección 10), así que antes de interpretarlo como calidad de la documentación conviene recalcular esas métricas.

El reporte interactivo del PCA, con todas las combinaciones de variables, series y enfoques, está en el anexo.
