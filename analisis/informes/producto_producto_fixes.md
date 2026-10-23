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
| Flujo de documentación | producto | Líneas de documentación agregadas o eliminadas en la ventana | Nueva |
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
| DLOC ↔ README Completeness (las tres versiones) | −0,33 a −0,44 robustas | +0,22 a +0,46 | Cambian de signo: las armaban los ejemplos, el `.mdx` y los backports. README Completeness ahora mide solo el README principal |
| CFDR y NUB ↔ MTTR (mediana) | −0,22 robustas | −0,06, sin relación | Las armaban los cierres de bots y la mezcla de quienes cierran issues |

### 4.5 Análisis particular

[[explorador robustas detalle]]

[[nota cfdr_producto nub_producto]]
**Qué muestran los datos:** las dos métricas siguen siendo prácticamente iguales (+1,00 en estables y +0,99 en canary). Casi todos los bugs los reportan usuarios externos a cualquiera de los dos "equipos", así que cambiar la definición de equipo casi no cambia el conteo. No constituye un hallazgo.
[[/nota]]

[[nota anmcc_mediana le_mediana]]
**Qué muestran los datos:**

- Es la relación robusta más fuerte entre métricas distintas (+0,48), y se fortalece respecto del análisis original (+0,39). Resiste el control por tamaño (+0,46) y se repite en canary (+0,22).
- Existe entre 2020 y 2024, con su máximo en 2023–24 (+0,67).
- Como en el análisis original, parte de la relación la explica la llegada de gente nueva: quien recién llega tiene LE cercano a 0 y hace cambios chicos, así que en los releases con muchos nuevos las dos medianas bajan juntas.
[[/nota]]

[[nota anmcc_mediana commits_doc_producto]]
**Qué muestran los datos:**

- Es una relación nueva (−0,46): en los releases donde el colaborador típico hace cambios más amplios, una parte menor de los commits toca documentación.
- Resiste el control por tamaño (−0,41) y se repite en canary (−0,25). Existe entre 2020 y 2024 (−0,71 en 2023–24) y es casi nula en 2025–26.
- Una lectura posible: los releases con más trabajo de código amplio (refactors, features grandes) son distintos de los releases donde se trabaja la documentación.
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

## 5. Componentes principales

Se usó el mismo método que en el primer análisis: rangos estandarizados, enfoque ajustado por tiempo y duración como principal, análisis paralelo de Horn para elegir cuántos componentes, rotación varimax y bootstrap de bloques. Con las métricas a nivel producto (13 variables, sin las variantes de MTTR) se usan 185 releases estables, desde fines de 2020, porque CFDR y NUB solo tienen datos desde entonces.

### 5.1 Cuántos componentes se retienen

[[pca screes producto+todas estable ajustado]]

[[pca criterios producto]]

- Con las 13 variables a nivel producto, Horn retiene **4 componentes**, que explican el **55 %** de la variación (antes 3 componentes y 63 % con 9 variables).
- Con las 21 variables (incluidas las de colaborador), retiene 7 y explican el 67 %.

### 5.2 Componentes identificados

[[pca cargas producto estable ajustado]]

1. **CP1 · Bugs reportados por usuarios (16 %):** CFDR y NUB (+0,97). Es el mismo componente del análisis original.
2. **CP2 · Wiki y documentación temprana (14 %):** Wiki Presence (+0,82), CD (+0,76) y NOB (+0,62). Lo arma sobre todo el escalón de Wiki Presence en 2020, y es el componente menos estable en el bootstrap (congruencia mediana de 0,69): conviene no interpretarlo como un patrón.
3. **CP3 · Issues abiertas y README (13 %):** README Completeness (+0,73), NOI (+0,70) y ANMCC (−0,54).
4. **CP4 · Flujo de documentación (12 %):** flujo de documentación (+0,82), commits que tocan documentación (+0,77) y LE (−0,41). Es un componente nuevo, que aparece con las métricas de flujo.

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

## 6. Síntesis

- **El análisis corregido es más confiable, pero encuentra menos patrones.** De las 7 relaciones robustas del análisis original, solo se mantiene CFDR ↔ NUB, que es la misma medida. Las relaciones de documentación y las de MTTR eran efectos de cómo se medía.
- **Lo que queda con contenido gira alrededor de ANMCC por colaborador:** se relaciona con LE por colaborador (+0,48) y, en sentido contrario, con la proporción de commits que tocan documentación (−0,46).
- **En el PCA se mantiene el componente de bugs** y aparece uno nuevo de flujo de documentación. El de documentación de antes desaparece, y el que aparece en su lugar lo arma el escalón de Wiki Presence.
- **Con la medición corregida, las métricas de Producto son bastante independientes entre sí.** Para la tesis, eso tiene dos lecturas: que cada métrica aporta información propia al cruce con Persona y Proceso, y que el proceso de corrección es un resultado en sí mismo, porque muestra cuánto pueden engañar las métricas de repositorio si no se controlan los bots, los backports, el formato de los archivos y las ventanas de tiempo.

El análisis original está en analisis/salidas_originales/reportes/informe_producto_producto.html.
