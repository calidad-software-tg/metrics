# Cruce Persona–Proceso

Variables: Persona 28, Proceso 12.

## Variables

| Tipo | Pares |
|---|---|
| patrón | 12 |
| escala | 15 |
| mecánico | 3 |
| no resiste tamaño | 4 |
| control | 2 |

### Patrones (robustos, sin escala ni construcción)

| Par | ρ corregida | con tamaño | canary | alcance |
|---|---|---|---|---|
| SC (Social Contribution) [mediana] ↔ Jarczyk Success Rate [producto] | +0,33 | +0,35 | +0,30 | solo 2020-2024 |
| REXPRev (Recent Review Experience) [mediana] ↔ CFDR (Customer Found Defects & Regressions) [producto] | -0,31 | -0,16 | -0,07 | solo 2023-2024 |
| REXPRev (Recent Review Experience) [mediana] ↔ NUB (Bugs Detected by Users) [producto] | -0,31 | -0,16 | -0,07 | solo 2023-2024 |
| EXPRev (Code Review Experience) [p90] ↔ CFDR (Customer Found Defects & Regressions) [producto] | -0,28 | -0,12 | -0,02 | desde 2025 |
| EXPRev (Code Review Experience) [p90] ↔ NUB (Bugs Detected by Users) [producto] | -0,27 | -0,12 | -0,03 | desde 2025 |
| Tasa de ingreso (commits) [ratio] ↔ CFDR (Customer Found Defects & Regressions) [producto] | +0,24 | +0,11 | +0,07 | sin relación en ningún período |
| Tasa de ingreso (commits) [ratio] ↔ NUB (Bugs Detected by Users) [producto] | +0,23 | +0,11 | +0,07 | sin relación en ningún período |
| Proporción que cierra issues [ratio] ↔ Process Performance [producto] | +0,23 | +0,23 | +0,15 | desde 2025 |
| Proporción que cierra issues [ratio] ↔ Jarczyk Success Rate [producto] | +0,23 | +0,25 | +0,26 | desde 2023 |
| EXPRev (Code Review Experience) [p90] ↔ Process Performance [producto] | +0,22 | +0,22 | +0,03 | solo 2016-2022 |
| EXPRev (Code Review Experience) [share_top10pct] ↔ MTTR (Mean Time to Repair) [producto] | +0,20 | +0,20 | +0,17 | intermitente |
| Proporción que comenta [ratio] ↔ ANMCC (Avg Modified Components per Commit) [producto] | +0,17 | +0,20 | +0,02 | sin relación en ningún período |

## Componentes

- CP1 Persona: nuevos_commits_conteo (+0.88), le_mediana (-0.85), tasa_nuevos_commits_ratio (+0.84), dev_exp_mediana (-0.78) · bootstrap +0,99 · canary +0,96
- CP3 Persona: exprev_share_top10pct (+0.88), nc_share_top10pct (+0.80), sc_share_top10pct (+0.76), sc_p90 (+0.66) · bootstrap +0,97 · canary +0,82
- CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) · bootstrap +0,96 · canary +0,97
- CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) · bootstrap +0,98 · canary +0,99
- CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) · bootstrap +0,95 · canary +0,97

| Par de componentes | ρ corregida | con tamaño | canary | resultado |
|---|---|---|---|---|
| CP1 Persona: nuevos_commits_conteo (+0.88), le_mediana (-0.85), tasa_nuevos_commits_ratio (+0.84), dev_exp_mediana (-0.78) ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,17 | +0,11 | +0,02 | no robusto |
| CP1 Persona: nuevos_commits_conteo (+0.88), le_mediana (-0.85), tasa_nuevos_commits_ratio (+0.84), dev_exp_mediana (-0.78) ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,18 | +0,17 | +0,05 | patrón |
| CP1 Persona: nuevos_commits_conteo (+0.88), le_mediana (-0.85), tasa_nuevos_commits_ratio (+0.84), dev_exp_mediana (-0.78) ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) | +0,15 | +0,14 | +0,07 | patrón |
| CP3 Persona: exprev_share_top10pct (+0.88), nc_share_top10pct (+0.80), sc_share_top10pct (+0.76), sc_p90 (+0.66) ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,28 | -0,18 | +0,02 | no robusto |
| CP3 Persona: exprev_share_top10pct (+0.88), nc_share_top10pct (+0.80), sc_share_top10pct (+0.76), sc_p90 (+0.66) ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,07 | +0,08 | +0,04 | no robusto |
| CP3 Persona: exprev_share_top10pct (+0.88), nc_share_top10pct (+0.80), sc_share_top10pct (+0.76), sc_p90 (+0.66) ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) | +0,21 | +0,26 | +0,16 | no robusto |

## Conjunto reducido

De cada lado: el puntaje de cada componente firme más las variables que no cargan en ningún componente. Persona: 17 elementos · Proceso: 9 · 153 pares.

| Tipo | Pares |
|---|---|
| patrón | 4 |
| escala | 6 |
| mecánico | 1 |
| no resiste tamaño | 0 |
| control | 0 |

| Par | ρ corregida | con tamaño | canary | tipo |
|---|---|---|---|---|
| Activos (interacción) [conteo] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,72 | -0,01 | +0,57 | escala |
| Nuevos contribuyentes (interacción) [conteo] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,68 | -0,03 | +0,54 | escala |
| Activos (comentarios) [conteo] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,68 | -0,13 | +0,46 | escala |
| Activos (cierre de issues) [conteo] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | +0,51 | +0,02 | +0,26 | escala |
| CDIV (Contribution Diversity) [share_top10pct] ↔ ANMCC (Avg Modified Components per Commit) [producto] | +0,43 | +0,45 | +0,17 | mecánico |
| SC (Social Contribution) [mediana] ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,36 | +0,38 | +0,22 | patrón |
| REXPRev (Recent Review Experience) [mediana] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,34 | -0,20 | -0,11 | patrón |
| Activos (cierre de issues) [conteo] ↔ CP5 Proceso: mttr_producto (+0.85), nci_producto (+0.74) | +0,30 | +0,25 | +0,54 | escala |
| Proporción que cierra issues [ratio] ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,29 | +0,30 | +0,31 | patrón |
| EXPRev (Code Review Experience) [p90] ↔ CP1 Proceso: cfdr_producto (+0.98), nub_producto (+0.98) | -0,29 | -0,11 | -0,08 | patrón |
| Activos (cierre de issues) [conteo] ↔ CP2 Proceso: jarczyk_success_rate_producto (+0.93), process_performance_producto (+0.92) | +0,26 | +0,30 | +0,36 | escala |

## Correlación canónica entre componentes

Correlaciones canónicas: +0,33, +0,27 (n = 185). Primera frente a la nula por corrimiento circular: p = 0.013 (percentil 95 nulo +0,28).

## Triangulación

| Par | componentes | par de componentes robusto |
|---|---|---|
| EXPRev (Code Review Experience) [p90] ↔ CFDR (Customer Found Defects & Regressions) [producto] | — / CP1 | no |
| EXPRev (Code Review Experience) [p90] ↔ NUB (Bugs Detected by Users) [producto] | — / CP1 | no |
| EXPRev (Code Review Experience) [p90] ↔ Process Performance [producto] | — / CP2 | no |
| EXPRev (Code Review Experience) [share_top10pct] ↔ MTTR (Mean Time to Repair) [producto] | CP3 / CP5 | no |
| Proporción que cierra issues [ratio] ↔ Jarczyk Success Rate [producto] | — / CP2 | no |
| Proporción que cierra issues [ratio] ↔ Process Performance [producto] | — / CP2 | no |
| Proporción que comenta [ratio] ↔ ANMCC (Avg Modified Components per Commit) [producto] | — / — | no |
| REXPRev (Recent Review Experience) [mediana] ↔ CFDR (Customer Found Defects & Regressions) [producto] | — / CP1 | no |
| REXPRev (Recent Review Experience) [mediana] ↔ NUB (Bugs Detected by Users) [producto] | — / CP1 | no |
| SC (Social Contribution) [mediana] ↔ Jarczyk Success Rate [producto] | — / CP2 | no |
| Tasa de ingreso (commits) [ratio] ↔ CFDR (Customer Found Defects & Regressions) [producto] | CP1 / CP1 | no |
| Tasa de ingreso (commits) [ratio] ↔ NUB (Bugs Detected by Users) [producto] | CP1 / CP1 | no |

## PCA conjunto

19 variables, 189 releases, Horn retiene 4.

- CP1 (27%): nuevos_commits_conteo (+0.94), tasa_nuevos_commits_ratio (+0.84), dev_exp_mediana (-0.81), le_mediana (-0.81), activos_commits_conteo (+0.80), cdiv_mediana (-0.69)
- CP2 (21%): exprev_share_top10pct (+0.90), nc_share_top10pct (+0.83), sc_p90 (+0.74), sc_share_top10pct (+0.69), cdiv_p90 (+0.52), prop_commitean_ratio (+0.45)
- CP3 (11%) · **mezcla dimensiones**: cfdr_producto (+0.92), nub_producto (+0.92), nci_producto (+0.50), prop_commitean_ratio (-0.47)
- CP4 (8%): process_performance_producto (+0.93), jarczyk_success_rate_producto (+0.90)
