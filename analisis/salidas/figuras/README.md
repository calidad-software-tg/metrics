# Figuras de los capítulos 4 y 5

Generadas con `python3 analisis/figuras_informe.py` (matplotlib, PNG a 300 dpi + SVG) solo desde `analisis/salidas/`. Qué difiere del texto y por qué: [diferencias.md](diferencias.md) (listado automático en [diferencias_automaticas.md](diferencias_automaticas.md)).

| Figura | Archivo | Sección | Fuente | Estado |
|---|---|---|---|---|
| 2 | `fig02_variables_por_dimension` | 4.1 | diccionario_variables.csv, relaciones/patrones.csv | hecha |
| 3 | `fig03_embudo` | 4.1 | relaciones/patrones.csv | hecha |
| 4 | `fig04_destino_resisten_tamano` | 4.2 | relaciones/patrones.csv, figuras/familias.csv | hecha |
| 5 | `fig05_red_persona` | 4.2.1 | relaciones/patrones.csv, figuras/familias.csv | hecha |
| 6 | `fig06_bosque_ABC` | 4.2.1 | relaciones/patrones.csv, relaciones/base/pares_correlacion.csv | hecha (sin las filas recalculadas sin recién llegados: falta la validación) |
| 7 | `fig07_estabilidad_ABC` | 4.2.1 | relaciones/patrones.csv, relaciones/base_epocas/pares_correlacion.csv | hecha |
| 8 | `fig08_experiencia_sin_recien_llegados` | 4.2.1 | validaciones/experiencia_ingreso_sin_recien_llegados (no existe) | falta dato: la validación de las medianas de experiencia sin recién llegados frente a la tasa de ingreso y la proporción que commitea no está en el código de analisis |
| 9 | `fig09_cargas_persona` | 4.2.1 | pca/pca_persona.json | hecha |
| 10 | `fig10_dendrograma_persona` | 4.2.1 | pca/clustering_persona.json, pca/pca_persona.json | hecha |
| 11 | `fig11_dos_actividades_proceso` | 4.2.2 | relaciones/patrones.csv | parcial: sin los valores de la validación nci_sin_issues_del_release (no está en el repo) |
| 12 | `fig12_bosque_proceso` | 4.2.2 | relaciones/patrones.csv, relaciones/base/pares_correlacion.csv | hecha |
| 13 | `fig13_nci_sin_issues_del_release` | 4.2.2 | validaciones/nci_sin_issues_del_release (no existe) | falta dato: no existe la validación nci_sin_issues_del_release en el código de analisis |
| 14 | `fig14_patrones_por_par` | 4.3.1 | relaciones/patrones.csv | hecha |
| 15 | `fig15_bosque_entre_dimensiones` | 4.3.1 | relaciones/patrones.csv, relaciones/base/pares_correlacion.csv | hecha (familias O y P: confirmar que son «las dos desarrolladas») |
| 15b | `fig15b_embudo_componentes_grupos` | 4.3.2 | bloques_etiquetas/pares.csv | hecha |
| 16 | `fig16_componentes_tres_dimensiones` | 4.3.2 | bloques_etiquetas/pares.csv | hecha |
| 17 | `fig17_multiverso_asignacion` | 4.3.3 | multiverso_asignacion/universos.csv | hecha |
| 18 | `fig18_tres_dimensiones_vs_azar` | 4.4.1 | tres_dimensiones/resumen.json | hecha |
| 19 | `fig19_cadena` | 4.4.2 | relaciones/triangulos.csv | hecha |
| 19b | `fig19b_cadena_mancuernas` | 4.4.2 | relaciones/triangulos.csv | hecha |
| 20 | `fig20_componentes_en_el_tiempo` | 4.5.1 | pca/pca_*.json | hecha (Proceso y Producto desde 2019: CFDR y NUB solo tienen datos desde v9.0.0) |
| 21 | `fig21_validacion` | 4.5.2 | validaciones/*/resumen.json, relaciones/patrones.csv | parcial: 0 de 18 relaciones tienen validación en el repo |
| 22 | `fig22_relaciones_nuevas_alternativos` | 4.5.3 | salidas de cruce_alternativos.py | sin generar |
| 23 | `fig23_random_forest` | 4.5.3 | salidas de cruce_alternativos.py | sin generar |
| 24 | `fig24_que_quedo` | 4.6 | relaciones/patrones.csv, figuras/familias.csv, validaciones/* | parcial: las descartadas son solo las 0 con validación en el repo |
| 25 | `fig25_aspectos_por_dimension` | 5.1 | relaciones/patrones.csv | hecha (aspectos = temas de multiverso_asignacion.tema, los de la columna tema_x/tema_y) |
| 26 | `fig26_mapa_conexiones` | 5.2 | relaciones/patrones.csv, multiverso_asignacion/universos.csv, bloques_etiquetas/pares.csv | hecha |
| 27 | `fig27_antes_despues_correcciones` | 5.4 | falta calcular (salidas_originales vs. salidas) | no se hace sin confirmación: falta calcular la comparación con el dataset original |
