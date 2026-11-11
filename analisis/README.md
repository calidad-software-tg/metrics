# Análisis por dimensión

> En la branch `ine/fixes-metricas` las métricas se recalculan con correcciones y en otra base
> (`resultados_metricas_fixes`). Ver [FIXES_METRICAS.md](../FIXES_METRICAS.md) para qué cambió y en qué
> orden correr todo; para apuntar cualquier paso de abajo a esa base, anteponer
> `POSTGRES_DB=resultados_metricas_fixes` al comando.

Cómo generar el análisis de correlaciones y de componentes principales (PCA) de una
dimensión (Persona, Proceso o Producto). Todo se corre desde la raíz del repositorio.

## Cómo se corre

Todo el análisis se corre con `python3 tres_p.py analizar` desde la raíz (ver el README principal),
que ejecuta los scripts en este orden:

1. `generar_diccionario.py`: el diccionario de variables (métrica, nivel, estadístico, dimensiones del catálogo).
2. `correlaciones.py`: pares dentro de cada dimensión.
3. `pca.py` y `clustering.py` de cada dimensión.
4. `cruces.py` para cada par de dimensiones, con la configuración de `analisis/cruces/`.
5. `tres_dimensiones.py`, `multiverso_asignacion.py`, `relaciones.py --recalcular` y `bloques_etiquetas.py`.
6. Los reportes HTML (`reporte_pca.py`, `reporte_cruce.py`).

Los datos salen de la base del proyecto (`POSTGRES_*` en `.env`) y de `persona_agregado_estable_canary.csv`
(`tres_p.py exportar`). El repositorio, los tags excluidos, el calendario, las épocas y las relaciones
descartadas al validar se leen de `proyecto.json` (`proyecto.py`).

## Cómo está organizado el código

| Script | Qué hace |
|---|---|
| `preprocesamiento.py` | Lo común a todos los análisis (no se corre solo): lee el diccionario, la base y el CSV de Persona, calcula las proporciones, saca los backports, arma la tabla de releases y la transforma (rangos, sin tendencia ni duración) y define los períodos (calendario o épocas). |
| `correlaciones.py` | Pares dentro de cada dimensión. Sus funciones para evaluar y clasificar un par las usa también `cruces.py`. |
| `pca.py` | PCA de una dimensión. |
| `clustering.py` | Clustering de métricas de una dimensión (después de `pca.py`). |
| `cruces.py` | Análisis entre dos dimensiones: reparte las métricas compartidas y cruza variables, componentes (de `pca.py`) y grupos (`--grupos`, de `clustering.py`); conjunto reducido, correlación canónica, triangulación y PCA conjunto. |
| `temporal.py` | Clustering de releases (`releases`) y épocas con todas las métricas (`epocas`). Contexto y prueba de sensibilidad, no técnica principal. |
| `tres_dimensiones.py` | Análisis de las tres dimensiones a la vez sobre los componentes de cada PCA: medida global (correlación canónica generalizada, RV y MFA), red de correlaciones parciales y triángulos, triangulación con variables, PCA y clustering conjunto, perfiles de releases y rezago. Salidas en `analisis/salidas/tres_dimensiones/`. |

| `pesos_catalogo.py` | Pertenencia ponderada según el catálogo (una métrica de dos dimensiones cuenta mitad para cada una): qué patrones de los cruces dependen de la asignación de las métricas compartidas, PCA y clustering conjunto de las tres dimensiones sin asignar y composición del factor común de `tres_dimensiones.py`. Salidas en `analisis/salidas/pesos_catalogo/`. |

| `multiverso_asignacion.py` | Sensibilidad a la asignación de las 16 métricas compartidas (multiverso): para todos los pares patrón (dentro y entre dimensiones), en qué parte de las asignaciones posibles relacionan dimensiones distintas, y la lista de hallazgos entre dimensiones con el criterio de cualquier asignación (`hallazgos_entre_dimensiones.md`; `--solo-variables` corre solo esta parte); y, en la asignación principal, cambiando cada métrica de lado, en la opuesta y en 500 al azar, los cruces de componentes, conjunto reducido, correlación canónica, grupos, PCA y clustering conjunto, triangulación y el análisis de tres dimensiones (versión liviana, sin bootstrap ni canary). Salidas en `analisis/salidas/multiverso_asignacion/`. |

| `relaciones.py` | **Criterio final para las relaciones entre variables.** Todos los pares de variables una sola vez, con una única corrección de Benjamini–Hochberg y los mismos filtros; cada patrón se etiqueta con todas las lecturas que permite el catálogo (los pares de dimensiones que puede conectar y si también es una relación dentro de una dimensión), sin asignar las métricas compartidas. Busca además triángulos de tres dimensiones entre variables (tres aspectos distintos, con la prueba de descontar el tercer vértice). Reemplaza al criterio del 100 % de `multiverso_asignacion.py`, que queda para las medidas globales. Salidas en `analisis/salidas/relaciones/`. |
| `bloques_etiquetas.py` | El mismo criterio para componentes y grupos: cada dimensión con todas sus variables (conjunto `todas`), puntajes con las variables que definen cada elemento, y cruces entre dimensiones sin las métricas compartidas (si a un elemento no le queda nada, no se evalúa). Etiqueta cada patrón con sus lecturas y busca triángulos de tres dimensiones entre componentes y entre grupos. Salidas en `analisis/salidas/bloques_etiquetas/`. |

Orden: `correlaciones.py` y `pca.py` → `clustering.py` → `cruces.py` (y `--grupos`) → `tres_dimensiones.py` → `pesos_catalogo.py`, `multiverso_asignacion.py` y `relaciones.py`. `temporal.py` es independiente.

**Períodos.** La regla de estabilidad usa los cuatro períodos de calendario. Con `--periodos epocas`
(`correlaciones.py` y `cruces.py`) usa las épocas de `preprocesamiento.CORTES_EPOCAS`, asignadas por número
de release; con `--periodos ambos` corre las dos y marca cada patrón como firme (pasa con los dos cortes) o
dependiente del corte.

Los nombres anteriores (`generar_correlaciones.py`, `generar_pca.py`, `generar_clustering.py`,
`cruce_dimensiones.py`, `cruce_clustering.py`) siguen funcionando: importarlos devuelve el módulo nuevo y
correrlos corre el script nuevo.

## Para ver los HTML

Los reportes se abren directo en el navegador, o con un servidor local:

```bash
python3 -m http.server 8765 --directory analisis/salidas/reportes
```

y entrando a `http://localhost:8765/informe_persona_persona.html`.

Los HTML y los CSV de resultados no se suben al repositorio: cada una los regenera con estos pasos.
