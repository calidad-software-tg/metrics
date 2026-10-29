# Cruce Persona–Proceso con los grupos del clustering (corte propio)

## Grupos de Persona

10 grupos en total, 5 de dos o más métricas · estabilidad 0.71 · canary 0.32 · coincidencia con el PCA 0.66

- G1: activos_commits_conteo, cdiv_mediana, dev_exp_mediana, le_mediana, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio (central: nuevos_commits_conteo; varianza del primer componente 58%)
- G2: activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, disc_centrality_mediana, nuevos_interaccion_conteo (central: activos_interaccion_conteo; varianza del primer componente 72%)
- G3: exprev_share_top10pct, nc_share_top10pct, prop_commitean_ratio, sc_mediana, sc_p90 (central: exprev_share_top10pct; varianza del primer componente 58%)
- G4: exprev_p90, nc_p90, prop_cierran_ratio, rexprev_mediana (central: exprev_p90; varianza del primer componente 55%)
- G5: cdiv_p90, sc_share_top10pct (central: cdiv_p90; varianza del primer componente 75%)
- Solas: cd_mediana, cdiv_share_top10pct, prop_comentan_ratio, ss_mediana, tasa_nuevos_interaccion_ratio

## Grupos de Proceso

7 grupos en total, 4 de dos o más métricas · estabilidad 0.64 · canary 0.5 · coincidencia con el PCA 0.70

- G1: cfdr_producto, nub_producto (central: cfdr_producto; varianza del primer componente 100%)
- G2: jarczyk_success_rate_producto, process_performance_producto (central: jarczyk_success_rate_producto; varianza del primer componente 89%)
- G3: mttr_producto, nci_producto (central: mttr_producto; varianza del primer componente 66%)
- G4: noi_producto, rc_producto (central: noi_producto; varianza del primer componente 68%)
- Solas: anmcc_producto, nob_42_producto, wp_producto

## Resumen por método

| | Promedio | Primer componente | Más representativa |
|---|---|---|---|
| Pares de grupos robustos | 8 | 8 | 2 |
| Patrones entre grupos | 5 | 5 | 1 |
| Patrones en el conjunto reducido | 3 | 3 | 2 |
| Primera correlación canónica | 0,65 (p 0,001) | 0,66 (p 0,001) | 0,62 (p 0,001) |
| Patrones triangulados | 4 de 16 | 4 de 16 | 1 de 16 |

## Pares de grupos robustos

| Método | Par | ρ corregida | con tamaño | canary | tipo |
|---|---|---|---|---|---|
| promedio | G2 Persona: Activos, Activos, Activos, Disc. Centrality, Nuevos contribuyentes ↔ G1 Proceso: CFDR, NUB | +0,64 | +0,05 | +0,50 | escala |
| promedio | G3 Persona: EXPRev, NC, Proporción que commitea [ratio], SC, SC ↔ G1 Proceso: CFDR, NUB | -0,37 | -0,13 | -0,07 | patrón |
| promedio | G2 Persona: Activos, Activos, Activos, Disc. Centrality, Nuevos contribuyentes ↔ G3 Proceso: MTTR, NCI | +0,22 | +0,03 | +0,40 | escala |
| promedio | G1 Persona: Activos, CDIV, dev_exp, LE, Nuevos contribuyentes… ↔ G1 Proceso: CFDR, NUB | +0,22 | +0,06 | +0,09 | no resiste tamaño |
| promedio | G4 Persona: EXPRev, NC, Proporción que cierra issues [ratio], REXPRev ↔ G2 Proceso: Jarczyk Success Rate, Process Performance | +0,21 | +0,26 | +0,14 | patrón |
| promedio | G3 Persona: EXPRev, NC, Proporción que commitea [ratio], SC, SC ↔ G3 Proceso: MTTR, NCI | +0,21 | +0,34 | +0,23 | patrón |
| promedio | G1 Persona: Activos, CDIV, dev_exp, LE, Nuevos contribuyentes… ↔ G3 Proceso: MTTR, NCI | +0,19 | +0,14 | +0,18 | patrón |
| promedio | G1 Persona: Activos, CDIV, dev_exp, LE, Nuevos contribuyentes… ↔ G2 Proceso: Jarczyk Success Rate, Process Performance | +0,18 | +0,16 | +0,07 | patrón |
| componente | G2 Persona: Activos, Activos, Activos, Disc. Centrality, Nuevos contribuyentes ↔ G1 Proceso: CFDR, NUB | +0,66 | +0,09 | +0,52 | escala |
| componente | G3 Persona: EXPRev, NC, Proporción que commitea [ratio], SC, SC ↔ G1 Proceso: CFDR, NUB | -0,37 | -0,14 | -0,06 | patrón |
| componente | G2 Persona: Activos, Activos, Activos, Disc. Centrality, Nuevos contribuyentes ↔ G3 Proceso: MTTR, NCI | +0,22 | +0,03 | +0,39 | escala |
| componente | G3 Persona: EXPRev, NC, Proporción que commitea [ratio], SC, SC ↔ G3 Proceso: MTTR, NCI | +0,21 | +0,34 | +0,24 | patrón |
| componente | G1 Persona: Activos, CDIV, dev_exp, LE, Nuevos contribuyentes… ↔ G1 Proceso: CFDR, NUB | +0,21 | +0,06 | +0,09 | no resiste tamaño |
| componente | G4 Persona: EXPRev, NC, Proporción que cierra issues [ratio], REXPRev ↔ G2 Proceso: Jarczyk Success Rate, Process Performance | +0,20 | +0,25 | +0,12 | patrón |
| componente | G1 Persona: Activos, CDIV, dev_exp, LE, Nuevos contribuyentes… ↔ G3 Proceso: MTTR, NCI | +0,20 | +0,15 | +0,18 | patrón |
| componente | G1 Persona: Activos, CDIV, dev_exp, LE, Nuevos contribuyentes… ↔ G2 Proceso: Jarczyk Success Rate, Process Performance | +0,17 | +0,16 | +0,08 | patrón |
| representativa | G2 Persona: Activos, Activos, Activos, Disc. Centrality, Nuevos contribuyentes · representa Activos ↔ G1 Proceso: CFDR, NUB · representa CFDR | +0,67 | +0,09 | +0,56 | escala |
| representativa | G3 Persona: EXPRev, NC, Proporción que commitea [ratio], SC, SC · representa EXPRev ↔ G3 Proceso: MTTR, NCI · representa MTTR | +0,24 | +0,22 | +0,17 | patrón |

## Patrones del conjunto reducido

| Método | Par | ρ corregida | con tamaño | canary |
|---|---|---|---|---|
| promedio | Proporción que comenta [ratio] ↔ G4 Proceso: NOI, RC | -0,51 | -0,44 | -0,17 |
| promedio | G3 Persona: EXPRev, NC, Proporción que commitea [ratio], SC, SC ↔ G1 Proceso: CFDR, NUB | -0,37 | -0,13 | -0,07 |
| promedio | G3 Persona: EXPRev, NC, Proporción que commitea [ratio], SC, SC ↔ NCI (Number of Closed Issues) [p90] | +0,27 | +0,25 | +0,23 |
| componente | Proporción que comenta [ratio] ↔ G4 Proceso: NOI, RC | -0,51 | -0,44 | -0,17 |
| componente | G3 Persona: EXPRev, NC, Proporción que commitea [ratio], SC, SC ↔ G1 Proceso: CFDR, NUB | -0,37 | -0,14 | -0,06 |
| componente | G3 Persona: EXPRev, NC, Proporción que commitea [ratio], SC, SC ↔ NCI (Number of Closed Issues) [p90] | +0,28 | +0,27 | +0,24 |
| representativa | G3 Persona: EXPRev, NC, Proporción que commitea [ratio], SC, SC · representa EXPRev ↔ NCI (Number of Closed Issues) [p90] | +0,37 | +0,36 | +0,31 |
| representativa | G3 Persona: EXPRev, NC, Proporción que commitea [ratio], SC, SC · representa EXPRev ↔ G3 Proceso: MTTR, NCI · representa MTTR | +0,24 | +0,22 | +0,17 |

## Triangulación de los patrones de variables

| Patrón de variables | Promedio | Primer componente | Más representativa |
|---|---|---|---|
| LE (Learning Ease) [mediana] ↔ ANMCC (Avg Modified Components per Commit) [mediana] | G1–solo: métrica sola (—) | G1–solo: métrica sola (—) | G1–solo: métrica sola (—) |
| dev_exp (Development Experience) [mediana] ↔ ANMCC (Avg Modified Components per Commit) [mediana] | G1–solo: métrica sola (—) | G1–solo: métrica sola (—) | G1–solo: métrica sola (—) |
| SC (Social Contribution) [mediana] ↔ Jarczyk Success Rate [producto] | G3–G2: no robusto (+0,17) | G3–G2: no robusto (+0,15) | G3–G2: no robusto (+0,15) |
| REXPRev (Recent Review Experience) [mediana] ↔ CFDR (Customer Found Defects & Regressions) [producto] | G4–G1: no robusto (-0,31) | G4–G1: no robusto (-0,31) | G4–G1: no robusto (-0,28) |
| REXPRev (Recent Review Experience) [mediana] ↔ NUB (Bugs Detected by Users) [producto] | G4–G1: no robusto (-0,31) | G4–G1: no robusto (-0,31) | G4–G1: no robusto (-0,28) |
| NC (Number of Comments) [share_top10pct] ↔ NCI (Number of Closed Issues) [p90] | G3–solo: métrica sola (—) | G3–solo: métrica sola (—) | G3–solo: métrica sola (—) |
| EXPRev (Code Review Experience) [p90] ↔ CFDR (Customer Found Defects & Regressions) [producto] | G4–G1: no robusto (-0,31) | G4–G1: no robusto (-0,31) | G4–G1: no robusto (-0,28) |
| EXPRev (Code Review Experience) [p90] ↔ NUB (Bugs Detected by Users) [producto] | G4–G1: no robusto (-0,31) | G4–G1: no robusto (-0,31) | G4–G1: no robusto (-0,28) |
| Tasa de ingreso (commits) [ratio] ↔ CFDR (Customer Found Defects & Regressions) [producto] | G1–G1: no resiste tamaño (+0,22) | G1–G1: no resiste tamaño (+0,21) | G1–G1: no robusto (+0,19) |
| Tasa de ingreso (commits) [ratio] ↔ NUB (Bugs Detected by Users) [producto] | G1–G1: no resiste tamaño (+0,22) | G1–G1: no resiste tamaño (+0,21) | G1–G1: no robusto (+0,19) |
| dev_exp (Development Experience) [mediana] ↔ MTTR (Mean Time to Repair) [mediana] | G1–solo: métrica sola (—) | G1–solo: métrica sola (—) | G1–solo: métrica sola (—) |
| Proporción que cierra issues [ratio] ↔ Process Performance [producto] | G4–G2: patrón (+0,21) | G4–G2: patrón (+0,20) | G4–G2: no robusto (+0,14) |
| Proporción que cierra issues [ratio] ↔ Jarczyk Success Rate [producto] | G4–G2: patrón (+0,21) | G4–G2: patrón (+0,20) | G4–G2: no robusto (+0,14) |
| EXPRev (Code Review Experience) [p90] ↔ Process Performance [producto] | G4–G2: patrón (+0,21) | G4–G2: patrón (+0,20) | G4–G2: no robusto (+0,14) |
| EXPRev (Code Review Experience) [share_top10pct] ↔ MTTR (Mean Time to Repair) [producto] | G3–G3: patrón (+0,21) | G3–G3: patrón (+0,21) | G3–G3: patrón (+0,24) |
| Proporción que comenta [ratio] ↔ ANMCC (Avg Modified Components per Commit) [producto] | solo–solo: métrica sola (—) | solo–solo: métrica sola (—) | solo–solo: métrica sola (—) |

## Frente al cruce con el PCA (cruce_dimensiones.py)

- Pares de componentes del PCA: 9, robustos 3: CP1 Persona: nuevos_commits_conteo (+0.88), le_mediana (-0.85), tasa_nuevos_commits_ratio (+0.84), dev_exp_mediana (-0.78) ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) (+0,18, patrón); CP2 Persona: activos_comentarios_conteo (+0.91), activos_interaccion_conteo (+0.89), nuevos_interaccion_conteo (+0.87), activos_cierre_conteo (+0.81) ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) (+0,54, escala); CP2 Persona: activos_comentarios_conteo (+0.91), activos_interaccion_conteo (+0.89), nuevos_interaccion_conteo (+0.87), activos_cierre_conteo (+0.81) ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) (+0,18, escala)
- Patrones del conjunto reducido con el PCA: 5
