# Análisis

Busca patrones entre las métricas de Persona, Proceso y Producto en tres niveles: **intradimensional**
(dentro de cada dimensión), **bidimensional** (entre pares de dimensiones) y **tridimensional** (las tres
a la vez). Este documento explica qué se corre, qué técnica aplica cada paso, con qué criterios y qué
reporte la muestra. Resume el capítulo 3 (*Metodología*, Fase 2) del informe del trabajo *Descubrimiento
de Patrones de Calidad en repositorios CVS*.

Cómo leer los resultados: [SALIDAS.md](../SALIDAS.md).

## Cómo se corre

Desde la raíz del repositorio, `python3 tres_p.py analizar` (o `--sin-reportes`). Corre en este orden:

| Paso | Script | Deja en `salidas/` |
|---|---|---|
| 1 | `generar_diccionario.py` | `1_variables/` |
| 2 | `correlaciones.py` | `2_dimensiones/correlaciones/` |
| 3 | `pca.py <Dim>` y `clustering.py <Dim>`, para cada dimensión | `2_dimensiones/<dim>/` |
| 4 | `cruces.py <DimA> <DimB>` para cada par (configuración en `cruces/`), y otra vez con `--grupos propio` para el cruce entre grupos | `3_cruces/<dima>_<dimb>/` y `.../clustering_propio/` |
| 5 | `tres_dimensiones.py` | `4_tres_dimensiones/` |
| 6 | `multiverso_asignacion.py` | `6_robustez/multiverso_asignacion/` |
| 7 | `relaciones.py --recalcular` (**clasificación final**) | `5_patrones/` |
| 8 | `bloques_etiquetas.py` | `6_robustez/metricas_compartidas/` |
| 8b | complementarios (salvo `--sin-complementarios`): `correlaciones.py --periodos ambos`, `cruces.py --periodos epocas` y `cruce_alternativos.py` por par, `complementarios/temporal.py releases` y `epocas`, `cruce_rezago.py` y `pesos_catalogo.py` | `complementarios/` |
| 9 | `reporte_pca.py`, `reporte_cruce.py`, `reporte_cruce_dimensiones.py`, `reporte_tres_dimensiones.py`, `reporte_resultados.py` y `reporte_complementarios.py`; después `reportes.py` los reúne | `reportes/intradimensional.html`, `bidimensional.html` y `tridimensional.html` |
| 10 | `indice.py` | `LEEME.md` |

Los pasos 5, 6 y 8 necesitan componentes en las tres dimensiones. Si una dimensión no tiene (pocas
releases para sus variables), se saltean con un aviso.

Los datos salen de la base del proyecto (`POSTGRES_*` en `.env`) y de
`datos/persona_agregado_estable_canary.csv` (`tres_p.py exportar`). El repositorio, los tags excluidos,
los períodos, las épocas y las relaciones descartadas al validar se leen de `proyecto.json`.

---

## 1. Esquema general

El análisis busca relaciones entre métricas de calidad de las tres dimensiones, Persona, Proceso y
Producto, a lo largo de la historia de un repositorio. Se organiza en tres niveles, en este orden:

| Nivel | Pregunta | Hipótesis del informe |
|---|---|---|
| Intradimensional | ¿Qué métricas de una misma dimensión se mueven juntas? ¿En qué aspectos se resume cada dimensión? | H1a |
| Bidimensional | ¿Qué métricas o aspectos de una dimensión se mueven junto con los de otra? | H1b |
| Tridimensional | ¿Hay patrones que involucren a las tres dimensiones a la vez? | H1c |

Los tres niveles parten del mismo preprocesamiento. Usan las mismas tres técnicas, correlaciones, PCA y
agrupamiento, con los mismos criterios: una relación entre dimensiones se juzga igual que una relación
dentro de una dimensión. Sobre el resultado se aplican pruebas de sensibilidad (asignación de las
métricas compartidas y forma de dividir la historia) y una validación final.

```
preprocesamiento ─► correlaciones ─► PCA ─► agrupamiento ─► cruces de a dos ─► tres dimensiones
                                                                   │
                     multiverso de asignaciones ◄──────────────────┤
                     clasificación final de los patrones (relaciones.py) ─► validación
```

## 2. Unidad de observación: la ventana entre releases

La historia del repositorio se divide en **ventanas entre releases consecutivos**: el intervalo que va
desde la publicación de una versión hasta la siguiente. Se eligió esta unidad porque los releases son
cortes que marca el propio proyecto. En cada ventana se calculan las métricas de las tres dimensiones,
así lo que pasa en el equipo y en el proceso puede relacionarse con el estado del producto en ese momento.

Se arman dos series (`metricas/run_versiones.py`):

- la **serie estable**, con las ventanas entre versiones estables. Es la base del análisis;
- la **serie canary**, que también incluye las prereleases. Cubre la misma historia con más ventanas y
  mucho más cortas, y se usa como **réplica**.

Criterios de construcción:

- se excluyen los **backports**: releases de una versión mayor anterior publicados cuando ya hay otra
  vigente;
- se excluyen los tags mal etiquetados (`excluir_estable` en `proyecto.json`);
- en la serie estable, los releases con menos de un día de diferencia se unen en una sola ventana;
- todas las corridas usan una **fecha de corte común** (`hasta`), así cualquier corrida produce las
  mismas ventanas.

Las métricas de estado (tamaño del código, documentación existente) se miden sobre la rama principal al
cierre de cada ventana. Las de actividad (commits, issues cerradas) se calculan sobre los eventos de la
ventana.

## 3. Preprocesamiento

**Scripts:** `generar_diccionario.py`, `preprocesamiento.py` (lo usan todos los demás) y
`metricas/export_persona.py`.
**Salida:** `salidas/1_variables/diccionario_variables.csv`.

Convierte los resultados de las métricas en un conjunto de **variables con un valor por ventana**, en cinco
pasos:

1. **Variables base.** Las métricas de producto tienen un valor por ventana. Las de persona tienen un
   valor por contribuyente en cada ventana.
2. **Integración de identidades** (`metricas/mapear_identidades.py`). Une el nombre de git de cada autor
   con su login de GitHub, para que una misma persona no cuente como dos. Descarta los bots.
3. **Construcción de variables.** Las métricas de persona se resumen con la **mediana** (el
   contribuyente típico). Las de volumen de actividad suman el **percentil 90** (los más activos) y la
   **proporción del total que concentra el 10 % más activo** (concentración del trabajo). Además se
   construyen **variables de participación**: contribuyentes activos por tipo de actividad, recién
   llegados y cinco proporciones entre esos conteos (por ejemplo, la tasa de ingreso).
4. **Limpieza.** Se quitan las variables que toman el mismo valor en más del 80 % de las ventanas (no
   pueden variar junto con otra) y las que tienen datos en menos de 30 ventanas. Las variantes de una
   misma métrica (por ejemplo, MTTR con y sin bots) quedan **solo como control**.
5. **Transformación.** Todas las variables se pasan a **rangos**. A cada una se le descuentan dos
   factores:
   - la **tendencia temporal**, con un spline natural de 4 grados de libertad sobre el orden de las
     ventanas, para que dos métricas que crecen con el proyecto no parezcan relacionadas solo por eso;
   - la **duración de la ventana**, como log(días), porque las ventanas más largas acumulan más
     actividad.

Las variables que el catálogo asigna a dos dimensiones se cuentan en las dos, así que la suma por
dimensión es mayor que la cantidad de variables.

## 4. Análisis de correlaciones

**Script:** `correlaciones.py`. `relaciones.py` lo usa para evaluar todos los pares juntos.
**Salidas:** `salidas/2_dimensiones/correlaciones/` (pares dentro de cada dimensión) y
`salidas/5_patrones/correlaciones/` (todos los pares).

Evalúa, par por par, si dos variables se mueven juntas de un release al siguiente. **Todos los pares se
evalúan una sola vez**, con el mismo procedimiento. Después cada uno se
clasifica según las dimensiones que puede conectar (sección 9).

- **Correlación.** Correlación parcial de Spearman, sin la tendencia ni la duración de la ventana. No
  depende de la escala ni de los valores extremos.
- **Bases de cálculo.** Cada par se calcula en tres bases:
  - la serie estable (principal);
  - la serie canary (réplica);
  - cada uno de los cuatro **períodos de calendario**, fijados antes de mirar los datos (`calendario`
    en `proyecto.json`; con `"auto"` se reparten los años en cuatro).
- **Pares de control.** No se interpretan ni entran en la corrección múltiple los pares relacionados por
  construcción:
  - la misma métrica medida de dos formas;
  - una variable que incluye a la otra;
  - una proporción con las cantidades que la forman.
- **Significancia.** Valor p e intervalo de confianza del 95 % con la **muestra efectiva**, porque
  releases consecutivos no son independientes (Pyper y Peterman, 1998). Los p se corrigen con
  **Benjamini–Hochberg**, una sola vez sobre todos los pares.

**Controles.** Una correlación significativa todavía puede tener una explicación ajena a la relación
entre las métricas. Por eso cada par pasa por estos controles:

1. **Estabilidad temporal:** el mismo signo en todos los períodos con datos suficientes (al menos 15
   ventanas por período y al menos tres períodos evaluables).
2. **Réplica en canary:** el mismo signo en la serie canary.
3. **Control por tamaño del equipo:** se recalcula descontando también log(contribuyentes activos). Los
   pares con una cantidad de participantes no admiten este control y no se consideran hallazgos.
4. **Definiciones superpuestas:** se descartan, si resultan robustos, los pares de métricas que comparten
   parte de sus datos (por ejemplo, CFDR y NUB cuentan las mismas issues de bugs reportadas desde fuera
   del equipo).
5. **Correlación sin controles y tendencia local:** no descartan pares, pero ayudan a leerlos. Muestran
   cuánto se debe al crecimiento del proyecto y si la relación se da release a release o refleja un
   cambio de etapa.

**Clasificación.**

| Categoría | Condición |
|---|---|
| Significativo | p corregido < 0,05 |
| Robusto | significativo, estable en el tiempo y replicado en canary |
| **Patrón** | robusto, resiste el control por tamaño y no tiene explicación mecánica |

- **Fuerza** (Cohen, 1988): débil de 0,1 a 0,3, moderada de 0,3 a 0,5, fuerte desde 0,5.
- **Nivel de evidencia:**
  - *alto*, con fuerza en toda la historia y relación release a release;
  - *bajo*, sin fuerza en ningún período o cuando la relación es un cambio de etapa;
  - *medio*, en el resto de los casos.

## 5. Análisis de componentes principales (PCA)

**Script:** `pca.py <Dimensión>`.
**Salida:** `salidas/2_dimensiones/<dim>/pca_*.csv` y `pca.json`. El reporte queda en
`salidas/reportes/reporte_pca_<dim>.html`.

Resume las variables que varían juntas en unos pocos **componentes**, y cada componente representa un
aspecto de la dimensión. Usa las mismas ventanas y transformaciones que las correlaciones. Como
referencia, se repite también sin ajustar y descontando el tamaño del equipo. Necesita una tabla sin
huecos, así que entran las variables con dato en al menos la mitad de las ventanas (sin variantes de una
misma métrica), y solo las ventanas con dato en todas ellas.

- **Cantidad de componentes:** análisis paralelo de Horn, con 500 permutaciones y el percentil 95. Se
  compara con el criterio de Kaiser, el codo del gráfico de autovalores y la varianza explicada (70 % y
  80 %).
- **Interpretación:** rotación varimax. Una variable define un componente si su carga es de al menos 0,4
  en valor absoluto. Cada componente tiene un puntaje por release.
- **Estabilidad:** 500 remuestreos por bloques de releases consecutivos, comparados con la congruencia
  de Tucker. Un componente es **firme** si la congruencia mediana es de al menos 0,85 en los remuestreos
  y de al menos 0,70 con la serie canary.
- No se usan entre dimensiones los componentes formados por métricas casi constantes en la historia (por
  ejemplo, una métrica que vale lo mismo en casi todas las releases).

El PCA necesita al menos 3 ventanas por variable (n ≥ 3p, y nunca menos de 30). Con pocas releases una
dimensión queda sin componentes: `pca.py` lo avisa y no escribe salidas, y los pasos que dependen de
ellos (agrupamiento, cruces de componentes, tres dimensiones, multiverso, métricas compartidas) se
saltean para esa dimensión. Las correlaciones y los patrones (`relaciones.py`) no dependen del PCA.

## 6. Agrupamiento de métricas (clustering)

**Script:** `clustering.py <Dimensión>`.
**Salida:** `salidas/2_dimensiones/<dim>/agrupamiento.json` y `agrupamiento_grupos.csv`.

Busca, igual que el PCA, métricas que varían juntas, pero con otro cálculo: no asigna pesos ni signos y
pone cada métrica en un único grupo. Usa las mismas variables, releases y transformaciones que el PCA, en
las series estable y canary, y sirve para contrastar la estructura que encuentra el PCA.

- **Distancia:** 1 − |correlación|, para que dos métricas muy correlacionadas queden cerca, en el mismo
  sentido o en el contrario. Los grupos se forman con **enlace promedio**.
- **Cantidad de grupos:** índice de silueta, comparado con el de datos permutados (200 permutaciones).
  Se contrasta con la misma cantidad de grupos que componentes retiene el PCA.
- **Estabilidad:** remuestreo por bloques (200) y réplica en canary, con el índice de Rand ajustado. Con
  el mismo índice se mide cuánto coinciden los grupos con los componentes.
- **Serie de cada grupo:** el promedio de los rangos ajustados de sus métricas, orientados según la
  métrica central del grupo.

## 7. Análisis bidimensional

**Script:** `cruces.py <DimA> <DimB> --config analisis/cruces/<dima>_<dimb>.json`.
**Salida:** `salidas/3_cruces/<dima>_<dimb>/`. El reporte queda en
`salidas/reportes/reporte_cruce_<dima>_<dimb>.html`.

Busca métricas o aspectos de una dimensión que se muevan junto con los de otra. Se analiza en cuatro
planos, de lo más detallado a lo más general:

1. **Entre variables:** los pares de la sección 4 cuyas variables pueden pertenecer a dimensiones
   distintas.
2. **Entre componentes:** se cruzan los componentes firmes de cada dimensión. Son muchas menos
   comparaciones y se interpretan más fácil. El puntaje de un componente es el promedio de las variables
   que lo definen. Si dos componentes comparten métricas, se cruza la parte propia de cada uno.
3. **Entre grupos:** el mismo cruce con los grupos del agrupamiento. Un grupo reúne menos métricas que
   un componente, así que muestra relaciones que en un componente quedan diluidas.
4. **Medida global:** **correlación canónica** entre los puntajes de los componentes firmes de las dos
   dimensiones. Su significancia se evalúa desplazando en el tiempo los datos de una dimensión, lo que
   rompe la relación entre las dos sin alterar a ninguna.

Un patrón entre dos variables está **triangulado** si también aparece entre los aspectos que las
resumen: cada variable define un componente de su dimensión y esos dos componentes forman, a su vez,
un patrón.

## 8. Análisis tridimensional

**Scripts:** `tres_dimensiones.py` (componentes) y `relaciones.py` (variables).
**Salidas:** `salidas/4_tres_dimensiones/` y `salidas/5_patrones/cadenas.csv`.

Los análisis de a pares muestran qué dimensiones se relacionan, pero no si tres relaciones de a pares son
un mismo patrón o relaciones independientes. Se aborda en dos pasos:

- **Medida global.** Cuánto se conectan las tres dimensiones en conjunto:
  - correlación canónica generalizada;
  - confirmada con el coeficiente RV y el análisis factorial múltiple (MFA);
  - comparada con 1.000 desalineaciones en el tiempo de los datos de cada dimensión.

  Qué componentes entran y cómo se llaman se configura en `proyecto.json` (`tres_dimensiones`). Si no se
  configura, se nombran solos.
- **Triángulos.** Tríos de elementos (variables, componentes o grupos) relacionados de a pares, uno de
  cada dimensión y que midan **aspectos distintos** (dos medidas de la concentración del trabajo no
  cuentan como dos elementos). Cada lado se recalcula descontando el tercer vértice:
  - si los tres lados se mantienen, el patrón es **tridimensional**;
  - si alguno desaparece, es una **cadena**: dos dimensiones se relacionan solo a través de la tercera.

`tres_dimensiones.py` también arma perfiles de releases y prueba el rezago entre dimensiones.

## 9. Métricas asociadas a más de una dimensión

**Scripts:** `relaciones.py`, `bloques_etiquetas.py` y `multiverso_asignacion.py`.
**Salidas:** `salidas/5_patrones/`, `salidas/6_robustez/metricas_compartidas/` y
`salidas/6_robustez/multiverso_asignacion/`.

Dieciséis métricas pertenecen a dos dimensiones según el catálogo, y sus variables heredan las dos. Por
ejemplo, EXPRev es de Persona y de Proceso: su relación con NCI (de Proceso) puede leerse como Persona–Proceso
o como una relación dentro de Proceso, y las dos lecturas son correctas. Asignar cada métrica a una sola
dimensión habría sido arbitrario y habría dejado afuera las relaciones del otro lado. Por eso **la
dimensión se trata como una etiqueta de la relación**:

- **Entre variables** (`relaciones.py`): cada patrón se etiqueta con todos los pares de dimensiones que
  puede conectar y, si corresponde, con la dimensión en la que también se lee. Es el **criterio final**
  para las relaciones entre variables.
- **Entre componentes y grupos** (`bloques_etiquetas.py`): cada dimensión incluye todas sus variables,
  también las compartidas. Cuando dos elementos comparten métricas, se cruza la parte propia de cada uno.
  Si a alguno no le queda ninguna, no se evalúa.
- **Medidas globales** (`multiverso_asignacion.py`): la correlación canónica y la generalizada comparan
  dimensiones completas, y ahí una métrica compartida quedaría de los dos lados. Por eso se evalúan
  **todas las asignaciones posibles** (análisis de multiverso; Steegen et al., 2016): 500 al azar, las
  que cambian una métrica por vez y la opuesta. Se informa en qué proporción de asignaciones las
  dimensiones aparecen conectadas.
- **Sensibilidad:** el mismo multiverso, en versión liviana, sobre los cruces de componentes y grupos y
  la triangulación. Indica cuánto depende cada resultado de la asignación.

## 10. Sensibilidad a la división de la historia

**Scripts:** `correlaciones.py --periodos ambos` (pares dentro de cada dimensión), `cruces.py --periodos epocas`
(pares entre dimensiones) y `complementarios/temporal.py` (complementarios:
`tres_p.py analizar` los corre salvo con `--sin-complementarios`).
**Salida:** `salidas/complementarios/` (`periodos/`, `clustering_temporal/`, `epocas_todas/`).

La regla de estabilidad temporal depende de cómo se corta la historia. Como prueba, se repite con
**épocas** en lugar de los períodos de calendario:

- las épocas son tramos contiguos de releases, agrupados con Ward con restricción de contigüidad sobre
  los valores sin ajustar (`cortes_epocas` en `proyecto.json`; con `"auto"`, cuartos de la serie);
- una relación que cumple la regla con las dos divisiones es **estable con los dos cortes**;
- el calendario se mantiene como criterio principal porque se fijó antes de mirar los datos, y las épocas
  salen de los mismos datos que se analizan.

`temporal.py` agrega contexto:

- estados que se repiten (k-means de releases contra una nula por corrimiento circular);
- cómo cambia la estructura de correlaciones entre períodos.

## 11. Validación de los resultados

**Dónde:** `descartados` en `proyecto.json`. Lo aplica `relaciones.py`.

Los controles de la sección 4 se aplican antes de ver los resultados y salen de la definición de cada
métrica. La validación, en cambio, se aplica **después**, solo a los patrones que ya pasaron todo.
Busca relaciones que existen porque las dos métricas comparten una parte del cálculo que no se ve en sus
definiciones.

Para cada hallazgo:

1. Se plantea la explicación alternativa más probable.
2. Se recalculan las variables sin los datos que podrían producir la relación por sí solos: un grupo de
   colaboradores (por ejemplo, los recién llegados), un tipo de commits (los que solo tocan
   documentación) o una parte del cálculo (las issues propias que se cierran en el mismo release). Antes
   se verifica que el cálculo con todos los datos reproduzca los valores del análisis.
3. Si sin esos datos la correlación queda en ±0,15 o menos, la relación la producía el cálculo y se
   **descarta en todos los niveles**.

Ejemplo: si Learning Ease y ANMCC se relacionan, pero sin los recién llegados la correlación cae cerca de 0,
la producía la diferencia entre los recién llegados, que hacen cambios chicos, y el resto.

Esta validación depende de cada proyecto y no se automatiza. Sin un CSV de `descartados`, los patrones se
informan como **candidatos a validar**.

## 12. Otras técnicas evaluadas

**Script:** `complementarios/cruce_alternativos.py` (complementario, como los de la sección 10).
**Salida:** `salidas/complementarios/alternativos/<cruce>/`.

Se aplicaron como comprobación otras técnicas habituales para buscar patrones entre métricas. Se usaron
para ver si encontraban relaciones nuevas y si confirmaban las principales. Ninguna es técnica principal:

| Técnica | Por qué no es la principal |
|---|---|
| Correlación canónica sobre todas las variables | con muchas variables frente a la cantidad de releases, siempre encuentra alguna combinación fuerte aunque no haya relación real |
| Reglas de asociación | obligan a pasar las métricas a categorías; pierden información y ocultan relaciones débiles |
| Regresión múltiple | con variables muy correlacionadas los coeficientes son inestables, y evalúa predicción, no pares |
| Información mutua | detecta relaciones de cualquier forma, pero con pocas releases solo separa del azar las fuertes |
| Random forest | muestra qué métricas ayudan a predecir otra, no si la relación es significativa ni su dirección |

Otros scripts de `complementarios/`:

- `cruce_rezago.py`: Proceso → Producto con rezago de 1 a 3 ventanas;
- `pesos_catalogo.py`: cada métrica compartida cuenta mitad para cada una de sus dimensiones.

## 13. Los tres reportes

**Scripts:** `reporte_pca.py`, `reporte_cruce.py`, `reporte_cruce_dimensiones.py`, `reporte_tres_dimensiones.py`,
`reporte_resultados.py` y `reporte_complementarios.py` generan cada vista; `reportes.py` las reúne.
**Salida:** `salidas/reportes/`.

Un HTML por nivel de análisis, autocontenido (SVG y JavaScript): se abre con doble clic, sin servidor ni
conexión, y se regenera en cada corrida. Cada uno tiene una pestaña por dimensión o por par y una vista por
técnica, y arriba enlaces a los otros dos:

| Reporte | Pestañas | Vistas de cada pestaña |
|---|---|---|
| `intradimensional.html` | Persona, Proceso, Producto | patrones finales · correlaciones · PCA y agrupamiento · complementarios |
| `bidimensional.html` | cada par de dimensiones | patrones finales · variables y componentes (conjunto reducido, correlación canónica, triangulación, PCA conjunto) · grupos · sin métricas compartidas · multiverso · complementarios |
| `tridimensional.html` | — | medida global, red, triángulos y tríos de variables · PCA y agrupamiento conjunto · multiverso y métricas compartidas · complementarios |

Los «patrones finales» son el criterio de `relaciones.py` y coinciden con `5_patrones/resumen.md`; la vista «variables y
componentes» usa el criterio de `cruces.py`, que asigna cada métrica compartida a un solo lado. La vista «complementarios»
reúne los análisis de `complementarios/` y la sensibilidad a los períodos (`reporte_complementarios.py`).

## Archivos de esta carpeta

| Archivo | Qué hace |
|---|---|
| `rutas.py` | Dónde lee y escribe cada paso (la estructura de `salidas/`). |
| `preprocesamiento.py` | Lo común a todos (no se corre solo): lee el diccionario, la base y el CSV de Persona, calcula las proporciones, saca los backports, arma la tabla de releases, la transforma (rangos, sin tendencia ni duración) y define los períodos. |
| `generar_diccionario.py` | El diccionario de variables: métrica, nivel, estadístico, dimensiones del catálogo y cobertura. |
| `correlaciones.py` | Evalúa y clasifica pares de variables (correlación parcial, BH, estabilidad, réplica, tamaño). Lo usan también `cruces.py` y `relaciones.py`. |
| `pca.py` | PCA de una dimensión: Horn, varimax, bootstrap de bloques, congruencia con canary. |
| `clustering.py` | Agrupamiento jerárquico de las métricas de una dimensión (después de `pca.py`). |
| `cruces.py` | Un par de dimensiones: variables, componentes, grupos (`--grupos`), conjunto reducido, correlación canónica, triangulación y PCA conjunto. |
| `tres_dimensiones.py` | Las tres dimensiones a la vez: correlación canónica generalizada, RV y MFA contra una nula temporal, triángulos de componentes, perfiles y rezago. |
| `multiverso_asignacion.py` | Las medidas globales con todas las asignaciones de las métricas compartidas. |
| `relaciones.py` | Todos los pares de variables una sola vez, con una corrección BH, etiquetados con todas las lecturas del catálogo, sin los descartados al validar. Busca las cadenas entre las tres dimensiones. |
| `bloques_etiquetas.py` | El mismo criterio para componentes y grupos, sin las métricas que comparten dos dimensiones. |
| `reporte_*.py` | Cada reporte HTML: de una dimensión (correlaciones o PCA con agrupamiento), de un cruce o de las tres dimensiones. |
| `reporte_resultados.py` | Las vistas sin generador propio: patrones finales, cruce entre grupos, cruces sin métricas compartidas, multiverso y PCA y agrupamiento conjunto. |
| `reporte_complementarios.py` | La vista «Complementarios» de cada reporte. |
| `reportes.py` | Reúne todo en tres páginas, una por nivel de análisis, con una pestaña por dimensión o por par y una vista por técnica. |
| `indice.py` | `salidas/LEEME.md`, el índice de las salidas. |
| `cruces/` | Configuración de cada cruce (qué métricas compartidas van a cada lado en los cruces de componentes). |
| `complementarios/` | Análisis complementarios (no son técnica principal): técnicas alternativas (`cruce_alternativos.py`), rezago (`cruce_rezago.py`), pesos del catálogo (`pesos_catalogo.py`) y análisis temporal y épocas (`temporal.py`). Escriben en `salidas/complementarios/`; `tres_p.py analizar` los corre salvo con `--sin-complementarios`. |

## Referencias

- Benjamini, Y. y Hochberg, Y. (1995). Controlling the false discovery rate. *JRSS B*, 57(1).
- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences*.
- Pyper, B. J. y Peterman, R. M. (1998). Comparison of methods to account for autocorrelation in
  correlation analyses of fish data. *CJFAS*, 55(9).
- Steegen, S. et al. (2016). Increasing transparency through a multiverse analysis. *Perspectives on
  Psychological Science*, 11(5).
- Alonso, F. y Robiolo, G. (2022): catálogo de métricas de calidad Persona, Proceso y Producto.
