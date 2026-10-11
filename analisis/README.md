# Análisis por dimensión

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

2. **Calcular las correlaciones** de todas las dimensiones (genera `analisis/salidas/pares_correlacion.csv`
   y `pares_valores.csv`):

   ```bash
   python3 analisis/generar_correlaciones.py
   ```

3. **Calcular el PCA de tu dimensión** (genera `analisis/salidas/pca/` y el reporte
   `analisis/salidas/reportes/reporte_pca_<dimension>.html`):

   ```bash
   python3 analisis/generar_pca.py Persona
   ```

   Por defecto retiene los componentes que indica el análisis paralelo de Horn; con `--k 4`
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

## Para ver los HTML

Los reportes se abren directo en el navegador, o con un servidor local:

```bash
python3 -m http.server 8765 --directory analisis/salidas/reportes
```

y entrando a `http://localhost:8765/informe_persona_persona.html`.

Los HTML y los CSV de resultados no se suben al repositorio: cada una los regenera con estos pasos.
