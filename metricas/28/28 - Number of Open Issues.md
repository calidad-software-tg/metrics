# 28 – Number of Open Issues

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                |
|---|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 43 - Cantidad de problemas (issues) abiertos en su repositorio                                                                                                             |
| **Métrica Original (ISL)** | Number of Open Issues                                                                                                                                                      |
| **Nombre Alternativo** | Open Bug Count                                                                                                                                                             |
| **Métrica Canónica JAIIO 2022** | Number of Open Issues                                                                                                                                                      |
| **Métrica Adoptada / Calculable** | Number of Open Issues (NOI)                                                                                                                                                |
| **Dimensiones Asociadas** | Producto, Proceso                                                                                                                                                          |
| **Fuente** | [Doc 1](https://docs.google.com/document/d/1Cqm_RJSD7IH2jpfB_3RXRqkfG4DOz46h/edit?rtpof=true) · [Doc 2](https://docs.google.com/document/d/1_AWD8cPFfUMymJvxRM0wy0QZLGThXbNP/edit) · [Evidencia](https://drive.google.com/file/d/1fMRgY71Hul3LNDwqw_97PLE-o1s_2Idn/view?usp=sharing) |

---

## 1. Observación

La consigna pide directamente la **cantidad de issues abiertos en el repositorio**. Es una **correspondencia directa**: la consigna utiliza prácticamente la misma definición que la métrica canónica del catálogo JAIIO 2022 ("Number of Open Issues"), sin necesidad de reinterpretación ni de buscar una métrica sustituta.

No se detectan discrepancias entre lo catalogado y lo efectivamente calculable (a diferencia de lo ocurrido con la métrica 20).

---

## 2. Definición de la Métrica

**Number of Open Issues (NOI)** cuantifica la cantidad de informes de errores o solicitudes de funciones (*issues*) que **no habían sido cerrados** en un momento determinado (*snapshot*) del repositorio.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Producto** | Refleja el estado de "deuda" de trabajo pendiente del repositorio como producto: cuántos problemas reportados siguen sin resolución. |
| **Proceso** | Es un indicador de la capacidad del equipo para procesar y dar de baja la carga de trabajo entrante (issue triage / resolución). |

No aplica a la dimensión **Persona**: la métrica no distingue autoría ni asigna el conteo a un desarrollador en particular, es un agregado a nivel repositorio.

### 2.2 Fundamento Teórico

Según **Jarczyk et al. (2018)**, el volumen de *open issues* tiende a crecer de forma casi inexorable debido a la acumulación de "problemas olvidados" (*issues* que quedan sin atención), lo cual afecta negativamente la percepción de calidad del proyecto y es un indicador de la efectividad de los procesos de desarrollo.

---

## 3. Cálculo

La función que implementa esta métrica recibe la colección de issues del repositorio y un instante de análisis (*snapshot*), y devuelve un número entero.

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **Metadata de issues del repositorio** | Lista de diccionarios obtenida de la API de GitHub (GraphQL) o GHTorrent. Cada elemento contiene: `number` (identificador del issue), `state` (`OPEN`/`CLOSED`), `created_at` (fecha de apertura) y `closed_at` (fecha de cierre, `None` si sigue abierto). |
| **fecha_snapshot** | Punto en el tiempo para el análisis. Si no se especifica, se usa el `fecha_fin` del período analizado (o la fecha actual). |

### 3.2 Lógica del proceso

Un issue se considera **abierto en el snapshot** si se cumplen ambas condiciones:

1. Fue creado antes o en la fecha del snapshot (`created_at <= fecha_snapshot`).
2. Sigue abierto (`closed_at is None`) **o** fue cerrado **después** de la fecha del snapshot (`closed_at > fecha_snapshot`).

Se cuenta la cantidad total de issues que cumplen esta condición.

### 3.3 Salida

| Salida | Qué representa |
|---|---|
| **Open Issues (NOI)** | Número entero: cantidad de issues que estaban en estado abierto en la fecha del snapshot analizado. |

En otras palabras: la métrica funciona como una **fotografía instantánea** del backlog de issues sin resolver del repositorio en un momento dado.

---

## 4. Salida Obtenida

**Repositorio analizado:** tldr-pages/tldr
**Período analizado:** 2025-08-07 → 2026-08-07
**Snapshot:** 2026-08-07T18:23:24 UTC (fecha_fin del período)

| Métrica | Valor |
|---|---|
| Issues totales obtenidos en el período | 1.788 |
| **Open Issues (NOI)** | **230** |

> El valor obtenido (230) coincide exactamente con el contador público de GitHub para `tldr-pages/tldr` en el momento de la corrida, lo que valida el cálculo.

### 4.1 Nota metodológica: fork vs. repositorio original

Durante la validación de esta métrica se corrió inicialmente contra **`calidad-software-tg/tldr`** (fork del equipo del repositorio original), obteniendo **0 issues y 0 PRs** en el período. Se verificó en GitHub que este fork tiene **0 contribuidores propios** y está **884 commits detrás** de `tldr-pages/tldr:main` — es decir, es una copia estática del código sin actividad de issues/PRs propia (los forks no heredan el historial de issues/PRs del repositorio original vía la API de GitHub salvo que se abran explícitamente contra el fork).

Se recomienda que todas las métricas del catálogo que dependan de issues o PRs (16, 18, 20, 23, 27, 28, 35, 40, 43, etc.) se calculen contra **`tldr-pages/tldr`** (el repositorio original) para evitar falsos negativos de este tipo y mantener resultados comparables entre todas las métricas del equipo.

---

## 5. Referencias

- Jarczyk, O. et al. (2018). Relación entre la acumulación de *open issues*, la percepción de calidad y la efectividad de los procesos de desarrollo.