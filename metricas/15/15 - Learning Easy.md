# 15 – Learning Easy

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 15 - La capacidad de aprender nuevas habilidades técnicas |
| **Métrica Original (ISL)** | Contribution Diversity (alt.: Multi-project Contribution) |
| **Métrica Canónica JAIIO 2022** | — |
| **Métrica Adoptada / Calculable** | Learning Easy |
| **Dimensiones Asociadas** | Producto, Persona |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true) |

---

## 1. Observación

La consigna original refiere a la **capacidad de aprender nuevas habilidades técnicas**. Dentro del Mapeo Sistemático (SM) sobre calidad de producto se identificó **Learning Easy (Aprendizaje Fácil)** como la operacionalización más directa: el tiempo que le toma a un desarrollador dominar un componente del sistema.

---

## 2. Definición de la Métrica

**Learning Easy (LE)** aproxima la curva de aprendizaje de un desarrollador sobre un componente del repositorio, midiendo el intervalo (en días) entre su primera y su última contribución a ese componente.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Producto** | El "componente" es una unidad estructural del producto (se aproxima como el primer segmento de la ruta del archivo). |
| **Persona** | El tiempo de dominio se mide por autor: cada desarrollador tiene su propia curva de aprendizaje sobre cada componente. |

### 2.2 Fundamento Teórico

Proviene del Mapeo Sistemático (SM) sobre calidad de producto, donde se define como el tiempo promedio que un desarrollador necesita para dejar de introducir defectos recurrentes en un componente, es decir, para "dominarlo".

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **commits_componente** | Lista de commits (con su `timestamp`) que un autor realizó sobre un componente específico del repositorio. |

### 3.2 Lógica del proceso

Se toman los timestamps de todos los commits del autor sobre el componente y se calcula la diferencia en días entre el más reciente y el más antiguo.

```python
def calcular_learning_easy(commits_componente):
    if not commits_componente:
        return 0
    timestamps = [c['timestamp'] for c in commits_componente]
    delta = max(timestamps) - min(timestamps)
    return delta.days
```

### 3.3 Implementación sobre GitHub

`metrics/15/le.py` descarga los commits del período (`/repos/{org}/{repo}/commits`) y, para cada uno, su detalle (`/commits/{sha}`) con la lista de archivos modificados. El **componente** se aproxima como el primer segmento de la ruta de cada archivo (p. ej. `src/utils/foo.py` → `src`). Se agrupan los registros por `(autor, componente)` y se aplica `calcular_learning_easy` a cada grupo.

- **`por_persona`**: promedio de LE entre todos los componentes que tocó cada autor.
- **`por_producto`**: promedio de LE entre todos los componentes del repositorio, sin distinguir autor.

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **LE (días)** | Tiempo promedio, en días, que un desarrollador tarda entre su primera y última contribución a un componente. Valores bajos sugieren componentes de aprendizaje rápido o baja actividad reciente; valores altos, mayor curva de aprendizaje o presencia sostenida en el componente. |

---

## 4. Salida Obtenida

**Repositorio analizado:** calidad-software-tg/tldr (muestra de 15 commits, ventana de 3 años)

| Colaborador | LE (días, promedio por componente) |
|---|---|
| Managor | 0.0 |
| Turmaxx | 0.0 |
| Ninzero | 0.0 |
| acuteenvy | 0.0 |
| dmmqz | 0.0 |
| IMHOJEONG | 0.0 |
| kant | 0.0 |
| nelsonfigueroa | 0.5 |

> Corrida de validación con `max_commits=15` (muestra reducida para no agotar la cuota de la API). Con la mayoría de los autores en 0 días porque, en esta muestra acotada, cada componente fue tocado una sola vez por commit. Para valores representativos se recomienda correr con `max_commits` elevado (o sin tope) sobre el período completo de análisis.

---

## 5. Referencias

- Mapeo Sistemático (SM) sobre calidad de producto — definición de Learning Easy como tiempo de dominio de un componente.
