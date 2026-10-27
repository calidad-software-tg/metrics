---
cruce: Producto-Producto
titulo: Análisis de la dimensión Producto · métricas corregidas
subtitulo: Correlaciones y componentes principales con las métricas recalculadas (branch ine/fixes-metricas) · next.js
publicados: reporte_producto_producto.html=https://claude.ai/artifact/57wgT493HAcQjLyfdrmepB, reporte_pca_producto.html=https://claude.ai/artifact/RXqMmXecJzVjEmCCMP9LAp
---

## 1. Variables medidas

Este análisis repite el de la dimensión Producto con las métricas recalculadas después de corregir los problemas de medición que aparecieron en el primer análisis (sección 3). Se evalúan **24 variables**: 16 a nivel producto y 8 por colaborador (17 en el análisis original). La columna "Estado" indica qué cambió en cada una.

| Variable | Nivel | Qué mide | Estado |
|---|---|---|---|
| ANMCC | producto | Promedio de archivos modificados por commit en la ventana | Corregida: sin commits de bots ni merges; nula sin commits |
| CD (Comment Density) | producto | Líneas de comentario dividido líneas de código, al cierre de la ventana | Corregida: sin código de terceros compilado ni vendorizado |
| CFDR | producto | Issues de bug creadas en la ventana por alguien externo al equipo (top 10 de contribuidores) | Corregida: equipo calculado al cierre de cada ventana; sin issues de bots |
| NUB | producto | Issues de bug creadas en la ventana por quien no tiene rol formal en el repositorio | Corregida: etiquetas comparadas completas; sin issues de bots |
| DLOC | producto | Líneas de documentación del repositorio al cierre de la ventana | Corregida: cuenta `.mdx`; sin `examples/`, tests ni código compilado |
| Learning Easy (LE) | producto | Días entre la primera contribución de una persona a un componente y su última en la ventana | Mismo cálculo, sobre las ventanas nuevas |
| MTTR | producto | Horas promedio entre apertura y cierre de las issues cerradas en la ventana | Corregida: sin cierres de bots; nula si no se cerró ninguna issue |
| NOI | producto | Issues abiertas al cierre de la ventana | Corregida: sin issues abiertas por bots |
| README Completeness | producto | Proporción de las 7 categorías de Prana et al. que cubre el README | Corregida: solo el README de la raíz (siguiendo el enlace simbólico) |
| Wiki Presence | producto | 1 si el repositorio tenía wiki en ese momento | Corregida: antes era constante; ahora sale del historial de la wiki |
| NOB | producto | Branches del repositorio principal con un PR abierto al cierre de la ventana | Corregida: antes era constante (las 2.706 branches de hoy) |
| DLOC 2.0 | producto | Líneas de documentación agregadas o eliminadas en la ventana (DLOC por ventana, en lugar del total acumulado) | Nueva |
| Commits que tocan doc | producto | Proporción de commits de la ventana que modifican documentación | Nueva |
| MTTR (mediana de issues) | producto | MTTR con la mediana de las issues en vez del promedio | Variante de MTTR (control) |
| MTTR de bugs | producto | MTTR solo de las issues clasificadas como bug | Variante de MTTR (control) |
| MTTR con bots | producto | MTTR con los cierres de bots, como en la versión original | Variante de MTTR (control) |
| ANMCC (mediana) | por colaborador | Mediana entre colaboradores de sus archivos por commit | Corregida: sin bots ni merges |
| CD (mediana) | por colaborador | Mediana entre colaboradores de la densidad de comentarios de sus archivos | Corregida: mismos filtros que CD; sin archivos cuyo último autor es un bot |
| DLOC (mediana), DLOC (p90), DLOC (share top 10%) | por colaborador | Líneas de documentación de las que cada persona es la última autora | Corregidas: mismos filtros que DLOC; sin bots |
| Learning Easy (mediana) | por colaborador | Mediana entre colaboradores de LE | Mismo cálculo, sobre las ventanas nuevas |
| MTTR (mediana) | por colaborador | Mediana entre quienes cierran issues de su MTTR | Corregida: sin bots ni autocierres (quien cierra su propia issue) |
| README Completeness (mediana) | por colaborador | Completitud del README según su último autor | Corregida: solo el README de la raíz |

Las tres variantes de MTTR sirven para comparar con la versión principal: en las correlaciones sus pares con MTTR son de **control** y no entran al PCA, porque son la misma métrica calculada de otra forma.

## 2. Ventanas de análisis

Cada ventana va desde un release hasta el siguiente. Las métricas se calcularon sobre dos series:

| | Estables · antes | Estables · ahora | Canary · antes | Canary · ahora |
|---|---|---|---|---|
| Ventanas | 371 | **271** | 3.858 | **3.785** |
| Duración mediana | 5,6 días | **8,2 días** | 0,56 días | 0,58 días |
| Ventanas de menos de un día | 89 | **1** | — | — |
| Backports | 60 | **0** | incluidos | **0** |

- **Serie estable:** releases marcados como estables en GitHub, **sin backports** (parches de una versión mayor anterior), sin los cuatro releases mal etiquetados como estables, y **uniendo las ventanas de menos de un día con la anterior**: 41 releases publicados a menos de un día del anterior se absorbieron en la ventana previa. La única ventana de menos de un día que queda es la última, que termina en la fecha de corte.
- **Serie canary:** todos los releases (también los canary), sin backports. En canary no se unen las ventanas cortas, porque los canary se publican varias veces por día: la serie sirve para replicar las relaciones con muchas ventanas angostas.
- **Fecha de corte común:** 1 de octubre de 2026, para que las métricas calculadas por distintas integrantes usen exactamente las mismas ventanas.

## 3. Preprocessing: correcciones en el cálculo de las métricas

En el primer análisis varias relaciones resultaron ser efectos de cómo se medían los datos, no del proyecto. Antes de repetir el análisis se corrigió el cálculo de las métricas. Las correcciones que afectan a Producto:

| Corrección | Problema que tenía | Sesgo que resuelve |
|---|---|---|
| Sin backports | La serie estable intercalaba parches de la v14 con releases de la v15 y v16, y las métricas de foto saltaban entre dos códigos distintos | Correlaciones armadas por el zigzag entre versiones (ej. CD ↔ README Completeness por colaborador en 2025–26) |
| Ventanas de menos de un día unidas | 89 ventanas duraban minutos u horas y casi no tenían actividad | Correlaciones armadas por ventanas vacías (ej. ANMCC ↔ MTTR, que valían 0 a la vez) |
| Fotos al cierre de la ventana | CD, DLOC y README se medían en el tag del release, al principio de la ventana, y en los backports en otra rama | Desfase entre las métricas de foto y las de actividad |
| Nulo cuando no hay datos | MTTR y ANMCC valían 0 cuando no se cerró ninguna issue o no hubo commits | Ceros falsos que se leían como "reparación instantánea" |
| Bots fuera también a nivel producto | El bot de issues inactivas cerraba issues viejas (el 68 % de los cierres de 2025) y los bots de release eran hasta el 19 % de los commits | MTTR y NCI inflados por cierres automáticos; ANMCC inflado por commits de release |
| DLOC con `.mdx` y sin carpetas que no son documentación | En 2023 la documentación pasó a `.mdx` y DLOC cayó a la mitad; contaba los README de cientos de ejemplos y salidas de tests | La caída de 2023 y los saltos por ejemplos y Turbopack |
| CD sin código de terceros | La mayoría de los comentarios estaba en librerías compiladas guardadas en el repo | Saltos de CD cada vez que se actualizaba esa librería |
| README Completeness solo de la raíz | Promediaba todos los README del árbol, casi todos de ejemplos | Cambios por agregar o borrar ejemplos sin que nadie edite un README |
| CFDR con el equipo de cada ventana | Aplicaba el top 10 de contribuidores de hoy a toda la historia | Personas que entraron al equipo después contadas como equipo en sus issues viejas |
| NUB con etiquetas completas | Contaba como bug las etiquetas de área "Error Handling" y "Error Overlay" | Bugs de más en 2025–26 |
| NOB y Wiki Presence por ventana | Eran constantes (las branches y el estado de la wiki de hoy) | No se podían analizar |
| Métricas de flujo de documentación | DLOC es una foto acumulada desde 2016 | Faltaba una medida de lo que se documenta en cada ventana |

El efecto de estas correcciones se ve en las series. DLOC deja de caer en 2023 y crece de forma pareja:

[[comparar serie dloc_producto]]

CD deja de saltar en 2021 y en 2024, cuando cambiaba el código de terceros:

[[comparar serie cd_producto]]

Y MTTR baja mucho en 2025, cuando el bot de issues inactivas cerraba la mayoría de las issues viejas:

[[comparar serie mttr_producto]]

## 4. Análisis de correlaciones

Se usa la misma correlación corregida que en el primer análisis: Spearman parcial que descuenta el momento del proyecto (curva suave) y la duración de la ventana, con la "n efectiva" por la dependencia entre releases consecutivos, corrección por comparaciones múltiples, y los mismos criterios de estabilidad, réplica en canary y control por tamaño.

### 4.1 Resumen

[[grafico kpis]]

| | Antes | Ahora |
|---|---|---|
| Pares | 136 | 276 |
| Pares de control | 11 | 20 |
| Con relación positiva | 7 | 11 |
| Con relación negativa | 9 | 9 |
| Robustas | 7 | 7 |
| **Robustas que se mantienen** | — | **1** (CFDR ↔ NUB) |

[[grafico categorias]]

### 4.2 Mapa de calor

[[grafico mapa]]

**Cambio marcado respecto del análisis original.** Antes el mapa tenía un bloque azul fuerte entre DLOC, CD y README Completeness (correlaciones negativas de −0,3 a −0,7):

[[antes mapa]]

- **El bloque de documentación desaparece.** Esas correlaciones las armaban el paso de la documentación a `.mdx`, el borrado de ejemplos, el código de terceros y los backports, que movían las tres métricas en sentidos opuestos en los mismos releases. Con las métricas corregidas, DLOC ↔ README Completeness pasa de −0,44 a +0,22 y deja de ser significativa.
- **Aparece un bloque nuevo con Wiki Presence** (con README Completeness, DLOC p90 y CD). No es un patrón: Wiki Presence vale 1 hasta enero de 2020 y 0 después, así que esas correlaciones salen de comparar los primeros años con el resto. Dentro de cada período Wiki Presence es constante y no tiene correlación.

### 4.3 Correlación cruda frente a corregida

[[grafico cruda_corregida]]

### 4.4 Relaciones robustas

Al hacer clic en una fila, su análisis particular se muestra en 4.5.

[[explorador robustas tabla]]

**Qué pasó con las robustas del análisis original:**

| Relación | Antes | Ahora | Por qué cambió |
|---|---|---|---|
| CFDR ↔ NUB | +1,00 robusta | +1,00 robusta | Se mantiene: es la misma medida con dos definiciones de equipo |
| CD ↔ DLOC | −0,66 robusta | −0,53, no robusta | Sigue negativa, pero ya no en todos los períodos (+0,03 en 2016–19): la fuerza que tenía en 2023–24 venía de los cambios de estructura del repositorio |
| DLOC ↔ README Completeness (las tres versiones) | −0,33 a −0,44 robustas | +0,01 a +0,46 | Cambian de signo: las armaban los ejemplos, el `.mdx` y los backports. README Completeness ahora mide solo el README principal |
| CFDR y NUB ↔ MTTR (mediana) | −0,22 robustas | −0,06, sin relación | Las armaban los cierres de bots y la mezcla de quienes cierran issues |

### 4.5 Análisis particular

[[explorador robustas detalle]]

[[nota cfdr_producto nub_producto]]
**Qué muestran los datos:** las dos métricas siguen siendo prácticamente iguales (+1,00 en estables y +0,99 en canary). Casi todos los bugs los reportan usuarios externos a cualquiera de los dos "equipos", así que cambiar la definición de equipo casi no cambia el conteo. No constituye un hallazgo.
[[/nota]]

[[nota anmcc_mediana le_mediana]]
**Qué muestran los datos:**

- Es la relación robusta más fuerte entre métricas distintas (+0,48), y se fortalece respecto del análisis original (+0,39). Resiste el control por tamaño (+0,45) y se repite en canary (+0,21).
- Existe entre 2020 y 2024, con su máximo en 2023–24 (+0,67).
- **Se descarta al validar (sección 4.7).** La explica la llegada de gente nueva: quien recién llega tiene LE cercano a 0 y hace cambios chicos, así que en los releases con muchos nuevos las dos medianas bajan juntas. Sin los recién llegados, la relación pasa a +0,08 y deja de ser robusta.
[[/nota]]

[[nota anmcc_mediana commits_doc_producto]]
**Qué muestran los datos:**

- Es una relación nueva (−0,45): en los releases donde el colaborador típico hace cambios más amplios, una parte menor de los commits toca documentación.
- Resiste el control por tamaño (−0,41) y se repite en canary (−0,25). Existe entre 2020 y 2024 (−0,71 en 2023–24) y es casi nula en 2025–26.
- **Se descarta al validar (sección 4.7).** La lectura posible era que los releases con más trabajo de código amplio son distintos de los releases donde se trabaja la documentación. Pero la arma la forma en que se calculan las dos métricas: los commits que solo tocan documentación cambian pocos archivos, así que suben la proporción de commits de documentación y bajan ANMCC a la vez. Sin esos commits, la relación pasa a −0,07.
[[/nota]]

[[nota commits_doc_producto dloc_flujo_producto]]
**Qué muestran los datos:** se relacionan en toda la historia (+0,47, y +0,84 en canary), pero es esperable: cuantos más commits tocan documentación, más líneas de documentación cambian. Las dos métricas miden el mismo trabajo desde dos lados, así que no es un hallazgo; confirma que las métricas de flujo se calculan de forma consistente.
[[/nota]]

[[nota mttr_con_bots_producto noi_producto]]
**Qué muestran los datos:** aparece solo con la versión de MTTR que incluye los cierres de bots (−0,34); con MTTR sin bots no hay relación. Muestra el efecto del bot de issues inactivas: cuando cierra issues viejas, sube el tiempo medio de cierre y baja la cantidad de issues abiertas, en el mismo release. No existe dentro de ningún período.
[[/nota]]

[[nota anmcc_mediana cfdr_producto; anmcc_mediana nub_producto]]
**Qué muestran los datos:** son débiles (−0,26) y pasan los criterios de robustez por poco: en canary casi desaparecen (−0,05), con el control por tamaño también (−0,08) y no existen dentro de ningún período. La cantidad de gente activa explica casi toda la relación, así que conviene no interpretarlas.
[[/nota]]

### 4.6 Relaciones significativas

[[explorador significativas tabla | direccion]]

[[grafico forest]]

**Estabilidad de las relaciones significativas por período:**

[[grafico estabilidad]]

- **Las relaciones con Wiki Presence** (con README Completeness, DLOC p90 y CD) no existen dentro de ningún período: salen del escalón de 2020.
- **CD ↔ DLOC** sigue siendo la relación negativa más fuerte (−0,53), pero solo existe en 2020–2024 y no se repite en canary (−0,09).
- **DLOC p90 ↔ README Completeness** pasa de negativa a positiva (+0,46): con README Completeness medido solo en el README principal, la relación cambia de sentido, y no es estable.

[[explorador significativas detalle]]

### 4.7 Validación de las relaciones con contenido

Las dos relaciones robustas que se podían interpretar (ANMCC por colaborador con LE por colaborador y con la proporción de commits que tocan documentación) tenían una explicación alternativa que no dice nada de la calidad. Para probarla se recalcularon las variables sin lo que podía estar armando la relación y se repitió la misma correlación. Los scripts están en `analisis/validaciones/` y no modifican la base.

| Relación | Como en el análisis | Sin commits que solo tocan documentación | Sin recién llegados | Las dos cosas |
|---|---|---|---|---|
| ANMCC (mediana) ↔ LE (mediana) | +0,48 (canary +0,21) | +0,28 (canary +0,14) | **+0,08** (canary +0,06) | +0,07 |
| ANMCC (mediana) ↔ commits que tocan documentación | −0,45 (canary −0,25) | **−0,07** (canary +0,02) | −0,24 (canary −0,15) | 0,00 |

- **ANMCC ↔ LE es composición del equipo.** En la ventana mediana, el 37 % de quienes commitean lo hace por primera vez. Esas personas tienen LE cercano a 0 y hacen commits chicos, así que en los releases donde entra más gente nueva las dos medianas bajan juntas. Entre quienes ya estaban en el proyecto, la experiencia en los componentes no se relaciona con la amplitud de los commits.
- **ANMCC ↔ commits que tocan documentación es construcción.** De los 35.959 commits de la rama, 3.881 (el 10,8 %) solo tocan documentación y cambian un archivo de mediana, contra cuatro en el resto. Cuando hay más commits de ese tipo, sube la proporción de commits de documentación y baja ANMCC por colaborador, aunque no haya relación entre los dos tipos de trabajo.
- Lo que sí muestran los datos es cómo se documenta en Next.js: en commits aparte y chicos, no junto con cambios grandes de código. 1.253 de los 4.010 colaboradores nunca hicieron un commit que no fuera de documentación, y suman el 37 % de esos commits.

## 5. Componentes principales

Se usó el mismo método que en el primer análisis: rangos estandarizados, enfoque ajustado por tiempo y duración como principal, análisis paralelo de Horn para elegir cuántos componentes, rotación varimax y bootstrap de bloques. Con las métricas a nivel producto (13 variables, sin las variantes de MTTR) se usan 185 releases estables, desde julio de 2019 (v9.0.0), porque CFDR y NUB solo tienen datos desde entonces y el PCA necesita dato en todas las variables a la vez. La sección 5.5 comprueba que ese período no condiciona los componentes.

### 5.1 Cuántos componentes se retienen

[[pca screes producto+todas estable ajustado]]

[[pca criterios producto]]

- Con las 13 variables a nivel producto, Horn retiene **4 componentes**, que explican el **55 %** de la variación (antes 3 componentes y 63 % con 9 variables).
- Con las 21 variables (incluidas las de colaborador), retiene 7 y explican el 67 %.

### 5.2 Componentes identificados

[[pca cargas producto estable ajustado]]

1. **CP1 · Bugs reportados por usuarios (16 %):** CFDR y NUB (+0,97). Es el mismo componente del análisis original. Es el único que no puede comprobarse con toda la historia, porque sus dos variables empiezan en 2019 (sección 5.5).
2. **CP2 · Wiki y documentación temprana (14 %):** Wiki Presence (+0,82), CD (+0,76) y NOB (+0,62). Lo arma sobre todo el escalón de Wiki Presence en 2020, y es el componente menos estable en el bootstrap (congruencia mediana de 0,69): conviene no interpretarlo como un patrón. En el período del PCA, Wiki Presence vale 1 en un solo release (la v9.0.0) y 0 en los otros 189, por eso es tan inestable. Con toda la historia se vuelve estable (0,96), porque la wiki existió en muchos más releases, pero sigue siendo un escalón (sección 5.5).
3. **CP3 · Issues abiertas y README (13 %):** README Completeness (+0,73), NOI (+0,70) y ANMCC (−0,54). Con toda la historia se mantiene (congruencia 0,89), pero ahí no se replica en canary (0,57), así que no se refuerza.
4. **CP4 · Flujo de documentación (12 %):** DLOC 2.0 (+0,82), commits que tocan documentación (+0,77) y LE (−0,41). Es un componente nuevo, que aparece con las métricas de flujo. Es el que mejor resiste todas las comprobaciones: con toda la historia es el mismo componente (0,95), se vuelve un poco más estable (0,94) y se replica en canary (0,90) (sección 5.5).

MTTR (comunalidad 0,21) y DLOC (0,14) casi no quedan representadas: con las métricas corregidas se mueven por su cuenta.

**Cambio marcado respecto del análisis original.** Los componentes de documentación e issues de antes no se repiten:

[[pca_antes cargas producto estable ajustado]]

| Antes | Ahora | Congruencia |
|---|---|---|
| CP1 · Bugs: CFDR y NUB | CP1 · Bugs: CFDR y NUB | 0,95 (el mismo) |
| CP2 · Documentación: CD (+0,87), DLOC (−0,86), README (+0,71) | CP2 · Wiki y documentación temprana | 0,82 (distinto) |
| CP3 · Issues: MTTR (+0,76), NOI (−0,75), LE (+0,47) | CP3 · Issues abiertas y README | 0,35 (distinto) |
| — | CP4 · Flujo de documentación | nuevo |

- **El componente de documentación se deshace:** CD, DLOC y README Completeness se movían juntas por los mismos saltos de medición que armaban sus correlaciones. Corregidas, DLOC queda casi sola y CD se agrupa con Wiki Presence.
- **El componente de issues cambia:** MTTR, que antes lo encabezaba, sale del componente cuando se descartan los cierres de bots.

[[pca puntajes producto estable ajustado]]

### 5.3 Solidez y consistencia

[[pca solidez producto estable ajustado]]

- Bugs (0,93) y flujo de documentación (0,92) son estables en el bootstrap; issues abiertas y README (0,84) algo menos; el componente de Wiki Presence (0,69) es inestable.

[[pca comparacion producto]]

- **Ajustado y sin tamaño dan los mismos componentes** (0,95 a 1,00).
- **Canary replica bugs (0,93), Wiki y documentación temprana (0,98) y flujo de documentación (0,94)**; el de issues abiertas y README queda en el límite (0,80).
- **El crudo da otros agrupamientos**, como en el análisis original, porque mezcla el crecimiento del proyecto.

### 5.4 Con las 21 variables

[[pca cargas todas estable ajustado]]

Aparecen los mismos grupos (bugs, flujo de documentación, Wiki Presence con CD y DLOC p90), y las variables por colaborador forman los suyos: README Completeness por colaborador con README e issues abiertas, LE y ANMCC por colaborador, y MTTR con su versión por colaborador.

### 5.5 Validación con toda la historia

El PCA de Producto usa solo los releases desde julio de 2019 porque CFDR y NUB empiezan ahí. Para comprobar que ese período no condiciona los componentes, se repitió el PCA con el mismo método sobre toda la historia (266 releases, de 2016 a 2026), sin CFDR ni NUB, y se comparó con el de esta sección. Para separar los dos cambios, también se calculó con las mismas variables pero solo desde 2019. El script es `analisis/validaciones/pca_producto_historia_completa.py`.

| Componente de esta sección | Con toda la historia | Bootstrap: desde 2019 → toda la historia | Canary con toda la historia |
|---|---|---|---|
| CP1 · Bugs de usuarios | No puede calcularse: CFDR y NUB solo tienen datos desde 2019 | — | — |
| CP2 · Wiki y documentación temprana | El mismo (0,94), ahora también con README Completeness | 0,69–0,71 → **0,96** | Parecido (0,80) |
| CP3 · Issues abiertas y README | El mismo (0,89) | 0,84 → 0,83 | No se replica (0,57) |
| CP4 · Flujo de documentación | El mismo (0,95) | 0,92 → 0,94 | Se replica (0,90) |

- **Se mantienen los tres componentes que pueden calcularse con toda la historia**, con las mismas variables, y **no aparece ningún componente nuevo**. Sacar CFDR y NUB no cambia los otros tres: con los mismos releases, la congruencia es de 0,99 a 1,00.
- **Se refuerza el flujo de documentación:** es el mismo en todas las versiones, gana estabilidad y se replica en canary.
- **El de Wiki gana estabilidad, pero no contenido:** con toda la historia Wiki Presence cambia en muchos releases y no en uno solo, pero sigue separando la etapa con wiki (2016–2020) del resto. Sigue sin interpretarse como patrón.
- **El de issues abiertas y README no se refuerza:** se mantiene en la serie estable, pero no se replica en canary.

En resumen, usar el período desde 2019 no condiciona los resultados del PCA de Producto, y los componentes que entran en el cruce con otras dimensiones (bugs y flujo de documentación) se sostienen.

## 6. Clustering de métricas

Como tercera técnica de análisis, las métricas de Producto se agruparon con un agrupamiento jerárquico (`analisis/generar_clustering.py`). Usa las mismas 13 variables, los mismos 185 releases y la misma transformación que el PCA, pero se calcula por separado: mide la distancia entre dos métricas como 1 − |correlación| y une primero las más parecidas, con enlace promedio. El resultado es un árbol (dendrograma) que se corta en una cantidad de grupos. Se analizaron dos cortes:

- **Con la misma cantidad de grupos que componentes del PCA (4),** para comparar las dos técnicas con la misma cantidad de grupos.
- **Con la cantidad que elige el propio clustering,** según la silueta comparada con la de datos permutados al azar, con la misma lógica que el análisis de Horn en el PCA. En Producto elige **9 grupos**.

En los dos cortes, la solidez se mide con el mismo bootstrap de bloques que el PCA y con la réplica en canary.

| | PCA | Clustering de métricas |
|---|---|---|
| Qué arma | Componentes: combinaciones de métricas con pesos (cargas) | Grupos de métricas, sin pesos |
| Pertenencia | Una métrica puede cargar en varios componentes o en ninguno (carga menor que 0,4) | Cada métrica va a un único grupo |
| Cuántos | Análisis de Horn, frente a datos permutados | Silueta, frente a datos permutados |
| Solidez | Bootstrap de bloques y réplica en canary | El mismo bootstrap de bloques y réplica en canary |

### 6.1 Cuántos grupos

[[clustering silueta producto estable ajustado]]

Todos los cortes superan la silueta de datos al azar, y el que más la supera es el de 9 grupos (0,30 frente a 0,06). Con pocas variables, la silueta tiende a favorecer grupos chicos: varios de los 9 grupos son pares de métricas o métricas solas.

[[clustering dendrograma producto estable ajustado]]

### 6.2 Con 4 grupos, como el PCA

[[clustering grupos_pca producto estable ajustado]]

1. **Bugs de usuarios y tiempo de reparación:** CFDR, NUB y MTTR.
2. **Flujo de documentación:** DLOC 2.0, commits que tocan documentación y LE. Es exactamente el CP4 del PCA.
3. **Documentación, wiki e issues abiertas:** Wiki Presence, CD, NOB, README Completeness, NOI y ANMCC. Junta el CP2 y el CP3 del PCA.
4. **DLOC**, sola.

La coincidencia con los componentes es moderada (ARI 0,57), pero este corte es inestable en el bootstrap (0,33) y se replica a medias en canary (0,62).

### 6.3 Con 9 grupos, el criterio del clustering

[[clustering grupos producto estable ajustado]]

Quedan cuatro pares y cinco métricas solas:

- **Pares:** CFDR y NUB; Wiki Presence y CD; README Completeness y NOI; DLOC 2.0 y commits que tocan documentación.
- **Solas:** NOB, ANMCC, LE, MTTR y DLOC.

Es un corte sólido: estable en el bootstrap (0,65), se repite igual en canary (1,00) y coincide con el PCA en el mismo nivel que el de 4 grupos (ARI 0,54).

### 6.4 Comparación entre PCA y clustering

| Componente del PCA | Clustering con 4 grupos | Clustering con 9 grupos | Lectura |
|---|---|---|---|
| CP1 · Bugs de usuarios: CFDR y NUB | CFDR, NUB y MTTR | CFDR y NUB, igual | Coinciden. Con 4 grupos se suma MTTR, que en el PCA no carga en ningún componente |
| CP2 · Wiki y documentación temprana: Wiki Presence, CD y NOB | Unido con el CP3 en un grupo de 6 métricas | Wiki Presence y CD; NOB queda sola | Coincide el núcleo. NOB es la que menos carga en el PCA (0,62) |
| CP3 · Issues abiertas y README: README, NOI y ANMCC | Unido con el CP2 | README y NOI; ANMCC queda sola | Coincide el núcleo. ANMCC es la que menos carga (−0,54) |
| CP4 · Flujo de documentación: DLOC 2.0, commits que tocan documentación y LE | Las tres métricas, igual | DLOC 2.0 y commits que tocan documentación; LE queda sola | Coinciden. LE es la que menos carga (−0,41) |
| Sin componente: MTTR y DLOC | DLOC sola; MTTR con los bugs | Cada una sola | El clustering obliga a ubicar cada métrica |

- **Las dos técnicas encuentran los mismos núcleos.** Los cuatro pares más correlacionados son el centro de los cuatro componentes del PCA y son los grupos del corte en 9.
- **Difieren en las métricas que cargan más débil** (NOB, ANMCC y LE). El PCA las suma a un componente con una carga moderada; el clustering, que no tiene pesos, las deja solas o, con menos grupos, junta componentes enteros.
- **Con la misma cantidad de grupos, el PCA es más sólido.** El corte en 4 grupos une los dos componentes menos estables del PCA (Wiki y documentación temprana, 0,69, e issues abiertas y README, 0,84) y es inestable. El clustering solo es estable cuando separa las métricas en pares.
- **Bugs y flujo de documentación aparecen con las dos técnicas y en los dos cortes.** Son los componentes que entran en los cruces con otras dimensiones.

### 6.5 Con las 21 variables

[[clustering dendrograma todas estable ajustado]]

Con las variables por colaborador, el clustering también elige 9 grupos y coincide con el PCA en lo principal (ARI 0,59): README Completeness del proyecto y por colaborador con NOI, Wiki Presence con CD y DLOC p90, y MTTR con su versión por colaborador forman grupos iguales a componentes del PCA. La diferencia es que junta el flujo de documentación con ANMCC del proyecto y por colaborador, que en el PCA cargan en componentes distintos.

## 7. Síntesis

- **El análisis corregido es más confiable, pero encuentra menos patrones.** De las 7 relaciones robustas del análisis original, solo se mantiene CFDR ↔ NUB, que es la misma medida. Las relaciones de documentación y las de MTTR eran efectos de cómo se medía.
- **Las dos relaciones que parecían tener contenido se descartan al validar.** ANMCC por colaborador ↔ LE por colaborador (+0,48) la arma la llegada de gente nueva, y ANMCC por colaborador ↔ commits que tocan documentación (−0,45), los commits chicos que solo tocan documentación (sección 4.7). Dentro de Producto no queda ningún patrón propio: solo relaciones esperables.
- **En el PCA se mantiene el componente de bugs** y aparece uno nuevo de flujo de documentación. El de documentación de antes desaparece, y el que aparece en su lugar lo arma el escalón de Wiki Presence. Con toda la historia (sin CFDR ni NUB) se obtienen los mismos componentes, y el de flujo de documentación sale reforzado (sección 5.5).
- **El clustering de métricas encuentra los mismos núcleos que los cuatro componentes del PCA** con un cálculo distinto, y en particular los de bugs y flujo de documentación, que son los que entran en los cruces. Con la misma cantidad de grupos, el PCA es más estable; el clustering solo es estable cuando separa las métricas en pares (sección 6).
- **Con la medición corregida, las métricas de Producto son bastante independientes entre sí.** Para la tesis, eso tiene dos lecturas: que cada métrica aporta información propia al cruce con Persona y Proceso, y que el proceso de corrección es un resultado en sí mismo, porque muestra cuánto pueden engañar las métricas de repositorio si no se controlan los bots, los backports, el formato de los archivos y las ventanas de tiempo.

El análisis original está en analisis/salidas_originales/reportes/informe_producto_producto.html.
