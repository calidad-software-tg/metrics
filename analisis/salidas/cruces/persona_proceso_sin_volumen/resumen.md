# Cruce Persona–Proceso

Variables: Persona 37, Proceso 12.

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
- CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) · bootstrap +0,96 · canary +0,97
- CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) · bootstrap +0,98 · canary +0,99
- CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) · bootstrap +0,95 · canary +0,97

| Par de componentes | ρ corregida | con tamaño | canary | resultado |
|---|---|---|---|---|
| CP1 Persona: le_mediana (+0.85), nuevos_commits_conteo (-0.84), tasa_nuevos_commits_ratio (-0.84), dev_exp_mediana (+0.78) ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,17 | -0,13 | +0,01 | no robusto |
| CP1 Persona: le_mediana (+0.85), nuevos_commits_conteo (-0.84), tasa_nuevos_commits_ratio (-0.84), dev_exp_mediana (+0.78) ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | -0,16 | -0,15 | -0,04 | no robusto |
| CP1 Persona: le_mediana (+0.85), nuevos_commits_conteo (-0.84), tasa_nuevos_commits_ratio (-0.84), dev_exp_mediana (+0.78) ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) | -0,23 | -0,21 | -0,06 | patrón |
| CP3 Persona: exprev_share_top10pct (+0.89), nc_share_top10pct (+0.80), sc_share_top10pct (+0.75), sc_p90 (+0.61) ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,28 | -0,20 | — | no robusto |
| CP3 Persona: exprev_share_top10pct (+0.89), nc_share_top10pct (+0.80), sc_share_top10pct (+0.75), sc_p90 (+0.61) ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,13 | +0,14 | — | no robusto |
| CP3 Persona: exprev_share_top10pct (+0.89), nc_share_top10pct (+0.80), sc_share_top10pct (+0.75), sc_p90 (+0.61) ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) | +0,28 | +0,33 | — | mecánico |

## Conjunto reducido

De cada lado: el puntaje de cada componente firme más las variables que no cargan en ningún componente. Persona: 25 elementos · Proceso: 9 · 225 pares.

| Tipo | Pares |
|---|---|
| patrón | 8 |
| escala | 6 |
| mecánico | 3 |
| no resiste tamaño | 0 |
| control | 2 |

| Par | ρ corregida | con tamaño | canary | tipo |
|---|---|---|---|---|
| Activos (interacción) [conteo] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,72 | -0,01 | +0,57 | escala |
| Nuevos contribuyentes (interacción) [conteo] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,68 | -0,03 | +0,54 | escala |
| Activos (comentarios) [conteo] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,68 | -0,13 | +0,46 | escala |
| MTTR (Mean Time to Repair) [mediana] ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) | +0,55 | +0,57 | +0,66 | mecánico |
| Activos (cierre de issues) [conteo] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,51 | +0,02 | +0,26 | escala |
| CDIV (Contribution Diversity) [share_top10pct] ↔ ANMCC (Avg Modified Components per Commit) [producto] | +0,43 | +0,45 | +0,17 | mecánico |
| SC (Social Contribution) [mediana] ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,36 | +0,38 | +0,22 | patrón |
| REXPRev (Recent Review Experience) [mediana] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,34 | -0,20 | -0,11 | patrón |
| MTTR (Mean Time to Repair) [mediana] ↔ DIS (Doc Issue Survival) [producto] | +0,32 | +0,32 | +0,41 | patrón |
| DIS (Doc Issue Survival) [mediana] ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) | +0,30 | +0,33 | +0,31 | patrón |
| Activos (cierre de issues) [conteo] ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) | +0,30 | +0,25 | +0,54 | escala |
| Proporción que cierra issues [ratio] ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,29 | +0,30 | +0,31 | patrón |
| EXPRev (Code Review Experience) [p90] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,29 | -0,11 | -0,08 | patrón |
| CP3 Persona: exprev_share_top10pct (+0.89), nc_share_top10pct (+0.80), sc_share_top10pct (+0.75), sc_p90 (+0.61) ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) | +0,28 | +0,33 | — | mecánico |
| Activos (cierre de issues) [conteo] ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,26 | +0,30 | +0,36 | escala |
| CP1 Persona: le_mediana (+0.85), nuevos_commits_conteo (-0.84), tasa_nuevos_commits_ratio (-0.84), dev_exp_mediana (+0.78) ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) | -0,23 | -0,21 | -0,06 | patrón |
| Proporción que comenta [ratio] ↔ ANMCC (Avg Modified Components per Commit) [producto] | +0,17 | +0,20 | +0,02 | patrón |

## Correlación canónica entre componentes

Correlaciones canónicas: +0,42, +0,29 (n = 184). Primera frente a la nula por corrimiento circular: p = 0.001 (percentil 95 nulo +0,30).

## Triangulación

| Par | componentes | par de componentes robusto |
|---|---|---|
| DIS (Doc Issue Survival) [mediana] ↔ Jarczyk Success Rate [producto] | — / CP2 | no |
| EXPRev (Code Review Experience) [p90] ↔ CFDR (Customer Found Defects & Regressions) [producto] | — / CP1 | no |
| EXPRev (Code Review Experience) [p90] ↔ NUB (Bugs Detected by Users) [producto] | — / CP1 | no |
| EXPRev (Code Review Experience) [p90] ↔ Process Performance [producto] | — / CP2 | no |
| EXPRev (Code Review Experience) [share_top10pct] ↔ MTTR (Mean Time to Repair) [producto] | CP3 / CP5 | no |
| MTTR (Mean Time to Repair) [mediana] ↔ DIS (Doc Issue Survival) [producto] | — / — | no |
| MTTR (Mean Time to Repair) [mediana] ↔ NCI (Number of Closed Issues) [producto] | — / CP5 | no |
| MTTR (Mean Time to Repair) [mediana] ↔ Process Performance [producto] | — / CP2 | no |
| NCI (Number of Closed Issues) [p90] ↔ DIS (Doc Issue Survival) [producto] | CP3 / — | no |
| NCI (Number of Closed Issues) [p90] ↔ Jarczyk Success Rate [producto] | CP3 / CP2 | no |
| Proporción que cierra issues [ratio] ↔ Jarczyk Success Rate [producto] | — / CP2 | no |
| Proporción que cierra issues [ratio] ↔ Process Performance [producto] | — / CP2 | no |
| Proporción que comenta [ratio] ↔ ANMCC (Avg Modified Components per Commit) [producto] | — / — | no |
| REXPRev (Recent Review Experience) [mediana] ↔ CFDR (Customer Found Defects & Regressions) [producto] | — / CP1 | no |
| REXPRev (Recent Review Experience) [mediana] ↔ NUB (Bugs Detected by Users) [producto] | — / CP1 | no |
| SC (Social Contribution) [mediana] ↔ Jarczyk Success Rate [producto] | — / CP2 | no |
| Tasa de ingreso (commits) [ratio] ↔ CFDR (Customer Found Defects & Regressions) [producto] | CP1 / CP1 | no |
| Tasa de ingreso (commits) [ratio] ↔ NUB (Bugs Detected by Users) [producto] | CP1 / CP1 | no |

## PCA conjunto

20 variables, 189 releases, Horn retiene 5.

- CP1 (27%): nuevos_commits_conteo (+0.94), tasa_nuevos_commits_ratio (+0.84), activos_commits_conteo (+0.82), le_mediana (-0.81), dev_exp_mediana (-0.80), cdiv_mediana (-0.67)
- CP2 (20%): exprev_share_top10pct (+0.78), sc_share_top10pct (+0.76), sc_p90 (+0.74), nc_share_top10pct (+0.72), cdiv_p90 (+0.63), anmcc_mediana (+0.41)
- CP3 (11%) · **mezcla dimensiones**: cfdr_producto (+0.94), nub_producto (+0.93), prop_commitean_ratio (-0.50)
- CP4 (8%): process_performance_producto (+0.93), jarczyk_success_rate_producto (+0.92)
- CP5 (7%) · **mezcla dimensiones**: mttr_producto (+0.77), nci_producto (+0.68), nci_p90 (+0.60)
