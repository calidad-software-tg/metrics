# Método: Correlaciones por Dimensión (3P)

## Fuente y serie

Datos de **vercel/next.js**, serie **estable** (`tipo_analisis = 'versiones'`),
excluyendo las 4 releases: `4.4.0-canary.2`, `4.4.0-canary.1`,
`v12.2.3-canary.5`, `v15.0.0-rc.1`.

Se incluye `rho_canary` calculada sobre la serie `versiones_canary`.

## Variables

- **nivel=producto**: valor de producto (`contribuyente_login IS NULL`).
- **nivel=persona_agregada**: mediana, p90, share_top10pct o conteo desde
  `persona_agregado_estable_canary.csv`, alcance=humanos.
- **ratios derivados** (estadistico=ratio): tasa_nuevos y prop_* calculados
  dividiendo conteos por release. Vacío si denominador = 0.

### Familia (variables con Persona)
tamano · composicion · intensidad · red · amplitud · otra

## Correlación corregida (Spearman parcial con tendencia flexible)

Spline natural de 4 df sobre `rank(periodo_num)` + `rank(log(duracion_días))`.
`rho_corregida_lineal` conserva el control lineal anterior.

### Muestra efectiva (n_efectiva)

Pyper-Peterman 1998: `n_ef = n × (1−r1x×r1y) / (1+r1x×r1y)`, acotado [10, n].
p_corregida: t con `n_ef − 7` gl. IC95: Fisher z con `se = 1/√(n_ef−3)`.

No hace falta logaritmo ni dividir por días: la correlación trabaja con rangos y
descuenta la duración de la ventana en todos los pares.

### Corrección por tamaño (rho_corregida_tamano)

Para todos los pares salvo los de control y los que incluyen una variable de la
familia tamano (`tamano_aplica`): misma correlación parcial controlando además por
`rank(log(activos_interaccion+1))`. K_controles = 6; gl = `n_ef − 8`.
Si no aplica queda vacía.

## Benjamini-Hochberg (p_fdr)

Dentro de cada cruce, solo pares con `por_construccion = false`.

## Pares por_construccion

misma_metrica; activos ↔ nuevos del mismo canal; activos_comentarios/cierre ↔ activos_interaccion;
proporciones ↔ sus dos componentes (numerador y denominador); nc/sc/nci ↔ exprev y rexprev, y
exprev ↔ rexprev (se calculan con los mismos eventos de issues, PR y comentarios).

## solapamiento_definicion

Métricas distintas cuya definición comparte ingredientes: ANMCC ↔ Contribution
Diversity; Learning Easy ↔ Development Experience; Learning Easy ↔ nuevos en commits;
REXP ↔ REXPRev; DLOC ↔ README Completeness (DLOC cuenta las líneas de los README.md);
NOI ↔ CFDR / NUB (cada bug abierto es una issue abierta); dos proporciones de participación que
comparten un conteo (por ejemplo, proporción que commitea y tasa de ingreso de commits, que usan los
commiters activos). Es el único criterio de relación mecánica, igual para las métricas del proyecto y
para las variables por colaborador.

## misma_familia

Las dos variables tienen la misma familia, salvo "otra" (que agrupa variables sin
familia propia y no es un aspecto común). Es descriptiva: no descarta pares (la relación mecánica se
marca solo con solapamiento_definicion). La familia tamaño define la escala.

## Categorías y fuerza

| Categoría | Criterio |
|---|---|
| control | `por_construccion = true` |
| insuficiente | `n < 30` |
| sin_relacion | IC95 completamente dentro de [−0,2; 0,2] |
| positiva / negativa | `p_fdr < 0,05` |
| no_concluyente | resto |

Fuerza: débil [0.1,0.3), moderada [0.3,0.5), fuerte ≥ 0.5.

## Chequeos de sensibilidad

| Columna | Qué calcula |
|---|---|
| `rho_corregida_sin_cortas` | La correlación corregida sin las ventanas de menos de 1 día |
| `depende_ventanas_cortas` | \|rho_corregida\| ≥ 0,1 y, sin las ventanas cortas, cambia de signo o baja de 0,1 |
| `rho_corregida_local` | La correlación corregida con una tendencia local: spline con un grado de libertad cada ~21 releases (`df_tendencia_local`) |
| `escala_relacion` | Solo pares significativos. "release a release" si con la tendencia local mantiene el signo, \|rho\| ≥ 0,1 y su IC95 no incluye el 0; si no, "cambio de etapa" |
| `ic_AAAA_AAAA`, `estado_AAAA_AAAA` | Por período, IC95 de la correlación corregida y estado: `+` / `-` si \|rho\| ≥ 0,1 y el IC95 no incluye el 0, `0` si no, vacío si no es evaluable |
| `alcance_temporal` | Toda la historia, desde AAAA, solo AAAA-AAAA, intermitente, cambia de signo o sin relación en ningún período |
| `anio_desde`, `anio_hasta` | Años que cubren las ventanas del par (los pares con CFDR / NUB empiezan en 2019–2020) |

## estable, robusta y robusta_tamano

`estable` = al menos 3 períodos evaluables y el mismo signo que rho_corregida en todos.
`robusta` = positiva|negativa AND estable AND rho_canary mismo signo (o vacío)
AND NOT depende_ventanas_cortas.
`robusta_tamano` = robusta AND |rho_corregida_tamano| ≥ 0,1 AND mismo signo
(vacío si el control por tamaño no aplica).

## hallazgo_candidato y nivel_evidencia

`hallazgo_candidato` = robusta AND NOT solapamiento_definicion
AND (resiste el control por tamaño, o el control no aplica) AND ninguna de las dos
variables es de la familia tamaño.

`relacion_tamano` = cumple todo lo anterior salvo la última condición: el par incluye una
variable de la familia tamaño, a la que no se le puede aplicar el control por tamaño. Es
la categoría "escala" de cruces.py: se informa aparte y no cuenta como hallazgo,
dentro de cada dimensión y entre dimensiones. Dentro de Persona describe cómo cambia el
equipo cuando crece o se achica; entre dimensiones no es evidencia de relación.

`nivel_evidencia` (hallazgos y relaciones con el tamaño): **alta** si `alcance_temporal` = toda la historia y
`escala_relacion` = release a release; **baja** si no tiene fuerza en ningún período o
es un cambio de etapa; **media** en el resto.

`motivo_descarte` lista por qué un par no es hallazgo ("escala (variable de tamaño)" en
las relaciones con el tamaño).

## Unión en Looker

`pares_correlacion.par_id = pares_valores.par_id`.
