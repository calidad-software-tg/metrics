# 43 – NCI (Number of Closed Issues)

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 43 - El tiempo promedio de resolución de problemas |
| **Métrica Original (ISL)** | Average Problem Resolution Time (alt.: Mean Time To Resolve Problems) |
| **Métrica Canónica JAIIO 2022** | Number of Closed Issues |
| **Métrica Adoptada / Calculable** | Number of Closed Issues (NCI) |
| **Dimensiones Asociadas** | Proceso |
| **Fuente** | [Documento de referencia (Google Drive)](https://drive.google.com/file/d/1fMRgY71Hul3LNDwqw_97PLE-o1s_2Idn/view?usp=sharing) |

---

## 1. Observación

La consigna pide tiempo promedio de resolución de problemas, pero **el catálogo canónico de 209 métricas no contiene una métrica explícita de tiempo de resolución** (Mean Resolution Time, Issue Resolution Time, etc.). La más cercana calculable es Number of Closed Issues: refleja capacidad de resolución, pero **no incorpora la dimensión temporal** que pide la consigna original — limitación explícita documentada en la planilla.

## ⚠️ Métrica reutilizada, no reimplementada

Esta es la **tercera** planilla del catálogo que llega a la misma operacionalización (throughput de cierre de issues), después de las consignas 35 (donde está la implementación original) y 40. El algoritmo `calcular_nci(metadata_issues, fecha_inicio, fecha_fin)` de esta planilla es idéntico en lógica a `por_producto` de `metrics/35/nci.py`.

`metrics/43/nci_reuse_43.py` reexporta la misma clase:

```python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "35"))
from nci import NumberOfClosedIssues
```

> Nota de nombres: como la consigna 40 ya tiene su propio wrapper llamado `nci_reuse.py`, este archivo se llamó `nci_reuse_43.py` para evitar que Python confunda los dos módulos (ambas carpetas quedan en `sys.path` a la vez en `run.py`, y un mismo nombre de archivo pisaría al otro). Verificado en código: `NumberOfClosedIssues` (35), la reexportada en 40, y la reexportada en 43 son literalmente el mismo objeto de clase (`is` → `True` las tres).

`run.py` la expone bajo la clave `"nci_resolution_time"`.

### Para el análisis de la tesis

El valor de NCI es el mismo para las tres consignas (35, 40, 43) — no hace falta correrlo tres veces. Ver `metrics/35/35 - Number of clossed issues.md` para la ficha técnica y valores de referencia.

---

## Referencias

- Jarczyk, O. et al. (2014, 2018). Cierre de problemas como indicador crítico de la calidad del soporte técnico.
- Ver también: `metrics/35/35 - Number of clossed issues.md`, `metrics/40/40 - NCI (reutilizada).md`.
