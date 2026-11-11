# Análisis

Busca patrones entre las métricas de Persona, Proceso y Producto: dentro de cada dimensión, entre pares
de dimensiones y entre las tres. **Qué técnicas usa y por qué: [metodologia.md](metodologia.md).**

## Cómo se corre

Desde la raíz del repositorio, `python3 tres_p.py analizar` (o `--sin-reportes`). Corre en este orden:

| Paso | Script | Deja en `salidas/` |
|---|---|---|
| 1 | `generar_diccionario.py` | `1_variables/` |
| 2 | `correlaciones.py` | `2_dimensiones/correlaciones/` |
| 3 | `pca.py <Dim>` y `clustering.py <Dim>`, para cada dimensión | `2_dimensiones/<dim>/` |
| 4 | `cruces.py <DimA> <DimB>` para cada par (configuración en `cruces/`), y otra vez con `--grupos propio` para el cruce entre grupos | `3_cruces/<dima>_<dimb>/` y `.../clustering_propio/` |
| 5 | `tres_dimensiones.py` | `4_tres_dimensiones/` |
| 6 | `multiverso_asignacion.py` | `6_robustez/multiverso_asignacion/` |
| 7 | `relaciones.py --recalcular` (**clasificación final**) | `5_patrones/` |
| 8 | `bloques_etiquetas.py` | `6_robustez/metricas_compartidas/` |
| 8b | complementarios (salvo `--sin-complementarios`): `correlaciones.py --periodos ambos`, `cruces.py --periodos epocas` y `cruce_alternativos.py` por par, `complementarios/temporal.py releases` y `epocas`, `cruce_rezago.py` y `pesos_catalogo.py` | `complementarios/` |
| 9 | `reporte_pca.py`, `reporte_cruce.py`, `reporte_cruce_dimensiones.py`, `reporte_tres_dimensiones.py`, `reporte_resultados.py` y `reporte_complementarios.py`; después `reportes.py` los reúne | `reportes/intradimensional.html`, `bidimensional.html` y `tridimensional.html` |
| 10 | `indice.py` | `LEEME.md` |

Los pasos 5, 6 y 8 necesitan componentes en las tres dimensiones. Si una dimensión no tiene (pocas
releases para sus variables), se saltean con un aviso.

Los datos salen de la base del proyecto (`POSTGRES_*` en `.env`) y de
`datos/persona_agregado_estable_canary.csv` (`tres_p.py exportar`). El repositorio, los tags excluidos,
los períodos, las épocas y las relaciones descartadas al validar se leen de `proyecto.json`.

## Archivos

| Archivo | Qué hace |
|---|---|
| `rutas.py` | Dónde lee y escribe cada paso (la estructura de `salidas/`). |
| `preprocesamiento.py` | Lo común a todos (no se corre solo): lee el diccionario, la base y el CSV de Persona, calcula las proporciones, saca los backports, arma la tabla de releases, la transforma (rangos, sin tendencia ni duración) y define los períodos. |
| `generar_diccionario.py` | El diccionario de variables: métrica, nivel, estadístico, dimensiones del catálogo y cobertura. |
| `correlaciones.py` | Evalúa y clasifica pares de variables (correlación parcial, BH, estabilidad, réplica, tamaño). Lo usan también `cruces.py` y `relaciones.py`. |
| `pca.py` | PCA de una dimensión: Horn, varimax, bootstrap de bloques, congruencia con canary. |
| `clustering.py` | Agrupamiento jerárquico de las métricas de una dimensión (después de `pca.py`). |
| `cruces.py` | Un par de dimensiones: variables, componentes, grupos (`--grupos`), conjunto reducido, correlación canónica, triangulación y PCA conjunto. |
| `tres_dimensiones.py` | Las tres dimensiones a la vez: correlación canónica generalizada, RV y MFA contra una nula temporal, triángulos de componentes, perfiles y rezago. |
| `multiverso_asignacion.py` | Las medidas globales con todas las asignaciones de las métricas compartidas. |
| `relaciones.py` | Todos los pares de variables una sola vez, con una corrección BH, etiquetados con todas las lecturas del catálogo, sin los descartados al validar. Busca las cadenas entre las tres dimensiones. |
| `bloques_etiquetas.py` | El mismo criterio para componentes y grupos, sin las métricas que comparten dos dimensiones. |
| `reporte_*.py` | Cada reporte HTML: de una dimensión (correlaciones o PCA con agrupamiento), de un cruce o de las tres dimensiones. |
| `reporte_resultados.py` | Las vistas sin generador propio: patrones finales, cruce entre grupos, cruces sin métricas compartidas, multiverso y PCA y agrupamiento conjunto. |
| `reporte_complementarios.py` | La vista «Complementarios» de cada reporte. |
| `reportes.py` | Reúne todo en tres páginas, una por nivel de análisis, con una pestaña por dimensión o por par y una vista por técnica. |
| `indice.py` | `salidas/LEEME.md`, el índice de las salidas. |
| `cruces/` | Configuración de cada cruce (qué métricas compartidas van a cada lado en los cruces de componentes). |
| `complementarios/` | Análisis complementarios (no son técnica principal): técnicas alternativas (`cruce_alternativos.py`), rezago (`cruce_rezago.py`), pesos del catálogo (`pesos_catalogo.py`) y análisis temporal y épocas (`temporal.py`). Escriben en `salidas/complementarios/`; `tres_p.py analizar` los corre salvo con `--sin-complementarios`. |

**Períodos.** La regla de estabilidad usa los cuatro períodos de calendario. Con `--periodos epocas`
(`correlaciones.py` y `cruces.py`) usa las épocas, y con `--periodos ambos` corre las dos y marca cada
patrón como firme o dependiente del corte.

## Ver los reportes

Hay tres, uno por nivel de análisis, y se abren directo en el navegador:

| Reporte | Pestañas | Vistas de cada pestaña |
|---|---|---|
| `intradimensional.html` | Persona, Proceso, Producto | patrones finales · correlaciones · PCA y agrupamiento · complementarios |
| `bidimensional.html` | cada par de dimensiones | patrones finales · variables y componentes (conjunto reducido, correlación canónica, triangulación, PCA conjunto) · grupos · sin métricas compartidas · multiverso · complementarios |
| `tridimensional.html` | — | medida global, red, triángulos y tríos de variables · PCA y agrupamiento conjunto · multiverso y métricas compartidas · complementarios |

Los «patrones finales» son el criterio de `relaciones.py` y coinciden con `5_patrones/resumen.md`; la vista «variables y
componentes» usa el criterio de `cruces.py`, que asigna cada métrica compartida a un solo lado. La vista «complementarios»
reúne los análisis de `complementarios/` y la sensibilidad a los períodos (`reporte_complementarios.py`).

Arriba de cada uno hay enlaces a los otros dos.
