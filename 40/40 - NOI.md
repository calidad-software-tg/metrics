# 40 – NOI (Number of Open Issues)

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 40 - La adhesión a las prácticas / políticas de desarrollo definidas |
| **Métrica Original (ISL)** | Process Compliance (alt.: Development Policy Adherence) |
| **Métrica Canónica JAIIO 2022** | Development Process Performance |
| **Métrica Adoptada / Calculable** | Process Performance (NOI) |
| **Dimensiones Asociadas** | Proceso |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1Ytxi7bWr0KWL9zzsFvR8J48LoaS86xH1/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

La planilla agrupa "Process Performance" en dos algoritmos complementarios: NOI (este archivo) y NCI (ver `40 - NCI (reutilizada).md`). Mientras NCI mide el **throughput** (cuánto se cierra), NOI mide la **acumulación** (cuánto queda pendiente) — juntas dan una foto más completa del manejo de la carga de trabajo del equipo.

---

## 2. Definición de la Métrica

**Number of Open Issues (NOI)** cuantifica la acumulación de tareas pendientes en el repositorio, en un momento puntual del tiempo (snapshot) — a diferencia de la mayoría de las otras métricas de este proyecto, no es un conteo sobre una ventana `[fecha_inicio, fecha_fin]`, sino una foto instantánea al final del período.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Proceso** | Refleja la capacidad del equipo para manejar la carga de trabajo activa del flujo de issues. |

### 2.2 Fundamento Teórico

Según Jarczyk et al. (2018), el volumen de open issues es un indicador de la carga de trabajo pendiente del equipo — un valor creciente en el tiempo puede señalar que el equipo no da abasto con el ritmo de reportes entrantes.

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **metadata_issues** | Lista de issues con `created_at` y `closed_at` (o `None` si sigue abierto). |
| **fecha_snapshot** | Punto en el tiempo del análisis. Si es `None`, usa "ahora". |

### 3.2 Lógica del proceso

```python
def calcular_open_issues(metadata_issues, fecha_snapshot=None):
    if fecha_snapshot is None:
        fecha_snapshot = datetime.datetime.now()
    total_open = 0
    for issue in metadata_issues:
        fecha_creacion = issue.get('created_at')
        fecha_cierre = issue.get('closed_at')
        if fecha_creacion and fecha_creacion <= fecha_snapshot:
            if fecha_cierre is None or fecha_cierre > fecha_snapshot:
                total_open += 1
    return total_open
```

Un issue cuenta como "abierto en el snapshot" si ya existía para esa fecha y, o nunca se cerró, o se cerró después del snapshot (es decir, estaba abierto en ese momento del tiempo, sin importar si se cerró más adelante).

### 3.3 Implementación sobre GitHub

`metrics/40/noi.py` descarga todos los issues vía GraphQL paginado (mismo patrón que Development Process Performance) y aplica `calcular_open_issues` usando `fecha_fin` del período como snapshot.

- **`por_producto`**: NOI del repositorio al cierre del período (`fecha_fin`).
- **`por_persona`**: **no aplica** (`NotImplementedError`) — el algoritmo no atribuye issues abiertos a un desarrollador.

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **NOI** | Entero ≥ 0. Cantidad de issues abiertos en el repositorio al momento del snapshot. |

---

## 4. Salida Obtenida

**Repositorio configurado en `.env`:** `calidad-software-tg/tldr` — sin issues.

**Corrida completa contra `tldr-pages/tldr`** (snapshot al 2026-07-31):

**NOI (Number of Open Issues): 230**

> Sobre 1.786 issues totales evaluados en la corrida de Development Process Performance, 230 seguían abiertos al momento del snapshot — consistente con el 78% de performance a 365 días (≈22% no resuelto dentro del año, más los issues recientes que todavía no cumplieron ese plazo).

---

## 5. Referencias

- Jarczyk, O. et al. (2018). Volumen de open issues como indicador de carga de trabajo pendiente del equipo.
