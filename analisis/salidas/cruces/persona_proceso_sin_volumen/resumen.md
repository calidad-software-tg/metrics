# Cruce Persona–Proceso

Variables: Persona 37, Proceso 11.

## Variables

| Tipo | Pares |
|---|---|
| patrón | 18 |
| escala | 15 |
| mecánico | 3 |
| no resiste tamaño | 6 |
| control | 8 |

### Patrones (robustos, sin escala ni construcción)

| Par | ρ corregida | con tamaño | canary | alcance |
|---|---|---|---|---|
| SC (Social Contribution) [mediana] ↔ Jarczyk Success Rate [producto] | +0,33 | +0,35 | +0,30 | solo 2020-2024 |
| MTTR (Mean Time to Repair) [mediana] ↔ DIS (Doc Issue Survival) [producto] | +0,32 | +0,32 | +0,41 | desde 2025 |
| REXPRev (Recent Review Experience) [mediana] ↔ CFDR (Customer Found Defects & Regressions) [producto] | -0,31 | -0,16 | -0,07 | solo 2023-2024 |
| REXPRev (Recent Review Experience) [mediana] ↔ NUB (Bugs Detected by Users) [producto] | -0,31 | -0,16 | -0,07 | solo 2023-2024 |
| EXPRev (Code Review Experience) [p90] ↔ CFDR (Customer Found Defects & Regressions) [producto] | -0,28 | -0,12 | -0,02 | desde 2025 |
| EXPRev (Code Review Experience) [p90] ↔ NUB (Bugs Detected by Users) [producto] | -0,27 | -0,12 | -0,03 | desde 2025 |
| DIS (Doc Issue Survival) [mediana] ↔ Jarczyk Success Rate [producto] | -0,27 | -0,26 | -0,31 | solo 2023-2024 |
| NCI (Number of Closed Issues) [p90] ↔ DIS (Doc Issue Survival) [producto] | +0,27 | +0,27 | +0,19 | desde 2025 |
| Tasa de ingreso (commits) [ratio] ↔ CFDR (Customer Found Defects & Regressions) [producto] | +0,24 | +0,11 | +0,07 | sin relación en ningún período |
| Tasa de ingreso (commits) [ratio] ↔ NUB (Bugs Detected by Users) [producto] | +0,23 | +0,11 | +0,07 | sin relación en ningún período |
| Proporción que cierra issues [ratio] ↔ Process Performance [producto] | +0,23 | +0,23 | +0,15 | desde 2025 |
| Proporción que cierra issues [ratio] ↔ Jarczyk Success Rate [producto] | +0,23 | +0,25 | +0,26 | desde 2023 |
| EXPRev (Code Review Experience) [p90] ↔ Process Performance [producto] | +0,22 | +0,22 | +0,03 | solo 2016-2022 |
| EXPRev (Code Review Experience) [share_top10pct] ↔ MTTR (Mean Time to Repair) [producto] | +0,20 | +0,20 | +0,17 | intermitente |
| NCI (Number of Closed Issues) [p90] ↔ Jarczyk Success Rate [producto] | +0,19 | +0,20 | +0,25 | sin relación en ningún período |
| MTTR (Mean Time to Repair) [mediana] ↔ NCI (Number of Closed Issues) [producto] | +0,18 | +0,23 | +0,21 | desde 2025 |
| MTTR (Mean Time to Repair) [mediana] ↔ Process Performance [producto] | -0,18 | -0,18 | -0,13 | sin relación en ningún período |
| Proporción que comenta [ratio] ↔ ANMCC (Avg Modified Components per Commit) [producto] | +0,17 | +0,20 | +0,02 | sin relación en ningún período |

## Componentes

- CP1 Persona: le_mediana (+0.85), nuevos_commits_conteo (-0.84), tasa_nuevos_commits_ratio (-0.84), dev_exp_mediana (+0.78) · bootstrap +0,97 · canary +0,87
- CP3 Persona: exprev_share_top10pct (+0.89), nc_share_top10pct (+0.80), sc_share_top10pct (+0.75), sc_p90 (+0.61) · bootstrap +0,96 · canary +0,76
- CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) · bootstrap +0,98 · canary +0,97
- CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.93) · bootstrap +0,98 · canary +0,98
- CP3 Proceso: rc_producto (+0.81), noi_producto (+0.72), anmcc_producto (-0.49) · bootstrap +0,96 · canary +0,93
- CP4 Proceso: mttr_producto (+0.86), nci_producto (+0.74) · bootstrap +0,90 · canary +0,96

| Par de componentes | ρ corregida | con tamaño | canary | resultado |
|---|---|---|---|---|
| CP1 Persona: le_mediana (+0.85), nuevos_commits_conteo (-0.84), tasa_nuevos_commits_ratio (-0.84), dev_exp_mediana (+0.78) ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,20 | -0,17 | +0,00 | no robusto |
| CP1 Persona: le_mediana (+0.85), nuevos_commits_conteo (-0.84), tasa_nuevos_commits_ratio (-0.84), dev_exp_mediana (+0.78) ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.93) | -0,14 | -0,14 | -0,04 | no robusto |
| CP1 Persona: le_mediana (+0.85), nuevos_commits_conteo (-0.84), tasa_nuevos_commits_ratio (-0.84), dev_exp_mediana (+0.78) ↔ CP3 Proceso: rc_producto (+0.81), noi_producto (+0.72), anmcc_producto (-0.49) | -0,04 | -0,08 | +0,01 | no robusto |
| CP1 Persona: le_mediana (+0.85), nuevos_commits_conteo (-0.84), tasa_nuevos_commits_ratio (-0.84), dev_exp_mediana (+0.78) ↔ CP4 Proceso: mttr_producto (+0.86), nci_producto (+0.74) | -0,23 | -0,22 | -0,06 | patrón |
| CP3 Persona: exprev_share_top10pct (+0.89), nc_share_top10pct (+0.80), sc_share_top10pct (+0.75), sc_p90 (+0.61) ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,30 | -0,23 | — | no robusto |
| CP3 Persona: exprev_share_top10pct (+0.89), nc_share_top10pct (+0.80), sc_share_top10pct (+0.75), sc_p90 (+0.61) ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.93) | +0,14 | +0,16 | — | no robusto |
| CP3 Persona: exprev_share_top10pct (+0.89), nc_share_top10pct (+0.80), sc_share_top10pct (+0.75), sc_p90 (+0.61) ↔ CP3 Proceso: rc_producto (+0.81), noi_producto (+0.72), anmcc_producto (-0.49) | +0,11 | +0,06 | — | no robusto |
| CP3 Persona: exprev_share_top10pct (+0.89), nc_share_top10pct (+0.80), sc_share_top10pct (+0.75), sc_p90 (+0.61) ↔ CP4 Proceso: mttr_producto (+0.86), nci_producto (+0.74) | +0,28 | +0,33 | — | mecánico |

## Conjunto reducido

De cada lado: el puntaje de cada componente firme más las variables que no cargan en ningún componente. Persona: 25 elementos · Proceso: 6 · 150 pares.

| Tipo | Pares |
|---|---|
| patrón | 13 |
| escala | 6 |
| mecánico | 2 |
| no resiste tamaño | 0 |
| control | 1 |

| Par | ρ corregida | con tamaño | canary | tipo |
|---|---|---|---|---|
| Activos (interacción) [conteo] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,70 | -0,01 | +0,57 | escala |
| Nuevos contribuyentes (interacción) [conteo] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,67 | -0,01 | +0,55 | escala |
| Activos (comentarios) [conteo] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,65 | -0,15 | +0,47 | escala |
| MTTR (Mean Time to Repair) [mediana] ↔ CP4 Proceso: mttr_producto (+0.86), nci_producto (+0.74) | +0,55 | +0,56 | +0,66 | mecánico |
| Activos (cierre de issues) [conteo] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,50 | +0,04 | +0,26 | escala |
| Proporción que comenta [ratio] ↔ CP3 Proceso: rc_producto (+0.81), noi_producto (+0.72), anmcc_producto (-0.49) | -0,49 | -0,43 | -0,17 | patrón |
| SC (Social Contribution) [mediana] ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.93) | +0,34 | +0,36 | +0,22 | patrón |
| MTTR (Mean Time to Repair) [mediana] ↔ DIS (Doc Issue Survival) [producto] | +0,32 | +0,32 | +0,41 | patrón |
| REXPRev (Recent Review Experience) [mediana] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,32 | -0,17 | -0,11 | patrón |
| CDIV (Contribution Diversity) [share_top10pct] ↔ CP3 Proceso: rc_producto (+0.81), noi_producto (+0.72), anmcc_producto (-0.49) | -0,32 | -0,29 | -0,05 | patrón |
| DIS (Doc Issue Survival) [mediana] ↔ CP4 Proceso: mttr_producto (+0.86), nci_producto (+0.74) | +0,31 | +0,34 | +0,31 | patrón |
| Proporción que cierra issues [ratio] ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.93) | +0,30 | +0,31 | +0,31 | patrón |
| Activos (cierre de issues) [conteo] ↔ CP4 Proceso: mttr_producto (+0.86), nci_producto (+0.74) | +0,30 | +0,26 | +0,55 | escala |
| EXPRev (Code Review Experience) [p90] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,29 | -0,13 | -0,08 | patrón |
| CP3 Persona: exprev_share_top10pct (+0.89), nc_share_top10pct (+0.80), sc_share_top10pct (+0.75), sc_p90 (+0.61) ↔ CP4 Proceso: mttr_producto (+0.86), nci_producto (+0.74) | +0,28 | +0,33 | — | mecánico |
| Activos (cierre de issues) [conteo] ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.93) | +0,27 | +0,31 | +0,36 | escala |
| REXPRev (Recent Review Experience) [mediana] ↔ DIS (Doc Issue Survival) [producto] | +0,24 | +0,25 | +0,03 | patrón |
| CP1 Persona: le_mediana (+0.85), nuevos_commits_conteo (-0.84), tasa_nuevos_commits_ratio (-0.84), dev_exp_mediana (+0.78) ↔ CP4 Proceso: mttr_producto (+0.86), nci_producto (+0.74) | -0,23 | -0,22 | -0,06 | patrón |
| EXPRev (Code Review Experience) [p90] ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.93) | +0,21 | +0,24 | +0,10 | patrón |
| Proporción que cierra issues [ratio] ↔ CP4 Proceso: mttr_producto (+0.86), nci_producto (+0.74) | +0,21 | +0,23 | +0,40 | patrón |
| SC (Social Contribution) [mediana] ↔ CP4 Proceso: mttr_producto (+0.86), nci_producto (+0.74) | +0,19 | +0,23 | +0,11 | patrón |

## Correlación canónica entre componentes

Correlaciones canónicas: +0,43, +0,31 (n = 184). Primera frente a la nula por corrimiento circular: p = 0.001 (percentil 95 nulo +0,33).

## Triangulación

| Par | componentes | par de componentes robusto |
|---|---|---|
| DIS (Doc Issue Survival) [mediana] ↔ Jarczyk Success Rate [producto] | — / CP2 | no |
| EXPRev (Code Review Experience) [p90] ↔ CFDR (Customer Found Defects & Regressions) [producto] | — / CP1 | no |
| EXPRev (Code Review Experience) [p90] ↔ NUB (Bugs Detected by Users) [producto] | — / CP1 | no |
| EXPRev (Code Review Experience) [p90] ↔ Process Performance [producto] | — / CP2 | no |
| EXPRev (Code Review Experience) [share_top10pct] ↔ MTTR (Mean Time to Repair) [producto] | CP3 / CP4 | no |
| MTTR (Mean Time to Repair) [mediana] ↔ DIS (Doc Issue Survival) [producto] | — / — | no |
| MTTR (Mean Time to Repair) [mediana] ↔ NCI (Number of Closed Issues) [producto] | — / CP4 | no |
| MTTR (Mean Time to Repair) [mediana] ↔ Process Performance [producto] | — / CP2 | no |
| NCI (Number of Closed Issues) [p90] ↔ DIS (Doc Issue Survival) [producto] | CP3 / — | no |
| NCI (Number of Closed Issues) [p90] ↔ Jarczyk Success Rate [producto] | CP3 / CP2 | no |
| Proporción que cierra issues [ratio] ↔ Jarczyk Success Rate [producto] | — / CP2 | no |
| Proporción que cierra issues [ratio] ↔ Process Performance [producto] | — / CP2 | no |
| Proporción que comenta [ratio] ↔ ANMCC (Avg Modified Components per Commit) [producto] | — / CP3 | no |
| REXPRev (Recent Review Experience) [mediana] ↔ CFDR (Customer Found Defects & Regressions) [producto] | — / CP1 | no |
| REXPRev (Recent Review Experience) [mediana] ↔ NUB (Bugs Detected by Users) [producto] | — / CP1 | no |
| SC (Social Contribution) [mediana] ↔ Jarczyk Success Rate [producto] | — / CP2 | no |
| Tasa de ingreso (commits) [ratio] ↔ CFDR (Customer Found Defects & Regressions) [producto] | CP1 / CP1 | no |
| Tasa de ingreso (commits) [ratio] ↔ NUB (Bugs Detected by Users) [producto] | CP1 / CP1 | no |

## PCA conjunto

23 variables, 185 releases, Horn retiene 6.

- CP1 (24%): nuevos_commits_conteo (+0.95), tasa_nuevos_commits_ratio (+0.84), activos_commits_conteo (+0.83), dev_exp_mediana (-0.81), le_mediana (-0.80), cdiv_mediana (-0.65)
- CP2 (18%) · **mezcla dimensiones**: exprev_share_top10pct (+0.74), sc_share_top10pct (+0.70), nc_share_top10pct (+0.70), cdiv_p90 (+0.68), sc_p90 (+0.68), anmcc_mediana (+0.43)
- CP3 (10%) · **mezcla dimensiones**: cfdr_producto (+0.95), nub_producto (+0.94), prop_commitean_ratio (-0.51)
- CP4 (8%): process_performance_producto (+0.92), jarczyk_success_rate_producto (+0.91)
- CP5 (7%): noi_producto (+0.74), rc_producto (+0.71), anmcc_producto (-0.55)
- CP6 (6%) · **mezcla dimensiones**: mttr_producto (+0.73), nci_producto (+0.71), nci_p90 (+0.62)
