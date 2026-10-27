# Cruce Proceso–Producto

Corrida del 26/10/2026 sobre `analisis` (a27ce17), base `resultados_metricas_fixes`, con `cruce_dimensiones.py` y la configuración `analisis/cruces/proceso_producto_asignado.json`. Sigue la regla del Anexo E: cada resumen por colaborador conserva la dimensión de su métrica.

**Resultado: Proceso y Producto casi no se relacionan directamente.** De 396 pares, 14 son patrones, pero 13 se repiten tal cual en otro cruce: son métricas que la planilla asigna a Persona y a Proceso (o a Persona y a Producto), y su relación ya aparece en Persona–Producto o en Persona–Persona. El único patrón propio de este cruce es NCI ↔ DLOC 2.0, débil y en el límite de la significación. Ningún par de componentes es robusto, la correlación canónica no es significativa, el PCA conjunto no mezcla dimensiones y no hay efecto con demora.

## Configuración

**Variables.** De cada lado entran las métricas del proyecto y los resúmenes por colaborador (mediana, p90 y parte del 10 % más activo) de las métricas de esa dimensión.

| Lado | Variables |
|---|---|
| Proceso (22) | Del proyecto: NCI, Jarczyk, Process Performance, DIS, MTTR, NOI. Por colaborador: NCI (p90, 10 %), DIS, MTTR, y las métricas que también son de Persona: Contribution Diversity, EXPRev, REXPRev, NC, SC (mediana, p90, 10 %) y Development Experience |
| Producto (18) | Del proyecto: CFDR, NUB, README Completeness, Wiki Presence, NOB, ANMCC, Comment Density, DLOC, DLOC 2.0, commits que tocan documentación, Learning Ease. Por colaborador: ANMCC, README Completeness, DLOC (mediana, p90, 10 %), y las que también son de Persona: Comment Density y Learning Ease |

**Métricas compartidas entre Proceso y Producto.** Se asignan según lo que miden: MTTR y NOI a Proceso, porque describen cómo se trabajan las issues; CFDR, NUB, README Completeness, Wiki Presence, NOB y ANMCC a Producto, porque describen defectos, documentación y código. Los resúmenes por colaborador siguen a su métrica: MTTR por colaborador a Proceso, ANMCC y README por colaborador a Producto.

**Métricas que también son de Persona.** Se dejan en el cruce, como dice la planilla, y sus hallazgos se marcan como repetidos (sección 1). Se probó sacarlas (sección 7): no aparece nada nuevo.

**Componentes elegidos a mano.** Del PCA de cada dimensión con sus métricas del proyecto. El umbral automático de "firmes" dejaba entrar los dos componentes de Proceso que arman escalones (README y backlog, Wiki y branches), y los dos PCA comparten el componente de bugs porque se calcularon con las métricas compartidas adentro.

| Lado | Componentes | Bootstrap | Canary |
|---|---|---|---|
| Proceso | CP2 · Resolución de lo nuevo (Jarczyk, Process Performance) | 0,98 | 0,99 |
| Proceso | CP5 · Cierre de lo viejo (MTTR, NCI) | 0,95 | 0,97 |
| Producto | CP1 · Bugs de usuarios (CFDR, NUB) | 0,93 | 0,93 |
| Producto | CP4 · Flujo de documentación (DLOC 2.0, commits que tocan documentación) | 0,92 | 0,94 |

## 1. Cruce de variables

396 pares: 25 robustos (14 patrones, 7 mecánicos y 4 que no resisten el control por tamaño).

**Propios de Proceso–Producto:**

| Par | ρ corregida | 2016–19 | 2020–22 | 2023–24 | 2025–26 | Canary | Con tamaño | Tipo |
|---|---|---|---|---|---|---|---|---|
| NCI ↔ DLOC 2.0 | +0,22 | +0,36 | +0,32 | +0,30 | +0,17 | +0,23 | +0,11 | patrón |
| NCI ↔ CFDR | +0,30 | — | +0,16 | +0,60 | +0,18 | +0,31 | +0,02 | no resiste tamaño |
| NCI ↔ NUB | +0,30 | — | +0,16 | +0,60 | +0,17 | +0,30 | +0,02 | no resiste tamaño |

- **NCI ↔ DLOC 2.0 es el único patrón propio, y es débil:** en los releases donde se cierran más issues también se cambia más documentación. Es positivo en los cuatro períodos y se repite en canary, pero el control por tamaño lo reduce a la mitad (+0,11). Además está en el límite de la significación (p = 0,0017): pasa la corrección por comparaciones múltiples con los 396 pares, pero no si se prueba solo con las métricas que no son de Persona (sección 7). Lo más probable es que refleje el volumen de trabajo del release. No triangula: los componentes que contienen esas métricas no se relacionan de forma robusta.
- **NCI ↔ bugs de usuarios es volumen:** en los releases con más gente activa se reportan más bugs y se cierran más issues. Con control por la cantidad de personas activas, la relación desaparece (+0,02).
- **Los resúmenes por colaborador que son solo de Proceso o solo de Producto** (NCI p90 y 10 %, DIS, MTTR, ANMCC, README y DLOC por colaborador) no forman ningún par robusto.

**Repetidos de otro cruce (13 patrones).** Son métricas de Persona y Proceso, o de Persona y Producto: las mismas series que en el otro cruce, con los mismos números. Se interpretan allá.

| Par | ρ corregida | Con tamaño | Canary | Ya está en |
|---|---|---|---|---|
| EXPRev (10 %) ↔ DLOC 2.0 | +0,29 | +0,34 | +0,18 | Persona–Producto: núcleo concentrado, más documentación |
| NC (10 %) ↔ DLOC 2.0 | +0,21 | +0,27 | +0,12 | Persona–Producto: núcleo concentrado, más documentación |
| SC (p90) ↔ DLOC 2.0 | +0,20 | +0,24 | +0,17 | Persona–Producto: núcleo concentrado, más documentación |
| REXPRev (mediana) ↔ CFDR | −0,31 | −0,16 | −0,07 | Persona–Producto: discusión concentrada, menos bugs |
| REXPRev (mediana) ↔ NUB | −0,31 | −0,16 | −0,07 | Persona–Producto: discusión concentrada, menos bugs |
| EXPRev (p90) ↔ CFDR | −0,28 | −0,12 | −0,02 | Persona–Producto: discusión concentrada, menos bugs |
| EXPRev (p90) ↔ NUB | −0,27 | −0,12 | −0,03 | Persona–Producto: discusión concentrada, menos bugs |
| Contribution Diversity (mediana) ↔ commits que tocan documentación | −0,42 | −0,38 | −0,24 | Persona–Producto (validado: lo arma el cálculo de las dos métricas) |
| Development Experience ↔ ANMCC (mediana) | +0,38 | +0,37 | +0,22 | Persona–Producto (validado: lo arman los recién llegados) |
| Contribution Diversity (p90) ↔ Comment Density | +0,28 | +0,29 | +0,02 | Persona–Producto |
| NC (p90) ↔ Learning Ease | −0,22 | −0,26 | −0,03 | Persona–Producto |
| EXPRev (10 %) ↔ Learning Ease | −0,20 | −0,24 | −0,05 | Persona–Producto |
| Contribution Diversity (mediana) ↔ Learning Ease (mediana) | +0,49 | +0,46 | +0,22 | Persona–Persona (las dos son de Persona) |

Los 7 pares mecánicos (Contribution Diversity ↔ ANMCC, Development Experience ↔ Learning Ease) y los 2 de Contribution Diversity ↔ bugs que no resisten tamaño también se repiten de Persona–Producto o Persona–Persona.

## 2. Cruce de componentes

| Par | ρ corregida | 2020–22 | 2023–24 | 2025–26 | Canary | Con tamaño |
|---|---|---|---|---|---|---|
| Resolución de lo nuevo ↔ Bugs de usuarios | +0,10 | −0,12 | +0,02 | +0,19 | +0,10 | +0,08 |
| Resolución de lo nuevo ↔ Flujo de documentación | +0,18 | +0,22 | +0,23 | −0,08 | +0,02 | +0,17 |
| Cierre de lo viejo ↔ Bugs de usuarios | −0,17 | −0,09 | −0,13 | −0,27 | −0,00 | **−0,40** |
| Cierre de lo viejo ↔ Flujo de documentación | +0,15 | +0,23 | +0,28 | +0,16 | +0,13 | +0,12 |

Ninguno es robusto: ninguno es significativo después de la corrección por comparaciones múltiples.

**A mirar, sin interpretarlo como patrón:** cierre de lo viejo ↔ bugs de usuarios es negativo en los tres períodos con datos, y con el control por tamaño se vuelve moderado (−0,40). Es decir, entre releases con la misma cantidad de gente, los que cierran issues más viejas tienen menos bugs reportados. Pero en canary es nulo (−0,00) y no es significativo, así que no alcanza.

## 3. Conjunto reducido

Componentes elegidos más las variables que no cargan en ninguno (Proceso: 20 elementos; Producto: 15). 300 pares: 9 patrones y 6 mecánicos, todos con métricas que también son de Persona. Los que involucran componentes repiten lo de Persona–Producto: la concentración de la participación (NC 10 %, SC p90, REXPRev, EXPRev p90) con el componente de bugs, y Contribution Diversity y Development Experience con el de flujo de documentación. Ningún par entre métricas propias de Proceso y de Producto es robusto.

## 4. Correlación canónica

Primera correlación canónica entre componentes: +0,24, frente a +0,25 del percentil 95 con datos desplazados en el tiempo (p = 0,063). **No hay una conexión global entre las dos dimensiones.**

## 5. PCA conjunto

Con las 9 variables que definen los componentes elegidos (189 releases), Horn retiene 4 componentes: bugs (29 %), resolución de lo nuevo (19 %), flujo de documentación (15 %) y cierre de lo viejo (13 %). **Cada componente sale de una sola dimensión**: ninguno mezcla métricas de Proceso y de Producto.

## 6. Métodos alternativos

`cruce_alternativos.py` (CCA sobre todas las variables, reglas de asociación, clustering, regresión, información mutua y random forest; DIS queda afuera por cobertura) no encuentra relaciones nuevas entre métricas propias de Proceso y de Producto.

- **CCA sobre todas las variables** (+0,72 sin escala ni definiciones superpuestas, canary +0,23): la arman EXPRev, NC y SC (p90 y 10 %) contra CFDR, NUB, Learning Ease y DLOC 2.0. Es el patrón de Persona–Producto.
- **Clustering de métricas** ("aporta" según el script): los grupos que mezclan dimensiones juntan la concentración de la participación con los bugs, y Contribution Diversity y Development Experience con ANMCC y la documentación. Otra vez lo de Persona–Producto.
- **Información mutua** ("aporta"): de los 3 pares nuevos que se repiten en canary, los 3 tienen una métrica que también es de Persona (EXPRev p90 ↔ DLOC, REXPRev ↔ Comment Density por colaborador, SC p90 ↔ DLOC), con ρ entre −0,17 y +0,21.
- **Reglas de asociación:** 2 reglas nuevas que se repiten en canary entre métricas propias (NOI bajo → Comment Density alto; NCI bajo → ANMCC por colaborador alto). No tienen correlación robusta detrás; quedan como indicio.
- **Regresión y random forest:** no predicen ninguna métrica de Producto fuera de muestra, en canary y con control de tamaño.

## 7. ¿Cambia algo si se sacan las métricas que también son de Persona?

No aparece nada nuevo. Se corrió excluyendo del lado de Proceso las 14 variables que también son de Persona y del lado de Producto Comment Density y Learning Ease por colaborador (`analisis/cruces/proceso_producto_sin_persona.json`):

| Variables | Pares | Robustos | Patrones | Componentes robustos |
|---|---|---|---|---|
| Todas (la de este informe) | 396 | 25 | 14 (13 repetidos + NCI ↔ DLOC 2.0) | 0 de 4 |
| Sin las que también son de Persona | 160 | 0 | 0 | 0 de 4 |

Con 160 pares, ningún par pasa la corrección por comparaciones múltiples (Benjamini–Hochberg), ni siquiera NCI ↔ DLOC 2.0. Su correlación es la misma; cambia el umbral, que depende de cuántos pares hay y de cuántos tienen p muy chicos. Como sacar esas métricas no revela nada y solo mueve el umbral, se dejan, como indica la planilla, y se marcan los repetidos.

Con la regla anterior (solo métricas del proyecto, 66 pares) el resultado era el mismo y no dependía de cómo se asignaran las métricas compartidas: por lo que miden, 3 robustos y 1 patrón (NCI ↔ DLOC 2.0); todas a Proceso, ninguno; excluidas de los dos lados, 1 patrón (NCI ↔ DLOC 2.0).

## 8. Efecto con demora

El cruce compara las dos dimensiones dentro del mismo release. Para ver si un efecto tarda en aparecer, se repitió comparando una dimensión en un release con la otra 1, 2 y 3 releases después, en las dos direcciones, con `analisis/cruce_rezago.py`. Se usó el mismo método: correlación parcial (controlando además la duración de las dos ventanas), n efectiva, Benjamini–Hochberg, signo en los cuatro períodos, canary (con una demora equivalente en tiempo: 1 release estable ≈ 14 canary) y control por tamaño de las dos ventanas.

| Demora | Proceso → Producto | Producto → Proceso |
|---|---|---|
| 1 release | 0 significativos de 400 | 0 de 400 |
| 2 releases | 0 de 400 | 0 de 400 |
| 3 releases | 0 de 400 | 0 de 400 |

- **No hay efecto con demora.** Ningún par pasa la corrección (la q más baja es 0,10) y ninguno supera |0,32|.
- **Entre métricas propias de Proceso y de Producto, lo que aparece es lo esperable por azar:** 59 de 984 pares con p < 0,05, frente a unos 49 por azar. Con las métricas que también son de Persona hay más (180 de 1.416, frente a 71), pero es el eco de los patrones del mismo release, que se arrastran de un release al siguiente.
- **La pista de "cierre de lo viejo ↔ menos bugs" se desvanece con la demora:** con MTTR solo, al release siguiente da −0,21, pero no es significativo después de la corrección y en canary es 0; a los dos y tres releases es prácticamente 0.
- **En canary, los pares con bugs dan casi siempre 0.** Las ventanas canary duran horas y casi no tienen bugs reportados, así que la réplica en canary es poco informativa para esas métricas.

## Síntesis

- **Las métricas de Proceso y de Producto se mueven de forma independiente** release a release, y tampoco se relacionan con 1 a 3 releases de demora. Lo único propio que las conecta es el volumen de actividad: en releases con más gente se cierran más issues, se reportan más bugs y se cambia más documentación.
- **Lo que sí conecta las dos dimensiones pasa por las personas.** Los 13 patrones repetidos son métricas que la planilla asigna también a Persona (la concentración de la participación, la experiencia, la amplitud de lo que toca cada uno), y se interpretan en Persona–Producto y Persona–Persona.
- **Es coherente con lo que se vio dentro de Proceso:** la cantidad de bugs que reportan los usuarios no depende de cómo se resuelven las issues. Ni la resolución de lo nuevo ni el cierre de lo viejo se relacionan con los bugs ni con la documentación.
- **Una relación a seguir:** cierre de lo viejo ↔ bugs de usuarios (−0,40 con control por tamaño), que no se repite en canary.
- **Para la tesis:** que dos dimensiones no se relacionen directamente es un resultado, no una falta de resultado. Con las métricas corregidas, la calidad del proceso (cómo se trabajan las issues) y la del producto (defectos, documentación, código) aparecen como aspectos separados de next.js, unidos solo por quiénes trabajan y cuántos son.

## Pendientes

1. Formato de la tarjeta de la página: un mapa con los repetidos marcados distinto, o dos mapas (todas las variables y solo las propias).
2. `cruce_alternativos.py` define su propio `MAX_PCT_MODA = 0.8` (commit 1519ab7), porque la constante de `generar_pca.py` se revirtió.
