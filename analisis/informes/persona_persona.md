---
cruce: Persona-Persona
titulo: Análisis de la dimensión Persona
subtitulo: Correlaciones y componentes principales entre métricas de la misma dimensión · next.js
---

## 1. Métricas de Persona

El análisis estudia las correlaciones entre métricas que caracterizan la actividad y la trayectoria de cada contribuyente, agregadas por release. Las definiciones salen del código de las métricas en este repositorio (`15/`, `18/`, `20/dc.py`, `38/`, `10/` y `16/`).

| Métrica | Qué mide / cómo se calcula |
|---|---|
| REXP (Recent Experience) | Suma de `1/(días hasta el cierre + 1)` sobre los commits del autor dentro de la ventana. Mide actividad reciente ponderada por cercanía al cierre, no experiencia; en el diccionario va en la familia **intensidad** (fix 23 de FIXES_METRICAS.md). |
| REXPRev (Recent Review Experience) | Suma de `1/(días hasta el cierre + 1)` sobre los eventos de revisión y discusión del autor en la ventana: issues y PRs abiertos y cerrados, comentarios en issues y comentarios de revisión de PRs. |
| EXPRev (Code Review Experience) | Suma, dentro de la ventana, de la actividad del autor: issues y PRs abiertos y cerrados, comentarios de issues y comentarios de revisión de PRs. |
| CDIV (Contribution Diversity) | Cantidad de archivos únicos del repositorio modificados por la persona dentro de la ventana. |
| ANMCC (Avg Modified Components per Commit) | Promedio de archivos modificados por commit no-merge del autor dentro de la ventana (fix 14: descarta merges y commits sin archivos; filtra bots). |
| LE (Learning Ease) | Para cada par (autor, componente) activo en la ventana, lapso en días entre la primera contribución **histórica** del autor a ese componente (viene del `git log` completo del runner local) y su última contribución dentro de la ventana. Promedio por autor sobre los pares activos. El "componente" es sub-proyecto en monorepos (p. ej. `packages/next`, `turbopack/crates/turbopack-core`). |
| FEXP (File Experience) | Para cada archivo tocado por un commit del autor en la ventana, cantidad de commits previos del mismo autor sobre ese archivo. **Promedio por commit del autor en la ventana** (no suma; `15/fexp.py:95` divide por la cantidad de commits del autor). |
| NC (Number of Comments) | Cantidad de comentarios escritos por la persona dentro de la ventana en issues y PRs, en commits y en revisiones de PRs. |
| NCI (Number of Closed Issues) | Cantidad de issues cerradas por la persona en la ventana, atribuidas al actor del `ClosedEvent`. Fix 16: excluye cierres sin actor y cierres por bots. |
| SC (Social Contribution) | Suma, por autor, de issues y PRs abiertos en la ventana más los que la misma persona cerró o mergeó dentro de la ventana (Falcão et al., 2020). Fix 20: cerrado/mergeado se cuenta solo si ocurrió antes del cierre de la ventana; antes usaba el estado de hoy. |
| SS (Skill Similarity) | Proporción de los lenguajes del repositorio (los que superan 0,1 % de los bytes del árbol al cierre de la ventana) que el autor también tiene en sus repos propios de GitHub. Ratio de 0 a 1; mide afinidad técnica con el stack, no cantidad de lenguajes conocidos. |
| Disc. Centrality | Grado del autor en la red social de discusión (MBSN) de la ventana: cantidad de otras personas con las que compartió al menos un hilo de issue, PR o commit mediante comentarios. Los bots se excluyen antes de armar el grafo. |
| Development Experience (`dev_exp`) | Meses desde el primer commit del autor en la rama principal del repositorio hasta el fin de la ventana (`días / 30.44`). En el agregado por release se restringe a quienes además tienen `anmcc` en la misma ventana. |
| MTTR (Mean Time to Repair) | Horas promedio entre apertura y cierre de las issues cerradas por el autor en la ventana. Excluye autocierres (quien cerró es quien abrió). Fix 16: no cuenta cierres por bots ni sin actor. |
| DIS (Doc Issue Survival) | Días entre apertura y cierre de issues de documentación cerradas por el autor en la ventana. |
| Activos (`activos_cierre`, `activos_comentarios`, `activos_commits`, `activos_interaccion`) | Cantidad de identidades canonizadas únicas que participaron en cada tipo de actividad en la ventana (ver §9 sobre identidades). |
| Nuevos contribuyentes (`nuevos_commits`, `nuevos_interaccion`) | Personas que participaron por primera vez en ese tipo de actividad en la ventana. |
| Proporciones (`prop_commitean`, `prop_cierran`, `prop_comentan`) | **Cociente de dos conteos** por release: `activos_commits / activos_interaccion`, `activos_cierre / activos_interaccion`, `activos_comentarios / activos_interaccion`. No se verifica que el numerador sea subconjunto del denominador; vacío cuando el denominador es 0. Como son cocientes independientes, pueden dar >1: `prop_commitean` lo hace en 12 de 4 002 ventanas y `prop_comentan` en 23 de 4 002. |
| Tasas de ingreso (`tasa_nuevos_commits`, `tasa_nuevos_interaccion`) | `nuevos_commits / activos_commits` y `nuevos_interaccion / activos_interaccion` por release. Vacío cuando el denominador es 0. |

## 2. Variables analizadas

Cada métrica se puede ver desde dos ángulos: la distribución de sus valores entre los contribuyentes de un release, o la cantidad de personas que participan. Para captar ambos, se calcularon:

- **Mediana** del valor por autor en el release.
- **p90** del valor por autor.
- **Share del top 10 %**: qué parte del total acumulado aporta el 10 % que más aporta.
- **Conteo** de identidades canonizadas únicas (activos y nuevos).
- **Ratio** de dos conteos (proporciones y tasas).

Se excluyen cuatro variables porque su valor modal se repite en más del 80 % de los releases (`pct_moda` del diccionario mide el porcentaje de **releases** que valen la moda, no el porcentaje de contribuyentes con un valor fijo). En las cuatro, la moda es 0: la mediana por autor en una ventana es 0 porque la mayoría de los contribuyentes activos no acumula actividad de ese tipo en la ventana.

- `exprev_mediana`: pct_moda = 93,4 %.
- `fexp_mediana`: pct_moda = 93,4 %.
- `nc_mediana`: pct_moda = 96,3 %.
- `nci_mediana`: pct_moda = 93,3 %.

Quedan **37 variables incluidas** (`diccionario_variables.csv`). Por familia (columna `familia`):

- **Tamaño (6):** `activos_cierre_conteo`, `activos_comentarios_conteo`, `activos_commits_conteo`, `activos_interaccion_conteo`, `nuevos_commits_conteo`, `nuevos_interaccion_conteo`.
- **Intensidad (12):** `dloc_p90`, `dloc_share_top10pct`, `exprev_p90`, `exprev_share_top10pct`, `nc_p90`, `nc_share_top10pct`, `nci_p90`, `nci_share_top10pct`, `rexp_mediana`, `rexprev_mediana`, `sc_p90`, `sc_share_top10pct`.
- **Composición (8):** `dev_exp_mediana`, `le_mediana`, `prop_cierran_ratio`, `prop_comentan_ratio`, `prop_commitean_ratio`, `ss_mediana`, `tasa_nuevos_commits_ratio`, `tasa_nuevos_interaccion_ratio`.
- **Amplitud (4):** `anmcc_mediana`, `cdiv_mediana`, `cdiv_p90`, `cdiv_share_top10pct`.
- **Red (1):** `disc_centrality_mediana`.
- **Otra (6):** `cd_mediana`, `dis_mediana`, `dloc_mediana`, `mttr_mediana`, `rc_mediana`, `sc_mediana`.

`dis_mediana` entra al cruce de correlaciones (n_estable = 132) pero se excluye del PCA por insuficientes releases con dato (49 % de ventanas con dato en estable).

## 3. Pares analizados

Combinando las 37 variables de a dos se obtienen **666 pares**. Se excluyen **40 pares de control**, que comparan una misma métrica calculada con distintos estadísticos (por ejemplo, p90 y share_top10pct de CDIV). Quedan **626 pares evaluados**.

[[grafico kpis]]

El mapa de calor muestra la correlación de cada par (las celdas vacías son la diagonal). Con el selector se puede ver la correlación corregida o la cruda:

[[grafico mapa]]

**Por qué el mapa crudo se ve más intenso.** Si dos métricas crecen a lo largo de la historia del proyecto, la correlación cruda las muestra relacionadas solo por esa tendencia común. La corregida la descuenta y mide si se mueven juntas de un release a otro.

- **La mayoría de las relaciones se debilitan al corregir** cuando las dos variables tienen tendencias de largo plazo del mismo signo (`rho_tiempo` en el diccionario). Ejemplo: `activos_comentarios ↔ nuevos_interaccion` pasa de +0,98 cruda a +0,92 corregida, y `anmcc ↔ cdiv` de +0,91 a +0,84.
- **Algunas se hacen más fuertes al corregir** cuando las dos variables tienen tendencias de largo plazo o dependencias de la duración de la ventana con **signos opuestos**: ese sentido contrario amortigua o invierte la cruda, y la corregida descuenta ambos efectos y hace emerger la asociación entre las desviaciones. Ejemplo: `nuevos_commits ↔ prop_commitean` pasa de −0,05 cruda a +0,51 corregida. En el diccionario, `nuevos_commits` tiene `rho_tiempo = −0,27` y `prop_commitean` tiene `rho_tiempo = +0,17`; su dependencia con la duración es +0,76 y −0,28, respectivamente.

## 4. Datos utilizados

- **Unidad de análisis:** la ventana entre un release estable y el siguiente. Son **271 ventanas** estables (todas con `parametros.absorbidas` presente, es decir con las ventanas de los fixes 1 y 2 ya aplicadas).
- **Datos faltantes:** cada par usa solo las ventanas donde las dos variables tienen dato. En `n_estable` del diccionario: la mayoría cubre las 271 ventanas, excepciones son `dis_mediana` (132), `dev_exp_mediana` (271), `mttr_mediana` (269), `rc_mediana` (267), `dloc_*` (270), `activos_cierre_conteo` (270).
- **Réplica:** los **3 785 releases canary** se usan para verificar si los resultados se repiten en otra serie de datos.

## 5. Tipos de correlación calculados

Para cada par se calcularon las siguientes correlaciones:

1. **Correlación cruda.** Spearman directo entre las dos variables, sin corrección.
2. **Correlación corregida lineal.** Descuenta el tiempo (modelado como una recta sobre el orden de los releases) y la duración de la ventana. Se usa solo como referencia.
3. **Correlación corregida (análisis principal).** Descuenta el crecimiento del proyecto y la duración de la ventana:
   1. Se pasan a rangos las dos variables y la duración de la ventana.
   2. Para cada variable se estima qué parte de su valor se explica por el momento del proyecto (curva suave sobre el orden de los releases) y la duración de la ventana.
   3. A cada release se le resta lo que predice esa regla; queda lo que la variable tiene de más o de menos respecto de lo esperable.
   4. Se correlacionan esas diferencias entre las dos variables.

>> El efecto de la corrección se ve comparando, para cada par, la correlación cruda con la corregida:
>>
>> [[grafico cruda_corregida]]

4. **Correlación corregida por tamaño.** Agrega al descuento anterior la cantidad de **personas activas en interacción** en el release. No se aplica a pares que incluyen una variable de la familia tamaño (está excluida del cálculo por diseño, dado que mide justamente la cantidad de participantes).

**Releases independientes.** Como los releases consecutivos se parecen entre sí, los datos contienen menos información independiente que la cantidad de releases. El número efectivo de releases independientes se usa para calcular el p-valor y el intervalo de confianza.

**Correlación por período.** La corregida se calcula también por separado en cuatro períodos (2016–19, 2020–22, 2023–24 y 2025–26) para evaluar estabilidad en el tiempo.

## 6. Clasificación de los resultados

La clasificación se basa en la correlación corregida.

**Significancia.** Se calculan un p-valor y un intervalo de confianza a partir del número efectivo de releases independientes. El p-valor se ajusta por comparaciones múltiples (Benjamini–Hochberg) dentro del cruce Persona–Persona.

**Categoría:**

- **Positiva o negativa:** significativa (p ajustado < 0,05).
- **Sin relación:** todo el intervalo de confianza queda entre −0,2 y 0,2.
- **No concluyente:** ni significativa ni "sin relación".

**Fuerza:** débil (0,1 a 0,3), moderada (0,3 a 0,5) o fuerte (más de 0,5), en valor absoluto.

**Estabilidad en el tiempo:** mismo signo que la correlación global en todos los períodos con dato, al menos tres períodos evaluables.

[[grafico categorias]]

[[grafico embudo]]

## 7. Relaciones robustas

Una relación es **robusta** cuando:

1. Es significativa (categoría positiva o negativa).
2. Es estable en el tiempo.
3. Se repite en los releases canary: calculada sobre canary, tiene el mismo signo que sobre estables.

### 7.1 Tabla y gráficos generales

Se identificaron **88 relaciones robustas**. Confirmado contra `generar_correlaciones.py:452` (`es_robusta`), son cuatro condiciones:

1. Categoría positiva o negativa (significativa tras BH).
2. Estable: mismo signo que la correlación global en todos los períodos con dato (al menos tres períodos evaluables).
3. Mismo signo en los releases canary (si `rho_canary` existe; cuando no, la condición se da por cumplida — ver §9).
4. No depende de ventanas de menos de un día: al recalcular sin esas ventanas, la correlación mantiene el signo y |ρ| ≥ 0,1.

Al hacer clic en una fila, el análisis particular se muestra en 7.2:

[[explorador robustas tabla]]

**Control por tamaño.** Una relación robusta lo resiste si, al descontar también la cantidad de personas activas, su correlación mantiene el signo y un valor absoluto ≥ 0,1. Las 88 se dividen así:

- **44 pasan** el control (|ρ con control| ≥ 0,1 y mismo signo).
- **1 falla**: `disc_centrality_mediana ↔ prop_comentan_ratio` (ρ corregida 0,17 cae a 0,09 con el control por tamaño).
- **43 no aplica** porque incluyen al menos una variable de la familia tamaño, que está excluida del cálculo por diseño.

### 7.2 Análisis particular

[[explorador robustas detalle]]

[[nota activos_comentarios_conteo nuevos_interaccion_conteo; activos_cierre_conteo nuevos_interaccion_conteo; activos_cierre_conteo activos_comentarios_conteo]]
**Qué muestran los datos** (`activos_comentarios ↔ nuevos_interaccion`, `activos_cierre ↔ activos_comentarios`, `activos_cierre ↔ nuevos_interaccion`):

- Son las relaciones más fuertes del bloque: ρ corregida +0,92, +0,69 y +0,62.
- Períodos para `activos_comentarios ↔ nuevos_interaccion`: 2016–19 = +0,81; 2020–22 = +0,90; 2023–24 = +0,95; 2025–26 = +0,76. Canary +0,73.
- **Las tres relaciones son en parte por construcción.** Un contribuyente que participa por primera vez en interacción en una ventana (nuevo) también entra como activo de interacción en esa misma ventana (`export_persona.py`, pseudo-métricas). Lo mismo pasa entre los distintos tipos de activos: el mismo conteo depende de contribuyentes que suelen participar en varios canales a la vez.
- **No aplica el control por tamaño** porque todas las variables están en la familia tamaño; ese control descuenta justamente lo que miden.

**Qué indica:** los releases con más actividad tienen más conteo en todos los subcanales. No se puede separar causalidad y parte de la asociación es definicional.
[[/nota]]

[[nota anmcc_mediana cdiv_mediana]]
**Qué muestran los datos** (`anmcc_mediana ↔ cdiv_mediana`):

- Relación más fuerte entre las que resisten el control por tamaño: ρ corregida +0,84, ρ con control +0,83.
- Períodos: 2016–19 = +0,73; 2020–22 = +0,89; 2023–24 = +0,86; 2025–26 = +0,75. Canary +0,91.
- **Solapamiento de definición** (flag `solapamiento_definicion = True` en `pares_correlacion.csv`): ANMCC cuenta el promedio de archivos por commit del autor en la ventana; CDIV cuenta los archivos únicos del autor en la ventana. Un autor que toca muchos archivos por commit también tiende a cubrir más archivos distintos. La correlación es alta por construcción.

**Qué indica:** las dos métricas capturan amplitud de los cambios desde ángulos muy cercanos. En el PCA aparecen juntas en el componente de experiencia y veteranía.
[[/nota]]

[[nota dev_exp_mediana le_mediana; dev_exp_mediana tasa_nuevos_commits_ratio; dev_exp_mediana nuevos_commits_conteo]]
**Qué muestran los datos** (`dev_exp ↔ LE`, `dev_exp ↔ tasa_nuevos_commits`, `dev_exp ↔ nuevos_commits`):

| par | ρ corregida | ρ con tamaño | canary | 16–19 | 20–22 | 23–24 | 25–26 |
|---|---|---|---|---|---|---|---|
| dev_exp ↔ le_mediana | +0,74 | +0,73 | +0,72 | +0,69 | +0,70 | +0,75 | +0,59 |
| dev_exp ↔ tasa_nuevos_commits | −0,71 | −0,71 | −0,45 | −0,58 | −0,56 | −0,76 | −0,55 |
| dev_exp ↔ nuevos_commits | −0,63 | — | −0,45 | −0,51 | −0,51 | −0,70 | −0,51 |

- **`dev_exp ↔ le_mediana`** comparten parcialmente la definición (flag `solapamiento_definicion = True`): LE se apoya en la primera contribución histórica del autor a cada componente (toma `datetime` muy cercano al primer commit general); dev_exp es meses desde el primer commit en la rama principal. Un autor de larga trayectoria tiene las dos altas.
- **`dev_exp ↔ nuevos_commits`** también está marcada con `solapamiento_definicion = True`: los nuevos committers tienen dev_exp cercano a 0 por definición (son recién llegados), y bajan la mediana del release.
- **`dev_exp ↔ tasa_nuevos_commits`** es la relación entre composición y renovación: cuanto más alta la tasa de ingreso, más baja la mediana de dev_exp. Resiste el control por tamaño (−0,71).
- **En canary las magnitudes bajan** (−0,45 vs −0,71 y −0,45 vs −0,63): las ventanas canary son mucho más cortas (mediana de medio día) y hay más ruido en el agregado por release.

**Qué indica:** `dev_exp`, `le_mediana`, `nuevos_commits` y `tasa_nuevos_commits` miden la mezcla veteranos/nuevos desde ángulos relacionados. Buena parte de la asociación es construccional (nuevos committers tienen dev_exp bajo).
[[/nota]]

[[nota le_mediana tasa_nuevos_commits_ratio; le_mediana nuevos_commits_conteo]]
**Qué muestran los datos** (`LE ↔ tasa_nuevos_commits`, `LE ↔ nuevos_commits`):

- `LE ↔ tasa_nuevos_commits`: ρ corregida −0,73, resiste tamaño (−0,72), canary −0,45. Períodos: −0,60 / −0,67 / −0,82 / −0,64.
- `LE ↔ nuevos_commits`: ρ corregida −0,68 (no se aplica control por tamaño porque `nuevos_commits` es de familia tamaño), canary −0,46.
- **`LE ↔ nuevos_commits`** tiene `solapamiento_definicion = True`: LE promedia días desde la primera contribución a cada componente, y un nuevo committer tiene valores cercanos a 0 por definición, así que empujan la mediana hacia abajo.

**Qué indica:** cuando entra mucha gente nueva, el contribuyente del medio tiene menos tiempo en los componentes que toca. Es la misma mezcla que captura `dev_exp ↔ renovación`.
[[/nota]]

[[nota exprev_share_top10pct prop_commitean_ratio; nc_share_top10pct prop_commitean_ratio; prop_commitean_ratio sc_p90]]
**Qué muestran los datos** (concentración del núcleo activo y proporción que commitea):

- `exprev_share_top10pct ↔ prop_commitean`: ρ corregida +0,47, ρ con control +0,45; períodos 0,47 / 0,54 / 0,56 / 0,37. Canary +0,34.
- `nc_share_top10pct ↔ prop_commitean`: ρ corregida +0,44, ρ con control +0,42; canary +0,13.
- `prop_commitean ↔ sc_p90`: ρ corregida +0,47, ρ con control +0,45; canary +0,17.

**Interpretación:** en los releases donde la actividad (revisiones, comentarios, contribución social) está más concentrada en el 10 % más activo, también hay mayor proporción de los que interactúan que además commitea. **No implica causalidad**: tanto la concentración como la proporción de committers pueden ser consecuencias del nivel de actividad del período. La asociación resiste el control por tamaño, así que no se explica por la cantidad de participantes.
[[/nota]]

## 8. Relaciones significativas

Una relación es **significativa** cuando su categoría es positiva o negativa: el p-valor ajustado por comparaciones múltiples es menor a 0,05.

### 8.1 Tabla y gráficos generales

Los 626 pares evaluados se distribuyen así: 234 sin relación, 226 no concluyentes, **101 positivas**, **65 negativas**. Hay 166 relaciones significativas en total.

La red resume las relaciones significativas:

[[grafico red | chico]]

[[explorador significativas tabla | direccion]]

**Observaciones:**

- La mayoría de las positivas vinculan variables de la misma familia (tamaño con tamaño, amplitud con amplitud, intensidad con intensidad). Tienen sentido por construcción.
- Las negativas más fuertes oponen composición (medianas de LE y dev_exp) a tamaño o a tasas de ingreso.
- Cinco pares robustos tienen `solapamiento_definicion = True`: `anmcc_mediana ↔ cdiv_mediana`, `anmcc_mediana ↔ cdiv_p90`, `dev_exp_mediana ↔ le_mediana`, `le_mediana ↔ nuevos_commits_conteo`, `rexp_mediana ↔ rexprev_mediana`. Las correlaciones altas son esperadas por construcción, no son hallazgos independientes.

[[grafico forest]]

**Estabilidad de las relaciones significativas por período:**

[[grafico estabilidad]]

### 8.2 Análisis particular

[[explorador significativas detalle]]

## 9. Advertencias sobre los datos de Persona

- **Identidades: nombres de git vs. logins.** Las métricas que corre `run_versiones_local.py` (anmcc, cdiv, fexp, le, rexp, cd, dloc, rc, loc_notion, commits_doc, dloc_flujo, developer_ownership_notion) atribuyen por el nombre git del autor (`%an`); las de la API (nc, exprev, rexprev, disc_centrality, sc, nci, mttr, dis, ss, dev_exp) atribuyen por el login de GitHub. Los conteos de activos y nuevos de cada canal se calculan por separado (no requerían cruzar identidades entre canales), pero el **filtro de dev_exp con anmcc** (ambas métricas por persona, cruzadas por igualdad exacta) y la **unión de cuentas_por_tipo** (anmcc ∪ exprev) sí dependían de que la misma persona tuviera la misma identidad en las dos fuentes. El análisis actual usa la tabla `db/identidades_git.csv` para canonizar nombre git → login en las métricas del runner local (y en dev_exp cuando la identidad no parece un login). Cobertura: 3 830 identidades (95,1 %) / 35 306 commits (98,1 %) resueltos; 19 ambiguos quedan sin traducir. Ver §11.
- **68 logins con varios nombres de git mapeados al mismo login** (`JJ Kasper`+`jj@jjsweb.site` → ijjk; `Donny/강동윤`+`강동윤` → kdy1; `Henrik Wenz`+`HaNdTriX`+`Henrik` → handtrix; etc.); de ellos, 34 personas tienen al menos dos identidades crudas que efectivamente colisionan en alguna ventana del seed. Para unificarlas por release se aplica una regla por métrica: suma en `dloc` y `rexp` (aditivas por autor), max en `dev_exp` (primer commit más antiguo), max n_commits en `anmcc`, `cdiv`, `le`, `fexp`, `cd` (no combinables sin recalcular desde los commits). Impacto medido: Δ mediana 0–7 % en la mayoría de las ventanas con colisión, 50–100 % en pocos outliers; Δ share_top10pct hasta 0,25 en casos puntuales. Casos registrados en `persona_duplicados_canon.csv`.
- **SS es un snapshot actual.** `/users/{login}/repos` se consulta una vez por login; `user_languages` no refleja cambios históricos en la configuración de repos propios del contribuyente. La composición del repositorio objetivo (`repo_languages`) sí se recalcula en el commit vigente al cierre de la ventana.
- **dev_exp cubre las 271 ventanas estables** (`n_estable = 271` en el diccionario). Con el alias validado, el filtro por anmcc en el agregado tiene **intersección en 271 de 271 ventanas** (100 %); en canary la cobertura del agregado es `n_canary = 3 628` de 3 785 ventanas (96 %, antes del alias era 20,7 %).
- **DIS tiene n_estable = 132** (`diccionario_variables.csv`). Se usa en correlaciones y se excluye del PCA porque solo cubre el 49 % de las ventanas estables, por debajo del umbral de dato completo del PCA.
- **`disc_centrality_mediana` toma el mismo valor en el 70,8 % de los releases.** Está sobre el umbral de exclusión (pct_moda < 80 %) pero muy cerca. Interpretarla con cuidado: la mediana queda definida por los contribuyentes periféricos de cada ventana.
- **RC es casi una variable escalonada.** Con el fix 11 (solo el README de la raíz, siguiendo el enlace simbólico), `rc_producto` toma 3 valores distintos: 1,0 en 161 ventanas, 0,857 en 87, 0,714 en 19. Las 19 ventanas con RC = 0,714 son dos tramos contiguos de la línea principal (no backports): v9.1.7 a v9.4.2 (14 ventanas, 2020-01-03 a 2020-05-28) y v12.2.0 a v12.2.4 (5 ventanas, 2022-06-28 a 2022-08-12). En el PCA, `rc_mediana` carga fuerte en CP6 (+0,74), que es inestable en el bootstrap (q05 = 0,31): parte de la "información" de CP6 son esos tres escalones.
- **`activos_cierre_conteo` cubre 270 de 271 ventanas**. La ventana faltante es `v16.2.5` (periodo_num = 256), que no tiene ningún contribuyente con `nci` por persona en el seed.
- **WP (Wiki Presence) y NOB (Number of Branches) no entran al cruce Persona.** Están marcadas con `dim_persona = 0` en el diccionario (solo producto).
- **`sc_disc` (variante de SC a nivel discussion)** existe en la base pero no está mapeada a una variable del diccionario; no entra al análisis.
- **Las proporciones son cocientes de conteos independientes.** `prop_commitean`, `prop_cierran` y `prop_comentan` dividen dos conteos por release sin verificar que el numerador sea subconjunto del denominador. Pueden dar valores >1 cuando hay más personas de un canal que del denominador: `prop_commitean` en 12 de 4 002 ventanas, `prop_comentan` en 23 de 4 002.
- **`replica_en_canary` devuelve True cuando `rho_canary` es NaN** (`analisis/generar_correlaciones.py:435`). En este cruce, 0 de las 88 relaciones robustas pasan por ese atajo: todas tienen dato en canary. Ver §11 para la diferencia con el análisis original.
- **Réplica solo por signo con una correlación casi nula en canary.** `replica_en_canary` acepta cualquier `rho_canary` con el mismo signo que `rho_corregida`, sin exigir magnitud. **12 de las 88 robustas tienen |rho_canary| < 0,1** (réplica solo por signo): `cdiv_p90 ↔ tasa_nuevos_commits_ratio` (−0,003), `prop_cierran ↔ sc_p90` (0,005), `dloc_mediana ↔ prop_cierran` (−0,011), `nc_share_top10pct ↔ rexprev_mediana` (0,015), `dev_exp ↔ mttr_mediana` (−0,020), `cdiv_p90 ↔ sc_share_top10pct` (0,044), `nc_share_top10pct ↔ prop_cierran` (0,046), `dis_mediana ↔ rexp_mediana` (0,066), `rexprev_mediana ↔ sc_p90` (0,086), `cdiv_mediana ↔ nuevos_interaccion` (−0,089), `activos_comentarios ↔ nc_share_top10pct` (−0,092), `activos_comentarios ↔ cdiv_mediana` (−0,093). `pares_correlacion.csv` no guarda el intervalo de confianza de canary, así que no se puede contar directamente en cuántas incluye el 0; con `|rho_canary|` tan chico es esperable que el 0 esté dentro en varias.

## 10. Componentes principales

El análisis de componentes principales (PCA) reduce las 37 variables de Persona (36 en la práctica, excluyendo `dis_mediana`) a un conjunto menor de componentes que conserva la mayor parte de la variación.

### 10.1 Cómo se calcularon

- **Matriz de datos:** una fila por release y una columna por variable. Se usan **265 releases estables** con dato completo en las 36 variables incluidas, desde 2016 hasta 2026. Antes del PCA se aplica `excluir_backports()` (`analisis/generar_pca.py`) por consistencia con el pipeline general. Con las ventanas nuevas (fix 1 y fix 4) ya no quedan backports para excluir; el JSON reporta `backports = 0` en los seis resultados.
- **Escala por rangos:** cada variable se reemplaza por su posición de menor a mayor y se estandariza (mismo criterio que la correlación de Spearman).
- **Tres enfoques:**
  - Crudo: los rangos tal cual.
  - Ajustado: a cada rango se le descuenta la tendencia de largo plazo y la duración de la ventana.
  - Ajustado y sin tamaño: además descuenta la cantidad de personas activas en interacción.

### 10.2 Cuántos componentes se retienen

Cuatro criterios: Kaiser (autovalor > 1), codo del scree, varianza acumulada (70 % y 80 %) y análisis paralelo de Horn (criterio principal, único que separa componente real del ruido).

[[pca screes todas estable ajustado]]

[[pca criterios todas]]

Con 36 variables en la serie estable ajustada:

- **Horn retiene 7 componentes.** Los primeros autovalores (6,00, 4,83, 3,14, 2,29, 1,91, 1,61, 1,47) superan al 95 % de lo que produce el azar (2,01, 1,86, 1,76, 1,67, 1,60, 1,54, 1,48).
- Kaiser pide 12 (muchos autovalores apenas superan 1); varianza acumulada necesita 11 para el 70 % y 15 para el 80 %. Como el PCA explica solo el 59 % con 7 componentes, Horn termina siendo el criterio principal porque es el único que prueba que el componente no sea ruido.
- **Canary** retiene 11 (con 2 400 releases, el umbral del azar es más bajo y se detecta más estructura). En canary el PCA excluye solo `dis_mediana` (n_canary = 509 de 3 785); `dev_exp_mediana` sí entra (n_canary = 3 628, 96 %). Quedan 36 variables.
- **Muestra del PCA menor que total de ventanas.** De 271 ventanas en estable y 3 785 en canary, el PCA usa 265 y 2 400 porque exige dato completo en las 36 variables incluidas. Las ventanas restantes tienen algún faltante.

### 10.3 Componentes identificados

Los porcentajes citados por componente son de la **varianza rotada** (suma de cargas al cuadrado / número de variables), que suele diferir de los autovalores sin rotar. El PCA explica el 59 % de la variación con 7 componentes.

[[pca cargas todas estable ajustado]]

1. **CP1 · Veteranía frente a renovación (14,1 %).** `le_mediana` (+0,85), `nuevos_commits_conteo` (−0,84), `tasa_nuevos_commits_ratio` (−0,84), `dev_exp_mediana` (+0,78), `cdiv_mediana` (+0,65), `anmcc_mediana` (+0,64), `activos_commits_conteo` (−0,62), `prop_commitean_ratio` (−0,47). Agrupa variables que miden tiempo del contribuyente típico en el proyecto (dev_exp, LE) y amplitud de los cambios (CDIV, ANMCC), opuestas a la entrada de nuevos committers.

2. **CP2 · Volumen de participación (11,7 %).** `activos_comentarios_conteo` (+0,92), `activos_interaccion_conteo` (+0,91), `nuevos_interaccion_conteo` (+0,88), `activos_cierre_conteo` (+0,81), `activos_commits_conteo` (+0,46), `disc_centrality_mediana` (+0,41), `prop_comentan_ratio` (+0,40), `nuevos_commits_conteo` (+0,33). Captura cuánta gente participó en el release. Al descontar la cantidad de personas activas en interacción (enfoque sin tamaño), este componente cae a congruencia 0,34, lo esperable dado que mide justamente ese volumen.

3. **CP3 · Concentración del núcleo activo (9,8 %).** `exprev_share_top10pct` (+0,89), `nc_share_top10pct` (+0,80), `sc_share_top10pct` (+0,75), `sc_p90` (+0,61), `cdiv_p90` (+0,51), `nci_p90` (+0,46), `prop_commitean_ratio` (+0,40), `sc_mediana` (+0,35). Alto cuando pocos acaparan más revisiones, comentarios y contribución social.

4. **CP4 · Volumen de actividad del percentil alto (8,5 %).** `exprev_p90` (+0,84), `nc_p90` (+0,78), `prop_cierran_ratio` (+0,53), `rexprev_mediana` (+0,53), `prop_commitean_ratio` (+0,51), `sc_p90` (+0,39). Distinto de la concentración (CP3): mide **cuánto** acumulan los más activos, no qué proporción del total.

5. **CP5 (5,3 %) — tentativo.** `dloc_mediana` (+0,69), `disc_centrality_mediana` (+0,56), `tasa_nuevos_interaccion_ratio` (+0,50), `dloc_share_top10pct` (−0,47), `prop_cierran_ratio` (−0,39), `cd_mediana` (−0,33). Bootstrap q05 = 0,19; no se interpreta.

6. **CP6 (4,9 %) — tentativo.** `dloc_p90` (+0,74), `rc_mediana` (+0,74), `nci_share_top10pct` (+0,44), `cd_mediana` (−0,37). Bootstrap q05 = 0,31; parte de la "información" viene de los tres escalones de RC (§9). No se interpreta.

7. **CP7 (4,6 %) — tentativo.** `rexp_mediana` (+0,59), `cdiv_share_top10pct` (−0,55), `cdiv_mediana` (+0,48), `ss_mediana` (−0,45), `mttr_mediana` (+0,40), `anmcc_mediana` (+0,34). Bootstrap q05 = 0,27; no se interpreta.

[[pca puntajes todas estable ajustado]]

### 10.4 Solidez y consistencia de los resultados

**Bootstrap de bloques.** Se remuestrearon los datos 500 veces en bloques de releases consecutivos y se midió la congruencia de Tucker de cada componente contra el original. La leyenda de solidez usa los mismos umbrales que la comparación entre series: ≥ 0,95 es el mismo componente, entre 0,85 y 0,95 es parecido, por debajo de 0,85 es distinto.

[[pca solidez todas estable ajustado]]

| componente | mediana | q05 | lectura |
|---|---|---|---|
| CP1 | 0,974 | 0,909 | estable en mediana y q05 |
| CP2 | 0,971 | 0,928 | estable en mediana y q05 |
| CP3 | 0,959 | 0,779 | estable en la mediana; q05 por debajo de 0,85 |
| CP4 | 0,947 | 0,835 | estable en la mediana; q05 justo por debajo de 0,85 |
| CP5 | 0,627 | 0,192 | tentativo |
| CP6 | 0,760 | 0,314 | tentativo |
| CP7 | 0,653 | 0,274 | tentativo |

Horn retiene 7 pero el bootstrap muestra que **CP1 y CP2 son estables en mediana y q05**, **CP3 y CP4 son estables en la mediana pero su q05 queda por debajo de 0,85** (en el 5 % de los peores remuestreos el componente ya no se parece). CP5 a CP7 varían entre remuestreos y no se interpretan.

**Consistencia entre enfoques y series.**

[[pca comparacion todas]]

La comparación recalcula la solución de cada enfoque/serie con `k = 7` (el `k` de estable ajustado, no el que elegiría cada caso por su cuenta) y empareja componentes por **mejor coincidencia de Tucker** usando asignación óptima (`linear_sum_assignment` sobre `|tucker|`). Es decir: en canary, que tendría `k = 11` por su cuenta, se fuerza una solución de 7 componentes antes de emparejar. Los números no comparan los 11 CPs de canary contra los 7 de estable.

- **Estable sin tamaño:** CP2 cae a 0,34 (lógico: ese enfoque descuenta la cantidad de personas activas y CP2 es exactamente eso). CP1, CP3, CP4, CP5, CP6 y CP7 mantienen congruencia 0,99, 0,99, 0,99, 0,99, 0,99 y 0,96.
- **Estable crudo:** congruencias 0,77 / 0,80 / 0,83 / 0,36 / 0,47 / 0,48 / 0,41. Sin la corrección por tiempo, los componentes se reordenan por tendencias temporales compartidas.
- **Canary ajustado:** CP1 = 0,87 (parecido), CP2 = 0,76 (distinto), CP3 = 0,76 (distinto), CP4 = 0,33 (no se replica), CP5 = 0,24, CP6 = 0,74, CP7 = 0,49.

### 10.5 Síntesis

Persona se resume en los primeros cuatro componentes:

1. CP1 · Veteranía frente a renovación (14,1 %).
2. CP2 · Volumen de participación (11,7 %).
3. CP3 · Concentración del núcleo activo (9,8 %).
4. CP4 · Volumen de actividad del percentil alto (8,5 %).

Los cuatro superan el umbral de Horn y son estables en la mediana del bootstrap. CP3 y CP4 lo son solo en la mediana (q05 por debajo de 0,85): su interpretación es menos firme. En canary, **CP1 se replica como "parecido"** (0,87); **CP2 y CP3 quedan como "distintos"** (0,76 cada uno) y **CP4 no se replica** (0,33). Los componentes 5 a 7 que Horn retiene no son reproducibles en el bootstrap y no deben interpretarse.

Para el cruce con otras dimensiones conviene usar estos cuatro componentes. Varias variables también están mapeadas a Proceso (CDIV, ANMCC, LE, SC, NC, NCI, EXPRev) y a Producto (ANMCC, LE, DLOC, CD, RC, MTTR); antes del cruce hay que acordar a qué dimensión se asigna cada variable compartida para no usar los mismos datos en ambos lados de la correlación.

El reporte interactivo del PCA, con todas las combinaciones de series y enfoques, está en el anexo.

## 11. Cambios respecto del análisis original

Este análisis se corre sobre `resultados_metricas_fixes`, la base corregida por los fixes de la rama `ine/fixes-metricas`.

### 11.1 Qué cambiaron los fixes (resumen de `FIXES_METRICAS.md`)

- **Fixes 1 y 2 · ventanas.** Backports (60 de 369 releases) y ventanas de menos de un día (88 de 369) dejan de cortar ventanas. Pasan de 371 a 271 ventanas estables en el seed.
- **Fix 3 · métricas de foto al cierre.** CD, DLOC, README Completeness, LOC y ownership se miden sobre la rama principal al cierre de la ventana, no en el tag del release.
- **Fixes 5 a 7 · métricas constantes.** NOB, Wiki Presence y Schedule Compliance ya no toman el estado de hoy.
- **Fixes 8 a 11 · métricas de foto del código.** `dloc_flujo` y `commits_doc` nuevas; DLOC cuenta `.mdx` y excluye `examples/`, tests y código generado; CD excluye código de terceros compilado; RC usa solo el README de la raíz.
- **Fixes 12 a 14 · valores 0 reemplazados por None cuando no hay datos.** MTTR, ANMCC, CD, README Completeness y DIS devuelven `None` cuando no observan.
- **Fixes 15 a 17 · bots.** `es_bot()` ahora también usa `bots_clasificados.csv`; todas las métricas filtran bots (incluidos los nombres git de bots de release).
- **Fixes 18 a 22 · issues y cierres.** MTTR excluye autocierres por persona; `mttr_bugs` y `mttr_p50` son nuevas; SC usa `closedAt` y `mergedAt` para contar cierre o merge dentro de la ventana; NUB y DIS normalizan etiquetas; CFDR usa el top 10 histórico, no el de hoy.
- **Fix 23 · definiciones.** REXP se cataloga como `intensidad` y la clase documenta que mide actividad reciente, no experiencia.

### 11.2 Comparación de correlaciones (`comparacion_persona_persona.md`)

Las categorías de Persona–Persona cambian así entre el análisis original y la corrida actual:

| Categoría | Antes | Después |
|---|---|---|
| positiva | 100 | 101 |
| negativa | 59 | 65 |
| sin relación | 278 | 234 |
| no concluyente | 157 | 226 |
| control | 36 | 40 |
| **robustas** | **94** | **88** |
| pares totales | 630 | 666 |

El total de pares crece (de 630 a 666) por las variables nuevas y por `sc_mediana` que dejó de ser constante. Las 94 robustas del original se descomponen así contra las 88 actuales: **66 se mantienen** y **28 se pierden**; además **22 aparecen** solo en la corrida actual. 66 + 28 = 94 (antes); 66 + 22 = 88 (después).

### 11.3 Identidades: el problema y su corrección

**Qué era.** Las métricas que corre `run_versiones_local.py` atribuyen por el nombre git del autor (`%an`); las de la API, por el login de GitHub. Después del fix 14 (ANMCC pasa a correr desde el runner local), `anmcc` también guarda nombres git. En `export_persona.py` dos puntos cruzaban identidades por igualdad exacta de `contribuyente_login` y se rompían con un contribuyente bajo dos formas:

- **Filtro de `dev_exp` con `anmcc`** (`EXISTS ... AND r2.contribuyente_login = r.contribuyente_login`, líneas 253 y 336): tras el fix 14, dev_exp seguía como login y anmcc pasaba a nombre git, así que la mayoría de los contribuyentes no cruzaba.
- **Unión `cuentas_por_tipo = anmcc ∪ exprev`** por release: la misma persona bajo `JJ Kasper` en anmcc y `ijjk` en exprev se contaba dos veces.

Los conteos de activos y nuevos de cada canal (`activos_commits`, `nuevos_commits`, `activos_interaccion`, …) **no cruzaban identidades entre métricas**: cada uno se calcula desde una sola métrica base (anmcc o exprev), así que no se rompían por el bug.

Para medir el impacto en dev_exp, dos chequeos distintos:

- **Intersección por identidades** (identidades únicas en toda la historia): `anmcc ∩ dev_exp` cayó de **97 %** en el análisis original (3 910 / 4 032 identidades, ambas en formato login) a **15 %** sin alias (605 / 3 996 identidades: dev_exp en login y anmcc en nombre git).
- **Intersección por ventana** (ventanas estables donde al menos un login cae en ambos conjuntos): **88,5 % en el original** (332 / 375 ventanas) → **77,5 % en fixes sin alias** (210 / 271) → **100 % con alias validado** (271 / 271).
- Con la intersección casi vacía, al agregado `dev_exp_mediana` solo le entraban los pocos contribuyentes cuyo nombre git casualmente respetaba el formato de login (típicamente nuevos sin cuenta vinculada), lo que sesgó la mediana por release hacia abajo (p50 global 0,46 meses en fixes sin alias contra 3,55 en el original).
- En consecuencia, en la primera versión de este informe aparecían caídas en los pares con `dev_exp`: `dev_exp ↔ le_mediana` iba de +0,78 a +0,28; `dev_exp ↔ nuevos_commits` de −0,66 a −0,25; `dev_exp ↔ tasa_nuevos_commits` de −0,67 a −0,32. **Eran un artefacto del cruce de identidades, no un resultado real de los fixes.**
- En canary, el análisis original **no tenía datos de dev_exp** (0 ventanas canary con dev_exp en la base original); por eso no había réplica contra la cual comparar. Con el alias validado, dev_exp canary tiene cobertura `n_canary = 3 628` (96 %).

**Cómo se corrigió.** Con `db/mapear_identidades.py` se construye una tabla `nombre_git → login` leyendo el clon local de next.js: emails `*@users.noreply.github.com` resuelven por el login del email; para el resto, GraphQL `object(oid:).author.user.login` con hasta 10 SHAs por nombre, consultando todos para detectar logins conflictivos. `export_persona.py` carga la tabla y aplica `canon(ident, metrica)` solo a las métricas del runner local y a `dev_exp` cuando la identidad no parece un login válido. Cobertura: 3 830 de 4 028 identidades (95,1 %); 35 306 de 35 980 commits (98,1 %); 19 ambiguos quedan afuera. Tras el alias, `dev_exp ∩ anmcc` recupera 100 % en estable y 96,1 % en canary; `dev_exp_mediana` en v15.0.0 vuelve a 29,2 meses.

**Nuevos_commits y la primera aparición.** La "primera fecha" por persona se calculaba agrupando por `contribuyente_login` crudo sobre `anmcc ∪ cdiv ∪ fexp ∪ rexp ∪ le`. En el original, anmcc venía por API con login y las otras cuatro por el runner local con nombre git, así que la misma persona tenía dos entradas en `pf_commits` y podía contar como "nueva" dos veces (al aparecer bajo cada identidad). Con el alias validado se consolidan en una sola primera aparición por canónico. En la práctica el efecto en los conteos actuales de `nuevos_commits` es chico (≤ 4 contribuyentes de caída en las ventanas afectadas, 3,4 % de ventanas).

**Limitaciones conocidas:**

- **Ambigüedades (19 nombres).** Nombres git usados por más de una persona en el repo: `Jimmy Lai` (feedthejim | timneutkens, 196 commits), `dan` (gaearon | gnoff, 48), `David Alexandru Ilie` (DavidIlie | timneutkens, 16), `Tom`, `Tim`, `Lucas Rosa`, `Alexander`, `Ryan`, `Flo`, `Alessandro`, `Ivan Kleshnin` y 8 más. Están en `db/identidades_ambiguas.csv` y no se traducen.
- **Revisión manual (383 entradas).** Nombres de pila cortos (275) y logins con 2+ nombres git disímiles (108), en `db/identidades_revisar.csv`.
- **68 logins con varios nombres git** mapeados al mismo canónico; de ellos **34 personas** tienen al menos 2 identidades crudas que efectivamente colisionan en alguna ventana del seed. Para unificar valores en la misma métrica/ventana se aplica una regla: suma en `dloc` y `rexp`, max en `dev_exp`, max n_commits en el resto. Impacto medido: Δ mediana 0–7 % en la mayoría de las ventanas con colisión; Δ share_top10pct hasta 0,25 en pocos outliers.

### 11.4 Las 5 robustas con dev_exp del original pasaron la réplica en canary sin datos

En `analisis/salidas_originales/pares_correlacion.csv`, las 5 relaciones robustas que incluyen `dev_exp_mediana` tienen **todas** `rho_canary` vacío: en la base original, `dev_exp` no se calculaba para canary (0 de 3 862 ventanas con dato). Pasaron el chequeo `replica_en_canary` por el atajo `return True si NaN` (`analisis/generar_correlaciones.py:435`), **sin evidencia real de réplica**.

| par del original | ρ corregida (orig) | rho_canary (orig) |
|---|---|---|
| activos_commits ↔ dev_exp | −0,42 | — |
| cdiv_mediana ↔ dev_exp | +0,36 | — |
| dev_exp ↔ le_mediana | +0,78 | — |
| dev_exp ↔ nuevos_commits | −0,66 | — |
| dev_exp ↔ tasa_nuevos_commits | −0,67 | — |

En la corrida actual (alias validado) las cinco se recalculan con `rho_canary` real (dev_exp canary tiene cobertura 96 % tras canonizar) y las cinco se mantienen robustas, en el mismo orden que la tabla:

| par | ρ corregida (actual) |
|---|---|
| activos_commits ↔ dev_exp | **−0,39** |
| cdiv_mediana ↔ dev_exp | **+0,41** |
| dev_exp ↔ le_mediana | **+0,74** |
| dev_exp ↔ nuevos_commits | **−0,63** |
| dev_exp ↔ tasa_nuevos_commits | **−0,71** |
