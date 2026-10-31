# Pertenencia ponderada según el catálogo

Cada variable cuenta para las dimensiones que le asigna el catálogo, en partes iguales.

## 1. Patrones de los cruces: ¿dependen de la asignación?

Un patrón depende de la asignación si sus dos variables comparten una dimensión del catálogo: con otra asignación sería una relación dentro de esa dimensión.

- **persona–proceso:** 16 patrones, 11 dependen de la asignación
- **persona–producto:** 23 patrones, 8 dependen de la asignación
- **proceso–producto:** 14 patrones, 6 dependen de la asignación

| Cruce | Patrón | ρ | Catálogo (x / y) | Dimensión común | Composición |
|---|---|---|---|---|---|
| persona–proceso | le_mediana ↔ anmcc_mediana | +0.48 | Persona+Producto / Proceso+Producto | Producto | Persona 25% · Proceso 25% · Producto 50% |
| persona–proceso | dev_exp_mediana ↔ anmcc_mediana | +0.38 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–proceso | sc_mediana ↔ jarczyk_success_rate_producto | +0.33 | Persona+Proceso / Proceso | Proceso | Persona 25% · Proceso 75% · Producto 0% |
| persona–proceso | rexprev_mediana ↔ cfdr_producto | -0.31 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–proceso | rexprev_mediana ↔ nub_producto | -0.31 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–proceso | nc_share_top10pct ↔ nci_p90 | +0.29 | Persona+Proceso / Proceso | Proceso | Persona 25% · Proceso 75% · Producto 0% |
| persona–proceso | exprev_p90 ↔ cfdr_producto | -0.28 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–proceso | exprev_p90 ↔ nub_producto | -0.27 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–proceso | dev_exp_mediana ↔ mttr_mediana | -0.23 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–proceso | exprev_p90 ↔ process_performance_producto | +0.22 | Persona+Proceso / Proceso | Proceso | Persona 25% · Proceso 75% · Producto 0% |
| persona–proceso | exprev_share_top10pct ↔ mttr_producto | +0.20 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–proceso | tasa_nuevos_commits_ratio ↔ cfdr_producto | +0.24 | Persona / Proceso+Producto | — | Persona 50% · Proceso 25% · Producto 25% |
| persona–proceso | tasa_nuevos_commits_ratio ↔ nub_producto | +0.23 | Persona / Proceso+Producto | — | Persona 50% · Proceso 25% · Producto 25% |
| persona–proceso | prop_cierran_ratio ↔ process_performance_producto | +0.23 | Persona / Proceso | — | Persona 50% · Proceso 50% · Producto 0% |
| persona–proceso | prop_cierran_ratio ↔ jarczyk_success_rate_producto | +0.23 | Persona / Proceso | — | Persona 50% · Proceso 50% · Producto 0% |
| persona–proceso | prop_comentan_ratio ↔ anmcc_producto | +0.17 | Persona / Proceso+Producto | — | Persona 50% · Proceso 25% · Producto 25% |
| persona–producto | le_mediana ↔ anmcc_mediana | +0.48 | Persona+Producto / Proceso+Producto | Producto | Persona 25% · Proceso 25% · Producto 50% |
| persona–producto | dev_exp_mediana ↔ anmcc_mediana | +0.38 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–producto | rexprev_mediana ↔ cfdr_producto | -0.31 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–producto | rexprev_mediana ↔ nub_producto | -0.31 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–producto | exprev_p90 ↔ cfdr_producto | -0.28 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–producto | exprev_p90 ↔ nub_producto | -0.27 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–producto | dev_exp_mediana ↔ mttr_mediana | -0.23 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–producto | exprev_share_top10pct ↔ mttr_producto | +0.20 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| persona–producto | cdiv_mediana ↔ commits_doc_producto | -0.42 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| persona–producto | prop_commitean_ratio ↔ le_producto | -0.29 | Persona / Producto | — | Persona 50% · Proceso 0% · Producto 50% |
| persona–producto | exprev_share_top10pct ↔ dloc_flujo_producto | +0.29 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| persona–producto | cdiv_p90 ↔ cd_producto | +0.28 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| persona–producto | tasa_nuevos_commits_ratio ↔ le_producto | -0.26 | Persona / Producto | — | Persona 50% · Proceso 0% · Producto 50% |
| persona–producto | tasa_nuevos_commits_ratio ↔ cfdr_producto | +0.24 | Persona / Proceso+Producto | — | Persona 50% · Proceso 25% · Producto 25% |
| persona–producto | tasa_nuevos_commits_ratio ↔ nub_producto | +0.23 | Persona / Proceso+Producto | — | Persona 50% · Proceso 25% · Producto 25% |
| persona–producto | nc_p90 ↔ le_producto | -0.22 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| persona–producto | nc_share_top10pct ↔ dloc_flujo_producto | +0.21 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| persona–producto | prop_commitean_ratio ↔ dloc_flujo_producto | +0.21 | Persona / Producto | — | Persona 50% · Proceso 0% · Producto 50% |
| persona–producto | exprev_share_top10pct ↔ le_producto | -0.20 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| persona–producto | sc_p90 ↔ dloc_flujo_producto | +0.20 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| persona–producto | nc_share_top10pct ↔ le_producto | -0.20 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| persona–producto | prop_cierran_ratio ↔ dloc_mediana | -0.20 | Persona / Producto | — | Persona 50% · Proceso 0% · Producto 50% |
| persona–producto | prop_comentan_ratio ↔ anmcc_producto | +0.17 | Persona / Proceso+Producto | — | Persona 50% · Proceso 25% · Producto 25% |
| proceso–producto | cdiv_mediana ↔ le_mediana | +0.49 | Persona+Proceso / Persona+Producto | Persona | Persona 50% · Proceso 25% · Producto 25% |
| proceso–producto | dev_exp_mediana ↔ anmcc_mediana | +0.38 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| proceso–producto | rexprev_mediana ↔ cfdr_producto | -0.31 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| proceso–producto | rexprev_mediana ↔ nub_producto | -0.31 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| proceso–producto | exprev_p90 ↔ cfdr_producto | -0.28 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| proceso–producto | exprev_p90 ↔ nub_producto | -0.27 | Persona+Proceso / Proceso+Producto | Proceso | Persona 25% · Proceso 50% · Producto 25% |
| proceso–producto | cdiv_mediana ↔ commits_doc_producto | -0.42 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| proceso–producto | exprev_share_top10pct ↔ dloc_flujo_producto | +0.29 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| proceso–producto | cdiv_p90 ↔ cd_producto | +0.28 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| proceso–producto | nc_p90 ↔ le_producto | -0.22 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| proceso–producto | nci_producto ↔ dloc_flujo_producto | +0.22 | Proceso / Producto | — | Persona 0% · Proceso 50% · Producto 50% |
| proceso–producto | nc_share_top10pct ↔ dloc_flujo_producto | +0.21 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| proceso–producto | exprev_share_top10pct ↔ le_producto | -0.20 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |
| proceso–producto | sc_p90 ↔ dloc_flujo_producto | +0.20 | Persona+Proceso / Producto | — | Persona 25% · Proceso 25% · Producto 50% |

## 2. PCA conjunto de las tres dimensiones, sin asignar

Todas las variables juntas. Composición de cada componente: carga al cuadrado de las variables que lo definen (|carga| ≥ 0,4), repartida según el catálogo (ponderada) o entera al lado asignado. Tridimensional: cada dimensión aporta al menos 20%.

**ajustado** (52 variables, 184 releases, k = 10):

| CP | Varianza | Bootstrap | Ponderada | Asignada | Variables |
|---|---|---|---|---|---|
| 1 (escala) | 15% | 0.97 | **una dimensión**: Persona 70% · Proceso 16% · Producto 14% | una dimensión: Persona 88% · Proceso 0% · Producto 12% | nuevos_commits_conteo +0.91, tasa_nuevos_commits_ratio +0.82, dev_exp_mediana -0.82, le_mediana -0.80, activos_commits_conteo +0.77, cdiv_mediana -0.66, anmcc_mediana -0.62, prop_commitean_ratio +0.60, rexp_mediana -0.56, le_producto -0.49, cdiv_share_top10pct +0.42 |
| 2 (escala) | 13% | 0.97 | **una dimensión**: Persona 67% · Proceso 19% · Producto 14% | dos dimensiones: Persona 67% · Proceso 6% · Producto 27% | activos_interaccion_conteo +0.88, nuevos_interaccion_conteo +0.86, activos_comentarios_conteo +0.83, activos_cierre_conteo +0.80, cfdr_producto +0.79, nub_producto +0.79, nci_producto +0.51, prop_commitean_ratio -0.46 |
| 3 | 7% | 0.86 | **dos dimensiones**: Persona 42% · Proceso 47% · Producto 11% | una dimensión: Persona 84% · Proceso 0% · Producto 16% | sc_share_top10pct +0.72, cdiv_p90 +0.69, exprev_share_top10pct +0.66, nc_share_top10pct +0.62, sc_p90 +0.59, anmcc_producto +0.48, commits_doc_producto -0.41 |
| 4 | 6% | 0.87 | **dos dimensiones**: Persona 18% · Proceso 41% · Producto 41% | una dimensión: Persona 18% · Proceso 16% · Producto 66% | rc_producto +0.84, rc_mediana +0.84, prop_comentan_ratio -0.65, noi_producto +0.62, anmcc_producto -0.40 |
| 5 | 5% | 0.86 | **dos dimensiones**: Persona 59% · Proceso 41% · Producto 0% | una dimensión: Persona 100% · Proceso 0% · Producto 0% | nc_p90 +0.70, exprev_p90 +0.68, prop_cierran_ratio +0.55, rexprev_mediana +0.55, cdiv_share_top10pct -0.43 |
| 6 | 5% | 0.89 | **una dimensión**: Persona 7% · Proceso 93% · Producto 0% | una dimensión: Persona 13% · Proceso 87% · Producto 0% | jarczyk_success_rate_producto +0.87, process_performance_producto +0.83, sc_mediana +0.46 |
| 7 | 4% | 0.83 | **dos dimensiones**: Persona 0% · Proceso 73% · Producto 27% | una dimensión: Persona 0% · Proceso 100% · Producto 0% | mttr_producto +0.74, mttr_mediana +0.72, nci_producto +0.60, nci_share_top10pct +0.59, nci_p90 +0.45 |
| 8 | 4% | 0.35 | **dos dimensiones**: Persona 0% · Proceso 22% · Producto 78% | una dimensión: Persona 0% · Proceso 0% · Producto 100% | wp_producto +0.82, cd_producto +0.75, dloc_p90 +0.52 |
| 9 | 3% | 0.70 | **una dimensión**: Persona 9% · Proceso 0% · Producto 91% | una dimensión: Persona 18% · Proceso 0% · Producto 82% | dloc_share_top10pct +0.73, dloc_mediana -0.62, cd_mediana +0.48, dloc_flujo_producto +0.40 |
| 10 | 3% | 0.49 | **dos dimensiones**: Persona 45% · Proceso 0% · Producto 55% | dos dimensiones: Persona 45% · Proceso 0% · Producto 55% | dloc_flujo_producto +0.56, disc_centrality_mediana +0.45, ss_mediana +0.44, commits_doc_producto +0.42 |
- clustering (propio, k = 10): grupos de tres dimensiones con el catálogo: Persona 46% · Proceso 21% · Producto 32%: anmcc_producto, commits_doc_producto, dloc_flujo_producto, le_producto, activos_commits_conteo, anmcc_mediana, cdiv_mediana, cdiv_p90, cdiv_share_top10pct, dev_exp_mediana, le_mediana, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio; Persona 25% · Proceso 38% · Producto 38%: noi_producto, rc_producto, prop_comentan_ratio, rc_mediana
- clustering (pca, k = 10): grupos de tres dimensiones con el catálogo: Persona 46% · Proceso 21% · Producto 32%: anmcc_producto, commits_doc_producto, dloc_flujo_producto, le_producto, activos_commits_conteo, anmcc_mediana, cdiv_mediana, cdiv_p90, cdiv_share_top10pct, dev_exp_mediana, le_mediana, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio; Persona 25% · Proceso 38% · Producto 38%: noi_producto, rc_producto, prop_comentan_ratio, rc_mediana

**tamano** (46 variables, 184 releases, k = 9):

| CP | Varianza | Bootstrap | Ponderada | Asignada | Variables |
|---|---|---|---|---|---|
| 1 | 13% | 0.96 | **tres dimensiones**: Persona 56% · Proceso 23% · Producto 21% | dos dimensiones: Persona 80% · Proceso 0% · Producto 20% | tasa_nuevos_commits_ratio +0.78, cdiv_mediana -0.76, le_mediana -0.76, dev_exp_mediana -0.75, anmcc_mediana -0.71, rexp_mediana -0.63, prop_commitean_ratio +0.61, cdiv_share_top10pct +0.50, le_producto -0.42, commits_doc_producto +0.42 |
| 2 | 10% | 0.87 | **dos dimensiones**: Persona 50% · Proceso 50% · Producto 0% | una dimensión: Persona 100% · Proceso 0% · Producto 0% | exprev_share_top10pct +0.77, nc_share_top10pct +0.74, sc_share_top10pct +0.69, sc_p90 +0.67, cdiv_p90 +0.61 |
| 3 | 8% | 0.76 | **dos dimensiones**: Persona 10% · Proceso 45% · Producto 45% | una dimensión: Persona 10% · Proceso 17% · Producto 73% | rc_mediana +0.79, rc_producto +0.79, noi_producto +0.58, anmcc_producto -0.52, prop_comentan_ratio -0.46 |
| 4 | 6% | 0.86 | **dos dimensiones**: Persona 55% · Proceso 35% · Producto 10% | una dimensión: Persona 90% · Proceso 0% · Producto 10% | nc_p90 +0.73, exprev_p90 +0.70, rexprev_mediana +0.54, prop_commitean_ratio +0.44, le_producto -0.43, prop_cierran_ratio +0.40 |
| 5 | 5% | 0.82 | **dos dimensiones**: Persona 0% · Proceso 78% · Producto 22% | una dimensión: Persona 0% · Proceso 100% · Producto 0% | nci_producto +0.72, mttr_producto +0.71, mttr_mediana +0.70, nci_share_top10pct +0.66, nci_p90 +0.51 |
| 6 | 5% | 0.87 | **una dimensión**: Persona 6% · Proceso 94% · Producto 0% | una dimensión: Persona 12% · Proceso 88% · Producto 0% | jarczyk_success_rate_producto +0.86, process_performance_producto +0.83, sc_mediana +0.45 |
| 7 | 4% | 0.35 | **dos dimensiones**: Persona 0% · Proceso 23% · Producto 77% | una dimensión: Persona 0% · Proceso 0% · Producto 100% | wp_producto +0.84, cd_producto +0.75, dloc_p90 +0.55 |
| 8 | 4% | 0.79 | **tres dimensiones**: Persona 21% · Proceso 40% · Producto 40% | dos dimensiones: Persona 21% · Proceso 0% · Producto 79% | cfdr_producto +0.86, nub_producto +0.86, prop_comentan_ratio -0.47, ss_mediana -0.41 |
| 9 | 4% | 0.73 | **una dimensión**: Persona 8% · Proceso 0% · Producto 92% | una dimensión: Persona 17% · Proceso 0% · Producto 83% | dloc_share_top10pct +0.78, dloc_mediana -0.56, dloc_flujo_producto +0.49, cd_mediana +0.48 |
- clustering (propio, k = 10): grupos de tres dimensiones con el catálogo: Persona 50% · Proceso 27% · Producto 23%: anmcc_producto, le_producto, anmcc_mediana, cdiv_mediana, cdiv_p90, cdiv_share_top10pct, dev_exp_mediana, le_mediana, prop_commitean_ratio, rexp_mediana, tasa_nuevos_commits_ratio
- clustering (pca, k = 9): grupos de tres dimensiones con el catálogo: Persona 42% · Proceso 23% · Producto 35%: anmcc_producto, commits_doc_producto, dloc_flujo_producto, le_producto, anmcc_mediana, cdiv_mediana, cdiv_p90, cdiv_share_top10pct, dev_exp_mediana, le_mediana, prop_commitean_ratio, rexp_mediana, tasa_nuevos_commits_ratio

## 3. Factor común del análisis de tres dimensiones

| Variante | Componentes (correlación con el factor) | Con la asignación | Con el catálogo |
|---|---|---|---|
| sin tamano ni documentacion | persona_cp3 +0.74, proceso_cp5 +0.58, producto_cp1 -0.76 | Persona 37% · Proceso 24% · Producto 39% | Persona 22% · Proceso 53% · Producto 25% |
| sin tamano ni renovacion | persona_cp3 -0.74, proceso_cp5 -0.64, producto_cp1 +0.67 | Persona 37% · Proceso 27% · Producto 36% | Persona 21% · Proceso 50% · Producto 28% |
| sin tamano | persona_cp1 -0.58, persona_cp3 -0.46, proceso_cp5 -0.61, producto_cp4 -0.68 | Persona 35% · Proceso 32% · Producto 33% | Persona 25% · Proceso 36% · Producto 39% |
