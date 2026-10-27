# Métodos alternativos · Persona–Proceso

28 variables de Persona y 11 de Proceso, 185 releases estables y 1827 canary con dato en todas. Nula: 200 corrimientos circulares de un lado respecto del otro.

| Método | ¿Aporta? | Resultado |
|---|---|---|
| CCA sobre todas las variables | **Sí** | Todas: r₁ = +0,86 frente a una nula de +0,63 (p95 +0,69), canary +0,75. Sin escala ni definiciones superpuestas: r₁ = +0,72 (nula p95 +0,64), canary +0,40; la arman exprev_share_top10pct (0.75), prop_cierran_ratio (0.69), nc_share_top10pct (0.68), sc_mediana (0.60), exprev_p90 (0.51) ↔ jarczyk_success_rate_producto (0.49), nci_producto (0.48), rc_producto (0.42), process_performance_producto (0.41). Sobre los componentes: r₁ = +0,59 (nula p95 +0,33), canary +0,51 |
| Reglas de asociación | No | 546 reglas con lift ≥ 1.5 frente a 50 con datos desalineados (p95 92); 191 repiten pares que la correlación ya encontró y 2 nuevas se repiten en canary |
| Clustering de releases | No | Ajustado: k = 2, silueta 0.11 (nula p95 0.05), estabilidad 0.25. Sin ajustar: k = 2, silueta 0.26, V de Cramér con el período 0.68 |
| Clustering de métricas | No | Con 6 grupos: ARI con los componentes del PCA 0.18, estabilidad 0.56, 4 grupos mezclan dimensiones |
| Regresión multivariable | No | Predice fuera de muestra, en canary y con control de tamaño: ninguna (sin exigir el control de tamaño: cfdr_producto, nci_producto, nub_producto) |
| Información mutua | **Sí** | 37 pares significativos (q < 0,05), 24 ya los encontró Spearman; 5 nuevos con más información que la que daría una relación monótona, 2 se repiten en canary; 8 más se descartan porque una de las variables tiene menos de 10 valores distintos |
| Random forest | **Sí** | Mejor que la regresión lineal, fuera de muestra, en canary y con control de tamaño: jarczyk_success_rate_producto, nci_producto (sin exigir el control de tamaño: jarczyk_success_rate_producto, nci_producto, noi_producto) |

## Modelos por variable

| Variable | R² cv regresión (nula p95) | canary | con tamaño | signos estables | R² cv RF (nula p95) | canary | con tamaño | RF top 3 en canary |
|---|---|---|---|---|---|---|---|---|
| ANMCC (Avg Modified Components per Commit) [producto] | -0,16 (-0,11) | -0,22 | -0,04 | 4/28 | -0,01 (-0,01) | -0,02 | -0,03 | prop_comentan_ratio, tasa_nuevos_commits_ratio, nuevos_commits_conteo |
| CFDR (Customer Found Defects & Regressions) [producto] | +0,35 (-0,07) | +0,28 | -0,09 | 8/28 | +0,33 (-0,00) | +0,34 | +0,00 | activos_interaccion_conteo, nuevos_interaccion_conteo, activos_comentarios_conteo |
| Jarczyk Success Rate [producto] | -0,05 (-0,10) | -0,06 | +0,01 | 9/28 | +0,13 (-0,01) | +0,12 | +0,12 | sc_mediana, activos_cierre_conteo, prop_cierran_ratio |
| MTTR (Mean Time to Repair) [producto] | -0,21 (-0,13) | -0,17 | -0,12 | 2/28 | -0,02 (+0,00) | +0,01 | -0,03 | exprev_share_top10pct, ss_mediana, cd_mediana |
| NCI (Number of Closed Issues) [producto] | +0,20 (-0,11) | +0,42 | +0,08 | 7/28 | +0,35 (+0,02) | +0,51 | +0,21 | activos_cierre_conteo, activos_interaccion_conteo, prop_cierran_ratio |
| NOB (branches activas con PR abierto) [producto] | -0,20 (-0,14) | -0,21 | -0,12 | 11/28 | -0,12 (-0,00) | +0,01 | -0,10 | ss_mediana, cdiv_share_top10pct, sc_share_top10pct |
| NOI (Number of Open Issues) [producto] | -0,05 (-0,02) | -0,23 | -0,01 | 9/28 | +0,14 (+0,12) | +0,06 | +0,05 | ss_mediana, prop_comentan_ratio, tasa_nuevos_interaccion_ratio |
| NUB (Bugs Detected by Users) [producto] | +0,36 (-0,08) | +0,29 | -0,08 | 9/28 | +0,33 (+0,01) | +0,34 | +0,01 | activos_interaccion_conteo, nuevos_interaccion_conteo, activos_comentarios_conteo |
| Process Performance [producto] | -0,17 (-0,14) | -0,19 | -0,08 | 6/28 | +0,07 (+0,00) | +0,02 | +0,06 | prop_cierran_ratio, activos_cierre_conteo, ss_mediana |
| RC (Readme Completeness) [producto] | +0,02 (-0,17) | -0,42 | +0,04 | 15/28 | +0,00 (+0,01) | -0,02 | +0,02 | prop_comentan_ratio, cd_mediana, ss_mediana |
| WP (Wiki Presence) [producto] | -0,37 (-0,13) | -0,38 | -0,34 | 2/28 | -0,04 (-0,01) | -0,01 | -0,03 | ss_mediana, nc_p90, prop_commitean_ratio |

## Reglas nuevas que se repiten en canary

- SS (Skill Similarity) [mediana] alto → NOI (Number of Open Issues) [producto] bajo
- Proporción que comenta [ratio] alto → NOI (Number of Open Issues) [producto] bajo

## Pares nuevos por información mutua que se repiten en canary

- Nuevos contribuyentes (commits) [conteo] ↔ Jarczyk Success Rate [producto] (MI 0.064, ρ +0.18)
- Proporción que cierra issues [ratio] ↔ NCI (Number of Closed Issues) [producto] (MI 0.081, ρ +0.32)

## Grupos de métricas

- k = 6: nob_42_producto, wp_producto | prop_comentan_ratio, noi_producto, rc_producto | sc_mediana, jarczyk_success_rate_producto, mttr_producto, process_performance_producto | activos_commits_conteo, cdiv_mediana, cdiv_p90, cdiv_share_top10pct, dev_exp_mediana, le_mediana, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio, anmcc_producto | activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, cd_mediana, disc_centrality_mediana, exprev_p90, exprev_share_top10pct, nc_p90, nc_share_top10pct, nuevos_interaccion_conteo, prop_cierran_ratio, prop_commitean_ratio, rexprev_mediana, sc_p90, sc_share_top10pct, tasa_nuevos_interaccion_ratio, cfdr_producto, nci_producto, nub_producto
- k = 8: nob_42_producto, wp_producto | prop_comentan_ratio, noi_producto, rc_producto | sc_mediana, jarczyk_success_rate_producto, process_performance_producto | activos_commits_conteo, cdiv_mediana, cdiv_p90, cdiv_share_top10pct, dev_exp_mediana, le_mediana, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio, anmcc_producto | activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, disc_centrality_mediana, exprev_p90, exprev_share_top10pct, nc_p90, nc_share_top10pct, nuevos_interaccion_conteo, prop_cierran_ratio, prop_commitean_ratio, rexprev_mediana, sc_p90, sc_share_top10pct, tasa_nuevos_interaccion_ratio, cfdr_producto, nci_producto, nub_producto
- k = 10: nob_42_producto, wp_producto | prop_comentan_ratio, noi_producto, rc_producto | sc_mediana, jarczyk_success_rate_producto, process_performance_producto | cdiv_p90, anmcc_producto | activos_commits_conteo, cdiv_mediana, cdiv_share_top10pct, dev_exp_mediana, le_mediana, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio | disc_centrality_mediana, tasa_nuevos_interaccion_ratio | activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, exprev_p90, exprev_share_top10pct, nc_p90, nc_share_top10pct, nuevos_interaccion_conteo, prop_cierran_ratio, prop_commitean_ratio, rexprev_mediana, sc_p90, sc_share_top10pct, cfdr_producto, nci_producto, nub_producto
