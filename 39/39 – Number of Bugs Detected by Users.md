# 39 – Number of Bugs Detected by Users

## Ficha Técnica

| Campo | Descripción                                                                                                                                                                |
|---|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Consigna** | 35 - Número de Bugs detectados por Usuarios                                                                                                                                |
| **Métrica Original (ISL)** | User Reported Bugs / User-Detected Bugs                                                                                                                                    |
| **Nombre Alternativo** | User-detected Defects                                                                                                                                                      |
| **Métrica Canónica JAIIO 2022** | Number of Bugs Detected by Users                                                                                                                                           |
| **Métrica Adoptada / Calculable** | Number of Bugs Detected by Users (NUB)                                                                                                                                     |
| **Dimensiones Asociadas** | Producto, Proceso                                                                                                                                                          |
| **Fuente** | [Catálogo canónico 2022 (Google Docs)](https://docs.google.com/document/d/1DCmKuqtu7s9BhdJQdVVzbGx6h0tM-TE7/edit?rtpof=true) |

---

## 1. Observación

Correspondencia prácticamente exacta: la consigna utiliza el mismo concepto que la métrica canónica identificada en la ISL 2022. No se identificaron métricas alternativas con mejor ajuste.

**Se implementa el algoritmo original de la consigna** (`calcular_bugs_detectados_por_usuarios`), que clasifica un issue como "bug" si alguna de sus **labels** coincide (por substring) con un set de palabras clave (`defect`, `error`, `bug`, `issue`, `mistake`, `incorrect`, `fault`, `flaw`), y excluye del conteo a los reportantes que pertenecen al **core team** del proyecto.

**Corrección aplicada al algoritmo:** el código original tal como fue provisto contiene un bug de *variable shadowing* en la línea de detección:

```python
es_bug = any(key in label for key in etiquetas for key in keywords_bug)
```

La variable `key` se reutiliza en los dos `for` del generador (primero recorriendo `etiquetas`, luego pisándola al recorrer `keywords_bug`), y `label` **nunca queda definida** — esto produce un `NameError` en tiempo de ejecución. Se corrigió a:

```python
es_bug = any(keyword in label for label in etiquetas for keyword in keywords_bug)
```

preservando la intención original: verificar si alguna keyword aparece como substring de alguna etiqueta del issue.

**Core team:** se identifica a partir del archivo `MAINTAINERS.md` (o `CODEOWNERS` como fallback) del repositorio, extrayendo los handles de GitHub mencionados.

> **Limitación metodológica reconocida:** tldr-pages/tldr no usa labels de tipo "bug"/severidad de forma consistente (sus labels están orientados a categorías como *page edit*, *new command*, *help wanted*), por lo que este cálculo fiel al algoritmo original probablemente arroje un valor bajo o cercano a 0 — de forma análoga a lo observado en las métricas 16 y 35. Queda documentado que una variante que use keywords en título/body del issue (en vez de labels) podría dar mayor cobertura, pero se prioriza la fidelidad al algoritmo tal como fue provisto en la consigna.

---

## 2. Definición de la Métrica

**Number of Bugs Detected by Users (NUB)** cuantifica el volumen de incidentes técnicos (o, en este caso, de contenido) reportados **exclusivamente por usuarios externos** al equipo principal (core team) del proyecto.

### 2.1 Dimensiones Asociadas

| Dimensión | Justificación |
|---|---|
| **Producto** | Evalúa la calidad del producto (en este caso, la documentación) desde la perspectiva externa del usuario final. |
| **Proceso** | Refleja la efectividad del proceso de revisión/QA interno: cuántos defectos se "escapan" y son detectados recién en producción por terceros. |

### 2.2 Fundamento Teórico

Según **Vasilescu et al. (2015)**, esta distinción entre defectos detectados por el core team y por usuarios externos permite diferenciar la **capacidad de descubrimiento interna** de los **defectos que se escapan a la fase de producción**.

---

## 3. Cálculo

### 3.1 Entradas

| Entrada | Qué representa |
|---|---|
| **Metadata de issues del repositorio** | Lista obtenida vía GraphQL. Cada issue contiene `user_login` (autor) y `labels` (lista de etiquetas). |
| **Core team** | Set de logins de GitHub extraídos de `MAINTAINERS.md` (vía REST API, contenido raw del archivo). |

### 3.2 Lógica del proceso

1. Se descarga el contenido de `MAINTAINERS.md` y se extraen los handles de GitHub mencionados (patrón `@usuario`) para construir el set de core team.
2. Para cada issue del período, se revisa si alguna de sus `labels` contiene (por substring) alguna de las keywords: `defect`, `error`, `bug`, `issue`, `mistake`, `incorrect`, `fault`, `flaw`.
3. Si el issue se clasifica como bug **y** su autor **no** pertenece al core team, se cuenta como un "bug detectado por usuario".

### 3.3 Salida

| Salida | Qué representa |
|---|---|
| **NUB total** | Número entero: cantidad de issues clasificados como bug, reportados por usuarios no afiliados al core team. |

---

## 4. Salida Obtenida

**Repositorio analizado:** tldr-pages/tldr
**Período analizado:** 2025-08-07 → 2026-08-07

| Métrica | Valor |
|---|---|
| Issues totales analizados en el período | 278 |
| Core team detectado (vía MAINTAINERS.md) | 96 |
| **Number of Bugs Detected by Users (NUB)** | **0** |

> Confirma la limitación metodológica anticipada en la sección 1: `MAINTAINERS.md` sí existe y se pudo leer correctamente (96 usuarios detectados), pero ninguno de los 278 issues del período tiene labels que matcheen con las keywords de bug (`defect`, `error`, `bug`, `issue`, `mistake`, `incorrect`, `fault`, `flaw`) — consistente con lo observado en las métricas 16 y 35: tldr-pages usa un esquema de labels orientado a categorías de contenido (*page edit*, *new command*, *help wanted*), no a severidad/tipo de defecto.

---

## 5. Referencias

- Vasilescu, B. et al. (2015). Distinción entre defectos detectados por el core team y por usuarios externos como indicador de calidad externa.