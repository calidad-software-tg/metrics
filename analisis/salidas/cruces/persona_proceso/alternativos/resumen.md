# Métodos alternativos · Persona–Proceso

36 variables de Persona y 11 de Proceso, 184 releases estables y 1593 canary con dato en todas. Nula: 200 corrimientos circulares de un lado respecto del otro.

| Método | ¿Aporta? | Resultado |
|---|---|---|
| CCA sobre todas las variables | **Sí** | Todas: r₁ = +0,87 frente a una nula de +0,67 (p95 +0,72), canary +0,71. Sin escala ni definiciones superpuestas: r₁ = +0,71 (nula p95 +0,64), canary +0,38; la arman exprev_share_top10pct (0.76), nc_share_top10pct (0.69), prop_cierran_ratio (0.69), sc_mediana (0.58), exprev_p90 (0.51) ↔ nci_producto (0.50), jarczyk_success_rate_producto (0.48), process_performance_producto (0.40), rc_producto (0.39). Sobre los componentes: r₁ = +0,59 (nula p95 +0,33), canary — |
| Reglas de asociación | **Sí** | 623 reglas con lift ≥ 1.5 frente a 73 con datos desalineados (p95 121); 213 repiten pares que la correlación ya encontró y 4 nuevas se repiten en canary |
| Clustering de releases | No | Ajustado: k = 2, silueta 0.10 (nula p95 0.05), estabilidad 0.54. Sin ajustar: k = 2, silueta 0.26, V de Cramér con el período 0.72 |
| Clustering de métricas | No | Con 6 grupos: ARI con los componentes del PCA 0.07, estabilidad 0.32, 3 grupos mezclan dimensiones |
| Regresión multivariable | No | Predice fuera de muestra, en canary y con control de tamaño: ninguna (sin exigir el control de tamaño: cfdr_producto, nci_producto, nub_producto) |
| Información mutua | **Sí** | 39 pares significativos (q < 0,05), 22 ya los encontró Spearman; 10 nuevos con más información que la que daría una relación monótona, 2 se repiten en canary; 7 más se descartan porque una de las variables tiene menos de 10 valores distintos |
| Random forest | **Sí** | Mejor que la regresión lineal, fuera de muestra, en canary y con control de tamaño: jarczyk_success_rate_producto, nci_producto (sin exigir el control de tamaño: jarczyk_success_rate_producto, nci_producto, noi_producto) |

## Modelos por variable

| Variable | R² cv regresión (nula p95) | canary | con tamaño | signos estables | R² cv RF (nula p95) | canary | con tamaño | RF top 3 en canary |
|---|---|---|---|---|---|---|---|---|
| ANMCC (Avg Modified Components per Commit) [producto] | -0,23 (-0,17) | -0,27 | -0,09 | 5/36 | -0,03 (+0,00) | -0,02 | -0,04 | prop_comentan_ratio, le_mediana, tasa_nuevos_interaccion_ratio |
| CFDR (Customer Found Defects & Regressions) [producto] | +0,32 (-0,07) | +0,23 | -0,14 | 13/36 | +0,33 (+0,09) | +0,32 | -0,00 | activos_interaccion_conteo, nuevos_interaccion_conteo, activos_comentarios_conteo |
| Jarczyk Success Rate [producto] | +0,04 (-0,22) | -0,09 | +0,05 | 14/36 | +0,15 (+0,01) | +0,15 | +0,14 | activos_cierre_conteo, sc_mediana, prop_cierran_ratio |
| MTTR (Mean Time to Repair) [producto] | -0,27 (-0,12) | -0,30 | -0,19 | 9/36 | -0,00 (+0,03) | +0,02 | -0,01 | nci_p90, exprev_share_top10pct, nc_share_top10pct |
| NCI (Number of Closed Issues) [producto] | +0,16 (-0,25) | +0,46 | +0,06 | 8/36 | +0,36 (+0,01) | +0,48 | +0,22 | activos_cierre_conteo, activos_interaccion_conteo, prop_cierran_ratio |
| NOB (branches activas con PR abierto) [producto] | -0,14 (-0,19) | -0,11 | -0,09 | 12/36 | -0,06 (+0,02) | +0,11 | -0,06 | dloc_mediana, dloc_share_top10pct, ss_mediana |
| NOI (Number of Open Issues) [producto] | -0,11 (-0,15) | -0,36 | -0,15 | 12/36 | +0,19 (-0,00) | +0,14 | +0,06 | rc_mediana, ss_mediana, tasa_nuevos_interaccion_ratio |
| NUB (Bugs Detected by Users) [producto] | +0,32 (-0,07) | +0,24 | -0,13 | 10/36 | +0,32 (+0,03) | +0,32 | -0,00 | activos_interaccion_conteo, nuevos_interaccion_conteo, activos_comentarios_conteo |
| Process Performance [producto] | -0,37 (-0,17) | -0,19 | -0,21 | 10/36 | +0,04 (+0,01) | +0,05 | +0,04 | prop_cierran_ratio, mttr_mediana, activos_cierre_conteo |
| RC (Readme Completeness) [producto] | -0,02 (-0,18) | -0,53 | -0,00 | 17/36 | -0,00 (+0,02) | -0,02 | +0,03 | cd_mediana, prop_comentan_ratio, ss_mediana |
| WP (Wiki Presence) [producto] | -0,75 (-0,24) | -0,24 | -0,58 | 1/36 | -0,07 (-0,01) | +0,01 | -0,04 | rc_mediana, dloc_p90, dloc_mediana |

## Reglas nuevas que se repiten en canary

- SS (Skill Similarity) [mediana] alto → NOI (Number of Open Issues) [producto] bajo
- ANMCC (Avg Modified Components per Commit) [mediana] alto y CDIV (Contribution Diversity) [mediana] alto → NCI (Number of Closed Issues) [producto] bajo
- ANMCC (Avg Modified Components per Commit) [mediana] alto → NCI (Number of Closed Issues) [producto] bajo
- Proporción que comenta [ratio] alto → NOI (Number of Open Issues) [producto] bajo

## Pares nuevos por información mutua que se repiten en canary

- Proporción que cierra issues [ratio] ↔ NCI (Number of Closed Issues) [producto] (MI 0.084, ρ +0.33)
- NCI (Number of Closed Issues) [p90] ↔ Process Performance [producto] (MI 0.091, ρ +0.09)

## Grupos de métricas

- k = 6: mttr_mediana, nci_p90, mttr_producto | activos_cierre_conteo, activos_comentarios_conteo, activos_commits_conteo, activos_interaccion_conteo, anmcc_mediana, cdiv_mediana, cdiv_p90, cdiv_share_top10pct, dev_exp_mediana, disc_centrality_mediana, exprev_p90, exprev_share_top10pct, le_mediana, nc_p90, nc_share_top10pct, nci_share_top10pct, nuevos_commits_conteo, nuevos_interaccion_conteo, prop_cierran_ratio, prop_commitean_ratio, rexp_mediana, rexprev_mediana, sc_mediana, sc_p90, sc_share_top10pct, tasa_nuevos_commits_ratio, tasa_nuevos_interaccion_ratio, anmcc_producto, cfdr_producto, jarczyk_success_rate_producto, nci_producto, nub_producto, process_performance_producto | cd_mediana, dloc_mediana, dloc_share_top10pct | dloc_p90, prop_comentan_ratio, rc_mediana, noi_producto, rc_producto, wp_producto
- k = 8: mttr_mediana, nci_p90, mttr_producto | activos_commits_conteo, anmcc_mediana, cdiv_mediana, cdiv_p90, cdiv_share_top10pct, dev_exp_mediana, le_mediana, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio, anmcc_producto | sc_mediana, jarczyk_success_rate_producto, process_performance_producto | activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, disc_centrality_mediana, exprev_p90, exprev_share_top10pct, nc_p90, nc_share_top10pct, nci_share_top10pct, nuevos_interaccion_conteo, prop_cierran_ratio, prop_commitean_ratio, rexprev_mediana, sc_p90, sc_share_top10pct, tasa_nuevos_interaccion_ratio, cfdr_producto, nci_producto, nub_producto | cd_mediana, dloc_mediana, dloc_share_top10pct | dloc_p90, prop_comentan_ratio, rc_mediana, noi_producto, rc_producto, wp_producto
- k = 10: mttr_mediana, nci_p90, mttr_producto | activos_commits_conteo, anmcc_mediana, cdiv_mediana, cdiv_p90, cdiv_share_top10pct, dev_exp_mediana, le_mediana, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio, anmcc_producto | sc_mediana, jarczyk_success_rate_producto, process_performance_producto | disc_centrality_mediana, tasa_nuevos_interaccion_ratio | activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, exprev_p90, exprev_share_top10pct, nc_p90, nc_share_top10pct, nci_share_top10pct, nuevos_interaccion_conteo, prop_cierran_ratio, prop_commitean_ratio, rexprev_mediana, sc_p90, sc_share_top10pct, cfdr_producto, nci_producto, nub_producto | cd_mediana, dloc_mediana, dloc_share_top10pct | dloc_p90, wp_producto | prop_comentan_ratio, rc_mediana, noi_producto, rc_producto
