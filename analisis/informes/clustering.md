# Clustering: métricas, cruces y tiempo

Análisis del 27/10/2026 sobre `analisis` (b1dcc9e), base `resultados_metricas_fixes`. Complementa el PCA y los cruces con dos técnicas de agrupamiento:

| Técnica | Qué agrupa | Pregunta | Script |
|---|---|---|---|
| Clustering de métricas | métricas | ¿Qué métricas se mueven juntas? | `generar_clustering.py`, `cruce_clustering.py` (Inés) |
| Clustering temporal | releases | ¿Hubo momentos parecidos? ¿Cambiaron las relaciones? | `validaciones/clustering_temporal.py` |

Todos usan los mismos datos y la misma transformación que el PCA (rangos, con la tendencia y la duración de la ventana descontadas) y los mismos controles: nula, estabilidad, réplica en canary y control por tamaño.

**Resumen:**

1. **El clustering de métricas llega a los mismos núcleos que el PCA en las tres dimensiones** y no contradice ningún hallazgo. Difiere solo en las métricas débiles o de escalón (Wiki, NOB, README, Comment Density).
2. **Entre dimensiones también coincide:** Proceso y Producto no se relacionan directamente, y lo que conecta las dimensiones pasa por Persona. En Persona–Proceso, además, confirma entre grupos una relación que con el PCA solo aparecía entre variables: **núcleo concentrado ↔ limpieza de lo viejo**.
3. **En el tiempo, next.js pasa por cuatro épocas** con cortes comunes a las tres dimensiones (dic 2017, dic 2021, mar 2024), pero no hay momentos que se repitan y las relaciones entre métricas se mantienen, salvo en Persona en 2016–2019.
4. **Los patrones de los cruces casi no dependen de cómo se corta la historia:** con las épocas en lugar de los períodos de calendario se mantiene el 70–80 %. Los que cambian están en el límite o son recientes.

## 1. Clustering de métricas dentro de cada dimensión

Agrupamiento jerárquico de las métricas (distancia 1 − |correlación|, enlace promedio), con la cantidad de grupos elegida por la silueta frente a datos permutados (`generar_clustering.py`). Estables, ajustado.

### Proceso (11 variables, 185 releases)

| Componente del PCA | Clustering (7 grupos; estabilidad 0,64; ARI con el PCA 0,70) | Canary (8 grupos) |
|---|---|---|
| CP1 · Bugs de usuarios: CFDR, NUB | CFDR y NUB | Igual |
| CP2 · Resolución de lo nuevo: Jarczyk, Process Performance | Jarczyk y Process Performance | Igual |
| CP5 · Cierre de lo viejo: MTTR, NCI | MTTR y NCI | Igual |
| CP3 · README y backlog (no se interpreta) | README y NOI | Separadas |
| CP4 · Wiki y branches (no se interpreta) | Separadas | Separadas |
| — | ANMCC sola | Sola |

- Los tres componentes que se interpretan salen igual y se repiten en canary. Confirma el Patrón 1 de Proceso: resolver lo nuevo y limpiar lo viejo son actividades distintas.
- Con menos grupos se juntan: con 5, el cierre de lo viejo se une a los bugs (CFDR, NUB, MTTR, NCI). Es la relación NCI ↔ bugs, que en los cruces se explica por el tamaño.

### Producto (13 variables, 185 releases)

Ver `informes/producto_producto_fixes.md`, sección 6. La corrida reproduce el mismo resultado: 9 grupos, los cuatro pares de núcleos del PCA (CFDR + NUB, Wiki + CD, README + NOI, DLOC 2.0 + commits que tocan documentación) y réplica en canary 1,00.

### Persona (28 variables, 270 releases)

| Componente del PCA | Clustering (10 grupos; estabilidad 0,71; ARI con el PCA 0,66) | Canary (réplica 0,32) |
|---|---|---|
| CP1 · Veteranía frente a renovación | Commiters activos y nuevos, tasa de ingreso, Development Experience, LE, REXP, Contribution Diversity (mediana) | Se repite |
| CP2 · Volumen de participación | Activos comentando, cerrando e interactuando, nuevos, Discussion Centrality | Se repite |
| CP3 · Concentración del núcleo | EXPRev y NC del 10 %, SC (mediana y p90), proporción que commitea | Se mezcla con CP4 |
| CP4 · Volumen del percentil alto | EXPRev y NC (p90), REXPRev, proporción que cierra issues | Se mezcla con CP3 |
| CP5 (tentativo) | No se forma | — |

Los cuatro componentes que se interpretan salen igual. Es la dimensión que menos se repite en canary: concentración y percentil alto se separan en estables, pero no en canary.

## 2. Cruces con grupos

`cruce_clustering.py` repite el cruce de componentes de `cruce_dimensiones.py` con las series de los grupos de métricas en lugar de los componentes del PCA.

**Métricas compartidas.** `cruce_clustering.py` arma los grupos con todas las métricas de cada dimensión y no aplica el `asignar` de la config. En Proceso–Producto quedan grupos idénticos de los dos lados (CFDR + NUB; NOI + README): esos pares salen como mecánicos, pero la correlación canónica da 1,00. `validaciones/cruce_clustering_asignado.py` corre el mismo script sacando de cada grupo las métricas asignadas al otro lado; los resultados de Proceso–Producto de esta sección son con esa corrección. En los cruces con Persona no cambia nada, porque no comparten métricas en los grupos.

### Resumen

| Cruce | Pares de componentes robustos (PCA) | Pares de grupos robustos (clustering, corte propio) | Correlación canónica entre grupos |
|---|---|---|---|
| Proceso–Producto | 0 de 4 | 0 | 0,26 (p 0,08) — con el PCA, 0,24 (p 0,063) |
| Persona–Producto | 3 (1 patrón, 1 mecánico, 1 escala) | 4 (2 patrones, 1 escala, 1 no resiste tamaño) | 0,65 (p 0,001) |
| Persona–Proceso | 3 (1 patrón, 2 escala) | 8 (5 patrones, 2 escala, 1 no resiste tamaño) | 0,65 (p 0,001) |

La correlación canónica de los cruces con Persona incluye el grupo de volumen (escala); confirma que las dimensiones se conectan a través de Persona, pero no se interpreta sola.

### Proceso–Producto

Mismo resultado que con el PCA: ningún par de grupos robusto, correlación canónica no significativa, y los patrones del conjunto reducido son los mismos que se repiten de Persona–Producto (Contribution Diversity ↔ LE, Development Experience ↔ ANMCC, SC y REXPRev ↔ bugs). **Proceso y Producto no se relacionan directamente.**

### Persona–Producto

- **Concentración ↔ bugs** (−0,37; con tamaño −0,13; canary −0,07): coincide con el CP3 ↔ CP1 del PCA (−0,36).
- **Renovación ↔ flujo de documentación: indicio.** Con el PCA salía mecánico porque LE está en los dos componentes; con grupos, LE queda sola y el par sale como patrón (+0,29). `validaciones/grupos_persona_sin_superposicion.py` muestra que no lo arma Contribution Diversity (sin ella, −0,33 orientado a veteranía) sino la renovación: commiters nuevos, tasa de ingreso y activos ↔ flujo de documentación **+0,41** (con tamaño +0,32; canary +0,39). Entre variables, tasa de ingreso de commiters ↔ commits que tocan documentación es +0,35 (con tamaño +0,30; canary +0,30), pero con los períodos de calendario no es estable porque en 2016–2019 vale 0,00; con las épocas sí (sección 5).

### Persona–Proceso

Con el PCA hay un patrón entre componentes (veteranía ↔ resolución de lo nuevo, +0,18). Con grupos aparecen cinco. Se verificaron sacando las métricas que comparten eventos con el otro lado (`validaciones/grupos_persona_sin_superposicion.py`):

| Par de grupos | Con todas las métricas | Sin la métrica sospechosa | Lectura |
|---|---|---|---|
| **Concentración ↔ limpieza de lo viejo** | +0,19 (con tamaño +0,30; canary +0,22) | Sin SC: +0,19 (+0,29; +0,21) | **Se sostiene.** Entre variables lo sostienen EXPRev del 10 % ↔ MTTR (+0,20; canary +0,17; patrón) y NC del 10 % ↔ NCI (+0,18; con tamaño +0,32). Con las épocas también es robusto entre componentes (sección 5) |
| Núcleo de revisión ↔ resolución de lo nuevo | +0,19 (+0,21; +0,14) | Sin proporción que cierra: +0,15 (+0,17; +0,08) | En parte es superposición: cuantas más issues nuevas se cierran, más gente cierra issues |
| Renovación ↔ limpieza de lo viejo | +0,31 (+0,20; +0,23) | — | En buena parte tamaño: entre variables, commiters nuevos ↔ NCI es escala |
| Concentración ↔ bugs | −0,35 (−0,13; −0,05) | — | Es el de Persona–Producto (CFDR y NUB son de las dos) |

**Lectura:** cuando pocos concentran las revisiones y los comentarios, se cierran más issues y más viejas. El núcleo concentrado se relaciona con la limpieza del backlog, no con la atención de lo nuevo. La relación "cerrar issues ↔ resolución de lo nuevo" queda como indicio: además de la superposición, es fuerte sobre todo desde 2024 (sección 5). SC (mediana) ↔ Jarczyk es por construcción (ver `informes/proceso_proceso.md`, Patrón 3).

## 3. Clustering temporal

`validaciones/clustering_temporal.py` agrupa releases (no métricas): cada release es un punto con todas las métricas de una dimensión. Para Proceso y Producto se usan dos versiones: como el PCA (desde 2019, por CFDR y NUB) y sin CFDR ni NUB (toda la historia), y las métricas compartidas se reparten como en los cruces.

### 3.1 Épocas

Con los valores tal cual, los releases se agrupan en épocas contiguas (coinciden con el período: V de Cramér 0,8–0,9). Los cortes coinciden entre dimensiones:

| Época | Persona (activos por release) | Proceso | Producto |
|---|---|---|---|
| 2016 – dic 2017 (1.x–4.1) | 104 | NOI 148, Jarczyk 0,52, MTTR 211 | DLOC ~1.000 |
| dic 2017 – dic 2021 (4.1–v12.0) | 307 | NOI 295, Jarczyk 0,55, MTTR 435 | DLOC 2.0: 40 → 500 |
| dic 2021 – mar 2024 (v12.0–v14.1) | 361 | NOI 1.297, Jarczyk 0,30, MTTR 1.300 | DLOC 17.000, NOB 24 |
| mar 2024 – hoy (v14.1–v16) | 174 | NOI 2.319, Jarczyk 0,15, MTTR 2.212 | DLOC 58.000, NOB 259 |

El equipo se triplica hasta 2021 y el proceso de issues aguanta; desde fines de 2021 el backlog se cuadruplica y la parte de issues nuevas que se cierra cae a la mitad; desde 2024 el equipo baja a la mitad, el producto sigue creciendo y el trabajo se concentra (el 10 % más activo pasa de hacer el 63 % de las revisiones al 73 %). Las épocas describen; no permiten atribuir causas.

### 3.2 No hay momentos que se repitan

Descontada la tendencia, los releases no forman grupos que pasen el criterio de `cruce_alternativos.py` (silueta ≥ 0,25, p < 0,05 y estabilidad ≥ 0,7): las siluetas van de 0,11 a 0,24, y el más cercano (Proceso con sus 5 métricas propias: 0,24, estabilidad 0,75) no se repite en canary. Ningún par de semestres separados por más de un año se parece más que por azar (los 5 de Persona que aparecen combinando estables y canary desaparecen con el control por tamaño). El patrón general de parecidos entre semestres sí se repite en canary (ρ 0,31–0,65, p < 0,01, también descontando la distancia en el tiempo), pero no alcanza para señalar momentos concretos.

### 3.3 Las relaciones se mantienen, salvo en Persona

Similitud de la matriz de correlaciones entre los cuatro períodos, frente al techo (las dos mitades de un mismo período):

- **Proceso (5 métricas propias):** 0,71–0,95 (canary 0,83–0,97), techo 0,93. Ningún par cambia.
- **Producto:** desde 2019, 0,78–0,94. Con toda la historia cambia, pero por las métricas de escalón.
- **Persona:** 2016–2019 es distinto (0,56–0,66, techo 0,77). Cambian 15 de 378 pares en estables y canary; por ejemplo, activos ↔ nuevos pasa de +0,77 a +0,10 (al principio crecer era sumar gente nueva; hoy hay una base estable y un flujo aparte de recién llegados) y EXPRev p90 ↔ proporción que commitea de +0,07 a +0,68.

### 3.4 Tabla cruzada entre dimensiones

¿Los releases que caen en un grupo de una dimensión caen en un grupo determinado de otra? (plan de análisis, punto 6.2)

| Cruce | V de Cramér (nula p95) | p |
|---|---|---|
| Persona × Proceso | 0,03 (0,13) | 0,66 |
| Persona × Producto | 0,38 (0,19) | 0,001 |
| Persona × Producto, sin CFDR ni NUB | 0,27 (0,34) | 0,37 |
| Proceso × Producto | 0,11 (0,16) | 0,19 |

La única coincidencia desaparece sin las métricas de bugs: es la relación entre la cantidad de gente activa y los bugs reportados (escala).

### 3.5 Los grupos de métricas en cada época

El clustering de métricas de la sección 1, corrido en cada período por separado:

- **Bugs (CFDR + NUB) y resolución de lo nuevo (Jarczyk + Process Performance) aparecen en todos los períodos,** en estables y en canary.
- **La limpieza de lo viejo (MTTR + NCI) se forma con claridad solo en 2025–2026.** En 2023–2024, NCI va con los bugs: es la época de más volumen, cuando NCI ↔ bugs llega a +0,60.
- **En Producto, el flujo de documentación (commits que tocan documentación + DLOC 2.0) se forma desde 2023;** antes, DLOC 2.0 iba con LE.

## 4. ¿Dependen los patrones de cómo se corta la historia?

La regla de estabilidad pide el mismo signo en los cuatro períodos de calendario (2016–2019, 2020–2022, 2023–2024, 2025–2026). `validaciones/cruce_epocas.py` repite los cruces con las cuatro épocas de la sección 3.1 (cortes en 4.1.4, v12.0.5 y v14.1.1).

| Cruce | Patrones con calendario | Con épocas | En los dos |
|---|---|---|---|
| Proceso–Producto | 14 | 11 | 9 |
| Persona–Producto | 23 | 21 | 17 |
| Persona–Proceso | 12 | 11 | 8 |

Los que cambian son pares en el límite, con un período cerca de cero. Lo propio de Proceso–Producto (NCI ↔ DLOC 2.0) no cambia.

**Con las épocas se confirman los dos hallazgos del clustering:**

- **Concentración ↔ limpieza de lo viejo** (Persona–Proceso) pasa a robusta entre componentes: CP3 Persona ↔ CP5 Proceso +0,21 (con tamaño +0,26; canary +0,16). Con el calendario fallaba solo por 2020–2022 (−0,01); por época: +0,27, +0,12, +0,15.
- **Renovación ↔ documentación** (Persona–Producto) pasa a patrón entre variables: tasa de ingreso de commiters ↔ commits que tocan documentación +0,35; por época: +0,27, +0,13, +0,56, +0,36.

**Se debilitan los que en realidad son recientes:**

- **EXPRev (p90) ↔ CFDR y NUB** (Persona–Producto, "discusión concentrada, menos bugs"): por época +0,07, −0,02, −0,36; existe desde 2024. REXPRev ↔ bugs se mantiene.
- **Proporción que cierra issues ↔ Jarczyk y Process Performance** (Persona–Proceso): por época +0,22, −0,10, +0,19, +0,52; es fuerte desde 2024 y tiene superposición.
- **Contribution Diversity ↔ commits que tocan documentación** se cae, pero ya estaba descartado como construcción (`validaciones/README.md`).

**Propuesta:** dejar los períodos de calendario como criterio principal, porque se fijaron antes de mirar los datos (las épocas salen de los mismos datos), y usar las épocas como prueba de sensibilidad: un patrón es *firme* si pasa con los dos cortes y *depende del corte* si pasa con uno solo.

## 5. Conclusiones

1. **La estructura es robusta al método:** PCA y clustering llegan a los mismos núcleos en las tres dimensiones.
2. **Proceso y Producto son independientes; Persona es el puente.** Lo que conecta la calidad del proceso con la del producto pasa por quiénes trabajan, cuántos son y qué tan concentrado está el trabajo.
3. **Persona se conecta con la limpieza del backlog, no con la atención de lo nuevo:** el núcleo concentrado va con cerrar más issues y más viejas; la relación con la resolución de lo nuevo es en parte superposición y reciente.
4. **El tiempo cambia los niveles, no las reglas.** next.js pasa por cuatro épocas, con un proceso de issues que se satura desde fines de 2021, pero las relaciones entre métricas de Proceso y Producto se mantienen. Solo Persona funciona distinto en sus primeros años.
5. **Algunas relaciones son de la última época:** la limpieza de lo viejo como grupo propio (2025–2026), el flujo de documentación (desde 2023) y la discusión concentrada con menos bugs (desde 2024).

**Limitaciones:** el clustering de releases es débil en todas las dimensiones (no permite describir estados); por período hay entre 54 y 66 releases estables; las métricas de escalón generan grupos y cambios que no se interpretan; las épocas son descriptivas.

## Cómo se corre

Desde la raíz del repo, con la base corregida, después de `generar_pca.py` y `generar_clustering.py` de las tres dimensiones y de `cruce_dimensiones.py` del par:

```bash
POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/clustering_temporal.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/cruce_clustering_asignado.py Proceso Producto analisis/cruces/proceso_producto_asignado.json propio
POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/cruce_epocas.py Proceso Producto --config analisis/cruces/proceso_producto_asignado.json
POSTGRES_DB=resultados_metricas_fixes python3 analisis/validaciones/grupos_persona_sin_superposicion.py
```

Persona–Proceso se corrió con la config de la rama `clara/persona-proceso` (`analisis/cruces/persona_proceso.json`), que todavía no está en `analisis`. Las salidas van a `analisis/salidas/validaciones/` y `analisis/salidas/cruces/`, fuera de git.
