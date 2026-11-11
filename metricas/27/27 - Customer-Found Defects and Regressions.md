# 27 – Customer-Found Defects and Regressions (CFDR)

## Ficha Técnica

| Campo | Descripción |
|---|---|
| **Consigna** | 27 - La calidad de las soluciones implementadas |
| **Métrica Original (ISL)** | Quality of implemented fixes / Solution Quality (alt.: Quality of implemented solutions) |
| **Métrica Canónica JAIIO 2022** | Customer-Found Defects and Regressions |
| **Métrica Adoptada / Calculable** | Customer-Found Defects and Regressions (CFDR) |
| **Dimensiones Asociadas** | Producto, Proceso |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1j3ZvlK5q1byPKS3yKbnIIJvl8cylpSC7/edit?usp=sharing&ouid=117949578369504995298&rtpof=true&sd=true), Rashid, J., Mahmood, T., & Nisar, M. W. — *A Study on Software Metrics and its Impact on Software Quality* |

---

## 1. Observación

La consigna original refiere a la calidad de las soluciones implementadas. CFDR complementa esa evaluación desde la perspectiva de los defectos observados por **usuarios externos** una vez implementada la solución — es decir, no mide si el fix funcionó bien en revisión interna, sino si terminó generando (o dejando pasar) errores visibles para quien usa el software en producción.

---

## 2. Definición de la Métrica

**Customer-Found Defects and Regressions (CFDR)** cuantifica el volumen de errores y regresiones (fallas en funcionalidades que antes andaban bien) reportados por usuarios externos al equipo principal, tras una liberación.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Producto** | Mide la calidad del software entregado, desde afuera hacia adentro (perspectiva del usuario final). |
| **Proceso** | Se deriva del flujo de reporte y etiquetado de issues del repositorio. |

### 2.2 Fundamento Teórico

Un valor alto sugiere una baja **DRE (Defect Removal Efficiency)** previa al lanzamiento: el equipo no detectó esos defectos antes de que llegaran a producción y los tuvo que descubrir el usuario. Se excluyen explícitamente los reportes hechos por miembros del equipo principal para evitar el sesgo de "internal testing" (un bug encontrado por el propio equipo en QA no es lo mismo que uno encontrado por un cliente real).

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **metadata_issues** | Lista de issues, cada uno con `user_login` (informante), `labels` (etiquetas) y `created_at`. |
| **lista_core_team** | Set de logins del equipo principal / contribuyentes frecuentes ("Surgical Team"). |

### 3.2 Lógica del proceso

```python
def calcular_customer_defects_and_regressions(metadata_issues, lista_core_team):
    keywords_error = {'bug', 'defect', 'error', 'fault', 'flaw', 'regression'}
    conteo_customer_defects = 0
    for issue in metadata_issues:
        reportero = issue.get('user_login')
        etiquetas = {et.lower() for et in issue.get('labels', [])}
        es_defecto = any(key in etiquetas for key in keywords_error)
        es_externo = reportero not in lista_core_team
        if es_defecto and es_externo:
            conteo_customer_defects += 1
    return conteo_customer_defects
```

### 3.3 Implementación sobre GitHub

`metrics/27/cfdr.py`:

1. **Core team**: se aproxima con los primeros N colaboradores del endpoint `/repos/{org}/{repo}/contributors` (ordenado por cantidad de commits, que es el orden que ya devuelve GitHub), tomando el top-`core_team_size` (default 10) como proxy del equipo principal / "Surgical Team".
2. **Issues**: se descargan vía GraphQL (paginado, `issues(first: 50, after: $after)`), trayendo `author.login`, `createdAt` y `labels`.
3. Se filtran los issues del período y se aplica `calcular_customer_defects_and_regressions` literalmente.

- **`por_producto`**: CFDR total del repositorio en el período — un único número.
- **`por_persona`**: **no aplica**. El conteo es a nivel repositorio y, por definición, excluye a los desarrolladores del equipo (son el grupo que se filtra del cálculo, no el sujeto de medición). `por_persona` tira `NotImplementedError`.

### 3.4 Salida

| Salida | Qué representa |
|---|---|
| **CFDR** | Entero ≥ 0. Cantidad de issues etiquetados como bug/defecto/regresión, reportados por usuarios fuera del core team, en el período analizado. |

---

## 4. Salida Obtenida

**Repositorio configurado en `.env`:** `calidad-software-tg/tldr` — sin issues (mismo fork sin actividad de discusión que afecta a NC, EXPRev, REXPRev y Discussion Centrality).

**Corrida completa contra `tldr-pages/tldr`** (repositorio original, ventana de 15 años, 1.750 issues descargados):

**Core team detectado (top 10 por commits):** `IMHOJEONG, Managor, ikks, kant, marchersimon, nelsonfigueroa, owenvoke, sbrl, sebastiaanspeck, waldyrious`

**CFDR (Customer-Found Defects and Regressions): 44**

> De 1.750 issues totales, 44 cumplen ambos criterios: etiquetados como `bug` (u otra keyword de error) y reportados por alguien fuera del top-10 de colaboradores. La gran mayoría de los issues etiquetados `bug` en tldr vienen de usuarios externos (no del core team), lo cual tiene sentido para un repo de documentación colaborativa donde la mayoría de los "bugs" reportados son errores de contenido en páginas, no fallas de código.

**Nota sobre el core team:** el tamaño (`core_team_size=10`) es un parámetro configurable. Un valor más chico endurece el criterio de "externo" (más reportes cuentan como internos); uno más grande lo relaja. Vale la pena probar con distintos valores y comparar sensibilidad del resultado antes de fijar uno para el análisis final de la tesis.

---

## 5. Referencias

- Rashid, J., Mahmood, T., & Nisar, M. W. — *A Study on Software Metrics and its Impact on Software Quality*.
- DRE (Defect Removal Efficiency) como marco teórico de referencia para interpretar el valor de CFDR.
