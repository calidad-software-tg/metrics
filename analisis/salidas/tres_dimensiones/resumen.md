# Análisis tridimensional

185 releases estables y 1827 canary con los siete componentes. Nula: 1000 corrimientos circulares de cada dimensión por separado (300 en canary).

## Componentes

| Componente | Dimensión | Variables que lo definen |
|---|---|---|
| persona_cp1 · renovación del equipo | Persona | nuevos_commits_conteo (+0.88), le_mediana (-0.85), tasa_nuevos_commits_ratio (+0.84), dev_exp_mediana (-0.78), activos_commits_conteo (+0.66), cdiv_mediana (-0.65), prop_commitean_ratio (+0.50), rexp_mediana (-0.49) |
| persona_cp2 · volumen de actividad | Persona | activos_comentarios_conteo (+0.91), activos_interaccion_conteo (+0.89), nuevos_interaccion_conteo (+0.87), activos_cierre_conteo (+0.81), disc_centrality_mediana (+0.48), prop_comentan_ratio (+0.44), activos_commits_conteo (+0.42) |
| persona_cp3 · concentración del núcleo | Persona | exprev_share_top10pct (+0.88), nc_share_top10pct (+0.80), sc_share_top10pct (+0.76), sc_p90 (+0.66), cdiv_p90 (+0.51), prop_commitean_ratio (+0.43) |
| proceso_cp2 · resolución de lo nuevo | Proceso | jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) |
| proceso_cp5 · cierre de lo viejo | Proceso | mttr_producto (+0.85), nci_producto (+0.74) |
| producto_cp1 · bugs de usuarios | Producto | cfdr_producto (+0.97), nub_producto (+0.97) |
| producto_cp4 · flujo de documentación | Producto | dloc_flujo_producto (+0.82), commits_doc_producto (+0.77), le_producto (-0.41) |

## 1. Medida global

| Variante | Serie | n | GCCA (1 a 3) | nula p95 | p | RV medio | nula p95 | p | MFA factor 1 | nula p95 | p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| todos | estable | 185 | 1.714 | 1.440 | 0.001 | 0.098 | 0.031 | 0.001 | 0.245 | 0.207 | 0.001 |
| todos | canary | 1827 | 1.630 | 1.124 | 0.003 | 0.066 | 0.003 | 0.003 | 0.229 | 0.163 | 0.003 |
| sin volumen | estable | 185 | 1.582 | 1.379 | 0.001 | 0.072 | 0.027 | 0.001 | 0.262 | 0.230 | 0.001 |
| sin volumen | canary | 1827 | 1.397 | 1.109 | 0.003 | 0.025 | 0.002 | 0.003 | 0.234 | 0.185 | 0.003 |
| sin tamano | estable | 185 | 1.576 | 1.381 | 0.001 | 0.072 | 0.027 | 0.001 | 0.261 | 0.231 | 0.001 |
| sin tamano | canary | 1827 | 1.383 | 1.112 | 0.003 | 0.025 | 0.002 | 0.003 | 0.233 | 0.187 | 0.003 |
| sin tamano ni documentacion | estable | 185 | 1.476 | 1.355 | 0.003 | 0.054 | 0.027 | 0.002 | 0.296 | 0.272 | 0.003 |
| sin tamano ni documentacion | canary | 1827 | 1.183 | 1.091 | 0.003 | 0.007 | 0.002 | 0.003 | 0.237 | 0.220 | 0.003 |
| sin tamano ni renovacion | estable | 185 | 1.502 | 1.368 | 0.002 | 0.052 | 0.029 | 0.001 | 0.302 | 0.274 | 0.002 |
| sin tamano ni renovacion | canary | 1827 | 1.260 | 1.096 | 0.003 | 0.012 | 0.002 | 0.003 | 0.254 | 0.222 | 0.003 |

Correlación entre las variables canónicas de cada par de dimensiones (0 Persona, 1 Proceso, 2 Producto) y RV por par:

- **todos:** GCCA 0-1 +0.29, 0-2 +0.55, 1-2 +0.18 · RV 0-1 0.06, 0-2 0.19, 1-2 0.05
- **sin volumen:** GCCA 0-1 +0.30, 0-2 +0.33, 1-2 +0.24 · RV 0-1 0.05, 0-2 0.12, 1-2 0.05
- **sin tamano:** GCCA 0-1 +0.30, 0-2 +0.32, 1-2 +0.24 · RV 0-1 0.05, 0-2 0.12, 1-2 0.05
- **sin tamano ni documentacion:** GCCA 0-1 +0.20, 0-2 +0.32, 1-2 +0.18 · RV 0-1 0.05, 0-2 0.09, 1-2 0.03
- **sin tamano ni renovacion:** GCCA 0-1 +0.22, 0-2 +0.32, 1-2 +0.21 · RV 0-1 0.03, 0-2 0.07, 1-2 0.05

Factores del MFA (correlación de cada componente con el factor; parte de la inercia de cada dimensión; congruencia de Tucker con el factor más parecido de canary):

- todos, factor 1 (24%, 3 dimensiones): persona_cp2 -0.64, producto_cp4 -0.61, producto_cp1 -0.57, persona_cp1 -0.56, proceso_cp2 -0.45 · Persona 42%, Proceso 17%, Producto 41% · canary: factor 1, congruencia 0.89
- todos, factor 2 (22%, 3 dimensiones): persona_cp3 +0.67, producto_cp1 -0.65, proceso_cp5 +0.61 · Persona 36%, Proceso 25%, Producto 39% · canary: factor 2, congruencia 0.85
- todos, factor 3 (15%, 2 dimensiones): persona_cp2 +0.61, persona_cp1 -0.51, proceso_cp5 +0.44 · Persona 68%, Proceso 24%, Producto 9% · canary: factor 3, congruencia 0.78
- sin volumen, factor 1 (26%, 3 dimensiones): producto_cp4 -0.72, persona_cp1 -0.65, proceso_cp5 -0.57 · Persona 36%, Proceso 31%, Producto 34% · canary: factor 1, congruencia 0.97
- sin volumen, factor 2 (24%, 2 dimensiones): producto_cp1 +0.78, persona_cp3 -0.64 · Persona 39%, Proceso 16%, Producto 45% · canary: factor 2, congruencia 0.90
- sin volumen, factor 3 (16%, 1 dimensiones): proceso_cp2 +0.80 · Persona 19%, Proceso 80%, Producto 1% · canary: factor 3, congruencia 0.43
- sin tamano, factor 1 (26%, 3 dimensiones): producto_cp4 -0.68, proceso_cp5 -0.61, persona_cp1 -0.58, persona_cp3 -0.46 · Persona 35%, Proceso 32%, Producto 33% · canary: factor 1, congruencia 0.97
- sin tamano, factor 2 (24%, 2 dimensiones): producto_cp1 +0.75, persona_cp3 -0.58, persona_cp1 +0.49 · Persona 40%, Proceso 15%, Producto 45% · canary: factor 2, congruencia 0.85
- sin tamano, factor 3 (16%, 1 dimensiones): proceso_cp2 +0.79 · Persona 20%, Proceso 79%, Producto 1% · canary: factor 3, congruencia 0.68
- sin tamano ni documentacion, factor 1 (30%, 3 dimensiones): producto_cp1 -0.76, persona_cp3 +0.74, proceso_cp5 +0.58 · Persona 37%, Proceso 24%, Producto 39% · canary: factor 1, congruencia 0.81
- sin tamano ni documentacion, factor 2 (25%, 2 dimensiones): persona_cp1 +0.78, proceso_cp2 +0.57, proceso_cp5 +0.46 · Persona 49%, Proceso 44%, Producto 7% · canary: factor 2, congruencia 0.59
- sin tamano ni documentacion, factor 3 (19%, 1 dimensiones): proceso_cp2 +0.77 · Persona 21%, Proceso 78%, Producto 1% · canary: factor 2, congruencia 0.53
- sin tamano ni renovacion, factor 1 (30%, 3 dimensiones): persona_cp3 -0.74, producto_cp1 +0.67, proceso_cp5 -0.64 · Persona 37%, Proceso 27%, Producto 36% · canary: factor 1, congruencia 0.90
- sin tamano ni renovacion, factor 2 (24%, 2 dimensiones): proceso_cp2 -0.77, producto_cp4 -0.67 · Persona 0%, Proceso 50%, Producto 49% · canary: factor 2, congruencia 0.67
- sin tamano ni renovacion, factor 3 (18%, 1 dimensiones): proceso_cp5 +0.54, proceso_cp2 -0.51 · Persona 18%, Proceso 62%, Producto 20% · canary: factor 2, congruencia 0.47

## 2. Red de correlaciones parciales

Marginal = el cruce de componentes de siempre; parcial = descontando los otros cinco componentes.

| Par | Marginal | tipo | Parcial | tipo | canary (parcial) | tamaño (parcial) |
|---|---|---|---|---|---|---|
| persona_cp1 ↔ proceso_cp2 | +0,18 | no_concluyente | +0,14 | no_concluyente | +0,05 | +0,16 |
| persona_cp1 ↔ proceso_cp5 | +0,15 | no_concluyente | +0,26 | patrón | +0,05 | +0,21 |
| persona_cp1 ↔ producto_cp1 | +0,17 | no_concluyente | +0,37 | patrón | +0,05 | +0,23 |
| persona_cp1 ↔ producto_cp4 | +0,33 | mecánico | +0,38 | mecánico | +0,29 | +0,36 |
| persona_cp2 ↔ proceso_cp2 | +0,13 | no_concluyente | +0,10 | no_concluyente | +0,12 | +0,18 |
| persona_cp2 ↔ proceso_cp5 | +0,18 | no_concluyente | +0,34 | escala | +0,21 | +0,06 |
| persona_cp2 ↔ producto_cp1 | +0,50 | escala | +0,60 | escala | +0,53 | -0,02 |
| persona_cp2 ↔ producto_cp4 | +0,19 | no_concluyente | +0,31 | escala | +0,09 | +0,14 |
| persona_cp3 ↔ proceso_cp2 | +0,07 | no_concluyente | +0,10 | no_concluyente | +0,04 | +0,07 |
| persona_cp3 ↔ proceso_cp5 | +0,21 | patrón solo con épocas | +0,12 | no_concluyente | +0,15 | +0,15 |
| persona_cp3 ↔ producto_cp1 | -0,36 | negativa | -0,31 | negativa | +0,02 | -0,20 |
| persona_cp3 ↔ producto_cp4 | +0,08 | no_concluyente | +0,01 | sin_relacion | +0,08 | +0,02 |
| proceso_cp2 ↔ producto_cp1 | +0,10 | no_concluyente | +0,03 | sin_relacion | +0,02 | +0,10 |
| proceso_cp2 ↔ producto_cp4 | +0,18 | no_concluyente | +0,10 | no_concluyente | -0,01 | +0,12 |
| proceso_cp5 ↔ producto_cp1 | -0,17 | no_concluyente | -0,30 | patrón | -0,11 | -0,36 |
| proceso_cp5 ↔ producto_cp4 | +0,15 | no_concluyente | -0,03 | sin_relacion | +0,08 | -0,05 |

### Triángulos (un componente por dimensión)

| Triángulo | Tipo (calendario) | Tipo (épocas) | Red parcial | Lados: marginal → sin el tercer vértice |
|---|---|---|---|---|
| persona_cp1 · proceso_cp2 · producto_cp1 | pares sueltos  | pares sueltos  | pares sueltos | persona_cp1↔proceso_cp2 +0,18 → +0,16; persona_cp1↔producto_cp1 +0,17 → +0,16; proceso_cp2↔producto_cp1 +0,10 → +0,07 |
| persona_cp1 · proceso_cp2 · producto_cp4 | pares sueltos  | pares sueltos  | pares sueltos | persona_cp1↔proceso_cp2 +0,18 → +0,13; persona_cp1↔producto_cp4 +0,33 → +0,31 (mecánico); proceso_cp2↔producto_cp4 +0,18 → +0,13 |
| persona_cp1 · proceso_cp5 · producto_cp1 | pares sueltos  | pares sueltos  | tridimensional | persona_cp1↔proceso_cp5 +0,15 → +0,19; persona_cp1↔producto_cp1 +0,17 → +0,20; proceso_cp5↔producto_cp1 -0,17 → -0,20 |
| persona_cp1 · proceso_cp5 · producto_cp4 | pares sueltos  | pares sueltos  | pares sueltos | persona_cp1↔proceso_cp5 +0,15 → +0,11; persona_cp1↔producto_cp4 +0,33 → +0,32 (mecánico); proceso_cp5↔producto_cp4 +0,15 → +0,11 |
| persona_cp2 · proceso_cp2 · producto_cp1 | solo tamaño  | solo tamaño  | pares sueltos | persona_cp2↔proceso_cp2 +0,13 → +0,09; persona_cp2↔producto_cp1 +0,50 → +0,49 (escala); proceso_cp2↔producto_cp1 +0,10 → +0,04 |
| persona_cp2 · proceso_cp2 · producto_cp4 | pares sueltos  | pares sueltos  | pares sueltos | persona_cp2↔proceso_cp2 +0,13 → +0,10; persona_cp2↔producto_cp4 +0,19 → +0,17; proceso_cp2↔producto_cp4 +0,18 → +0,16 |
| persona_cp2 · proceso_cp5 · producto_cp1 | solo tamaño  | solo tamaño  | pares sueltos | persona_cp2↔proceso_cp5 +0,18 → +0,31; persona_cp2↔producto_cp1 +0,50 → +0,54 (escala); proceso_cp5↔producto_cp1 -0,17 → -0,31 |
| persona_cp2 · proceso_cp5 · producto_cp4 | pares sueltos  | pares sueltos  | pares sueltos | persona_cp2↔proceso_cp5 +0,18 → +0,16; persona_cp2↔producto_cp4 +0,19 → +0,16; proceso_cp5↔producto_cp4 +0,15 → +0,12 |
| persona_cp3 · proceso_cp2 · producto_cp1 | pares sueltos  | pares sueltos  | pares sueltos | persona_cp3↔proceso_cp2 +0,07 → +0,11; persona_cp3↔producto_cp1 -0,36 → -0,37; proceso_cp2↔producto_cp1 +0,10 → +0,13 |
| persona_cp3 · proceso_cp2 · producto_cp4 | pares sueltos  | pares sueltos  | pares sueltos | persona_cp3↔proceso_cp2 +0,07 → +0,05; persona_cp3↔producto_cp4 +0,08 → +0,07; proceso_cp2↔producto_cp4 +0,18 → +0,18 |
| persona_cp3 · proceso_cp5 · producto_cp1 | pares sueltos  | pares sueltos persona_cp3__proceso_cp5 | pares sueltos | persona_cp3↔proceso_cp5 +0,21 → +0,16 (patrón solo con épocas); persona_cp3↔producto_cp1 -0,36 → -0,34; proceso_cp5↔producto_cp1 -0,17 → -0,10 |
| persona_cp3 · proceso_cp5 · producto_cp4 | pares sueltos  | pares sueltos persona_cp3__proceso_cp5 | pares sueltos | persona_cp3↔proceso_cp5 +0,21 → +0,20 (patrón solo con épocas); persona_cp3↔producto_cp4 +0,08 → +0,05; proceso_cp5↔producto_cp4 +0,15 → +0,13 |

### Triangulación con variables

- **persona_cp1 · proceso_cp5 · producto_cp1:** cadena 2, pares sueltos 20, solo tamaño 6
- **persona_cp3 · proceso_cp5 · producto_cp1:** pares sueltos 24

| Variables | Tipo | Tipo (épocas) | Lados: marginal → sin el tercero |
|---|---|---|---|
| tasa_nuevos_commits_ratio · nci_producto · cfdr_producto | cadena a través de tasa_nuevos_commits_ratio | pares sueltos | tasa_nuevos_commits_ratio↔nci_producto +0,22 → +0,16 (patrón); tasa_nuevos_commits_ratio↔cfdr_producto +0,24 → +0,18 (patrón); nci_producto↔cfdr_producto +0,30 → +0,27 (no resiste tamaño) |
| tasa_nuevos_commits_ratio · nci_producto · nub_producto | cadena a través de tasa_nuevos_commits_ratio | pares sueltos | tasa_nuevos_commits_ratio↔nci_producto +0,22 → +0,16 (patrón); tasa_nuevos_commits_ratio↔nub_producto +0,24 → +0,18 (patrón); nci_producto↔nub_producto +0,30 → +0,26 (no resiste tamaño) |

## 3. PCA y clustering conjunto

**ajustado** (28 variables, 189 releases, k = 4):
- CP1 (24%, bootstrap 0.99) (dos dimensiones): nuevos_commits_conteo +0.92, tasa_nuevos_commits_ratio +0.83, le_mediana -0.82, dev_exp_mediana -0.81, activos_commits_conteo +0.80, cdiv_mediana -0.66, prop_commitean_ratio +0.60, le_producto -0.51
- CP2 (18%, bootstrap 0.99) **(tres dimensiones)**: activos_interaccion_conteo +0.95, activos_comentarios_conteo +0.94, nuevos_interaccion_conteo +0.92, activos_cierre_conteo +0.74, cfdr_producto +0.73, nub_producto +0.73, prop_commitean_ratio -0.50, nci_producto +0.47
- CP3 (11%, bootstrap 0.97): exprev_share_top10pct +0.83, sc_share_top10pct +0.76, nc_share_top10pct +0.75, sc_p90 +0.69, cdiv_p90 +0.56
- CP4 (7%, bootstrap 0.92): process_performance_producto +0.88, jarczyk_success_rate_producto +0.88
- clustering (propio, k = 9, silueta 0.3398 frente a 0.0534): [Persona, Producto] activos_commits_conteo, cdiv_mediana, dev_exp_mediana, le_mediana, le_producto, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio; [Persona, Proceso, Producto] activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, cfdr_producto, nci_producto, nub_producto, nuevos_interaccion_conteo
- clustering (pca, k = 4, silueta 0.2422 frente a 0.0334): [Persona, Producto] activos_commits_conteo, cdiv_mediana, cdiv_p90, commits_doc_producto, dev_exp_mediana, dloc_flujo_producto, exprev_share_top10pct, le_mediana, le_producto, nc_share_top10pct, nuevos_commits_conteo, prop_commitean_ratio, rexp_mediana, sc_p90, sc_share_top10pct, tasa_nuevos_commits_ratio; [Persona, Proceso, Producto] activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, cfdr_producto, disc_centrality_mediana, nci_producto, nub_producto, nuevos_interaccion_conteo, prop_comentan_ratio

**tamano** (22 variables, 189 releases, k = 6):
- CP1 (20%, bootstrap 0.99) (dos dimensiones): dev_exp_mediana +0.86, le_mediana +0.85, tasa_nuevos_commits_ratio -0.79, prop_commitean_ratio -0.66, cdiv_mediana +0.62, rexp_mediana +0.59, le_producto +0.59
- CP2 (17%, bootstrap 0.97): exprev_share_top10pct +0.81, sc_share_top10pct +0.78, sc_p90 +0.75, nc_share_top10pct +0.73, cdiv_p90 +0.60
- CP3 (10%, bootstrap 0.97) (dos dimensiones): cfdr_producto +0.94, nub_producto +0.94, prop_comentan_ratio -0.59
- CP4 (9%, bootstrap 0.96): jarczyk_success_rate_producto +0.92, process_performance_producto +0.92
- CP5 (7%, bootstrap 0.89) (dos dimensiones): mttr_producto +0.81, nci_producto +0.71, exprev_share_top10pct +0.41, nc_share_top10pct +0.41
- CP6 (6%, bootstrap 0.92): dloc_flujo_producto +0.79, commits_doc_producto +0.79
- clustering (propio, k = 9, silueta 0.351 frente a 0.0595): [Persona, Producto] dev_exp_mediana, le_mediana, le_producto, prop_commitean_ratio, tasa_nuevos_commits_ratio
- clustering (pca, k = 6, silueta 0.3013 frente a 0.0488): [Persona, Producto] cdiv_mediana, dev_exp_mediana, le_mediana, le_producto, prop_commitean_ratio, rexp_mediana, tasa_nuevos_commits_ratio; [Persona, Producto] cfdr_producto, nub_producto, prop_comentan_ratio

## 4. Perfiles de releases

Diferencia entre el tercio de releases con el puntaje más alto y el más bajo de cada componente, en desvíos del componente de otra dimensión.

| Desde | Otro | Diferencia | nula p95 | q | canary | años (alto / bajo) |
|---|---|---|---|---|---|---|
| persona_cp1 | proceso_cp2 | +0,39 | ±0.32 | 0.072 | +0,15 | 2023 / 2024 |
| persona_cp1 | proceso_cp5 | +0,35 | ±0.35 | 0.085 | +0,15 | 2023 / 2024 |
| persona_cp1 | producto_cp1 | +0,40 | ±0.38 | 0.062 | +0,04 | 2023 / 2024 |
| persona_cp1 | producto_cp4 | +0,64 | ±0.32 | 0.005 | +0,67 | 2023 / 2024 |
| persona_cp2 | proceso_cp2 | +0,28 | ±0.43 | 0.201 | +0,29 | 2023 / 2023 |
| persona_cp2 | proceso_cp5 | +0,22 | ±0.44 | 0.347 | +0,41 | 2023 / 2023 |
| persona_cp2 | producto_cp1 | +0,92 | ±0.55 | 0.005 | +1,11 | 2023 / 2023 |
| persona_cp2 | producto_cp4 | +0,40 | ±0.32 | 0.062 | +0,20 | 2023 / 2023 |
| persona_cp3 | proceso_cp2 | +0,03 | ±0.40 | 0.932 | +0,08 | 2024 / 2023 |
| persona_cp3 | proceso_cp5 | +0,52 | ±0.40 | 0.062 | +0,35 | 2024 / 2023 |
| persona_cp3 | producto_cp1 | -0,76 | ±0.58 | 0.005 | +0,00 | 2024 / 2023 |
| persona_cp3 | producto_cp4 | +0,27 | ±0.37 | 0.247 | +0,25 | 2024 / 2023 |
| proceso_cp2 | persona_cp1 | +0,39 | ±0.29 | 0.038 | +0,12 | 2023 / 2024 |
| proceso_cp2 | persona_cp2 | +0,25 | ±0.36 | 0.257 | +0,37 | 2023 / 2024 |
| proceso_cp2 | persona_cp3 | +0,19 | ±0.36 | 0.391 | +0,07 | 2023 / 2024 |
| proceso_cp2 | producto_cp1 | +0,17 | ±0.41 | 0.509 | +0,26 | 2023 / 2024 |
| proceso_cp2 | producto_cp4 | +0,51 | ±0.34 | 0.036 | +0,05 | 2023 / 2024 |
| proceso_cp5 | persona_cp1 | +0,46 | ±0.35 | 0.005 | +0,10 | 2024 / 2024 |
| proceso_cp5 | persona_cp2 | +0,34 | ±0.41 | 0.179 | +0,34 | 2024 / 2024 |
| proceso_cp5 | persona_cp3 | +0,57 | ±0.30 | 0.005 | +0,33 | 2024 / 2024 |
| proceso_cp5 | producto_cp1 | -0,37 | ±0.40 | 0.102 | -0,04 | 2024 / 2024 |
| proceso_cp5 | producto_cp4 | +0,34 | ±0.33 | 0.091 | +0,29 | 2024 / 2024 |
| producto_cp1 | persona_cp1 | +0,34 | ±0.43 | 0.197 | +0,02 | 2023 / 2024 |
| producto_cp1 | persona_cp2 | +1,13 | ±0.57 | 0.005 | +1,11 | 2023 / 2024 |
| producto_cp1 | persona_cp3 | -0,78 | ±0.55 | 0.028 | +0,03 | 2023 / 2024 |
| producto_cp1 | proceso_cp2 | +0,27 | ±0.49 | 0.307 | +0,15 | 2023 / 2024 |
| producto_cp1 | proceso_cp5 | -0,42 | ±0.44 | 0.102 | +0,03 | 2023 / 2024 |
| producto_cp4 | persona_cp1 | +0,86 | ±0.34 | 0.005 | +0,69 | 2023 / 2024 |
| producto_cp4 | persona_cp2 | +0,43 | ±0.40 | 0.046 | +0,15 | 2023 / 2024 |
| producto_cp4 | persona_cp3 | +0,21 | ±0.33 | 0.307 | +0,19 | 2023 / 2024 |
| producto_cp4 | proceso_cp2 | +0,37 | ±0.39 | 0.102 | +0,04 | 2023 / 2024 |
| producto_cp4 | proceso_cp5 | +0,44 | ±0.38 | 0.062 | +0,27 | 2023 / 2024 |

## Rezago de un release (descriptivo)

| Antes | Después | ρ | q | canary |
|---|---|---|---|---|
| producto_cp1 | persona_cp3 | -0,33 | 0.008 | -0,04 |
| persona_cp3 | producto_cp1 | -0,31 | 0.011 | -0,05 |
| persona_cp2 | producto_cp1 | +0,26 | 0.070 | +0,14 |
| producto_cp1 | persona_cp2 | +0,27 | 0.070 | +0,13 |
| persona_cp1 | proceso_cp2 | +0,19 | 0.076 | +0,01 |
| proceso_cp5 | persona_cp3 | +0,18 | 0.114 | +0,08 |
| proceso_cp2 | producto_cp4 | +0,19 | 0.114 | +0,06 |
| producto_cp4 | proceso_cp2 | +0,16 | 0.189 | +0,05 |
| persona_cp3 | proceso_cp2 | -0,16 | 0.197 | +0,02 |
| proceso_cp5 | producto_cp1 | -0,16 | 0.197 | +0,01 |
