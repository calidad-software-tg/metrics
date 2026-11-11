# 15 – FEXP (Experiencia en Archivos)

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 15 - La capacidad de aprender nuevas habilidades técnicas |
| **Métrica Original (ISL)** | Contribution Diversity (alt.: Multi-project Contribution) |
| **Métrica Canónica JAIIO 2022** | — |
| **Métrica Adoptada / Calculable** | FEXP (Experiencia en Archivos) |
| **Dimensiones Asociadas** | Persona |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

FEXP mide la experiencia local del autor sobre los archivos específicos que modifica en cada commit, en lugar de su experiencia general en el repositorio. Es un indicador de "cuánto conoce" el desarrollador de las partes puntuales del código que está tocando, relevante para evaluar su capacidad de incorporar nuevas habilidades sobre componentes ya conocidos vs. desconocidos.

---

## 2. Definición de la Métrica

**FEXP** suma, para cada archivo modificado en un commit, la cantidad de commits previos que el mismo autor ya había realizado sobre ese archivo.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Persona** | Mide la experticia local acumulada de un desarrollador específico sobre archivos puntuales. |

### 2.2 Fundamento Teórico

Permite controlar el sesgo de la experticia local sobre componentes críticos, en lugar de depender únicamente de la experiencia general del desarrollador (REXP/EXP).

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **commit_actual** | Diccionario con `files` (rutas modificadas) y `timestamp` del commit evaluado. |
| **historial_commits_usuario** | Lista de commits previos del mismo autor, cada uno con `files` y `timestamp`. |

### 3.2 Lógica del proceso

```python
def calcular_fexp(commit_actual, historial_commits_usuario):
    fexp_total = 0
    archivos_objetivo = commit_actual['files']
    ts_actual = commit_actual['timestamp']
    for archivo in archivos_objetivo:
        conteo_previo = sum(1 for c in historial_commits_usuario
                             if archivo in c['files'] and c['timestamp'] < ts_actual)
        fexp_total += conteo_previo
    return fexp_total
```

### 3.3 Implementación sobre GitHub

`metrics/15/fexp.py` descarga los commits del período y, para cada uno, su detalle (`/commits/{sha}`) con la lista de archivos modificados. Por cada autor, ordena sus commits cronológicamente y calcula `calcular_fexp` de cada commit contra el historial estrictamente anterior del mismo autor.

- **`por_persona`**: FEXP promedio por commit de cada colaborador.
- **`por_producto`**: no aplica (métrica exclusivamente de Persona).

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **FEXP (promedio)** | Cuántas veces, en promedio, el autor ya había tocado antes cada archivo que modifica. Valores altos indican alta familiaridad con los archivos que toca; valores cercanos a 0 indican que suele trabajar sobre archivos nuevos para él. |

---

## 4. Salida Obtenida

**Repositorio analizado:** calidad-software-tg/tldr (muestra de 15 commits, ventana de 3 años)

| Colaborador | FEXP (promedio por commit) |
|---|---|
| Managor | 0.0 |
| nelsonfigueroa | 0.0 |
| Turmaxx | 0.0 |
| Ninzero | 0.0 |
| acuteenvy | 0.0 |
| dmmqz | 0.0 |
| IMHOJEONG | 0.0 |
| kant | 0.0 |

> Corrida de validación con `max_commits=15`. Todos en 0 porque, en esta muestra reducida, ningún autor repitió archivo entre sus propios commits. Con una ventana de commits mayor se esperan valores > 0 en archivos "core" tocados recurrentemente por los mismos autores.

---

## 5. Referencias

- Definición de FEXP como suma de commits previos del autor sobre cada archivo de una contribución (indicador de experticia local).
