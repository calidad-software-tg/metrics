# Tablas de los capítulos 4 y 5 (generadas desde analisis/salidas/)

## Tabla 7. Pares que quedaron en cada etapa, por dimensión

`tabla07_embudo_por_dimension.csv`

| dimension | pares_evaluados | significativas | robustas | resisten_tamano | mecanicas | descartadas_validacion | patrones |
|---|---|---|---|---|---|---|---|
| Persona | 339 | 112 | 72 | 32 | 6 | 0 | 26 |
| Proceso | 394 | 65 | 43 | 36 | 6 | 2 | 28 |
| Producto | 199 | 21 | 7 | 5 | 1 | 2 | 2 |

## Tabla 8. Familias de Persona

`tabla08_familias_persona.csv`

| familia | nombre | patrones | rho | entre | no_son_patron_en_los_datos |
|---|---|---|---|---|---|
| A | Participación en el código y concentración del núcleo | 5 | +0,25 a +0,47 | Persona–Proceso |  |
| B | Participación en el cierre de issues y revisores más activos | 4 | +0,25 a +0,31 | Persona–Proceso |  |
| C | Participación en el código y experiencia de quienes commitean | 2 | −0,33 y −0,30 | Persona–Proceso; Persona–Producto |  |
| D | Medidas de la concentración del núcleo entre sí | 5 | +0,19 a +0,47 | Persona–Proceso |  |
| E | Medidas de la experiencia entre sí | 1 | +0,44 | Persona–Proceso |  |
| F | Diversidad de los más activos y experiencia | 2 | −0,29 y +0,24 | Persona–Proceso |  |

## Tabla 9. Familias de Proceso

`tabla09_familias_proceso.csv`

| familia | nombre | patrones | rho | entre | no_son_patron_en_los_datos |
|---|---|---|---|---|---|
| G | Resolver lo nuevo y cerrar lo viejo | 4 | −0,18 a +0,29 | Proceso–Producto |  |
| H | Issues de documentación y ritmo general de las issues | 6 | −0,27 a +0,32 | Persona–Proceso; Proceso–Producto |  |
| I | Dos medidas de la resolución de lo nuevo | 1 | +0,83 |  |  |
| J | Experiencia y tiempo de resolución | 1 | −0,23 | Persona–Proceso; Persona–Producto; Proceso–Producto |  |
| K | Concentración del núcleo y cierre de lo viejo | 2 | +0,20 y +0,29 | Persona–Proceso; Persona–Proceso; Persona–Producto; Proceso–Producto |  |
| L | Revisores más activos y resolución de lo nuevo | 2 | +0,18 y +0,22 | Persona–Proceso |  |
| M | Revisores más activos y bugs de usuarios | 4 | −0,31 a −0,27 | Persona–Proceso; Persona–Producto; Proceso–Producto |  |
| D | Medidas de la concentración del núcleo entre sí | 5 | +0,19 a +0,47 | Persona–Proceso |  |

## Tabla 10. Familias de Producto

`tabla10_familias_producto.csv`

| familia | nombre | patrones | rho | entre | no_son_patron_en_los_datos |
|---|---|---|---|---|---|
| N | Flujo de documentación | 2 | −0,16 y +0,47 | Proceso–Producto |  |

## Tabla 11. Patrones por par de dimensiones

`tabla11_patrones_por_par.csv`

| par | patrones | solo_entre | tambien_dentro |
|---|---|---|---|
| Persona–Proceso | 37 | 5 | 32 |
| Persona–Producto | 22 | 12 | 10 |
| Proceso–Producto | 20 | 8 | 12 |

## Tabla 12. Familias entre dimensiones

`tabla12_familias_entre_dimensiones.csv`

| familia | nombre | patrones | rho | entre | no_son_patron_en_los_datos |
|---|---|---|---|---|---|
| O | Concentración del núcleo y documentación | 5 | +0,20 a +0,29 | Persona–Producto; Persona–Producto; Proceso–Producto |  |
| P | Participación en el cierre de issues y resolución de lo nuevo | 2 | +0,23 y +0,23 | Persona–Proceso |  |
| Q | Ingreso de nuevos contribuyentes y bugs reportados | 2 | +0,23 y +0,24 | Persona–Proceso; Persona–Producto |  |
| R | Learning Ease del proyecto, participación en el código y concentración del núcleo | 3 | −0,22 a −0,20 | Persona–Producto; Proceso–Producto | LE del proyecto ↔ Proporción que commitea (descartado al validar: construcción de LE (los recién llegados)) |
| S | Documentación y cierre de issues | 1 | +0,22 | Proceso–Producto |  |
| T | Documentación por colaborador y participación en el cierre de issues | 1 | −0,20 | Persona–Producto |  |
| U | Tamaño de los cambios y participación en la discusión | 1 | +0,17 | Persona–Proceso; Persona–Producto |  |

## Tabla 13. Correlación canónica entre pares de dimensiones

`tabla13_correlacion_canonica.csv`

| par | cca_principal | p | pct_asignaciones_sobre_azar | n_azar |
|---|---|---|---|---|
| Persona–Proceso | +0,45 | +0,01 | 99,80 | 500 |
| Persona–Producto | +0,61 | +0,01 | 98,80 | 500 |
| Proceso–Producto | +0,33 | +0,10 | 81,40 | 500 |

## Tabla 14. Relaciones validadas

`tabla14_validaciones.csv`

| x | y | relacion | explicacion | rho_original | rho_validado | fuente | estado_en_datos | texto_original | texto_validado | texto_resultado |
|---|---|---|---|---|---|---|---|---|---|---|
| le_mediana | anmcc_mediana | LE (mediana) ↔ ANMCC (mediana) | recién llegados | +0,48 | — |  | Descartada | +0,48 | +0,08 | Descartada |
| dev_exp_mediana | anmcc_mediana | Development Experience (mediana) ↔ ANMCC (mediana) | recién llegados | +0,38 | — |  | Descartada | +0,38 | −0,01 | Descartada |
| le_mediana | tasa_nuevos_commits_ratio | LE (mediana) ↔ Tasa de ingreso (commits) | recién llegados | −0,73 | — |  | Se mantiene (patrón) | −0,73 | +0,01 | Descartada |
| dev_exp_mediana | tasa_nuevos_commits_ratio | Development Experience (mediana) ↔ Tasa de ingreso (commits) | recién llegados | −0,71 | — |  | Se mantiene (patrón) | −0,71 | −0,02 | Descartada |
| cdiv_mediana | tasa_nuevos_commits_ratio | CDIV (mediana) ↔ Tasa de ingreso (commits) | recién llegados | −0,44 | — |  | Se mantiene (patrón) | −0,44 | +0,01 | Descartada |
| rexp_mediana | tasa_nuevos_commits_ratio | REXP (mediana) ↔ Tasa de ingreso (commits) | recién llegados | −0,29 | — |  | Se mantiene (patrón) | −0,29 | −0,02 | Descartada |
| cdiv_mediana | le_mediana | CDIV (mediana) ↔ LE (mediana) | recién llegados | +0,49 | — |  | Se mantiene (patrón) | +0,49 | +0,04 | Descartada |
| cdiv_mediana | dev_exp_mediana | CDIV (mediana) ↔ Development Experience (mediana) | recién llegados | +0,41 | — |  | Se mantiene (patrón) | +0,41 | +0,06 | Descartada |
| le_mediana | rexp_mediana | LE (mediana) ↔ REXP (mediana) | recién llegados | +0,29 | — |  | Se mantiene (patrón) | +0,29 | +0,07 | Descartada |
| le_mediana | prop_commitean_ratio | LE (mediana) ↔ Proporción que commitea | recién llegados | −0,33 | — |  | Se mantiene (patrón) | −0,33 | −0,38 | Se mantiene |
| dev_exp_mediana | prop_commitean_ratio | Development Experience (mediana) ↔ Proporción que commitea | recién llegados | −0,30 | — |  | Se mantiene (patrón) | −0,30 | −0,29 | Se mantiene |
| cdiv_mediana | commits_doc_producto | CDIV (mediana) ↔ Commits que tocan documentación | commits solo de documentación | −0,42 | — |  | Descartada | −0,42 | −0,15 | Descartada |
| anmcc_mediana | commits_doc_producto | ANMCC (mediana) ↔ Commits que tocan documentación | commits solo de documentación | −0,45 | — |  | Descartada | −0,45 | −0,07 | Descartada |
| sc_mediana | jarczyk_success_rate_producto | SC (mediana) ↔ Jarczyk Success Rate | issues del mismo release | +0,33 | — |  | Descartada | +0,33 | 0,00 | Descartada |
| nci_producto | jarczyk_success_rate_producto | NCI ↔ Jarczyk Success Rate | issues del mismo release | +0,39 | — |  | Se mantiene (patrón) | +0,39 | +0,15 | Descartada |
| nci_producto | process_performance_producto | NCI ↔ Process Performance | issues del mismo release | +0,28 | — |  | Se mantiene (patrón) | +0,28 | +0,08 | Descartada |
| tasa_nuevos_commits_ratio | le_producto | Tasa de ingreso (commits) ↔ LE del proyecto | recién llegados | −0,26 | — |  | Descartada | −0,26 | +0,08 | Descartada |
| prop_commitean_ratio | le_producto | Proporción que commitea ↔ LE del proyecto | recién llegados | −0,29 | — |  | Descartada | −0,29 | −0,20 | Se mantiene |

## Tabla (a numerar). Candidatos a triángulo de tres dimensiones

`tabla_triangulos.csv`

| nivel | elementos | asignacion | tipo | desaparece |
|---|---|---|---|---|
| variables | cdiv_mediana · le_mediana · rexp_mediana | cdiv_mediana→Proceso, le_mediana→Producto, rexp_mediana→Persona | dos aspectos | le_mediana ↔ rexp_mediana |
| variables | cdiv_mediana · le_mediana · tasa_nuevos_commits_ratio | cdiv_mediana→Proceso, le_mediana→Producto, tasa_nuevos_commits_ratio→Persona | dos aspectos | cdiv_mediana ↔ tasa_nuevos_commits_ratio |
| variables | dloc_flujo_producto · exprev_share_top10pct · prop_commitean_ratio | dloc_flujo_producto→Producto, exprev_share_top10pct→Proceso, prop_commitean_ratio→Persona | cadena | dloc_flujo_producto ↔ prop_commitean_ratio |
| variables | dloc_flujo_producto · nc_share_top10pct · prop_commitean_ratio | dloc_flujo_producto→Producto, nc_share_top10pct→Proceso, prop_commitean_ratio→Persona | cadena | dloc_flujo_producto ↔ nc_share_top10pct; dloc_flujo_producto ↔ prop_commitean_ratio |
| variables | dloc_flujo_producto · nc_share_top10pct · sc_p90 | dloc_flujo_producto→Producto, nc_share_top10pct→Persona, sc_p90→Proceso / dloc_flujo_producto→Producto, nc_share_top10pct→Proceso, sc_p90→Persona | dos aspectos | dloc_flujo_producto ↔ nc_share_top10pct; dloc_flujo_producto ↔ sc_p90 |
| variables | dloc_flujo_producto · prop_commitean_ratio · sc_p90 | dloc_flujo_producto→Producto, prop_commitean_ratio→Persona, sc_p90→Proceso | cadena | dloc_flujo_producto ↔ prop_commitean_ratio; dloc_flujo_producto ↔ sc_p90 |
| grupo | persona_g4 (concentración del núcleo) · proceso_g10 (cierre de lo viejo) · producto_g8 (Learning Ease) | persona_g4→Persona, proceso_g10→Proceso, producto_g8→Producto | cadena | persona_g4↔proceso_g10 |

## Anexo I. Patrones

`anexo_I_patrones.csv`

| relacion | x | y | rho | rho_canary | rho_tamano | nivel | tipo | entre | dentro | mismo_tema |
|---|---|---|---|---|---|---|---|---|---|---|
| Jarczyk Success Rate ↔ Process Performance | jarczyk_success_rate_producto | process_performance_producto | +0,83 | +0,52 | +0,83 | alta | dentro | — | Proceso | True |
| Commits que tocan documentación ↔ DLOC 2.0 | commits_doc_producto | dloc_flujo_producto | +0,47 | +0,84 | +0,43 | alta | dentro | — | Producto | True |
| Jarczyk Success Rate ↔ NCI | jarczyk_success_rate_producto | nci_producto | +0,39 | +0,44 | +0,40 | alta | dentro | — | Proceso | False |
| DIS ↔ NCI | dis_producto | nci_producto | +0,29 | +0,18 | +0,32 | media | dentro | — | Proceso | False |
| REXP (mediana) ↔ Tasa de ingreso (commits) | rexp_mediana | tasa_nuevos_commits_ratio | −0,29 | −0,27 | −0,27 | media | dentro | — | Persona | True |
| NCI ↔ Process Performance | nci_producto | process_performance_producto | +0,28 | +0,19 | +0,33 | media | dentro | — | Proceso | False |
| DIS (mediana) ↔ Jarczyk Success Rate | dis_mediana | jarczyk_success_rate_producto | −0,27 | −0,31 | −0,26 | media | dentro | — | Proceso | False |
| DIS ↔ NCI (p90) | dis_producto | nci_p90 | +0,27 | +0,18 | +0,27 | media | dentro | — | Proceso | False |
| DIS (mediana) ↔ NCI (p90) | dis_mediana | nci_p90 | +0,25 | +0,18 | +0,25 | media | dentro | — | Proceso | False |
| Jarczyk Success Rate ↔ NCI (p90) | jarczyk_success_rate_producto | nci_p90 | +0,19 | +0,25 | +0,20 | baja | dentro | — | Proceso | False |
| DLOC 2.0 ↔ EXPRev (10 % más activo) | dloc_flujo_producto | exprev_share_top10pct | +0,29 | +0,18 | +0,34 | media | entre dimensiones | Persona–Producto; Proceso–Producto | — | False |
| CD ↔ CDIV (p90) | cd_producto | cdiv_p90 | +0,28 | +0,02 | +0,29 | baja | entre dimensiones | Persona–Producto; Proceso–Producto | — | False |
| CFDR ↔ Tasa de ingreso (commits) | cfdr_producto | tasa_nuevos_commits_ratio | +0,24 | +0,07 | +0,11 | baja | entre dimensiones | Persona–Proceso; Persona–Producto | — | False |
| NUB ↔ Tasa de ingreso (commits) | nub_producto | tasa_nuevos_commits_ratio | +0,23 | +0,07 | +0,11 | baja | entre dimensiones | Persona–Proceso; Persona–Producto | — | False |
| Process Performance ↔ Proporción que cierra issues | process_performance_producto | prop_cierran_ratio | +0,23 | +0,15 | +0,23 | media | entre dimensiones | Persona–Proceso | — | False |
| Jarczyk Success Rate ↔ Proporción que cierra issues | jarczyk_success_rate_producto | prop_cierran_ratio | +0,23 | +0,26 | +0,25 | media | entre dimensiones | Persona–Proceso | — | False |
| LE del proyecto ↔ NC (p90) | le_producto | nc_p90 | −0,22 | −0,03 | −0,26 | baja | entre dimensiones | Persona–Producto; Proceso–Producto | — | False |
| DLOC 2.0 ↔ NCI | dloc_flujo_producto | nci_producto | +0,22 | +0,23 | +0,11 | media | entre dimensiones | Proceso–Producto | — | False |
| DLOC 2.0 ↔ NC (10 % más activo) | dloc_flujo_producto | nc_share_top10pct | +0,21 | +0,12 | +0,27 | media | entre dimensiones | Persona–Producto; Proceso–Producto | — | False |
| DLOC 2.0 ↔ Proporción que commitea | dloc_flujo_producto | prop_commitean_ratio | +0,21 | +0,32 | +0,29 | media | entre dimensiones | Persona–Producto | — | False |
| EXPRev (10 % más activo) ↔ LE del proyecto | exprev_share_top10pct | le_producto | −0,20 | −0,05 | −0,24 | media | entre dimensiones | Persona–Producto; Proceso–Producto | — | False |
| DLOC 2.0 ↔ SC (p90) | dloc_flujo_producto | sc_p90 | +0,20 | +0,17 | +0,24 | media | entre dimensiones | Persona–Producto; Proceso–Producto | — | False |
| LE del proyecto ↔ NC (10 % más activo) | le_producto | nc_share_top10pct | −0,20 | −0,04 | −0,24 | media | entre dimensiones | Persona–Producto; Proceso–Producto | — | False |
| DLOC (mediana) ↔ Proporción que cierra issues | dloc_mediana | prop_cierran_ratio | −0,20 | −0,01 | −0,21 | media | entre dimensiones | Persona–Producto | — | False |
| ANMCC ↔ Proporción que comenta | anmcc_producto | prop_comentan_ratio | +0,17 | +0,02 | +0,20 | baja | entre dimensiones | Persona–Proceso; Persona–Producto | — | False |
| LE (mediana) ↔ Tasa de ingreso (commits) | le_mediana | tasa_nuevos_commits_ratio | −0,73 | −0,45 | −0,72 | alta | entre y dentro | Persona–Producto | Persona | False |
| Development Experience (mediana) ↔ Tasa de ingreso (commits) | dev_exp_mediana | tasa_nuevos_commits_ratio | −0,71 | −0,45 | −0,71 | alta | entre y dentro | Persona–Proceso | Persona | True |
| CDIV (mediana) ↔ LE (mediana) | cdiv_mediana | le_mediana | +0,49 | +0,22 | +0,46 | media | entre y dentro | Persona–Proceso; Persona–Producto; Proceso–Producto | Persona | False |
| EXPRev (10 % más activo) ↔ Proporción que commitea | exprev_share_top10pct | prop_commitean_ratio | +0,47 | +0,34 | +0,45 | alta | entre y dentro | Persona–Proceso | Persona | False |
| Proporción que commitea ↔ SC (p90) | prop_commitean_ratio | sc_p90 | +0,47 | +0,17 | +0,45 | alta | entre y dentro | Persona–Proceso | Persona | False |
| NC (10 % más activo) ↔ SC (p90) | nc_share_top10pct | sc_p90 | +0,47 | +0,15 | +0,45 | alta | entre y dentro | Persona–Proceso | Persona; Proceso | True |
| CDIV (p90) ↔ SC (10 % más activo) | cdiv_p90 | sc_share_top10pct | +0,46 | +0,04 | +0,47 | media | entre y dentro | Persona–Proceso | Persona; Proceso | True |
| CDIV (mediana) ↔ Tasa de ingreso (commits) | cdiv_mediana | tasa_nuevos_commits_ratio | −0,44 | −0,33 | −0,40 | media | entre y dentro | Persona–Proceso | Persona | True |
| CDIV (mediana) ↔ REXP (mediana) | cdiv_mediana | rexp_mediana | +0,44 | +0,38 | +0,42 | media | entre y dentro | Persona–Proceso | Persona | True |
| NC (10 % más activo) ↔ Proporción que commitea | nc_share_top10pct | prop_commitean_ratio | +0,43 | +0,29 | +0,40 | alta | entre y dentro | Persona–Proceso | Persona | False |
| NC (10 % más activo) ↔ SC (10 % más activo) | nc_share_top10pct | sc_share_top10pct | +0,42 | +0,10 | +0,46 | alta | entre y dentro | Persona–Proceso | Persona; Proceso | True |
| CDIV (mediana) ↔ Development Experience (mediana) | cdiv_mediana | dev_exp_mediana | +0,41 | +0,23 | +0,39 | media | entre y dentro | Persona–Proceso | Persona; Proceso | True |
| Proporción que commitea ↔ SC (mediana) | prop_commitean_ratio | sc_mediana | +0,35 | +0,32 | +0,32 | media | entre y dentro | Persona–Proceso | Persona | False |
| LE (mediana) ↔ Proporción que commitea | le_mediana | prop_commitean_ratio | −0,33 | −0,23 | −0,40 | media | entre y dentro | Persona–Producto | Persona | False |
| DIS ↔ MTTR (mediana) | dis_producto | mttr_mediana | +0,32 | +0,41 | +0,32 | media | entre y dentro | Proceso–Producto | Proceso | False |
| CFDR ↔ REXPRev (mediana) | cfdr_producto | rexprev_mediana | −0,31 | −0,07 | −0,16 | media | entre y dentro | Persona–Proceso; Persona–Producto; Proceso–Producto | Proceso | False |
| NUB ↔ REXPRev (mediana) | nub_producto | rexprev_mediana | −0,31 | −0,07 | −0,16 | media | entre y dentro | Persona–Proceso; Persona–Producto; Proceso–Producto | Proceso | False |
| NC (10 % más activo) ↔ SC (mediana) | nc_share_top10pct | sc_mediana | +0,31 | +0,13 | +0,29 | media | entre y dentro | Persona–Proceso | Persona; Proceso | False |
| EXPRev (p90) ↔ Proporción que cierra issues | exprev_p90 | prop_cierran_ratio | +0,31 | +0,15 | +0,28 | media | entre y dentro | Persona–Proceso | Persona | False |
| Proporción que cierra issues ↔ REXPRev (mediana) | prop_cierran_ratio | rexprev_mediana | +0,30 | +0,15 | +0,26 | media | entre y dentro | Persona–Proceso | Persona | False |
| Development Experience (mediana) ↔ Proporción que commitea | dev_exp_mediana | prop_commitean_ratio | −0,30 | −0,20 | −0,34 | media | entre y dentro | Persona–Proceso | Persona | True |
| NC (10 % más activo) ↔ NCI (p90) | nc_share_top10pct | nci_p90 | +0,29 | +0,17 | +0,28 | media | entre y dentro | Persona–Proceso | Proceso | False |
| MTTR ↔ NCI | mttr_producto | nci_producto | +0,29 | +0,35 | +0,35 | media | entre y dentro | Proceso–Producto | Proceso | True |
| CDIV (p90) ↔ Tasa de ingreso (commits) | cdiv_p90 | tasa_nuevos_commits_ratio | −0,29 | 0,00 | −0,28 | media | entre y dentro | Persona–Proceso | Persona | False |
| LE (mediana) ↔ REXP (mediana) | le_mediana | rexp_mediana | +0,29 | +0,14 | +0,27 | media | entre y dentro | Persona–Producto | Persona | False |
| CFDR ↔ EXPRev (p90) | cfdr_producto | exprev_p90 | −0,28 | −0,02 | −0,12 | media | entre y dentro | Persona–Proceso; Persona–Producto; Proceso–Producto | Proceso | False |
| NC (10 % más activo) ↔ Proporción que cierra issues | nc_share_top10pct | prop_cierran_ratio | +0,27 | +0,05 | +0,25 | media | entre y dentro | Persona–Proceso | Persona | False |
| EXPRev (p90) ↔ NUB | exprev_p90 | nub_producto | −0,27 | −0,03 | −0,12 | baja | entre y dentro | Persona–Proceso; Persona–Producto; Proceso–Producto | Proceso | False |
| Proporción que commitea ↔ REXPRev (mediana) | prop_commitean_ratio | rexprev_mediana | +0,25 | +0,22 | +0,19 | media | entre y dentro | Persona–Proceso | Persona | False |
| Proporción que cierra issues ↔ SC (p90) | prop_cierran_ratio | sc_p90 | +0,25 | +0,01 | +0,23 | media | entre y dentro | Persona–Proceso | Persona | False |
| DIS ↔ REXPRev (mediana) | dis_producto | rexprev_mediana | +0,24 | +0,03 | +0,25 | baja | entre y dentro | Persona–Proceso | Proceso | False |
| CDIV (p90) ↔ REXP (mediana) | cdiv_p90 | rexp_mediana | +0,24 | +0,14 | +0,23 | baja | entre y dentro | Persona–Proceso | Persona | False |
| Development Experience (mediana) ↔ MTTR (mediana) | dev_exp_mediana | mttr_mediana | −0,23 | −0,02 | −0,23 | media | entre y dentro | Persona–Proceso; Persona–Producto; Proceso–Producto | Proceso | False |
| EXPRev (p90) ↔ Process Performance | exprev_p90 | process_performance_producto | +0,22 | +0,03 | +0,22 | media | entre y dentro | Persona–Proceso | Proceso | False |
| EXPRev (10 % más activo) ↔ MTTR | exprev_share_top10pct | mttr_producto | +0,20 | +0,17 | +0,20 | media | entre y dentro | Persona–Proceso; Persona–Producto; Proceso–Producto | Proceso | False |
| CDIV (p90) ↔ SC (p90) | cdiv_p90 | sc_p90 | +0,19 | +0,19 | +0,18 | media | entre y dentro | Persona–Proceso | Persona; Proceso | True |
| MTTR (mediana) ↔ NCI | mttr_mediana | nci_producto | +0,18 | +0,21 | +0,23 | media | entre y dentro | Proceso–Producto | Proceso | True |
| EXPRev (p90) ↔ Jarczyk Success Rate | exprev_p90 | jarczyk_success_rate_producto | +0,18 | +0,10 | +0,20 | media | entre y dentro | Persona–Proceso | Proceso | False |
| MTTR (mediana) ↔ Process Performance | mttr_mediana | process_performance_producto | −0,18 | −0,13 | −0,18 | baja | entre y dentro | Proceso–Producto | Proceso | False |
| ANMCC ↔ Commits que tocan documentación | anmcc_producto | commits_doc_producto | −0,16 | −0,09 | −0,15 | baja | entre y dentro | Proceso–Producto | Producto | False |

## Anexo J. Relaciones robustas que no son patrón

`anexo_J_robustas_no_patron.csv`

(94 filas: ver el CSV)

## Diferencias con el texto

- **Tabla 7** · Persona descartadas_validacion: datos=0 · texto=7
- **Tabla 7** · Persona patrones: datos=26 · texto=19
- **Tabla 7** · Proceso descartadas_validacion: datos=2 · texto=5
- **Tabla 7** · Proceso patrones: datos=28 · texto=25
- **Tabla 11** · Persona–Proceso patrones: datos=37 · texto=27
- **Tabla 11** · Persona–Proceso también dentro: datos=32 · texto=22
- **Tabla 11** · Persona–Producto patrones: datos=22 · texto=20
- **Tabla 11** · Persona–Producto solo entre: datos=12 · texto=13
- **Tabla 11** · Persona–Producto también dentro: datos=10 · texto=7
- **Tabla 11** · Proceso–Producto patrones: datos=20 · texto=17
- **Tabla 11** · Proceso–Producto también dentro: datos=12 · texto=9
- **Tabla 12** · familia R patrones: datos=3 · texto=4
- **Tabla 12** · familia R ρ: datos=−0,22 a −0,20 · texto=−0,29 a −0,20
- **Tabla 14** · LE (mediana) ↔ ANMCC (mediana): sin validación en el repo (texto +0,08; en los datos: Descartada)
- **Tabla 14** · Development Experience (mediana) ↔ ANMCC (mediana): sin validación en el repo (texto −0,01; en los datos: Descartada)
- **Tabla 14** · LE (mediana) ↔ Tasa de ingreso (commits): sin validación en el repo (texto +0,01; en los datos: Se mantiene (patrón))
- **Tabla 14** · Development Experience (mediana) ↔ Tasa de ingreso (commits): sin validación en el repo (texto −0,02; en los datos: Se mantiene (patrón))
- **Tabla 14** · CDIV (mediana) ↔ Tasa de ingreso (commits): sin validación en el repo (texto +0,01; en los datos: Se mantiene (patrón))
- **Tabla 14** · REXP (mediana) ↔ Tasa de ingreso (commits): sin validación en el repo (texto −0,02; en los datos: Se mantiene (patrón))
- **Tabla 14** · CDIV (mediana) ↔ LE (mediana): sin validación en el repo (texto +0,04; en los datos: Se mantiene (patrón))
- **Tabla 14** · CDIV (mediana) ↔ Development Experience (mediana): sin validación en el repo (texto +0,06; en los datos: Se mantiene (patrón))
- **Tabla 14** · LE (mediana) ↔ REXP (mediana): sin validación en el repo (texto +0,07; en los datos: Se mantiene (patrón))
- **Tabla 14** · LE (mediana) ↔ Proporción que commitea: sin validación en el repo (texto −0,38; en los datos: Se mantiene (patrón))
- **Tabla 14** · Development Experience (mediana) ↔ Proporción que commitea: sin validación en el repo (texto −0,29; en los datos: Se mantiene (patrón))
- **Tabla 14** · CDIV (mediana) ↔ Commits que tocan documentación: sin validación en el repo (texto −0,15; en los datos: Descartada)
- **Tabla 14** · ANMCC (mediana) ↔ Commits que tocan documentación: sin validación en el repo (texto −0,07; en los datos: Descartada)
- **Tabla 14** · SC (mediana) ↔ Jarczyk Success Rate: sin validación en el repo (texto 0,00; en los datos: Descartada)
- **Tabla 14** · NCI ↔ Jarczyk Success Rate: sin validación en el repo (texto +0,15; en los datos: Se mantiene (patrón))
- **Tabla 14** · NCI ↔ Process Performance: sin validación en el repo (texto +0,08; en los datos: Se mantiene (patrón))
- **Tabla 14** · Tasa de ingreso (commits) ↔ LE del proyecto: sin validación en el repo (texto +0,08; en los datos: Descartada)
- **Tabla 14** · Proporción que commitea ↔ LE del proyecto: sin validación en el repo (texto −0,20; en los datos: Descartada)
