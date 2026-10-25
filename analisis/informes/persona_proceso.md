# Cruce Persona–Proceso · métricas corregidas

Análisis entre dimensiones con las métricas recalculadas (base `resultados_metricas_fixes`) · next.js

Este análisis busca patrones que conecten **cómo está compuesto y cómo participa el equipo** (Persona) con **cómo funciona el proceso de desarrollo** (Proceso): cómo se reportan, se resuelven y se cierran las issues. Responde dos preguntas:

1. **¿Las dos dimensiones están conectadas?** Es decir, si los releases en los que el equipo cambia también son releases en los que el proceso cambia, una vez descontado el crecimiento del proyecto.
2. **¿Por dónde pasa esa conexión?** Qué métricas o aspectos de cada lado se mueven juntos.

Usa el mismo método que el análisis dentro de cada dimensión (ventanas, correlación parcial, significancia, robustez y PCA). El detalle técnico está en [`analisis/cruce_dimensiones.md`](../cruce_dimensiones.md). Los gráficos y el explorador de cada par están en el reporte interactivo `analisis/salidas/reportes/reporte_cruce_persona_proceso.html`.

## 1. Qué entra de cada lado

| | Persona | Proceso |
|---|---|---|
| Variables | 37 | 12 |
| Nivel | Resúmenes por colaborador (mediana, p90, share top 10 %), conteos y proporciones del equipo | Valor del proyecto en cada ventana |
| Componentes principales que se cruzan | CP1 Veteranía, CP2 Volumen de participación, CP3 Concentración | CP1 Bugs de usuarios, CP2 Resolución de lo nuevo, CP5 Cierre de lo viejo |

**Las métricas que están en las dos dimensiones** (NC, SC, NCI, EXPRev, Contribution Diversity, DIS, MTTR, ANMCC, README Completeness, entre otras) se reparten por nivel, con la regla común a los tres cruces:

- el **resumen por colaborador** (por ejemplo, la mediana de NCI) va del lado de **Persona**, porque mide cómo se reparte la métrica entre las personas;
- el **valor del proyecto** (NCI del proyecto) va del lado de **Proceso**;
- cuando la **misma métrica** queda en los dos lados (NCI p90 ↔ NCI del proyecto), el par es de **control**: se informa, pero no cuenta como resultado ni entra en la corrección por comparaciones múltiples. Hay 8 pares de control.

Así, ninguna variable aparece en los dos lados.

**Variables que no entran:**

- Las **variantes** de MTTR y NCI (con bots, mediana de issues, de bugs) quedan afuera, igual que en el PCA de cada dimensión.
- Las **medianas de NC, NCI, EXPRev y FEXP** toman el mismo valor en más del 80 % de los releases, igual que en el análisis de Persona.
- **Schedule Compliance** tiene valor en solo 15 releases.

**Wiki Presence entra en Proceso**, como en el informe de Proceso (la planilla la asigna a Producto y a Proceso). No aporta ningún resultado: ninguno de sus pares es robusto.

**Componentes elegidos.** Se usan los componentes que cada dimensión interpreta:

- De **Persona**, CP1 a CP3. CP4 (percentil alto) queda afuera porque no se replica en canary (0,33).
- De **Proceso**, CP1, CP2 y CP5. Los otros dos son estables, pero el informe de Proceso no los interpreta: CP3 "README y backlog" porque README Completeness es casi un escalón, y CP4 "Wiki y branches" porque lo arma un solo release (v9.0.0). Si entraran, sumarían comparaciones sin significado y meterían a Wiki Presence en el PCA conjunto. NOI, README Completeness y ANMCC no se pierden: como no cargan en ningún componente elegido, entran solas en el conjunto reducido (sección 4).

## 2. Cruce de variables

Se evaluaron los **444 pares** (37 × 12): correlación parcial de Spearman descontando la tendencia del tiempo y la duración de la ventana, con Benjamini–Hochberg, estabilidad en los cuatro períodos, réplica en canary y control por la cantidad de personas activas.

| Resultado | Pares |
|---|---|
| Control (misma métrica en los dos lados) | 8 |
| Significativos (positivos y negativos) | 59 (39 positivos, 20 negativos) |
| **Robustos** | **42** |
| · de escala | 15 |
| · mecánicos | 3 |
| · no resisten el control por tamaño | 6 |
| · **patrones** | **18** |

**Escala (15).** Son los pares en los que una de las variables es un conteo de participantes: personas activas o nuevas, comentando, cerrando issues o interactuando. Con más gente participando hay más de todo, en especial más bugs reportados por usuarios (Activos ↔ CFDR y NUB, +0,61 a +0,65) e issues cerradas (Activos que cierran issues ↔ NCI, +0,55). Son relaciones reales, pero hablan del **tamaño de la participación**, no de la calidad.

**Mecánicos (3).** Contribution Diversity (mediana, p90 y share) ↔ ANMCC del proyecto: las dos cuentan archivos tocados por commit.

**No resisten el tamaño (6).** Por ejemplo, ANMCC mediana ↔ CFDR (−0,26) cae a −0,08 al controlar por la cantidad de personas.

### Los 18 patrones, según su solidez

Que un par sea "patrón" quiere decir que pasó los filtros del método. Pero esos filtros son permisivos en dos puntos: en canary solo piden **el mismo signo**, y en el control por tamaño aceptan que la correlación baje a la mitad. Por eso los separamos en tres grupos:

- **Sólidos:** la correlación casi no cambia con el control por tamaño y canary la repite con una fuerza parecida.
- **Indicios:** cumplen lo anterior, pero dependen de DIS, que tiene datos en solo la mitad de los releases (sección 9).
- **Débiles:** la correlación cae mucho con el tamaño o en canary es casi cero.

**Sólidos (7)**

| Persona | Proceso | ρ | con tamaño | canary | Períodos (16–19 / 20–22 / 23–24 / 25–26) |
|---|---|---|---|---|---|
| SC (mediana) | Jarczyk | +0,33 | +0,35 | +0,30 | +0,21 / +0,59 / +0,54 / +0,14 |
| Proporción que cierra issues | Jarczyk | +0,23 | +0,25 | +0,26 | +0,06 / +0,05 / +0,34 / +0,40 |
| Proporción que cierra issues | Process Performance | +0,23 | +0,23 | +0,15 | +0,05 / +0,09 / +0,19 / +0,43 |
| NCI (p90) | Jarczyk | +0,19 | +0,20 | +0,25 | +0,10 / +0,22 / +0,23 / +0,20 |
| MTTR (mediana) | Process Performance | −0,18 | −0,18 | −0,13 | — |
| MTTR (mediana) | NCI | +0,18 | +0,23 | +0,21 | — |
| EXPRev (share top 10 %) | MTTR | +0,20 | +0,20 | +0,17 | intermitente |

Los cuatro primeros forman el patrón principal del cruce (sección 7). Los dos de MTTR mediana se leen con cuidado: MTTR mediana es la versión por colaborador de MTTR, y MTTR del proyecto forma un componente con NCI y se calcula con los mismos tiempos de cierre que Process Performance.

**Indicios (3): dependen de DIS**

| Persona | Proceso | ρ | con tamaño | canary |
|---|---|---|---|---|
| MTTR (mediana) | DIS | +0,32 | +0,32 | +0,41 |
| DIS (mediana) | Jarczyk | −0,27 | −0,26 | −0,31 |
| NCI (p90) | DIS | +0,27 | +0,27 | +0,19 |

**Débiles (8)**

| Persona | Proceso | ρ | con tamaño | canary | Por qué |
|---|---|---|---|---|---|
| REXPRev (mediana) | CFDR / NUB | −0,31 | −0,16 | −0,07 | Cae a la mitad con tamaño; canary casi cero |
| EXPRev (p90) | CFDR / NUB | −0,28 | −0,12 | −0,02 | Ídem |
| Tasa de ingreso (commits) | CFDR / NUB | +0,24 | +0,11 | +0,07 | Ídem |
| EXPRev (p90) | Process Performance | +0,22 | +0,23 | +0,03 | No se repite en canary |
| Proporción que comenta | ANMCC | +0,17 | +0,20 | +0,02 | No se repite en canary |

Los pares con CFDR y NUB aparecen duplicados porque las dos métricas miden prácticamente lo mismo (+0,98 en el PCA de Proceso). Además, solo tienen datos desde mediados de 2020. Estos pares son los restos de la relación de escala Volumen ↔ Bugs de usuarios.

## 3. Cruce de componentes

| Persona ↔ Proceso | ρ | con tamaño | canary | Resultado |
|---|---|---|---|---|
| CP2 Volumen ↔ CP1 Bugs de usuarios | **+0,55** | −0,12 | +0,50 | Escala |
| CP2 Volumen ↔ CP5 Cierre de lo viejo | +0,18 | +0,05 | +0,11 | Escala |
| CP1 Veteranía ↔ CP5 Cierre de lo viejo | −0,23 | −0,21 | −0,06 | Patrón, débil en canary |
| CP3 Concentración ↔ CP5 Cierre de lo viejo | +0,28 | +0,33 | — | Mecánico: los dos incluyen NCI |
| Los otros 5 pares | entre −0,28 y +0,13 | | | No robustos |

La relación más fuerte entre las dos dimensiones, **Volumen de participación ↔ Bugs de usuarios**, es de escala: cuanta más gente participa, más bugs se reportan. Al controlar por la cantidad de personas pasa a −0,12.

**Correlación canónica.** Mide cuánto se conectan en conjunto los componentes de las dos dimensiones. La significancia se prueba desplazando en el tiempo una de las series (1000 corrimientos):

| | 1ª correlación canónica | Umbral del azar (p95) | p |
|---|---|---|---|
| Con los 3 componentes de Persona | +0,59 | +0,33 | 0,001 |
| Sin Volumen (prueba de sensibilidad) | +0,42 | +0,30 | 0,001 |

Sin el componente de escala la conexión baja, pero sigue claramente por encima del azar. **Las dos dimensiones están conectadas más allá del tamaño**, aunque de forma moderada.

## 4. Conjunto reducido

De cada lado entra un puntaje por componente elegido, más las variables que no cargan en ninguno (Persona 20 elementos, Proceso 9; 180 pares). Así cada aspecto aparece una sola vez y hay menos comparaciones. Resultado: 7 patrones, 1 de escala, 3 mecánicos y 2 de control.

| Persona | Proceso | ρ | con tamaño | canary |
|---|---|---|---|---|
| SC (mediana) | CP2 Resolución de lo nuevo | +0,36 | +0,38 | +0,22 |
| Proporción que cierra issues | CP2 Resolución de lo nuevo | +0,29 | +0,30 | +0,31 |
| MTTR (mediana) | DIS | +0,32 | +0,32 | +0,41 |
| DIS (mediana) | CP5 Cierre de lo viejo | +0,30 | +0,33 | +0,31 |
| REXPRev (mediana) | CP1 Bugs de usuarios | −0,34 | −0,20 | −0,11 |
| EXPRev (p90) | CP1 Bugs de usuarios | −0,29 | −0,11 | −0,08 |
| CP1 Veteranía | CP5 Cierre de lo viejo | −0,23 | −0,21 | −0,06 |

El patrón principal aparece de nuevo, ahora contra el componente completo de resolución: SC mediana y Proporción que cierra issues se relacionan con **Resolución de lo nuevo**, y la relación resiste el tamaño y se repite en canary.

## 5. Triangulación y PCA conjunto

**Triangulación.** Ningún patrón queda triangulado. Para eso, sus dos variables tendrían que cargar en componentes que a su vez se relacionen como patrón. Las variables del patrón principal (SC mediana, Proporción que cierra issues) no cargan en ningún componente firme de Persona, así que este criterio no las puede confirmar. Eso no quiere decir que el patrón sea falso: quiere decir que no forma parte de los aspectos que resumen a Persona.

**PCA conjunto** (26 variables, 189 releases, Horn retiene 4):

- **CP1 (25 %) mezcla dimensiones:** personas activas y nuevas en la interacción, junto con CFDR y NUB. Es la misma relación de escala.
- **CP2 (19 %):** Veteranía, solo de Persona.
- **CP3 (11 %):** Concentración, solo de Persona.
- **CP4 (7 %):** Resolución de lo nuevo (Jarczyk y Process Performance), solo de Proceso.

Fuera de la escala, los aspectos de cada dimensión siguen separados: el patrón principal es una relación entre métricas puntuales, no una fusión de componentes.

## 6. Comprobación con los métodos descartados

`cruce_alternativos.py` corre, sobre este mismo cruce, los métodos que se descartaron, para que el descarte no dependa solo del argumento. Usa 36 variables de Persona y 11 de Proceso; quedan afuera las dos de DIS, que tienen datos en menos del 60 % de los releases. Usa 184 releases estables y 1593 canary.

| Método | ¿Aporta? | Qué encuentra |
|---|---|---|
| CCA sobre todas las variables | Sí | Sin escala ni definiciones superpuestas: r₁ = +0,71 frente a una nula de +0,64 (canary +0,38). La arman la concentración del núcleo (EXPRev y NC share), la Proporción que cierra issues y SC mediana, frente a NCI, Jarczyk y Process Performance |
| Random forest | Sí | Con métricas de Persona predice Jarczyk (R² +0,15, canary +0,15, con tamaño +0,14) y NCI (+0,36, canary +0,48, con tamaño +0,22). Las variables que más pesan: personas que cierran issues, SC mediana y Proporción que cierra issues |
| Información mutua | Sí | 10 pares nuevos, 2 se repiten en canary: Proporción que cierra issues ↔ NCI (ρ +0,33) y NCI p90 ↔ Process Performance |
| Reglas de asociación | Sí, exploratorio | 4 reglas nuevas que se repiten en canary (por ejemplo, ANMCC mediana alto → NCI bajo; Skill Similarity alto → NOI bajo). El método pasa las métricas a categorías y genera cientos de reglas: se toman como pistas, no como hallazgos |
| Regresión multivariable | No | Ningún modelo predice fuera de muestra, en canary y con control por tamaño |
| Clustering de releases | No | Los grupos son débiles (silueta 0,10) y sin ajustar salen por época |
| Clustering de métricas | No | No coincide con los componentes (ARI 0,07) y es inestable |

**Lo importante:** los métodos que aportan algo **vuelven a encontrar el mismo patrón** por caminos distintos (CCA, random forest e información mutua). No aparece ninguna relación nueva sólida.

## 7. Patrones identificados

### Patrón principal: más participación en el cierre de issues, más resolución de lo nuevo

En los releases en que **una parte mayor del equipo cierra issues**, y en que **el colaborador típico abre y resuelve más issues y pull requests** (SC mediana), **se resuelve una parte mayor de las issues creadas en ese mismo release** (Jarczyk y Process Performance).

| Evidencia | Valor |
|---|---|
| Variables: SC mediana ↔ Jarczyk | +0,33 (con tamaño +0,35, canary +0,30) |
| Variables: Proporción que cierra issues ↔ Jarczyk | +0,23 (con tamaño +0,25, canary +0,26) |
| Variables: NCI p90 ↔ Jarczyk | +0,19 (con tamaño +0,20, canary +0,25) |
| Conjunto reducido: Proporción que cierra issues ↔ Resolución de lo nuevo | +0,29 (con tamaño +0,30, canary +0,31) |
| Conjunto reducido: SC mediana ↔ Resolución de lo nuevo | +0,36 (con tamaño +0,38, canary +0,22) |
| CCA con todas las variables, sin escala | La primera correlación la arma este eje |
| Random forest | Predice Jarczyk y NCI con estas variables, con control por tamaño |

**Por qué no es un efecto del tamaño.** Las variables de Persona son **proporciones y medianas**, no conteos, y el control por la cantidad de personas no cambia la correlación (+0,23 → +0,25; +0,33 → +0,35).

**Coincide con lo que encontró Proceso.** El informe de Proceso tiene como Patrón 3 (en verificación) "más participación del colaborador típico, más resolución de lo nuevo", con el mismo par SC mediana ↔ Jarczyk. Este cruce lo amplía: suma la Proporción que cierra issues y NCI p90, lo confirma contra el componente completo de Resolución de lo nuevo y lo vuelve a encontrar con los métodos alternativos.

**Cuándo se ve.**
- **SC mediana ↔ Jarczyk** es fuerte en 2020–2024 (+0,59 y +0,54) y débil antes y después (+0,21 y +0,14).
- **Proporción que cierra issues ↔ Jarczyk** aparece recién desde 2023 (+0,34 y +0,40).

O sea, las dos variables muestran el mismo eje en momentos distintos de la historia del proyecto.

**Límites.**
- **Puede haber una superposición de construcción en las dos variables principales, y falta medirla.**
  - Proporción que cierra issues y Jarczyk salen de los mismos eventos de cierre: una cuenta personas y la otra cuenta issues.
  - SC suma las issues que una persona abre y cierra ella misma en la ventana, y esas issues también cuentan en Jarczyk. El informe de Proceso señala lo mismo.
  - Mientras no se mida cuánto pesa, el patrón se presenta como **tentativo**.
- Es una relación **moderada** (ρ entre +0,2 y +0,36), lejos de las relaciones fuertes dentro de Persona (Veteranía, −0,73).
- No queda triangulado (sección 5).
- Como toda correlación, **no indica causa**: no dice si más gente cerrando issues hace que se resuelvan más, o si cuando entran issues fáciles de resolver más gente participa en cerrarlas.

### Indicio: tiempos de cierre por colaborador y de documentación

MTTR mediana ↔ DIS (+0,32, canary +0,41) y DIS mediana ↔ Cierre de lo viejo (+0,30, canary +0,31) sugieren que cuando el colaborador típico tarda más en cerrar issues, también tardan más las issues de documentación. No se presenta como hallazgo por las limitaciones de DIS (sección 9).

### Lo que no es un patrón de calidad: la escala

La relación más fuerte del cruce es **Volumen de participación ↔ Bugs de usuarios** (+0,55 entre componentes; +0,61 a +0,65 entre variables). Se mantiene en toda la historia y en canary, pero desaparece al controlar por la cantidad de personas: describe el tamaño de la comunidad, no la calidad del proceso.

## 8. Cambios respecto de la primera corrida del cruce

La primera corrida (23/10) se hizo antes de dos correcciones del código compartido:

| Qué cambió | Efecto |
|---|---|
| Se revirtió la regla del PCA que excluía variables casi constantes (moda > 80 %) en los releases del PCA | El PCA de Proceso pasa de 4 a 5 componentes, igual que en el informe de Proceso |
| El diccionario asigna Wiki Presence a Proceso (el que estaba en `analisis` era anterior a ese cambio) | Proceso pasa de 11 a 12 variables. Wiki Presence no aporta pares robustos |
| Se usan solo los componentes interpretados de Proceso (CP1, CP2 y CP5) | Desaparecen pares contra "README y backlog", como Contribution Diversity share ↔ CP3, que no se repetía en canary |

El cruce de variables no cambió (los mismos 18 patrones). La correlación canónica pasa de +0,63 a +0,59, y sin Volumen de +0,43 a +0,42. Las conclusiones son las mismas.

## 9. Advertencias

- **DIS** tiene datos en 132 de 271 releases estables y puede contar como de documentación etiquetas que contienen "doc" (por ejemplo, "Docker"). Sus pares van como indicio y queda afuera del PCA y de los métodos alternativos.
- **CFDR y NUB** solo tienen datos desde mediados de 2020. Además, NUB está inflado en 2025–2026: 39 ventanas cuentan como bug etiquetas como "Error Handling".
- **Los criterios del método son permisivos** en canary (mismo signo) y en el control por tamaño. Por eso este informe separa los patrones por solidez (sección 2). Es una decisión que conviene unificar en los tres cruces.
- **README Completeness y Wiki Presence** son escalones en el tiempo. Sus relaciones no se interpretan.
- **Skill Similarity** usa los lenguajes que cada persona tiene hoy, no en cada release.

## 10. Síntesis

- Persona y Proceso están **conectadas de forma moderada**. La correlación canónica entre sus componentes es +0,59 y se sostiene sin el efecto de escala (+0,42; en los dos casos p = 0,001).
- La conexión pasa por **un eje claro: la participación de las personas en el cierre de issues se mueve junto con la resolución de las issues nuevas**. Lo encuentran la correlación de a pares, el conjunto reducido, la CCA sobre todas las variables y el random forest. Resiste el control por tamaño y se repite en canary. Queda como tentativo hasta medir la superposición con Jarczyk (sección 7).
- La relación más fuerte entre las dos dimensiones (**participantes ↔ bugs de usuarios**) es de **escala** y no se interpreta como calidad.
- La **veteranía** del equipo, el patrón más fuerte dentro de Persona, **no se conecta de forma sólida con Proceso**: su relación con el Cierre de lo viejo es débil y no se repite en canary.

## Cómo se reproduce

```bash
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_diccionario.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_pca.py Proceso
POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruce_dimensiones.py Persona Proceso --config analisis/cruces/persona_proceso.json
python3 analisis/reporte_cruce_dimensiones.py Persona Proceso
POSTGRES_DB=resultados_metricas_fixes python3 analisis/cruce_alternativos.py Persona Proceso --config analisis/cruces/persona_proceso.json
```

La prueba de sensibilidad sin Volumen usa `analisis/cruces/persona_proceso_sin_volumen.json`, y sus resultados están en `analisis/salidas/cruces/persona_proceso_sin_volumen/`. El PCA de Persona es el de la segunda corrida (`analisis/salidas/pca/pca_persona.json`).