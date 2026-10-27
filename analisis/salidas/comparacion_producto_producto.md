# Antes y después de los fixes · Producto–Producto

## Correlaciones · Producto–Producto

| Categoría | Antes | Después |
|---|---|---|
| positiva | 7 | 11 |
| negativa | 9 | 9 |
| sin_relacion | 50 | 91 |
| no_concluyente | 59 | 145 |
| insuficiente | 0 | 0 |
| control | 11 | 20 |
| **Robustas** | 7 | 7 |
| Pares en total | 136 | 276 |

### Robustas que se mantienen (1)

| Par | ρ corregida antes | ρ corregida después |
|---|---|---|
| CFDR (Customer Found Defects & Regressions) [producto] ↔ NUB (Bugs Detected by Users) [producto] | +1.00 (positiva) | +1.00 (positiva) |

### Robustas que se pierden (6)

| Par | ρ corregida antes | ρ corregida después |
|---|---|---|
| CD (Comment Density) [producto] ↔ DLOC (Documentation Lines of Code) [producto] | -0.66 (negativa) | -0.53 (negativa) |
| CFDR (Customer Found Defects & Regressions) [producto] ↔ MTTR (Mean Time to Repair) [mediana] | -0.22 (negativa) | -0.06 (no_concluyente) |
| DLOC (Documentation Lines of Code) [p90] ↔ RC (Readme Completeness) [mediana] | -0.33 (negativa) | +0.46 (positiva) |
| DLOC (Documentation Lines of Code) [producto] ↔ RC (Readme Completeness) [mediana] | -0.41 (negativa) | +0.22 (no_concluyente) |
| DLOC (Documentation Lines of Code) [producto] ↔ RC (Readme Completeness) [producto] | -0.44 (negativa) | +0.22 (no_concluyente) |
| MTTR (Mean Time to Repair) [mediana] ↔ NUB (Bugs Detected by Users) [producto] | -0.22 (negativa) | -0.06 (no_concluyente) |

### Robustas nuevas (6)

| Par | ρ corregida antes | ρ corregida después |
|---|---|---|
| ANMCC (Avg Modified Components per Commit) [mediana] ↔ CFDR (Customer Found Defects & Regressions) [producto] | -0.16 (no_concluyente) | -0.26 (negativa) |
| ANMCC (Avg Modified Components per Commit) [mediana] ↔ Commits que tocan documentación (proporción) [producto] | no existía | -0.46 (negativa) |
| ANMCC (Avg Modified Components per Commit) [mediana] ↔ LE (Learning Ease) [mediana] | +0.39 (positiva) | +0.48 (positiva) |
| ANMCC (Avg Modified Components per Commit) [mediana] ↔ NUB (Bugs Detected by Users) [producto] | -0.15 (no_concluyente) | -0.26 (negativa) |
| Commits que tocan documentación (proporción) [producto] ↔ DLOC flujo (líneas de documentación cambiadas en la ventana) [producto] | no existía | +0.47 (positiva) |
| MTTR con bots [producto] ↔ NOI (Number of Open Issues) [producto] | no existía | -0.34 (negativa) |

### Pares con el mayor cambio de ρ corregida

| Par | Antes | Después |
|---|---|---|
| DLOC (Documentation Lines of Code) [p90] ↔ RC (Readme Completeness) [mediana] | -0.33 (negativa) | +0.46 (positiva) |
| DLOC (Documentation Lines of Code) [producto] ↔ RC (Readme Completeness) [producto] | -0.44 (negativa) | +0.22 (no_concluyente) |
| CD (Comment Density) [producto] ↔ DLOC (Documentation Lines of Code) [p90] | -0.15 (no_concluyente) | +0.48 (positiva) |
| DLOC (Documentation Lines of Code) [producto] ↔ RC (Readme Completeness) [mediana] | -0.41 (negativa) | +0.22 (no_concluyente) |
| RC (Readme Completeness) [mediana] ↔ RC (Readme Completeness) [producto] | +0.42 (control) | +1.00 (control) |
| DLOC (Documentation Lines of Code) [p90] ↔ RC (Readme Completeness) [producto] | -0.09 (no_concluyente) | +0.46 (positiva) |
| CD (Comment Density) [producto] ↔ DLOC (Documentation Lines of Code) [share_top10pct] | -0.41 (negativa) | +0.01 (no_concluyente) |
| DLOC (Documentation Lines of Code) [producto] ↔ DLOC (Documentation Lines of Code) [share_top10pct] | +0.22 (control) | -0.20 (control) |
| DLOC (Documentation Lines of Code) [producto] ↔ NOI (Number of Open Issues) [producto] | -0.36 (negativa) | +0.03 (sin_relacion) |
| DLOC (Documentation Lines of Code) [mediana] ↔ DLOC (Documentation Lines of Code) [share_top10pct] | -0.04 (control) | -0.41 (control) |

## Componentes principales · Producto

### producto|estable|ajustado (estables, ajustado)

| | Antes | Después |
|---|---|---|
| Releases | 200 | 185 |
| Variables | 9 | 13 |
| Componentes (Horn) | 3 | 4 |
| Varianza explicada | 63 % | 55 % |

Variables nuevas: commits_doc_producto, dloc_flujo_producto, nob_42_producto, wp_producto. Variables que ya no están: ninguna.

Componentes emparejados por la congruencia de Tucker sobre las variables comunes (≥ 0,95: el mismo; 0,85–0,95: parecido; < 0,85: distinto):

| Antes | Después | Congruencia |
|---|---|---|
| CP1: cfdr_producto (+0.99), nub_producto (+0.99) | CP1: cfdr_producto (+0.97), nub_producto (+0.97) | 0.95 |
| CP2: cd_producto (+0.87), dloc_producto (-0.86), rc_producto (+0.71) | CP2: wp_producto (+0.82), cd_producto (+0.76), nob_42_producto (+0.62) | 0.82 |
| CP3: mttr_producto (+0.76), noi_producto (-0.75), le_producto (+0.47) | CP3: rc_producto (+0.73), noi_producto (+0.70), anmcc_producto (-0.54) | 0.35 |
| — | CP4: dloc_flujo_producto (+0.82), commits_doc_producto (+0.77), le_producto (-0.41) (nuevo) | — |

### todas|estable|ajustado (estables, ajustado)

| | Antes | Después |
|---|---|---|
| Releases | 196 | 184 |
| Variables | 17 | 21 |
| Componentes (Horn) | 5 | 7 |
| Varianza explicada | 61 % | 67 % |

Variables nuevas: commits_doc_producto, dloc_flujo_producto, nob_42_producto, wp_producto. Variables que ya no están: ninguna.

Componentes emparejados por la congruencia de Tucker sobre las variables comunes (≥ 0,95: el mismo; 0,85–0,95: parecido; < 0,85: distinto):

| Antes | Después | Congruencia |
|---|---|---|
| CP1: cd_producto (+0.81), dloc_producto (-0.78), rc_mediana (+0.73), rc_producto (+0.71), dloc_share_top10pct (-0.47), dloc_p90 (-0.41) | CP1: rc_mediana (+0.93), rc_producto (+0.93), noi_producto (+0.58), dloc_share_top10pct (-0.56) | 0.55 |
| CP2: cfdr_producto (+0.94), nub_producto (+0.94) | CP2: cfdr_producto (+0.97), nub_producto (+0.97) | 0.92 |
| CP3: le_mediana (+0.80), anmcc_mediana (+0.75), le_producto (+0.61), anmcc_producto (+0.56) | CP4: le_mediana (+0.87), le_producto (+0.67), anmcc_mediana (+0.61) | 0.95 |
| CP4: mttr_producto (+0.84), noi_producto (-0.60), mttr_mediana (+0.49) | CP5: mttr_producto (+0.83), mttr_mediana (+0.83), dloc_producto (+0.42) | 0.59 |
| CP5: dloc_mediana (+0.83), dloc_share_top10pct (-0.64), dloc_p90 (+0.55) | CP6: dloc_mediana (+0.80), cd_mediana (-0.54), dloc_share_top10pct (-0.50) | 0.76 |
| — | CP3: wp_producto (+0.84), cd_producto (+0.80), dloc_p90 (+0.59), nob_42_producto (+0.40) (nuevo) | — |
| — | CP7: dloc_flujo_producto (+0.82), commits_doc_producto (+0.71) (nuevo) | — |
