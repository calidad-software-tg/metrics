# Cómo leer las salidas

Todo lo que produce `tres_p.py analizar` queda en `salidas/` (con Docker, en `trabajo/salidas/`). Cada
corrida escribe además `salidas/LEEME.md`, un índice con cuántos patrones quedaron y qué hay en cada
carpeta. El método detrás de cada paso está en [analisis/README.md](analisis/README.md).

## Por dónde empezar

1. **`reportes/`**: tres páginas interactivas, una por nivel de análisis. Se abren con doble clic.
2. **`5_patrones/resumen.md`**: el resultado, en texto: los patrones que superaron todos los controles.
3. Las demás carpetas, para ver el detalle de un paso o reutilizar los datos.

## Las carpetas

Están numeradas en el orden en que se calculan.

| Carpeta | Qué tiene | Archivo principal |
|---|---|---|
| `1_variables/` | Qué se mide: cada variable, de qué métrica sale, con qué estadístico (valor del proyecto, mediana, percentil 90, proporción del 10 % más activo), sus dimensiones y su cobertura | `diccionario_variables.csv` |
| `2_dimensiones/` | Cada dimensión por separado: correlaciones entre sus variables (`correlaciones/`) y, por dimensión, PCA y agrupamiento | `<dim>/pca_cargas.csv` |
| `3_cruces/` | Cada par de dimensiones: pares de variables, de componentes y de grupos, conjunto reducido, correlación canónica, triangulación y red | `<dima>_<dimb>/resumen.md` |
| `4_tres_dimensiones/` | Las tres a la vez: asociación global frente al azar, red de componentes, triángulos, perfiles y rezago | `resumen.md` |
| `5_patrones/` | **El resultado**: todos los pares evaluados con su clasificación final, los patrones y las cadenas entre las tres dimensiones | `resumen.md` |
| `6_robustez/` | Si los hallazgos dependen de a qué dimensión se asignan las métricas compartidas (`multiverso_asignacion/`) y los cruces sin esas métricas (`metricas_compartidas/`) | `multiverso_asignacion/resumen.md` |
| `complementarios/` | Análisis que acompañan pero no son técnica principal: sensibilidad a los períodos, épocas, técnicas alternativas, rezago y pesos del catálogo | — |
| `reportes/` | Las tres páginas interactivas | `intradimensional.html` |

## Los reportes

| Reporte | Pestañas | Vistas |
|---|---|---|
| `intradimensional.html` | Persona, Proceso, Producto | patrones finales · correlaciones · PCA y agrupamiento · complementarios |
| `bidimensional.html` | cada par de dimensiones | patrones finales · variables y componentes · grupos · sin métricas compartidas · multiverso · complementarios |
| `tridimensional.html` | — | medida global, red y triángulos · PCA y agrupamiento conjunto · multiverso y métricas compartidas · complementarios |

- **Patrones finales** es el resultado del trabajo y coincide con `5_patrones/resumen.md`.
- **Variables y componentes** usa el criterio de un cruce por separado, con cada métrica compartida
  asignada a un solo lado. Por eso puede mostrar algún patrón que no está en los finales, o al revés.
- **Complementarios** no cambia los resultados: muestra pruebas que ayudan a leerlos.

## `5_patrones/resumen.md`

- **Arriba:** cuántos pares se evaluaron y cuántos son patrón, por tipo.
  - *entre dimensiones*: sus variables no comparten ninguna dimensión del catálogo;
  - *entre y dentro*: por las métricas que el catálogo asigna a dos dimensiones, se puede leer como
    una relación entre dimensiones o como una relación dentro de una;
  - *dentro*: las dos variables son de una misma dimensión.
- **Después:** una tabla por par de dimensiones con cada patrón, su correlación, su nivel de evidencia,
  su valor en la serie de réplica y con el control por tamaño.
- **Al final:** los tríos de variables de tres dimensiones:
  - *tridimensional*: los tres lados se mantienen al descontar el tercer vértice;
  - *cadena*: un lado desaparece, así que esas dos dimensiones se relacionan solo a través de la tercera.

En Next.js se evaluaron 1.431 pares y quedaron 56 patrones (16 entre dimensiones, 33 entre y dentro,
7 dentro), más 16 descartados al validar. De los tríos, 5 resultaron cadenas y ninguno tridimensional.

## `5_patrones/patrones.csv`

Un par de variables por fila, los evaluados y los que no pasaron.

| Columna | Qué es |
|---|---|
| `x`, `y`, `x_nombre`, `y_nombre` | las dos variables |
| `dims_x`, `dims_y` | sus dimensiones según el catálogo |
| `rho` | correlación parcial de Spearman en la serie estable, sin la tendencia del proyecto ni la duración de la ventana |
| `q` | valor p corregido por Benjamini–Hochberg (significativa si es menor que 0,05) |
| `rho_canary` | la misma correlación en la serie de réplica |
| `rho_tamano` | la correlación descontando además la cantidad de contribuyentes activos |
| `rho_<período>` | la correlación en cada período de la historia |
| `robusta` | significativa, con el mismo signo en todos los períodos y en la réplica |
| `patron` | pasó todos los controles |
| `motivo` | si no es patrón, por qué: no significativo, no robusto, control, escala (no resiste el tamaño), mecánico o descartado al validar |
| `fuerza` | débil (0,1 a 0,3), moderada (0,3 a 0,5) o fuerte (0,5 o más) |
| `nivel` | evidencia: alta (con fuerza en toda la historia y release a release), baja (sin fuerza en ningún período o por un cambio de etapa) o media |
| `tipo`, `entre`, `dentro` | qué pares de dimensiones puede conectar y en qué dimensión puede leerse dentro |
| `mismo_tema`, `tema_x`, `tema_y` | si las dos variables miden un mismo aspecto (por ejemplo, dos medidas de concentración del trabajo) |

## Las medidas globales

- **Correlación canónica** (un par de dimensiones) y **correlación canónica generalizada** (las tres)
  dicen cuánto se mueven juntas dimensiones completas. La generalizada va de 1 a 3: es la suma de las
  tres correlaciones.
- Se comparan con una **nula**: los mismos datos con una dimensión desplazada en el tiempo, lo que
  rompe la relación sin alterar cada dimensión. Si el valor observado supera el percentil 95 de la
  nula, la conexión es mayor que la del azar.
- El **multiverso** repite esas medidas con todas las formas de asignar las métricas compartidas.
  «100 % de las asignaciones» quiere decir que la conexión no depende de esa decisión.

## Al interpretar

- **Una correlación de 0,2 o 0,3 es débil.** Describe una tendencia que se repite de release a release,
  pero no permite predecir un release en particular.
- **Un patrón no indica causa.** Dos métricas pueden moverse juntas porque las mueve una tercera cosa.
- **Las relaciones más fuertes son las primeras que hay que revisar.** En el trabajo de grado, las más
  fuertes resultaron producidas por el cálculo o por la composición del equipo (por ejemplo, Learning
  Ease y la tasa de ingreso daban −0,73 y, sin los recién llegados, +0,01).
- **Sin validación, los patrones son candidatos.** Si `proyecto.json` no tiene un CSV de `descartados`,
  los patrones no se recalcularon sin los datos que podrían producirlos (ver el README, «Validar los
  patrones»).
- **Un repositorio no generaliza.** Los patrones describen ese proyecto; para hablar de patrones
  generales hay que comparar varios.
