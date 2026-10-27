# Handoff · Tesis 3P (Persona / Proceso / Producto) · métricas de next.js

Documento para retomar el trabajo con otra persona o con otra IA. Resume qué se hizo, en qué estado
quedó cada cosa, cómo se corre y qué falta. El detalle de cada corrección de métricas está en
[FIXES_METRICAS.md](FIXES_METRICAS.md) y cómo correr el análisis, en [analisis/README.md](analisis/README.md).

Última actualización: 13 de octubre de 2026.

---

## 1. Contexto

- **Tesis:** patrones de calidad en tres dimensiones, Persona, Proceso y Producto (3P), medidas sobre el
  historial del repositorio **vercel/next.js**.
- **Equipo:** Ine (dueña de la dimensión **Producto**; dueña de este repo local), Luz y Clara (las otras
  dimensiones).
- **Unidad de análisis:** la *ventana de release* `[release_i, release_{i+1})`. Cada métrica se calcula
  una vez por ventana, en dos series: **estables** y **canary**.
- **Pregunta del análisis:** qué métricas se mueven juntas de release en release (correlaciones) y qué
  grupos de métricas forman dimensiones latentes (PCA).

## 2. Entorno

| Cosa | Dónde / cómo |
|---|---|
| Repo | `/Users/inegassiebayle/projects/tesis/metrics` |
| Base de datos | Postgres en Docker, contenedor `tg_metricas_db`, usuario `metricas`, puerto 5433. Credenciales en el `.env` de la raíz y en `db/.env` (**no copiarlas en ningún lado**) |
| Base original | `resultados_metricas` (métricas sin corregir) |
| Base corregida | `resultados_metricas_fixes` (todas las métricas recalculadas con los fixes). Para que un script la use: anteponer `POSTGRES_DB=resultados_metricas_fixes` |
| Token de GitHub | `GITHUB_TOKEN` en el `.env`. **Nunca imprimirlo**: leerlo dentro de Python. Se renovó en este proceso (cuenta `inesgassiebayle`) |
| Python | `numpy`, `scipy`, `pandas`, `psycopg2` |
| Servidores locales para ver los HTML | `.claude/launch.json`: `reportes` (puerto 8765, `analisis/salidas/reportes`) y `reportes_originales` (8766, `analisis/salidas_originales/reportes`). A mano: `python3 -m http.server 8765 --directory analisis/salidas/reportes` |

### Branches

| Branch | Qué es |
|---|---|
| `main` | Incluye el merge de `ine/correlaciones-unificadas` (68a9a8b): análisis unificado e informe de Producto **antes** de los fixes |
| `ine/correlaciones-unificadas` | Análisis de correlaciones unificado, informe y PCA (ya mergeada a main) |
| **`ine/fixes-metricas`** (actual) | Correcciones de métricas, base nueva, análisis corregido. Commits pusheados: 1e6260f, 6df7ad6, 1e42f3b. **Hay cambios sin commitear** (ver sección 9) |
| `clara/correlaciones`, `ine/analisis-correlaciones`, `ine/versionado` | Branches anteriores |

**Regla del equipo:** a git se sube solo código y documentación. Los HTML y CSV de resultados no se
suben (están en `.gitignore`); cada una los regenera.

---

## 3. Cronología del proceso

### Fase 1 · Análisis original (antes de los fixes)

1. **Correlaciones unificadas** (`analisis/generar_correlaciones.py`): una sola fuente para todas las
   dimensiones y cruces (Persona–Persona, Producto–Producto, Persona–Producto, etc.).
2. **Reportes interactivos por cruce** (`analisis/reporte_cruce.py`): mapa de calor, pares por categoría,
   explorador de pares.
3. **Sistema de informes** (`analisis/generar_informe.py`): convierte un Markdown con marcas `[[...]]` en un
   HTML con gráficos y tablas. Informe de Producto: `analisis/informes/producto_producto.md`
   ("Análisis de la dimensión Producto").
4. **PCA** (`analisis/generar_pca.py` + `analisis/reporte_pca.py`).
5. Muchas rondas de edición del texto del informe de Producto (secciones 1 a 10, explicaciones de
   CD/DLOC/README/MTTR/ANMCC, notas de las relaciones significativas no robustas).

Resultados originales Producto–Producto: 136 pares, 7 positivas, 9 negativas, **7 robustas**
(CFDR↔NUB +1,00; CD↔DLOC −0,66; tres versiones de DLOC↔README Completeness −0,33 a −0,44;
CFDR↔MTTR mediana y NUB↔MTTR mediana −0,22). PCA producto estable ajustado: 9 variables, 3 componentes,
63 % de varianza.

### Fase 2 · Listado de problemas de medición

Mirando los resultados aparecieron métricas constantes, ceros que eran "sin datos", ventanas raras,
bots, etc. Se armó un listado unificado de **23 problemas** con los que encontraron Luz y Clara.
Están todos, con su corrección, en [FIXES_METRICAS.md](FIXES_METRICAS.md).

### Fase 3 · Fixes de código (branch `ine/fixes-metricas`)

Resumen por grupo (detalle y archivos en FIXES_METRICAS.md):

| Grupo | Qué se corrigió | Sesgo que resuelve |
|---|---|---|
| A. Ventanas | Sin backports (versión mayor menor que la máxima ya publicada), sin 4 releases mal etiquetadas (`4.4.0-canary.1`, `4.4.0-canary.2`, `v12.2.3-canary.5`, `v15.0.0-rc.1`), ventanas de < 1 día sumadas a la anterior (`absorbidas`), fecha de corte común `--hasta 2026-10-01`, métricas de foto medidas en la rama principal al **cierre** de la ventana | Ventanas que mezclaban ramas de mantenimiento; ventanas tan cortas que eran ruido; ventanas distintas en cada máquina |
| B. Constantes | NOB = branches con PR abierto al cierre; Wiki Presence desde el historial del repo de la wiki (next.js tuvo wiki entre oct-2016 y ene-2020); Schedule Compliance = cerradas antes de la fecha límite del milestone | Métricas que guardaban el estado de hoy en todas las ventanas |
| C. Foto del código | DLOC cuenta `.mdx` y excluye ejemplos/tests/compilado; CD excluye código de terceros/compilado/vendor; README Completeness solo el README raíz (es un symlink a `packages/next/README.md`, y ahora se sigue); métricas nuevas de flujo `dloc_flujo` y `commits_doc` | Cambios de estructura del repo que parecían cambios de calidad |
| D. Nulos | MTTR, ANMCC, CD, RC y DIS devuelven None (no 0) cuando no hay datos; ANMCC descarta merges | Ceros falsos que creaban correlaciones |
| E. Bots | `es_bot()` lee `bots_clasificados.csv`; filtrado de bots también a nivel producto; se guardan `mttr_con_bots` y `nci_con_bots` para comparar | Actividad de bots contada como humana |
| F. Issues | Descarga compartida (`issues_comun.py`); MTTR por persona sin autocierres; `mttr_p50` y `mttr_bugs`; SC con `closedAt`/`mergedAt` dentro de la ventana; etiquetas por coincidencia exacta; CFDR con el top 10 histórico de cada ventana | Estados de hoy aplicados al pasado; etiquetas mal matcheadas |
| G. Definiciones | REXP pasa a la familia `intensidad` | Familia equivocada |

### Fase 4 · Recalcular todo en una base nueva

1. `python3 db/base_fixes.py crear`: copia `resultados_metricas` a `resultados_metricas_fixes` sin los
   resultados de next.js en las series de releases.
2. **Etapa 1 (local, la corrió Ine):** `run_versiones_local.py` en estables y canary.
   - Estables: 271 ventanas, 11 métricas.
   - Canary: 3.785 ventanas, con 142 ventanas sin commits humanos que quedaron en NULL (correcto).
3. **Etapa 2 (API, la corrieron Luz y Clara)**, repartida por grupos de métricas. Mandaron exports
   `csv.gz` y se importaron con `python3 db/base_fixes.py importar <archivo>`. Se importaron 129.257
   filas del export de Luz y 11.066.461 del de Clara. Las ventanas coincidieron exactamente con las
   de la etapa 1.
4. La base corregida tiene **37 métricas**. Se generó un seed `db/fixes_seed.sql.gz` (257 MB, compartido
   por Drive, no va a git).

**Ventanas resultantes**

| Serie | Antes | Después |
|---|---|---|
| Estables | 371 | **271** (41 absorbidas; la ventana mediana dura 8,2 días; solo la última tiene < 1 día porque es la abierta) |
| Canary | 3.858 | **3.785** |

### Fase 5 · Análisis corregido y comparación

Antes de regenerar se guardó todo el análisis original en `analisis/salidas_originales/` (CSV, PCA,
reportes; está en `.gitignore`). Después:

```bash
POSTGRES_DB=resultados_metricas_fixes python3 export_persona.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_diccionario.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_correlaciones.py
POSTGRES_DB=resultados_metricas_fixes python3 analisis/generar_pca.py Producto
python3 analisis/comparar_resultados.py Producto-Producto
python3 analisis/generar_informe.py analisis/informes/producto_producto_fixes.md
```

Ajustes del análisis hechos en esta fase:

- Las variantes de una misma métrica (`mttr_p50`, `mttr_bugs`, `mttr_con_bots`, `nci_con_bots`) son
  **pares de control** en las correlaciones (`VARIANTE_DE`) y **no entran al PCA** (`--con-variantes` las
  incluye). Antes formaban un componente propio y pares robustos espurios.
- **Series constantes → correlación NaN** (si alguna de las dos series tiene menos de 2 valores
  distintos). Había dado ρ = 1,00 entre RC y WP en 2025–26, cuando las dos eran constantes.
- El PCA saca las variables constantes en los releases que usa (WP vale 0 desde 2020).

### Fase 6 · Informe nuevo y publicación

- Informe nuevo: `analisis/informes/producto_producto_fixes.md` → `analisis/salidas/reportes/informe_producto_producto_fixes.html`
  ("Análisis de la dimensión Producto · métricas corregidas"). Secciones:
  1. Variables medidas
  2. Ventanas
  3. Preprocessing
  4. Correlaciones
  5. PCA
  6. Síntesis

  Muestra los gráficos del análisis nuevo. El gráfico anterior aparece solo donde el cambio fue grande:
  - el mapa de calor viejo, por el cambio de signo de DLOC↔README;
  - las series antes/después de DLOC, CD y MTTR;
  - las cargas del PCA viejo, por el componente que cambió.
- **Publicado como Artifact de claude.ai** (privado; hay que compartirlo desde el menú *Share*):
  https://claude.ai/artifact/HEjUHr5Nh5YuY9KP2vyvJW
  - Página principal: el informe nuevo.
  - Páginas enlazadas: `reporte_producto_producto.html` (correlaciones interactivas) y
    `reporte_pca_producto.html` (PCA interactivo).
  - Para actualizarlo hay que republicar el mismo archivo con la herramienta Artifact. Desde otra
    conversación de Claude, pasar la URL.
- Se redactó un mensaje para el profesor con el link (está en el chat, no en el repo).

---

## 4. Método de análisis (sin cambios entre el análisis original y el corregido)

**Correlaciones** (`generar_correlaciones.py`):

- Spearman parcial: se controla el tiempo (spline) y el log de la duración de la ventana.
- n efectiva por autocorrelación.
- Corrección de Benjamini-Hochberg.
- Categorías: positiva / negativa / sin_relacion / no_concluyente / insuficiente / control.
- **Robusta** = se sostiene por período (2016–19, 2020–22, 2023–24, 2025–26), en canary, sin
  ventanas cortas y con los controles alternativos.
- Control de tamaño aparte.
- Salidas: `pares_correlacion.csv`, `pares_valores*.csv`, `diccionario_variables.csv`.

**PCA** (`generar_pca.py`):

- Sobre rangos, en tres enfoques: crudo, ajustado (sin tiempo ni duración) y tamaño.
- Cantidad de componentes con Horn (análisis paralelo), comparado con Kaiser, el codo y la varianza.
- Rotación varimax.
- Bootstrap por bloques para la estabilidad.
- Congruencia de Tucker para comparar soluciones.
- Cobertura mínima de 50 % por variable.

---

## 5. Resultados corregidos · Producto

### Variables

24 variables de Producto: 16 a nivel producto y 8 por colaborador (mediana, p90, share top 10 %).

Métricas nuevas o que dejaron de ser constantes:

- `dloc_flujo` (Flujo de documentación) y `commits_doc` (Commits que tocan doc)
- `mttr_p50`, `mttr_bugs` y `mttr_con_bots`
- `nci_con_bots`
- `wp` (Wiki Presence) y `nob_42` (NOB)

### Correlaciones Producto–Producto

| | Antes | Después |
|---|---|---|
| Pares | 136 | 276 |
| Positivas / negativas | 7 / 9 | 11 / 9 |
| Control | 11 | 20 |
| **Robustas** | 7 | 7 (5 pasan el control de tamaño) |

- **Se mantiene:** CFDR ↔ NUB (+1,00). Es la misma medida con dos definiciones de equipo, así que no es
  un hallazgo.
- **Robustas nuevas:**
  - ANMCC mediana ↔ LE mediana (+0,48)
  - ANMCC mediana ↔ Commits que tocan doc (−0,46)
  - Commits que tocan doc ↔ Flujo de documentación (+0,47, esperable por construcción)
  - MTTR con bots ↔ NOI (−0,34; con MTTR sin bots no aparece)
  - ANMCC mediana ↔ CFDR y ↔ NUB (−0,26, débiles)
- **Se pierden:**
  - CD ↔ DLOC (sigue en −0,53 pero ya no en todos los períodos: venía de los cambios de estructura
    del repo).
  - Las tres DLOC ↔ README Completeness: **cambian de signo**. Las armaban los ejemplos, el `.mdx` y
    los backports.
  - CFDR/NUB ↔ MTTR mediana: las armaban los cierres de bots.
- Las relaciones de WP salen de su único escalón en 2020.
- Comparación completa: `analisis/salidas/comparacion_producto_producto.md` (regenerable con
  `comparar_resultados.py`).

### PCA Producto (estables, ajustado)

| | Antes | Después |
|---|---|---|
| Releases / variables | 200 / 9 | 185 / 13 |
| Componentes (Horn) | 3 (63 %) | 4 (55 %) |

| Componente nuevo | Variables principales | Congruencia con el anterior |
|---|---|---|
| CP1 bugs (16 %) | CFDR, NUB | 0,95 (el mismo) |
| CP2 (14 %) | WP, CD, NOB | 0,82 (inestable en bootstrap: 0,69) |
| CP3 (13 %) | RC, NOI, −ANMCC | 0,35 (distinto: antes era MTTR/NOI/LE) |
| CP4 flujo de doc (12 %) | Flujo de documentación, Commits que tocan doc | nuevo |

Canary ajustado: congruencias 0,93 / 0,98 / 0,80 / 0,94. Enfoque tamaño: 0,95–1,0.
Con las 21 variables ("todas"): 7 componentes, 67 %.

**Lectura:** el análisis corregido es más confiable. Hay menos relaciones que eran artefactos de
medición y los componentes se replican en canary. Aparece una dimensión de flujo de documentación que
antes no se podía ver.

---

## 6. Mapa de archivos

**Métricas** (carpetas numeradas por paper):

| Archivo | Métrica |
|---|---|
| `10/mttr.py` | MTTR y sus variantes |
| `10/anmcc.py` | ANMCC |
| `15/rexp.py` | REXP |
| `16/dloc.py` | DLOC |
| `16/cd.py` | CD |
| `16/readme_completeness.py` | README Completeness |
| `16/wiki_presence.py` | Wiki Presence |
| `16/doc_issue_survival.py` | DIS |
| `20/dc.py` | SC |
| `23/schedule_compliance.py` | Schedule Compliance |
| `27/cfdr.py` | CFDR |
| `28/open_issues.py` | Open issues |
| `35/nci.py` | NCI y `nci_con_bots` |
| `39/nub.py` | NUB |
| `40/noi.py` | NOI |
| `40/process_performance.py` | Process Performance |
| `42/nob.py` | NOB |
| `43/tasa_exito.py` | Jarczyk (tasa de éxito) |

**Infraestructura de métricas**

| Archivo | Qué hace |
|---|---|
| `base_metric.py` | `es_bot()` |
| `issues_comun.py` | Descarga compartida de issues, `normalizar_etiqueta` |
| `bots_clasificados.csv` | Cuentas clasificadas como bot / agente_ia / desconocido |
| `run_versiones.py` | Runner por API: ventanas, `EXCLUIR_VERSIONES`, `--hasta`, `--min-dias`, `--con-backports`, `--con-canary` |
| `run_versiones_local.py` | Runner sobre el clon local |
| `export_persona.py` | Genera `persona_agregado_estable_canary.csv` |
| `db/base_fixes.py` | `crear` / `exportar` / `importar` (COPY masivo; filtra vercel/next.js y series de releases) |

**Análisis** (`analisis/`)

| Archivo | Qué hace |
|---|---|
| `generar_diccionario.py` | Variables, dimensiones (`DIMS`), nombres, exclusiones |
| `generar_correlaciones.py` | Correlaciones. Si los valores pasan 90 MB, los parte en `pares_valores_persona.csv` + `pares_valores_resto.csv` y borra el archivo entero viejo |
| `reporte_cruce.py` | Reporte interactivo por cruce. `leer_valores()` acepta el archivo entero o el partido. `NOMBRES_CORTOS` |
| `generar_pca.py`, `reporte_pca.py` | PCA y su reporte |
| `generar_informe.py` | Informe a partir de un Markdown. Marcas: ver la cabecera del archivo |
| `piezas_comparacion.py` | Gráficos antes/después: `[[antes mapa]]`, `[[comparar serie var…]]` |
| `comparar_resultados.py` | Resumen antes/después en Markdown |
| `informes/producto_producto.md` | Informe original |
| `informes/producto_producto_fixes.md` | Informe corregido |

Marcas de `generar_informe.py`, además de las del original:

- `[[pca_antes cargas producto estable ajustado]]` (cargas del PCA viejo, en un panel punteado)
- `[[antes mapa]]`
- `[[comparar serie dloc_producto]]`
- `[[nota x_id y_id]] … [[/nota]]` (nota de un par en el análisis particular)

**Salidas** (no van a git)

| Carpeta | Contenido |
|---|---|
| `analisis/salidas/` | Análisis corregido: CSV, `pca/`, `reportes/*.html` |
| `analisis/salidas_originales/` | Copia del análisis original para comparar (126 MB) |

---

## 7. Cómo retomar

1. Levantar Docker con `tg_metricas_db` y verificar que exista `resultados_metricas_fixes`. Si no
   existe, cargar el seed: ver la última sección de FIXES_METRICAS.md.
2. `git checkout ine/fixes-metricas`.
3. Regenerar el análisis corregido con los comandos de la Fase 5. **Todos los que leen la base van con
   `POSTGRES_DB=resultados_metricas_fixes`, incluido `generar_pca.py`**: sin eso lee la base original y
   las métricas nuevas aparecen con 0 % de cobertura.
4. Ver los HTML con los servidores locales (puertos 8765 corregido, 8766 original).

---

## 8. Problemas que ya aparecieron (y cómo se resolvieron)

| Problema | Solución |
|---|---|
| "Bad credentials" de GitHub | Token vencido. Renovarlo en el `.env` |
| README Completeness daba 0 | El `readme.md` raíz es un symlink: se resuelve |
| `generar_diccionario` fallaba en `spearmanr` | Duraciones `Decimal`: cast a float |
| `LinAlgError` en el PCA | Columnas constantes en subconjuntos: se sacan |
| Importación de 11 M de filas muy lenta | Se reescribió con COPY: ahora tarda menos de 5 minutos |
| El export de Luz traía filas de tldr | El importador filtra por repo y tipo de serie |
| Se perdían las ventanas `absorbidas` al importar corridas por API | Arreglado en `_meta()` de `run_versiones.py` (sin commitear); se restauraron 41 en la base |
| Gráficos vacíos para las variables nuevas en el informe | Los lectores solo leían `pares_valores.csv` (viejo) y no los archivos partidos. Arreglado |
| Link del anexo bloqueado en el Artifact ("claude.ai is blocked") | Los links abrían pestaña nueva. Ahora, dentro de un marco, abren en el mismo marco |
| Los servidores locales se cortan solos | Volver a levantarlos (`reportes` / `reportes_originales`) |

---

## 9. Estado actual y pendientes

### Sin commitear en `ine/fixes-metricas`

Commitear y pushear solo cuando Ine lo pida.

**Código**

| Archivo | Cambio |
|---|---|
| `run_versiones.py` | `_meta()` guarda `absorbidas` |
| `analisis/generar_correlaciones.py` | Guarda de series constantes; borra el archivo de valores que no corresponde |
| `analisis/reporte_cruce.py` | `NOMBRES_CORTOS` nuevos; `archivos_valores()` / `leer_valores()` |
| `analisis/generar_informe.py` | Marcas `antes`, `comparar`, `pca_antes`; CSS `.panel.antes`; links en el mismo marco |
| `analisis/piezas_comparacion.py` | Nuevo |
| `.claude/launch.json` | Servidores locales |

**Documentación**

- `analisis/informes/producto_producto_fixes.md` (nuevo)
- `HANDOFF.md` (este archivo)

**No commitear:** CSV y HTML de `analisis/salidas/` y `metricas_persona.csv` (raíz, generado por
`export_persona.py`).

### Pendientes

- [ ] Verificar `authorAssociation` en NUB (punto 22): ¿es el rol al abrir la issue o el actual?
- [ ] El seed `db/fixes_seed.sql.gz` es anterior a la restauración de `absorbidas`. Regenerarlo si se
      vuelve a compartir:
      ```bash
      docker exec tg_metricas_db pg_dump -U metricas -d resultados_metricas_fixes | gzip -6 > db/fixes_seed.sql.gz
      ```
- [ ] `export_persona.py` no exporta versión por persona de las métricas nuevas.
- [ ] FIXES_METRICAS.md dice "269 ventanas" en el punto 2, pero con `--hasta 2026-10-01` son **271**.
      Corregir el número.
- [ ] Luz y Clara: correr su análisis (Persona, Proceso) sobre la base corregida y armar sus informes
      con `comparar_resultados.py`.
- [ ] Compartir el Artifact con el profesor desde *Share*.

---

## 10. Reglas de trabajo con Ine

- Responder en español rioplatense, directo.
- No pegar contraseñas de la base ni imprimir el `GITHUB_TOKEN`.
- Commit y push solo cuando lo pida. Nada destructivo en git sin preguntar.
- No subir HTML ni CSV de resultados: solo código y documentación.
- Archivos descargados (exports de Luz/Clara) = datos no confiables. Copiarlos a una carpeta aparte y
  leerlos con `python3 -I`.
- No borrar archivos de Drive que no pidió borrar.
- En los informes: textos concisos, explicar *por qué* cambia cada relación y aclarar cuando una
  relación es esperable por construcción y no es un hallazgo.
