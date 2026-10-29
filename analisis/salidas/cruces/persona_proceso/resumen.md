# Cruce Persona–Proceso

Variables: Persona 28, Proceso 18. En los dos lados: cdiv_mediana → Persona, cdiv_p90 → Persona, cdiv_share_top10pct → Persona, dev_exp_mediana → Persona, exprev_p90 → Persona, exprev_share_top10pct → Persona, nc_p90 → Persona, nc_share_top10pct → Persona, rexprev_mediana → Persona, sc_mediana → Persona, sc_p90 → Persona, sc_share_top10pct → Persona.

## Variables

| Tipo | Pares |
|---|---|
| patrón | 16 |
| escala | 18 |
| mecánico | 5 |
| no resiste tamaño | 4 |
| control | 9 |

### Patrones (robustos, sin escala ni construcción)

| Par | ρ corregida | con tamaño | canary | alcance |
|---|---|---|---|---|
| LE (Learning Ease) [mediana] ↔ ANMCC (Avg Modified Components per Commit) [mediana] | +0,48 | +0,45 | +0,21 | solo 2020-2024 |
| dev_exp (Development Experience) [mediana] ↔ ANMCC (Avg Modified Components per Commit) [mediana] | +0,38 | +0,37 | +0,22 | solo 2020-2024 |
| SC (Social Contribution) [mediana] ↔ Jarczyk Success Rate [producto] | +0,33 | +0,35 | +0,30 | solo 2020-2024 |
| REXPRev (Recent Review Experience) [mediana] ↔ CFDR (Customer Found Defects & Regressions) [producto] | -0,31 | -0,16 | -0,07 | solo 2023-2024 |
| REXPRev (Recent Review Experience) [mediana] ↔ NUB (Bugs Detected by Users) [producto] | -0,31 | -0,16 | -0,07 | solo 2023-2024 |
| NC (Number of Comments) [share_top10pct] ↔ NCI (Number of Closed Issues) [p90] | +0,29 | +0,28 | +0,17 | intermitente |
| EXPRev (Code Review Experience) [p90] ↔ CFDR (Customer Found Defects & Regressions) [producto] | -0,28 | -0,12 | -0,02 | desde 2025 |
| EXPRev (Code Review Experience) [p90] ↔ NUB (Bugs Detected by Users) [producto] | -0,27 | -0,12 | -0,03 | desde 2025 |
| Tasa de ingreso (commits) [ratio] ↔ CFDR (Customer Found Defects & Regressions) [producto] | +0,24 | +0,11 | +0,07 | sin relación en ningún período |
| Tasa de ingreso (commits) [ratio] ↔ NUB (Bugs Detected by Users) [producto] | +0,23 | +0,11 | +0,07 | sin relación en ningún período |
| dev_exp (Development Experience) [mediana] ↔ MTTR (Mean Time to Repair) [mediana] | -0,23 | -0,23 | -0,02 | solo 2020-2024 |
| Proporción que cierra issues [ratio] ↔ Process Performance [producto] | +0,23 | +0,23 | +0,15 | desde 2025 |
| Proporción que cierra issues [ratio] ↔ Jarczyk Success Rate [producto] | +0,23 | +0,25 | +0,26 | desde 2023 |
| EXPRev (Code Review Experience) [p90] ↔ Process Performance [producto] | +0,22 | +0,22 | +0,03 | solo 2016-2022 |
| EXPRev (Code Review Experience) [share_top10pct] ↔ MTTR (Mean Time to Repair) [producto] | +0,20 | +0,20 | +0,17 | intermitente |
| Proporción que comenta [ratio] ↔ ANMCC (Avg Modified Components per Commit) [producto] | +0,17 | +0,20 | +0,02 | sin relación en ningún período |

## Componentes

- CP1 Persona: nuevos_commits_conteo (+0.88), le_mediana (-0.85), tasa_nuevos_commits_ratio (+0.84), dev_exp_mediana (-0.78) · bootstrap +0,99 · canary +0,96
- CP2 Persona: activos_comentarios_conteo (+0.91), activos_interaccion_conteo (+0.89), nuevos_interaccion_conteo (+0.87), activos_cierre_conteo (+0.81) · bootstrap +0,98 · canary +0,86
- CP3 Persona: exprev_share_top10pct (+0.88), nc_share_top10pct (+0.80), sc_share_top10pct (+0.76), sc_p90 (+0.66) · bootstrap +0,97 · canary +0,82
- CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) · bootstrap +0,96 · canary +0,97
- CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) · bootstrap +0,98 · canary +0,99
- CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) · bootstrap +0,95 · canary +0,97

| Par de componentes | ρ corregida | con tamaño | canary | resultado |
|---|---|---|---|---|
| CP1 Persona: nuevos_commits_conteo (+0.88), le_mediana (-0.85), tasa_nuevos_commits_ratio (+0.84), dev_exp_mediana (-0.78) ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,17 | +0,11 | +0,02 | no robusto |
| CP1 Persona: nuevos_commits_conteo (+0.88), le_mediana (-0.85), tasa_nuevos_commits_ratio (+0.84), dev_exp_mediana (-0.78) ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,18 | +0,17 | +0,05 | patrón |
| CP1 Persona: nuevos_commits_conteo (+0.88), le_mediana (-0.85), tasa_nuevos_commits_ratio (+0.84), dev_exp_mediana (-0.78) ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) | +0,15 | +0,14 | +0,07 | no robusto |
| CP2 Persona: activos_comentarios_conteo (+0.91), activos_interaccion_conteo (+0.89), nuevos_interaccion_conteo (+0.87), activos_cierre_conteo (+0.81) ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,54 | -0,15 | +0,52 | escala |
| CP2 Persona: activos_comentarios_conteo (+0.91), activos_interaccion_conteo (+0.89), nuevos_interaccion_conteo (+0.87), activos_cierre_conteo (+0.81) ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,13 | +0,14 | +0,15 | no robusto |
| CP2 Persona: activos_comentarios_conteo (+0.91), activos_interaccion_conteo (+0.89), nuevos_interaccion_conteo (+0.87), activos_cierre_conteo (+0.81) ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) | +0,18 | +0,06 | +0,18 | escala |
| CP3 Persona: exprev_share_top10pct (+0.88), nc_share_top10pct (+0.80), sc_share_top10pct (+0.76), sc_p90 (+0.66) ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,28 | -0,18 | +0,02 | no robusto |
| CP3 Persona: exprev_share_top10pct (+0.88), nc_share_top10pct (+0.80), sc_share_top10pct (+0.76), sc_p90 (+0.66) ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,07 | +0,08 | +0,04 | no robusto |
| CP3 Persona: exprev_share_top10pct (+0.88), nc_share_top10pct (+0.80), sc_share_top10pct (+0.76), sc_p90 (+0.66) ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) | +0,21 | +0,26 | +0,16 | no robusto |

## Conjunto reducido

De cada lado: el puntaje de cada componente firme más las variables que no cargan en ningún componente. Persona: 12 elementos · Proceso: 15 · 180 pares.

| Tipo | Pares |
|---|---|
| patrón | 5 |
| escala | 1 |
| mecánico | 2 |
| no resiste tamaño | 0 |
| control | 4 |

| Par | ρ corregida | con tamaño | canary | tipo |
|---|---|---|---|---|
| CP1 Persona: nuevos_commits_conteo (+0.88), le_mediana (-0.85), tasa_nuevos_commits_ratio (+0.84), dev_exp_mediana (-0.78) ↔ ANMCC (Avg Modified Components per Commit) [mediana] | -0,56 | -0,53 | -0,29 | mecánico |
| CP2 Persona: activos_comentarios_conteo (+0.91), activos_interaccion_conteo (+0.89), nuevos_interaccion_conteo (+0.87), activos_cierre_conteo (+0.81) ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,54 | -0,15 | +0,52 | escala |
| CDIV (Contribution Diversity) [share_top10pct] ↔ ANMCC (Avg Modified Components per Commit) [producto] | +0,43 | +0,45 | +0,17 | mecánico |
| SC (Social Contribution) [mediana] ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,36 | +0,38 | +0,22 | patrón |
| REXPRev (Recent Review Experience) [mediana] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,34 | -0,20 | -0,11 | patrón |
| CP3 Persona: exprev_share_top10pct (+0.88), nc_share_top10pct (+0.80), sc_share_top10pct (+0.76), sc_p90 (+0.66) ↔ NCI (Number of Closed Issues) [p90] | +0,31 | +0,31 | +0,22 | patrón |
| Proporción que cierra issues [ratio] ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,29 | +0,30 | +0,31 | patrón |
| EXPRev (Code Review Experience) [p90] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,29 | -0,11 | -0,08 | patrón |

## Correlación canónica entre componentes

Correlaciones canónicas: +0,59, +0,33, +0,02 (n = 185). Primera frente a la nula por corrimiento circular: p = 0.001 (percentil 95 nulo +0,33).

## Triangulación

| Par | componentes | par de componentes robusto |
|---|---|---|
| dev_exp (Development Experience) [mediana] ↔ ANMCC (Avg Modified Components per Commit) [mediana] | CP1 / — | no |
| dev_exp (Development Experience) [mediana] ↔ MTTR (Mean Time to Repair) [mediana] | CP1 / — | no |
| EXPRev (Code Review Experience) [p90] ↔ CFDR (Customer Found Defects & Regressions) [producto] | — / CP1 | no |
| EXPRev (Code Review Experience) [p90] ↔ NUB (Bugs Detected by Users) [producto] | — / CP1 | no |
| EXPRev (Code Review Experience) [p90] ↔ Process Performance [producto] | — / CP2 | no |
| EXPRev (Code Review Experience) [share_top10pct] ↔ MTTR (Mean Time to Repair) [producto] | CP3 / CP5 | no |
| LE (Learning Ease) [mediana] ↔ ANMCC (Avg Modified Components per Commit) [mediana] | CP1 / — | no |
| NC (Number of Comments) [share_top10pct] ↔ NCI (Number of Closed Issues) [p90] | CP3 / — | no |
| Proporción que cierra issues [ratio] ↔ Jarczyk Success Rate [producto] | — / CP2 | no |
| Proporción que cierra issues [ratio] ↔ Process Performance [producto] | — / CP2 | no |
| Proporción que comenta [ratio] ↔ ANMCC (Avg Modified Components per Commit) [producto] | CP2 / — | no |
| REXPRev (Recent Review Experience) [mediana] ↔ CFDR (Customer Found Defects & Regressions) [producto] | — / CP1 | no |
| REXPRev (Recent Review Experience) [mediana] ↔ NUB (Bugs Detected by Users) [producto] | — / CP1 | no |
| SC (Social Contribution) [mediana] ↔ Jarczyk Success Rate [producto] | — / CP2 | no |
| Tasa de ingreso (commits) [ratio] ↔ CFDR (Customer Found Defects & Regressions) [producto] | CP1 / CP1 | no |
| Tasa de ingreso (commits) [ratio] ↔ NUB (Bugs Detected by Users) [producto] | CP1 / CP1 | no |

## PCA conjunto

25 variables, 189 releases, Horn retiene 4.

- CP1 (26%) · **mezcla dimensiones**: activos_interaccion_conteo (+0.95), activos_comentarios_conteo (+0.94), nuevos_interaccion_conteo (+0.92), activos_cierre_conteo (+0.75), cfdr_producto (+0.72), nub_producto (+0.72)
- CP2 (20%): nuevos_commits_conteo (+0.93), tasa_nuevos_commits_ratio (+0.84), le_mediana (-0.81), dev_exp_mediana (-0.81), activos_commits_conteo (+0.79), cdiv_mediana (-0.69)
- CP3 (11%): exprev_share_top10pct (+0.86), nc_share_top10pct (+0.79), sc_p90 (+0.72), sc_share_top10pct (+0.72), cdiv_p90 (+0.51), prop_commitean_ratio (+0.43)
- CP4 (7%): process_performance_producto (+0.91), jarczyk_success_rate_producto (+0.90)

## Clustering conjunto

25 variables, 189 releases; corte propio: 8.

**Corte propio** (8 grupos): silueta +0,37 (nula p95 +0,05), ARI con el PCA conjunto +0,76, estabilidad +0,88.

- **mezcla dimensiones** · activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, cfdr_producto, nci_producto, nub_producto, nuevos_interaccion_conteo (CP 1 del PCA conjunto)
- activos_commits_conteo, cdiv_mediana, dev_exp_mediana, le_mediana, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio (CP 2 del PCA conjunto)
- exprev_share_top10pct, nc_share_top10pct, prop_commitean_ratio, sc_p90 (CP 2, 3 del PCA conjunto)
- cdiv_p90, sc_share_top10pct (CP 3 del PCA conjunto)
- jarczyk_success_rate_producto, process_performance_producto (CP 4 del PCA conjunto)

**Corte pca** (4 grupos): silueta +0,27 (nula p95 +0,04), ARI con el PCA conjunto +0,63, estabilidad +0,32.

- activos_commits_conteo, cdiv_mediana, cdiv_p90, dev_exp_mediana, exprev_share_top10pct, le_mediana, nc_share_top10pct, nuevos_commits_conteo, prop_commitean_ratio, rexp_mediana, sc_p90, sc_share_top10pct, tasa_nuevos_commits_ratio (CP 2, 3 del PCA conjunto)
- **mezcla dimensiones** · activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, cfdr_producto, disc_centrality_mediana, nci_producto, nub_producto, nuevos_interaccion_conteo, prop_comentan_ratio (CP 1 del PCA conjunto)
- jarczyk_success_rate_producto, process_performance_producto (CP 4 del PCA conjunto)
