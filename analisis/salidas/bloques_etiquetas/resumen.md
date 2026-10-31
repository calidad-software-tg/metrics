# Componentes y grupos entre dimensiones, con las lecturas del catálogo

Cada dimensión con todas sus variables (compartidas incluidas). Si dos elementos comparten métricas, se cruza la parte propia de cada uno; si a alguno no le queda nada, el cruce no se evalúa.

## Elementos

| Elemento | Tipo | Tema | Variables |
|---|---|---|---|
| persona_cp1 | componente | renovación y experiencia | nuevos_commits_conteo, le_mediana, tasa_nuevos_commits_ratio, dev_exp_mediana, activos_commits_conteo, cdiv_mediana, prop_commitean_ratio, rexp_mediana |
| persona_cp2 | componente | volumen de actividad | activos_comentarios_conteo, activos_interaccion_conteo, nuevos_interaccion_conteo, activos_cierre_conteo, disc_centrality_mediana, prop_comentan_ratio, activos_commits_conteo |
| persona_cp3 | componente | concentración del núcleo | exprev_share_top10pct, nc_share_top10pct, sc_share_top10pct, sc_p90, cdiv_p90, prop_commitean_ratio |
| persona_g6 | grupo | volumen de actividad | activos_cierre_conteo, activos_comentarios_conteo, activos_interaccion_conteo, disc_centrality_mediana, nuevos_interaccion_conteo |
| persona_g2 | grupo | renovación y experiencia | activos_commits_conteo, cdiv_mediana, dev_exp_mediana, le_mediana, nuevos_commits_conteo, rexp_mediana, tasa_nuevos_commits_ratio |
| persona_g1 | grupo | concentración del núcleo | cdiv_p90, sc_share_top10pct |
| persona_g5 | grupo | revisores más activos | exprev_p90, nc_p90, prop_cierran_ratio, rexprev_mediana |
| persona_g4 | grupo | concentración del núcleo | exprev_share_top10pct, nc_share_top10pct, prop_commitean_ratio, sc_mediana, sc_p90 |
| proceso_cp3 | componente | renovación y experiencia | cdiv_mediana, anmcc_mediana, dev_exp_mediana, cdiv_share_top10pct, cdiv_p90 |
| proceso_cp4 | componente | resolución de lo nuevo | jarczyk_success_rate_producto, process_performance_producto |
| proceso_cp6 | componente | cierre de lo viejo | mttr_producto, mttr_mediana, nci_producto, nci_share_top10pct, nci_p90 |
| proceso_cp7 | componente | concentración del núcleo | anmcc_producto, cdiv_share_top10pct, cdiv_p90 |
| proceso_g4 | grupo | tamaño de los cambios | anmcc_producto, anmcc_mediana, cdiv_mediana, cdiv_p90, cdiv_share_top10pct, dev_exp_mediana |
| proceso_g6 | grupo | bugs de usuarios | cfdr_producto, nub_producto |
| proceso_g8 | grupo | resolución de lo nuevo | jarczyk_success_rate_producto, process_performance_producto, sc_mediana |
| proceso_g9 | grupo | cierre de lo viejo | mttr_producto, mttr_mediana |
| proceso_g10 | grupo | cierre de lo viejo | nci_producto, nci_p90, nci_share_top10pct |
| proceso_g1 | grupo | README e issues abiertas | noi_producto, rc_producto, rc_mediana |
| proceso_g7 | grupo | revisores más activos | exprev_p90, nc_p90, rexprev_mediana |
| proceso_g5 | grupo | concentración del núcleo | exprev_share_top10pct, nc_share_top10pct, sc_p90, sc_share_top10pct |
| producto_cp2 | componente | bugs de usuarios | cfdr_producto, nub_producto |
| producto_cp4 | componente | Learning Ease | le_mediana, le_producto, anmcc_mediana |
| producto_cp6 | componente | cierre de lo viejo | mttr_producto, mttr_mediana, dloc_producto |
| producto_g9 | grupo | tamaño de los cambios | anmcc_producto, commits_doc_producto, dloc_flujo_producto, anmcc_mediana |
| producto_g5 | grupo | documentación | cd_producto, wp_producto, dloc_p90 |
| producto_g7 | grupo | bugs de usuarios | cfdr_producto, nub_producto, cd_mediana |
| producto_g8 | grupo | Learning Ease | le_producto, le_mediana |
| producto_g1 | grupo | cierre de lo viejo | mttr_producto, mttr_mediana |
| producto_g4 | grupo | README e issues abiertas | noi_producto, rc_producto, rc_mediana |
| producto_g3 | grupo | documentación | dloc_mediana, dloc_share_top10pct |

## Cruce de componentes

33 pares entre dimensiones; 0 no se evalúan (mismo contenido); 8 se evaluaron sin las métricas compartidas. 4 patrones entre aspectos distintos.

| Par | Temas | ρ | Canary | Con tamaño | Puede conectar | También dentro de | Sin |
|---|---|---|---|---|---|---|---|
| persona_cp3 ↔ producto_cp2 | concentración del núcleo ↔ bugs de usuarios | -0,37 | -0,07 | -0,20 | Persona–Proceso; Persona–Producto | — | — |
| persona_cp1 ↔ proceso_cp6 | renovación y experiencia ↔ cierre de lo viejo | +0,27 | +0,11 | +0,26 | Persona–Proceso | — | — |
| proceso_cp4 ↔ producto_cp6 | resolución de lo nuevo ↔ cierre de lo viejo | -0,25 | -0,13 | -0,24 | Proceso–Producto | — | — |
| proceso_cp6 ↔ producto_cp4 | cierre de lo viejo ↔ Learning Ease | -0,22 | -0,07 | -0,20 | Proceso–Producto | — | — |

## Cruce de grupos

131 pares entre dimensiones; 6 no se evalúan (mismo contenido); 8 se evaluaron sin las métricas compartidas. 15 patrones entre aspectos distintos.

| Par | Temas | ρ | Canary | Con tamaño | Puede conectar | También dentro de | Sin |
|---|---|---|---|---|---|---|---|
| persona_g2 ↔ proceso_g4 | renovación y experiencia ↔ tamaño de los cambios | -0,40 | -0,26 | -0,37 | Persona–Proceso; Persona–Producto | — | cdiv, dev_exp |
| persona_g4 ↔ producto_g7 | concentración del núcleo ↔ bugs de usuarios | -0,40 | -0,11 | -0,22 | Persona–Producto | — | — |
| proceso_g5 ↔ producto_g7 | concentración del núcleo ↔ bugs de usuarios | -0,38 | -0,07 | -0,28 | Persona–Producto; Proceso–Producto | — | — |
| persona_g4 ↔ proceso_g6 | concentración del núcleo ↔ bugs de usuarios | -0,36 | -0,07 | -0,13 | Persona–Proceso; Persona–Producto | — | — |
| persona_g2 ↔ proceso_g10 | renovación y experiencia ↔ cierre de lo viejo | +0,32 | +0,14 | +0,27 | Persona–Proceso | — | — |
| proceso_g7 ↔ producto_g8 | revisores más activos ↔ Learning Ease | -0,31 | -0,06 | -0,35 | Persona–Producto; Proceso–Producto | — | — |
| persona_g5 ↔ producto_g8 | revisores más activos ↔ Learning Ease | -0,30 | -0,07 | -0,33 | Persona–Producto | — | — |
| persona_g4 ↔ producto_g8 | concentración del núcleo ↔ Learning Ease | -0,29 | -0,15 | -0,33 | Persona–Producto | — | — |
| proceso_g4 ↔ producto_g7 | tamaño de los cambios ↔ bugs de usuarios | -0,28 | -0,02 | -0,14 | Proceso–Producto | — | — |
| persona_g5 ↔ proceso_g8 | revisores más activos ↔ resolución de lo nuevo | +0,28 | +0,18 | +0,29 | Persona–Proceso | — | — |
| persona_g4 ↔ proceso_g7 | concentración del núcleo ↔ revisores más activos | +0,26 | +0,10 | +0,17 | Persona–Proceso | Persona | exprev, nc |
| proceso_g10 ↔ producto_g8 | cierre de lo viejo ↔ Learning Ease | -0,25 | -0,05 | -0,25 | Proceso–Producto | — | — |
| proceso_g10 ↔ producto_g9 | cierre de lo viejo ↔ tamaño de los cambios | +0,25 | +0,10 | +0,20 | Proceso–Producto | — | — |
| persona_g2 ↔ proceso_g8 | renovación y experiencia ↔ resolución de lo nuevo | +0,22 | +0,12 | +0,23 | Persona–Proceso | — | — |
| persona_g4 ↔ proceso_g10 | concentración del núcleo ↔ cierre de lo viejo | +0,21 | +0,18 | +0,34 | Persona–Proceso | — | — |

## Triángulos de tres dimensiones entre componentes

Ninguno: no hay tres componentes de dimensiones distintas, sin métricas en común y de tres aspectos distintos, relacionados de a pares.

## Triángulos de tres dimensiones entre grupos

- **cadena**: persona_g4 (concentración del núcleo) · proceso_g10 (cierre de lo viejo) · producto_g8 (Learning Ease) · persona_g4↔proceso_g10 +0.21 → +0.15; persona_g4↔producto_g8 -0.29 → -0.25; proceso_g10↔producto_g8 -0.25 → -0.20 · se debilita: persona_g4↔proceso_g10
