# 10 – Mean Time to Repair / Mean Time to Failure / Mean Time Between Failures (MTTR / MTTF / MTBF)

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                |
|---|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 52 - La utilización eficiente de recursos                                                                                                                                  |
| **Métrica Original (ISL)** | CPU Usage                                                                                                                                      |
| **Métricas Adoptadas** | MTTR (Tiempo Medio de Reparación), MTTF (Tiempo Medio de Falla), MTBF (Tiempo Medio entre Fallas)                                                                          |
| **Dimensiones Asociadas** | Proceso, Producto                                                                                                                                                          |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

El **catálogo canónico de 2022** no contiene una métrica explícita de *uso de recursos computacionales* (CPU Usage, Processor Utilization, etc.), ya que este tipo de indicador requiere instrumentación en tiempo de ejecución que excede el alcance de la metadata típicamente disponible en el historial de un repositorio.

Las métricas más cercanas disponibles y **calculables** a partir de los datos existentes son **MTTR, MTTF y MTBF**, ya que:

- Se obtienen directamente de las **marcas de tiempo (timestamps)** de reporte y resolución de incidentes, sin requerir instrumentación adicional.
- Reflejan la **eficiencia operativa del equipo** ante fallas, más que el consumo de recursos de cómputo en sí.

> **Conclusión de la sustitución:** MTTR/MTTF/MTBF se adoptan como *proxy* de CPU Usage, priorizando la eficiencia y confiabilidad del proceso de resolución de incidentes sobre la medición directa del consumo de recursos. 

---

## 2. Definición de las Métricas

| Métrica | Qué mide |
|---|---|
| **MTTR** (Mean Time to Repair) | El tiempo promedio que transcurre entre que se detecta/reporta un incidente y el momento en que queda resuelto. |
| **MTTF** (Mean Time to Failure) | El tiempo promedio que un componente o sistema opera correctamente antes de que ocurra una falla. |
| **MTBF** (Mean Time Between Failures) | El tiempo promedio que transcurre entre una falla y la siguiente. |

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Proceso** | Miden la capacidad de respuesta y eficiencia del equipo frente a incidentes dentro del flujo de trabajo operativo. |
| **Producto** | Reflejan indirectamente la confiabilidad y estabilidad del sistema/software analizado. |

### 2.2 Fundamento

Las tres métricas se derivan de pares de timestamps (creación/detección y cierre/resolución) registrados en la metadata de incidentes, lo cual permite calcularlas sin necesidad de monitoreo en tiempo real de recursos de hardware.

---

## 3. Cálculo

De las tres métricas, se dispone del cálculo detallado para **MTTR**; MTTF y MTBF siguen una lógica análoga mediante otros pares de timestamps.

### 3.1 MTTR — Entradas

| Entrada | Qué representa |
|---|---|
| **Colección de incidencias** | Un listado de incidencias, cada una con su timestamp de **creación** (detección) y su timestamp de **cierre** (reparación), ambos como objetos de fecha/hora. |

### 3.2 MTTR — Lógica del proceso

El cálculo recorre cada incidencia de la colección y obtiene la duración entre su creación y su cierre (es decir, cuánto tardó en repararse). Esas duraciones individuales se acumulan en un total.

Al finalizar el recorrido, ese total se divide por la cantidad de incidencias resueltas, obteniendo así el **tiempo promedio de reparación**, expresado en horas.

Si no hay incidencias resueltas en la colección, el cálculo no puede realizarse y el resultado se define como cero para evitar una división inválida.

### 3.3 MTTR — Salida

| Salida | Qué representa |
|---|---|
| **Tiempo promedio de reparación (horas)** | Un número que indica, en promedio, cuántas horas transcurren entre que se detecta una incidencia y se resuelve. |

### 3.4 MTTF y MTBF — Lógica análoga

- **MTTF** se calcularía de forma equivalente, pero usando el par de timestamps *puesta en funcionamiento → primera falla* de cada componente, en lugar de *creación → cierre* de una incidencia.
- **MTBF** se calcularía usando los timestamps de **fallas consecutivas** de un mismo componente/sistema, promediando el intervalo entre una falla y la siguiente.

En los tres casos, la métrica funciona como un promedio: suma duraciones individuales entre dos eventos de interés y divide ese total por la cantidad de casos, obteniendo un tiempo promedio expresado en horas.

---

## 4. Salida Obtenida

**Resultado de la última ejecución:** `0`

Este valor se debe a que el repositorio tldr de entrada no contiene issues reales.
