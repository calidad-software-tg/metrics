# Métodos alternativos · Persona–Proceso

28 variables de Persona y 16 de Proceso, 184 releases estables y 1593 canary con dato en todas. Nula: 200 corrimientos circulares de un lado respecto del otro.

| Método | ¿Aporta? | Resultado |
|---|---|---|
| CCA sobre todas las variables | **Sí** | Todas: r₁ = +0,91 frente a una nula de +0,66 (p95 +0,70), canary +0,82. Sin escala ni definiciones superpuestas: r₁ = +0,80 (nula p95 +0,66), canary +0,58; la arman prop_cierran_ratio (0.82), exprev_share_top10pct (0.52), nc_share_top10pct (0.47), tasa_nuevos_commits_ratio (0.41), sc_p90 (0.35) ↔ anmcc_mediana (0.53), nci_producto (0.38), jarczyk_success_rate_producto (0.31), cfdr_producto (0.28). Sobre los componentes: r₁ = +0,59 (nula p95 +0,33), canary +0,51 |
| Reglas de asociación | **Sí** | 687 reglas con lift ≥ 1.5 frente a 64 con datos desalineados (p95 150); 291 repiten pares que la correlación ya encontró y 3 nuevas se repiten en canary |
| Clustering de releases | No | Ajustado: k = 2, silueta 0.10 (nula p95 0.05), estabilidad 0.51. Sin ajustar: k = 2, silueta 0.26, V de Cramér con el período 0.69 |
| Clustering de métricas | No | Con 6 grupos: ARI con los componentes del PCA 0.13, estabilidad 0.49, 3 grupos mezclan dimensiones |
| Regresión multivariable | No | Predice fuera de muestra, en canary y con control de tamaño: ninguna (sin exigir el control de tamaño: cfdr_producto, nci_producto, nub_producto) |
| Información mutua | **Sí** | 49 pares significativos (q < 0,05), 32 ya los encontró Spearman; 8 nuevos con más información que la que daría una relación monótona, 2 se repiten en canary; 8 más se descartan porque una de las variables tiene menos de 10 valores distintos |
| Random forest | **Sí** | Mejor que la regresión lineal, fuera de muestra, en canary y con control de tamaño: jarczyk_success_rate_producto, nci_producto (sin exigir el control de tamaño: jarczyk_success_rate_producto, nci_producto) |

## Modelos por variable

| Variable | R² cv regresión (nula p95) | canary | con tamaño | signos estables | R² cv RF (nula p95) | canary | con tamaño | RF top 3 en canary |
|---|---|---|---|---|---|---|---|---|
| ANMCC (Avg Modified Components per Commit) [mediana] | +0,24 (-0,08) | -0,15 | +0,23 | 9/28 | +0,24 (-0,01) | +0,07 | +0,24 | tasa_nuevos_commits_ratio, nuevos_commits_conteo, rexp_mediana |
| ANMCC (Avg Modified Components per Commit) [producto] | -0,17 (-0,10) | -0,22 | -0,05 | 5/28 | -0,03 (-0,01) | -0,02 | -0,06 | prop_comentan_ratio, le_mediana, tasa_nuevos_interaccion_ratio |
| CFDR (Customer Found Defects & Regressions) [producto] | +0,37 (-0,07) | +0,25 | -0,08 | 9/28 | +0,34 (+0,03) | +0,33 | -0,00 | activos_interaccion_conteo, nuevos_interaccion_conteo, prop_comentan_ratio |
| Jarczyk Success Rate [producto] | -0,06 (-0,14) | -0,03 | +0,01 | 7/28 | +0,12 (+0,01) | +0,13 | +0,14 | sc_mediana, activos_cierre_conteo, prop_cierran_ratio |
| MTTR (Mean Time to Repair) [mediana] | -0,16 (-0,14) | -0,20 | -0,11 | 5/28 | -0,04 (+0,01) | -0,01 | -0,01 | disc_centrality_mediana, prop_comentan_ratio, ss_mediana |
| MTTR (Mean Time to Repair) [producto] | -0,15 (-0,12) | -0,31 | -0,07 | 10/28 | +0,00 (+0,01) | +0,01 | -0,03 | exprev_share_top10pct, ss_mediana, nc_share_top10pct |
| NCI (Number of Closed Issues) [p90] | -0,19 (-0,17) | -0,28 | -0,09 | 6/28 | +0,08 (-0,01) | +0,00 | +0,09 | exprev_share_top10pct, rexprev_mediana, sc_mediana |
| NCI (Number of Closed Issues) [producto] | +0,17 (-0,13) | +0,40 | +0,07 | 7/28 | +0,36 (+0,02) | +0,46 | +0,20 | activos_cierre_conteo, activos_interaccion_conteo, prop_cierran_ratio |
| NCI (Number of Closed Issues) [share_top10pct] | -0,19 (-0,12) | -0,81 | -0,24 | 6/28 | +0,06 (+0,02) | -0,20 | +0,03 | prop_cierran_ratio, disc_centrality_mediana, sc_p90 |
| NOB (branches activas con PR abierto) [producto] | -0,19 (-0,09) | -0,23 | -0,12 | 10/28 | -0,13 (+0,06) | +0,01 | -0,12 | ss_mediana, sc_share_top10pct, cdiv_share_top10pct |
| NOI (Number of Open Issues) [producto] | -0,07 (-0,06) | -0,24 | -0,02 | 9/28 | +0,13 (-0,02) | +0,02 | +0,04 | ss_mediana, prop_comentan_ratio, tasa_nuevos_interaccion_ratio |
| NUB (Bugs Detected by Users) [producto] | +0,37 (-0,07) | +0,27 | -0,06 | 7/28 | +0,34 (+0,04) | +0,33 | -0,00 | activos_interaccion_conteo, nuevos_interaccion_conteo, prop_comentan_ratio |
| Process Performance [producto] | -0,20 (-0,11) | -0,17 | -0,11 | 6/28 | +0,05 (+0,04) | +0,02 | +0,04 | prop_cierran_ratio, activos_cierre_conteo, ss_mediana |
| RC (Readme Completeness) [mediana] | +0,04 (-0,14) | -0,45 | +0,06 | 15/28 | -0,01 (-0,01) | -0,03 | +0,03 | prop_comentan_ratio, cd_mediana, ss_mediana |
| RC (Readme Completeness) [producto] | +0,04 (-0,16) | -0,45 | +0,06 | 17/28 | -0,01 (-0,00) | -0,03 | +0,03 | prop_comentan_ratio, cd_mediana, ss_mediana |
| WP (Wiki Presence) [producto] | -0,36 (-0,15) | -0,36 | -0,33 | 1/28 | -0,04 (-0,02) | -0,01 | -0,03 | nc_p90, sc_share_top10pct, prop_comentan_ratio |

## Reglas nuevas que se repiten en canary

- EXPRev (Code Review Experience) [share_top10pct] alto → NCI (Number of Closed Issues) [p90] alto
- SS (Skill Similarity) [mediana] alto → NOI (Number of Open Issues) [producto] bajo
- Proporción que comenta [ratio] alto → NOI (Number of Open Issues) [producto] bajo

## Pares nuevos por información mutua que se repiten en canary

- Proporción que cierra issues [ratio] ↔ NCI (Number of Closed Issues) [producto] (MI 0.084, ρ +0.33)
- REXP (Recent Experience) [mediana] ↔ NCI (Number of Closed Issues) [share_top10pct] (MI 0.070, ρ -0.21)

## Grupos de métricas

- k = 6: prop_comentan_ratio, nob_42_producto, noi_producto, rc_mediana, rc_producto, wp_producto | activos_commits_conteo, cdiv_mediana, cdiv_p90, cdiv_share_top10pct, dev_exp_mediana, le_mediana, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio, anmcc_mediana, anmcc_producto | activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, disc_centrality_mediana, exprev_p90, exprev_share_top10pct, nc_p90, nc_share_top10pct, nuevos_interaccion_conteo, prop_cierran_ratio, prop_commitean_ratio, rexprev_mediana, sc_mediana, sc_p90, sc_share_top10pct, tasa_nuevos_interaccion_ratio, cfdr_producto, jarczyk_success_rate_producto, nci_producto, nci_share_top10pct, nub_producto, process_performance_producto | mttr_mediana, mttr_producto, nci_p90
- k = 8: prop_comentan_ratio, noi_producto, rc_mediana, rc_producto | nob_42_producto, wp_producto | activos_commits_conteo, cdiv_mediana, cdiv_p90, cdiv_share_top10pct, dev_exp_mediana, le_mediana, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio, anmcc_mediana, anmcc_producto | sc_mediana, jarczyk_success_rate_producto, process_performance_producto | activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, disc_centrality_mediana, exprev_p90, exprev_share_top10pct, nc_p90, nc_share_top10pct, nuevos_interaccion_conteo, prop_cierran_ratio, prop_commitean_ratio, rexprev_mediana, sc_p90, sc_share_top10pct, tasa_nuevos_interaccion_ratio, cfdr_producto, nci_producto, nci_share_top10pct, nub_producto | mttr_mediana, mttr_producto, nci_p90
- k = 10: prop_comentan_ratio, noi_producto, rc_mediana, rc_producto | nob_42_producto, wp_producto | activos_commits_conteo, cdiv_mediana, cdiv_p90, cdiv_share_top10pct, dev_exp_mediana, le_mediana, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio, anmcc_mediana, anmcc_producto | sc_mediana, jarczyk_success_rate_producto, process_performance_producto | disc_centrality_mediana, tasa_nuevos_interaccion_ratio | activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, nuevos_interaccion_conteo, cfdr_producto, nci_producto, nci_share_top10pct, nub_producto | exprev_p90, exprev_share_top10pct, nc_p90, nc_share_top10pct, prop_cierran_ratio, prop_commitean_ratio, rexprev_mediana, sc_p90, sc_share_top10pct | mttr_mediana, mttr_producto, nci_p90
