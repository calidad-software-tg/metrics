# Diferencias entre los datos de `analisis` y el texto de los capítulos 4 y 5

Fecha: 4/11/2026 · rama `clara/visualizaciones` (creada desde `analisis`, commit `5702d73`, del 31/10).

Todas las salidas se regeneraron con el código de `analisis` (base `resultados_metricas_fixes`, solo lectura). `relaciones/patrones.csv` y `relaciones/triangulos.csv` dieron **idénticos** a los commiteados (diferencia numérica máxima: 0). Las figuras usan siempre el dato real; donde el texto dice otra cosa, se anota acá.

El listado automático de cada número que no coincide está en [diferencias_automaticas.md](diferencias_automaticas.md) (lo regenera `figuras_informe.py`). Este documento explica de dónde viene cada diferencia.

---

## 1. Cuáles son las diferencias reales

Son de dos tipos: las que se explican porque **el texto usa validaciones que no están en el código de `analisis`**, y las que son **errores o imprecisiones del texto** (aparecen aunque se corra con los datos más nuevos).

### 1.1 Validaciones que no están en `analisis` (la causa principal)

En `analisis/relaciones.py` (líneas 56–64), la lista `DESCARTADOS` está escrita a mano y tiene **7** relaciones descartadas al validar. El texto se escribió con **15** descartadas y con una relación que pasa de descartada a "se mantiene". Por eso:

| | Código de `analisis` | Texto |
|---|---|---|
| Descartadas al validar | 7 | 15 |
| Patrones | **65** | **57** |
| Persona: descartadas / patrones (Tabla 7) | 0 / 26 | 7 / 19 |
| Proceso: descartadas / patrones (Tabla 7) | 2 / 28 | 5 / 25 |
| Producto (Tabla 7) | igual | igual |

Relaciones que el texto descarta y en `analisis` siguen siendo patrón (8):

| Relación | ρ | Validación que la descarta en el texto | ¿Está el script en `analisis`? |
|---|---|---|---|
| LE (mediana) ↔ tasa de ingreso | −0,73 → +0,01 | sin recién llegados | **No** (`experiencia_ingreso_sin_recien_llegados.py`) |
| Development Experience (mediana) ↔ tasa de ingreso | −0,71 → −0,02 | sin recién llegados | **No** (mismo script) |
| CDIV (mediana) ↔ tasa de ingreso | −0,44 → +0,01 | sin recién llegados | **No** (mismo script) |
| REXP (mediana) ↔ tasa de ingreso | −0,29 → −0,02 | sin recién llegados | **No** (mismo script) |
| CDIV ↔ LE (medianas) | +0,49 → +0,04 | sin recién llegados | **No** (mismo script) |
| CDIV ↔ Development Experience (medianas) | +0,41 → +0,06 | sin recién llegados | **No** (mismo script) |
| LE ↔ REXP (medianas) | +0,29 → +0,07 | sin recién llegados | **No** (mismo script) |
| NCI ↔ Jarczyk Success Rate | +0,39 → +0,15 | sin las issues del mismo release | **No** (`nci_sin_issues_del_release`) |
| NCI ↔ Process Performance | +0,28 → +0,08 | sin las issues del mismo release | **No** (mismo script) |

Y una que va al revés:

| Relación | Código de `analisis` | Texto |
|---|---|---|
| Proporción que commitea ↔ LE del proyecto (−0,29) | descartada ("construcción de LE") | **se mantiene** (−0,29 → −0,20); es parte de la familia R y de la segunda cadena |

Cuenta: 7 + 9 − 1 = 15 descartadas → 72 − 15 = 57 patrones.

Además, el texto informa valores recalculados que **ningún script de `analisis` produce**:

- las medianas de LE y Development Experience frente a la proporción que commitea sin recién llegados (−0,33 → −0,38 y −0,30 → −0,29; familia C, Fig. 6 y Fig. 8);
- NCI con MTTR sin las issues del mismo release (+0,29 → +0,51) y NCI con DIS (Fig. 11 y Fig. 13);
- la tasa de ingreso y la proporción que commitea con LE del proyecto sin recién llegados (−0,26 → +0,08 y −0,29 → −0,20).

**Consecuencias en el texto** (todas vienen de lo anterior, no son errores propios):

- Embudo: 57 patrones y 15 descartados (datos: 65 y 7). Todo el embudo hasta "72 sin explicación mecánica" **coincide**.
- Tabla 11: Persona–Proceso 27 (5 + 22), Persona–Producto 20 (13 + 7), Proceso–Producto 17 (8 + 9). Datos: 37 (5 + 32), 22 (12 + 10), 20 (8 + 12). Entre dimensiones: 42 (16 + 26) en el texto; datos: 55 (15 + 40).
- Familia R: el texto tiene 4 patrones (−0,20 a −0,29); los datos 3 (−0,20 a −0,22), porque falta proporción que commitea ↔ LE del proyecto.
- Segunda cadena (concentración → proporción que commitea → LE del proyecto, sección 4.4.2 y 5.3): **no aparece en `relaciones/triangulos.csv`** porque uno de sus lados está descartado en el código.
- Épocas: "43 de los 57 patrones" se refiere a los 57.

### 1.2 Diferencias que son del texto (no dependen de qué datos se usen)

Estas hay que corregirlas en el texto aunque se corra con los datos más nuevos, porque los números que las sostienen no cambian con las validaciones:

1. **Embudo de componentes (4.3.2 y figura a numerar).** El texto dice "9 robustos → 7 que no son de escala ni mecánicos → 5 patrones". Con 2 de escala y 2 mecánicos, 9 − 2 − 2 = **5**, no 7. Los datos dan 33 → 10 → 9 → 5 → 4. Grupos coincide (125 → 36 → 26 → 17 → 15).
2. **Volumen de participación ↔ bugs de usuarios (5.2 y Fig. 26).** El texto dice +0,50 → −0,15 con control por tamaño. Entre componentes los datos dan **+0,55 → −0,14**; entre grupos, +0,64 → +0,06 y +0,54 → −0,01. Ninguno da +0,50 / −0,15.
3. **Cadena principal (4.4.2, 5.3 y Fig. 19).** El texto dice que al descontar la concentración "los otros dos lados casi no cambian". Es cierto en la versión con EXPRev (+0,29 → +0,22), pero en las versiones con NC y con SC p90 el lado concentración ↔ DLOC 2.0 **también cae**: +0,21 → +0,13 y +0,20 → +0,12 (dentro de ±0,15). El rango del lado directo (+0,21 → +0,08 a +0,13) sí coincide. Se ve en la Fig. 19b.
4. **Nombre de DLOC.** La variable de la cadena y de la familia O es `dloc_flujo_producto` = **DLOC 2.0** (líneas de documentación agregadas o eliminadas en la ventana). El texto alterna "Documented Lines of Code", "Documentation Lines of Code" y, en la familia O, "Documented Lines **Of Comments**" (ese último está mal).
5. **Nombres de los componentes de Persona.** Los temas que asigna el código (`multiverso_asignacion.tema_de`) son "renovación y experiencia", "volumen de actividad", "concentración del núcleo", "revisores más activos" y "participación". El texto usa "renovación del equipo", "volumen de participación" e "ingreso a la discusión" para el quinto. Las figuras usan los nombres del código; conviene unificar.
6. **Porcentajes de la Tabla 13.** El texto dice 100 %, 99 % y 81 %; los datos dan 99,8 %, 98,8 % y 81,4 % (sobre las 500 asignaciones al azar). Es redondeo, pero "100 %" puede leerse como "todas". Sugerencia: "más del 99 %".
7. **Fig. 15.** El texto dice "las dos familias desarrolladas" sin nombrarlas; se usaron O y P. Confirmar.
8. **Fig. 18.** El texto pide una banda "del mínimo al P95 de la nula", pero `tres_dimensiones/resumen.json` guarda solo el P95. La banda va desde 1 hasta el P95.

### 1.3 Lo que coincide exactamente con el texto

Para tranquilidad: embudo hasta 72; Tabla 7 completa en Producto y en todas las columnas menos validación y patrones; 20 de las 21 familias (A–Q y S–U) con su cantidad y rango de ρ; Tabla 13 y Fig. 17 (0,45 / 0,61 / 0,33; P5–P95 0,54–0,84, 0,50–0,73, 0,32–0,71; 518 asignaciones); 4.4.1 completa (GCCA 1,71 vs. 1,44; canary 1,63 vs. 1,12; sin tamaño 1,58 vs. 1,38; RV 0,098 vs. 0,031; MFA 24 % vs. 21 %); PCA de Persona (5 componentes, 59 %, varianzas rotadas 16,5 / 14,5 / 12,1 / 10,3 / 5,9 %, 3 firmes), de Proceso (5 componentes, 76 %, 5 firmes) y de Producto (4, 55 %, 2 firmes); clustering (10, 7 y 9 grupos; ARI 0,71 y 0,66 en Persona); familia B cambia de signo en la época 2 en 3 relaciones; cadena principal (+0,43 a +0,47; +0,20 a +0,29; +0,21 → +0,08 a +0,13); los 4 patrones entre componentes (−0,37, +0,27, −0,25, −0,22); 838 pares intradimensionales, 94 en dos dimensiones.

---

## 2. Qué figuras afectan

### Terminadas: no dependen de las validaciones que faltan

Estas salen igual con los datos de tu amiga, porque las validaciones no las tocan (el PCA, el clustering, los bloques, el multiverso y las tres dimensiones no usan la lista `DESCARTADOS`). Se pueden dar por terminadas, salvo las correcciones de texto de la sección 1.2.

| Figura | Archivo | Nota |
|---|---|---|
| 2 | `fig02_variables_por_dimension` | |
| 7 | `fig07_estabilidad_ABC` | |
| 9 | `fig09_cargas_persona` | nombres de componentes del código (1.2.5) |
| 10 | `fig10_dendrograma_persona` | |
| 12 | `fig12_bosque_proceso` | |
| 15 | `fig15_bosque_entre_dimensiones` | confirmar que son O y P (1.2.7) |
| 15b | `fig15b_embudo_componentes_grupos` | corregir el "7" del texto (1.2.1) |
| 16 | `fig16_componentes_tres_dimensiones` | |
| 17 | `fig17_multiverso_asignacion` | |
| 18 | `fig18_tres_dimensiones_vs_azar` | banda desde 1 (1.2.8) |
| 19 | `fig19_cadena` | |
| 19b | `fig19b_cadena_mancuernas` | muestra el matiz de 1.2.3 |
| 20 | `fig20_componentes_en_el_tiempo` | |

### Cambian cuando se agreguen las validaciones (rehacer con los datos nuevos)

El código de estas figuras ya está hecho: solo hay que volver a correrlo. Las marcadas con † necesitan además que el script de validación guarde un `resumen.json` para que la figura lo lea.

| Figura | Archivo | Qué cambia |
|---|---|---|
| 3 | `fig03_embudo` | último escalón: 65 → 57 y 7 → 15 descartados |
| 4 | `fig04_destino_resisten_tamano` | segmentos de descartados y patrones en Persona y Proceso |
| 5 | `fig05_red_persona` | las 7 relaciones de medianas de experiencia pasan a "descartadas al validar" |
| 6 † | `fig06_bosque_ABC` | se agregan las 2 filas de la familia C sin recién llegados (−0,38 y −0,29) |
| 8 † | `fig08_experiencia_sin_recien_llegados` | **no se puede hacer** sin `experiencia_ingreso_sin_recien_llegados` |
| 11 † | `fig11_dos_actividades_proceso` | NCI ↔ Jarczyk pasa a descartada; faltan +0,51 y +0,15 |
| 13 † | `fig13_nci_sin_issues_del_release` | **no se puede hacer** sin `nci_sin_issues_del_release` |
| 14 | `fig14_patrones_por_par` | 37/22/20 → 27/20/17 |
| 21 † | `fig21_validacion` | hoy tiene solo las validaciones que existen; con las nuevas, las 18 filas |
| 24 † | `fig24_que_quedo` | bloque "descartada" completo y familia R con 4 patrones |
| 25 | `fig25_aspectos_por_dimension` | cantidad de patrones por aspecto en Persona y Proceso |
| 26 | `fig26_mapa_conexiones` | grosor de las aristas (27/20/17); el recuadro de tamaño no cambia |
| Tablas 7, 11, 12, 14, 16 | `analisis/salidas/tablas/` | por lo mismo |

### Pendientes por otros motivos

| Figura | Motivo |
|---|---|
| 22, 23 | dependen de `cruce_alternativos.py` (Persona–Proceso, Persona–Producto, Proceso–Producto), que está corriendo; no dependen de las validaciones |
| 27 | falta calcular la comparación dataset original vs. corregido; no se hace sin confirmación |

---

## 3. ¿Conviene que tu amiga lo corra con sus datos?

**Sí, pero lo importante no son sus datos sino su código.** Las salidas de `analisis` se reproducen idénticas con la base que ya está; la diferencia viene de validaciones que no están en el repositorio. Si ella solo comparte CSV o números, las figuras quedarían apoyadas en resultados que nadie puede regenerar. Lo correcto es que **suba a `analisis` el código** de esas validaciones y la lista de descartados actualizada, y después se corre todo (lo puede correr ella o cualquiera con la base).

### Qué tiene que subir a `analisis`

1. **`analisis/relaciones.py`** con `DESCARTADOS` actualizado: agregar las 9 relaciones de la tabla de 1.1 y sacar `prop_commitean_ratio ↔ le_producto`.
2. **Los scripts de validación** que producen los números del texto, en `analisis/validaciones/`:
   - `experiencia_ingreso_sin_recien_llegados.py`: medianas de experiencia sin recién llegados frente a la tasa de ingreso, entre sí y frente a la proporción que commitea; y LE del proyecto frente a la tasa de ingreso y a la proporción que commitea.
   - `nci_sin_issues_del_release.py`: NCI sin las issues abiertas en el mismo release frente a Jarczyk, Process Performance, MTTR y DIS.
3. Que cada uno escriba `analisis/salidas/validaciones/<nombre_del_script>/resumen.json` con, por cada relación, el ρ original y el recalculado (como hacen `cdiv_sin_commits_doc.py` y `anmcc_sin_commits_doc.py`). Con eso las figuras 6, 8, 11, 13, 21 y 24 los leen directamente; si el formato es otro, hay que ajustar la función `validados()` de `figuras_informe.py`.

### Qué hay que correr después (desde la raíz del repo)

```bash
git switch analisis && git pull                      # con lo que subió ella
export POSTGRES_DB=resultados_metricas_fixes

# 1. relaciones con la lista de descartados nueva (no hace falta --recalcular: los pares no cambian)
python3 analisis/relaciones.py

# 2. validaciones (las nuevas y las que ya existen)
python3 analisis/validaciones/experiencia_ingreso_sin_recien_llegados.py
python3 analisis/validaciones/nci_sin_issues_del_release.py
python3 analisis/validaciones/experiencia_sin_recien_llegados.py
python3 analisis/validaciones/cdiv_sin_commits_doc.py
python3 analisis/validaciones/anmcc_sin_commits_doc.py
python3 analisis/verificar_sc_jarczyk.py "$PWD"

# 3. figuras y tablas (en la rama de visualizaciones, con analisis mergeado)
git switch clara/visualizaciones && git merge analisis
python3 analisis/figuras_informe.py
python3 analisis/tablas_informe.py
```

No hace falta volver a correr PCA, clustering, épocas, `tres_dimensiones.py`, `bloques_etiquetas.py` ni `multiverso_asignacion.py`: no dependen de `DESCARTADOS`. Si cambió algo más en sus métricas (no solo validaciones), entonces sí hay que correr todo, en el orden de `analisis/README.md`.

Al terminar, `diferencias_automaticas.md` tiene que quedar solo con las diferencias de la sección 1.2 (que se corrigen en el texto). Si aparece cualquier otra, es que el texto y los datos todavía no coinciden.
