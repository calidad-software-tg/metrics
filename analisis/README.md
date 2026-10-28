# Análisis por dimensión

> En la branch `ine/fixes-metricas` las métricas se recalculan con correcciones y en otra base
> (`resultados_metricas_fixes`). Ver [FIXES_METRICAS.md](../FIXES_METRICAS.md) para qué cambió y en qué
> orden correr todo; para apuntar cualquier paso de abajo a esa base, anteponer
> `POSTGRES_DB=resultados_metricas_fixes` al comando.

Cómo generar el análisis de correlaciones y de componentes principales (PCA) de una
dimensión (Persona, Proceso o Producto). Todo se corre desde la raíz del repositorio.

## Antes de empezar

- La base de datos levantada y cargada (contenedor `tg_metricas_db`), con las
  credenciales en el `.env` de la raíz (`POSTGRES_*`).
- Python 3 con `numpy`, `scipy`, `pandas` y `psycopg2`.

## Pasos

1. **Exportar las métricas por persona** (genera `persona_agregado_estable_canary.csv`):

   ```bash
   python3 export_persona.py
   ```

   Usa credenciales fijas en el script (`DB = ...`); si tu base usa otras, cambialas ahí.
   Si falla en las validaciones del final, los CSV ya quedaron generados.

2. **Calcular las correlaciones** dentro de cada dimensión (genera `analisis/salidas/pares_correlacion.csv`
   y `pares_valores.csv`):

   ```bash
   python3 analisis/correlaciones.py
   ```

   Con `--periodos ambos` repite la regla de estabilidad con las épocas y compara (ver más abajo).

3. **Calcular el PCA y el clustering de tu dimensión** (generan `analisis/salidas/pca/` y el reporte
   `analisis/salidas/reportes/reporte_pca_<dimension>.html`):

   ```bash
   python3 analisis/pca.py Persona
   python3 analisis/clustering.py Persona
   ```

   Por defecto el PCA retiene los componentes que indica el análisis paralelo de Horn; con `--k 4`
   se fija otra cantidad.

4. **Escribir tu informe.** Copiá `analisis/informes/producto_producto.md` como
   `analisis/informes/persona_persona.md` (o `proceso_proceso.md`), cambiá en el encabezado
   `cruce: Persona-Persona` y el título, y reemplazá el texto por tu análisis. Las líneas
   `[[...]]` son marcas que se reemplazan por gráficos y tablas; la lista completa está al
   principio de `analisis/generar_informe.py`.

5. **Generar el informe** (también regenera el reporte interactivo de correlaciones del cruce):

   ```bash
   python3 analisis/generar_informe.py analisis/informes/persona_persona.md
   ```

   Queda en `analisis/salidas/reportes/informe_persona_persona.html`.

## Cómo está organizado el código

| Script | Qué hace |
|---|---|
| `preprocesamiento.py` | Lo común a todos los análisis (no se corre solo): lee el diccionario, la base y el CSV de Persona, calcula las proporciones, saca los backports, arma la tabla de releases y la transforma (rangos, sin tendencia ni duración) y define los períodos (calendario o épocas). |
| `correlaciones.py` | Pares dentro de cada dimensión. Sus funciones para evaluar y clasificar un par las usa también `cruces.py`. |
| `pca.py` | PCA de una dimensión. |
| `clustering.py` | Clustering de métricas de una dimensión (después de `pca.py`). |
| `cruces.py` | Análisis entre dos dimensiones: reparte las métricas compartidas y cruza variables, componentes (de `pca.py`) y grupos (`--grupos`, de `clustering.py`); conjunto reducido, correlación canónica, triangulación y PCA conjunto. |
| `temporal.py` | Clustering de releases (`releases`) y épocas con todas las métricas (`epocas`). Contexto y prueba de sensibilidad, no técnica principal. |

Orden: `correlaciones.py` y `pca.py` → `clustering.py` → `cruces.py` (y `--grupos`). `temporal.py` es independiente.

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
