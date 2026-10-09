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

### Corrección por tamaño (rho_corregida_tamano)

Para pares con al menos una variable de Persona (excluye familia tamano):
misma correlación parcial controlando además por `rank(log(activos_interaccion+1))`.
K_controles = 6; gl = `n_ef − 8`.

## Benjamini-Hochberg (p_fdr)

Dentro de cada cruce, solo pares con `por_construccion = false`.

## Pares por_construccion

misma_metrica; activos ↔ nuevos del mismo canal; activos_comentarios/cierre ↔
activos_interaccion; proporciones ↔ sus dos componentes (numerador y denominador);
nc/sc/nci ↔ exprev.

## Categorías y fuerza

| Categoría | Criterio |
|---|---|
| control | `por_construccion = true` |
| insuficiente | `n < 30` |
| sin_relacion | IC95 completamente dentro de [−0,2; 0,2] |
| positiva / negativa | `p_fdr < 0,05` |
| no_concluyente | resto |

Fuerza: débil [0.1,0.3), moderada [0.3,0.5), fuerte ≥ 0.5.

## robusta y robusta_tamano

`robusta` = positiva|negativa AND estable AND rho_canary mismo signo (o vacío).
`robusta_tamano` = robusta AND |rho_corregida_tamano| ≥ 0,1 AND mismo signo.

## Unión en Looker

`pares_correlacion.par_id = pares_valores.par_id`.

## Cómo reproducir

### Orden de ejecución

1. `export_persona.py` — exporta ventanas de métricas persona desde la DB a `persona_detalle_estable.csv`
2. `resolver_y_unificar.py` — resuelve identidades y genera `persona_agregado_estable_canary.csv`
3. `analisis/generar_diccionario.py` → `analisis/salidas/diccionario_variables.csv`
4. `analisis/generar_correlaciones.py` → `pares_correlacion.csv`, `pares_valores.csv`, `revision_persona.csv`

### Librerías Python requeridas

`numpy`, `scipy`, `psycopg2`

### Fuente de datos

Los datos provienen del seed de la rama `luz/bugs-tipo-issue` en la DB `resultados_metricas`
(container Docker `tg_metricas_db`, puerto 5432). Las métricas persona se leen
de `persona_agregado_estable_canary.csv` (generado por los pasos 1–2).

### pares_valores.csv

El archivo `pares_valores.csv` (~85 MB) **no está en el repositorio**.
Se regenera ejecutando los pasos 3–4, o se descarga desde el Drive del equipo.
