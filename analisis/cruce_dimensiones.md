# Análisis entre dimensiones

Este documento explica qué hace [`cruce_dimensiones.py`](cruce_dimensiones.py): qué análisis corre para buscar patrones que conecten dos dimensiones de la calidad, cómo se calcula cada uno y por qué se eligió. Al final están las alternativas que se evaluaron y se descartaron.

El script usa **el mismo método** que el análisis dentro de cada dimensión. Las ventanas, los filtros, la correlación parcial, la significancia y los criterios de robustez salen de `generar_correlaciones.py`, y los componentes, de `generar_pca.py`. Así, una relación entre dimensiones se juzga con la misma vara que una relación dentro de una dimensión.

## Cómo se corre

```bash
POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruce_dimensiones.py Persona Producto --config analisis/cruces/persona_producto.json
```

Antes tienen que existir:
- `analisis/salidas/diccionario_variables.csv`, generado con `generar_diccionario.py`;
- `analisis/salidas/pca/pca_<dim>.json` de las dos dimensiones, generados con `generar_pca.py <Dim>` sobre la misma base.

Los resultados quedan en `analisis/salidas/cruces/<dima>_<dimb>/`:

| Archivo | Contenido |
|---|---|
| `pares_variables.csv` | Todos los pares de variables, con sus estadísticas y su tipo |
| `pares_componentes.csv` | Los pares de componentes |
| `pares_reducido.csv` | Los pares del conjunto reducido |
| `triangulacion.csv` | Qué patrones de variables se confirman con los componentes |
| `red_nodos.csv`, `red_aristas.csv` | La red de relaciones robustas |
| `resumen.json`, `resumen.md` | El resumen de todo lo anterior |
| `valores.json` | Valores por release, residuos corregidos y puntajes, para el reporte |

El reporte interactivo se genera después con:

```bash
python3 analisis/reporte_cruce_dimensiones.py Persona Producto
```

Queda en `analisis/salidas/reportes/reporte_cruce_<dima>_<dimb>.html`, con un mapa de calor cruzado, la red de relaciones, el explorador de cada par y una sección por cada análisis de este documento.

## Qué variables entran de cada lado

**Ninguna variable puede estar en los dos lados.** Si lo estuviera, el cruce la compararía consigo misma o con su propia familia, y aparecerían relaciones perfectas que no dicen nada.

**Por defecto:**
- **Persona** aporta todas sus variables, que son resúmenes por colaborador.
- **Las otras dimensiones** aportan solo sus variables del proyecto. Sus resúmenes por colaborador (por ejemplo, ANMCC mediana) cuentan como Persona, porque miden cómo se reparte la métrica entre las personas.
- **Las variantes de una misma métrica** (MTTR con bots, MTTR de bugs, etc.) quedan afuera, igual que en el PCA de cada dimensión.

Cuando una variable del proyecto está asignada a las dos dimensiones, hay que decidir a cuál pertenece. Por defecto se excluye de los dos lados, y en el JSON se puede asignar una por una con `"asignar"`.

## 1. Cruce de variables

**Qué es.** Para cada variable de un lado y cada variable del otro, se calcula la **correlación parcial de Spearman**, descontando la tendencia del tiempo y la duración de la ventana. Después se aplican los mismos criterios que dentro de cada dimensión:
- **muestra efectiva**, porque los releases consecutivos se parecen;
- **Benjamini–Hochberg** sobre todos los pares del cruce;
- **estabilidad**, con el mismo signo en los cuatro períodos;
- **réplica en canary**;
- **control por tamaño**, la cantidad de personas activas.

**Cómo se clasifica cada par.** Además de la categoría (positiva, negativa, sin relación, etc.), cada par robusto recibe un tipo:

| Tipo | Cuándo | Por qué se separa |
|---|---|---|
| **control** | Las dos variables se relacionan por definición | No es un resultado |
| **escala** | Una de las variables es un conteo de participantes (familia `tamano`) | Con más gente participando hay más de todo: más bugs reportados, más documentación. La relación refleja el tamaño de la ventana, no la calidad. El control por tamaño no se puede aplicar porque la variable *es* el tamaño, así que hay que separarla a mano |
| **mecánico** | Misma familia o definiciones superpuestas | Las dos variables comparten datos o cálculo |
| **no resiste tamaño** | Es robusta, pero desaparece al controlar por la cantidad de personas | Probablemente también es escala |
| **patrón** | Es robusta y no cae en ninguno de los casos anteriores | Es la candidata a relación real entre dimensiones |

**Por qué.** Es la base de todo y responde la pregunta más directa: ¿qué métricas de una dimensión se mueven junto con métricas de la otra? Sin la separación por tipo, las relaciones más fuertes serían casi todas de escala.

## 2. Cruce de componentes

**Qué es.** La misma correlación, pero entre los **puntajes por release** de los componentes principales de cada dimensión.

**Qué es un puntaje.** Un componente es una combinación de métricas con pesos (sus cargas). Para cada release se combinan los valores de esas métricas, ya pasados a rangos y ajustados, y el resultado es el puntaje del componente en ese release: qué tan alto está ese release en ese aspecto. Cada componente se convierte así en una serie con un número por release, que se cruza igual que una métrica. No se cruza la varianza explicada, que es un único número por componente.

**Cómo.**
- Se usan solo los componentes **firmes**: congruencia del bootstrap ≥ 0,85 y réplica en canary ≥ 0,70. Se pueden elegir a mano en el JSON.
- Los puntajes salen del enfoque **ajustado**, que ya descuenta el tiempo y la duración.
- Para la réplica en canary, se busca el componente de la solución canary que corresponde a cada componente estable, con la **congruencia de Tucker** sobre las variables comunes.
- Se aplican los mismos criterios de significancia, estabilidad, canary y control por tamaño que a las variables. Los puntajes ya vienen ajustados por tiempo y duración, y la correlación parcial vuelve a descontarlos; el segundo ajuste casi no cambia nada, pero mantiene el método idéntico.
- El control por tamaño se aplica a todos los pares de componentes.

**Cómo se clasifica cada par de componentes.** Además de robusto o no:

| Tipo | Cuándo |
|---|---|
| **escala** | Uno de los dos componentes está hecho sobre todo de conteos de participantes: la mitad o más de sus variables fuertes son de escala, como en "Volumen de participación" |
| **mecánico** | Los dos componentes comparten una métrica entre las que los definen. Por ejemplo, la Veteranía de Persona incluye Learning Ease (mediana) y el Flujo de documentación de Producto incluye Learning Ease (proyecto): parte de su relación es esa métrica compartida |
| **no resiste tamaño** | Es robusto, pero desaparece al controlar por la cantidad de personas |
| **patrón** | Es robusto y no cae en ninguno de los casos anteriores |

**Por qué.** Cada componente resume un aspecto completo de la dimensión, como la veteranía del equipo o los bugs de usuarios. Cruzar 2 o 3 componentes por lado son unas 6 comparaciones en vez de cientos. Hay mucho menos riesgo de encontrar relaciones por azar y el resultado es más fácil de interpretar.

## 3. Conjunto reducido

**Qué es.** Un cruce intermedio entre los dos anteriores. De cada lado entran:
- **un elemento por cada componente firme:** su puntaje por release o, con `"reducido": {"modo": "marcadoras"}`, su variable de carga más alta;
- **las variables que no cargan en ningún componente firme** (|carga| < 0,4 en todos), que tienen información propia que los componentes no recogen. En Producto, por ejemplo, MTTR, NOI, DLOC o Comment Density.

**Cómo.**
- Se cruzan todos los elementos de un lado con todos los del otro, con el mismo cálculo que en los puntos 1 y 2: correlación parcial, muestra efectiva, Benjamini–Hochberg sobre los pares de este conjunto, estabilidad, canary y control por tamaño.
- Se usan los mismos tipos que en el cruce de variables. Además, un par es **mecánico** si el componente de un lado contiene la misma métrica que la variable o el componente del otro. Por ejemplo, la Veteranía de Persona, que incluye ANMCC por colaborador, frente a ANMCC del proyecto.
- Un componente cuenta como **escala** con la misma regla que en el punto 2.

**Por qué.**
- **No repite la misma información:** en el cruce de variables, CFDR y NUB dan siempre resultados duplicados, y un aspecto con cinco métricas aparece cinco veces. Acá cada aspecto aparece una vez.
- **Hay más poder para detectar relaciones reales:** son unas 200 comparaciones en vez de 481, así que la corrección de Benjamini–Hochberg castiga menos.
- **Se lee en términos de aspectos:** "Veteranía ↔ MTTR" en lugar de diez pares de variables sueltas.
- **No pierde las métricas independientes,** que en el cruce de componentes quedan afuera.

**Puntajes o variables marcadoras.** El puntaje es más confiable porque promedia varias métricas y tiene menos ruido. La variable marcadora se entiende mejor porque es una métrica real, pero es más ruidosa. Por defecto se usan los puntajes.

## 4. Correlación canónica entre componentes

**Qué es.** La **correlación canónica (CCA)** busca la combinación de componentes de un lado que más se relaciona con una combinación de componentes del otro. Da una medida **global** de cuánto se conectan las dos dimensiones.

**Cómo.**
- Se calcula sobre los puntajes de los componentes firmes, en las ventanas que tienen datos de los dos lados.
- La significancia de la primera correlación canónica se prueba con 1000 **permutaciones por corrimiento circular**: se desplaza en el tiempo la serie de un lado, lo que conserva el parecido entre releases consecutivos pero rompe la relación entre las dos dimensiones.

**Por qué.** Complementa el cruce de a pares. Dos dimensiones pueden estar conectadas por una combinación de aspectos aunque ningún par suelto se destaque.

**Por qué solo sobre componentes.** Con las variables sueltas (unas 50) y unos 185 releases, la CCA casi siempre encuentra correlaciones canónicas cercanas a 1, aunque no haya relación, porque tiene demasiados grados de libertad. Con pocos componentes ese problema desaparece.

## 5. Triangulación

**Qué es.** Un patrón de variables se considera **triangulado** si se cumplen dos condiciones:
- sus dos variables cargan (|carga| ≥ 0,4) en componentes de sus dimensiones;
- esos dos componentes también tienen una relación que es un **patrón**: robusta, que resiste el control por tamaño, que no es de escala y en la que los componentes no comparten una métrica.

**Por qué.** Es el criterio más fuerte para afirmar que un patrón conecta dimensiones: aparece a nivel de las métricas y también a nivel de los aspectos que resumen esas métricas. Un patrón aislado puede ser casualidad o depender de una sola métrica; uno triangulado es más difícil de explicar por azar.

## 6. PCA conjunto

**Qué es.** Un PCA con las variables de las dos dimensiones juntas.

**Cómo.**
- Por defecto entran solo las variables que definen los componentes firmes de cada lado. El PCA necesita al menos 3 releases completos por variable, y con todas las variables no alcanzan.
- Usa el mismo procedimiento que el PCA de cada dimensión: rangos, enfoque ajustado, Horn, varimax y bootstrap por bloques.
- Se marcan los componentes que **mezclan dimensiones**, es decir, que tienen cargas fuertes en variables de los dos lados.

**Por qué.** Es un chequeo independiente. Si las dos dimensiones están conectadas, debería aparecer algún componente que agrupe variables de las dos. Y si un componente mixto coincide con un par de componentes relacionados del punto 2, el patrón se refuerza.

## 7. Red de métricas

**Qué es.** Una tabla de nodos (variables) y aristas (relaciones robustas, con su tipo). Cada variable tiene su **grado**: cuántos patrones la involucran.

**Por qué.** No es un análisis estadístico nuevo, sino otra forma de presentar el cruce de variables. Muestra qué métricas hacen de **puente** entre las dimensiones y sirve para comunicar el resultado o dibujarlo.

## Cómo leer los resultados

- Lo más confiable es un **patrón triangulado**, que además aparezca en un componente mixto del PCA conjunto.
- Un patrón que aparece en el cruce de variables y también en el conjunto reducido (por ejemplo, entre un componente y una métrica independiente) es más sólido que uno que aparece en uno solo.
- Las relaciones de **escala** son reales, pero no hablan de calidad: hablan del tamaño de la participación. Se informan, pero no se interpretan como patrones de calidad.
- Las relaciones que involucran CFDR o NUB aparecen duplicadas, porque las dos métricas miden prácticamente lo mismo. Además, solo tienen datos desde 2019.
- Una correlación entre dimensiones **no implica causa**. Solo dice que dos aspectos se mueven juntos de release en release.

## Configuración

Todo lo que puede cambiar entre un cruce y otro se define en un JSON. Hay ejemplos en `analisis/cruces/`.

| Clave | Para qué |
|---|---|
| `lados.<Dim>.niveles` | Qué niveles de variable aporta cada lado (`producto`, `persona_agregada`) |
| `lados.<Dim>.excluir` | Variables que no entran |
| `lados.<Dim>.variantes` | `true` para incluir las variantes de una métrica |
| `compartidas` | Qué hacer con las variables que quedan en los dos lados: `excluir` o el nombre de la dimensión que se las queda |
| `asignar` | Asignar variables compartidas una por una: `{"cfdr_producto": "Producto"}` |
| `escala.familias`, `escala.variables` | Qué cuenta como escala (por defecto, la familia `tamano`) |
| `componentes.conjunto` | Qué conjunto del PCA usar por dimensión (`producto` o `todas`) |
| `componentes.enfoque` | `ajustado` (por defecto), `crudo` o `tamano` |
| `componentes.elegir` | Componentes a usar a mano: `{"Producto": [1, 4]}` |
| `componentes.umbral_bootstrap`, `componentes.umbral_canary` | Umbrales de congruencia para que un componente sea firme |
| `carga_minima` | Desde qué carga una variable define un componente (0,4) |
| `reducido.modo` | `puntajes` (por defecto) o `marcadoras` para el conjunto reducido |
| `reducido.escala_si` | Proporción de variables de escala desde la que un componente cuenta como escala (0,5) |
| `permutaciones` | Permutaciones de la CCA (1000) |
| `pca_conjunto`, `pca_conjunto_variables` | Correr o no el PCA conjunto, y con qué variables (`componentes` o `todas`) |

## Alternativas descartadas

| Alternativa | Qué haría | Por qué se descartó |
|---|---|---|
| **Matriz de correlaciones cruzadas** | Todas las correlaciones entre las variables de las dos dimensiones | No se descartó: es el cruce de variables del punto 1, presentado como matriz |
| **CCA sobre todas las variables** | La relación global entre los dos grupos completos de métricas | Con unas 50 variables y unos 185 releases, da correlaciones canónicas cercanas a 1 aunque no haya relación, por exceso de grados de libertad. Se usa solo sobre los componentes |
| **Reglas de asociación** (support, confidence, lift) | Combinaciones frecuentes de valores, del tipo "si A es alto, B es bajo" | Obliga a pasar las métricas a categorías, lo que pierde información y hace depender el resultado de dónde se corta. Genera cientos de reglas sin control de comparaciones múltiples e ignora que los releases consecutivos se parecen |
| **Clustering de releases** | Grupos de versiones con características parecidas | Con métricas que crecen con el proyecto, los grupos salen por época y no por calidad. Con los datos ajustados se podría probar, pero no hay una forma clara de validar si los grupos son reales. Queda como posible trabajo futuro |
| **Clustering de métricas** | Grupos de métricas que se parecen | Es lo que ya hace el PCA, con criterios claros para decidir cuántos grupos hay (Horn) y si son estables (bootstrap) |
| **Regresiones multivariables** | Predecir una métrica de una dimensión con varias de la otra | Con tantas variables correlacionadas entre sí, los coeficientes son inestables y cambian de signo según qué variables entren. Los releases no son independientes, así que los errores estándar quedan subestimados. La correlación parcial ya controla tiempo, duración y tamaño |
| **Información mutua** | Dependencias no lineales | Con unos 185 releases autocorrelacionados, su estimación es ruidosa y difícil de testear. Spearman ya capta las relaciones monótonas, aunque no sean lineales |
| **Random forest y otros modelos de machine learning** | Importancia de cada métrica para predecir otra | Con pocos datos se ajusta al ruido, y la importancia de una variable no es una prueba estadística: no dice si la relación es real ni en qué dirección va. Tampoco respeta el orden en el tiempo |

### Comprobación con los datos

`analisis/cruce_alternativos.py` corre estas alternativas sobre un cruce ya hecho, para que el descarte no dependa solo del argumento:

```bash
POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruce_alternativos.py Persona Producto --config analisis/cruces/persona_producto.json
```

Necesita scikit-learn (`python3 -m pip install scikit-learn`) y que antes se haya corrido `cruce_dimensiones.py` para el mismo par, porque compara con sus resultados. Usa los mismos releases y la misma transformación que el PCA ajustado. Cada método se compara con una nula que corre un lado en forma circular respecto del otro, tiene que repetirse en canary y no cuenta lo que se explica por el tamaño, por definiciones superpuestas, por la misma métrica en los dos lados o por variables con menos de 10 valores distintos. Deja en `analisis/salidas/cruces/<a>_<b>/alternativos/` un `resumen.md` con el veredicto por método y un CSV por método.

En Persona–Producto ninguno encuentra un patrón nuevo: la CCA sobre todas las variables, sin escala ni definiciones superpuestas, vuelve a encontrar la relación entre la concentración del núcleo y los bugs de usuarios (y le agrega una réplica débil en canary), y random forest vuelve a encontrar la de ANMCC y los commits de documentación, con forma no lineal. El resto se explica por relaciones ya encontradas, por el tamaño o por variables escalón.
