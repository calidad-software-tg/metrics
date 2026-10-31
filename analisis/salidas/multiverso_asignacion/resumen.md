# Multiverso de asignaciones de las métricas compartidas

16 métricas compartidas (anmcc, cd, cdiv, cfdr, dev_exp, exprev, le, mttr, nc, nob_42, noi, nub, rc, rexprev, sc, wp). Universos: la asignación principal, cada métrica cambiada de lado sola, la opuesta y 500 al azar. Los porcentajes son sobre las asignaciones al azar.

## 1. Cruce de variables

Todos los pares que son patrón en algún nivel (dentro de cada dimensión o en los cruces). Proporción de las asignaciones posibles en la que relacionan dimensiones distintas; la correlación es la misma en todas.

Pares de un mismo tema (por ejemplo, dos medidas de la concentración del núcleo) que quedan entre dimensiones solo si ese tema se reparte entre dos dimensiones: 16 de los nuevos.

- **entre dimensiones con cualquier asignación:** 18
- **depende de la asignación:** 13
- **nuevo: solo con otras asignaciones:** 31
- **siempre dentro de una dimensión:** 12

### Nuevo: solo con otras asignaciones

| Par | ρ | Catálogo | Principal | Entre dimensiones | Lecturas |
|---|---|---|---|---|---|
| cdiv_mediana ↔ le_mediana (mismo tema) | +0.49 | Persona+Proceso / Persona+Producto | dentro de Persona | 75% | dentro de Persona 25%; Persona–Producto 25%; Persona–Proceso 25%; Proceso–Producto 25% |
| cfdr_producto ↔ nub_producto (mismo tema) | +1.00 | Proceso+Producto / Proceso+Producto | dentro de Producto | 50% | Proceso–Producto 50%; dentro de Proceso 25%; dentro de Producto 25% |
| le_mediana ↔ tasa_nuevos_commits_ratio (mismo tema) | -0.73 | Persona+Producto / Persona | dentro de Persona | 50% | dentro de Persona 50%; Persona–Producto 50% |
| dev_exp_mediana ↔ tasa_nuevos_commits_ratio (mismo tema) | -0.71 | Persona+Proceso / Persona | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| exprev_share_top10pct ↔ prop_commitean_ratio | +0.47 | Persona+Proceso / Persona | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| prop_commitean_ratio ↔ sc_p90 | +0.47 | Persona / Persona+Proceso | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| nc_share_top10pct ↔ sc_p90 (mismo tema) | +0.47 | Persona+Proceso / Persona+Proceso | dentro de Persona | 50% | Persona–Proceso 50%; dentro de Persona 25%; dentro de Proceso 25% |
| cdiv_p90 ↔ sc_share_top10pct (mismo tema) | +0.46 | Persona+Proceso / Persona+Proceso | dentro de Persona | 50% | Persona–Proceso 50%; dentro de Persona 25%; dentro de Proceso 25% |
| anmcc_mediana ↔ commits_doc_producto | -0.45 | Proceso+Producto / Producto | dentro de Producto | 50% | Proceso–Producto 50%; dentro de Producto 50% |
| cdiv_mediana ↔ tasa_nuevos_commits_ratio (mismo tema) | -0.44 | Persona+Proceso / Persona | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| cdiv_mediana ↔ rexp_mediana (mismo tema) | +0.44 | Persona+Proceso / Persona | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| nc_share_top10pct ↔ prop_commitean_ratio | +0.43 | Persona+Proceso / Persona | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| nc_share_top10pct ↔ sc_share_top10pct (mismo tema) | +0.42 | Persona+Proceso / Persona+Proceso | dentro de Persona | 50% | Persona–Proceso 50%; dentro de Persona 25%; dentro de Proceso 25% |
| cdiv_mediana ↔ dev_exp_mediana (mismo tema) | +0.41 | Persona+Proceso / Persona+Proceso | dentro de Persona | 50% | Persona–Proceso 50%; dentro de Persona 25%; dentro de Proceso 25% |
| prop_commitean_ratio ↔ sc_mediana | +0.35 | Persona / Persona+Proceso | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| le_mediana ↔ prop_commitean_ratio (mismo tema) | -0.33 | Persona+Producto / Persona | dentro de Persona | 50% | dentro de Persona 50%; Persona–Producto 50% |
| dis_producto ↔ mttr_mediana | +0.32 | Proceso / Proceso+Producto | dentro de Proceso | 50% | dentro de Proceso 50%; Proceso–Producto 50% |
| nc_share_top10pct ↔ sc_mediana | +0.31 | Persona+Proceso / Persona+Proceso | dentro de Persona | 50% | Persona–Proceso 50%; dentro de Persona 25%; dentro de Proceso 25% |
| exprev_p90 ↔ prop_cierran_ratio | +0.31 | Persona+Proceso / Persona | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| prop_cierran_ratio ↔ rexprev_mediana | +0.30 | Persona / Persona+Proceso | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| dev_exp_mediana ↔ prop_commitean_ratio (mismo tema) | -0.30 | Persona+Proceso / Persona | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| mttr_producto ↔ nci_producto (mismo tema) | +0.29 | Proceso+Producto / Proceso | dentro de Proceso | 50% | dentro de Proceso 50%; Proceso–Producto 50% |
| cdiv_p90 ↔ tasa_nuevos_commits_ratio | -0.29 | Persona+Proceso / Persona | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| le_mediana ↔ rexp_mediana (mismo tema) | +0.29 | Persona+Producto / Persona | dentro de Persona | 50% | dentro de Persona 50%; Persona–Producto 50% |
| nc_share_top10pct ↔ prop_cierran_ratio | +0.27 | Persona+Proceso / Persona | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| prop_commitean_ratio ↔ rexprev_mediana | +0.25 | Persona / Persona+Proceso | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| prop_cierran_ratio ↔ sc_p90 | +0.25 | Persona / Persona+Proceso | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| cdiv_p90 ↔ rexp_mediana | +0.24 | Persona+Proceso / Persona | dentro de Persona | 50% | dentro de Persona 50%; Persona–Proceso 50% |
| cdiv_p90 ↔ sc_p90 (mismo tema) | +0.19 | Persona+Proceso / Persona+Proceso | dentro de Persona | 50% | Persona–Proceso 50%; dentro de Persona 25%; dentro de Proceso 25% |
| mttr_mediana ↔ nci_producto (mismo tema) | +0.18 | Proceso+Producto / Proceso | dentro de Proceso | 50% | dentro de Proceso 50%; Proceso–Producto 50% |
| mttr_mediana ↔ process_performance_producto | -0.18 | Proceso+Producto / Proceso | dentro de Proceso | 50% | dentro de Proceso 50%; Proceso–Producto 50% |

### Depende de la asignación

| Par | ρ | Catálogo | Principal | Entre dimensiones | Lecturas |
|---|---|---|---|---|---|
| anmcc_mediana ↔ le_mediana | +0.48 | Proceso+Producto / Persona+Producto | Persona–Producto | 75% | Persona–Proceso 25%; Proceso–Producto 25%; Persona–Producto 25%; dentro de Producto 25% |
| anmcc_mediana ↔ dev_exp_mediana | +0.38 | Proceso+Producto / Persona+Proceso | Persona–Producto | 75% | Persona–Proceso 25%; dentro de Proceso 25%; Persona–Producto 25%; Proceso–Producto 25% |
| cfdr_producto ↔ rexprev_mediana | -0.31 | Proceso+Producto / Persona+Proceso | Persona–Producto | 75% | Persona–Proceso 25%; dentro de Proceso 25%; Persona–Producto 25%; Proceso–Producto 25% |
| nub_producto ↔ rexprev_mediana | -0.31 | Proceso+Producto / Persona+Proceso | Persona–Producto | 75% | Persona–Proceso 25%; dentro de Proceso 25%; Persona–Producto 25%; Proceso–Producto 25% |
| cfdr_producto ↔ exprev_p90 | -0.28 | Proceso+Producto / Persona+Proceso | Persona–Producto | 75% | Persona–Proceso 25%; dentro de Proceso 25%; Persona–Producto 25%; Proceso–Producto 25% |
| exprev_p90 ↔ nub_producto | -0.27 | Persona+Proceso / Proceso+Producto | Persona–Producto | 75% | Persona–Proceso 25%; Persona–Producto 25%; dentro de Proceso 25%; Proceso–Producto 25% |
| dev_exp_mediana ↔ mttr_mediana | -0.23 | Persona+Proceso / Proceso+Producto | Persona–Proceso | 75% | Persona–Proceso 25%; Persona–Producto 25%; dentro de Proceso 25%; Proceso–Producto 25% |
| exprev_share_top10pct ↔ mttr_producto | +0.20 | Persona+Proceso / Proceso+Producto | Persona–Proceso | 75% | Persona–Proceso 25%; Persona–Producto 25%; dentro de Proceso 25%; Proceso–Producto 25% |
| jarczyk_success_rate_producto ↔ sc_mediana | +0.33 | Proceso / Persona+Proceso | Persona–Proceso | 50% | Persona–Proceso 50%; dentro de Proceso 50% |
| nc_share_top10pct ↔ nci_p90 | +0.29 | Persona+Proceso / Proceso | Persona–Proceso | 50% | Persona–Proceso 50%; dentro de Proceso 50% |
| dis_producto ↔ rexprev_mediana | +0.24 | Proceso / Persona+Proceso | Persona–Proceso | 50% | Persona–Proceso 50%; dentro de Proceso 50% |
| exprev_p90 ↔ process_performance_producto | +0.22 | Persona+Proceso / Proceso | Persona–Proceso | 50% | Persona–Proceso 50%; dentro de Proceso 50% |
| exprev_p90 ↔ jarczyk_success_rate_producto | +0.18 | Persona+Proceso / Proceso | Persona–Proceso | 50% | Persona–Proceso 50%; dentro de Proceso 50% |

### Entre dimensiones con cualquier asignación

| Par | ρ | Catálogo | Principal | Entre dimensiones | Lecturas |
|---|---|---|---|---|---|
| cdiv_mediana ↔ commits_doc_producto | -0.42 | Persona+Proceso / Producto | Persona–Producto | 100% | Persona–Producto 50%; Proceso–Producto 50% |
| prop_commitean_ratio ↔ le_producto | -0.29 | Persona / Producto | Persona–Producto | 100% | Persona–Producto 100% |
| exprev_share_top10pct ↔ dloc_flujo_producto | +0.29 | Persona+Proceso / Producto | Persona–Producto | 100% | Persona–Producto 50%; Proceso–Producto 50% |
| cdiv_p90 ↔ cd_producto | +0.28 | Persona+Proceso / Producto | Persona–Producto | 100% | Persona–Producto 50%; Proceso–Producto 50% |
| tasa_nuevos_commits_ratio ↔ le_producto | -0.26 | Persona / Producto | Persona–Producto | 100% | Persona–Producto 100% |
| tasa_nuevos_commits_ratio ↔ cfdr_producto | +0.24 | Persona / Proceso+Producto | Persona–Producto | 100% | Persona–Proceso 50%; Persona–Producto 50% |
| tasa_nuevos_commits_ratio ↔ nub_producto | +0.23 | Persona / Proceso+Producto | Persona–Producto | 100% | Persona–Proceso 50%; Persona–Producto 50% |
| prop_cierran_ratio ↔ process_performance_producto | +0.23 | Persona / Proceso | Persona–Proceso | 100% | Persona–Proceso 100% |
| prop_cierran_ratio ↔ jarczyk_success_rate_producto | +0.23 | Persona / Proceso | Persona–Proceso | 100% | Persona–Proceso 100% |
| nc_p90 ↔ le_producto | -0.22 | Persona+Proceso / Producto | Persona–Producto | 100% | Persona–Producto 50%; Proceso–Producto 50% |
| nci_producto ↔ dloc_flujo_producto | +0.22 | Proceso / Producto | Proceso–Producto | 100% | Proceso–Producto 100% |
| nc_share_top10pct ↔ dloc_flujo_producto | +0.21 | Persona+Proceso / Producto | Persona–Producto | 100% | Persona–Producto 50%; Proceso–Producto 50% |
| prop_commitean_ratio ↔ dloc_flujo_producto | +0.21 | Persona / Producto | Persona–Producto | 100% | Persona–Producto 100% |
| exprev_share_top10pct ↔ le_producto | -0.20 | Persona+Proceso / Producto | Persona–Producto | 100% | Persona–Producto 50%; Proceso–Producto 50% |
| sc_p90 ↔ dloc_flujo_producto | +0.20 | Persona+Proceso / Producto | Persona–Producto | 100% | Persona–Producto 50%; Proceso–Producto 50% |
| nc_share_top10pct ↔ le_producto | -0.20 | Persona+Proceso / Producto | Persona–Producto | 100% | Persona–Producto 50%; Proceso–Producto 50% |
| prop_cierran_ratio ↔ dloc_mediana | -0.20 | Persona / Producto | Persona–Producto | 100% | Persona–Producto 100% |
| prop_comentan_ratio ↔ anmcc_producto | +0.17 | Persona / Proceso+Producto | Persona–Producto | 100% | Persona–Proceso 50%; Persona–Producto 50% |

## 2. Cruces de a pares que dependen de la asignación

Patrones de componentes, grupos y del conjunto reducido (reconocidos por su tema), componentes y grupos conjuntos que mezclan dos dimensiones, y triangulaciones: proporción de asignaciones en que aparecen y si aparecen con la asignación principal. «Decide»: métrica compartida cuyo lado cambia en 30 puntos o más esa proporción.

- Correlación canónica Persona–Proceso: mayor que el azar en el 100% de las asignaciones; principal 0.45 (p 0.005)
- Correlación canónica Persona–Producto: mayor que el azar en el 99% de las asignaciones; principal 0.61 (p 0.005)
- Correlación canónica Proceso–Producto: mayor que el azar en el 81% de las asignaciones; principal 0.33 (p 0.100)

### Componentes

| Patrón | Asignaciones | Con la principal | Decide |
|---|---|---|---|
| Persona:participación ↔ Proceso:resolución de lo nuevo | 81% | no | — |
| Persona:renovación y experiencia ↔ Proceso:resolución de lo nuevo | 47% | no | — |
| Persona:renovación y experiencia ↔ Producto:documentación | 45% | no | — |
| Persona:renovación y experiencia ↔ Proceso:concentración del núcleo | 40% | no | — |
| Persona:concentración del núcleo ↔ Proceso:concentración del núcleo (mismo tema) | 35% | no | — |
| Persona:concentración del núcleo ↔ Producto:documentación | 28% | no | — |
| Proceso:resolución de lo nuevo ↔ Producto:documentación | 27% | no | — |
| Proceso:concentración del núcleo ↔ Producto:documentación | 27% | no | — |
| Persona:participación ↔ Proceso:revisores más activos | 26% | no | nc en Proceso (45% vs 5%) |
| Persona:renovación y experiencia ↔ Proceso:cierre de lo viejo | 22% | sí | mttr en Proceso (46% vs 2%) |
| Persona:participación ↔ Proceso:concentración del núcleo | 21% | no | nc en Proceso (38% vs 3%) |
| Persona:revisores más activos ↔ Proceso:resolución de lo nuevo | 21% | no | — |
| Persona:concentración del núcleo ↔ Proceso:revisores más activos | 19% | no | — |
| Proceso:concentración del núcleo ↔ Producto:bugs de usuarios | 19% | no | — |
| Persona:concentración del núcleo ↔ Proceso:cierre de lo viejo | 19% | sí | mttr en Proceso (40% vs 1%) |
| Persona:renovación y experiencia ↔ Proceso:renovación y experiencia (mismo tema) | 17% | no | cdiv en Proceso (34% vs 0%) |
| Persona:revisores más activos ↔ Proceso:concentración del núcleo | 14% | no | — |
| Proceso:resolución de lo nuevo ↔ Producto:bugs de usuarios | 13% | no | — |
| Proceso:renovación y experiencia ↔ Producto:documentación | 12% | no | — |
| Persona:participación ↔ Proceso:cierre de lo viejo | 12% | no | — |
| Persona:concentración del núcleo ↔ Proceso:bugs de usuarios | 12% | no | — |
| Persona:concentración del núcleo ↔ Producto:bugs de usuarios | 11% | sí | — |
| Proceso:revisores más activos ↔ Producto:documentación | 11% | no | — |
| Proceso:revisores más activos ↔ Producto:bugs de usuarios | 10% | no | — |

### Conjunto reducido

| Patrón | Asignaciones | Con la principal | Decide |
|---|---|---|---|
| Persona:participación ↔ Proceso:resolución de lo nuevo | 80% | no | — |
| Persona:renovación y experiencia ↔ Producto:documentación | 43% | no | — |
| Persona:renovación y experiencia ↔ Proceso:resolución de lo nuevo | 41% | no | — |
| Persona:renovación y experiencia ↔ Proceso:concentración del núcleo | 40% | no | — |
| Persona:concentración del núcleo ↔ Proceso:concentración del núcleo (mismo tema) | 35% | no | — |
| Persona:sc_mediana ↔ Proceso:resolución de lo nuevo | 35% | sí | sc en Persona (64% vs 0%) |
| Proceso:concentración del núcleo ↔ Producto:documentación | 27% | no | — |
| Persona:concentración del núcleo ↔ Producto:documentación | 25% | no | — |
| Proceso:resolución de lo nuevo ↔ Producto:documentación | 24% | no | — |
| Persona:participación ↔ Proceso:revisores más activos | 24% | no | nc en Proceso (43% vs 3%) |
| Persona:renovación y experiencia ↔ Proceso:cierre de lo viejo | 22% | sí | mttr en Proceso (45% vs 2%) |
| Persona:participación ↔ Proceso:concentración del núcleo | 21% | no | nc en Proceso (38% vs 2%) |
| Persona:revisores más activos ↔ Proceso:resolución de lo nuevo | 19% | no | — |
| Persona:concentración del núcleo ↔ Proceso:revisores más activos | 19% | no | — |
| Proceso:concentración del núcleo ↔ Producto:bugs de usuarios | 19% | no | — |
| Persona:concentración del núcleo ↔ Proceso:cierre de lo viejo | 19% | sí | mttr en Proceso (40% vs 1%) |
| Persona:renovación y experiencia ↔ Proceso:renovación y experiencia (mismo tema) | 17% | no | cdiv en Proceso (34% vs 0%) |
| Persona:revisores más activos ↔ Proceso:concentración del núcleo | 14% | no | — |
| Persona:sc_mediana ↔ Proceso:concentración del núcleo | 12% | no | — |
| Proceso:resolución de lo nuevo ↔ Producto:bugs de usuarios | 12% | no | — |
| Proceso:renovación y experiencia ↔ Producto:documentación | 12% | no | — |
| Persona:concentración del núcleo ↔ Proceso:bugs de usuarios | 12% | no | — |
| Persona:concentración del núcleo ↔ Producto:bugs de usuarios | 11% | sí | — |
| Persona:participación ↔ Proceso:cierre de lo viejo | 11% | no | — |
| Proceso:revisores más activos ↔ Producto:documentación | 11% | no | — |
| Proceso:revisores más activos ↔ Producto:bugs de usuarios | 10% | no | — |

### Grupos

| Patrón | Asignaciones | Con la principal | Decide |
|---|---|---|---|
| Proceso:resolución de lo nuevo ↔ Producto:documentación | 46% | no | — |
| Persona:renovación y experiencia ↔ Proceso:resolución de lo nuevo | 45% | no | dev_exp en Persona (67% vs 17%) |
| Persona:renovación y experiencia ↔ Proceso:concentración del núcleo | 21% | no | cdiv en Proceso (40% vs 0%); dev_exp en Persona (35% vs 2%) |
| Proceso:concentración del núcleo ↔ Producto:documentación | 20% | no | — |
| Persona:concentración del núcleo ↔ Proceso:resolución de lo nuevo | 19% | no | sc en Persona (35% vs 0%) |
| Persona:revisores más activos ↔ Proceso:resolución de lo nuevo | 19% | no | — |
| Persona:renovación y experiencia ↔ Producto:documentación | 18% | no | — |
| Persona:revisores más activos ↔ Producto:documentación | 18% | sí | — |
| Persona:revisores más activos ↔ Proceso:concentración del núcleo | 18% | no | sc en Proceso (39% vs 0%) |
| Persona:concentración del núcleo ↔ Producto:documentación | 17% | no | sc en Persona (31% vs 0%) |
| Persona:concentración del núcleo ↔ Proceso:revisores más activos | 14% | no | — |
| Proceso:revisores más activos ↔ Producto:documentación | 14% | no | — |
| Persona:volumen de actividad ↔ Proceso:concentración del núcleo | 12% | no | — |
| Persona:concentración del núcleo ↔ Proceso:bugs de usuarios | 10% | no | — |
| Proceso:resolución de lo nuevo ↔ Producto:bugs de usuarios | 6% | sí | — |

### Triangulación

| Patrón | Asignaciones | Con la principal | Decide |
|---|---|---|---|
| Persona:prop_cierran_ratio ↔ Proceso:jarczyk_success_rate_producto | 85% | no | — |
| Persona:prop_cierran_ratio ↔ Proceso:process_performance_producto | 85% | no | — |
| Persona:prop_commitean_ratio ↔ Producto:dloc_flujo_producto | 38% | no | — |
| Persona:prop_cierran_ratio ↔ Proceso:nc_share_top10pct | 35% | no | nc en Proceso (68% vs 0%) |
| Persona:tasa_nuevos_commits_ratio ↔ Proceso:cdiv_mediana | 35% | no | cdiv en Proceso (70% vs 0%) |
| Persona:prop_commitean_ratio ↔ Proceso:exprev_share_top10pct | 35% | no | exprev en Proceso (71% vs 0%) |
| Persona:exprev_p90 ↔ Proceso:process_performance_producto | 33% | no | exprev en Persona (65% vs 0%) |
| Persona:exprev_p90 ↔ Proceso:jarczyk_success_rate_producto | 33% | no | exprev en Persona (65% vs 0%) |
| Persona:prop_commitean_ratio ↔ Proceso:nc_share_top10pct | 32% | no | nc en Proceso (63% vs 0%) |
| Persona:rexp_mediana ↔ Proceso:cdiv_mediana | 30% | no | cdiv en Proceso (60% vs 0%) |
| Persona:prop_cierran_ratio ↔ Proceso:exprev_p90 | 27% | no | exprev en Proceso (55% vs 0%) |
| Persona:tasa_nuevos_commits_ratio ↔ Proceso:cdiv_p90 | 27% | no | cdiv en Proceso (54% vs 0%) |
| Persona:sc_p90 ↔ Proceso:nc_share_top10pct | 26% | no | nc en Proceso (51% vs 0%); sc en Persona (49% vs 0%) |
| Persona:prop_commitean_ratio ↔ Proceso:sc_p90 | 26% | no | sc en Proceso (56% vs 0%) |
| Proceso:nci_producto ↔ Producto:dloc_flujo_producto | 25% | no | — |
| Persona:prop_cierran_ratio ↔ Proceso:sc_p90 | 25% | no | sc en Proceso (53% vs 0%) |
| Persona:dev_exp_mediana ↔ Proceso:cdiv_mediana | 25% | no | cdiv en Proceso (49% vs 0%); dev_exp en Persona (44% vs 0%) |
| Persona:rexp_mediana ↔ Proceso:cdiv_p90 | 24% | no | cdiv en Proceso (48% vs 0%) |
| Persona:prop_cierran_ratio ↔ Proceso:rexprev_mediana | 24% | no | rexprev en Proceso (45% vs 0%) |
| Proceso:cdiv_p90 ↔ Producto:cd_producto | 23% | no | cdiv en Proceso (46% vs 0%) |
| Persona:nc_share_top10pct ↔ Proceso:sc_p90 | 23% | no | nc en Persona (47% vs 0%); sc en Proceso (49% vs 0%) |
| Persona:prop_commitean_ratio ↔ Proceso:sc_mediana | 23% | no | sc en Proceso (49% vs 0%) |
| Persona:sc_share_top10pct ↔ Proceso:nc_share_top10pct | 23% | no | nc en Proceso (44% vs 0%); sc en Persona (42% vs 0%) |
| Persona:nc_share_top10pct ↔ Proceso:sc_share_top10pct | 21% | no | nc en Persona (44% vs 0%); sc en Proceso (46% vs 0%) |
| Persona:prop_commitean_ratio ↔ Proceso:rexprev_mediana | 20% | no | rexprev en Proceso (38% vs 0%) |
| Persona:cdiv_mediana ↔ Producto:commits_doc_producto | 19% | no | cdiv en Persona (39% vs 0%) |
| Persona:prop_commitean_ratio ↔ Proceso:dev_exp_mediana | 19% | no | dev_exp en Proceso (44% vs 0%) |
| Persona:exprev_share_top10pct ↔ Proceso:mttr_producto | 18% | sí | exprev en Persona (37% vs 0%); mttr en Proceso (39% vs 0%) |
| Persona:tasa_nuevos_commits_ratio ↔ Proceso:dev_exp_mediana | 17% | no | dev_exp en Proceso (39% vs 0%); le en Producto (33% vs 0%) |
| Proceso:cdiv_mediana ↔ Producto:commits_doc_producto | 17% | no | cdiv en Proceso (33% vs 0%) |

### PCA y clustering conjunto (componentes y grupos que mezclan las dos dimensiones, sin escala)

| Análisis | Temas | Asignaciones | Con la principal |
|---|---|---|---|
| PCA conjunto Persona–Proceso | Persona:renovación y experiencia + Persona:volumen de actividad + Proceso:concentración del núcleo + Proceso:renovación y experiencia | 38% | no |
| PCA conjunto Persona–Proceso | Persona:participación + Persona:volumen de actividad + Proceso:cierre de lo viejo + Proceso:resolución de lo nuevo | 34% | no |
| PCA conjunto Persona–Proceso | Persona:participación + Persona:renovación y experiencia + Proceso:cierre de lo viejo | 3% | sí |
| PCA conjunto Persona–Producto | Persona:renovación y experiencia + Persona:volumen de actividad + Producto:documentación + Producto:renovación y experiencia | 39% | no |
| PCA conjunto Persona–Producto | Persona:renovación y experiencia + Persona:volumen de actividad + Producto:documentación | 34% | sí |
| PCA conjunto Persona–Producto | Persona:participación + Producto:README e issues abiertas + Producto:tamaño de los cambios | 8% | sí |
| PCA conjunto Proceso–Producto | Proceso:Wiki y branches + Producto:documentación | 21% | no |
| PCA conjunto Proceso–Producto | Proceso:resolución de lo nuevo + Producto:documentación | 16% | sí |
| clustering conjunto Persona–Proceso | Persona:concentración del núcleo + Persona:participación + Persona:renovación y experiencia + Persona:revisores más activos + Persona:volumen de actividad + Proceso:bugs de usuarios + Proceso:cierre de lo viejo + Proceso:concentración del núcleo + Proceso:revisores más activos | 22% | no |
| clustering conjunto Persona–Proceso | Persona:participación + Proceso:README e issues abiertas | 21% | no |
| clustering conjunto Persona–Proceso | Persona:participación + Persona:renovación y experiencia + Persona:volumen de actividad + Proceso:cierre de lo viejo | 7% | sí |
| clustering conjunto Persona–Producto | Persona:concentración del núcleo + Persona:participación + Persona:renovación y experiencia + Persona:revisores más activos + Persona:volumen de actividad + Producto:bugs de usuarios | 26% | sí |
| clustering conjunto Persona–Producto | Persona:renovación y experiencia + Persona:volumen de actividad + Producto:documentación | 17% | sí |
| clustering conjunto Persona–Producto | Persona:participación + Producto:README e issues abiertas | 7% | sí |
| clustering conjunto Persona–Producto | Persona:concentración del núcleo + Producto:documentación + Producto:tamaño de los cambios | 3% | sí |
| clustering conjunto Proceso–Producto | Proceso:Wiki y branches + Producto:documentación | 25% | no |
| clustering conjunto Proceso–Producto | Proceso:cierre de lo viejo + Proceso:resolución de lo nuevo + Producto:bugs de usuarios | 9% | sí |

## 3. Tres dimensiones

| Resultado | Asignaciones al azar | Principal |
|---|---|---|
| Correlación canónica generalizada mayor que el azar | 100% | sí |
| RV medio mayor que el azar | 100% | sí |
| Primer factor del MFA mayor que el azar | 100% | sí |
| Patrón candidato (concentración + cierre de lo viejo + bugs, en tres dimensiones) | 0% | no |

Factores del MFA (de los tres primeros) que juntan las tres dimensiones, por frecuencia:

| Temas (dimensiones:tema) | Asignaciones | Con la principal |
|---|---|---|
| Persona/Proceso/Producto:renovación y experiencia + Producto:documentación | 15% | no |
| Persona/Proceso:renovación y experiencia + Proceso:concentración del núcleo + Producto:documentación | 6% | no |
| Persona/Proceso:renovación y experiencia + Producto:documentación | 4% | no |
| Persona/Proceso/Producto:renovación y experiencia | 3% | no |
| Persona/Proceso:concentración del núcleo + Persona/Proceso:revisores más activos + Persona:renovación y experiencia + Proceso:cierre de lo viejo + Producto:documentación | 3% | no |
| Persona/Proceso/Producto:renovación y experiencia + Proceso:revisores más activos + Producto:documentación | 3% | no |
| Persona/Proceso/Producto:renovación y experiencia + Persona/Proceso:concentración del núcleo + Persona/Proceso:revisores más activos + Proceso:cierre de lo viejo + Producto:documentación | 3% | no |
| Persona/Proceso:concentración del núcleo + Proceso/Producto:bugs de usuarios | 3% | no |
| Persona:participación + Proceso/Producto:bugs de usuarios + Proceso:README e issues abiertas | 2% | no |
| Persona/Proceso:concentración del núcleo + Persona/Proceso:revisores más activos + Persona/Producto:renovación y experiencia + Proceso:cierre de lo viejo + Producto:documentación | 2% | no |
| Persona/Proceso:renovación y experiencia + Proceso:revisores más activos + Producto:documentación | 2% | no |
| Persona/Proceso:concentración del núcleo + Persona/Proceso:renovación y experiencia + Producto:documentación | 2% | no |

Temas que forman parte de algún factor de tres dimensiones:

- renovación y experiencia: 78%
- documentación: 69%
- concentración del núcleo: 51%
- revisores más activos: 39%
- bugs de usuarios: 30%
- cierre de lo viejo: 18%
- participación: 17%
- README e issues abiertas: 12%
- tamaño de los cambios: 11%
- resolución de lo nuevo: 3%
- Wiki y branches: 0%
