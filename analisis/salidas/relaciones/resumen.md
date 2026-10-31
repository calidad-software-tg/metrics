# Relaciones entre métricas con las lecturas del catálogo

1431 pares de variables (sin las variantes), evaluados una sola vez y corregidos con Benjamini–Hochberg en una sola familia. 66 son patrón (robustos, resisten el tamaño, no son mecánicos ni de escala, no se descartaron al validar).

| Tipo | Patrones | Qué significa |
|---|---|---|
| entre dimensiones | 15 | sus variables no comparten ninguna dimensión del catálogo |
| entre y dentro | 41 | pueden conectar dimensiones distintas o leerse dentro de una dimensión que comparten |
| dentro | 10 | las dos variables son de la misma dimensión y de ninguna otra |

Descartados al validar (no cuentan): 6.

## Persona–Proceso

37 patrones pueden conectar estas dos dimensiones; 5 solo pueden leerse como entre dimensiones.

| Patrón | ρ | Nivel | Catálogo | Otras lecturas | Canary | Con tamaño |
|---|---|---|---|---|---|---|
| cfdr_producto ↔ tasa_nuevos_commits_ratio | +0,24 | baja | Proceso+Producto / Persona | Persona–Producto | +0,07 | +0,11 |
| nub_producto ↔ tasa_nuevos_commits_ratio | +0,23 | baja | Proceso+Producto / Persona | Persona–Producto | +0,07 | +0,11 |
| process_performance_producto ↔ prop_cierran_ratio | +0,23 | media | Proceso / Persona | — | +0,15 | +0,23 |
| jarczyk_success_rate_producto ↔ prop_cierran_ratio | +0,23 | media | Proceso / Persona | — | +0,26 | +0,25 |
| anmcc_producto ↔ prop_comentan_ratio | +0,17 | baja | Proceso+Producto / Persona | Persona–Producto | +0,02 | +0,20 |
| cdiv_mediana ↔ le_mediana | +0,49 | media | Persona+Proceso / Persona+Producto | Persona–Producto, Proceso–Producto, dentro de Persona | +0,22 | +0,46 |
| exprev_share_top10pct ↔ prop_commitean_ratio | +0,47 | alta | Persona+Proceso / Persona | dentro de Persona | +0,34 | +0,45 |
| prop_commitean_ratio ↔ sc_p90 | +0,47 | alta | Persona / Persona+Proceso | dentro de Persona | +0,17 | +0,45 |
| nc_share_top10pct ↔ prop_commitean_ratio | +0,43 | alta | Persona+Proceso / Persona | dentro de Persona | +0,29 | +0,40 |
| prop_commitean_ratio ↔ sc_mediana | +0,35 | media | Persona / Persona+Proceso | dentro de Persona | +0,32 | +0,32 |
| cfdr_producto ↔ rexprev_mediana | -0,31 | media | Proceso+Producto / Persona+Proceso | Persona–Producto, Proceso–Producto, dentro de Proceso | -0,07 | -0,16 |
| nub_producto ↔ rexprev_mediana | -0,31 | media | Proceso+Producto / Persona+Proceso | Persona–Producto, Proceso–Producto, dentro de Proceso | -0,07 | -0,16 |
| nc_share_top10pct ↔ sc_mediana | +0,31 | media | Persona+Proceso / Persona+Proceso | dentro de Persona, dentro de Proceso | +0,13 | +0,29 |
| exprev_p90 ↔ prop_cierran_ratio | +0,31 | media | Persona+Proceso / Persona | dentro de Persona | +0,15 | +0,28 |
| prop_cierran_ratio ↔ rexprev_mediana | +0,30 | media | Persona / Persona+Proceso | dentro de Persona | +0,15 | +0,26 |
| nc_share_top10pct ↔ nci_p90 | +0,29 | media | Persona+Proceso / Proceso | dentro de Proceso | +0,17 | +0,28 |
| cdiv_p90 ↔ tasa_nuevos_commits_ratio | -0,29 | media | Persona+Proceso / Persona | dentro de Persona | -0,00 | -0,28 |
| cfdr_producto ↔ exprev_p90 | -0,28 | media | Proceso+Producto / Persona+Proceso | Persona–Producto, Proceso–Producto, dentro de Proceso | -0,02 | -0,12 |
| nc_share_top10pct ↔ prop_cierran_ratio | +0,27 | media | Persona+Proceso / Persona | dentro de Persona | +0,05 | +0,25 |
| exprev_p90 ↔ nub_producto | -0,27 | baja | Persona+Proceso / Proceso+Producto | Persona–Producto, Proceso–Producto, dentro de Proceso | -0,03 | -0,12 |
| prop_commitean_ratio ↔ rexprev_mediana | +0,25 | media | Persona / Persona+Proceso | dentro de Persona | +0,22 | +0,19 |
| prop_cierran_ratio ↔ sc_p90 | +0,25 | media | Persona / Persona+Proceso | dentro de Persona | +0,01 | +0,23 |
| dis_producto ↔ rexprev_mediana | +0,24 | baja | Proceso / Persona+Proceso | dentro de Proceso | +0,03 | +0,25 |
| cdiv_p90 ↔ rexp_mediana | +0,24 | baja | Persona+Proceso / Persona | dentro de Persona | +0,14 | +0,23 |
| dev_exp_mediana ↔ mttr_mediana | -0,23 | media | Persona+Proceso / Proceso+Producto | Persona–Producto, Proceso–Producto, dentro de Proceso | -0,02 | -0,23 |
| exprev_p90 ↔ process_performance_producto | +0,22 | media | Persona+Proceso / Proceso | dentro de Proceso | +0,03 | +0,22 |
| exprev_share_top10pct ↔ mttr_producto | +0,20 | media | Persona+Proceso / Proceso+Producto | Persona–Producto, Proceso–Producto, dentro de Proceso | +0,17 | +0,20 |
| exprev_p90 ↔ jarczyk_success_rate_producto | +0,18 | media | Persona+Proceso / Proceso | dentro de Proceso | +0,10 | +0,20 |
| dev_exp_mediana ↔ tasa_nuevos_commits_ratio (mismo tema) | -0,71 | alta | Persona+Proceso / Persona | dentro de Persona | -0,45 | -0,71 |
| nc_share_top10pct ↔ sc_p90 (mismo tema) | +0,47 | alta | Persona+Proceso / Persona+Proceso | dentro de Persona, dentro de Proceso | +0,15 | +0,45 |
| cdiv_p90 ↔ sc_share_top10pct (mismo tema) | +0,46 | media | Persona+Proceso / Persona+Proceso | dentro de Persona, dentro de Proceso | +0,04 | +0,47 |
| cdiv_mediana ↔ tasa_nuevos_commits_ratio (mismo tema) | -0,44 | media | Persona+Proceso / Persona | dentro de Persona | -0,33 | -0,40 |
| cdiv_mediana ↔ rexp_mediana (mismo tema) | +0,44 | media | Persona+Proceso / Persona | dentro de Persona | +0,38 | +0,42 |
| nc_share_top10pct ↔ sc_share_top10pct (mismo tema) | +0,42 | alta | Persona+Proceso / Persona+Proceso | dentro de Persona, dentro de Proceso | +0,10 | +0,46 |
| cdiv_mediana ↔ dev_exp_mediana (mismo tema) | +0,41 | media | Persona+Proceso / Persona+Proceso | dentro de Persona, dentro de Proceso | +0,23 | +0,39 |
| dev_exp_mediana ↔ prop_commitean_ratio (mismo tema) | -0,30 | media | Persona+Proceso / Persona | dentro de Persona | -0,20 | -0,34 |
| cdiv_p90 ↔ sc_p90 (mismo tema) | +0,19 | media | Persona+Proceso / Persona+Proceso | dentro de Persona, dentro de Proceso | +0,19 | +0,18 |

## Persona–Producto

22 patrones pueden conectar estas dos dimensiones; 12 solo pueden leerse como entre dimensiones.

| Patrón | ρ | Nivel | Catálogo | Otras lecturas | Canary | Con tamaño |
|---|---|---|---|---|---|---|
| dloc_flujo_producto ↔ exprev_share_top10pct | +0,29 | media | Producto / Persona+Proceso | Proceso–Producto | +0,18 | +0,34 |
| cd_producto ↔ cdiv_p90 | +0,28 | baja | Producto / Persona+Proceso | Proceso–Producto | +0,02 | +0,29 |
| cfdr_producto ↔ tasa_nuevos_commits_ratio | +0,24 | baja | Proceso+Producto / Persona | Persona–Proceso | +0,07 | +0,11 |
| nub_producto ↔ tasa_nuevos_commits_ratio | +0,23 | baja | Proceso+Producto / Persona | Persona–Proceso | +0,07 | +0,11 |
| le_producto ↔ nc_p90 | -0,22 | baja | Producto / Persona+Proceso | Proceso–Producto | -0,03 | -0,26 |
| dloc_flujo_producto ↔ nc_share_top10pct | +0,21 | media | Producto / Persona+Proceso | Proceso–Producto | +0,12 | +0,27 |
| dloc_flujo_producto ↔ prop_commitean_ratio | +0,21 | media | Producto / Persona | — | +0,32 | +0,29 |
| exprev_share_top10pct ↔ le_producto | -0,20 | media | Persona+Proceso / Producto | Proceso–Producto | -0,05 | -0,24 |
| dloc_flujo_producto ↔ sc_p90 | +0,20 | media | Producto / Persona+Proceso | Proceso–Producto | +0,17 | +0,24 |
| le_producto ↔ nc_share_top10pct | -0,20 | media | Producto / Persona+Proceso | Proceso–Producto | -0,04 | -0,24 |
| dloc_mediana ↔ prop_cierran_ratio | -0,20 | media | Producto / Persona | — | -0,01 | -0,21 |
| anmcc_producto ↔ prop_comentan_ratio | +0,17 | baja | Proceso+Producto / Persona | Persona–Proceso | +0,02 | +0,20 |
| le_mediana ↔ tasa_nuevos_commits_ratio | -0,73 | alta | Persona+Producto / Persona | dentro de Persona | -0,45 | -0,72 |
| cdiv_mediana ↔ le_mediana | +0,49 | media | Persona+Proceso / Persona+Producto | Persona–Proceso, Proceso–Producto, dentro de Persona | +0,22 | +0,46 |
| le_mediana ↔ prop_commitean_ratio | -0,33 | media | Persona+Producto / Persona | dentro de Persona | -0,23 | -0,40 |
| cfdr_producto ↔ rexprev_mediana | -0,31 | media | Proceso+Producto / Persona+Proceso | Persona–Proceso, Proceso–Producto, dentro de Proceso | -0,07 | -0,16 |
| nub_producto ↔ rexprev_mediana | -0,31 | media | Proceso+Producto / Persona+Proceso | Persona–Proceso, Proceso–Producto, dentro de Proceso | -0,07 | -0,16 |
| le_mediana ↔ rexp_mediana | +0,29 | media | Persona+Producto / Persona | dentro de Persona | +0,14 | +0,27 |
| cfdr_producto ↔ exprev_p90 | -0,28 | media | Proceso+Producto / Persona+Proceso | Persona–Proceso, Proceso–Producto, dentro de Proceso | -0,02 | -0,12 |
| exprev_p90 ↔ nub_producto | -0,27 | baja | Persona+Proceso / Proceso+Producto | Persona–Proceso, Proceso–Producto, dentro de Proceso | -0,03 | -0,12 |
| dev_exp_mediana ↔ mttr_mediana | -0,23 | media | Persona+Proceso / Proceso+Producto | Persona–Proceso, Proceso–Producto, dentro de Proceso | -0,02 | -0,23 |
| exprev_share_top10pct ↔ mttr_producto | +0,20 | media | Persona+Proceso / Proceso+Producto | Persona–Proceso, Proceso–Producto, dentro de Proceso | +0,17 | +0,20 |

## Proceso–Producto

21 patrones pueden conectar estas dos dimensiones; 8 solo pueden leerse como entre dimensiones.

| Patrón | ρ | Nivel | Catálogo | Otras lecturas | Canary | Con tamaño |
|---|---|---|---|---|---|---|
| dloc_flujo_producto ↔ exprev_share_top10pct | +0,29 | media | Producto / Persona+Proceso | Persona–Producto | +0,18 | +0,34 |
| cd_producto ↔ cdiv_p90 | +0,28 | baja | Producto / Persona+Proceso | Persona–Producto | +0,02 | +0,29 |
| le_producto ↔ nc_p90 | -0,22 | baja | Producto / Persona+Proceso | Persona–Producto | -0,03 | -0,26 |
| dloc_flujo_producto ↔ nci_producto | +0,22 | media | Producto / Proceso | — | +0,23 | +0,11 |
| dloc_flujo_producto ↔ nc_share_top10pct | +0,21 | media | Producto / Persona+Proceso | Persona–Producto | +0,12 | +0,27 |
| exprev_share_top10pct ↔ le_producto | -0,20 | media | Persona+Proceso / Producto | Persona–Producto | -0,05 | -0,24 |
| dloc_flujo_producto ↔ sc_p90 | +0,20 | media | Producto / Persona+Proceso | Persona–Producto | +0,17 | +0,24 |
| le_producto ↔ nc_share_top10pct | -0,20 | media | Producto / Persona+Proceso | Persona–Producto | -0,04 | -0,24 |
| cdiv_mediana ↔ le_mediana | +0,49 | media | Persona+Proceso / Persona+Producto | Persona–Proceso, Persona–Producto, dentro de Persona | +0,22 | +0,46 |
| anmcc_mediana ↔ commits_doc_producto | -0,45 | media | Proceso+Producto / Producto | dentro de Producto | -0,25 | -0,41 |
| dis_producto ↔ mttr_mediana | +0,32 | media | Proceso / Proceso+Producto | dentro de Proceso | +0,41 | +0,32 |
| cfdr_producto ↔ rexprev_mediana | -0,31 | media | Proceso+Producto / Persona+Proceso | Persona–Proceso, Persona–Producto, dentro de Proceso | -0,07 | -0,16 |
| nub_producto ↔ rexprev_mediana | -0,31 | media | Proceso+Producto / Persona+Proceso | Persona–Proceso, Persona–Producto, dentro de Proceso | -0,07 | -0,16 |
| cfdr_producto ↔ exprev_p90 | -0,28 | media | Proceso+Producto / Persona+Proceso | Persona–Proceso, Persona–Producto, dentro de Proceso | -0,02 | -0,12 |
| exprev_p90 ↔ nub_producto | -0,27 | baja | Persona+Proceso / Proceso+Producto | Persona–Proceso, Persona–Producto, dentro de Proceso | -0,03 | -0,12 |
| dev_exp_mediana ↔ mttr_mediana | -0,23 | media | Persona+Proceso / Proceso+Producto | Persona–Proceso, Persona–Producto, dentro de Proceso | -0,02 | -0,23 |
| exprev_share_top10pct ↔ mttr_producto | +0,20 | media | Persona+Proceso / Proceso+Producto | Persona–Proceso, Persona–Producto, dentro de Proceso | +0,17 | +0,20 |
| mttr_mediana ↔ process_performance_producto | -0,18 | baja | Proceso+Producto / Proceso | dentro de Proceso | -0,13 | -0,18 |
| anmcc_producto ↔ commits_doc_producto | -0,16 | baja | Proceso+Producto / Producto | dentro de Producto | -0,09 | -0,15 |
| mttr_producto ↔ nci_producto (mismo tema) | +0,29 | media | Proceso+Producto / Proceso | dentro de Proceso | +0,35 | +0,35 |
| mttr_mediana ↔ nci_producto (mismo tema) | +0,18 | media | Proceso+Producto / Proceso | dentro de Proceso | +0,21 | +0,23 |

## Tres dimensiones entre variables

Triángulos de tres variables relacionadas de a pares a las que el catálogo permite asignar tres dimensiones distintas. Tridimensional: los tres lados se mantienen como patrón al descontar el tercer vértice. Cadena: el lado que se debilita conecta dos dimensiones solo a través de la tercera. Los triángulos con dos medidas del mismo aspecto (por ejemplo, dos medidas de la concentración del núcleo) o de un solo aspecto no conectan aspectos distintos y no cuentan.

### Tridimensional (0)

| Variables | Temas | Lados: ρ → sin el tercero | Asignaciones que lo hacen de tres dimensiones |
|---|---|---|---|

### Cadena (3)

| Variables | Temas | Lados: ρ → sin el tercero | Asignaciones que lo hacen de tres dimensiones |
|---|---|---|---|
| dloc_flujo_producto · exprev_share_top10pct · prop_commitean_ratio | concentración del núcleo + documentación + renovación y experiencia | dloc_flujo_producto ↔ exprev_share_top10pct +0,29 → +0,22; dloc_flujo_producto ↔ prop_commitean_ratio +0,21 → +0,08; exprev_share_top10pct ↔ prop_commitean_ratio +0,47 → +0,44 | dloc_flujo_producto→Producto, exprev_share_top10pct→Proceso, prop_commitean_ratio→Persona |
| dloc_flujo_producto · nc_share_top10pct · prop_commitean_ratio | concentración del núcleo + documentación + renovación y experiencia | dloc_flujo_producto ↔ nc_share_top10pct +0,21 → +0,13; dloc_flujo_producto ↔ prop_commitean_ratio +0,21 → +0,13; nc_share_top10pct ↔ prop_commitean_ratio +0,43 → +0,40 | dloc_flujo_producto→Producto, nc_share_top10pct→Proceso, prop_commitean_ratio→Persona |
| dloc_flujo_producto · prop_commitean_ratio · sc_p90 | concentración del núcleo + documentación + renovación y experiencia | dloc_flujo_producto ↔ prop_commitean_ratio +0,21 → +0,13; dloc_flujo_producto ↔ sc_p90 +0,20 → +0,12; prop_commitean_ratio ↔ sc_p90 +0,47 → +0,45 | dloc_flujo_producto→Producto, prop_commitean_ratio→Persona, sc_p90→Proceso |

### Dos aspectos (3)

| Variables | Temas | Lados: ρ → sin el tercero | Asignaciones que lo hacen de tres dimensiones |
|---|---|---|---|
| cdiv_mediana · le_mediana · tasa_nuevos_commits_ratio | Learning Ease + renovación y experiencia | cdiv_mediana ↔ le_mediana +0,49 → +0,27; cdiv_mediana ↔ tasa_nuevos_commits_ratio -0,44 → -0,14; le_mediana ↔ tasa_nuevos_commits_ratio -0,73 → -0,66 | cdiv_mediana→Proceso, le_mediana→Producto, tasa_nuevos_commits_ratio→Persona |
| cdiv_mediana · le_mediana · rexp_mediana | Learning Ease + renovación y experiencia | cdiv_mediana ↔ le_mediana +0,49 → +0,42; cdiv_mediana ↔ rexp_mediana +0,44 → +0,35; le_mediana ↔ rexp_mediana +0,29 → +0,10 | cdiv_mediana→Proceso, le_mediana→Producto, rexp_mediana→Persona |
| dloc_flujo_producto · nc_share_top10pct · sc_p90 | concentración del núcleo + documentación | dloc_flujo_producto ↔ nc_share_top10pct +0,21 → +0,13; dloc_flujo_producto ↔ sc_p90 +0,20 → +0,12; nc_share_top10pct ↔ sc_p90 +0,47 → +0,44 | dloc_flujo_producto→Producto, nc_share_top10pct→Persona, sc_p90→Proceso | dloc_flujo_producto→Producto, nc_share_top10pct→Proceso, sc_p90→Persona |

### Un solo aspecto (0)

| Variables | Temas | Lados: ρ → sin el tercero | Asignaciones que lo hacen de tres dimensiones |
|---|---|---|---|

