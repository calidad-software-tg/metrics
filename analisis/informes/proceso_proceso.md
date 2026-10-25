---
cruce: Proceso-Proceso
titulo: Análisis de la dimensión Proceso · métricas corregidas
subtitulo: Correlaciones y componentes principales con las métricas recalculadas (branch ine/fixes-metricas) · next.js
---

El análisis Proceso–Proceso busca entender cómo se relacionan entre sí las métricas del proceso de desarrollo: cómo se reportan y se resuelven las issues, cuánto se discute y se revisa, y cómo se reparte el trabajo. Igual que en Persona y Producto, es un paso previo a cruzar Proceso con las otras dos dimensiones, y responde dos preguntas:

1. **¿Qué métricas de Proceso aportan información propia?** Varias se calculan a partir de los mismos eventos (por ejemplo, las issues que se abren y se cierran en cada release), así que es esperable que algunas midan prácticamente lo mismo. El objetivo es reducir la dimensión a un conjunto más chico de métricas principales para los cruces.
2. **¿Qué aspectos del proceso aparecen juntos?** Es decir, qué relaciones se mantienen una vez descontado el crecimiento del proyecto.

## 1. Variables medidas

Este análisis repite el de la dimensión Proceso con las métricas recalculadas después de corregir los problemas de medición del primer análisis (sección 3). Se evalúan **34 variables**: 12 a nivel proyecto, 18 por colaborador y 4 variantes de MTTR y NCI (27 en el análisis original). La columna "Estado" indica qué cambió en cada una.

| Variable | Nivel | Qué mide | Estado |
|---|---|---|---|
| ANMCC | proyecto | Promedio de archivos modificados por commit en la ventana | Corregida: sin commits de bots ni merges; nula sin commits |
| MTTR | proyecto | Horas promedio entre apertura y cierre de las issues cerradas en la ventana | Corregida: sin cierres de bots; nula si no se cerró ninguna issue |
| NCI | proyecto | Issues cerradas en la ventana | Corregida: sin cierres de bots |
| NOI | proyecto | Issues abiertas al cierre de la ventana | Corregida: sin issues abiertas por bots |
| Tasa de Éxito de Jarczyk | proyecto | Parte de las issues creadas en la ventana que se cerró antes del fin de la ventana | Corregida: sin issues de bots; las que cerró un bot cuentan como no resueltas |
| Process Performance | proyecto | Parte de las issues creadas en la ventana que se cerró en menos de tres días | Corregida: igual que Jarczyk |
| CFDR | proyecto | Issues de bug creadas en la ventana por alguien externo al equipo (top 10 de contribuidores) | Corregida: equipo calculado al cierre de cada ventana; sin issues de bots |
| NUB | proyecto | Issues de bug creadas en la ventana por quien no tiene rol formal en el repositorio | Corregida: etiquetas comparadas completas; sin issues de bots |
| DIS (Doc Issue Survival) | proyecto | Cuánto tardan en cerrarse las issues de documentación cerradas en la ventana | Corregida: etiquetas comparadas completas; sin cierres de bots; nula si no se cerró ninguna |
| README Completeness | proyecto | Proporción de las 7 categorías de Prana et al. que cubre el README | Corregida: solo el README de la raíz |
| NOB | proyecto | Branches del repositorio principal con un PR abierto al cierre de la ventana | Corregida: antes era constante (las 2.706 branches de hoy) |
| Wiki Presence | proyecto | 1 si el repositorio tenía wiki en ese momento | **Nueva en Proceso.** Antes era constante; ahora sale del historial de la wiki |
| MTTR con bots, NCI con bots | proyecto | MTTR y NCI con los cierres de bots, como en la versión original | Variantes (control) |
| MTTR (mediana de issues), MTTR de bugs | proyecto | MTTR con la mediana en vez del promedio, y solo de las issues de bug | Variantes (control) |
| ANMCC (mediana) | por colaborador | Mediana entre colaboradores de sus archivos por commit | Corregida: sin bots ni merges |
| Contribution Diversity (mediana, p90, share top 10%) | por colaborador | Archivos distintos que toca cada persona en la ventana | Mismo cálculo, sobre las ventanas nuevas |
| Development Experience (mediana) | por colaborador | Experiencia de cada persona en el proyecto, en meses | Mismo cálculo, sobre las ventanas nuevas |
| DIS (mediana) | por colaborador | DIS de las issues de documentación que cierra cada persona | Corregida: igual que DIS |
| EXPRev (p90, share top 10%) | por colaborador | Acciones de revisión de cada persona en issues y pull requests | Mismo cálculo, sobre las ventanas nuevas |
| REXPRev (mediana) | por colaborador | Acciones de revisión recientes de cada persona | Mismo cálculo, sobre las ventanas nuevas |
| MTTR (mediana) | por colaborador | Mediana entre quienes cierran issues de su MTTR | Corregida: sin bots ni autocierres (quien cierra su propia issue) |
| NC (p90, share top 10%) | por colaborador | Comentarios que escribe cada persona | Mismo cálculo, sobre las ventanas nuevas |
| NCI (p90, share top 10%) | por colaborador | Issues que cierra cada persona | Corregida: sin bots |
| README Completeness (mediana) | por colaborador | Completitud del README según su último autor | Corregida: solo el README de la raíz |
| SC (mediana, p90, share top 10%) | por colaborador | Issues y pull requests que abre cada persona, más los que ella misma cerró o mergeó en la ventana | Corregida: usa la fecha real de cierre o merge |

Las cuatro variantes sirven para comparar con la versión principal: en las correlaciones sus pares con MTTR o NCI son de **control**, y no entran al PCA.

**Métricas de la planilla que no entran:**

- **Schedule Compliance** tiene valor en solo 15 releases: next.js usó milestones con fecha límite durante un período corto.
- **ROSI** está marcada como no calculable: mide la rentabilidad de las inversiones en seguridad, y el repositorio no tiene datos de costos.
- Las **medianas de EXPRev, NC y NCI** toman el mismo valor en más del 80 % de los releases (el colaborador típico escribe un solo comentario o cierra una sola issue). La mediana de SC, que antes también se descartaba, ahora varía lo suficiente y entra.

**Wiki Presence ahora entra en Proceso.** La planilla la asigna a Producto y a Proceso (registro 16, Documentation Quality), pero en la corrida anterior el análisis la tenía solo en Producto. NCI, en cambio, queda solo en Proceso, como en la planilla combinada y en las fichas 35, 40 y 43.

Varias métricas también pertenecen a Producto (ANMCC, MTTR, README Completeness, Wiki Presence, CFDR, NUB, NOI, NOB) o a Persona (Contribution Diversity, EXPRev, REXPRev, NC, SC, Development Experience).

## 2. Ventanas de análisis

Cada ventana va desde un release hasta el siguiente. Las métricas se calcularon sobre dos series:

| | Estables · antes | Estables · ahora | Canary · antes | Canary · ahora |
|---|---|---|---|---|
| Ventanas | 371 | **271** | 3.858 | **3.785** |
| Duración mediana | 5,6 días | **8,2 días** | 0,56 días | 0,58 días |
| Ventanas de menos de un día | 89 | **1** | — | — |
| Backports | 60 | **0** | incluidos | **0** |

- **Serie estable:** releases marcados como estables, **sin backports** ni los cuatro releases mal etiquetados como estables, y **uniendo las ventanas de menos de un día con la anterior**. La única ventana de menos de un día que queda es la última, que termina en la fecha de corte.
- **Serie canary:** todos los releases, sin backports y sin unir ventanas cortas. Sirve para replicar las relaciones con muchas ventanas angostas.
- **Fecha de corte común:** 1 de octubre de 2026, igual para las tres dimensiones.
- **Datos faltantes:** cada par usa solo las ventanas donde las dos variables tienen dato. CFDR y NUB tienen 190 ventanas (desde mediados de 2019, cuando next.js empieza a etiquetar bugs), DIS 132 (desde 2022) y Development Experience 210. Las demás tienen dato en casi todas.

## 3. Preprocessing: correcciones en el cálculo de las métricas

En el primer análisis varias relaciones resultaron ser efectos de cómo se medían los datos. Las correcciones que afectan a Proceso:

| Corrección | Problema que tenía | Sesgo que resuelve |
|---|---|---|
| Sin backports | La serie estable intercalaba parches de versiones anteriores con la línea principal | Ventanas que mezclaban dos códigos distintos |
| Ventanas de menos de un día unidas | 89 ventanas duraban minutos u horas y casi no tenían actividad | Correlaciones armadas por ventanas vacías (ej. ANMCC ↔ MTTR, que pasa de +0,42 a +0,08) |
| Nulo cuando no hay datos | MTTR, ANMCC y DIS valían 0 cuando no había nada que medir | Ceros falsos que se leían como "reparación instantánea" |
| Bots fuera a nivel proyecto | El bot de issues inactivas cerraba issues viejas (el 68 % de los cierres de 2025) | MTTR, NCI, Jarczyk y Process Performance inflados por cierres automáticos |
| MTTR por persona sin autocierres | Contaba las issues que la propia persona abrió y cerró | MTTR por colaborador dependía de quién cierra |
| DIS y NUB con etiquetas completas | Buscaban etiquetas por subcadena (ej. "doc" dentro de otra etiqueta) | Issues contadas como documentación o como bug sin serlo |
| CFDR con el equipo de cada ventana | Aplicaba el top 10 de contribuidores de hoy a toda la historia | Personas que entraron al equipo después contadas como equipo |
| SC con la fecha real de cierre | Tomaba el estado de hoy de cada issue o pull request | Cierres posteriores a la ventana contados dentro de ella |
| README Completeness solo de la raíz | Promediaba todos los README del árbol, casi todos de ejemplos | Cambios por agregar o borrar ejemplos |
| NOB y Wiki Presence por ventana | Eran constantes (las branches y el estado de la wiki de hoy) | No se podían analizar |

El efecto del bot se ve en las series. Sin sus cierres, NCI baja a menos de la mitad en 2025–26 (mediana de 42 a 18,5 issues por release):

[[comparar serie nci_producto]]

Y MTTR deja de dispararse en 2025, cuando el bot cerraba issues de meses o años (mediana de unas 7.300 a unas 2.500 horas):

[[comparar serie mttr_producto]]

## 4. Análisis de correlaciones

Se usa la misma correlación corregida que en el primer análisis y en las otras dimensiones: Spearman parcial que descuenta el momento del proyecto (curva suave) y la duración de la ventana, con la "n efectiva" por la dependencia entre releases consecutivos, corrección por comparaciones múltiples (Benjamini–Hochberg, dentro del cruce) y los mismos criterios de estabilidad, réplica en canary y control por tamaño. Con la corrección de Inés del 23/10, una variable constante dentro de un período ya no da correlación en ese período (antes daba ±1).

### 4.1 Resumen

[[grafico kpis]]

Los indicadores incluyen los pares con variantes de MTTR y NCI. Esos 112 pares se usan solo para comparar con la versión principal (por ejemplo, para medir cuánto de una relación se debe a los bots), así que el texto da los conteos **sin variantes**:

| | Antes | Ahora | Ahora, sin variantes |
|---|---|---|---|
| Variables | 27 | 34 | 30 |
| Pares | 351 | 561 | — |
| Pares de control | 27 | 45 | — |
| Pares evaluados | 324 | 516 | **404** |
| Con relación positiva | 55 | 77 | **51** |
| Con relación negativa | 20 | 29 | **22** |
| Robustas | 35 | 67 | **44** |
| Hallazgos candidatos | 21 | 46 | **25** |
| **Robustas originales que se mantienen** | — | **24 de 35** | |

De los 404 pares evaluados, 195 son no concluyentes y 136 no tienen relación: igual que antes, en cuatro de cada cinco pares no hay evidencia de relación.

[[grafico categorias]]

**Del total de pares a los hallazgos:**

| Paso | Pares (sin variantes) |
|---|---|
| Pares evaluados | 404 |
| Con relación significativa | 73 |
| Robustas: estables en el tiempo y se repiten en canary | 44 |
| Se mantienen al descontar la cantidad de personas activas | 37 |
| Sin solapamiento de definición | 32 |
| Entre métricas de distinta familia | **25** |

- **Cantidad de personas activas:** dejan de ser robustas las relaciones de CFDR y NUB con NCI, con ANMCC (mediana) y con Contribution Diversity (mediana), y Contribution Diversity ↔ NCI. En los releases con más gente se reportan más bugs, se cierran más issues y las medianas por colaborador bajan, sin que una cosa tenga que ver con la otra.
- **Solapamiento de definición:** 5 pares entre ANMCC y Contribution Diversity, que cuentan los dos archivos modificados.
- **Misma familia:** 7 pares entre NC, SC, EXPRev, REXPRev y NCI por colaborador, que miden la participación en discusiones.

El embudo del gráfico incluye las variantes (516 pares evaluados y 46 al final):

[[grafico embudo]]

**Wiki Presence no cambia el resultado.** Suma 33 pares: ninguno es robusto. Solo dos son significativos, con README Completeness y su mediana (+0,71), y no existen dentro de ningún período: las dos métricas son escalones (Wiki Presence vale 1 hasta enero de 2020 y 0 después) y la correlación sale de comparar los primeros años con el resto. Los 528 pares que ya existían dan exactamente los mismos resultados.

### 4.2 Mapa de calor

[[grafico mapa]]

Azul: negativa; naranja: positiva; gris: cerca de 0. El mapa del análisis original:

[[antes mapa]]

- **Hay más relaciones moderadas que antes:** 25 pares significativos con |ρ| ≥ 0,3 (sin variantes), contra 17 en el análisis original, con una cantidad parecida de significativos (73 y 75). Las correcciones sacaron ruido (ventanas vacías, cierres de bots) que debilitaba relaciones release a release.
- **Desaparecen las que armaban las ventanas vacías y los bots:** ANMCC ↔ MTTR pasa de +0,42 a +0,08, porque en las ventanas de minutos las dos valían 0 a la vez; CFDR y NUB ↔ MTTR (mediana) pasan de −0,22 a −0,06.
- **Las relaciones con README Completeness se debilitan** (por ejemplo, con NC share del top 10 %, de +0,18 a −0,09): ahora mide solo el README principal, que casi no cambia.

### 4.3 Correlación cruda frente a corregida

[[grafico cruda_corregida]]

### 4.4 Métricas que miden lo mismo

Para la primera pregunta se buscan pares de métricas distintas que se mueven prácticamente igual (correlación corregida mayor a 0,7). Hay tres:

- **CFDR y NUB (+1,00).** Las dos cuentan los bugs reportados por personas externas al equipo; solo cambia cómo se define el equipo.
- **Tasa de Éxito de Jarczyk y Process Performance (+0,83).** Las dos se calculan sobre las issues creadas en la ventana: Jarczyk mide qué parte se cerró antes del fin de la ventana, y Process Performance qué parte se cerró en menos de tres días, que es un subconjunto de la anterior.
- **ANMCC y Contribution Diversity (+0,84, en la mediana por colaborador).** Las dos cuentan archivos modificados. Es el mismo caso que en Persona.

EXPRev y NC también se mueven casi igual (0,72 en el p90 y 0,94 en el share del top 10 %), pero se tratan como pares de control: EXPRev suma las acciones de cada persona en issues y pull requests, que son mayormente comentarios.

**README Completeness y Wiki Presence casi no varían.** README mide solo el README principal y en 271 releases cambia de valor 7 veces (0,71, 0,86 o 1,0). Wiki Presence vale 1 hasta enero de 2020 y 0 después. Son escalones en el tiempo, así que no sirven para buscar relaciones release a release: se mantienen en la lista, pero sus relaciones no se interpretan.

Con este criterio, la dimensión Proceso queda reducida a **once métricas principales**:

| Aspecto | Métrica principal | Qué describe del release |
|---|---|---|
| Bugs reportados por usuarios | CFDR | Cuántos bugs reportan personas externas al equipo |
| Volumen de cierre | NCI | Cuántas issues se cerraron (sin bots) |
| Resolución de lo nuevo | Tasa de Éxito de Jarczyk | Qué parte de las issues creadas se cerró dentro del mismo release |
| Antigüedad de lo cerrado | MTTR | Cuánto tiempo estuvieron abiertas las issues que se cerraron (sin bots) |
| Backlog | NOI | Cuántas issues quedan abiertas |
| Ramas activas | NOB | Cuántas branches tienen un pull request abierto |
| Documentación (issues) | DIS | Cuánto tardan en cerrarse las issues de documentación |
| Documentación (README y wiki) | README Completeness | Qué tan completo está el README principal (casi constante; Wiki Presence, también escalón, no suma información) |
| Reparto del trabajo | Contribution Diversity (mediana) | Cuántos archivos distintos toca el colaborador típico |
| Discusión | NC (share del top 10 %) | Si unos pocos escriben la mayoría de los comentarios |
| Participación | SC (mediana) | Cuántas issues y pull requests abre y cierra el colaborador típico |

### 4.5 Relaciones robustas

Las 46 relaciones que pasan todos los filtros (25 sin variantes). Al hacer clic en una fila, su análisis particular se muestra en 4.6.

[[explorador hallazgos tabla]]

**Qué pasó con las robustas del análisis original:** se mantienen 24 de las 35.

| Relación | Antes | Ahora | Por qué cambió |
|---|---|---|---|
| CFDR ↔ NUB, Jarczyk ↔ Process Performance, ANMCC ↔ Contribution Diversity | +0,76 a +1,00 robustas | +0,83 a +1,00 robustas | Se mantienen: miden lo mismo (4.4) |
| NCI ↔ MTTR | +0,41 robusta | +0,29 robusta | Se mantiene, más débil: parte la armaban los cierres del bot |
| NCI ↔ Jarczyk | +0,29 robusta | +0,39 robusta | Se fortalece: es el núcleo del Patrón 1 |
| CFDR y NUB ↔ MTTR (mediana) | −0,22 robustas | −0,06, no concluyente | Se pierde el Patrón 2 anterior: lo armaban los cierres de bots y los autocierres |
| EXPRev (p90) ↔ MTTR, MTTR (mediana) ↔ NCI (p90) | +0,21 y +0,16 robustas | +0,02 y +0,06, sin relación | Las armaban los cierres de bots |
| DIS y DIS (mediana) ↔ MTTR (mediana) | +0,38 y +0,41 robustas | +0,32 y +0,27, no robustas | Siguen positivas, pero ya no en todos los períodos; DIS ahora compara etiquetas exactas |
| NC (share del top 10 %) ↔ README Completeness | +0,18 robusta | −0,09 | README ahora mide solo el README principal |
| Otras cuatro débiles (por ejemplo, NC p90 ↔ SC p90) | −0,20 a +0,36 robustas | −0,18 a +0,30, no robustas | Ya no pasan alguno de los filtros de estabilidad o réplica |

### 4.6 Análisis particular

[[explorador hallazgos detalle]]

Al revisar las 25 relaciones, varias no son un hallazgo:

- **Miden lo mismo:** CFDR ↔ NUB y Jarczyk ↔ Process Performance (4.4).
- **Evidencia baja:** CFDR / NUB ↔ REXPRev, CFDR / NUB ↔ EXPRev (p90), DIS ↔ REXPRev y ANMCC ↔ Development Experience (medianas). No se repiten en canary (entre −0,07 y +0,09) y no existen en ningún período por separado. En las de CFDR, además, el control por tamaño las deja casi en el límite: reflejan que en los releases con más gente hay más bugs y medianas por colaborador más bajas.
- **No se repiten en canary:** Contribution Diversity (p90) ↔ SC (share del top 10 %) (+0,47 en estables y +0,04 en canary) y NC (share del top 10 %) ↔ SC (mediana) (+0,31 y +0,13).
- **Ya están en Persona:** Contribution Diversity (p90) ↔ SC (p90), entre dos variables por colaborador, solo en 2023–2024.

Las relaciones restantes forman tres patrones.

#### Patrón 1: resolver lo nuevo y limpiar lo viejo son actividades distintas

[[par jarczyk_success_rate_producto nci_producto: periodos, dispersion]]

En los releases donde se cierran más issues que lo esperable para ese momento del proyecto:

- se resuelve una parte mayor de las issues **nuevas** (NCI ↔ Jarczyk: +0,39; NCI ↔ Process Performance: +0,28), y
- las issues cerradas llevaban **más tiempo abiertas** (NCI ↔ MTTR: +0,29).

Pero **resolver lo nuevo y cerrar lo viejo no van juntos**: Jarczyk ↔ MTTR es −0,12, sin relación en ningún período. Un release con muchos cierres puede ser uno que atendió lo que acababa de entrar o uno que limpió lo acumulado.

| Par | Corregida | 2016–19 | 2020–22 | 2023–24 | 2025–26 | Canary | Sin tamaño |
|---|---|---|---|---|---|---|---|
| NCI ↔ Jarczyk | +0,39 | +0,56 | +0,34 | +0,61 | +0,32 | +0,44 | +0,40 |
| NCI ↔ MTTR | +0,29 | +0,50 | +0,30 | +0,21 | +0,58 | +0,35 | +0,35 |
| Jarczyk ↔ MTTR | −0,12 | +0,10 | +0,04 | +0,01 | −0,14 | −0,16 | −0,12 |

[[nota jarczyk_success_rate_producto nci_producto; mttr_producto nci_producto; nci_producto process_performance_producto]]
**Qué muestran los datos:** las tres relaciones son positivas en los cuatro períodos, se repiten en canary y el control por tamaño las deja igual o más fuertes. Una parte es mecánica: NCI cuenta todos los cierres, así que las issues que se crean y se cierran en el mismo release suman en NCI y en Jarczyk, y las viejas que se cierran suben MTTR. Lo que no es mecánico es que Jarczyk y MTTR no se relacionen entre sí (−0,12): el volumen de cierre mezcla dos actividades distintas. El PCA llega a lo mismo por otro camino (sección 5).
[[/nota]]

**Los bots.** En el análisis original este patrón incluía una tercera parte: en esos releases quedaban menos issues abiertas. Con la corrección se ve que esa parte la causaba el bot que cierra issues inactivas:

| Par | Con bots | Sin bots |
|---|---|---|
| MTTR ↔ NCI | +0,42 | +0,29 |
| MTTR ↔ NOI | −0,34 | +0,01 |

[[nota mttr_con_bots_producto noi_producto]]
**Qué muestran los datos:** con los cierres del bot, MTTR ↔ NOI es −0,34 en toda la historia; sin ellos, +0,01. El bot cierra de golpe las issues más viejas, así que en los releases donde actúa sube MTTR y bajan las issues abiertas a la vez. Dentro de cada período, en cambio, las dos versiones dan valores parecidos y débiles (sin bots, entre −0,09 y −0,26), así que no se puede decir que la relación desaparezca del todo: lo que se pierde es el efecto de las limpiezas grandes del bot. Es el mismo caso que en Producto.
[[/nota]]

#### Patrón 2: la documentación no tiene un ritmo propio

[[par dis_producto mttr_p50_producto: periodos, dispersion]]

En los releases donde las issues en general tardan más en cerrarse, las de documentación también:

| Par | Corregida | 2020–22 | 2023–24 | 2025–26 | Canary |
|---|---|---|---|---|---|
| DIS ↔ MTTR (mediana de las issues) | +0,44 | +0,27 | +0,31 | +0,49 | +0,51 |
| DIS (mediana) ↔ MTTR (mediana de las issues) | +0,41 | +0,20 | +0,29 | +0,41 | +0,51 |
| DIS ↔ NCI | +0,29 | +0,37 | +0,27 | +0,37 | +0,18 |
| DIS (mediana) ↔ Jarczyk | −0,27 | −0,01 | −0,32 | −0,20 | −0,31 |

[[nota dis_producto mttr_p50_producto; dis_producto nci_producto]]
**Qué muestran los datos:** el proyecto no trata la documentación aparte: ni la prioriza ni la posterga. En parte es esperable, porque las issues de documentación también cuentan en el tiempo de cierre general. DIS tiene dato solo desde 2022 (132 releases), así que el patrón describe la etapa reciente, y se fortalece en 2025–26.
[[/nota]]

#### Patrón 3 (en verificación): más participación del colaborador típico, más resolución de lo nuevo

[[par jarczyk_success_rate_producto sc_mediana: periodos, dispersion]]

| Par | Corregida | 2016–19 | 2020–22 | 2023–24 | 2025–26 | Canary | Sin tamaño |
|---|---|---|---|---|---|---|---|
| SC (mediana) ↔ Jarczyk | +0,33 | +0,20 | +0,56 | +0,56 | +0,16 | +0,30 | +0,35 |
| EXPRev (p90) ↔ Process Performance | +0,22 | +0,37 | +0,27 | +0,11 | +0,18 | +0,03 | +0,22 |
| EXPRev (p90) ↔ Jarczyk | +0,18 | +0,24 | +0,32 | +0,11 | +0,08 | +0,10 | +0,20 |

[[nota jarczyk_success_rate_producto sc_mediana]]
**Qué muestran los datos:** en los releases donde el colaborador típico participa más, se resuelve una parte mayor de las issues nuevas. Es positiva en los cuatro períodos, se repite en canary y no depende de cuánta gente participa. Las de EXPRev van en la misma dirección pero son débiles y no se repiten bien en canary.

**Falta verificar cuánto pesa una superposición:** SC cuenta las issues que una persona abre y además cierra ella misma en la ventana, y esas issues también suman en Jarczyk. Hasta medirlo, el patrón se presenta como tentativo.
[[/nota]]

#### Lo que no se mantiene

- **Patrón 2 anterior (CFDR ↔ MTTR mediana por colaborador):** pasa de −0,22 a −0,06. Queda una versión débil con la mediana de las issues del proyecto (−0,23), solo desde 2025 y más débil en canary (−0,14). No se interpreta como patrón.
- **MTTR (mediana de las issues) ↔ Jarczyk (−0,38) y ↔ Process Performance (−0,35):** en parte se dan por definición: si muchas issues nuevas se cierran rápido, la mediana del tiempo de cierre baja sola.
- **Relaciones débiles sueltas:** EXPRev (share del top 10 %) ↔ MTTR (+0,20), MTTR por colaborador ↔ NCI (+0,18, desde 2025) y ↔ Process Performance (−0,18). No forman un patrón.

### 4.7 Relaciones significativas

[[explorador significativas tabla | direccion]]

[[grafico forest]]

**Estabilidad de las relaciones significativas por período:**

[[grafico estabilidad]]

- **El Patrón 1** está presente en todos los períodos. NCI ↔ MTTR es más fuerte en 2016–19 (+0,50) y en 2025–26 (+0,58); NCI ↔ Jarczyk, en 2016–19 (+0,56) y 2023–24 (+0,61).
- **El Patrón 2** solo se puede evaluar desde 2022 y se fortalece en 2025–26.
- **El Patrón 3** es más fuerte en 2020–2024 (+0,56) y más débil en los extremos.
- **Las relaciones de Wiki Presence con README Completeness** no tienen barras por período: dentro de cada período Wiki Presence es constante.

[[explorador significativas detalle]]

## 5. Componentes principales

Se usó el mismo método que en Producto: rangos estandarizados, enfoque ajustado por tiempo y duración como principal, análisis paralelo de Horn para elegir cuántos componentes, rotación varimax y bootstrap de bloques. Las variantes de MTTR y NCI no entran, y DIS queda afuera porque tiene valor en menos de la mitad de los releases. Con las **11 métricas a nivel proyecto** se usan **185 releases estables**, desde mediados de 2019, cuando empiezan CFDR y NUB.

### 5.1 Cuántos componentes se retienen

[[pca screes producto+todas estable ajustado]]

[[pca criterios producto]]

- Con las 11 variables a nivel proyecto, Horn retiene **5 componentes**, que explican el **76 %** de la variación (antes 3 componentes y 67 % con 9 variables). Los cinco primeros autovalores (2,52, 1,76, 1,58, 1,27 y 1,21) superan lo que da el azar (1,54, 1,37, 1,26, 1,18 y 1,10); el sexto (0,84) queda por debajo (1,03).
- Con las 28 variables (sumando las versiones por colaborador, 139 releases), retiene 7 y explican el 66 %.

### 5.2 Componentes identificados

[[pca cargas producto estable ajustado]]

1. **CP1 · Bugs de usuarios (20 %):** CFDR y NUB (+0,98). Es el mismo componente del análisis original y el mismo que en Producto.
2. **CP2 · Resolución de lo nuevo (18 %):** Jarczyk (+0,93) y Process Performance (+0,92), con NCI en parte (+0,34).
3. **CP3 · README y backlog (13 %):** NOI (+0,80) y README Completeness (+0,65), con ANMCC en contra (−0,61). No se interpreta como patrón: README es casi un escalón y de a pares su relación con NOI es débil (+0,18). Producto encuentra el mismo agrupamiento.
4. **CP4 · Wiki y branches (13 %):** Wiki Presence (+0,76), NOB (+0,73) y README Completeness (+0,53). **No se interpreta:** lo arma el escalón de Wiki Presence. En los 185 releases del PCA, Wiki Presence vale 1 en uno solo, el primero (v9.0.0), y ese release tiene un puntaje de 9,8 en este componente contra menos de 2,1 en todos los demás. Es el componente menos estable en el bootstrap (0,51 en el 5 % de los peores remuestreos). Es el mismo caso que el componente "Wiki y documentación temprana" de Producto.
5. **CP5 · Cierre de lo viejo (12 %):** MTTR (+0,85) y NCI (+0,74). Es el Patrón 1.

NCI carga en CP2 y en CP5 a la vez: el volumen de cierre se reparte entre resolver lo nuevo y cerrar lo viejo, que son componentes separados. Sin Wiki Presence, el PCA da 4 componentes iguales a CP1, CP2, CP3 y CP5: sumarla agrega un componente pero no cambia los demás.

**Cambio respecto del análisis original:**

[[pca_antes cargas producto estable ajustado]]

| Antes | Ahora | Congruencia |
|---|---|---|
| CP1 · Bugs: CFDR y NUB | CP1 · Bugs: CFDR y NUB | 0,96 (el mismo) |
| CP2 · Resolución: Jarczyk, Process Performance y NCI | CP2 · Resolución de lo nuevo | 0,89 (parecido) |
| CP3 · Limpieza del backlog: MTTR (+0,82), NOI (−0,66), NCI (+0,62), README (−0,45) | CP5 · Cierre de lo viejo: MTTR y NCI | 0,78 (distinto) |
| — | CP3 · README y backlog | nuevo, no se interpreta |
| — | CP4 · Wiki y branches | nuevo, no se interpreta |

- **La "limpieza del backlog" pasa a ser "cierre de lo viejo":** NOI salía con signo contrario porque el bot cerraba issues viejas y bajaba el backlog en el mismo release. Sin sus cierres, NOI deja ese componente.
- **El componente de resolución de lo nuevo se mantiene,** y NCI pasa a repartirse entre resolución y cierre de lo viejo.
- **Los dos componentes nuevos los arman escalones** (README y Wiki Presence), que entran ahora porque antes eran constantes o se medían de otra forma.

[[pca puntajes producto estable ajustado]]

### 5.3 Solidez y consistencia

[[pca solidez producto estable ajustado]]

- Bugs (0,96) y resolución de lo nuevo (0,98) son muy estables en el bootstrap, y cierre de lo viejo (0,95, con 0,80 en el 5 % de los peores remuestreos) también. README y backlog (0,89) y Wiki y branches (0,88, con 0,51 en el peor 5 %) lo son menos.

[[pca comparacion producto]]

- **Canary repite los cinco componentes** (0,97, 0,99, 0,96, 0,97 y 0,97).
- **Sin el efecto del tamaño**, Horn retiene 4, y los cinco componentes de referencia se reconocen (0,92 a 1,00).
- **El crudo da solo 2 componentes**, que reflejan cómo crecieron las métricas con los años y no cómo se mueven de un release a otro.

### 5.4 Con las 28 variables

[[pca cargas todas estable ajustado]]

Aparecen siete grupos: concentración de la participación (EXPRev, NC y SC share del top 10 %, SC p90), bugs (con EXPRev, NC y REXPRev en contra, el efecto de tamaño de la sección 4.1), cierre de lo viejo (MTTR, NCI y sus versiones por colaborador), resolución de lo nuevo (con SC mediana, como en el Patrón 3), amplitud de los cambios (ANMCC y Contribution Diversity por colaborador), README y wiki (README Completeness y su mediana, Wiki Presence y NOB), y ANMCC con NOI en contra. Son menos estables (congruencia mediana entre 0,78 y 0,95). Para los cruces conviene usar los componentes de las 11 métricas a nivel proyecto, sin interpretar los dos de escalones.

## 6. Advertencias sobre los datos de Proceso

- **README Completeness y Wiki Presence son escalones** (4.4). Sus relaciones y los dos componentes que arman en el PCA (README y backlog, Wiki y branches) no se interpretan.
- **DIS tiene datos solo desde 2022,** y CFDR y NUB desde mediados de 2019.
- **SC incluye los cierres propios** de cada persona, que también cuentan en Jarczyk: el Patrón 3 está en verificación.
- **Rol del autor en NUB.** NUB decide quién es del equipo con el rol que GitHub informa hoy, no el que tenía la persona cuando abrió la issue. CFDR sí usa el top 10 de contribuidores hasta el cierre de cada ventana.
- **Clasificación de cuentas.** `kodiakhq` está clasificado como humano. Sus cierres a nivel proyecto son pull requests mergeados, así que no afecta a NCI ni a MTTR, pero conviene revisarlo.
- **Métricas compartidas con Producto** (CFDR, NUB, MTTR, NOI, NOB, README Completeness, Wiki Presence y ANMCC): antes de cruzar Proceso con Producto hay que acordar en cuál de las dos cuenta cada una.

## 7. Síntesis

- **El proceso de next.js tiene tres aspectos independientes:** los bugs que reportan los usuarios, la resolución de lo que entra y la limpieza de lo acumulado. Salen como componentes separados del PCA, se repiten en canary, y ninguno predice a los otros. Ninguna métrica sola alcanza para describir el proceso.
- **Las métricas se reducen a once.** CFDR y NUB, y Jarczyk y Process Performance, miden prácticamente lo mismo, y README Completeness y Wiki Presence casi no varían.
- **El hallazgo más firme es que cerrar muchas issues puede significar dos cosas distintas:** atender lo nuevo o limpiar lo viejo, que casi nunca pasan en el mismo release. Para la calidad, "issues cerradas" no sirve como indicador único.
- **La cantidad de bugs no depende de la velocidad del equipo.** La relación entre bugs y tiempo de resolución del análisis original desaparece con las correcciones. Lo mismo la "limpieza del backlog": la armaba el bot de issues inactivas.
- **Las demás relaciones son débiles:** la documentación sigue el ritmo general del proyecto, y la participación del colaborador típico va con más resolución de lo nuevo (en verificación).
- **Las correcciones son un resultado en sí mismo:** sin filtrar bots, backports y ventanas vacías, varias de las relaciones del análisis original se habrían leído como patrones del proceso.

El análisis original está en analisis/salidas_originales/reportes/.
