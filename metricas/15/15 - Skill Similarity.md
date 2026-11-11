# 15 – Skill Similarity

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 15 - La capacidad de aprender nuevas habilidades técnicas |
| **Métrica Original (ISL)** | Contribution Diversity (alt.: Multi-project Contribution) |
| **Métrica Canónica JAIIO 2022** | — |
| **Métrica Adoptada / Calculable** | Skill Similarity |
| **Dimensiones Asociadas** | Persona |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

Se identifica en el estudio sobre "Equipos Quirúrgicos", donde se utiliza para medir la afinidad técnica entre desarrolladores y repositorios en base a los lenguajes de programación dominados. Aporta a la consigna de "capacidad de aprender" midiendo cuánta base técnica previa tiene el desarrollador respecto del stack del repositorio (a menor solapamiento, mayor esfuerzo de aprendizaje requerido).

---

## 2. Definición de la Métrica

**Skill Similarity (SS)** mide el grado de solapamiento entre los lenguajes de programación dominados por un autor (según sus propios repositorios) y los lenguajes que componen el repositorio objetivo.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Persona** | Mide la afinidad técnica individual de un desarrollador respecto del proyecto. |

### 2.2 Fundamento Teórico

Utilizada en el estudio de "Equipos Quirúrgicos" para medir la adecuación técnica previa de un desarrollador frente al stack de un repositorio, como predictor de la probabilidad de introducir defectos durante el onboarding.

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **user_languages** | Conjunto de lenguajes dominados por el usuario, identificados por sus contribuciones en otros proyectos. |
| **repo_languages** | Conjunto de lenguajes que componen el repositorio objetivo, con una contribución mayor al 0.1% en bytes. |

### 3.2 Lógica del proceso

```python
def calcular_skill_similarity(user_languages, repo_languages):
    if not repo_languages:
        return 0
    habilidades_comunes = user_languages.intersection(repo_languages)
    return len(habilidades_comunes) / len(repo_languages)
```

### 3.3 Implementación sobre GitHub

`metrics/15/ss.py` obtiene `repo_languages` desde `/repos/{org}/{repo}/languages` (filtrando por >0.1% del total de bytes). Para cada colaborador (`/repos/{org}/{repo}/contributors`) obtiene sus repositorios propios (`/users/{login}/repos`) y toma el lenguaje primario declarado de cada uno como aproximación de `user_languages`.

- **`por_persona`**: aplica `calcular_skill_similarity` por colaborador.
- **`por_producto`**: no aplica (métrica exclusivamente de Persona).

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **SS** | Ratio de 0 a 1: proporción de los lenguajes del repositorio que el desarrollador ya domina según su historial. 1 indica dominio completo del stack; 0, ninguna afinidad previa. |

---

## 4. Salida Obtenida

**Repositorio analizado:** calidad-software-tg/tldr — lenguajes del repo (>0.1%): `Markdown, Python, Shell`

| Colaborador | SS |
|---|---|
| Managor | 0.6667 |
| owenvoke | 0.6667 |
| kant | 0.3333 |
| sebastiaanspeck | 0.3333 |
| nelsonfigueroa | 0.3333 |

> Corrida de validación con `max_contributors=5`.

---

## 5. Referencias

- Estudio de "Equipos Quirúrgicos" — afinidad técnica autor–repositorio basada en lenguajes de programación.
