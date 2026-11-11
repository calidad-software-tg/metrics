# 40 – NCI (Number of Closed Issues)

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 40 - La adhesión a las prácticas / políticas de desarrollo definidas |
| **Métrica Original (ISL)** | Process Compliance (alt.: Development Policy Adherence) |
| **Métrica Canónica JAIIO 2022** | Development Process Performance |
| **Métrica Adoptada / Calculable** | Process Performance (NCI) |
| **Dimensiones Asociadas** | Proceso |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1Ytxi7bWr0KWL9zzsFvR8J48LoaS86xH1/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## ⚠️ Métrica reutilizada, no reimplementada

**Esta métrica ya está implementada** en `metrics/35/nci.py` bajo la clase `NumberOfClosedIssues`, documentada en `metrics/35/35 - Number of clossed issues.md`.

El algoritmo provisto en **esta** planilla (consigna 40) para "NCI" es la misma lógica:

```python
def calcular_number_of_closed_issues(metadata_issues, fecha_inicio, fecha_fin):
    total_cerrados = 0
    for issue in metadata_issues:
        fecha_clausura = issue.get('closed_at')
        if fecha_clausura and fecha_inicio <= fecha_clausura <= fecha_fin:
            total_cerrados += 1
    return total_cerrados
```

Que coincide exactamente con la lógica de `por_producto` de `35/nci.py`:

```python
def por_producto(self, fecha_inicio, fecha_fin):
    return sum(
        1 for issue in self.issues
        if issue["closed_at"] and fecha_inicio <= issue["closed_at"] <= fecha_fin
    )
```

Ambas consignas (35 "Number of closed issues" y 40 "adhesión a prácticas/políticas de desarrollo") citan la misma operacionalización — throughput de cierre de issues — como métrica calculable.

### Decisión

`metrics/40/nci_reuse.py` reexporta la clase ya existente en vez de duplicar el fetch por GraphQL, la paginación y la lógica de conteo:

```python
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "35"))
from nci import NumberOfClosedIssues
```

`run.py` la expone bajo la clave `"nci_process"` (para distinguirla de `"nci"`, la de la consigna 35), pero ambas ejecutan literalmente la misma clase — validado en código: `NumberOfClosedIssues is NumberOfClosedIssuesProcess` da `True`.

### Para el análisis de la tesis

El valor de NCI para la consigna 40 **es el mismo número** que el de la consigna 35 — no hace falta correrla dos veces. Ver `metrics/35/35 - Number of clossed issues.md` para la ficha técnica y valores de referencia ya calculados.

**Validado contra `tldr-pages/tldr`** (ventana de 90 días): NCI = 53 issues cerrados.

---

## Referencias

- Vasilescu, B. et al. (2015). Throughput de cierre de issues como indicador de productividad.
- Ver también: `metrics/35/35 - Number of clossed issues.md` (ficha técnica completa de la métrica).
