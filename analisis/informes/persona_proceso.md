# Cruce Persona–Proceso · métricas corregidas

Análisis entre dimensiones con las métricas recalculadas (base `resultados_metricas_fixes`) · next.js

Este análisis busca patrones que conecten **cómo está compuesto y cómo participa el equipo** (Persona) con **cómo funciona el proceso de desarrollo** (Proceso): cómo se reportan, se resuelven y se cierran las issues. Responde dos preguntas:

1. **¿Las dos dimensiones están conectadas?** Es decir, si los releases en los que el equipo cambia también son releases en los que el proceso cambia, una vez descontado el crecimiento del proyecto.
2. **¿Por dónde pasa esa conexión?** Qué métricas o aspectos de cada lado se mueven juntos.

Usa el mismo método que el análisis dentro de cada dimensión (ventanas, correlación parcial, significancia, robustez y PCA). El detalle técnico está en [`analisis/cruce_dimensiones.md`](../cruce_dimensiones.md). Los gráficos y el explorador de cada par están en el reporte interactivo `analisis/salidas/reportes/reporte_cruce_persona_proceso.html`.

## 1. Qué entra de cada lado

| | Persona | Proceso |
|---|---|---|
| Variables | 28 | 12 |
| Nivel | Resúmenes por colaborador (mediana, p90, share top 10 %) de las métricas de Persona, más conteos y proporciones del equipo | Valor del proyecto en cada ventana |
| Componentes principales que se cruzan | CP1 Renovación (frente a veteranía), CP2 Volumen de participación, CP3 Concentración | CP1 Bugs de usuarios, CP2 Resolución de lo nuevo, CP5 Cierre de lo viejo |

**Cada variable queda en la dimensión que el Anexo E le asigna a su métrica.**

- Del lado de **Persona** entran los resúmenes por colaborador de las métricas que el Anexo E asigna a Persona: NC, SC, EXPRev, REXPRev, Contribution Diversity, Development Experience, Learning Ease, REXP, Skill Similarity, Discussion Centrality y Comment Density. También entran los conteos y proporciones del equipo (activos, nuevos, tasa de ingreso, proporción que commitea, comenta o cierra issues).
- Del lado de **Proceso** entra el valor del proyecto de cada métrica de Proceso.
- **Los resúmenes por colaborador de métricas que no son de Persona no entran en Persona.** Son ANMCC, MTTR, README Completeness, DIS, DLOC y NCI por persona. Siguen siendo variables de su dimensión. Esta regla se definió el 25/10/2026; antes esas 9 variables se etiquetaban también como Persona (ver sección 8).
- Cuando una métrica tiene las dos dimensiones en el Anexo E (por ejemplo, SC es de Persona y de Proceso), su resumen por colaborador va a Persona y su valor de proyecto a Proceso. Así, ninguna variable aparece en los dos lados.
- **Pares de control.** Son los pares cuyas variables se relacionan por definición. Se informan, pero no cuentan como resultado ni entran en la corrección por comparaciones múltiples. Acá hay 2: EXPRev (p90 y share) ↔ NCI, porque las acciones de revisión incluyen cerrar issues.

**Variables que no entran:**

- Las **variantes** de MTTR y NCI (con bots, mediana de issues, de bugs), igual que en el PCA de cada dimensión.
- Las **medianas de NC, EXPRev y FEXP**, que toman el mismo valor en más del 80 % de los releases.
- **Schedule Compliance**, que tiene valor en solo 15 releases.

**Wiki Presence entra en Proceso**, como en el informe de Proceso. Ninguno de sus pares es robusto.

**Componentes elegidos.** Se usan los componentes que cada dimensión interpreta:

- De **Persona**, CP1 a CP3. Con las 28 variables, el PCA de Persona retiene 5 componentes. Los tres primeros son los mismos de antes (Renovación, Volumen y Concentración) y se repiten mejor en canary (0,96, 0,86 y 0,82). El CP1 quedó orientado al revés que en la corrida anterior: un puntaje alto indica **más renovación** (más gente nueva y menos trayectoria), no más veteranía.
- De **Proceso**, CP1, CP2 y CP5. Los otros dos son estables, pero el informe de Proceso no los interpreta: CP3 "README y backlog" porque README Completeness es casi un escalón, y CP4 "Wiki y branches" porque lo arma un solo release (v9.0.0). NOI, README Completeness, ANMCC, NOB y Wiki Presence no cargan en ningún componente elegido, así que entran solas en el conjunto reducido (sección 4).

## 2. Cruce de variables

Se evaluaron los **336 pares** (28 × 12). Para cada par se calcula la correlación parcial de Spearman descontando la tendencia del tiempo y la duración de la ventana, y se aplican Benjamini–Hochberg, estabilidad en los cuatro períodos, réplica en canary y control por la cantidad de personas activas.

| Resultado | Pares |
|---|---|
| Control | 2 |
| Significativos | 44 (29 positivos, 15 negativos) |
| **Robustos** | **34** |
| · de escala | 15 |
| · mecánicos | 3 |
| · no resisten el control por tamaño | 4 |
| · **patrones** | **12** |

**Escala (15).** Son los pares en los que una de las variables es un conteo de participantes: personas activas o nuevas, comentando, cerrando issues o interactuando. Con más gente participando hay más de todo, en especial más bugs reportados por usuarios (Activos en interacción ↔ CFDR y NUB, +0,65) e issues cerradas (Activos que cierran issues ↔ NCI, +0,55). Son relaciones reales, pero hablan del **tamaño de la participación**, no de la calidad.

**Mecánicos (3).** Contribution Diversity (mediana, p90 y share) ↔ ANMCC del proyecto: las dos cuentan archivos tocados.

**No resisten el tamaño (4).** Por ejemplo, Contribution Diversity mediana ↔ CFDR (−0,22) cae a −0,06 al controlar por la cantidad de personas.

### Los 12 patrones, según su solidez

Que un par sea "patrón" quiere decir que pasó los filtros del método. Pero esos filtros son permisivos en dos puntos:

- en canary solo piden **el mismo signo**;
- en el control por tamaño aceptan que la correlación baje a la mitad.

Por eso los separamos en dos grupos. Son **sólidos** los pares cuya correlación casi no cambia con el control por tamaño y que canary repite con una fuerza parecida. Son **débiles** los pares cuya correlación cae mucho con el tamaño o que en canary dan casi cero.

**Sólidos (4)**

| Persona | Proceso | ρ | con tamaño | canary | Por período (16–19 / 20–22 / 23–24 / 25–26) |
|---|---|---|---|---|---|
| SC (mediana) | Jarczyk | +0,33 | +0,35 | +0,30 | +0,21 / +0,59 / +0,54 / +0,14 |
| Proporción que cierra issues | Jarczyk | +0,23 | +0,25 | +0,26 | +0,06 / +0,05 / +0,34 / +0,40 |
| Proporción que cierra issues | Process Performance | +0,23 | +0,23 | +0,15 | +0,05 / +0,09 / +0,19 / +0,43 |
| EXPRev (share top 10 %) | MTTR | +0,20 | +0,20 | +0,17 | +0,42 / +0,30 / +0,19 / +0,29 |

Los tres primeros forman el patrón principal del cruce (sección 7). El cuarto es una relación secundaria y débil: cuando la revisión se concentra en el 10 % más activo, las issues tardan más en cerrarse. El componente de Concentración frente al de Cierre de lo viejo va en la misma dirección (+0,21), pero no es robusto.

**Débiles (8)**

| Persona | Proceso | ρ | con tamaño | canary | Por qué |
|---|---|---|---|---|---|
| REXPRev (mediana) | CFDR / NUB | −0,31 | −0,16 | −0,07 | Cae a la mitad con tamaño; canary casi cero |
| EXPRev (p90) | CFDR / NUB | −0,28 | −0,12 | −0,02 | Ídem |
| Tasa de ingreso (commits) | CFDR / NUB | +0,24 | +0,11 | +0,07 | Ídem |
| EXPRev (p90) | Process Performance | +0,22 | +0,22 | +0,03 | No se repite en canary |
| Proporción que comenta | ANMCC | +0,17 | +0,20 | +0,02 | No se repite en canary |

Los pares con CFDR y NUB aparecen duplicados porque las dos métricas miden prácticamente lo mismo (+0,98 en el PCA de Proceso). Además, solo tienen datos desde mediados de 2020. Estos pares son los restos de la relación de escala Volumen ↔ Bugs de usuarios.

## 3. Cruce de componentes

| Persona ↔ Proceso | ρ | con tamaño | canary | Resultado |
|---|---|---|---|---|
| CP2 Volumen ↔ CP1 Bugs de usuarios | **+0,54** | −0,15 | +0,52 | Escala |
| CP2 Volumen ↔ CP5 Cierre de lo viejo | +0,18 | +0,06 | +0,18 | Escala |
| CP1 Renovación ↔ CP2 Resolución de lo nuevo | +0,18 | +0,17 | +0,05 | Patrón, débil en canary |
| Los otros 6 pares | entre −0,28 y +0,21 | | | No robustos |

La relación más fuerte entre las dos dimensiones, **Volumen de participación ↔ Bugs de usuarios**, es de escala: cuanta más gente participa, más bugs se reportan. Al controlar por la cantidad de personas pasa a −0,15.

**Correlación canónica.** Mide cuánto se conectan en conjunto los componentes de las dos dimensiones. La significancia se prueba desplazando en el tiempo una de las series (1000 corrimientos):

| | 1ª correlación canónica | Umbral del azar (p95) | p | canary |
|---|---|---|---|---|
| Con los 3 componentes de Persona | +0,59 | +0,33 | 0,001 | +0,51 |
| Sin Volumen (prueba de sensibilidad) | +0,33 | +0,28 | 0,013 | |

Con los tres componentes, la conexión es clara y se repite en canary. Pero la mayor parte la aporta la escala: sin el componente de Volumen baja a +0,33. Sigue siendo significativa, aunque apenas por encima de lo que da el azar. **Más allá del tamaño, las dos dimensiones están conectadas de forma débil.**

## 4. Conjunto reducido

De cada lado entra un puntaje por componente elegido, más las variables que no cargan en ninguno (Persona 12 elementos, Proceso 9; 108 pares). Así cada aspecto aparece una sola vez y hay menos comparaciones. Resultado: 4 patrones, 1 de escala y 1 mecánico.

| Persona | Proceso | ρ | con tamaño | canary |
|---|---|---|---|---|
| SC (mediana) | CP2 Resolución de lo nuevo | +0,36 | +0,38 | +0,22 |
| Proporción que cierra issues | CP2 Resolución de lo nuevo | +0,29 | +0,30 | +0,31 |
| REXPRev (mediana) | CP1 Bugs de usuarios | −0,34 | −0,20 | −0,11 |
| EXPRev (p90) | CP1 Bugs de usuarios | −0,29 | −0,11 | −0,08 |

Los dos primeros son el patrón principal, ahora contra el componente completo de resolución: resisten el tamaño y se repiten en canary. Los otros dos son débiles, por el mismo motivo que en el cruce de variables.

## 5. Triangulación y PCA conjunto

**Triangulación.** Ningún patrón queda triangulado. Para eso, sus dos variables tendrían que cargar en componentes que a su vez se relacionen como patrón. Las variables del patrón principal (SC mediana, Proporción que cierra issues) no cargan en ningún componente firme de Persona, así que este criterio no las puede confirmar. Eso no quiere decir que el patrón sea falso: quiere decir que no forma parte de los aspectos que resumen a Persona.

**PCA conjunto** (25 variables, 189 releases, Horn retiene 4):

- **CP1 (26 %) mezcla dimensiones:** personas activas y nuevas en la interacción, junto con CFDR y NUB. Es la misma relación de escala.
- **CP2 (20 %):** Renovación, solo de Persona.
- **CP3 (11 %):** Concentración, solo de Persona.
- **CP4 (7 %):** Resolución de lo nuevo (Jarczyk y Process Performance), solo de Proceso.

Fuera de la escala, los aspectos de cada dimensión siguen separados: el patrón principal es una relación entre métricas puntuales, no una fusión de componentes.

## 6. Comprobación con los métodos descartados

`cruce_alternativos.py` corre, sobre este mismo cruce, los métodos que se descartaron, para que el descarte no dependa solo del argumento. Usa 28 variables de Persona y 11 de Proceso (DIS queda afuera: tiene datos en menos del 60 % de los releases), con 185 releases estables y 1827 canary.

| Método | ¿Aporta? | Qué encuentra |
|---|---|---|
| CCA sobre todas las variables | Sí | Sin escala ni definiciones superpuestas: r₁ = +0,72 frente a una nula de +0,64 (canary +0,40). La arman la concentración del núcleo (EXPRev y NC share), la Proporción que cierra issues y SC mediana, frente a Jarczyk, NCI, README Completeness y Process Performance |
| Random forest | Sí | Con métricas de Persona predice Jarczyk (R² +0,13, canary +0,12, con tamaño +0,12) y NCI (+0,35, canary +0,51, con tamaño +0,21). Las variables que más pesan: SC mediana, personas que cierran issues y Proporción que cierra issues |
| Información mutua | Sí | 5 pares nuevos, 2 se repiten en canary: Proporción que cierra issues ↔ NCI (ρ +0,32) y Nuevos contribuyentes (commits) ↔ Jarczyk (ρ +0,18) |
| Reglas de asociación | No | 546 reglas sobre el azar, pero solo 2 nuevas se repiten en canary |
| Regresión multivariable | No | Ningún modelo predice fuera de muestra, en canary y con control por tamaño |
| Clustering de releases | No | Grupos débiles (silueta 0,11) e inestables; sin ajustar salen por época |
| Clustering de métricas | No | No coincide con los componentes (ARI 0,18) |

**Lo importante:** los métodos que aportan algo **vuelven a encontrar el mismo patrón** por caminos distintos (CCA, random forest e información mutua). No aparece ninguna relación nueva sólida.

## 7. Patrones identificados

### Patrón principal (tentativo): más participación en el cierre de issues, más resolución de lo nuevo

En los releases en que **una parte mayor del equipo cierra issues**, y en que **el colaborador típico abre y resuelve más issues y pull requests** (SC mediana), **se resuelve una parte mayor de las issues creadas en ese mismo release** (Jarczyk y Process Performance).

| Evidencia | Valor |
|---|---|
| Variables: SC mediana ↔ Jarczyk | +0,33 (con tamaño +0,35, canary +0,30) |
| Variables: Proporción que cierra issues ↔ Jarczyk | +0,23 (con tamaño +0,25, canary +0,26) |
| Conjunto reducido: Proporción que cierra issues ↔ Resolución de lo nuevo | +0,29 (con tamaño +0,30, canary +0,31) |
| Conjunto reducido: SC mediana ↔ Resolución de lo nuevo | +0,36 (con tamaño +0,38, canary +0,22) |
| CCA con todas las variables, sin escala | La primera correlación la arma este eje |
| Random forest | Predice Jarczyk y NCI con estas variables, con control por tamaño |
| Información mutua | Proporción que cierra issues ↔ NCI, repetida en canary |

**Por qué no es un efecto del tamaño.** Las variables de Persona son **proporciones y medianas**, no conteos, y el control por la cantidad de personas no cambia la correlación (+0,23 → +0,25; +0,33 → +0,35).

**Coincide con lo que encontró Proceso.** El informe de Proceso tiene como Patrón 3 (en verificación) "más participación del colaborador típico, más resolución de lo nuevo", con el mismo par SC mediana ↔ Jarczyk. Este cruce lo amplía: suma la Proporción que cierra issues, lo confirma contra el componente completo de Resolución de lo nuevo y lo vuelve a encontrar con los métodos alternativos.

**Cuándo se ve.**
- **SC mediana ↔ Jarczyk** es fuerte en 2020–2024 (+0,59 y +0,54) y débil antes y después (+0,21 y +0,14).
- **Proporción que cierra issues ↔ Jarczyk** aparece recién desde 2023 (+0,34 y +0,40).

O sea, el mismo eje se ve a través de métricas distintas en distintos momentos. Hasta 2024 lo marca cuánto participa el colaborador típico. Desde 2023, cuando la comunidad pasa a ser un grupo más chico (análisis Persona–Persona), lo marca qué parte de ese grupo se ocupa de cerrar issues.

**Límites.**
- **Puede haber una superposición de construcción, y falta medirla.** Proporción que cierra issues y Jarczyk salen de los mismos eventos de cierre: una cuenta personas y la otra issues. Además, SC suma las issues que una persona abre y cierra ella misma en la ventana, y esas issues también cuentan en Jarczyk (el informe de Proceso señala lo mismo). Mientras no se mida cuánto pesa, el patrón se presenta como **tentativo**.
- Es una relación **moderada** (ρ entre +0,23 y +0,36), lejos de las relaciones fuertes dentro de Persona.
- No queda triangulado (sección 5).
- Como toda correlación, **no indica causa**: no dice si más gente cerrando issues hace que se resuelvan más, o si cuando entran issues fáciles de resolver más gente participa en cerrarlas.

### Lo que no es un patrón de calidad: la escala

La relación más fuerte del cruce es **Volumen de participación ↔ Bugs de usuarios** (+0,54 entre componentes; hasta +0,65 entre variables). Se mantiene en toda la historia y en canary, pero desaparece al controlar por la cantidad de personas: describe el tamaño de la comunidad, no la calidad del proceso.

### Lo que no se conecta: la renovación del equipo

La renovación (cuánta gente nueva entra y cuánta trayectoria tiene el colaborador típico) es el aspecto más marcado dentro de Persona, pero **no se conecta de forma sólida con Proceso**. Su relación con la Resolución de lo nuevo (+0,18) no se repite en canary (+0,05).

## 8. Cambios respecto de las corridas anteriores

| Corrida | Qué cambió | Efecto |
|---|---|---|
| 23/10 | Primera corrida, con la regla del PCA que excluía variables casi constantes y con el diccionario anterior a Wiki Presence en Proceso | Luego corregida |
| 25/10 (1) | Se revirtió la regla del PCA, Wiki Presence entra en Proceso y se usan los componentes interpretados de Proceso (CP1, CP2 y CP5) | El PCA de Proceso da 5 componentes, como en su informe. Los patrones de variables no cambian |
| 25/10 (2) | Persona deja afuera los resúmenes por colaborador de métricas que no son de Persona en el Anexo E (37 → 28 variables) | Ver abajo |

**Efecto del último cambio:**

- Se van 6 patrones, los que usaban NCI p90, MTTR mediana y DIS mediana. Eran relaciones entre una métrica de Proceso medida por persona y otra de Proceso medida en el proyecto.
- Desaparecen los tres indicios con DIS.
- El patrón principal no cambia.
- La correlación canónica con los tres componentes queda igual (+0,59), pero sin Volumen baja de +0,42 a +0,33.

## 9. Advertencias

- **CFDR y NUB** solo tienen datos desde mediados de 2020. Además, NUB está inflado en 2025–2026: 39 ventanas cuentan como bug etiquetas como "Error Handling".
- **Los criterios del método son permisivos** en canary (mismo signo) y en el control por tamaño. Por eso este informe separa los patrones por solidez (sección 2). Es una decisión que conviene unificar en los tres cruces.
- **README Completeness y Wiki Presence** son escalones en el tiempo. Sus relaciones no se interpretan.
- **DIS** tiene datos en 132 de 271 releases estables. Queda afuera del PCA de Proceso y de los métodos alternativos, y ninguno de sus pares es robusto.
- **Skill Similarity** usa los lenguajes que cada persona tiene hoy, no en cada release.

## 10. Síntesis

- **Persona y Proceso están conectadas, pero sobre todo por la escala.** La correlación canónica entre sus componentes es +0,59, y la mayor parte la explica el volumen de participación. Sin ese efecto queda una conexión débil (+0,33, apenas sobre el azar).
- **La conexión que no es escala pasa por un solo eje:** la participación de las personas en el cierre de issues se mueve junto con la resolución de las issues nuevas.
  - Lo encuentran la correlación de a pares, el conjunto reducido, la CCA sobre todas las variables, el random forest y la información mutua.
  - Resiste el control por tamaño y se repite en canary.
  - Queda como tentativo hasta medir la superposición con Jarczyk (sección 7).
- **La relación más fuerte entre las dos dimensiones** (participantes ↔ bugs de usuarios) es de escala y no se interpreta como calidad.
- **La renovación del equipo,** el patrón más fuerte dentro de Persona, no se conecta de forma sólida con Proceso. Lo que se relaciona con cómo funciona el proceso no es cuánto tiempo lleva la gente en el proyecto, sino cómo se reparte entre las personas la tarea de cerrar issues.

## Cómo se reproduce

```bash
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_diccionario.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_correlaciones.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_pca.py Persona
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_pca.py Proceso
POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruce_dimensiones.py Persona Proceso --config analisis/cruces/persona_proceso.json
python3 analisis/reporte_cruce_dimensiones.py Persona Proceso
POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruce_alternativos.py Persona Proceso --config analisis/cruces/persona_proceso.json
```

La prueba de sensibilidad sin Volumen usa `analisis/cruces/persona_proceso_sin_volumen.json`, y sus resultados están en `analisis/salidas/cruces/persona_proceso_sin_volumen/`.