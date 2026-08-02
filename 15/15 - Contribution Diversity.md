# 15 – Contribution Diversity

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 15 - La capacidad de aprender nuevas habilidades técnicas |
| **Métrica Original (ISL)** | Contribution Diversity (alt.: Multi-project Contribution) |
| **Métrica Canónica JAIIO 2022** | — |
| **Métrica Adoptada / Calculable** | Contribution Diversity (Diversidad de Contribución) |
| **Dimensiones Asociadas** | Persona, Proceso |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

> **Nota de implementación:** el archivo de código se llama `cdiv.py` (no `cd.py`) para evitar colisión de módulo con "Comment Density" (`16/cd.py`), ya utilizado en `run.py` para otra métrica del catálogo.

---

## 1. Observación

Contribution Diversity es la métrica original (ISL) asociada a esta consigna. Se vincula conceptualmente con la versatilidad técnica mencionada en el Mapeo Sistemático, aunque su operacionalización matemática efectivamente calculable se deriva de metadatos de autores y archivos del repositorio, no de un cruce entre proyectos.

---

## 2. Definición de la Métrica

**Contribution Diversity (CDIV)** mide la versatilidad de un desarrollador según la dispersión de sus cambios en el árbol de archivos (componentes) del repositorio: cuántos archivos distintos ha tocado.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Persona** | Mide la versatilidad individual de un desarrollador. |
| **Proceso** | Se deriva del historial de commits (metadatos de contribución) del repositorio. |

### 2.2 Fundamento Teórico

Un desarrollador con alta diversidad de contribución ha demostrado capacidad de trabajar sobre partes heterogéneas del sistema, lo cual es un indicador indirecto de su capacidad de aprender nuevas habilidades técnicas ante desafíos diversos.

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **historial_commits_usuario** | Lista de commits del autor, cada uno con la lista de archivos (`files`) modificados. |

### 3.2 Lógica del proceso

```python
def calcular_contribution_diversity(historial_commits_usuario):
    componentes_unicos = set()
    for commit in historial_commits_usuario:
        componentes_unicos.update(commit['files'])
    return len(componentes_unicos)
```

### 3.3 Implementación sobre GitHub

`metrics/15/cdiv.py` descarga los commits del período y el detalle de archivos de cada uno (`/commits/{sha}`), agrupa por autor y aplica `calcular_contribution_diversity` sobre el historial de cada colaborador.

- **`por_persona`**: cantidad de archivos únicos tocados por cada colaborador.
- **`por_producto`**: no aplica (métrica exclusivamente de Persona/Proceso).

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **CDIV** | Entero ≥ 0. Cantidad de archivos distintos que el desarrollador modificó en el período analizado. Valores altos indican contribuciones dispersas por el repositorio; valores bajos, foco en pocos archivos/componentes. |

---

## 4. Salida Obtenida

**Repositorio analizado:** calidad-software-tg/tldr (muestra de 15 commits, ventana de 3 años)

| Colaborador | CDIV (archivos únicos) |
|---|---|
| nelsonfigueroa | 98 |
| Ninzero | 7 |
| Turmaxx | 3 |
| Managor | 2 |
| IMHOJEONG | 2 |
| acuteenvy | 1 |
| dmmqz | 1 |
| kant | 1 |

> Corrida de validación con `max_commits=15`. `nelsonfigueroa` destaca por un commit masivo que tocó múltiples archivos (p. ej. una actualización en lote de páginas del repositorio).

---

## 5. Referencias

- Métrica original ISL de la consigna 15: Contribution Diversity / Multi-project Contribution.
