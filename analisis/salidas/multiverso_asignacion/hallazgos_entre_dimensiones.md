# Hallazgos entre dimensiones con cualquier asignación

Criterio: un patrón de variables es hallazgo entre dimensiones si relaciona dimensiones distintas con cualquier asignación de las métricas compartidas, es decir, si sus dos variables no comparten ninguna dimensión del catálogo. Los demás dependen de la asignación: la relación es la misma, pero según cómo se repartan las métricas compartidas puede contar como relación dentro de una dimensión. La asignación principal se mantiene para calcular los componentes y presentar los resultados.

## Hallazgo entre dimensiones (18)

| Par | ρ | Catálogo | Asignaciones en que es entre dimensiones | Con la principal | Cruces | Validación |
|---|---|---|---|---|---|---|
| cdiv_mediana ↔ commits_doc_producto | -0.42 | Persona+Proceso / Producto | 100% | entre dimensiones | Persona–Producto, Proceso–Producto | descartado: sin los commits que solo tocan documentación cae a −0,15 |
| prop_commitean_ratio ↔ le_producto | -0.29 | Persona / Producto | 100% | entre dimensiones | Persona–Producto | — |
| exprev_share_top10pct ↔ dloc_flujo_producto | +0.29 | Persona+Proceso / Producto | 100% | entre dimensiones | Persona–Producto, Proceso–Producto | — |
| cdiv_p90 ↔ cd_producto | +0.28 | Persona+Proceso / Producto | 100% | entre dimensiones | Persona–Producto, Proceso–Producto | — |
| tasa_nuevos_commits_ratio ↔ le_producto | -0.26 | Persona / Producto | 100% | entre dimensiones | Persona–Producto | — |
| tasa_nuevos_commits_ratio ↔ cfdr_producto | +0.24 | Persona / Proceso+Producto | 100% | entre dimensiones | Persona–Proceso, Persona–Producto | — |
| tasa_nuevos_commits_ratio ↔ nub_producto | +0.23 | Persona / Proceso+Producto | 100% | entre dimensiones | Persona–Proceso, Persona–Producto | — |
| prop_cierran_ratio ↔ process_performance_producto | +0.23 | Persona / Proceso | 100% | entre dimensiones | Persona–Proceso | — |
| prop_cierran_ratio ↔ jarczyk_success_rate_producto | +0.23 | Persona / Proceso | 100% | entre dimensiones | Persona–Proceso | — |
| nc_p90 ↔ le_producto | -0.22 | Persona+Proceso / Producto | 100% | entre dimensiones | Persona–Producto, Proceso–Producto | — |
| nci_producto ↔ dloc_flujo_producto | +0.22 | Proceso / Producto | 100% | entre dimensiones | Proceso–Producto | — |
| nc_share_top10pct ↔ dloc_flujo_producto | +0.21 | Persona+Proceso / Producto | 100% | entre dimensiones | Persona–Producto, Proceso–Producto | — |
| prop_commitean_ratio ↔ dloc_flujo_producto | +0.21 | Persona / Producto | 100% | entre dimensiones | Persona–Producto | — |
| exprev_share_top10pct ↔ le_producto | -0.20 | Persona+Proceso / Producto | 100% | entre dimensiones | Persona–Producto, Proceso–Producto | — |
| sc_p90 ↔ dloc_flujo_producto | +0.20 | Persona+Proceso / Producto | 100% | entre dimensiones | Persona–Producto, Proceso–Producto | — |
| nc_share_top10pct ↔ le_producto | -0.20 | Persona+Proceso / Producto | 100% | entre dimensiones | Persona–Producto | — |
| prop_cierran_ratio ↔ dloc_mediana | -0.20 | Persona / Producto | 100% | entre dimensiones | Persona–Producto | — |
| prop_comentan_ratio ↔ anmcc_producto | +0.17 | Persona / Proceso+Producto | 100% | entre dimensiones | Persona–Proceso, Persona–Producto | — |

## Depende de la asignación (44)

| Par | ρ | Catálogo | Asignaciones en que es entre dimensiones | Con la principal | Cruces | Validación |
|---|---|---|---|---|---|---|
| anmcc_mediana ↔ le_mediana | +0.48 | Proceso+Producto / Persona+Producto | 75% | entre dimensiones | Persona–Proceso, Persona–Producto | descartado: sin los recién llegados cae a +0,08 |
| anmcc_mediana ↔ dev_exp_mediana | +0.38 | Proceso+Producto / Persona+Proceso | 75% | entre dimensiones | Persona–Proceso, Persona–Producto, Proceso–Producto | descartado: sin los recién llegados cae a −0,01 |
| cfdr_producto ↔ rexprev_mediana | -0.31 | Proceso+Producto / Persona+Proceso | 75% | entre dimensiones | Persona–Proceso, Persona–Producto, Proceso–Producto | — |
| nub_producto ↔ rexprev_mediana | -0.31 | Proceso+Producto / Persona+Proceso | 75% | entre dimensiones | Persona–Proceso, Persona–Producto, Proceso–Producto | — |
| cfdr_producto ↔ exprev_p90 | -0.28 | Proceso+Producto / Persona+Proceso | 75% | entre dimensiones | Persona–Proceso, Persona–Producto, Proceso–Producto | — |
| exprev_p90 ↔ nub_producto | -0.27 | Persona+Proceso / Proceso+Producto | 75% | entre dimensiones | Persona–Proceso, Persona–Producto, Proceso–Producto | — |
| dev_exp_mediana ↔ mttr_mediana | -0.23 | Persona+Proceso / Proceso+Producto | 75% | entre dimensiones | Persona–Proceso, Persona–Producto | — |
| exprev_share_top10pct ↔ mttr_producto | +0.20 | Persona+Proceso / Proceso+Producto | 75% | entre dimensiones | Persona–Proceso, Persona–Producto | — |
| exprev_share_top10pct ↔ prop_commitean_ratio | +0.47 | Persona+Proceso / Persona | 50% | dentro de Persona | — | — |
| prop_commitean_ratio ↔ sc_p90 | +0.47 | Persona / Persona+Proceso | 50% | dentro de Persona | — | — |
| anmcc_mediana ↔ commits_doc_producto | -0.45 | Proceso+Producto / Producto | 50% | dentro de Producto | — | — |
| nc_share_top10pct ↔ prop_commitean_ratio | +0.43 | Persona+Proceso / Persona | 50% | dentro de Persona | — | — |
| prop_commitean_ratio ↔ sc_mediana | +0.35 | Persona / Persona+Proceso | 50% | dentro de Persona | — | — |
| jarczyk_success_rate_producto ↔ sc_mediana | +0.33 | Proceso / Persona+Proceso | 50% | entre dimensiones | Persona–Proceso | descartado: sin las issues propias cerradas en el mismo release cae |
| dis_producto ↔ mttr_mediana | +0.32 | Proceso / Proceso+Producto | 50% | dentro de Proceso | — | — |
| nc_share_top10pct ↔ sc_mediana | +0.31 | Persona+Proceso / Persona+Proceso | 50% | dentro de Persona | — | — |
| exprev_p90 ↔ prop_cierran_ratio | +0.31 | Persona+Proceso / Persona | 50% | dentro de Persona | — | — |
| prop_cierran_ratio ↔ rexprev_mediana | +0.30 | Persona / Persona+Proceso | 50% | dentro de Persona | — | — |
| nc_share_top10pct ↔ nci_p90 | +0.29 | Persona+Proceso / Proceso | 50% | entre dimensiones | Persona–Proceso | — |
| cdiv_p90 ↔ tasa_nuevos_commits_ratio | -0.29 | Persona+Proceso / Persona | 50% | dentro de Persona | — | — |
| nc_share_top10pct ↔ prop_cierran_ratio | +0.27 | Persona+Proceso / Persona | 50% | dentro de Persona | — | — |
| prop_commitean_ratio ↔ rexprev_mediana | +0.25 | Persona / Persona+Proceso | 50% | dentro de Persona | — | — |
| prop_cierran_ratio ↔ sc_p90 | +0.25 | Persona / Persona+Proceso | 50% | dentro de Persona | — | — |
| dis_producto ↔ rexprev_mediana | +0.24 | Proceso / Persona+Proceso | 50% | entre dimensiones | — | — |
| cdiv_p90 ↔ rexp_mediana | +0.24 | Persona+Proceso / Persona | 50% | dentro de Persona | — | — |
| exprev_p90 ↔ process_performance_producto | +0.22 | Persona+Proceso / Proceso | 50% | entre dimensiones | Persona–Proceso | — |
| exprev_p90 ↔ jarczyk_success_rate_producto | +0.18 | Persona+Proceso / Proceso | 50% | entre dimensiones | — | — |
| mttr_mediana ↔ process_performance_producto | -0.18 | Proceso+Producto / Proceso | 50% | dentro de Proceso | — | — |
| cdiv_mediana ↔ le_mediana (mismo tema) | +0.49 | Persona+Proceso / Persona+Producto | 75% | dentro de Persona | Proceso–Producto | — |
| cfdr_producto ↔ nub_producto (mismo tema) | +1.00 | Proceso+Producto / Proceso+Producto | 50% | dentro de Producto | — | — |
| le_mediana ↔ tasa_nuevos_commits_ratio (mismo tema) | -0.73 | Persona+Producto / Persona | 50% | dentro de Persona | — | — |
| dev_exp_mediana ↔ tasa_nuevos_commits_ratio (mismo tema) | -0.71 | Persona+Proceso / Persona | 50% | dentro de Persona | — | — |
| nc_share_top10pct ↔ sc_p90 (mismo tema) | +0.47 | Persona+Proceso / Persona+Proceso | 50% | dentro de Persona | — | — |
| cdiv_p90 ↔ sc_share_top10pct (mismo tema) | +0.46 | Persona+Proceso / Persona+Proceso | 50% | dentro de Persona | — | — |
| cdiv_mediana ↔ tasa_nuevos_commits_ratio (mismo tema) | -0.44 | Persona+Proceso / Persona | 50% | dentro de Persona | — | — |
| cdiv_mediana ↔ rexp_mediana (mismo tema) | +0.44 | Persona+Proceso / Persona | 50% | dentro de Persona | — | — |
| nc_share_top10pct ↔ sc_share_top10pct (mismo tema) | +0.42 | Persona+Proceso / Persona+Proceso | 50% | dentro de Persona | — | — |
| cdiv_mediana ↔ dev_exp_mediana (mismo tema) | +0.41 | Persona+Proceso / Persona+Proceso | 50% | dentro de Persona | — | — |
| le_mediana ↔ prop_commitean_ratio (mismo tema) | -0.33 | Persona+Producto / Persona | 50% | dentro de Persona | — | — |
| dev_exp_mediana ↔ prop_commitean_ratio (mismo tema) | -0.30 | Persona+Proceso / Persona | 50% | dentro de Persona | — | — |
| mttr_producto ↔ nci_producto (mismo tema) | +0.29 | Proceso+Producto / Proceso | 50% | dentro de Proceso | — | — |
| le_mediana ↔ rexp_mediana (mismo tema) | +0.29 | Persona+Producto / Persona | 50% | dentro de Persona | — | — |
| cdiv_p90 ↔ sc_p90 (mismo tema) | +0.19 | Persona+Proceso / Persona+Proceso | 50% | dentro de Persona | — | — |
| mttr_mediana ↔ nci_producto (mismo tema) | +0.18 | Proceso+Producto / Proceso | 50% | dentro de Proceso | — | — |
