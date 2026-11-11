# 15 – REXP (Experiencia Reciente)

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 15 - La capacidad de aprender nuevas habilidades técnicas |
| **Métrica Original (ISL)** | Contribution Diversity (alt.: Multi-project Contribution) |
| **Métrica Canónica JAIIO 2022** | — |
| **Métrica Adoptada / Calculable** | REXP (Experiencia Reciente) |
| **Dimensiones Asociadas** | Persona |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

REXP pondera la experiencia acumulada (EXP) de un desarrollador por la antigüedad de sus contribuciones, dando más peso a lo reciente. En el marco de "capacidad de aprender", permite distinguir entre un desarrollador con experiencia vigente y uno con conocimiento históricamente alto pero desactualizado.

---

## 2. Definición de la Métrica

**REXP** es la experiencia reciente de un desarrollador, calculada como la suma de contribuciones ponderadas por un factor de decaimiento temporal (a mayor antigüedad, menor peso).

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Persona** | Mide la vigencia del conocimiento técnico de un desarrollador específico. |

### 2.2 Fundamento Teórico

Otorga mayor peso a las habilidades técnicas aplicadas recientemente, bajo la premisa de que el conocimiento reciente es más valioso que el histórico para predecir la calidad de las contribuciones actuales.

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **user_commits** | Lista de commits del desarrollador, cada uno con su fecha (`date`). |
| **fecha_actual** | Fecha de referencia respecto de la cual se calcula la antigüedad. |

### 3.2 Lógica del proceso

```python
def calcular_rexp(user_commits, fecha_actual):
    rexp_total = 0
    for commit in user_commits:
        dias_antiguedad = (fecha_actual - commit['date']).days
        rexp_total += 1 / (dias_antiguedad + 1)
    return rexp_total
```

### 3.3 Implementación sobre GitHub

`metrics/15/rexp.py` descarga los commits del período (`/repos/{org}/{repo}/commits`, paginado) con autor y fecha, los agrupa por colaborador y aplica `calcular_rexp` usando `fecha_fin` del período de análisis como `fecha_actual`.

- **`por_persona`**: REXP por colaborador.
- **`por_producto`**: no aplica (métrica exclusivamente de Persona).

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **REXP** | Número real ≥ 0. A mayor valor, mayor cantidad de contribuciones recientes del desarrollador. Un commit del mismo día suma ~1; uno de hace un año suma ~0.003. |

---

## 4. Salida Obtenida

**Repositorio analizado:** calidad-software-tg/tldr (ventana de 3 años, 200 commits)

| Colaborador | REXP |
|---|---|
| nelsonfigueroa | 0.4032 |
| IMHOJEONG | 0.3109 |
| Managor | 0.2592 |
| kant | 0.1922 |
| Ninzero | 0.1872 |
| acuteenvy | 0.1557 |
| ivanbaluta | 0.0616 |
| reinhart1010 | 0.0606 |
| ... | ... |

> Tabla completa disponible al correr `rexp.py` sin recorte de salida. `fecha_actual` = fecha de fin del período consultado.

---

## 5. Referencias

- REXP como versión ponderada temporalmente de EXP (Experience), consistente con el uso de REXPRev en experiencia de revisión.
